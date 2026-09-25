---
title: AlloyDB for PostgreSQL
subgroup: Bases de données
icon: produits/alloydb
schema:
  size: [760, 300]
  zones:
    - {label: Région principale, x: 16, y: 16, w: 510, h: 268}
    - {label: Région secondaire, x: 540, y: 16, w: 206, h: 268}
  nodes:
    vertex: {label: Vertex AI, sub: embeddings, icon: produits/vertex-ai, x: 40, y: 36, w: 130}
    app: {label: GKE, sub: application, icon: produits/gke, x: 40, y: 130, w: 130}
    alloy: {label: AlloyDB, sub: instance principale, icon: produits/alloydb, focus: true, x: 210, y: 122, w: 190, h: 70}
    pool: {label: Pool de lecture, sub: nœuds équilibrés, icon: produits/alloydb, x: 210, y: 226, w: 190, h: 50}
    backup: {label: Sauvegardes, sub: continues, icon: categories/storage, x: 366, y: 36, w: 156}
    sec: {label: Cluster secondaire, sub: promouvable, icon: produits/alloydb, x: 550, y: 122, w: 190}
  flows:
    - {from: app, to: alloy, text: "L'application se connecte au point de terminaison privé de l'instance, par le connecteur de langage ou l'AlloyDB Auth Proxy"}
    - {from: alloy, to: pool, text: "Les requêtes en lecture seule vont au pool de lecture, qui lit la même couche de stockage et se répartit la charge"}
    - {from: alloy, to: vertex, from_offset: -20, text: "Depuis le SQL, l'extension google_ml_integration appelle un modèle pour produire des embeddings, indexés par ScaNN"}
    - {from: alloy, to: backup, text: "Sauvegarde continue du cluster : restauration vers n'importe quel instant de la fenêtre de rétention"}
    - {from: alloy, to: sec, text: "Réplication asynchrone vers un cluster secondaire d'une autre région, promouvable en cluster principal"}
captures:
  - image: https://docs.cloud.google.com/static/alloydb/images/upgrade-free-trial-cluster.png
    page: https://docs.cloud.google.com/alloydb/docs/create-free-trial-cluster
    legende: "Vue d'ensemble d'un cluster dans la console, avec le menu AlloyDB Studio, System insights et Query insights"
  - image: https://docs.cloud.google.com/static/alloydb/images/adb-system-insights-main-dashboard.png
    page: https://docs.cloud.google.com/alloydb/docs/monitor-instance
    legende: "System insights d'un cluster : stockage, nombre de nœuds, utilisation du processeur et charge de la base par instance"
docs:
  Page produit: https://cloud.google.com/products/alloydb
  Documentation: https://docs.cloud.google.com/alloydb/docs
  AlloyDB AI: https://docs.cloud.google.com/alloydb/docs/ai
  Moteur en colonnes: https://docs.cloud.google.com/alloydb/docs/columnar-engine/about
  AlloyDB Omni: https://docs.cloud.google.com/alloydb/omni/docs/overview
  API REST: https://docs.cloud.google.com/alloydb/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/alloydb
  Connecteurs de langage: https://docs.cloud.google.com/alloydb/docs/connect-language-connectors
  Client Python: https://docs.cloud.google.com/python/docs/reference/alloydb/latest
  Quotas et limites: https://docs.cloud.google.com/alloydb/quotas
  Tarifs: https://cloud.google.com/alloydb/pricing
  Notes de version: https://docs.cloud.google.com/alloydb/docs/release-notes
---

## Ce que c'est

Base **compatible PostgreSQL** dont Google a réécrit le moteur et le stockage, pour les charges transactionnelles exigeantes. Les applications, les pilotes et les extensions PostgreSQL fonctionnent sans changement ; l'architecture, elle, n'est plus celle d'un serveur PostgreSQL.

- **Calcul et stockage séparés.** Les nœuds de calcul exécutent les requêtes ; une couche de stockage distribuée, répartie sur plusieurs zones, conserve les données et grandit toute seule.
- **Hiérarchie** : *cluster* (conteneur régional des bases) → *instances* (points de connexion) → *nœuds* (les VM). L'instance principale, unique par cluster, porte les écritures ; les **pools de lecture** ajoutent des instances en lecture seule, dont la charge est répartie entre les nœuds.
- **Haute disponibilité** par défaut : l'instance principale tient sur deux nœuds dans deux zones, avec bascule automatique. SLA de 99,99 % dans la plupart des régions. La maintenance est préparée sur des serveurs de remplacement, ce qui la ramène en général sous la seconde d'indisponibilité.
- **Moteur en colonnes** : une représentation des données en colonnes, tenue en mémoire, qui accélère les requêtes analytiques sur les tables transactionnelles, sans copie vers un autre système.
- **Réglage automatique** : conseiller d'index, autovacuum adaptatif, gestion automatique de la mémoire et du stockage.
- **AlloyDB AI** : l'extension `vector` (variante de pgvector), l'index `alloydb_scann` pour la recherche approximative de voisins, `google_ml_integration` pour appeler un modèle depuis le SQL, `alloydb_ai_nl` pour interroger la base en langage naturel.
- **Reprise** : sauvegarde continue avec restauration à un instant donné, sauvegardes complètes planifiées, clusters secondaires inter-régions.
- **AlloyDB Omni** : le même moteur, téléchargeable, exécutable sur n'importe quel environnement Linux.
- **Facturation** : vCPU et mémoire des instances, stockage consommé, sortie réseau.

## À quoi ça sert

- PostgreSQL sous forte charge, quand une instance [Cloud SQL](#cloud-sql) ne suit plus et qu'on ne veut ni changer de moteur ni redécouper l'application.
- Croiser transactions et analyse dans la même base (*HTAP*) : tableaux de bord et agrégats calculés sur les données vivantes grâce au moteur en colonnes.
- Applications d'IA générative : embeddings, recherche vectorielle et appels de modèles sans sortir les données de la base.
- Migration d'un PostgreSQL existant ou d'une base propriétaire, avec Database Migration Service.

**À éviter** pour une petite base ou un environnement de test : le cluster réserve au minimum un nœud de calcul et coûte plus cher que la même chose en Cloud SQL. À éviter aussi quand il faut du MySQL ou du SQL Server (Cloud SQL), quand les écritures doivent se répartir sur plusieurs régions ([Spanner](#spanner)), ou pour un entrepôt analytique à part entière ([BigQuery](#bigquery)).

## Alternatives en logiciel libre

- **PostgreSQL** autohébergé, avec **CloudNativePG** ou **Patroni** pour la haute disponibilité : la compatibilité est totale dans ce sens, puisque AlloyDB parle PostgreSQL.
- **pgvector** : l'extension de recherche vectorielle dont dérive celle d'AlloyDB.
- **Citus** : extension PostgreSQL de répartition des tables sur plusieurs nœuds, pour l'échelle horizontale.
- **DuckDB** via l'extension **pg_duckdb**, ou **Apache Doris** à côté de la base : l'accélération analytique en colonnes, en pièces détachées.
- **Apache AGE**, **PostGIS**, **pg_cron** : les extensions qui spécialisent un PostgreSQL vers un usage donné, là où AlloyDB en intègre certaines d'office.
