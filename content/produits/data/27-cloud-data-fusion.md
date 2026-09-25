---
title: Cloud Data Fusion
subgroup: Analytique
icon: categories/data-analytics
schema:
  size: [760, 330]
  zones:
    - {label: Projet GCP, x: 160, y: 16, w: 586, h: 306}
  nodes:
    src: {label: Sources, sub: "bases, SaaS, SAP", external: true, x: 8, y: 40, w: 140}
    gcs: {label: Cloud Storage, sub: "fichiers bruts", icon: produits/cloud-storage, x: 180, y: 40, w: 200}
    cdf: {label: Cloud Data Fusion, sub: "Studio, plugins", icon: categories/data-analytics, focus: true, x: 180, y: 140, w: 200, h: 72}
    spark: {label: Managed Spark, sub: "cluster éphémère", icon: categories/data-analytics, x: 180, y: 250, w: 200}
    bq: {label: BigQuery, sub: "tables cibles", icon: produits/bigquery, x: 520, y: 40, w: 200}
    kc: {label: Knowledge Catalog, sub: "lignage des champs", icon: categories/data-analytics, x: 520, y: 250, w: 200}
  flows:
    - {from: src, to: cdf, to_offset: -60, text: "Conception : le plugin source lit un échantillon, que Wrangler nettoie colonne par colonne"}
    - {from: gcs, to: cdf, text: "Les fichiers déjà déposés dans le lac de données servent de seconde source au pipeline"}
    - {from: cdf, to: spark, control: true, text: "Au lancement, l'instance provisionne un cluster Managed Spark éphémère, lui soumet le pipeline compilé, puis le supprime"}
    - {from: src, to: spark, to_side: left, text: "À l'exécution, les tâches Spark relisent la source par le même plugin"}
    - {from: spark, to: bq, from_side: right, to_side: left, text: "Écriture des lignes transformées dans les tables cibles"}
    - {from: cdf, to: kc, to_side: top, text: "Publication du lignage, au niveau du jeu de données et du champ, dans Knowledge Catalog"}
captures:
  - image: https://docs.cloud.google.com/static/data-fusion/docs/images/quickstart/studio-details.png
    page: https://docs.cloud.google.com/data-fusion/docs/create-data-pipeline
    legende: "Studio : un pipeline déployé, ses nœuds source, transformation et puits, et la barre d'exécution"
  - image: https://docs.cloud.google.com/static/data-fusion/docs/images/tutorials/targeting-campaign-pipeline/customers-workspace-no-transforms.png
    page: https://docs.cloud.google.com/data-fusion/docs/tutorials/targeting-campaign-pipeline
    legende: "Wrangler : un fichier CSV chargé en grille, la liste des colonnes et le panneau des étapes de transformation"
docs:
  Page produit: https://cloud.google.com/data-fusion
  Documentation: https://docs.cloud.google.com/data-fusion/docs
  Présentation: https://docs.cloud.google.com/data-fusion/docs/concepts/overview
  Catalogue des plugins: https://cloud.google.com/data-fusion/plugins
  Types de plugins: https://docs.cloud.google.com/data-fusion/docs/concepts/plugins
  API REST: https://docs.cloud.google.com/data-fusion/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/beta/data-fusion
  Client Python: https://docs.cloud.google.com/python/docs/reference/datafusion/latest
  Quotas et limites: https://docs.cloud.google.com/data-fusion/quotas
  Tarifs: https://cloud.google.com/data-fusion/pricing
  Notes de version: https://docs.cloud.google.com/data-fusion/docs/release-notes
---

## Ce que c'est

Service d'intégration de données **graphique** : on assemble un pipeline en reliant des nœuds (source, transformation, puits) dans une interface web, sans écrire de code. Il repose sur le projet libre **CDAP**.

- **Instance** : l'unité de déploiement, créée dans une région et dans une édition — Developer, Basic ou Enterprise. Les services qui gèrent le cycle de vie des pipelines tournent dans un **projet locataire** (*tenant project*) séparé, qui hérite de la configuration réseau du projet client.
- **Deux plans** : la *console* pilote l'instance elle-même (création, redémarrage, mise à niveau) ; le **Studio** est l'interface de conception et d'exécution des pipelines.
- **Pipeline** : un graphe orienté acyclique de nœuds. Chaque nœud est un **plugin** — source par lots ou en flux, transformation, agrégat, puits, collecteur d'erreurs, action. Le *Hub* liste les plugins disponibles et les pipelines d'exemple.
- **Wrangler** : préparation interactive sur un échantillon ; la suite de directives produite (la *recette*) devient un nœud de transformation du pipeline.
- **Exécution** : le pipeline est compilé en job Spark. Par défaut, Cloud Data Fusion provisionne un cluster [Managed Service for Apache Spark](#managed-service-for-apache-spark) éphémère dans le projet client, exécute le pipeline, puis supprime le cluster. Un **profil de calcul** décrit cet environnement (provisionneur, mémoire, nombre de nœuds). Les transformations peuvent aussi être **poussées dans BigQuery** (*pushdown*) plutôt qu'exécutées dans Spark.
- **Namespaces** : partitions logiques d'une instance, chacune avec ses pipelines, ses métadonnées et son compte de service.
- **Facturation** : à la minute, du moment où l'instance est créée à celui où elle est supprimée, au tarif de son édition ; l'exécution est facturée à part, au prix des clusters Spark et des autres ressources consommées.

## À quoi ça sert

- Ingestion depuis un grand catalogue de systèmes : bases relationnelles, SAP (ERP, BW, ODP, SuccessFactors), Salesforce, ServiceNow, entrepôts tiers.
- Faire construire des pipelines par des profils non développeurs : l'interface, l'aperçu sur un échantillon et Wrangler remplacent le code.
- Migration de traitements ETL existants venus d'outils graphiques comparables.
- **Replication** : réplication continue d'une base vers BigQuery, configurée en quelques écrans.

**À éviter** quand l'équipe écrit déjà du code : une instance tourne — et se facture — en continu, même sans pipeline actif. Pour une transformation purement SQL dans BigQuery, préférer [Dataform](#dataform) ; pour de la réplication de base de données seule, [Datastream](#datastream) ; pour un pipeline de flux sans interface graphique, Dataflow ou [Managed Service for Apache Spark](#managed-service-for-apache-spark).

> [!WARNING]
> Le coût d'une instance court tant qu'elle existe, pas seulement pendant les exécutions. Une instance Developer réservée au développement, supprimée entre deux campagnes de travail, évite de payer une édition Enterprise à vide.

## Alternatives en logiciel libre

- **CDAP** : le projet dont Cloud Data Fusion est la version gérée ; même Studio, mêmes plugins, à héberger soi-même.
- **Apache NiFi** : flux de données graphiques, orientés routage et transformation d'enregistrements en continu.
- **Apache Hop** : conception visuelle de transformations par lots, l'ETL graphique classique.
- **Meltano** : connecteurs d'extraction et de chargement, sans transformation graphique.
