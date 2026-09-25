---
title: "Batch : ETL ou ELT"
---

Un pipeline par lots se conçoit d'abord sur une question : **où a lieu la transformation ?** Avant le chargement, dans un moteur de traitement (*ETL*), ou après, en SQL dans l'entrepôt (*ELT*). Quand la destination est [BigQuery](#bigquery), l'ELT est le choix par défaut : le chargement est gratuit, le moteur SQL passe à l'échelle sans réglage, et les données brutes restent disponibles pour recalculer. L'ETL reprend l'avantage quand la transformation ne s'écrit pas en SQL.

![Architecture batch de référence : ELT et ETL vers BigQuery](../../svg/batch-etl-elt.svg)

Les fichiers arrivent dans un bucket [Cloud Storage](#cloud-storage) qui sert de zone brute. En ELT, un job de chargement les verse tels quels dans un dataset brut, puis [Dataform](#dataform) construit les tables métier en SQL. En ETL, [Dataflow](#dataflow), [Managed Service for Apache Spark](#managed-service-for-apache-spark) ou [Cloud Data Fusion](#cloud-data-fusion) lisent les fichiers, transforment, et écrivent directement le résultat. Les sources SaaS et les autres entrepôts passent souvent par BigQuery Data Transfer Service, sans fichier intermédiaire. L'enchaînement est piloté par un orchestrateur (voir [Orchestration](#orchestration)).

## ETL ou ELT

| | ELT : charger, puis SQL | ETL : transformer, puis charger |
|---|---|---|
| **Outils** | `bq load` ou `LOAD DATA`, puis [Dataform](#dataform) ou requêtes planifiées | [Dataflow](#dataflow), [Spark](#managed-service-for-apache-spark), [Data Fusion](#cloud-data-fusion) |
| **Coût** | Chargement gratuit ; transformations facturées comme des requêtes | Ressources du moteur (workers, cluster, instance) en plus de BigQuery |
| **Rejouer** | Le brut est dans BigQuery : on relance le SQL | Il faut relire les fichiers sources |
| **Logique** | SQL, UDF, fonctions distantes | Tout code : formats exotiques, appels d'API, dédoublonnage complexe |
| **Données sensibles** | Arrivent brutes dans l'entrepôt : à protéger dès le dataset brut | Filtrées ou masquées avant d'atterrir |
| **Destination** | BigQuery uniquement | N'importe quelle destination, plusieurs à la fois |

Questions qui départagent :

- **La transformation s'écrit-elle en SQL ?** Si oui, ELT. Jointures, agrégats, historisation et dédoublonnage par clé s'y prêtent très bien.
- **Faut-il retirer des données avant qu'elles n'atterrissent ?** Données personnelles hors périmètre, colonnes interdites : ETL, ou dé-identification en amont par [Sensitive Data Protection](#sensitive-data-protection).
- **Du code Spark existe-t-il déjà ?** Le garder sur Spark. Pour un pipeline neuf qui ne tient pas en SQL, Dataflow : même code en batch et en streaming, rien à provisionner (voir [Choisir un moteur de traitement](#choisir-un-moteur)).
- **Qui construit le pipeline ?** Data Fusion vise des profils sans code et des connecteurs d'entreprise (SAP, Salesforce), au prix d'une instance facturée en continu.

## Charger dans BigQuery

| Méthode | Mécanisme | Coût | Quand l'utiliser |
|---|---|---|---|
| **Job de chargement** (`bq load`, `LOAD DATA`) | Lit des fichiers Cloud Storage et les écrit en stockage BigQuery ; tout ou rien | Gratuit sur le pool de slots partagé | Cas général du batch |
| **Table externe** | Aucune copie : chaque requête lit les fichiers en place | Chaque requête paie le volume lu | Données qui changent souvent, lecture ponctuelle, ELT en une passe par `CREATE TABLE ... AS SELECT` (voir [Architecture lakehouse](#lakehouse-architecture)) |
| **BigQuery Data Transfer Service** | Transferts planifiés et gérés depuis des SaaS, d'autres entrepôts, Cloud Storage, S3, Azure | Selon la source ; les jobs créés comptent dans les quotas de chargement | Sources prises en charge, sans code (voir [Migrations et transferts](#migrations-transferts)) |
| **Storage Write API, type *pending*** | L'application écrit des lignes en gRPC, puis valide le flux d'un coup (*commit* atomique) | 2 Tio gratuits par mois, puis au volume | Lignes produites par du code, sans fichiers intermédiaires |
| **`INSERT ... SELECT`, `CREATE TABLE ... AS SELECT`** | Requête qui écrit dans une table | Volume lu par la requête | Données déjà dans BigQuery ou dans une table externe |

Le pool partagé ne garantit ni capacité ni débit. Un chargement qui doit tenir une échéance passe sur une réservation dont l'affectation est de type `PIPELINE`.

```bash
# Chargement de fichiers Parquet, schéma lu dans les fichiers
bq load --source_format=PARQUET DATASET.ventes "gs://BUCKET/ventes/2026-09-23/*.parquet"
```

```sql
-- Même chargement en SQL, utilisable dans un script ou une action Dataform
LOAD DATA INTO DATASET.ventes
FROM FILES (format = 'PARQUET', uris = ['gs://BUCKET/ventes/2026-09-23/*.parquet']);
```

## Formats de fichiers

| Format | Organisation | Chargement | Points forts | Limites |
|---|---|---|---|---|
| **Avro** | Lignes, schéma embarqué | Format préféré : blocs lus en parallèle même compressés | Typage, schéma qui évolue, rapide à écrire | Moins compact que Parquet pour l'analyse ; blocs de 16 Mo au plus |
| **Parquet** | Colonnes | Parallèle | Meilleure compression, lecture des seules colonnes utiles : format de référence d'un lac ou d'une table externe | Plus coûteux à écrire ligne par ligne |
| **ORC** | Colonnes | Parallèle par *stripe* (256 Mo ou moins conseillés) | Comparable à Parquet, fréquent dans l'écosystème Hive | Moins répandu hors Hadoop |
| **CSV** | Texte | Parallèle seulement non compressé | Universel | Ni types ni structures imbriquées ; séparateurs et retours à la ligne à échapper ; gzip seul, 4 Go au plus compressé |
| **JSON** (une ligne par objet) | Texte | Parallèle seulement non compressé | Structures imbriquées | Verbeux ; mêmes limites de compression que CSV |

Avro, Parquet et ORC se compressent par leur codec interne ; un fichier passé entier dans gzip n'est pas accepté. Pour CSV et JSON, gzip réduit la bande passante mais supprime la lecture parallèle.

## Idempotence et backfills

Un chargement **idempotent** donne le même résultat s'il est relancé : c'est ce qui rend les reprises et les *backfills* sans risque. Trois leviers :

- **Écraser une partition plutôt qu'ajouter.** Chaque exécution remplace la partition de sa date logique ; relancer ne crée pas de doublons.
- **Fusionner sur une clé.** `MERGE` sur la clé métier pour les mises à jour ; c'est ce que produit une table incrémentale Dataform avec une clé unique.
- **Fixer l'identifiant du job.** Un job dont l'ID existe déjà est refusé (erreur `duplicate`, 409) : un orchestrateur qui relance avec le même ID ne charge pas deux fois. Le refus vaut aussi après un échec : la reprise d'un job échoué prend un nouvel ID.

```bash
# Remplace uniquement la partition du 23 septembre (décorateur $AAAAMMJJ)
# --job_id est une option globale : elle se place avant la commande
bq --job_id=ventes_20260923 load --source_format=PARQUET --replace \
  'DATASET.ventes$20260923' "gs://BUCKET/ventes/2026-09-23/*.parquet"
```

Pour un backfill, le pipeline est paramétré par date et relancé partition par partition, ou par plages. Un job ne peut pas modifier plus de 4 000 partitions. BigQuery Data Transfer Service propose ses propres backfills sur un intervalle de dates. Garder les fichiers bruts dans Cloud Storage, avec une règle de cycle de vie vers une classe froide (voir [Classes de stockage Cloud Storage](#cloud-storage-classes)), permet de tout recalculer.

## Pièges

- **Quota de chargements par table.** 1 500 jobs par table et par jour, échecs compris, non modifiable ; 100 000 par projet. Un chargement par fichier qui arrive l'épuise vite : regrouper les fichiers par joker (`*`) dans un seul job, ou passer au streaming si la fraîcheur l'exige (voir [Streaming](#streaming)).
- **Coût du DML.** Un `UPDATE` ou un `MERGE` est facturé comme une requête, sur les colonnes lues de la table cible : sans filtre sur la colonne de partition, il relit toute la table. BigQuery n'exécute que deux DML de modification à la fois par table, en met 20 en file, et rejette les suivants. Des milliers de mises à jour ligne à ligne sont un contresens : charger dans une table d'attente, puis un seul `MERGE` filtré sur les partitions concernées (voir [Organiser BigQuery](#organiser-bigquery)).
- **Petits fichiers.** Un job accepte jusqu'à 10 millions de fichiers, mais des milliers de fichiers de quelques kilo-octets ralentissent le chargement et la lecture des tables externes, dont le simple listage peut prendre plusieurs minutes. Regrouper en amont en fichiers moins nombreux et plus gros, ou activer le cache de métadonnées des tables externes et BigLake.
- **Région.** Charger depuis un bucket situé dans une autre région que le dataset entraîne des frais de transfert : placer la zone brute au même endroit que BigQuery.
- **Dérive de schéma.** En ajout, un chargement peut seulement ajouter des colonnes ou rendre une colonne `REQUIRED` facultative ; tout autre changement exige d'écraser la table. Avro et Parquet portent leur schéma et limitent les surprises de l'auto-détection sur CSV.

> [!TIP]
> Une table externe sert aussi de sas d'ELT : déclarer les fichiers en table externe, puis un seul `INSERT ... SELECT` qui nettoie et type les colonnes en une passe, sans dataset brut intermédiaire.

## Alternatives en logiciel libre

- **dbt Core** (Apache 2.0) : l'ELT en SQL versionné, avec `ref()`, tests et tables incrémentales, comme Dataform ; des adaptateurs couvrent BigQuery, PostgreSQL, Trino, DuckDB et d'autres entrepôts.
- **SQLMesh** (Apache 2.0) : même démarche que dbt, avec des environnements virtuels et un calcul par intervalles de dates qui rend les *backfills* explicites.
- **dlt** (Apache 2.0) et **Meltano** (MIT) : l'extraction et le chargement depuis des API et des SaaS, en Python ou par connecteurs Singer ; le rôle de BigQuery Data Transfer Service, à planifier et à héberger soi-même.
- **Apache Spark** (Apache 2.0) : l'ETL en code sur de gros volumes ; le même moteur que Managed Service for Apache Spark, mais cluster, versions et reprise sur panne restent à la charge de l'équipe.
- **Apache Beam** (Apache 2.0) sur un *runner* Flink ou Spark : le code d'un pipeline Dataflow tourne sans réécriture, sans l'autoscaling ni le *shuffle* gérés de Dataflow.
- **Trino** (Apache 2.0) ou **DuckDB** (MIT) : le moteur SQL d'un ELT hors entrepôt, sur des fichiers Parquet ou des tables Iceberg ; Trino se répartit sur un cluster, DuckDB tient sur une seule machine.
- **Apache Hop** (Apache 2.0) : conception graphique des transformations, dans l'esprit de Cloud Data Fusion, avec exécution locale ou sur Spark, Flink et Dataflow par Beam.
