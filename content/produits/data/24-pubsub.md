---
title: Pub/Sub
subgroup: Analytique
icon: categories/data-analytics
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 156, y: 16, w: 590, h: 268}
  nodes:
    prod: {label: Producteurs, sub: "applis, IoT, logs", external: true, x: 8, y: 103, w: 128}
    topic: {label: Pub/Sub, sub: sujet + abonnements, icon: categories/data-analytics, focus: true, x: 180, y: 96, w: 170, h: 70}
    dlq: {label: Dead-letter, sub: messages en échec, icon: categories/data-analytics, x: 180, y: 222, w: 170, h: 50}
    df: {label: Dataflow, sub: pipeline streaming, icon: categories/data-analytics, x: 396, y: 36, w: 168}
    bq: {label: BigQuery, sub: tables, icon: produits/bigquery, x: 618, y: 36, w: 124}
    run: {label: Cloud Run, sub: service HTTPS, icon: produits/cloud-run, x: 396, y: 196, w: 168}
  flows:
    - {from: prod, to: topic, text: "Publication des messages dans le sujet ; chaque abonnement en reçoit une copie"}
    - {from: topic, to: df, text: "Abonnement pull : Dataflow lit les messages et les acquitte une fois traités"}
    - {from: df, to: bq, text: "Écriture des données transformées"}
    - {from: topic, to: run, text: "Abonnement push : Pub/Sub appelle le service HTTPS à chaque message"}
    - {from: topic, to: dlq, text: "Message non acquitté après N tentatives : transféré vers le sujet de lettres mortes"}
docs:
  Page produit: https://cloud.google.com/pubsub
  Documentation: https://docs.cloud.google.com/pubsub/docs
  API REST: https://docs.cloud.google.com/pubsub/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/pubsub
  Bibliothèques clientes: https://docs.cloud.google.com/pubsub/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/pubsub/latest
  Quotas et limites: https://docs.cloud.google.com/pubsub/quotas
  Tarifs: https://cloud.google.com/pubsub/pricing
  Notes de version: https://docs.cloud.google.com/pubsub/docs/release-notes
---

## Ce que c'est

Service de **messagerie asynchrone** géré et mondial, sur le modèle publication / abonnement : les producteurs publient des messages dans un **sujet** (topic), chaque **abonnement** rattaché au sujet en reçoit une copie.

- **Modes de livraison** : *pull* (le consommateur récupère les messages), *push* (Pub/Sub appelle un point de terminaison HTTPS), ou export direct vers BigQuery ou Cloud Storage.
- **Garanties** : livraison *au moins une fois* par défaut, *exactement une fois* en option pour les abonnements pull ; ordre garanti seulement entre messages qui partagent une **clé d'ordonnancement**.
- **Acquittement** : un message non acquitté avant l'échéance est relivré ; après un nombre d'échecs donné, il peut partir dans un sujet de lettres mortes (*dead-letter topic*).
- **Rétention et relecture** : conservation des messages acquittés possible sur l'abonnement ou le sujet, et relecture par *seek* vers un instantané ou une date.
- **Serverless** : aucune capacité à provisionner, facturation au volume de messages.

## À quoi ça sert

- Point d'entrée des flux d'événements : applications, IoT, journaux, changements de données.
- Découpler producteurs et consommateurs, absorber les pics de charge.
- Alimenter un pipeline de streaming : Pub/Sub → Dataflow → BigQuery.
- Déclencher des traitements à chaque événement (Cloud Run, Eventarc).

**À éviter** quand l'écosystème attend l'API Kafka (préférer Managed Service for Apache Kafka), ou pour une file de tâches avec contrôle du débit et des tentatives vers un service précis (préférer Cloud Tasks).

## Alternatives en logiciel libre

- **Apache Kafka** : journal d'événements distribué, la référence du streaming ; partitions, rétention longue, relecture.
- **Apache Pulsar** : sujets et abonnements multiples, multi-tenant, stockage à plusieurs niveaux ; le modèle le plus proche de Pub/Sub.
- **NATS JetStream** : messagerie légère avec persistance et acquittements.
- **RabbitMQ** : courtier de messages AMQP, routage fin, files de travail.
