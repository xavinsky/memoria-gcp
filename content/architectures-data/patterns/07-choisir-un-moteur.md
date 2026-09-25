---
title: Choisir le moteur de traitement
---

Le moteur se choisit d'abord sur le **point de départ** : du code Spark à reprendre, des données déjà dans BigQuery qu'on transforme en SQL, un pipeline neuf à écrire (en particulier en continu), ou une équipe qui construit sans coder. Le modèle de facturation et la charge d'exploitation départagent ensuite.

![Arbre de décision : du point de départ au moteur de traitement](../../svg/choix-moteur-traitement.svg)

## Matrice de choix

| Moteur | Écriture | Lots / continu | Existant visé | Exploitation | Facturation |
|---|---|---|---|---|---|
| **[BigQuery](#bigquery) en SQL** (ELT) | SQL GoogleSQL, requêtes planifiées | Lots ; continu par les **requêtes continues** | Données déjà chargées dans BigQuery | Aucune | Octets lus (à la demande) ou slots (éditions) |
| **[Dataform](#dataform)** | Fichiers SQLX versionnés dans Git, dépendances par `ref()`, assertions | Lots planifiés, tables incrémentales | Entrepôt BigQuery ; équipes habituées à dbt | Aucune | Service gratuit ; seules les requêtes BigQuery sont facturées |
| **[Dataflow](#dataflow)** | Code Apache Beam (Java, Python, Go) ou modèles fournis | Les deux, même code ; exactement une fois par défaut | Pipelines Beam | Faible : workers créés et supprimés par job, autoscaling | Ressources des workers à la seconde, plus Shuffle et Streaming Engine ; FlexRS pour les lots différables |
| **[Managed Service for Apache Spark](#managed-service-for-apache-spark)** | PySpark, Spark SQL, Scala, R ; écosystème Hadoop sur clusters | Lots ; Spark Structured Streaming | Jobs Spark, Hive, Hadoop à reprendre sans réécriture | Clusters : dimensionnement, versions, initialisation ; serverless : faible | Clusters : VM Compute Engine plus frais de gestion ; serverless : DCU à la seconde |
| **[Cloud Data Fusion](#cloud-data-fusion)** | Graphique (Studio, Wrangler), plugins CDAP | Lots surtout, pipelines temps réel possibles | Outils ETL graphiques ; sources SAP, Salesforce, bases relationnelles | Une instance à maintenir ; exécution sur clusters Spark éphémères | Instance à la minute selon l'édition, tant qu'elle existe, plus les clusters |
| **Préparation de données BigQuery** | Graphique, suggestions de Gemini | Lots, planifiés par Dataform | Tables BigQuery à nettoyer | Aucune | Requêtes BigQuery |

- **Où tourne réellement le calcul.** Dataform et la préparation de données BigQuery produisent du SQL exécuté par BigQuery. Cloud Data Fusion compile ses pipelines en jobs Spark, ou pousse les transformations dans BigQuery (*pushdown*). Seuls Dataflow et Spark sont des moteurs à part entière.
- **Continu.** Dataflow est le choix par défaut dès qu'il faut du fenêtrage, de l'état, des données tardives ou un enrichissement au fil de l'eau (voir [Streaming](#streaming)). Les requêtes continues de BigQuery traitent en SQL les lignes qui arrivent dans une table et les exportent vers Pub/Sub, Bigtable ou Spanner, mais demandent une réservation Enterprise ou Enterprise Plus et n'acceptent qu'une partie du SQL (opérations avec état limitées).
- **Sans transformation**, pas de moteur : un abonnement BigQuery de Pub/Sub, [Datastream](#datastream) pour la réplication d'une base, ou BigQuery Data Transfer Service pour un chargement planifié (voir [CDC](#cdc) et [Migrations et transferts](#migrations-transferts)).

## Questions qui départagent

- **ETL ou ELT ?** Si les données peuvent être chargées brutes dans BigQuery, la transformation en SQL (ELT) évite un moteur de plus : chargement par lots gratuit, puis Dataform pour enchaîner les couches. L'ETL avec Dataflow ou Spark se justifie pour des formats exotiques, des appels à des services externes, du nettoyage qui ne s'écrit pas en SQL, ou quand les données brutes ne doivent pas entrer dans l'entrepôt (voir [Batch ETL / ELT](#batch-etl-elt)).
- **Dataflow ou Spark pour un pipeline neuf ?** Dataflow : pas de cluster, un même code pour les lots et le continu, autoscaling géré. Spark : quand l'équipe maîtrise déjà Spark, que les bibliothèques ou les notebooks existants sont en PySpark, ou que le même code doit tourner ailleurs. Le serverless de Managed Service for Apache Spark réduit alors l'écart d'exploitation.
- **Clusters Spark permanents ou éphémères ?** Éphémères, un par job ou par workflow, avec les données dans Cloud Storage ou BigQuery plutôt que dans HDFS. Un cluster permanent ne se justifie que pour un usage interactif soutenu.
- **Requêtes planifiées ou Dataform ?** Quelques requêtes indépendantes : requêtes planifiées de BigQuery. Un graphe de tables avec des dépendances, des tests de qualité, une revue de code et des environnements séparés : Dataform.
- **Cloud Data Fusion ou code ?** Data Fusion quand les pipelines sont construits par des profils non développeurs, ou quand ses connecteurs (SAP en particulier) évitent d'écrire un extracteur. Pour une équipe qui écrit du code, l'instance coûte en permanence sans apporter grand-chose.
- **Qui planifie ?** Aucun de ces moteurs n'orchestre des étapes hétérogènes (transfert, puis Spark, puis SQL, puis notification) : c'est le rôle de Managed Service for Apache Airflow ou de Workflows (voir [Orchestration](#orchestration)).

## Dataprep

Dataprep [!DECONSEILLE] (*Dataprep by Trifacta*) est un service de préparation visuelle de données **édité et exploité par Alteryx**, proposé sur Google Cloud Marketplace ; ses recettes s'exécutent sur Dataflow ou dans BigQuery. Alteryx le présente comme l'offre parallèle, pour Google Cloud, de son produit **Alteryx Designer Cloud**. Il ne fait pas partie du catalogue de Google : la page produit de Google renvoie vers BigQuery, et la documentation est celle d'Alteryx, dont les dernières notes de version publiées datent de juin 2024 (consulté en septembre 2026).

Pour un nouveau projet, la préparation visuelle se fait dans BigQuery Studio avec la **préparation de données BigQuery** (suggestions de Gemini, planification par Dataform), ou dans Cloud Data Fusion (Wrangler) quand les données ne sont pas encore dans BigQuery.

> [!WARNING]
> Un pipeline Dataprep existant dépend d'un contrat et d'un support Alteryx, non de Google. Le reprendre en Dataform (SQL) ou en préparation de données BigQuery supprime cette dépendance.

## Pièges

- **Réécrire du Spark qui fonctionne.** Migrer des jobs Spark vers Dataflow coûte une réécriture complète ; les faire tourner sur Managed Service for Apache Spark, avec des clusters éphémères ou en serverless, est presque immédiat.
- **Ajouter un moteur pour ce que BigQuery fait déjà.** Une jointure, un dédoublonnage ou une agrégation sur des tables BigQuery s'écrivent en SQL ; les faire sortir vers Dataflow ou Spark ajoute un transfert et un job à surveiller.
- **Laisser tourner une instance Data Fusion ou un cluster Spark inactif.** Les deux se facturent tant qu'ils existent, qu'un pipeline s'exécute ou non.
- **Choisir le modèle BigQuery sans regarder le volume lu.** Les transformations ELT lourdes et répétées sont souvent moins chères en éditions (slots) qu'à la demande ; l'organisation des tables compte autant (voir [BigQuery : organiser les tables](#organiser-bigquery)).

## Alternatives en logiciel libre

- **Apache Spark** (Apache 2.0) : le moteur de lots et de micro-lots le plus répandu, sur Kubernetes ou YARN ; même code que Managed Service for Apache Spark, sans les clusters éphémères ni le serverless gérés.
- **Apache Flink** (Apache 2.0) : le moteur de flux avec état, pour le terrain de Dataflow en continu ; il traite aussi les lots, mais son point fort reste le temps réel.
- **Apache Beam** (Apache 2.0) : le modèle de programmation de Dataflow, exécutable sur Flink ou Spark ; il garde le même code pour les lots et le continu, et laisse la porte ouverte à Dataflow.
- **Trino** (Apache 2.0) : SQL distribué sur des fichiers, des tables Iceberg et des bases fédérées ; l'équivalent le plus proche de BigQuery comme moteur de transformation SQL, cluster à dimensionner en plus.
- **DuckDB** (MIT) : moteur SQL en colonnes embarqué, sans serveur ; il suffit pour des transformations qui tiennent sur une machine, là où BigQuery ou Spark seraient surdimensionnés.
- **dbt Core** (Apache 2.0) : la couche de modélisation SQL au-dessus de Trino, Spark, DuckDB ou PostgreSQL, là où Dataform reste lié à BigQuery.
- **Apache Hop** (Apache 2.0) et **Apache NiFi** (Apache 2.0) : la construction sans code ; Hop pour l'ETL par lots, exécuté par Beam, NiFi pour l'acheminement continu d'enregistrements, dans le rôle de Cloud Data Fusion.
