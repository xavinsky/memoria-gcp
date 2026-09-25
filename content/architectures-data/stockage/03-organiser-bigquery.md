---
title: "BigQuery : organiser les tables"
---

Dans [BigQuery](#bigquery), le découpage en **projets** et **datasets** fixe qui paie, qui accède à quoi et où vivent les données. Ensuite, la façon de ranger une table décide du volume lu par chaque requête, donc de son coût et de sa durée. Deux leviers physiques — **partitionnement** et **clustering** — se choisissent à la création ; le **type de table** dit où vivent les données ; les **vues matérialisées** évitent de recalculer des agrégats demandés souvent.

## Découper en projets et datasets

Un *job* BigQuery (requête, chargement, export) appartient toujours à un projet, qui n'est pas forcément celui des données : une requête peut lire des tables de plusieurs projets. Pour lire une table, il faut donc deux droits distincts : un droit sur la table, et le droit de créer un job dans le projet qui exécute.

| | Projet de stockage | Projet de calcul |
|---|---|---|
| Contient | Datasets : tables, vues, routines | Jobs, et les datasets de travail de l'équipe |
| Facture | Le stockage des datasets | Les requêtes à la demande, au projet qui les exécute ; en éditions, les slots sont facturés au projet d'administration qui les achète, puis affectés à des projets, des dossiers ou l'organisation |
| Quotas | Les quelques quotas par dataset | Les quotas de calcul (requêtes, chargements, requêtes simultanées), comptés sur le projet qui crée le job |
| Droits typiques | `dataViewer` pour les lecteurs, `dataEditor` pour le pipeline d'ingestion | `jobUser` pour ceux qui lancent des requêtes |

La documentation décrit deux organisations, souvent combinées :

- **Lac central, *data marts* par département** : un projet de stockage central, alimenté par l'équipe data ; chaque département interroge depuis son propre projet, rattaché à son compte de facturation, avec ses propres quotas. Les analystes ont `dataViewer` sur les datasets centraux qui les concernent, `dataEditor` et `jobUser` dans le projet de leur département.
- **Lacs par département, entrepôt central** : chaque département gère le projet de ses données brutes ; un projet central porte les agrégats et exécute les requêtes des analystes et des outils de BI. Ce projet concentre les requêtes simultanées : relever son quota, ou lui affecter une réservation de slots.

**Le dataset est une frontière** pour plusieurs réglages :

- **Emplacement** : fixé à la création, il ne change plus ; on copie le dataset ailleurs ou on le recrée. Une requête s'exécute dans l'emplacement des tables qu'elle lit, et un projet peut contenir des datasets de régions différentes.
- **Droits** : les tables, vues et routines héritent des droits posés sur leur dataset, qui hérite lui-même du projet, des dossiers et de l'organisation. Un droit sur une seule table ou vue reste possible.
- **Expiration par défaut** : `default_table_expiration_days` et `default_partition_expiration_days` s'appliquent aux tables créées ensuite ; une table créée avec sa propre expiration l'ignore, et changer la valeur ne touche pas les tables existantes.
- **Clé [CMEK](#chiffrement) par défaut**, **modèle de facturation du stockage** (logique ou physique) et **fenêtre de *time travel*** se règlent aussi au niveau du dataset.

D'où la règle de découpage : un dataset regroupe des tables qui partagent les mêmes lecteurs, la même région et la même rétention. En pratique, un dataset par domaine et par couche (`ventes_brut`, `ventes_expose`), et un dataset à part pour les données sensibles plutôt que des droits table par table.

```sql
CREATE SCHEMA `PROJECT_ID.ventes_brut`
OPTIONS (
  location = 'europe-west1',
  default_table_expiration_days = 90,
  default_kms_key_name = 'projects/PROJECT_ID/locations/europe-west1/keyRings/RING/cryptoKeys/KEY'
);

GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT_ID.ventes_expose`
TO "group:analystes@example.com";
```

### Rôles BigQuery prédéfinis

| Rôle | Ce qu'il permet | Où le poser |
|---|---|---|
| `roles/bigquery.jobUser` | Lancer des jobs, dont les requêtes, dans le projet ; aucun accès aux données | Projet, dossier ou organisation uniquement |
| `roles/bigquery.user` | Lancer des jobs, lister les datasets du projet, créer des datasets (dont le créateur devient `dataOwner`), ouvrir des sessions de lecture | Projet ; sur un dataset, il ne donne que la liste des tables et les métadonnées |
| `roles/bigquery.dataViewer` | Lire les métadonnées et les données, exporter, créer des instantanés ; lister et appeler les routines | Dataset, ou table, vue, routine |
| `roles/bigquery.dataEditor` | Celui de `dataViewer`, plus créer, modifier et supprimer tables et vues ; au niveau projet, créer des datasets | Dataset, ou table, vue, routine |
| `roles/bigquery.dataOwner` | Tout sur le dataset et son contenu, y compris ses droits et les politiques d'accès aux lignes | Dataset, ou table, vue, routine |
| `roles/bigquery.metadataViewer` | Schémas et métadonnées, sans lire les données | Dataset, ou table, vue, routine |
| `roles/bigquery.readSessionUser` | Créer et lire des sessions de l'API Storage Read (connecteurs Spark, Trino) | Projet, dossier ou organisation |
| `roles/bigquery.connectionUser` | Utiliser une connexion : tables BigLake, fonctions distantes | Connexion ou projet |
| `roles/bigquery.resourceViewer` | Voir les jobs de tous et les réservations, sans rien modifier | Projet, dossier ou organisation |
| `roles/bigquery.admin` | Tout, dont annuler les jobs des autres | Projet |

- **L'analyste type** reçoit `jobUser` (ou `user` s'il doit créer ses propres datasets) sur le projet qui exécute ses requêtes, et `dataViewer` sur les seuls datasets qu'il lit. `dataOwner` et `admin` sont réservés aux équipes qui administrent les données.
- `jobUser` seul ne lit rien ; `dataViewer` seul ne permet pas de lancer une requête. Une erreur `bigquery.jobs.create` désigne le projet de calcul, une erreur `bigquery.tables.getData` le dataset.
- Un droit de lecture sur le bucket d'une table externe ne remplace pas les rôles BigQuery, et contourne la sécurité fine : voir [Lakehouse](#lakehouse-architecture). Les principes généraux (groupes, niveau le plus bas) sont dans [IAM : bonnes pratiques](#iam-bonnes-pratiques).

## Partitionnement ou clustering

Le partitionnement découpe la table en segments selon une colonne ; une requête qui filtre sur cette colonne ignore les autres segments (*partition pruning*). Le clustering trie les blocs de stockage selon une à quatre colonnes ; une requête filtrée sur ces colonnes saute les blocs hors plage (*block pruning*).

| | Partitionnement | Clustering |
|---|---|---|
| Colonnes | Une seule | Jusqu'à quatre, l'ordre compte |
| Types | `DATE`, `TIMESTAMP`, `DATETIME`, `INT64`, ou l'heure d'ingestion | `STRING`, `INT64`, `NUMERIC`, `BIGNUMERIC`, `DATE`, `DATETIME`, `TIMESTAMP`, `BOOL`, `GEOGRAPHY`, `RANGE` |
| Estimation avant exécution | Précise : le *dry run* connaît les partitions lues | Approximative : le volume réel n'est connu qu'après exécution |
| Gestion | Expiration, remplacement ou suppression d'une partition, filtre obligatoire | Aucune : reclustering automatique et gratuit en arrière-plan |
| Limites | 10 000 partitions par table ; 4 000 partitions modifiées par job ; 30 000 modifications de partitions par jour (table partitionnée par colonne) | Pas de limite propre |
| Cardinalité adaptée | Faible à moyenne, avec des partitions d'au moins 10 Go environ | Élevée : identifiants, codes, clients |
| Stockage à long terme | Chaque partition bascule seule après 90 jours sans modification | La table entière doit rester 90 jours sans modification |

**Trois façons de partitionner :**

- **Colonne de temps** (`DATE`, `TIMESTAMP`, `DATETIME`) : granularité horaire, quotidienne (par défaut), mensuelle ou annuelle, bornes en UTC. C'est le choix naturel quand les requêtes filtrent sur une date métier.
- **Heure d'ingestion** : BigQuery range chaque ligne selon son heure d'arrivée, exposée par les pseudo-colonnes `_PARTITIONTIME` et `_PARTITIONDATE`. Utile quand les données n'ont pas de date fiable.
- **Plage d'entiers** : `RANGE_BUCKET` sur une colonne `INT64`, avec début, fin et pas ; au plus 10 000 plages. Pas d'expiration de partition possible.

Les lignes hors plage vont dans la partition `__UNPARTITIONED__`, les valeurs nulles dans `__NULL__`.

**Quand choisir quoi :**

- Partitionner quand les requêtes filtrent sur une date, que le coût doit être connu avant exécution, ou que les données expirent par tranche.
- Clusteriser quand les filtres portent sur plusieurs colonnes ou sur une colonne à forte cardinalité, quand les partitions seraient trop petites, ou quand des DML touchent la plupart des partitions à quelques minutes d'intervalle. Au-dessous de 64 Mo par table ou partition, le gain est négligeable.
- **Combiner les deux** est le cas courant : partition par jour sur la date d'événement, clustering sur les colonnes filtrées ensuite (client, pays, statut). Avec un historique long et peu de lignes par jour, partitionner par mois ou par an et clusteriser sur la colonne de date.
- **Ne pas fragmenter en tables datées** (`events_20260101`, `events_20260102`…) : une table partitionnée fait la même chose avec un seul schéma et de meilleures performances.

> [!WARNING]
> L'élagage ne fonctionne qu'avec une expression **constante** sur la colonne de partition, isolée d'un côté de la comparaison ou enveloppée dans une fonction reconnue (`DATE_TRUNC`, `TIMESTAMP_SUB`, `EXTRACT`…). `WHERE event_date = (SELECT MAX(d) FROM t2)` ou `WHERE event_ts >= other_ts` lisent toute la table. Le *dry run* dit si la requête élague.

## Options de gestion

- **`partition_expiration_days`** : chaque partition est supprimée ce nombre de jours après sa borne de fin. Une valeur par défaut peut être posée au niveau du dataset ; l'expiration de la table, si elle existe, l'emporte. Réduire la valeur supprime aussitôt les partitions trop anciennes.
- **`require_partition_filter = TRUE`** : toute requête sans filtre sur la colonne de partition échoue. C'est la protection simple contre le `SELECT` qui lit des années d'historique.
- **Changer après coup** : le clustering se modifie sur une table existante (`bq update --clustering_fields=customer_id DATASET.TABLE`), mais seules les nouvelles données sont triées selon la nouvelle clé ; réécrire les lignes existantes par un `UPDATE` pour tout reclusteriser. Le partitionnement, lui, ne se change pas : il faut recréer la table par `CREATE TABLE ... AS SELECT`.

```sql
-- Événements : partition quotidienne, clustering, expiration à 400 jours
CREATE TABLE DATASET.events (
  event_ts    TIMESTAMP NOT NULL,
  customer_id STRING,
  country     STRING,
  event_type  STRING,
  payload     JSON
)
PARTITION BY TIMESTAMP_TRUNC(event_ts, DAY)
CLUSTER BY customer_id, event_type
OPTIONS (
  partition_expiration_days = 400,
  require_partition_filter = TRUE
);

-- Historique long, peu de lignes par jour : partition mensuelle, clustering sur la date
CREATE TABLE DATASET.invoices (invoice_date DATE, customer_id STRING, amount NUMERIC)
PARTITION BY DATE_TRUNC(invoice_date, MONTH)
CLUSTER BY invoice_date, customer_id;

-- Plage d'entiers : 100 partitions de 10 000 identifiants
CREATE TABLE DATASET.accounts (account_id INT64, region STRING)
PARTITION BY RANGE_BUCKET(account_id, GENERATE_ARRAY(0, 1000000, 10000));

-- Modifier après création
ALTER TABLE DATASET.events SET OPTIONS (partition_expiration_days = 180);
ALTER TABLE DATASET.accounts SET OPTIONS (require_partition_filter = TRUE);
```

## Où vivent les données : types de tables

| Type | Données | Écriture | Droits | Performances | Cas typique |
|---|---|---|---|---|---|
| **Table native** | Stockage géré de BigQuery | DML, chargement, streaming | IAM, sécurité par ligne et par colonne | Les meilleures ; partitionnement et clustering complets | Entrepôt, tout ce qui est interrogé souvent |
| **Table externe** | Fichiers (Cloud Storage, Drive) ou Bigtable | Lecture seule | L'utilisateur doit lire la table **et** la source | Plus lentes ; pas de clustering, partitionnement Hive limité | Lecture ponctuelle, ELT en une passe vers une table native |
| **Table BigLake** | Fichiers Parquet, ORC, Avro, CSV… sur Cloud Storage, S3 ou Azure | Lecture seule | Délégation d'accès par une connexion : droit sur la table seulement ; sécurité par ligne, par colonne, masquage | Cache de métadonnées (fraîcheur de 30 minutes à 7 jours) | Lac de données partagé avec d'autres moteurs, données restées chez un autre fournisseur |
| **Table d'objets** | Fichiers non structurés (images, PDF, audio) sur Cloud Storage, vus comme une ligne de métadonnées par objet | Lecture seule | Délégation d'accès, sécurité par ligne | — | Inférence BigQuery ML ou fonctions distantes sur des documents |
| **Table Iceberg gérée** | Parquet au format Iceberg, dans un bucket du client | DML, streaming par la Storage Write API | Comme une table native | Optimisation automatique (compactage, clustering) | *Lakehouse* ouvert : même copie lue par Spark ou Flink |

- **Table externe ou BigLake ?** Dès que la table est partagée au-delà de son créateur, BigLake : on ne donne plus aux utilisateurs l'accès au bucket, et le cache de métadonnées accélère les requêtes sur de nombreux fichiers. Une table externe peut être convertie en table BigLake.
- **Charger ou lire en place ?** Charger dans une table native reste plus rapide et le chargement par lots est gratuit. Lire en place se justifie quand d'autres moteurs écrivent les fichiers ou quand les données changent souvent. Le détail du catalogue et des tables ouvertes est dans [Lakehouse](#lakehouse-architecture) et la fiche [Lakehouse](#lakehouse).

```sql
-- Table BigLake sur des fichiers Parquet, cache de métadonnées rafraîchi automatiquement
CREATE EXTERNAL TABLE DATASET.sales_raw
WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://BUCKET/sales/*.parquet'],
  max_staleness = INTERVAL 4 HOUR,
  metadata_cache_mode = 'AUTOMATIC'
);

-- Table d'objets sur des PDF
CREATE EXTERNAL TABLE DATASET.invoices_pdf
WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID`
OPTIONS (object_metadata = 'SIMPLE', uris = ['gs://BUCKET/invoices/*.pdf']);
```

## Vues matérialisées

Une vue matérialisée stocke le résultat d'une requête d'agrégation et le tient à jour en arrière-plan. Les requêtes restent fraîches : BigQuery lit la vue et complète avec les seules modifications récentes des tables de base. Une vue **incrémentale** bénéficie du *smart tuning* : une requête écrite contre la table de base est réacheminée vers la vue quand celle-ci suffit à y répondre.

- **Pour** : tableaux de bord qui répètent les mêmes agrégats, prétraitement de flux à fort débit, vue autorisée qui partage un sous-ensemble agrégé.
- **Limites** : SQL restreint pour les vues incrémentales (agrégats, filtres, certaines jointures) ; `allow_non_incremental_definition = true` accepte le reste, mais chaque rafraîchissement recalcule tout et le *smart tuning* ne s'applique plus. 100 vues matérialisées au plus par table de base dans un même projet.
- **`max_staleness`** accepte des résultats un peu anciens en échange d'un coût et d'une latence stables : BigQuery sert la vue sans relire les tables de base tant que le dernier rafraîchissement est assez récent.

```sql
CREATE MATERIALIZED VIEW DATASET.daily_revenue
OPTIONS (enable_refresh = true, refresh_interval_minutes = 60)
AS
SELECT DATE(event_ts) AS day, country, SUM(amount) AS revenue, COUNT(*) AS orders
FROM DATASET.orders
GROUP BY day, country;
```

## Ce que ça change sur la facture

| | À la demande | Éditions (capacité) |
|---|---|---|
| Unité facturée | Octets lus par la requête, au Tio ; le premier Tio du mois est gratuit ; minimum 10 Mo par table lue | Slots consommés, à l'heure-slot ; autoscaling ou engagement d'un ou trois ans |
| Effet de l'élagage | Direct : chaque partition ou bloc sauté n'est pas facturé | Indirect : moins de données lues libère des slots et raccourcit les requêtes |
| Garde-fou | Plafond d'octets facturés par requête (`maximum_bytes_billed`), quotas personnalisés | Taille maximale de la réservation |

- Le coût à la demande dépend des **colonnes** lues : `SELECT *` suivi de `LIMIT` lit toutes les colonnes, sur toutes les partitions non élaguées.
- Le **stockage** baisse d'environ 50 % pour une table ou une partition non modifiée depuis 90 jours, sans perte de performances. Partitionner permet de profiter de ce tarif sur l'historique tout en écrivant chaque jour dans la partition du jour.
- Les tables externes et BigLake ne paient pas de stockage BigQuery, mais leurs requêtes lisent souvent plus : pas de clustering, et un format de fichier moins efficace que le stockage natif.
- Les vues matérialisées ajoutent un stockage et un coût de rafraîchissement : elles se justifient quand la requête qu'elles servent revient souvent.

## Alternatives en logiciel libre

- **ClickHouse** (Apache 2.0) : `PARTITION BY` pour découper et expirer, clé de tri `ORDER BY` qui joue le rôle du clustering, `TTL` pour supprimer ou déplacer les données anciennes, vues matérialisées alimentées à l'insertion ; tout est à dimensionner et à surveiller.
- **Apache Iceberg** (Apache 2.0) : partitionnement caché (transformations `day`, `bucket`, `truncate`) et ordre de tri par table ; contrairement à BigQuery, le partitionnement peut évoluer sans recréer la table, mais le compactage relève du moteur.
- **Delta Lake** (Apache 2.0) : *liquid clustering*, qui trie les fichiers selon des colonnes modifiables après coup ; le plus proche du clustering automatique de BigQuery dans un format ouvert.
- **Apache Doris** et **StarRocks** (Apache 2.0) : entrepôts MPP avec partitions et répartition par hachage, vues matérialisées asynchrones et réécriture automatique des requêtes vers ces vues, comme le *smart tuning*.
- **PostgreSQL** (licence PostgreSQL) avec **pg_partman** (licence PostgreSQL) : partitionnement déclaratif par plage ou liste, création et rétention automatiques des partitions ; pour des volumes qui tiennent sur une base transactionnelle.
- **Apache Druid** (Apache 2.0) : segments par intervalle de temps et agrégation à l'ingestion (*rollup*) ; adapté aux séries d'événements interrogées par période.
