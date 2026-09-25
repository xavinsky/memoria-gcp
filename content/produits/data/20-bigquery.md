---
title: BigQuery
subgroup: Analytique
icon: produits/bigquery
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 16, w: 566, h: 268}
  nodes:
    sources: {label: Sources, sub: "applis, fichiers", external: true, x: 10, y: 122, w: 120}
    gcs: {label: Cloud Storage, sub: fichiers bruts, icon: produits/cloud-storage, x: 210, y: 50, w: 160}
    pubsub: {label: Pub/Sub, sub: événements, icon: categories/data-analytics, x: 210, y: 200, w: 160}
    bq: {label: BigQuery, sub: "tables, SQL", icon: produits/bigquery, focus: true, x: 404, y: 122, w: 140, h: 60}
    bi: {label: Looker, sub: tableaux de bord, icon: produits/looker, x: 584, y: 50, w: 158}
    ml: {label: Agent Platform, sub: "modèles, IA", icon: produits/vertex-ai, x: 584, y: 200, w: 158}
  flows:
    - {from: sources, to: gcs, text: "Dépôt des fichiers (CSV, Parquet, Avro) dans un bucket"}
    - {from: gcs, to: bq, text: "Chargement par lots (bq load, gratuit) ou lecture directe en table externe"}
    - {from: sources, to: pubsub, text: "Publication des événements en continu"}
    - {from: pubsub, to: bq, text: "Abonnement BigQuery : les messages sont écrits directement dans une table"}
    - {from: bq, to: bi, text: "Requêtes SQL des tableaux de bord et des analystes"}
    - {from: bq, to: ml, text: "BigQuery ML et appels aux modèles Gemini depuis le SQL"}
captures:
  - image: https://docs.cloud.google.com/static/bigquery/images/bq-studio-ui.png
    page: https://docs.cloud.google.com/bigquery/docs/bigquery-web-ui
    legende: "BigQuery Studio : explorateur des ressources à gauche, onglets de requêtes et de notebooks à droite"
  - image: https://docs.cloud.google.com/static/bigquery/images/query-results-ui.png
    page: https://docs.cloud.google.com/bigquery/docs/sandbox
    legende: "Résultats d'une requête dans la console"
docs:
  Page produit: https://cloud.google.com/bigquery
  Documentation: https://docs.cloud.google.com/bigquery/docs
  Référence GoogleSQL: https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax
  API REST: https://docs.cloud.google.com/bigquery/docs/reference/rest
  CLI bq: https://docs.cloud.google.com/bigquery/docs/reference/bq-cli-reference
  Bibliothèques clientes: https://docs.cloud.google.com/bigquery/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/bigquery/latest
  Quotas et limites: https://docs.cloud.google.com/bigquery/quotas
  Tarifs: https://cloud.google.com/bigquery/pricing
  Notes de version: https://docs.cloud.google.com/bigquery/docs/release-notes
---

## Ce que c'est

Entrepôt de données analytique **serverless** : aucune instance à dimensionner, on crée des datasets et des tables, puis on interroge en SQL (dialecte GoogleSQL).

- **Stockage et calcul séparés.** Les tables sont stockées en format colonnes sur le stockage distribué de Google ; les requêtes s'exécutent sur un moteur massivement parallèle qui alloue dynamiquement des unités de calcul, les **slots**.
- **Organisation** : projet → dataset (porte la région et les droits) → tables, vues, vues matérialisées, fonctions, modèles.
- **Ingestion** : chargement par lots depuis Cloud Storage (gratuit), écriture en continu par la Storage Write API, abonnement Pub/Sub vers BigQuery, transferts planifiés (BigQuery Data Transfer Service).
- **Données externes** : tables externes et tables BigLake sur des fichiers de Cloud Storage (Parquet, ORC, Avro, Iceberg), requêtes fédérées vers Cloud SQL, AlloyDB et Spanner.
- **Au-delà du SQL** : BigQuery ML pour entraîner et appeler des modèles en SQL, notebooks et DataFrames Python, accélération en mémoire par BI Engine.
- **Facturation** : stockage au volume (moins cher après 90 jours sans modification) ; calcul soit **à la demande** (au volume lu par la requête), soit **en capacité** (éditions, facturées en slots).

## À quoi ça sert

- Entrepôt de données central : historique de l'entreprise, reporting, tableaux de bord (Looker, Data Studio, Connected Sheets).
- Analyse ad hoc sur de gros volumes, du gigaoctet au pétaoctet, sans administration.
- Destination de pipelines batch et streaming (Dataflow, Pub/Sub, Datastream).
- Machine learning et IA générative au plus près des données, en SQL.

**À éviter** pour un usage transactionnel : mises à jour unitaires fréquentes, lectures ponctuelles par clé à la milliseconde. Préférer Cloud SQL, AlloyDB ou Spanner pour les transactions, Bigtable pour les accès par clé à très faible latence (voir [Choisir une base de données](#choisir-une-base)).

> [!TIP]
> Le coût d'une requête à la demande dépend des **colonnes lues**, pas des lignes renvoyées : `SELECT *` suivi de `LIMIT 10` lit toute la table. Partitionner et clusteriser les tables réduit le volume lu.

## Alternatives en logiciel libre

- **ClickHouse** : base analytique en colonnes, très rapide sur les agrégations ; la plus proche en usage.
- **Trino** + **Apache Iceberg** : moteur SQL distribué sur des tables ouvertes stockées dans un object storage ; l'équivalent d'un lakehouse BigQuery + BigLake.
- **Apache Druid**, **Apache Pinot** : analytique temps réel à faible latence sur des flux.
- **Apache Doris**, **StarRocks** : entrepôts MPP compatibles MySQL.
- **DuckDB** : moteur analytique embarqué, pour des volumes qui tiennent sur une machine.
