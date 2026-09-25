---
title: Managed Service for Apache Airflow
subgroup: Analytique
icon: categories/data-analytics
aka: Cloud Composer
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 130, y: 16, w: 616, h: 268}
  nodes:
    dev: {label: Data engineer, sub: DAG Python, external: true, x: 4, y: 120, w: 124}
    bucket: {label: Cloud Storage, sub: dossier dags/, icon: produits/cloud-storage, x: 150, y: 120, w: 170}
    airflow: {label: Managed Airflow, sub: "planificateur, workers", icon: categories/data-analytics, focus: true, x: 364, y: 104, w: 200, h: 88}
    bq: {label: BigQuery, sub: requêtes SQL, icon: produits/bigquery, x: 580, y: 36, w: 160}
    spark: {label: Managed Spark, sub: batch PySpark, icon: categories/data-analytics, x: 580, y: 120, w: 160}
    df: {label: Dataflow, sub: job par lots, icon: categories/data-analytics, x: 580, y: 204, w: 160}
    logs: {label: Cloud Logging, sub: journaux des tâches, icon: categories/observability, x: 364, y: 224, w: 200}
  flows:
    - {from: dev, to: bucket, text: "Le fichier Python du DAG est déposé dans le dossier dags/ du bucket de l'environnement"}
    - {from: bucket, to: airflow, text: "Le processeur de DAG analyse le fichier, le planificateur en déduit les exécutions à lancer"}
    - {from: airflow, to: bq, control: true, from_side: right, from_offset: -30, text: "Une tâche soumet une requête BigQuery et attend son résultat"}
    - {from: airflow, to: spark, control: true, from_side: right, text: "Une autre tâche lance un batch Spark, la dépendance entre les deux étant décrite dans le DAG"}
    - {from: airflow, to: df, control: true, from_side: right, from_offset: 30, text: "Une troisième tâche démarre un job Dataflow à partir d'un modèle"}
    - {from: airflow, to: logs, text: "Les journaux de chaque tâche partent dans Cloud Logging et dans le bucket de l'environnement"}
captures:
  - image: https://docs.cloud.google.com/static/composer/docs/images/composer-investigation-dags-list-failed-runs.png
    page: https://docs.cloud.google.com/composer/docs/composer-3/troubleshoot-tasks-and-dag-runs-with-agent
    legende: "Onglet DAGs d'un environnement dans la console : état de chaque DAG, dernière exécution, exécutions réussies et en échec"
  - image: https://docs.cloud.google.com/static/composer/docs/images/graph-view.png
    page: https://docs.cloud.google.com/composer/docs/composer-3/run-hadoop-wordcount-job
    legende: "Interface web d'Airflow : vue graphe d'un DAG et de ses trois tâches, avec le détail d'une tâche au survol"
docs:
  Page produit: https://cloud.google.com/products/managed-service-for-apache-airflow
  Documentation: https://docs.cloud.google.com/composer/docs
  Présentation (Gen 3): https://docs.cloud.google.com/composer/docs/composer-3/composer-overview
  Architecture d'un environnement: https://docs.cloud.google.com/composer/docs/composer-3/environment-architecture
  Écrire des DAG: https://docs.cloud.google.com/composer/docs/composer-3/write-dags
  Opérateurs Google Cloud pour Airflow: https://airflow.apache.org/docs/apache-airflow-providers-google/stable/index.html
  API REST: https://docs.cloud.google.com/composer/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/composer
  Bibliothèques clientes: https://docs.cloud.google.com/composer/docs/apis
  Client Python: https://docs.cloud.google.com/python/docs/reference/composer/latest
  Quotas et limites: https://docs.cloud.google.com/composer/quotas
  Tarifs: https://cloud.google.com/products/managed-service-for-apache-airflow/pricing
  Notes de version: https://docs.cloud.google.com/composer/docs/release-notes
---

## Ce que c'est

**Apache Airflow** exploité par Google : on décrit des workflows en Python, le service fournit l'infrastructure qui les planifie et les exécute.

- **DAG** (*Directed Acyclic Graph*) : un fichier Python déclare des tâches et leurs dépendances. Chaque tâche appelle un **opérateur** — une requête BigQuery, un job Dataflow, un pod Kubernetes, un appel HTTP, un envoi de courriel. Un DAG se déclenche à l'horaire, à la main, ou sur un événement comme le dépôt d'un fichier dans un bucket.
- **Environnement** : un déploiement Airflow isolé, dans une région, reposant sur un cluster **GKE** géré par le service. Il réunit les composants Airflow (planificateur, processeur de DAG, *workers* autoscalés, *triggerer*, serveur web), une base de données de métadonnées gérée, et un **bucket Cloud Storage** qui contient les dossiers `dags/`, `plugins/`, `data/` et `logs/`. Plusieurs environnements peuvent cohabiter dans un même projet.
- **Deux interfaces** : la console Google Cloud (liste des DAG, exécutions, journaux) et l'interface web native d'Airflow, propre à chaque environnement ; côté ligne de commande, `gcloud composer` relaie les commandes de la CLI Airflow.
- **Extensibilité** : dépendances Python installées depuis PyPI ou un dépôt privé (Artifact Registry), plugins Airflow personnalisés, options de configuration Airflow modifiables — sauf une liste d'options bloquées par le service.
- **Réseau et sécurité** : environnements à IP publique ou privée, rattachement à un VPC, VPC partagé, VPC Service Controls, CMEK. Les droits se donnent par IAM au niveau du projet, et par le contrôle d'accès de l'interface Airflow à l'intérieur de l'environnement.
- **Génération 3** : la génération courante, qui propose des environnements Airflow 2 ou Airflow 3 ; un environnement Airflow 2 existant ne passe pas encore à Airflow 3 par mise à niveau. Les environnements des générations précédentes restent documentés à part.
- **Facturation** : en *milli-DCU-heures*, une unité qui agrège le vCPU, la mémoire et le stockage consommés par les composants de l'environnement — donc un coût de base tant que l'environnement existe, plus la part variable des workers autoscalés. S'ajoutent le stockage de la base Airflow et le trafic sortant.

## À quoi ça sert

- Orchestrer une chaîne de traitements qui traverse plusieurs services : extraction, chargement dans [BigQuery](#bigquery), job [Spark](#managed-service-for-apache-spark) ou [Dataflow](#dataflow), contrôle qualité, rafraîchissement d'un tableau de bord.
- Gérer les dépendances, les tentatives, les alertes et le rattrapage (*backfill*) d'exécutions manquées.
- Piloter des ressources éphémères : créer un cluster pour un job, le supprimer à la fin.
- Orchestrer au-delà de Google Cloud : les *providers* Airflow couvrent les autres fournisseurs, les bases de données et les systèmes sur site.

**À éviter** pour un déclenchement événementiel à la seconde ou à très forte fréquence : Airflow planifie des tâches, il ne réagit pas à un flux — préférer Eventarc, Cloud Run ou un pipeline [Dataflow](#dataflow). À éviter aussi pour un seul job périodique isolé : Cloud Scheduler, Cloud Run Jobs ou les requêtes planifiées de BigQuery coûtent bien moins cher qu'un environnement qui tourne en permanence.

> [!TIP]
> Le code d'un DAG est relu à chaque analyse du fichier : tout ce qui est écrit au niveau du module (requête, appel réseau, lecture de fichier) s'exécute en boucle, même quand le DAG ne tourne pas. Ce travail se place dans les tâches, pas dans le corps du fichier.

## Alternatives en logiciel libre

- **Apache Airflow** lui-même, installé sur un cluster Kubernetes avec son chart Helm ou son opérateur : mêmes DAG, mêmes opérateurs.
- **Dagster** : orchestration centrée sur les actifs de données produits plutôt que sur les tâches, avec typage et tests.
- **Prefect** : workflows en Python ordinaire, sans DAG déclaré à l'avance.
- **Argo Workflows** : enchaînement de conteneurs sur Kubernetes, décrit en YAML.
- **Apache DolphinScheduler** : ordonnanceur distribué avec édition graphique des workflows.
