---
title: Spanner
subgroup: Bases de données
icon: produits/cloud-spanner
aka: Cloud Spanner
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 156, y: 16, w: 590, h: 268}
  nodes:
    clients: {label: Clients, sub: "web, mobile", external: true, x: 8, y: 122, w: 126}
    run: {label: Cloud Run, sub: services régionaux, icon: produits/cloud-run, x: 180, y: 118, w: 170}
    sp: {label: Spanner, sub: instance multirégionale, icon: produits/cloud-spanner, focus: true, x: 388, y: 110, w: 200, h: 70}
    df: {label: Dataflow, sub: flux de changements, icon: categories/data-analytics, x: 388, y: 224, w: 200, h: 50}
    bq: {label: BigQuery, sub: analyse, icon: produits/bigquery, x: 612, y: 224, w: 130}
    backup: {label: Sauvegardes, sub: planifiées, icon: categories/storage, x: 610, y: 36, w: 134}
    boost: {label: Data Boost, sub: calcul isolé, icon: produits/cloud-spanner, x: 610, y: 130, w: 132}
  flows:
    - {from: clients, to: run, text: "Les clients atteignent le service déployé au plus près d'eux, dans l'une des régions de l'instance"}
    - {from: run, to: sp, text: "Le service lit et écrit en SQL ; TrueTime horodate chaque transaction, ce qui rend les lectures cohérentes partout"}
    - {from: sp, to: backup, from_offset: -20, text: "Sauvegardes planifiées, complètes ou incrémentales, restaurables dans n'importe quelle région de l'instance"}
    - {from: sp, to: boost, text: "Data Boost exécute les gros balayages sur un calcul serverless, sans peser sur les nœuds qui servent l'application"}
    - {from: sp, to: df, text: "Un flux de changements publie chaque écriture de la base ; Dataflow le consomme en continu"}
    - {from: df, to: bq, text: "Les changements atterrissent dans BigQuery, pour l'analyse et l'historique"}
captures:
  - image: https://docs.cloud.google.com/static/spanner/docs/images/console/annotated-query-editor.png
    page: https://docs.cloud.google.com/spanner/docs/tune-query-with-visualizer
    legende: "Éditeur de requêtes de la console, avec le plan d'exécution visuel"
  - image: https://docs.cloud.google.com/static/spanner/docs/images/console/system_insights_dashboard2.png
    page: https://docs.cloud.google.com/spanner/docs/monitoring-console
    legende: "Tableau de bord System insights d'une instance : utilisation du processeur, latences de lecture et d'écriture, débit, par région"
docs:
  Page produit: https://cloud.google.com/spanner
  Documentation: https://docs.cloud.google.com/spanner/docs
  Éditions: https://docs.cloud.google.com/spanner/docs/editions-overview
  TrueTime et cohérence externe: https://docs.cloud.google.com/spanner/docs/true-time-external-consistency
  Spanner Graph: https://docs.cloud.google.com/spanner/docs/graph/overview
  Référence GoogleSQL: https://docs.cloud.google.com/spanner/docs/reference/standard-sql/query-syntax
  Interface PostgreSQL: https://docs.cloud.google.com/spanner/docs/reference/postgresql/overview
  API REST: https://docs.cloud.google.com/spanner/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/spanner
  Bibliothèques clientes: https://docs.cloud.google.com/spanner/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/spanner/latest
  Quotas et limites: https://docs.cloud.google.com/spanner/quotas
  Tarifs: https://cloud.google.com/spanner/pricing
  Notes de version: https://docs.cloud.google.com/spanner/docs/release-notes
---

## Ce que c'est

Base relationnelle **distribuée** : les tables sont découpées en *splits* répartis sur des serveurs, répliqués entre zones ou entre régions, et les transactions restent cohérentes sur l'ensemble. Elle se comporte comme une base sur une seule machine, mais grandit en ajoutant des serveurs.

- **Cohérence externe.** Chaque transaction reçoit un horodatage issu de **TrueTime**, l'horloge distribuée de Google. Une transaction validée après une autre est vue comme telle par tous les lecteurs, y compris dans une autre région : c'est la garantie la plus forte, plus stricte que la sérialisabilité seule.
- **Instances** : une *configuration d'instance* fixe la géographie (régionale, birégionale ou multirégionale), la *capacité de calcul* fixe la taille. Elle se mesure en unités de traitement, 1 000 unités valant un nœud ; en dessous de 1 000, il faut raisonner en unités.
- **Trois éditions.** *Standard* (régional, SLA 99,99 %) ; *Enterprise* ajoute Spanner Graph, la recherche plein texte et vectorielle, l'autoscaling géré, les groupes de localité et les sauvegardes incrémentales ; *Enterprise Plus* ajoute les configurations birégionales et multirégionales (jusqu'à 99,999 % de disponibilité) et le partitionnement géographique.
- **Multimodèle** : relationnel en GoogleSQL ou en dialecte PostgreSQL, accès clé-valeur, graphes (Spanner Graph, requêtes en GQL), recherche plein texte et recherche vectorielle dans la même base.
- **Flux de changements** (*change streams*) : chaque insertion, modification ou suppression peut être publiée et consommée par Dataflow ou Kafka.
- **Analyse** : *Data Boost* exécute les requêtes lourdes sur un calcul serverless indépendant des nœuds de service ; BigQuery interroge Spanner en requête fédérée, et l'*inverse ETL* ramène des résultats depuis BigQuery.
- **Facturation** : capacité de calcul, stockage, sauvegardes et sortie réseau ; le prix dépend de l'édition et de la configuration d'instance.

> [!TIP]
> La conception du schéma pèse plus que la taille de l'instance. Les tables **entrelacées** (`INTERLEAVE IN PARENT`) rangent physiquement les lignes filles à côté de leur parent, ce qui évite une jointure distribuée ; à l'inverse, une clé primaire croissante (horodatage, séquence) concentre les écritures sur un seul *split*.

## À quoi ça sert

- Application transactionnelle qui doit rester disponible et cohérente au-delà d'une région : paiements, inventaire, jeux en ligne, télécommunications.
- Charges dont les écritures dépassent ce qu'une machine encaisse, sans partitionnement applicatif à écrire soi-même.
- Bases multi-tenant très volumineuses, où le partitionnement géographique garde les données d'un client dans son pays.
- Applications qui mêlent relationnel, graphe et recherche sans multiplier les bases.

**À éviter** pour une base modeste ou une migration à l'identique : le SQL, les types et les index diffèrent de PostgreSQL ou de MySQL, et le ticket d'entrée est plus élevé — préférer [Cloud SQL](#cloud-sql) ou [AlloyDB](#alloydb). À éviter aussi pour du balayage analytique massif ([BigQuery](#bigquery)) ou pour des accès clé-valeur à très haut débit sans besoin de transactions ([Bigtable](#bigtable)). Voir [Choisir une base de données](#choisir-une-base).

## Alternatives en logiciel libre

- **YugabyteDB** : base SQL distribuée inspirée de l'article Spanner, sous licence Apache 2.0, avec réplication Raft, transactions distribuées et protocole PostgreSQL. C'est l'équivalent le plus proche.
- **TiDB** : SQL distribué compatible MySQL, avec le moteur analytique TiFlash en colonnes.
- **Apache Cassandra** : l'échelle horizontale et la réplication multirégionale, mais sans transactions distribuées ni cohérence externe.
- **Vitess** : partitionnement horizontal de MySQL, la voie « faire grossir l'existant » plutôt que changer de moteur.
- **Citus** : répartition des tables d'un PostgreSQL sur plusieurs nœuds.
