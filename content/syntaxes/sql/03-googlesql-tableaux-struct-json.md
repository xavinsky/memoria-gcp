---
title: "GoogleSQL : ARRAY, STRUCT et JSON"
subgroup: Requêtes
type: syntax
---

BigQuery stocke volontiers les données dénormalisées : un `ARRAY` de `STRUCT` dans la ligne parente remplace la table fille et la jointure. Le type `JSON` sert aux données dont le schéma varie.

### Construire des tableaux

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Tableau littéral | `[1, 2, 3]`, `ARRAY<STRING>['a', 'b']` | `ARRAY<INT64>`, `ARRAY<STRING>` |
| Tableau depuis une sous-requête | `ARRAY(SELECT sku FROM DATASET.lignes AS l WHERE l.cmd_id = c.id ORDER BY sku)` | Un tableau par ligne de `c` ; l'ordre est gardé |
| Agréger en tableau | `ARRAY_AGG(sku ORDER BY ts DESC LIMIT 5)` | Les cinq derniers `sku` du groupe |
| Écarter les `NULL` | `ARRAY_AGG(remise IGNORE NULLS)` | Tableau sans `NULL` ; un résultat final ne peut pas contenir d'élément `NULL` |
| Valeurs distinctes | `ARRAY_AGG(DISTINCT pays)` | Sans doublon, ordre arbitraire |
| Concaténer des tableaux | `ARRAY_CONCAT(a, b)`, `ARRAY_CONCAT_AGG(tags)` | Un tableau ; la version `_AGG` fusionne ceux d'un groupe |
| Suite d'entiers ou de dates | `GENERATE_ARRAY(1, 10)`, `GENERATE_DATE_ARRAY('2025-01-01', '2025-01-31')` | Bornes incluses ; pas d'un jour par défaut |
| Tableau vers texte | `ARRAY_TO_STRING(tags, ', ')` | Chaîne ; les `NULL` sont ignorés |

> [!WARNING]
> Un tableau de tableaux n'existe pas : `ARRAY<ARRAY<INT64>>` est refusé. Passer par un `ARRAY<STRUCT<valeurs ARRAY<INT64>>>`, construit avec `SELECT AS STRUCT`.

### Lire des tableaux

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Taille | `ARRAY_LENGTH(tags)` | `0` pour un tableau vide, `NULL` pour un tableau `NULL` |
| Élément par position | `tags[OFFSET(0)]`, `tags[ORDINAL(1)]` | Premier élément ; erreur hors limites |
| Élément sans erreur | `tags[SAFE_OFFSET(3)]` | `NULL` si l'index dépasse |
| Premier, dernier | `ARRAY_FIRST(tags)`, `ARRAY_LAST(tags)` | Erreur sur un tableau vide |
| Sous-tableau | `ARRAY_SLICE(tags, 0, 2)` | Éléments aux positions 0 à 2 incluses |
| Appartenance | `WHERE 'promo' IN UNNEST(tags)` | Vrai si le tableau contient la valeur |
| Au moins un élément vérifie | `WHERE EXISTS (SELECT 1 FROM UNNEST(lignes) AS l WHERE l.qte > 10)` | Filtre sur le contenu du tableau |
| Transformer chaque élément | `ARRAY(SELECT UPPER(t) FROM UNNEST(tags) AS t)` | Nouveau tableau |
| Filtrer un tableau | `ARRAY(SELECT l FROM UNNEST(lignes) AS l WHERE l.qte > 0)` | Même type, éléments retenus seulement |
| Agréger dans la ligne | `(SELECT SUM(l.qte * l.prix) FROM UNNEST(lignes) AS l) AS total` | Un total par commande, sans `GROUP BY` |

### Aplatir avec UNNEST

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Une ligne par élément | `SELECT c.id, t FROM DATASET.commandes AS c CROSS JOIN UNNEST(c.tags) AS t` | Les commandes au tableau vide ou `NULL` disparaissent |
| Écriture courte | `FROM DATASET.commandes AS c, UNNEST(c.tags) AS t` | La virgule vaut `CROSS JOIN` |
| Garder les tableaux vides | `FROM DATASET.commandes AS c LEFT JOIN UNNEST(c.tags) AS t` | `t` vaut `NULL` pour les commandes sans tag |
| Position de l'élément | `CROSS JOIN UNNEST(c.etapes) AS e WITH OFFSET AS pos` | Colonne `pos` à partir de 0 ; `UNNEST` seul ne garantit pas l'ordre |
| Tableau de STRUCT à plat | `SELECT c.id, l.sku, l.qte FROM DATASET.commandes AS c, UNNEST(c.lignes) AS l` | Une ligne par ligne de commande, champs accessibles par `l.` |
| Tableau littéral en table | `SELECT * FROM UNNEST(['FR', 'BE', 'CH']) AS pays` | Petite table de référence en ligne |

> [!TIP]
> Filtrer d'abord, aplatir ensuite : `WHERE EXISTS (... UNNEST ...)` ou une sous-requête `ARRAY(...)` évite de multiplier les lignes puis de les regrouper à nouveau.

### STRUCT

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un STRUCT | `STRUCT('Paris' AS ville, '75001' AS cp) AS adresse` | Champs nommés `ville` et `cp` |
| Créer un STRUCT typé | `STRUCT<ville STRING, cp STRING>('Paris', '75001')` | Types imposés |
| Lire un champ | `adresse.ville`, `client.adresse.cp` | Notation pointée, sur plusieurs niveaux |
| Tous les champs en colonnes | `SELECT adresse.* FROM ...` | Une colonne par champ |
| Une ligne en STRUCT | `SELECT AS STRUCT sku, qte FROM ...` | Chaque ligne devient un STRUCT (utile dans `ARRAY(...)`) |
| Construire un imbriqué répété | `SELECT c.id, ARRAY_AGG(STRUCT(l.sku, l.qte, l.prix) ORDER BY l.num) AS lignes FROM DATASET.commandes AS c JOIN DATASET.lignes AS l ON l.cmd_id = c.id GROUP BY c.id` | Une ligne par commande avec ses lignes en `ARRAY<STRUCT>` |
| Déclarer la colonne dans le DDL | `lignes ARRAY<STRUCT<sku STRING, qte INT64, prix NUMERIC>>` | Champ `RECORD` en mode `REPEATED` dans le schéma |
| Comparer deux STRUCT | `WHERE a = b` | Égalité champ par champ, dans l'ordre des champs, noms ignorés ; pas de `<` ni de `>` |

### JSON

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Littéral JSON | `JSON '{"client": {"id": 42}, "tags": ["a", "b"]}'` | Valeur de type `JSON` |
| Chaîne vers JSON | `PARSE_JSON(payload)` | Erreur si le texte n'est pas du JSON ; `SAFE.PARSE_JSON` rend `NULL` ; `wide_number_mode => 'round'` accepte les nombres trop précis |
| Accès par notation pointée | `evt.client.id`, `evt.tags[0]`, `evt['champ-avec-tiret']` | Valeur `JSON`, `NULL` si le chemin n'existe pas |
| Extraire un scalaire en texte | `JSON_VALUE(evt, '$.client.nom')` | `STRING` sans guillemets ; `NULL` si la cible est un objet ou un tableau |
| Extraire un sous-objet | `JSON_QUERY(evt, '$.client')` | `JSON` (ou chaîne JSON si l'entrée est une chaîne) |
| Extraire un tableau | `JSON_QUERY_ARRAY(evt, '$.tags')` | `ARRAY<JSON>` à passer dans `UNNEST` |
| Tableau de scalaires | `JSON_VALUE_ARRAY(evt, '$.tags')` | `ARRAY<STRING>` |
| Convertir strictement | `INT64(evt.client.id)`, `STRING(evt.nom)`, `BOOL(evt.actif)` | Erreur si le type JSON ne correspond pas |
| Convertir avec tolérance | `LAX_INT64(evt.qte)`, `LAX_STRING(evt.code)`, `LAX_FLOAT64(...)`, `LAX_BOOL(...)` | `"12"` devient `12` ; `NULL` au lieu d'une erreur |
| Valeur SQL vers JSON | `TO_JSON(STRUCT(id, nom))` | Objet `JSON` |
| Ligne vers texte JSON | `TO_JSON_STRING(t)`, `TO_JSON_STRING(t, TRUE)` | Chaîne JSON, indentée avec `TRUE` |
| Lister les clés | `JSON_KEYS(evt)`, `JSON_KEYS(evt, 1)` | `ARRAY<STRING>` trié, dédoublonné ; `1` limite au premier niveau |
| Type d'une valeur | `JSON_TYPE(evt.qte)` | `'number'`, `'string'`, `'object'`, `'array'`… |
| Construire un objet | `JSON_OBJECT('id', id, 'nom', nom)` | `JSON` ; `JSON_ARRAY(1, 2)` pour un tableau |
| Modifier un document | `JSON_SET(evt, '$.statut', 'traite')`, `JSON_REMOVE(evt, '$.tmp')` | Nouveau `JSON` modifié |
| Grouper ou trier sur un champ | `GROUP BY JSON_VALUE(evt, '$.pays')` | Passage obligatoire par un scalaire |

> [!WARNING]
> Le type `JSON` n'a ni égalité ni comparaison : pas de `GROUP BY`, `ORDER BY`, `DISTINCT` ni de partitionnement ou de clustering sur une colonne `JSON`. Extraire le champ en scalaire avec `JSON_VALUE` ou un convertisseur. `JSON_EXTRACT`, `JSON_EXTRACT_SCALAR` et `JSON_EXTRACT_ARRAY` [!DECONSEILLE] sont dépréciées : utiliser `JSON_QUERY`, `JSON_VALUE` et `JSON_QUERY_ARRAY`.

> [!TIP]
> Un champ de colonne `JSON` souvent filtré mérite sa propre colonne typée : il devient partitionnable, clusterisable, et la requête n'a plus à convertir.

Contexte : [requêtes GoogleSQL](#googlesql-requetes), [fonctions de fenêtre](#googlesql-fenetres), [DDL BigQuery](#bigquery-ddl), [Organiser BigQuery](#organiser-bigquery), [BigQuery](#bigquery).
