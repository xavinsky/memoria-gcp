---
title: BigQuery Migration Service
subgroup: Migration et hybride
icon: categories/migration
schema:
  size: [760, 330]
  zones:
    - {label: Entrepôt existant, x: 6, y: 90, w: 186, h: 150}
    - {label: Projet GCP, x: 212, y: 10, w: 534, h: 310}
  nodes:
    src: {label: Entrepôt source, sub: "Teradata, Redshift…", external: true, x: 18, y: 130, w: 162, h: 64}
    gcs: {label: Cloud Storage, sub: "journaux, SQL, métadonnées", icon: produits/cloud-storage, x: 236, y: 132, w: 230}
    bqms: {label: BigQuery Migration Service, sub: "évaluation, traduction SQL", icon: categories/migration, focus: true, x: 490, y: 30, w: 248, h: 64}
    rep: {label: Data Studio, sub: "rapport d'évaluation", icon: categories/business-intelligence, x: 236, y: 30, w: 230}
    dts: {label: Data Transfer Service, sub: "connecteurs de migration", icon: produits/bigquery, x: 236, y: 244, w: 230}
    bq: {label: BigQuery, sub: "tables et SQL traduit", icon: produits/bigquery, x: 490, y: 244, w: 248}
  flows:
    - {from: src, to: gcs, text: "L'outil dwh-migration-dumper extrait les métadonnées et les journaux de requêtes de l'entrepôt ; les scripts SQL à traduire sont déposés dans le même bucket"}
    - {from: gcs, to: bqms, text: "Un job d'évaluation ou de traduction par lots lit les fichiers du bucket"}
    - {from: bqms, to: rep, text: "L'évaluation écrit ses résultats dans un dataset BigQuery et produit un rapport Data Studio : coût cible, requêtes, dépendances, plan de migration"}
    - {from: bqms, to: bq, text: "Le SQL traduit en GoogleSQL est déployé dans BigQuery : DDL des tables, vues, procédures, requêtes"}
    - {from: src, to: dts, from_side: bottom, to_side: left, text: "Le BigQuery Data Transfer Service copie le schéma et les données, avec un agent de migration pour Teradata"}
    - {from: dts, to: bq, text: "Chargement des tables dans BigQuery, avec partitionnement et clustering choisis dans le schéma cible"}
captures:
  - image: https://docs.cloud.google.com/static/bigquery/images/sql-translation-code-tab.png
    page: https://docs.cloud.google.com/bigquery/docs/batch-sql-translator
    legende: "Détail d'un job de traduction par lots : fichiers SQL du bucket, entrée Teradata et sortie GoogleSQL côte à côte, suggestions de Gemini"
  - image: https://docs.cloud.google.com/static/bigquery/images/assessment-report.png
    page: https://docs.cloud.google.com/bigquery/docs/migration-assessment
    legende: "Rapport d'évaluation d'un entrepôt Teradata : volumétrie existante, optimisations possibles dans BigQuery, taux de traduction automatique et durée de transfert estimée"
docs:
  Présentation de la migration: https://docs.cloud.google.com/bigquery/docs/migration-intro
  Page des services de migration: https://cloud.google.com/solutions/data-migration
  Schéma et données: https://docs.cloud.google.com/bigquery/docs/migration/schema-data-overview
  Évaluation de migration: https://docs.cloud.google.com/bigquery/docs/migration-assessment
  Traducteur SQL par lots: https://docs.cloud.google.com/bigquery/docs/batch-sql-translator
  Traducteur SQL interactif: https://docs.cloud.google.com/bigquery/docs/interactive-sql-translator
  Dialectes SQL pris en charge: https://docs.cloud.google.com/bigquery/docs/enable-sql-translations
  Migration Teradata: https://docs.cloud.google.com/bigquery/docs/migration/teradata-overview
  Transfert Snowflake: https://docs.cloud.google.com/bigquery/docs/migration/snowflake-transfer
  API REST: https://docs.cloud.google.com/bigquery/docs/reference/migration/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/bq/migration-workflows
  Client Python: https://docs.cloud.google.com/python/docs/reference/bigquerymigration/latest
  Quotas et limites: https://docs.cloud.google.com/bigquery/quotas
  Tarifs du Data Transfer Service: https://cloud.google.com/bigquery/pricing
---

## Ce que c'est

Ensemble d'outils intégrés à BigQuery pour migrer un entrepôt de données existant : évaluation, traduction du SQL, transfert des données. On le trouve dans la console BigQuery, menu **Migration**. Google Cloud le présente commercialement, avec les programmes d'accompagnement, sous le nom *Data Analytics Migration Services*.

- **Sources** : Amazon Redshift, Hadoop, Hive et Spark, IBM Netezza, Oracle et Exadata, Snowflake, Teradata. L'évaluation couvre aussi Databricks et Informatica [!PREVERSION].
- **Extraction** : l'outil en ligne de commande open source `dwh-migration-dumper` lit les métadonnées (DDL, statistiques) et les journaux de requêtes de la source et produit une archive ZIP à déposer dans Cloud Storage. Il sert à la fois à l'évaluation et à la traduction.
- **Évaluation** (*migration assessment*) : un job analyse les fichiers extraits et écrit ses résultats dans un dataset BigQuery. Un rapport **Data Studio** en tire le coût de possession dans BigQuery (édition, engagement de *slots*), les tables inutilisées, les candidates au partitionnement et au clustering, le taux de traduction automatique des requêtes et un plan de migration par vagues.
- **Traduction SQL** vers GoogleSQL, sous trois formes : le **traducteur interactif** dans l'éditeur de requêtes (une requête à la fois) ; le **traducteur par lots**, qui traduit des dossiers de scripts depuis un bucket et renvoie les fichiers traduits, un rapport CSV des erreurs et une table de correspondance des noms ; l'**API de traduction**, appelable depuis un pipeline. Des fichiers YAML de configuration réécrivent la sortie (casse, préfixes, renommages), et Gemini propose des corrections pour les erreurs restantes.
- **Dialectes** : Redshift, HiveQL, Netezza, Snowflake et Teradata (dont BTEQ et TPT).
- [!PREVERSION] **Autres dialectes** : Oracle PL/SQL, SQL Server T-SQL, Azure Synapse, Spark SQL, Impala, Trino, PostgreSQL, MySQL, DB2, Greenplum, Vertica et SQLite.
- **Transfert des données** : délégué au **BigQuery Data Transfer Service**. Teradata passe par un agent de migration installé près de la source, qui extrait par partition avec Teradata Parallel Transporter ; Redshift passe par un déchargement vers S3 ; Snowflake par une zone de transit dans Cloud Storage en fichiers Parquet.
- **Validation** : l'outil open source *Data Validation Tool* compare les tables source et cible (nombres de lignes, agrégats, sommes de contrôle) après le transfert.
- **Limites** : 10 tâches de traduction actives par projet, 10 Mo par fichier source et 1 Go au total par job de traduction par lots, 1 Mo par requête interactive.
- **Facturation** : l'API de migration (évaluation et traduction) est gratuite, seul le stockage des fichiers dans Cloud Storage est facturé. L'orchestration des connecteurs de migration du Data Transfer Service (Teradata, Redshift, Snowflake) est gratuite ; les chargements dans des tables natives aussi, les fusions sont facturées au tarif BigQuery.

> [!TIP]
> La traduction par lots donne de bien meilleurs résultats quand on joint les métadonnées de la source : sans DDL, le traducteur ne connaît pas les colonnes et renvoie des erreurs `RelationNotFound` ou `AttributeNotFound` en cascade. Lancer `dwh-migration-dumper` avant la première traduction.

## À quoi ça sert

- Chiffrer et planifier la migration d'un entrepôt Teradata, Redshift ou Snowflake vers BigQuery, à partir de l'usage réel mesuré dans les journaux de requêtes.
- Convertir en masse des milliers de scripts, vues et procédures stockées vers GoogleSQL, puis reprendre à la main la part non traduite.
- Traduire au fil de l'eau une requête isolée d'un analyste habitué à un autre dialecte.
- Copier le schéma et l'historique des tables, puis tenir la cible à jour par transferts incrémentaux jusqu'à la bascule.

**À éviter** pour migrer une base transactionnelle (MySQL, PostgreSQL, Oracle OLTP) vers Cloud SQL ou AlloyDB : c'est le rôle de [Database Migration Service](#database-migration-service). Pour une réplication continue d'une base de production vers BigQuery, préférer [Datastream](#datastream). Pour des traitements Spark ou Hadoop qu'on ne réécrit pas en SQL, la cible est [Managed Service for Apache Spark](#managed-service-for-apache-spark), pas la traduction.

## Alternatives en logiciel libre

- **SQLGlot** : analyseur et traducteur SQL en Python, qui convertit entre une trentaine de dialectes (dont Teradata, Snowflake, Redshift et BigQuery) ; sans connaissance des métadonnées de la source.
- **dbt** (dbt Core, licence Apache 2.0) : pas un traducteur, mais le cadre où l'on réécrit et teste les transformations une fois le SQL porté.
- **Data Validation Tool** et **dwh-migration-tools** : les outils d'extraction et de validation du service sont eux-mêmes publiés en open source par Google et utilisables seuls.
- **Apache NiFi** ou **Meltano** : copie des données d'un entrepôt source vers BigQuery, sans évaluation ni traduction.
