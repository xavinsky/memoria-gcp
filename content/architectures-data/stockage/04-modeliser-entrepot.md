---
title: "Modéliser l'entrepôt BigQuery"
---

Dans [BigQuery](#bigquery), le schéma d'un entrepôt se choisit sur les **requêtes** qu'il sert, pas sur la forme de la base source. Un moteur en colonnes distribué paie cher les jointures entre grosses tables, et peu le stockage : la règle par défaut est de **dénormaliser**, en gardant les relations parent-enfant dans des champs imbriqués et répétés. Le schéma en étoile reste valable dans des cas précis. L'organisation physique (partitionnement, clustering, types de tables) est dans [BigQuery : organiser les tables](#organiser-bigquery).

## Quatre modèles

| Modèle | Forme | Jointures à la lecture | Mises à jour | Cas typique |
|---|---|---|---|---|
| **Normalisé** (schéma de la source) | Une table par entité, clés étrangères | Nombreuses, souvent entre grosses tables | Simples : une valeur à un seul endroit | Reprise brute d'une base transactionnelle, couche d'atterrissage |
| **Étoile** (ou flocon) | Table de faits centrale, tables de dimensions autour ; flocon : dimensions elles-mêmes normalisées | Une par dimension, grosse table contre petites | Localisées dans la dimension | Outils BI, dimensions partagées entre plusieurs faits |
| **Dénormalisé à plat** | Une ligne par ligne fille, attributs du parent recopiés | Aucune | Coûteuses : chaque recopie est à réécrire | Tables étroites, relation un-à-un |
| **Imbriqué et répété** | Une ligne par parent, lignes filles dans un `ARRAY<STRUCT<…>>` | Aucune pour la hiérarchie | Réécriture de la ligne parente | Commande et ses lignes, session et ses événements, livre et ses auteurs |

- **Pourquoi dénormaliser** : une jointure oblige les *slots* à échanger des données ; une ligne dénormalisée se traite en parallèle sur un seul slot. Le surcoût de stockage pèse peu face au gain de lecture.
- **Pourquoi ne pas tout aplatir** : aplatir une relation un-à-plusieurs multiplie les lignes et impose ensuite un `GROUP BY` par clé parente, donc un *shuffle*. L'imbriqué-répété garde une ligne par parent et évite ce regroupement.
- **Pourquoi ne pas garder le schéma source** : chaque requête rejoue les mêmes jointures, et BigQuery n'indexe pas les clés primaires.

## Champs imbriqués et répétés

Un `STRUCT` (`RECORD` dans le schéma) range une entité liée dans la ligne ; un champ en mode `REPEATED` (un `ARRAY`) y range une relation un-à-plusieurs ; les deux se combinent en `ARRAY<STRUCT<…>>`. La syntaxe de lecture (`UNNEST`, notation pointée, sous-requêtes sur tableau) est dans [GoogleSQL : ARRAY, STRUCT et JSON](#googlesql-tableaux-struct-json).

```sql
-- Commandes : une ligne par commande, lignes de commande imbriquées
CREATE TABLE DATASET.orders (
  order_id   INT64 NOT NULL,
  order_ts   TIMESTAMP,
  customer   STRUCT<id INT64, name STRING, country STRING>,
  items      ARRAY<STRUCT<sku STRING, qty INT64, price NUMERIC>>
)
PARTITION BY DATE(order_ts)
CLUSTER BY customer.country;

-- Montant par commande, sans jointure ni GROUP BY sur la table
SELECT order_id,
       (SELECT SUM(i.qty * i.price) FROM UNNEST(items) AS i) AS total
FROM DATASET.orders
WHERE DATE(order_ts) = '2026-09-01';

-- Construire la table depuis un schéma normalisé
CREATE OR REPLACE TABLE DATASET.orders AS
SELECT o.order_id, o.order_ts,
       STRUCT(c.id, c.name, c.country) AS customer,
       ARRAY_AGG(STRUCT(l.sku, l.qty, l.price)) AS items
FROM DATASET.src_orders o
JOIN DATASET.src_customers c ON c.id = o.customer_id
JOIN DATASET.src_order_lines l ON l.order_id = o.order_id
GROUP BY o.order_id, o.order_ts, c.id, c.name, c.country;
```

- **Bonne cible** : relations hiérarchiques lues ensemble, de cardinalité modérée par parent. Une relation à très forte cardinalité (des millions d'enfants par parent) reste une table séparée.
- **Limites** : 15 niveaux d'imbrication de `RECORD` au plus, répétés ou non ; 10 000 colonnes par table, résultat de requête ou vue, champs imbriqués compris (les colonnes supprimées peuvent compter un temps) ; environ 100 Mo par ligne.
- Un `RECORD` est incompatible avec `UNION`, `INTERSECT`, `EXCEPT DISTINCT` et `SELECT DISTINCT`.
- Les formats à schéma objet (JSON, Avro, exports Firestore) se chargent directement en champs imbriqués et répétés.

## Quand garder une étoile

La documentation le dit : un schéma en étoile est déjà optimisé pour l'analyse, et le dénormaliser davantage ne change souvent pas grand-chose. Il reste le bon choix dans ces cas :

- **Outils BI** qui attendent faits et dimensions ([Looker](#looker), modèles sémantiques) ; BI Engine accélère justement une table de faits jointe à quelques petites dimensions (voir plus bas).
- **Dimensions partagées** entre plusieurs tables de faits (client, produit, calendrier) : les recopier dans chaque fait les dupliquerait.
- **Dimensions qui changent souvent** : une modification touche une petite table au lieu de réécrire toutes les lignes de faits qui en portent une copie.
- **Dimensions historisées** (voir plus bas) : l'historique vit dans la dimension, le fait pointe vers la bonne version.

Pour aider l'optimiseur, déclarer les clés : `PRIMARY KEY (id) NOT ENFORCED` sur la dimension, `FOREIGN KEY (client_id) REFERENCES DATASET.dim_client(id) NOT ENFORCED` sur le fait. BigQuery s'en sert pour simplifier les plans mais **ne vérifie rien** : une clé déclarée et fausse donne des résultats faux.

## Ce que coûte une jointure

| Plan | Quand | Coût | Dans le plan d'exécution |
|---|---|---|---|
| **Diffusion** (*broadcast join*) | Un côté tient en mémoire sur un slot : typiquement une dimension | Faible : la petite table est envoyée à chaque slot qui lit la grande | `JOIN EACH WITH ALL` |
| **Hachage** (*hash join*) | Deux grosses tables | Élevé : les deux côtés sont redistribués (*shuffle*) par clé | `JOIN EACH WITH EACH` |

- Placer la plus grosse table en premier, puis la plus petite, puis les autres par taille décroissante  : l'optimiseur choisit lui-même le côté de chaque table, mais c'est l'ordre que recommande la documentation.
- Joindre sur des `INT64` plutôt que des `STRING` : la comparaison est plus rapide et BigQuery n'indexe pas les clés.
- Filtrer et agréger **avant** la jointure ; ne pas appliquer de fonction sur la colonne de jointure (normaliser la clé à l'ingestion).
- Une clé très déséquilibrée (*skew*, une valeur qui concentre les lignes) laisse un slot travailler seul : temps maximal d'une étape bien supérieur au temps moyen. Pré-filtrer la valeur dominante ou traiter la requête en deux passes. Lire le plan : [Diagnostiquer BigQuery](#diagnostiquer-bigquery).

## Dimensions à évolution lente

Une dimension à évolution lente (*slowly changing dimension*, SCD) change rarement mais change : adresse d'un client, catégorie d'un produit. Le type dit ce qu'on garde de l'ancienne valeur.

| Type | Traitement | Colonnes ajoutées | Lecture d'un fait ancien | Écriture |
|---|---|---|---|---|
| **1** | Écraser la valeur | Aucune | Voit la valeur actuelle | `MERGE` avec `UPDATE` (*upsert*) |
| **2** | Fermer la ligne courante, insérer une nouvelle version | Clé de version, `valid_from`, `valid_to`, `is_current` | Voit la valeur en vigueur à la date du fait | `MERGE` qui ferme et insère en une instruction |

- **Type 2, jointure** : soit le fait porte la clé de la version (posée au chargement), soit on joint à la date : `f.ts >= d.valid_from AND (f.ts < d.valid_to OR d.valid_to IS NULL)`.
- **Clustering** : clusteriser la dimension sur la clé métier ; filtrer `is_current` pour les lectures qui ne veulent que l'état actuel.
- La syntaxe `MERGE` d'un type 2 est dans [GoogleSQL : DML et transactions](#googlesql-dml).

> [!WARNING]
> Le voyage dans le temps (`FOR SYSTEM_TIME AS OF`) ne remplace pas une SCD : sa fenêtre va de deux à sept jours. L'historique métier se modélise dans la table.

## Vue logique, vue matérialisée ou table

| | Vue logique | Vue matérialisée | Table calculée (`CREATE TABLE AS`, requête planifiée) |
|---|---|---|---|
| Stockage | Aucun | Oui, facturé | Oui, facturé |
| Calcul | Requête rejouée à chaque lecture | Rafraîchissement en arrière-plan ; lecture de la vue plus des seules modifications récentes | Une fois par exécution du traitement |
| Fraîcheur | Toujours à jour | À jour (vue incrémentale), ou bornée par `max_staleness` (de 30 minutes à 3 jours) | Celle du dernier traitement |
| SQL | Complet : fenêtres, UDF, toutes les jointures | Restreint (voir ci-dessous) | Complet |
| Réacheminement automatique | Non | *Smart tuning* (vues incrémentales) | Non |
| Pour | Couche sémantique, sécurité, logique encore mouvante | Agrégats répétés sur des tables qui changent | Transformation lourde, résultat figé, instantané |

**Restrictions des vues matérialisées incrémentales :**

- Forme `SELECT … FROM … WHERE … GROUP BY` ; les agrégats sont des sorties, on ne calcule, ne filtre ni ne joint sur un agrégat (`COUNT(*) / 10` est refusé).
- Agrégats admis : `COUNT`, `COUNTIF`, `SUM`, `AVG`, `MIN`, `MAX`, `ANY_VALUE`, `ARRAY_AGG`, `APPROX_COUNT_DISTINCT`, `HLL_COUNT.INIT`, `MAX_BY`, `MIN_BY`, `LOGICAL_AND`/`OR`, `BIT_AND`/`OR`/`XOR` (avec des réserves sur les `STRUCT` et `ARRAY`).
- Refusés : fonctions de fenêtre, auto-jointures, `RIGHT`/`FULL OUTER JOIN`, fonctions non déterministes (`CURRENT_DATE()`, `RAND()`, `SESSION_USER()`), UDF, sous-requêtes `ARRAY`, `TABLESAMPLE`, `FOR SYSTEM_TIME AS OF`, fonctions d'IA générative.
- [!PREVERSION] `LEFT OUTER JOIN` et `UNION ALL` : acceptés, sans *smart tuning*.
- **Jointures** : la vue ne se rafraîchit en incrémental que sur les ajouts à la table la plus à gauche ; toute modification d'une autre table invalide la vue. Dans une étoile, mettre la table de faits en premier.
- Pas de vue matérialisée sur une autre vue matérialisée, sur une table externe (hors BigLake), une table générique ou un instantané. La définition ne se modifie pas : il faut recréer la vue.
- `allow_non_incremental_definition = true` lève la plupart des restrictions (jointures externes, `HAVING`, fenêtres) contre un recalcul complet à chaque rafraîchissement, une fraîcheur bornée par `max_staleness` obligatoire, et plus de *smart tuning*.
- L'édition Standard ne crée pas de vues matérialisées ; elle ne fait qu'interroger celles qui existent.

Syntaxe et options de rafraîchissement : [BigQuery : organiser les tables](#organiser-bigquery) et [BigQuery : DDL](#bigquery-ddl).

## BI Engine

BI Engine est un cache en mémoire avec un moteur vectorisé, placé devant BigQuery. Il accélère les requêtes `SELECT` qui passent par l'API, donc la console, les pilotes JDBC/ODBC, [Data Studio](#data-studio), [Looker](#looker), Tableau ou Power BI, sans changer les requêtes.

- **Réservation** : une capacité en Gio de mémoire, par projet et par région (la région des données), de 1 à 250 Gio par défaut, facturée à la Gio-heure. Disponible avec les éditions Enterprise et Enterprise Plus et en tarification à la demande, pas avec l'édition Standard.
- **Tables préférées** : limitent l'accélération à une liste de tables ; les autres requêtes utilisent les slots habituels. Une requête multi-tables n'est accélérée que si toutes ses tables sont dans la liste ; une vue matérialisée, seulement avec ses tables de base.
- **Ce qu'il accélère** : les étapes feuilles (lecture, filtre, calcul, agrégation, tri) et les jointures `INNER` ou `LEFT OUTER` d'une grosse table de faits avec **quatre dimensions au plus**, chacune sous 5 millions de lignes et 5 Gio (1 Gio de partitions lues si elle est partitionnée). Le reste retombe sur les slots, sans échec.
- **Ce qu'il n'accélère pas** : tables génériques, tables externes, sécurité au niveau des lignes, UDF non SQL, colonnes `JSON` ; fenêtres seulement sur une table unique, non partitionnée, de moins de 5 millions de lignes.
- **Quand c'est utile** : tableaux de bord interactifs qui répètent des requêtes courtes sur un jeu de tables connu. Pour garantir l'accélération d'un ensemble de requêtes, un projet dédié avec sa propre réservation.
- **Combinaison** : une vue matérialisée qui pré-joint et aplatit, marquée table préférée avec sa table de base, donne à BI Engine une seule table large à servir.
- **Mesure** : `INFORMATION_SCHEMA.JOBS` (`bi_engine_statistics.acceleration_mode`), `INFORMATION_SCHEMA.BI_CAPACITIES`, Cloud Monitoring ; désactiver le cache de résultats pour comparer.

```sql
ALTER BI_CAPACITY `PROJECT_ID.region-REGION.default`
SET OPTIONS (size_gb = 20,
             preferred_tables = ['DATASET.fact_ventes', 'DATASET.dim_client']);
```

## Anti-patterns de calcul

| Au lieu de | Écrire | Pourquoi |
|---|---|---|
| Auto-jointure pour comparer une ligne à la précédente | Fonction de fenêtre (`LAG`, `ROW_NUMBER`), ou `PIVOT` ([Fonctions de fenêtre](#googlesql-fenetres)) | L'auto-jointure peut élever au carré le nombre de lignes |
| Filtrer ou agréger après la jointure | `WHERE` et `GROUP BY` dans une sous-requête avant `JOIN` | Moins de données redistribuées |
| `SELECT *` suivi de `LIMIT` | Les colonnes utiles, ou `SELECT * EXCEPT (…)` ; l'aperçu de table pour explorer | `LIMIT` ne réduit pas les octets lus : toutes les colonnes sont facturées |
| UDF JavaScript pour un calcul simple | UDF SQL, persistante dans un dataset partagé | Une UDF JavaScript lance un sous-processus ; l'optimiseur ne voit pas son contenu |
| `ORDER BY` sans `LIMIT` sur un gros résultat, ou au milieu d'une requête | `ORDER BY` en fin de requête avec `LIMIT`, ou dans une fenêtre ; limiter avant la fenêtre | Tri final sur un seul nœud : *Resources exceeded* |
| Jointure sur une clé déséquilibrée | Pré-filtrer la valeur dominante, découper la requête | Un slot porte l'essentiel du travail |
| Jointure croisée non voulue | Pré-agréger, ou fenêtre | Sortie égale au produit des deux entrées |
| Même CTE référencée plusieurs fois | Table temporaire ou variable dans une requête multi-instructions | Une CTE peut être réévaluée à chaque référence |
| Mêmes jointures répétées dans chaque requête | Champs imbriqués, ou résultat matérialisé dans une table | Même données relues et redistribuées à chaque fois |
| `UPDATE` ou `INSERT` ligne à ligne | DML par lots depuis une table de préparation, streaming pour les insertions | BigQuery est un moteur d'analyse, pas une base transactionnelle |
| Tables datées (`events_20260901`…) | Table partitionnée | Schéma, métadonnées et droits vérifiés par table |

## Questions qui départagent

- **Les données filles se lisent-elles toujours avec leur parent ?** Oui : champ imbriqué et répété. Non, ou cardinalité énorme : table séparée.
- **La dimension sert-elle plusieurs faits, ou change-t-elle souvent ?** Oui : garder une dimension en étoile. Non : l'imbriquer ou la recopier dans le fait.
- **Faut-il la valeur d'une dimension à la date du fait ?** Oui : SCD de type 2. Non : type 1.
- **La même agrégation revient-elle souvent sur des données qui changent ?** Vue matérialisée. Transformation lourde relue telle quelle : table calculée. Logique qui bouge ou couche d'accès : vue logique.
- **Des tableaux de bord attendent-ils des réponses en moins d'une seconde ?** BI Engine sur des tables préférées, idéalement une table large ou une étoile à quatre dimensions au plus.

## Pièges

- Recopier le schéma normalisé d'une base transactionnelle et joindre à chaque requête : chaque tableau de bord rejoue des jointures entre grosses tables.
- Aplatir une relation un-à-plusieurs en recopiant le parent : les agrégats au niveau du parent comptent chaque ligne plusieurs fois, ou exigent un `DISTINCT` coûteux.
- Déclarer des clés primaires ou étrangères `NOT ENFORCED` sur des données qui ne les respectent pas : l'optimiseur s'y fie.
- Mettre une petite dimension en premier dans une vue matérialisée jointe : chaque ajout dans le fait n'est plus incrémental.
- Utiliser `CURRENT_DATE()` dans une vue matérialisée : refusé ; filtrer à la lecture, ou passer par une table calculée.
- Réserver BI Engine sans tables préférées sur un projet partagé : des requêtes ad hoc occupent la mémoire au détriment des tableaux de bord.
- Oublier que les colonnes supprimées peuvent compter dans la limite de 10 000 : une table large qu'on fait souvent évoluer finit par atteindre la limite.

## Alternatives en logiciel libre

- **ClickHouse** (Apache 2.0) : types `Nested`, `Array` et `Tuple` pour garder les hiérarchies dans la ligne, dictionnaires en mémoire pour des dimensions jointes à bas coût, vues matérialisées alimentées à l'insertion ; les nœuds sont à dimensionner.
- **Apache Doris** et **StarRocks** (Apache 2.0) : entrepôts MPP pensés pour l'étoile, avec jointures diffusées ou colocalisées et vues matérialisées qui réécrivent les requêtes, comme le *smart tuning*.
- **DuckDB** (MIT) : types `STRUCT` et `LIST` proches de ceux de BigQuery, sur une seule machine ; pratique pour prototyper un modèle imbriqué sur un extrait.
- **dbt Core** (Apache 2.0) : modèles SQL versionnés et *snapshots*, qui produisent une dimension de type 2 avec colonnes de validité ; s'exécute sur BigQuery comme ailleurs.
- **SQLMesh** (Apache 2.0) : modèles de type SCD 2 déclarés dans la définition du modèle, et planification des changements de schéma avant exécution.
- **Cube** (Apache 2.0) : couche sémantique entre l'entrepôt et les outils BI, avec des pré-agrégations stockées qui jouent le rôle des vues matérialisées et de BI Engine pour les tableaux de bord.
