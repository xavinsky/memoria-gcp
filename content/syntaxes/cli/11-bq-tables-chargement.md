---
title: "bq : datasets, tables et chargement"
subgroup: bq
type: syntax
---

Les tables se désignent `DATASET.TABLE`, ou `PROJECT_ID:DATASET.TABLE` hors du projet courant. Un nom qui contient `$` (décorateur de partition) se met entre apostrophes.

### Datasets

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un dataset | `bq --location=REGION mk --dataset --description="..." --label=equipe:finance PROJECT_ID:DATASET` | L'emplacement est définitif ; sans `--location`, c'est l'emplacement par défaut du projet, à défaut la multirégion `US` |
| Expiration par défaut des tables | `bq --location=REGION mk --dataset --default_table_expiration=604800 DATASET` | Toute nouvelle table expire 7 jours après sa création ; `--default_partition_expiration` pour les partitions |
| Fenêtre de *time travel* réduite | `bq --location=REGION mk --dataset --max_time_travel_hours=48 DATASET` | 48 à 168 heures (7 jours par défaut) ; moins de stockage facturé en modèle physique |
| Facturer le stockage physique | `bq update --storage_billing_model=PHYSICAL DATASET` | Octets compressés facturés, time travel et fail-safe compris |
| Lister les datasets | `bq ls` puis `bq ls --filter='labels.equipe:finance'` | Datasets du projet courant, filtrés par libellé |
| Afficher un dataset et ses accès | `bq show --format=prettyjson DATASET` | Emplacement, expirations, liste `access` |
| Modifier les accès du dataset | `bq show --format=prettyjson DATASET > ds.json`, éditer `access`, puis `bq update --source=ds.json DATASET` | Liste d'accès remplacée par celle du fichier |
| Changer description ou libellé | `bq update --description="..." --set_label=equipe:data DATASET` | `--clear_label=CLE:VALEUR` retire un libellé |
| Supprimer un dataset et son contenu | `bq rm -r -f -d DATASET` | Sans `-r`, échec si le dataset contient des tables ; `-f` supprime la confirmation |
| Restaurer un dataset supprimé | `bq undelete DATASET` | Possible pendant la fenêtre de time travel |

### Tables et vues

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer une table, schéma en ligne | `bq mk --table DATASET.TABLE id:INTEGER,nom:STRING,maj:TIMESTAMP` | Colonnes `NULLABLE` ; pour `REQUIRED` ou `RECORD`, passer par un fichier |
| Créer une table, schéma en fichier | `bq mk --table --schema=schema.json --description="..." DATASET.TABLE` | Fichier JSON : `[{"name": "id", "type": "INTEGER", "mode": "REQUIRED"}, ...]` |
| Table partitionnée par jour et clusterisée | `bq mk --table --schema=schema.json --time_partitioning_field=jour --time_partitioning_type=DAY --clustering_fields=client_id,pays --require_partition_filter=true DATASET.TABLE` | `HOUR`, `MONTH`, `YEAR` possibles ; quatre colonnes de clustering au plus |
| Partitions qui expirent | `bq mk --table --schema=schema.json --time_partitioning_field=jour --time_partitioning_expiration=7776000 DATASET.TABLE` | Chaque partition supprimée 90 jours après sa date |
| Partitionnement par plage d'entiers | `bq mk --table --schema=schema.json --range_partitioning=client_id,0,100000,1000 DATASET.TABLE` | Forme `colonne,début,fin,pas` : 100 partitions de 1 000 identifiants |
| Table partitionnée par date d'ingestion | `bq mk --table --schema=schema.json --time_partitioning_type=DAY DATASET.TABLE` | Sans `--time_partitioning_field` : pseudo-colonne `_PARTITIONTIME` |
| Table qui expire | `bq mk --table --expiration=3600 --schema=schema.json DATASET.TMP` | Supprimée une heure après sa création |
| Créer une vue | `bq mk --use_legacy_sql=false --view='SELECT ... FROM DATASET.TABLE' DATASET.VUE` | Sans `--use_legacy_sql=false`, la vue est créée en SQL historique |
| Voir le schéma | `bq show --schema --format=prettyjson DATASET.TABLE > schema.json` | Fichier réutilisable par `bq mk` et `bq update` |
| Ajouter une colonne | `bq update DATASET.TABLE schema.json` | Le fichier contient le schéma complet, nouvelle colonne en fin, `NULLABLE` ou `REPEATED` ; supprimer ou retyper une colonne passe par `ALTER TABLE` |
| Changer expiration, description, libellés | `bq update --expiration=0 --description="..." --set_label=env:prod DATASET.TABLE` | `--expiration=0` retire l'expiration |
| Changer le clustering | `bq update --clustering_fields=client_id DATASET.TABLE` | Ne trie que les nouvelles données ; le partitionnement ne se change pas |
| Vider une table en gardant son schéma | ``bq query --use_legacy_sql=false 'TRUNCATE TABLE `DATASET.TABLE`'`` | Toutes les lignes supprimées, schéma et options conservés |
| Supprimer une table ou une vue | `bq rm -f -t DATASET.TABLE` | Récupérable par `bq cp` avec un décorateur temporel pendant la fenêtre de time travel |

### Charger des fichiers

| Objectif | Syntaxe | Résultat |
|---|---|---|
| CSV avec en-tête, schéma déduit | `bq load --source_format=CSV --skip_leading_rows=1 --autodetect DATASET.TABLE 'gs://BUCKET/rep/*.csv'` | Table créée si elle n'existe pas ; job de chargement gratuit sur le pool partagé |
| CSV avec schéma imposé | `bq load --source_format=CSV --skip_leading_rows=1 DATASET.TABLE gs://BUCKET/f.csv schema.json` | Schéma en troisième argument (fichier ou `col:TYPE,...`) |
| CSV particulier | `bq load --source_format=CSV -F ';' --encoding=ISO-8859-1 --null_marker='\N' --allow_quoted_newlines DATASET.TABLE gs://BUCKET/f.csv schema.json` | Séparateur, encodage, marqueur de NULL, retours à la ligne entre guillemets |
| Tolérer des lignes invalides | `bq load --source_format=CSV --max_bad_records=100 ...` | Jusqu'à 100 lignes rejetées sans faire échouer le job |
| JSON | `bq load --source_format=NEWLINE_DELIMITED_JSON --autodetect DATASET.TABLE 'gs://BUCKET/rep/*.json'` | Un objet JSON par ligne ; un tableau JSON unique est refusé |
| Parquet ou ORC | `bq load --source_format=PARQUET DATASET.TABLE 'gs://BUCKET/rep/*.parquet'` | Schéma lu dans les fichiers ; `ORC` de même |
| Avro | `bq load --source_format=AVRO --use_avro_logical_types=true DATASET.TABLE 'gs://BUCKET/rep/*.avro'` | Types logiques convertis (`timestamp-micros` → `TIMESTAMP`) au lieu de l'entier brut |
| Fichier local | `bq load --source_format=CSV --skip_leading_rows=1 DATASET.TABLE ./f.csv schema.json` | Un fichier par commande, sans joker ; pour de gros volumes, déposer d'abord sur Cloud Storage |
| Remplacer tout le contenu | `bq load --replace --source_format=PARQUET DATASET.TABLE 'gs://BUCKET/rep/*.parquet'` | Données et schéma écrasés ; `--replace_data` garde le schéma |
| Ajouter en élargissant le schéma | `bq load --noreplace --schema_update_option=ALLOW_FIELD_ADDITION --source_format=PARQUET DATASET.TABLE 'gs://BUCKET/rep/*.parquet'` | Colonnes nouvelles des fichiers ajoutées à la table |
| Recharger une seule partition | `bq load --replace --source_format=PARQUET 'DATASET.TABLE$20260131' 'gs://BUCKET/ventes/jour=2026-01-31/*.parquet'` | Seule la partition du 31 janvier est remplacée ; sans `--replace`, ajout dans la partition |
| Fichiers rangés en partitions Hive | `bq load --source_format=PARQUET --hive_partitioning_mode=AUTO --hive_partitioning_source_uri_prefix=gs://BUCKET/ventes DATASET.TABLE 'gs://BUCKET/ventes/*'` | Clés `jour=...`, `pays=...` du chemin ajoutées en colonnes ; `STRINGS` pour les garder en texte |

> [!WARNING]
> Un seul `*` par URI, jamais dans le nom du bucket. Mettre l'URI entre apostrophes pour que le shell ne développe pas le joker. Le bucket doit se trouver au même emplacement que le dataset.

### Tables externes

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Générer une définition | `bq mkdef --source_format=PARQUET 'gs://BUCKET/rep/*.parquet' > def.json` | Définition JSON à relire avant usage |
| Définition avec partitions Hive | `bq mkdef --source_format=PARQUET --hive_partitioning_mode=AUTO --hive_partitioning_source_uri_prefix=gs://BUCKET/ventes --require_hive_partition_filter=true 'gs://BUCKET/ventes/*' > def.json` | Filtre sur une clé de partition exigé dans chaque requête |
| Définition pour une table BigLake | `bq mkdef --connection_id=PROJECT_ID.REGION.CONNEXION --source_format=PARQUET 'gs://BUCKET/rep/*.parquet' > def.json` | Lecture par le compte de service de la connexion, pas par l'utilisateur ; cf. [Lakehouse](#lakehouse) |
| Créer la table externe | `bq mk --table --external_table_definition=def.json DATASET.EXT` | Données laissées sur Cloud Storage, lues à chaque requête |
| Définition en ligne, sans fichier | `bq mk --table --external_table_definition=id:INTEGER,nom:STRING@CSV=gs://BUCKET/f.csv DATASET.EXT` | Forme `SCHEMA@FORMAT=URI` |

### Exporter, copier, restaurer

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Exporter en CSV compressé | `bq extract --destination_format=CSV --compression=GZIP DATASET.TABLE 'gs://BUCKET/export/part-*.csv.gz'` | 1 Go au plus par fichier : le `*` répartit l'export sur plusieurs fichiers ; pas de colonne imbriquée ou répétée en CSV |
| Exporter en Parquet | `bq extract --destination_format=PARQUET --compression=ZSTD DATASET.TABLE 'gs://BUCKET/export/part-*.parquet'` | Parquet : `SNAPPY`, `GZIP` ou `ZSTD` ; Avro : `DEFLATE` ou `SNAPPY` ; JSON : `GZIP` |
| Exporter une partition | `bq extract --destination_format=AVRO 'DATASET.TABLE$20260131' 'gs://BUCKET/export/2026-01-31-*.avro'` | Seule la partition du jour exportée |
| Copier une table | `bq cp -n DATASET.TABLE DATASET2.TABLE` | `-n` refuse d'écraser, `-f` écrase sans demander, `-a` ajoute ; copie entre régions possible, avec frais de transfert |
| Fusionner plusieurs tables | `bq cp DATASET.T1,DATASET.T2 DATASET.TOTAL` | Tables sources de même schéma |
| Instantané (*snapshot*) | `bq cp --snapshot --no_clobber --expiration=2592000 DATASET.TABLE DATASET.TABLE_SNAP` | Lecture seule, facturé sur les seuls octets qui diffèrent de la table de base ; expire après 30 jours |
| Instantané d'un état passé | `bq cp --snapshot --no_clobber 'DATASET.TABLE@-3600000' DATASET.TABLE_SNAP` | État d'il y a une heure (décalage en millisecondes) |
| Clone modifiable | `bq cp --clone --no_clobber DATASET.TABLE DATASET.TABLE_CLONE` | Table inscriptible qui ne facture que ses propres modifications |
| Restaurer depuis un instantané | `bq cp --restore --no_clobber DATASET.TABLE_SNAP DATASET.TABLE_RESTAUREE` | Table standard, inscriptible ; `--force` à la place de `--no_clobber` pour écraser la table d'origine |
| Restaurer une table supprimée ou abîmée | `bq cp 'DATASET.TABLE@1767225600000' DATASET.TABLE_RESTAUREE` | État à cet horodatage en millisecondes (`date -d '2026-01-01 00:00:00Z' +%s000`), dans la fenêtre de time travel |

> [!TIP]
> Au-delà de la fenêtre de time travel, le *fail-safe* garde encore 7 jours les données supprimées, mais on ne peut ni les interroger ni les restaurer soi-même : la récupération passe par Cloud Customer Care. Il ne remplace pas un instantané.

Contexte : [BigQuery](#bigquery), [organiser les tables](#organiser-bigquery), [requêtes et jobs](#bq-requetes-jobs), [DDL BigQuery](#bigquery-ddl), [Cloud Storage](#cloud-storage), [batch, ETL et ELT](#batch-etl-elt).
