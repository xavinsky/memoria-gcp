---
title: Eventarc
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 10, y: 10, w: 738, h: 282}
  nodes:
    gcs: {label: Cloud Storage, sub: objet déposé, icon: produits/cloud-storage, x: 24, y: 118, w: 180}
    cal: {label: Cloud Audit Logs, sub: "création d'une table", icon: categories/observability, x: 24, y: 214, w: 210}
    ps: {label: Pub/Sub, sub: transport des messages, icon: categories/data-analytics, x: 300, y: 26, w: 190}
    eva: {label: Eventarc, sub: "déclencheur, filtres", icon: categories/integration-services, focus: true, x: 300, y: 118, w: 190, h: 64}
    run: {label: Cloud Run, sub: récepteur CloudEvents, icon: produits/cloud-run, x: 550, y: 118, w: 190}
    wf: {label: Workflows, sub: exécution déclenchée, icon: categories/integration-services, x: 550, y: 214, w: 190}
  flows:
    - {from: gcs, to: eva, text: "Le dépôt d'un objet dans le bucket émet un événement, envoyé directement par la source Cloud Storage."}
    - {from: cal, to: eva, text: "Les autres services passent par une entrée de Cloud Audit Logs, que le déclencheur filtre sur le type d'événement et ses attributs."}
    - {from: eva, to: ps, text: "Eventarc Standard crée et gère un sujet Pub/Sub qui sert de couche de transport et absorbe les réessais."}
    - {from: ps, to: run, text: "Une souscription push remet l'événement au service au format CloudEvents, au moins une fois."}
    - {from: eva, to: wf, text: "Un second déclencheur route le même type d'événement vers un workflow, qui le reçoit en argument d'exécution."}
docs:
  Documentation: https://docs.cloud.google.com/eventarc/docs
  Vue d'ensemble des éditions: https://docs.cloud.google.com/eventarc/docs/overview
  Eventarc Standard: https://docs.cloud.google.com/eventarc/standard/docs/overview
  Eventarc Advanced: https://docs.cloud.google.com/eventarc/advanced/docs/overview
  Sources et destinations: https://docs.cloud.google.com/eventarc/standard/docs/event-providers-targets
  Types d'événements: https://docs.cloud.google.com/eventarc/standard/docs/event-types
  Événements pris en charge: https://docs.cloud.google.com/eventarc/docs/reference/supported-events
  Format CloudEvents: https://docs.cloud.google.com/eventarc/docs/cloudevents
  Motifs de chemin: https://docs.cloud.google.com/eventarc/docs/path-patterns
  Réessais: https://docs.cloud.google.com/eventarc/docs/retry-events
  Transformer les événements: https://docs.cloud.google.com/eventarc/advanced/docs/receive-events/transform-events
  API REST: https://docs.cloud.google.com/eventarc/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/eventarc
  Client Python: https://docs.cloud.google.com/python/docs/reference/eventarc/latest
  Quotas et limites: https://docs.cloud.google.com/eventarc/docs/quotas
  Tarifs: https://cloud.google.com/eventarc/pricing
  Notes de version: https://docs.cloud.google.com/eventarc/docs/release-notes
---

## Ce que c'est

Service d'acheminement d'événements : il capte les changements d'état produits par les services Google Cloud et les remet à une cible applicative, au format **CloudEvents**, en gérant la livraison, les réessais et les autorisations. Deux éditions partagent le même modèle de données ; on passe de l'une à l'autre sans réécrire les producteurs.

- **Eventarc Standard.** L'unité de configuration est le **déclencheur** : il filtre les événements entrants sur leur source, leur type et quelques attributs, puis les route vers une destination. Plus de 130 fournisseurs Google sont couverts, soit directement par la source (dépôt d'un objet dans [Cloud Storage](#cloud-storage), message [Pub/Sub](#pubsub)), soit à travers une entrée de Cloud Audit Logs pour tout le reste. Destinations : services et jobs [Cloud Run](#cloud-run), fonctions, services [GKE](#gke), [Workflows](#workflows), points d'entrée HTTP internes d'un VPC. Limite : 500 déclencheurs par projet et par région, événements de 512 Kio au plus.
- **Eventarc Advanced.** Trois objets remplacent le déclencheur. Un **bus** est un point d'entrée unique qui reçoit tout ce que publient les fournisseurs. Une **inscription** (*enrollment*) est un abonnement à ce bus, dont les critères s'écrivent en **CEL** sur n'importe quel attribut. Un **pipeline** porte la destination et, au passage, la transformation ou la conversion de format du message. Un bus et cent pipelines par projet et par région, événements jusqu'à 1 Mio, livraison entre projets, publication directe par l'API Eventarc Publishing.
- **Transport.** En édition Standard, les événements transitent par un sujet Pub/Sub qu'Eventarc crée et gère, avec une souscription *push* vers la destination. C'est ce sujet qui porte la file de lettres mortes lorsqu'on en configure une.
- **Format.** Les événements arrivent en CloudEvents, en mode binaire sur HTTP, avec une charge utile en `application/json` ou `application/protobuf` selon le fournisseur. Une destination Workflows reçoit l'événement converti en objet JSON, passé en argument d'exécution.
- **Livraison.** Au moins une fois : un récepteur doit être idempotent. Un événement non acquitté est réessayé avec un délai exponentiel pendant 24 heures par défaut. Ni l'une ni l'autre édition ne garantit l'ordre.
- **Facturation.** Les 50 000 premiers événements facturables du mois sont gratuits. Les événements issus de sources Google ou Pub/Sub sont gratuits, les autres coûtent 1 $ par million. S'ajoutent le transport Pub/Sub au tarif standard, Cloud Logging pour les événements passant par les journaux d'audit, et le coût de la cible. Un événement est compté par tranche de 64 Kio.

> [!WARNING]
> Un événement passant par Cloud Audit Logs n'existe que si le journal correspondant est activé — les journaux d'accès aux données ne le sont pas par défaut, et ils sont facturés. Les sources directes (Cloud Storage, Pub/Sub, Firestore) évitent ce détour et arrivent avec moins de latence.

## À quoi ça sert

- Déclencher un traitement à l'arrivée d'un fichier : conversion d'image, chargement dans [BigQuery](#bigquery), analyse d'un document déposé.
- Réagir à une opération d'administration — création d'une VM, modification d'une règle de pare-feu — pour étiqueter, corriger ou alerter.
- Relier des microservices sans qu'ils se connaissent : le producteur publie, Eventarc route, le consommateur n'est qu'une URL.
- Lancer un [workflow](#workflows) sur événement, quand la réaction suppose plusieurs appels enchaînés plutôt qu'un seul service.
- Centraliser, avec l'édition Advanced, les flux d'événements de plusieurs équipes et projets sur un bus unique, avec filtrage fin et transformation avant livraison.

**À éviter** quand producteur et consommateur sont les deux extrémités d'une file que l'on maîtrise déjà : [Pub/Sub](#pubsub) seul est plus simple et moins cher, Eventarc n'apportant que le filtrage et le format CloudEvents. À éviter aussi pour un travail différé déclenché par sa propre application : une file de tâches avec cadence et réessais paramétrables, [Cloud Tasks](#cloud-tasks), correspond mieux qu'un événement d'infrastructure.

## Alternatives en logiciel libre

- **Knative Eventing** (Apache 2.0) : l'équivalent le plus direct — sources, courtiers, déclencheurs filtrés sur les attributs CloudEvents, le tout sur Kubernetes.
- **Argo Events** (Apache 2.0) : sources d'événements, capteurs et déclencheurs Kubernetes, avec une vingtaine de connecteurs (objets S3, webhooks, files).
- **NATS avec JetStream** (Apache 2.0) : messagerie légère avec persistance, souscriptions filtrées par sujet et livraison au moins une fois.
- **Apache Kafka** (Apache 2.0) : le socle habituel quand le volume et la relecture comptent plus que la simplicité de configuration.
- **CloudEvents** (Apache 2.0) : la spécification elle-même et ses SDK, utilisables indépendamment pour garder un format d'événement portable.
- **Debezium** (Apache 2.0) : capture des changements d'une base de données et les publie en événements, pour la partie « réagir à une écriture ».
