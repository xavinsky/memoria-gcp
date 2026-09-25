---
title: Lakehouse
subgroup: Analytique
icon: categories/data-analytics
aka: BigLake (BigLake metastore pour le catalogue)
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 16, y: 16, w: 520, h: 268}
  nodes:
    bq: {label: BigQuery, sub: "SQL, tables gérées", icon: produits/bigquery, x: 40, y: 40, w: 210}
    spark: {label: Managed Spark, sub: lecture et écriture, icon: categories/data-analytics, x: 290, y: 40, w: 210}
    ext: {label: Moteurs externes, sub: "Trino, Flink, Spark", external: true, x: 576, y: 40, w: 170}
    lh: {label: Lakehouse, sub: catalogue Iceberg REST, icon: categories/data-analytics, focus: true, x: 150, y: 124, w: 240, h: 70}
    gcs: {label: Cloud Storage, sub: "fichiers Parquet, Iceberg", icon: produits/cloud-storage, x: 150, y: 214, w: 240}
  flows:
    - {from: gcs, to: lh, text: "Les données restent en fichiers Apache Iceberg dans les buckets ; le catalogue n'en gère que les métadonnées"}
    - {from: lh, to: bq, from_side: top, from_offset: -60, text: "BigQuery lit et écrit les tables du catalogue en SQL, sous la forme projet.catalogue.espace.table"}
    - {from: lh, to: spark, from_side: top, from_offset: 60, text: "Managed Service for Apache Spark utilise le catalogue comme metastore de ses jobs"}
    - {from: ext, to: lh, from_side: bottom, to_side: right, text: "Un moteur open source s'authentifie sur le point de terminaison Iceberg REST et voit les mêmes tables"}
    - {from: lh, to: gcs, control: true, from_side: bottom, from_offset: 60, to_side: top, to_offset: 60, text: "La gestion des tables compacte les fichiers et ramasse les instantanés périmés"}
docs:
  Page produit: https://cloud.google.com/products/lakehouse
  Documentation: https://docs.cloud.google.com/lakehouse/docs
  Présentation: https://docs.cloud.google.com/lakehouse/docs/introduction
  Concepts clés: https://docs.cloud.google.com/lakehouse/docs/key-concepts
  Point de terminaison Iceberg REST: https://docs.cloud.google.com/lakehouse/docs/about-iceberg-rest-catalog-endpoint
  API REST: https://docs.cloud.google.com/lakehouse/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/biglake
  Bibliothèques clientes: https://docs.cloud.google.com/lakehouse/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/biglake/latest
  Quotas et limites: https://docs.cloud.google.com/lakehouse/docs/quotas
  Tarifs BigQuery: https://cloud.google.com/bigquery/pricing
  Tarifs Cloud Storage: https://cloud.google.com/storage/pricing
  Notes de version: https://docs.cloud.google.com/lakehouse/docs/release-notes
---

## Ce que c'est

Couche de **catalogue et de gestion de tables ouvertes** au-dessus de Cloud Storage : les données restent dans des fichiers **Apache Iceberg**, et plusieurs moteurs les lisent et les écrivent sans copie ni synchronisation de métadonnées.

- **Catalogue d'exécution Lakehouse** (*Lakehouse runtime catalog*) : service de métadonnées serverless, source de vérité unique pour les tables. Il s'expose de trois façons : le **point de terminaison Apache Iceberg REST** (la voie standard, pour Spark, Flink, Trino), un catalogue Iceberg adossé directement à BigQuery, et un **point de terminaison Hive** pour les charges qui attendent une interface de metastore Hive.
- **Séparation stockage / calcul** : le stockage est celui de Cloud Storage, le calcul celui du moteur qui interroge. Une table porte le nom `PROJECT_ID.CATALOG.NAMESPACE.TABLE` vue depuis BigQuery, et un chemin `bl://projects/PROJECT_ID/catalogs/CATALOG_ID` vu depuis un moteur open source.
- **Types de tables** : tables Iceberg créées depuis un moteur open source (écriture par ce moteur, lecture par BigQuery) ; tables Iceberg gérées par BigQuery, qui prend en charge la disposition des fichiers et l'optimisation ; tables natives BigQuery rattachées au catalogue ; tables externes en lecture seule.
- **Fonctions de table Iceberg** : évolution du schéma et du partitionnement sans réécriture, *time travel* vers un instantané ou une date, mise en cache des métadonnées, compactage et ramasse-miettes automatiques sur les tables gérées.
- **Sécurité et gouvernance** : *credential vending* — le catalogue délivre au moteur des jetons courts, limités aux chemins nécessaires à la requête — contrôle d'accès IAM et par table, et enregistrement automatique des tables dans Knowledge Catalog pour la traçabilité et la recherche.
- **Lakehouse sans frontières** (*borderless*) : synchronisation des métadonnées de catalogues externes (AWS Glue, Databricks Unity Catalog, Snowflake Horizon, SAP BDC) pour interroger ces données sans les déplacer.
- **Facturation** : pas de tarif propre au catalogue ; on paie le stockage Cloud Storage et le calcul du moteur qui exécute la requête.

## À quoi ça sert

- Construire un *lakehouse* ouvert : une seule copie des données en Iceberg sur Cloud Storage, interrogée par [BigQuery](#bigquery), [Spark](#managed-service-for-apache-spark), Flink ou Trino.
- Remplacer un metastore Hive autogéré par un service managé, sans changer les jobs Spark ou Hive existants.
- Organiser un entrepôt en couches (brut, nettoyé, exposé) où seules les tables de la couche exposée sont servies par BigQuery.
- Interroger des données restées chez un autre fournisseur ou dans un autre catalogue, sans migration.

**À éviter** quand les données n'ont qu'un seul consommateur et qu'il s'agit de BigQuery : les tables natives BigQuery sont plus simples et plus rapides (voir [Choisir une base de données](#choisir-une-base)). À éviter aussi pour du transactionnel à faible latence : Iceberg est un format analytique, les écritures se font par instantanés.

> [!WARNING]
> Les interfaces ne portent pas le nom du produit : les API, les bibliothèques clientes, les commandes `gcloud` et les rôles IAM s'appellent `biglake`, et le catalogue d'exécution apparaît sous le nom `BigLake metastore` dans une partie des messages et des paramètres.

## Alternatives en logiciel libre

- **Apache Iceberg** : le format de table lui-même, indépendant de tout fournisseur ; c'est exactement ce que stocke Lakehouse.
- **Apache Polaris** et **Project Nessie** : catalogues Iceberg REST autogérés, Nessie ajoutant un versionnement par branches à la Git.
- **Apache Gravitino** : catalogue de métadonnées fédéré au-dessus de plusieurs sources et formats.
- **Apache Hive Metastore** : le metastore historique, encore attendu par beaucoup d'outils.
- **Trino** : moteur SQL distribué qui interroge les tables Iceberg d'un catalogue partagé.
- **Apache Hudi**, **Delta Lake** : formats de tables concurrents d'Iceberg, avec mises à jour et *time travel*.
