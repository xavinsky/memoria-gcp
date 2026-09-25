---
title: Cloud Tasks
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 160, y: 10, w: 588, h: 282}
  nodes:
    users: {label: Utilisateurs, sub: requête web, external: true, x: 8, y: 120, w: 140}
    api: {label: Service d'API, sub: Cloud Run, icon: produits/cloud-run, x: 176, y: 120, w: 170}
    q: {label: Cloud Tasks, sub: file de tâches, icon: categories/integration-services, focus: true, x: 376, y: 118, w: 180, h: 64}
    worker: {label: Worker, sub: Cloud Run, icon: produits/cloud-run, x: 576, y: 26, w: 165}
    db: {label: Cloud SQL, sub: base métier, icon: produits/cloud-sql, x: 576, y: 214, w: 165}
  flows:
    - {from: users, to: api, text: "L'utilisateur envoie sa requête au service d'API, qui doit lui répondre sans attendre le travail long."}
    - {from: api, to: q, text: "Le service crée une tâche HTTP avec sa charge utile, éventuellement datée, puis répond immédiatement."}
    - {from: q, to: worker, text: "La file distribue les tâches au rythme configuré, sans dépasser le nombre d'exécutions simultanées autorisé."}
    - {from: worker, to: q, from_side: left, from_offset: 16, to_side: right, to_offset: 16, control: true, text: "Une réponse autre que 2xx laisse la tâche en file : elle est réessayée avec un délai exponentiel, jusqu'au nombre maximal de tentatives."}
    - {from: worker, to: db, text: "Le worker termine le travail, écrit en base et renvoie 2xx, ce qui supprime la tâche de la file."}
docs:
  Documentation: https://docs.cloud.google.com/tasks/docs
  Vue d'ensemble: https://docs.cloud.google.com/tasks/docs/dual-overview
  Configurer une file: https://docs.cloud.google.com/tasks/docs/configuring-queues
  Créer des tâches à cible HTTP: https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks
  Pièges courants: https://docs.cloud.google.com/tasks/docs/common-pitfalls
  API REST: https://docs.cloud.google.com/tasks/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/tasks
  Bibliothèques clientes: https://docs.cloud.google.com/tasks/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/cloudtasks/latest
  Quotas et limites: https://docs.cloud.google.com/tasks/docs/quotas
  Tarifs: https://cloud.google.com/tasks/pricing
  Notes de version: https://docs.cloud.google.com/tasks/docs/release-notes
---

## Ce que c'est

File de tâches managée pour sortir du chemin de la requête tout ce qui peut attendre. L'application crée une **tâche**, la file la conserve, puis l'envoie à un *worker* sous forme de requête HTTP, au rythme et avec la politique de réessai qu'on a fixés.

- **File et tâche.** Une **file** est une ressource régionale qui porte la cadence, les réessais et, pour les cibles HTTP, une route par défaut. Une **tâche** porte un nom, une méthode, une URL, des en-têtes et une charge utile ; elle peut être **datée** jusqu'à 30 jours à l'avance. La création renvoie un accusé dès que la tâche est écrite de façon durable.
- **Cibles.** Une cible **HTTP** peut être n'importe quel point d'entrée : [Cloud Run](#cloud-run), une fonction, [GKE](#gke), [Compute Engine](#compute-engine), un serveur hors de Google Cloud. La file joint un jeton OIDC ou OAuth émis par un compte de service dédié, distinct de celui de l'application qui crée les tâches. Une cible **App Engine** vise directement un service de l'application du projet.
- **Contrôle du débit.** Deux réglages : le nombre de tâches distribuées par seconde (500 au maximum par file) et le nombre d'exécutions simultanées. C'est le moyen de lisser un pic de trafic ou de respecter la limite de débit d'une API tierce. Une file se met en pause, se vide, se reprend.
- **Réessais.** Nombre maximal de tentatives, durée maximale de réessai, délai minimal et maximal, nombre de doublements : le délai croît exponentiellement entre ces bornes. Le délai d'attente d'une réponse vaut 10 minutes par défaut et 30 minutes au plus pour une cible HTTP ; sur App Engine en mise à l'échelle manuelle, il peut aller jusqu'à 24 heures.
- **Garantie de livraison.** Au moins une fois : une même tâche peut être exécutée deux fois, donc le *worker* doit être idempotent. Nommer explicitement une tâche active la déduplication, effective 24 heures après sa suppression, mais ralentit la création.
- **Limites.** 1 000 files par région, 1 Mio par tâche, création par lots de 100 tâches (10 Mio), conservation d'une tâche pendant 31 jours au plus, et une file sans aucun appel ni distribution pendant 30 jours passe à l'état inactif.
- **Facturation** à l'opération facturable — un appel d'API ou une tentative de distribution — découpée par tranches de 32 Kio : le premier million par mois et par compte de facturation est gratuit, puis 0,40 $ par million. Les tâches en échec du fait de Google ne sont pas facturées.

> [!WARNING]
> Cloud Tasks garantit la livraison mais pas le moment : une tâche peut partir avec du retard. Ne jamais l'utiliser pour un traitement dont un utilisateur attend le résultat à l'écran.

## À quoi ça sert

- Rendre la main tout de suite à l'utilisateur en différant ce qui est lent : envoi de courriels, génération de documents, indexation, appels à des services tiers.
- Lisser un pic : le service d'entrée accepte tout, la file distribue à débit constant et protège la base ou l'API en aval.
- Respecter la limite de débit d'une API externe sans écrire de compteur, en réglant simplement la cadence de la file.
- Conserver le travail en cours pendant un incident de production : les tâches restent en file et repartent quand le *worker* revient.
- Réessayer proprement un appel fragile, avec une politique explicite plutôt qu'une boucle improvisée dans le code.

**À éviter** pour diffuser le même message à plusieurs consommateurs, ou pour un flux continu à fort débit : c'est le modèle *publication-abonnement* de [Pub/Sub](#pubsub), alors que Cloud Tasks vise une tâche, une cible, un contrôle fin du débit. À éviter aussi pour un enchaînement d'étapes dépendantes, qui relève de [Workflows](#workflows), et pour une répétition à heure fixe, qui est le métier de [Cloud Scheduler](#cloud-scheduler).

## Alternatives en logiciel libre

- **Celery** (BSD 3 clauses) : file de tâches Python appuyée sur RabbitMQ ou Redis, avec réessais, tâches datées et limitation de débit par file — l'équivalent le plus courant.
- **RQ** (BSD 2 clauses) : même idée en beaucoup plus simple, sur Redis seul.
- **Sidekiq** (LGPL 3.0 pour l'édition libre) : l'équivalent côté Ruby, avec files pondérées et réessais exponentiels.
- **BullMQ** (MIT) et **Asynq** (MIT) : files de tâches sur Redis pour Node.js et Go, avec tâches différées et tableau de bord.
- **RabbitMQ** (MPL 2.0) : le courtier lui-même, quand on veut construire la file et sa politique de réessai à la main.
- **Temporal** (MIT) : va plus loin qu'une file — réessais, état durable, compensation — si le travail différé devient un processus à plusieurs étapes.
