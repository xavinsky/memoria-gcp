---
title: "BigQuery : DDL"
subgroup: DML et DDL
type: syntax
---

Créer et modifier datasets, tables, vues, fonctions et politiques en SQL. Le choix du partitionnement, du clustering et du type de table est expliqué dans [BigQuery : organiser les tables](#organiser-bigquery).

### Datasets

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un dataset dans une région | `CREATE SCHEMA IF NOT EXISTS PROJECT_ID.DATASET OPTIONS (location = 'REGION', description = '...')` | `SCHEMA` désigne un dataset ; sans `location`, il est créé là où s'exécute la requête |
| Poser des expirations par défaut | `CREATE SCHEMA DATASET OPTIONS (default_table_expiration_days = 30, default_partition_expiration_days = 400)` | Valeurs héritées par les **nouvelles** tables, qui peuvent les surcharger |
| Libeller un dataset | `ALTER SCHEMA DATASET SET OPTIONS (labels = [('equipe', 'data'), ('env', 'prod')])` | Libellés repris dans l'export de facturation |
| Réduire la fenêtre de *time travel* | `ALTER SCHEMA DATASET SET OPTIONS (max_time_travel_hours = 48)` | Multiple de 24, de 48 à 168 h (défaut 168) |
| Facturer le stockage en octets physiques | `ALTER SCHEMA DATASET SET OPTIONS (storage_billing_model = 'PHYSICAL')` | Effet sous 24 h ; plus de changement possible pendant 14 jours |
| Supprimer un dataset et son contenu | `DROP SCHEMA DATASET CASCADE` | Sans `CASCADE`, `RESTRICT` par défaut : échec si le dataset n'est pas vide |

### Créer une table

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Table avec schéma explicite | `CREATE TABLE DATASET.TABLE (id INT64 NOT NULL, nom STRING OPTIONS (description = '...'), maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP())` | `NOT NULL` = mode `REQUIRED` ; `DEFAULT` s'applique aux colonnes omises à l'insertion |
| Recréer sans erreur | `CREATE OR REPLACE TABLE ...` ou `CREATE TABLE IF NOT EXISTS ...` | Les deux formes s'excluent ; `OR REPLACE` ne peut pas changer le type de partitionnement |
| Partition quotidienne sur un horodatage | `PARTITION BY DATE(ts)` ou `PARTITION BY TIMESTAMP_TRUNC(ts, DAY)` | Granularités `HOUR`, `DAY`, `MONTH`, `YEAR` avec `TIMESTAMP_TRUNC` ou `DATETIME_TRUNC` |
| Partition mensuelle sur une date | `PARTITION BY DATE_TRUNC(jour, MONTH)` | `MONTH` ou `YEAR` ; une colonne `DATE` seule donne des partitions quotidiennes |
| Partition par heure d'ingestion | `PARTITION BY _PARTITIONDATE` | Pseudo-colonnes `_PARTITIONTIME` et `_PARTITIONDATE` ; incompatible avec `AS SELECT` |
| Partition par plage d'entiers | `PARTITION BY RANGE_BUCKET(client_id, GENERATE_ARRAY(0, 1000000, 10000))` | Début inclus, fin exclue, pas de 10 000 |
| Clustering | `CLUSTER BY client_id, statut` | Jusqu'à quatre colonnes de premier niveau, l'ordre compte |
| Options de gestion | `OPTIONS (partition_expiration_days = 400, require_partition_filter = TRUE, description = '...', labels = [('env', 'prod')])` | Expiration par partition et filtre de partition obligatoire, pour une table partitionnée seulement |
| Table qui expire | `OPTIONS (expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))` | Table supprimée à cette date |
| Colonne d'identité | `id INT64 GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1)` | Valeurs générées ; `BY DEFAULT` accepte aussi une valeur fournie ; des valeurs peuvent être sautées |
| Clés primaire et étrangère | `PRIMARY KEY (id) NOT ENFORCED`, `FOREIGN KEY (client_id) REFERENCES DATASET.CLIENTS(id) NOT ENFORCED` | Non vérifiées par BigQuery, qui s'en sert pour optimiser les requêtes : l'unicité reste à garantir |
| Créer depuis une requête (CTAS) | `CREATE TABLE DATASET.TABLE PARTITION BY jour CLUSTER BY client_id AS SELECT ...` | Schéma déduit de la requête ; `NOT NULL` n'est pas propagé |
| Même schéma, sans données | `CREATE TABLE DATASET.T2 LIKE DATASET.T1` | Schéma et métadonnées copiés |
| Copie complète | `CREATE TABLE DATASET.T2 COPY DATASET.T1` | Schéma, métadonnées et données |
| Clone modifiable à faible coût | `CREATE TABLE DATASET.T_CLONE CLONE DATASET.T1` | Seules les données qui divergent de la source sont facturées ; utile pour les tests |
| Instantané en lecture seule | `CREATE SNAPSHOT TABLE DATASET.T_SNAP CLONE DATASET.T1 FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) OPTIONS (expiration_timestamp = ...)` | Photo figée de la table, dans la fenêtre de *time travel* |
| Restaurer depuis un instantané | `CREATE TABLE DATASET.T_RESTAUREE CLONE DATASET.T_SNAP` | Nouvelle table modifiable |
| Table temporaire de script | `CREATE TEMP TABLE staging (id INT64)` | Nom sans dataset ; voir [DML et transactions](#googlesql-dml) |

### Modifier une table

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Ajouter une colonne | `ALTER TABLE DATASET.TABLE ADD COLUMN IF NOT EXISTS pays STRING` | `NULL` pour les lignes existantes ; pas de colonne `REQUIRED`, ni de colonne de partition ou de clustering |
| Supprimer une colonne | `ALTER TABLE DATASET.TABLE DROP COLUMN IF EXISTS ancien` | Métadonnées seulement : le stockage est libéré à la prochaine réécriture ; récupérable par *time travel* |
| Renommer une colonne | `ALTER TABLE DATASET.TABLE RENAME COLUMN nom TO nom_client` | Supprime les *aspects* Knowledge Catalog attachés à la colonne |
| Renommer une table | `ALTER TABLE DATASET.TABLE RENAME TO TABLE_V2` | Nouveau nom seul, sans dataset ; impossible sur une table Iceberg gérée |
| Élargir un type | `ALTER TABLE DATASET.TABLE ALTER COLUMN montant SET DATA TYPE NUMERIC` | Seulement vers un type moins restrictif : `INT64` → `NUMERIC`, `BIGNUMERIC`, `FLOAT64` ; `NUMERIC` → `BIGNUMERIC` ; `STRING(5)` → `STRING(7)` |
| Rendre une colonne facultative | `ALTER TABLE DATASET.TABLE ALTER COLUMN code DROP NOT NULL` | `REQUIRED` → `NULLABLE` ; l'inverse est impossible |
| Poser une valeur par défaut | `ALTER TABLE DATASET.TABLE ALTER COLUMN statut SET DEFAULT 'actif'` | Vaut pour les insertions suivantes |
| Décrire une colonne | `ALTER TABLE DATASET.TABLE ALTER COLUMN id SET OPTIONS (description = 'Identifiant client')` | Colonne de premier niveau seulement |
| Changer les options de la table | `ALTER TABLE DATASET.TABLE SET OPTIONS (partition_expiration_days = 180, require_partition_filter = TRUE)` | Réduire l'expiration supprime aussitôt les partitions trop anciennes |
| Retirer une option | `ALTER TABLE DATASET.TABLE SET OPTIONS (expiration_timestamp = NULL)` | La valeur `NULL` efface l'option |
| Changer le partitionnement | `CREATE TABLE DATASET.T2 PARTITION BY ... AS SELECT * FROM DATASET.T1`, puis bascule | Pas de `ALTER` possible ; le clustering, lui, se change par `bq update --clustering_fields` |
| Supprimer une table | `DROP TABLE IF EXISTS DATASET.TABLE` | Aussi `DROP VIEW`, `DROP MATERIALIZED VIEW`, `DROP EXTERNAL TABLE`, `DROP SNAPSHOT TABLE`, `DROP FUNCTION`, `DROP PROCEDURE` |

### Vues

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Vue logique | `CREATE OR REPLACE VIEW DATASET.VUE OPTIONS (description = '...') AS SELECT ...` | Requête réexécutée à chaque lecture, facturée sur les tables sous-jacentes |
| Vue matérialisée | `CREATE MATERIALIZED VIEW DATASET.VM PARTITION BY jour CLUSTER BY pays OPTIONS (enable_refresh = TRUE, refresh_interval_minutes = 60) AS SELECT jour, pays, SUM(montant) AS ca FROM DATASET.VENTES GROUP BY jour, pays` | Rafraîchissement automatique (défaut : activé, toutes les 30 min) ; partitionnement identique à celui de la table de base |
| Accepter des résultats un peu anciens | `OPTIONS (max_staleness = INTERVAL '4:0:0' HOUR TO SECOND)` | Vue servie sans relire les tables de base tant que le dernier rafraîchissement a moins de 4 h |
| Vue matérialisée non incrémentale | `OPTIONS (allow_non_incremental_definition = TRUE, max_staleness = ...)` | SQL plus large (jointures externes, `UNION`, fenêtres) ; `max_staleness` obligatoire ; chaque rafraîchissement recalcule tout ; option fixée à la création |
| Changer l'intervalle de rafraîchissement | `ALTER MATERIALIZED VIEW DATASET.VM SET OPTIONS (refresh_interval_minutes = 120)` | — |
| Donner un rôle en SQL | ``GRANT `roles/bigquery.dataViewer` ON VIEW DATASET.VUE TO "group:analystes@example.com"`` | Ressources `SCHEMA`, `TABLE`, `VIEW`, `EXTERNAL TABLE`, `PROJECT` ; retrait par `REVOKE` |

> [!TIP]
> Une **vue autorisée** lit un dataset source auquel ses lecteurs n'ont pas accès. L'autorisation ne se fait pas en DDL : on ajoute la vue à la liste d'accès du dataset source (console, `bq update --source` sur la définition JSON du dataset, ou API). Les utilisateurs reçoivent BigQuery Data Viewer sur le dataset **de la vue** et BigQuery Job User sur le projet qui exécute leurs requêtes.

### Tables externes, BigLake et Iceberg

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Table externe sur des CSV | `CREATE EXTERNAL TABLE DATASET.EXT OPTIONS (format = 'CSV', uris = ['gs://BUCKET/chemin/*.csv'], skip_leading_rows = 1)` | Schéma détecté si la liste des colonnes est omise ; lecture seule |
| Partitionnement Hive détecté | `CREATE EXTERNAL TABLE DATASET.EXT WITH PARTITION COLUMNS OPTIONS (format = 'PARQUET', uris = ['gs://BUCKET/ventes/*'], hive_partition_uri_prefix = 'gs://BUCKET/ventes', require_hive_partition_filter = TRUE)` | Colonnes déduites de chemins `.../jour=2026-06-01/pays=FR/...` ; les lister dans `WITH PARTITION COLUMNS (jour DATE, pays STRING)` pour les typer |
| Table BigLake (accès délégué) | `` CREATE EXTERNAL TABLE DATASET.EXT WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID` OPTIONS (format = 'PARQUET', uris = [...], max_staleness = INTERVAL 4 HOUR, metadata_cache_mode = 'AUTOMATIC') `` | Les utilisateurs n'ont plus besoin de droits sur le bucket ; cache de métadonnées. `WITH CONNECTION DEFAULT` utilise la connexion par défaut |
| Table d'objets (fichiers non structurés) | `CREATE EXTERNAL TABLE DATASET.DOCS WITH CONNECTION DEFAULT OPTIONS (object_metadata = 'SIMPLE', uris = ['gs://BUCKET/pdf/*'])` | Une ligne de métadonnées par objet, entrée des fonctions `AI.*` |
| Table Iceberg gérée | `CREATE TABLE DATASET.ICE (id INT64, jour DATE) CLUSTER BY id WITH CONNECTION DEFAULT OPTIONS (file_format = 'PARQUET', table_format = 'ICEBERG', storage_uri = 'gs://BUCKET/ice/')` | Données Parquet dans le bucket du client, DML et streaming complets ; ni `COPY`, ni `CLONE`, ni `SNAPSHOT`, ni renommage |
| Publier l'instantané Iceberg pour d'autres moteurs | `EXPORT TABLE METADATA FROM DATASET.ICE` | Métadonnées Iceberg V2 écrites sous `storage_uri`, lisibles par Spark ; facturé en slots Enterprise |

### Fonctions, procédures, sécurité par ligne

| Objectif | Syntaxe | Résultat |
|---|---|---|
| UDF SQL persistante | `CREATE OR REPLACE FUNCTION DATASET.ttc(ht NUMERIC, taux NUMERIC) RETURNS NUMERIC AS (ht * (1 + taux))` | Appel `DATASET.ttc(prix, 0.2)` depuis toute requête |
| UDF temporaire | `CREATE TEMP FUNCTION norm(s STRING) AS (LOWER(TRIM(s)));` | Vit le temps de la requête ; nom sans dataset |
| UDF JavaScript | `CREATE TEMP FUNCTION f(x FLOAT64) RETURNS FLOAT64 LANGUAGE js AS r"""return x * 2;""";` | `RETURNS` obligatoire ; plus lente qu'une UDF SQL |
| UDF Python | `CREATE FUNCTION DATASET.f(x FLOAT64) RETURNS FLOAT64 LANGUAGE python OPTIONS (entry_point = 'f', runtime_version = 'python-3.11', packages = ['pandas==2.2']) AS r"""..."""` | Exécutée dans un conteneur géré |
| Fonction distante | `` CREATE FUNCTION DATASET.f(x STRING) RETURNS STRING REMOTE WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID` OPTIONS (endpoint = 'https://...') `` | Appelle un service Cloud Run par lots de lignes |
| Fonction de table (TVF) | `CREATE OR REPLACE TABLE FUNCTION DATASET.ventes_de(j DATE) AS SELECT * FROM DATASET.VENTES WHERE jour = j` | `SELECT * FROM DATASET.ventes_de('2026-06-01')` : une vue paramétrée |
| Procédure stockée | `CREATE OR REPLACE PROCEDURE DATASET.purge(IN jours INT64, OUT nb INT64) BEGIN ... END` | Script SQL réutilisable, appelé par `CALL` |
| Politique d'accès aux lignes | `CREATE ROW ACCESS POLICY fr ON DATASET.TABLE GRANT TO ("group:equipe-fr@example.com") FILTER USING (pays = 'FR')` | Chaque groupe ne voit que ses lignes ; qui n'est couvert par aucune politique ne voit **rien** |
| Politique par utilisateur | `FILTER USING (email = SESSION_USER())` | Chacun voit ses propres lignes |
| Retirer les politiques | `DROP ROW ACCESS POLICY fr ON DATASET.TABLE` ; `DROP ALL ROW ACCESS POLICIES ON DATASET.TABLE` | La dernière politique d'une table ne part qu'avec `DROP ALL` |

Contexte : [BigQuery : organiser les tables](#organiser-bigquery), [GoogleSQL : DML et transactions](#googlesql-dml), [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture), [BigQuery](#bigquery).
