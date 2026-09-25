---
title: Datastream
subgroup: Analytique
icon: categories/data-analytics
schema:
  size: [760, 340]
  zones:
    - {label: Sur site ou autre cloud, x: 6, y: 112, w: 180, h: 112}
    - {label: Projet GCP, x: 206, y: 10, w: 540, h: 320}
  nodes:
    src: {label: Base source, sub: "MySQL, Oracle, PG", external: true, x: 18, y: 144, w: 156}
    ds: {label: Datastream, sub: "flux CDC + backfill", icon: categories/data-analytics, focus: true, x: 236, y: 136, w: 200, h: 72}
    bq: {label: BigQuery, sub: "tables répliquées", icon: produits/bigquery, x: 530, y: 30, w: 200}
    bi: {label: Looker, sub: "tableaux de bord", icon: produits/looker, x: 530, y: 112, w: 200}
    gcs: {label: Cloud Storage, sub: "fichiers Avro ou JSON", icon: produits/cloud-storage, x: 530, y: 212, w: 200}
    flow: {label: Dataflow, sub: "modèle de chargement", icon: categories/data-analytics, x: 236, y: 264, w: 200}
  flows:
    - {from: src, to: ds, from_side: right, to_side: left, from_offset: -16, to_offset: -16, text: "Remplissage initial : Datastream lit les tables entières pour constituer l'état de départ"}
    - {from: src, to: ds, from_side: right, to_side: left, from_offset: 16, to_offset: 16, text: "Puis capture continue des changements dans le journal de transactions de la source, par connectivité privée"}
    - {from: ds, to: bq, from_offset: -20, text: "Écriture des événements dans les tables BigQuery, en mode fusion ou en ajout seul"}
    - {from: bq, to: bi, text: "Les tableaux de bord interrogent des tables à quelques minutes de la source"}
    - {from: ds, to: gcs, from_offset: 20, text: "Variante : le flux d'événements est déposé en fichiers Avro ou JSON dans un bucket"}
    - {from: gcs, to: flow, from_offset: 16, to_offset: 16, text: "Un modèle Dataflow relit ces fichiers pour charger Spanner, Cloud SQL ou un autre système"}
docs:
  Page produit: https://cloud.google.com/datastream
  Documentation: https://docs.cloud.google.com/datastream/docs
  Présentation: https://docs.cloud.google.com/datastream/docs/overview
  Comportement et concepts: https://docs.cloud.google.com/datastream/docs/behavior-overview
  Sources prises en charge: https://docs.cloud.google.com/datastream/docs/sources
  Destination BigQuery: https://docs.cloud.google.com/datastream/docs/destination-bigquery
  API REST: https://docs.cloud.google.com/datastream/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/datastream
  Client Python: https://docs.cloud.google.com/python/docs/reference/datastream/latest
  Quotas et limites: https://docs.cloud.google.com/datastream/docs/quotas
  Tarifs: https://cloud.google.com/datastream/pricing
  Notes de version: https://docs.cloud.google.com/datastream/docs/release-notes
---

## Ce que c'est

Service **serverless** de capture de changements (*change data capture*, CDC) et de réplication : il lit le journal de transactions d'une base de production et rejoue les modifications dans une destination analytique, sans requête lourde sur la source.

- **Trois objets** : une **configuration de connectivité privée** (appairage VPC ou interface Private Service Connect) pour joindre une source sans passer par l'internet ; des **profils de connexion**, un par extrémité ; un **flux** (*stream*) qui relie un profil source à un profil de destination et choisit les tables.
- **Sources** : bases MySQL, Oracle, PostgreSQL (dont AlloyDB), SQL Server, MongoDB, Spanner ; applications Salesforce, Salesforce Marketing Cloud, Microsoft Dataverse et ServiceNow.
- **Destinations** : BigQuery, Cloud Storage, et les tables Apache Iceberg gérées par BigLake.
- **Deux phases** : un **remplissage initial** (*backfill*) qui lit les tables entières, puis la capture continue des événements. Chaque événement est traduit dans un **type unifié**, représentation commune des types de toutes les sources.
- **Écriture dans BigQuery** : en mode **fusion**, la table de destination reflète l'état courant de la source (`UPSERT`) ; en mode **ajout seul**, chaque changement devient une ligne, avec son type d'opération. Une colonne `datastream_metadata` porte l'identifiant de l'événement et l'horodatage de la source.
- **Facturation** : au volume d'octets traités, sans coût fixe — un flux inactif ne coûte rien. Une franchise mensuelle de 100 Gio couvre les flux AlloyDB et Spanner vers BigQuery. Les opérations de fusion dans BigQuery sont facturées à part.

## À quoi ça sert

- Mettre une réplique analytique d'une base de production dans BigQuery, avec une latence de l'ordre de la minute, sans écrire de pipeline.
- Alimenter un entrepôt à partir de plusieurs bases hétérogènes vers un schéma unique.
- Migrer une base vers Google Cloud en gardant l'ancienne active : Datastream tient la cible à jour jusqu'à la bascule.
- Produire un flux d'événements à partir d'une base existante, pour une architecture événementielle (via Cloud Storage, ou [Pub/Sub](#pubsub) en aval).

**À éviter** pour transformer les données au passage : Datastream réplique, il ne calcule pas. La transformation se fait après, dans BigQuery avec [Dataform](#dataform), ou dans un pipeline Dataflow. Pour un besoin de haute disponibilité entre deux bases transactionnelles, préférer la réplication native du moteur (voir [Choisir une base de données](#choisir-une-base)).

> [!WARNING]
> L'octet facturé est une représentation interne de la donnée source, souvent deux à cinq fois plus volumineuse que la donnée elle-même : estimer le coût d'un flux à partir de la taille de la base conduit à le sous-évaluer. Côté destination, le paramètre `max_staleness` de la table arbitre entre fraîcheur et coût — plus il est bas, plus les fusions sont fréquentes et chères.

## Alternatives en logiciel libre

- **Debezium** : la référence du CDC, avec des connecteurs pour MySQL, PostgreSQL, Oracle, SQL Server et MongoDB ; s'utilise avec Kafka Connect ou en serveur autonome.
- **Apache Flink CDC** : mêmes sources, intégrées à un moteur de traitement de flux avec état.
- **Kafka Connect** : le socle de connecteurs source et puits, dont Debezium est l'implémentation CDC la plus répandue.
- **Meltano** (licence MIT) et ses connecteurs Singer : réplication par lots ou incrémentale d'un large catalogue de sources, à la granularité de la table plutôt que de la transaction.
- **pglogical** et les outils de réplication logique de PostgreSQL : réplication native entre bases du même moteur.
