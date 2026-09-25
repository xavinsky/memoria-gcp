---
title: Managed Service for Apache Kafka
subgroup: Analytique
icon: categories/data-analytics
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 150, y: 16, w: 596, h: 268}
  nodes:
    prod: {label: Producteurs, sub: "applis, capteurs", external: true, x: 8, y: 100, w: 128}
    kafka: {label: Managed Kafka, sub: "brokers, topics, partitions", icon: categories/data-analytics, focus: true, x: 180, y: 92, w: 230, h: 76}
    sr: {label: Registre de schémas, sub: "Avro, Protobuf", icon: categories/data-analytics, x: 180, y: 212, w: 230}
    df: {label: Dataflow, sub: consommateur streaming, icon: categories/data-analytics, x: 470, y: 36, w: 200}
    connect: {label: Kafka Connect, sub: connecteurs gérés, icon: categories/data-analytics, x: 470, y: 120, w: 200}
    bq: {label: BigQuery, sub: tables cibles, icon: produits/bigquery, x: 470, y: 212, w: 200}
  flows:
    - {from: prod, to: kafka, text: "Les producteurs écrivent dans un topic ; chaque partition est répliquée sur trois zones"}
    - {from: prod, to: sr, text: "Les clients publient et récupèrent leurs schémas Avro ou Protobuf dans le registre du cluster"}
    - {from: kafka, to: df, from_side: right, from_offset: -20, text: "Un groupe de consommateurs lit les partitions et valide sa position (offset)"}
    - {from: kafka, to: connect, from_side: right, from_offset: 20, text: "Le cluster Connect exécute les connecteurs, en puisant sa configuration et son état dans le cluster Kafka"}
    - {from: connect, to: bq, text: "Le connecteur puits écrit les messages dans BigQuery sans code à maintenir"}
docs:
  Page produit: https://cloud.google.com/products/managed-service-for-apache-kafka
  Documentation: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs
  Présentation: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/overview
  Kafka Connect: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/kafka-connect-overview
  Registre de schémas: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/schema-registry/schema-registry-overview
  Kafka ou Pub/Sub: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/choose-kafka-pubsub
  API REST: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/managed-kafka
  Bibliothèques clientes: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/google-cloud-managedkafka/latest
  Quotas et limites: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/quotas
  Tarifs: https://cloud.google.com/managed-service-for-apache-kafka/pricing
  Notes de version: https://docs.cloud.google.com/managed-service-for-apache-kafka/docs/release-notes
---

## Ce que c'est

**Apache Kafka** exploité par Google : les clusters restent des clusters Kafka, avec l'API et les outils du projet open source, mais le provisionnement, les correctifs et la réplication sont pris en charge.

- **Dimensionnement** : on déclare un total de vCPU et de mémoire pour le cluster, pas un nombre de brokers — le service en provisionne autant que nécessaire. Augmenter la taille peut ajouter des brokers et déclencher un rééquilibrage automatique des partitions.
- **Stockage à deux niveaux** (*tiered storage*) : un volume limité de disque local attaché aux brokers, et un stockage distant pratiquement illimité, moins cher et non provisionné à l'avance. La rétention se règle topic par topic.
- **Réseau** : le cluster est joignable depuis plusieurs VPC, projets et régions, par des adresses IP privées et des points de terminaison **Private Service Connect** créés automatiquement. L'URL du serveur d'amorçage (*bootstrap*) est la même partout, ce qui évite d'adapter la configuration des clients d'un environnement à l'autre.
- **Sécurité** : connexions TLS obligatoires, chiffrement au repos (clés Google ou CMEK), authentification **SASL** adossée à IAM ou **mTLS** par certificat client, autorisation par rôles IAM et par ACL Kafka. Les brokers tournent dans un projet locataire isolé, sans adresse publique.
- **Kafka Connect géré** : des clusters Connect associés à un cluster Kafka, avec des connecteurs préemballés et maintenus par Google — BigQuery, Cloud Storage, Pub/Sub, PostgreSQL, MirrorMaker 2.
- **Registre de schémas** compatible avec l'API Confluent, pour publier et faire évoluer les schémas Avro ou Protobuf des topics.
- **Facturation** : vCPU et mémoire du cluster convertis en *Data Compute Units*, stockage local et stockage longue durée au gigaoctet-heure, transfert entre zones pour la réplication, et un tarif de calcul distinct pour les clusters Connect.

## À quoi ça sert

- Migrer un existant Kafka — applications, connecteurs, outils de supervision — sans réécrire le code des clients.
- Standardiser sur l'API Kafka quand les mêmes applications tournent sur site, chez un autre fournisseur et sur Google Cloud.
- Journal d'événements durable et relisible : rétention longue, reprise d'un consommateur à une position antérieure, plusieurs groupes de consommateurs indépendants.
- Alimenter [BigQuery](#bigquery) ou [Dataflow](#dataflow) à partir de flux applicatifs, par un connecteur géré plutôt que par du code.

**À éviter** pour un projet neuf sans attachement à l'API Kafka : [Pub/Sub](#pubsub) est serverless et mondial, sans partitions à dimensionner ni cluster à redimensionner. À éviter aussi quand les producteurs et les consommateurs sont répartis sur plusieurs régions : un cluster Kafka est régional, la réplication inter-régions se construit à la main avec MirrorMaker.

> [!WARNING]
> Un cluster occupe toujours trois zones, et les zones ne se choisissent pas. Le nombre de partitions d'un topic reste, lui, un choix de conception : trop peu sature les brokers, trop gaspille des ressources.

## Alternatives en logiciel libre

- **Apache Kafka** autogéré, sur VM ou sur Kubernetes avec l'opérateur **Strimzi** ; **Cruise Control** pour le rééquilibrage des partitions.
- **Apache Pulsar** : sujets et abonnements multiples, multi-tenant, stockage par paliers natif.
- **NATS JetStream** : messagerie légère avec persistance, plus simple à exploiter pour de petits volumes.
- **Karapace** : registre de schémas et proxy REST compatibles avec l'API Confluent.
- **Debezium** : capture de changements de bases de données vers Kafka, à la place des connecteurs sources gérés.
