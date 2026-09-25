---
title: Cloud Scheduler
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 10, y: 10, w: 738, h: 282}
  nodes:
    sch: {label: Cloud Scheduler, sub: "0 6 * * 1-5", icon: categories/integration-services, focus: true, x: 30, y: 118, w: 210, h: 64}
    job: {label: Job Cloud Run, sub: "traitement de nuit", icon: produits/cloud-run, x: 300, y: 26, w: 210}
    ps: {label: Pub/Sub, sub: sujet de déclenchement, icon: categories/data-analytics, x: 300, y: 118, w: 210}
    wf: {label: Workflows, sub: enchaînement d'appels, icon: categories/integration-services, x: 300, y: 214, w: 200}
    sub: {label: Service abonné, sub: Cloud Run, icon: produits/cloud-run, x: 560, y: 118, w: 180}
  flows:
    - {from: sch, to: job, control: true, text: "À l'heure prévue, le planificateur appelle l'API d'administration de Cloud Run, muni d'un jeton OIDC, pour lancer un job."}
    - {from: sch, to: ps, text: "Une autre tâche se contente de publier un message sur un sujet Pub/Sub, avec une charge utile fixe."}
    - {from: ps, to: sub, text: "Le service abonné consomme le message et fait le travail, sans rien savoir de l'horloge."}
    - {from: sch, to: wf, control: true, text: "Une troisième tâche crée une exécution de workflow, quand le traitement demande plusieurs appels enchaînés."}
    - {from: job, to: sch, from_side: bottom, to_side: top, control: true, text: "Une exécution qui ne renvoie pas de succès est réessayée selon la politique de la tâche : nombre de tentatives et délai exponentiel."}
docs:
  Documentation: https://docs.cloud.google.com/scheduler/docs
  Vue d'ensemble: https://docs.cloud.google.com/scheduler/docs/overview
  Format des horaires: https://docs.cloud.google.com/scheduler/docs/configuring/cron-job-schedules
  Créer une tâche: https://docs.cloud.google.com/scheduler/docs/creating
  Authentifier une cible HTTP: https://docs.cloud.google.com/scheduler/docs/http-target-auth
  Déclencher par Pub/Sub: https://docs.cloud.google.com/scheduler/docs/tut-gcf-pub-sub
  API REST: https://docs.cloud.google.com/scheduler/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/scheduler
  Bibliothèques clientes: https://docs.cloud.google.com/scheduler/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/cloudscheduler/latest
  Quotas et limites: https://docs.cloud.google.com/scheduler/quotas
  Tarifs: https://cloud.google.com/scheduler/pricing
  Notes de version: https://docs.cloud.google.com/scheduler/docs/release-notes
---

## Ce que c'est

Planificateur managé : l'équivalent de `cron`, mais sans machine à maintenir et avec des réessais. Une **tâche** associe un horaire à une cible ; à chaque échéance, Cloud Scheduler déclenche une **exécution**.

- **Horaire.** Format `unix-cron` à cinq champs — minute, heure, jour du mois, mois, jour de la semaine — avec un fuseau horaire explicite, donc un passage à l'heure d'été correctement géré. Une syntaxe plus lisible (*every 5 minutes*, *every monday 09:00*) est également acceptée.
- **Trois types de cible.** Un **point d'entrée HTTP ou HTTPS**, avec méthode, en-têtes et corps de requête ; un **sujet [Pub/Sub](#pubsub)**, où la tâche publie un message fixe ; une **application [App Engine](#app-engine)** du même projet. Pour une cible HTTP, le planificateur joint un jeton OIDC ou OAuth émis par un compte de service, ce qui suffit à appeler un service [Cloud Run](#cloud-run) privé ou une API Google Cloud.
- **Réessais.** Une exécution sans acquittement est réessayée selon la politique de la tâche : nombre maximal de tentatives, durée maximale de réessai, délai minimal et maximal, nombre de doublements. La livraison est **au moins une fois** — une même échéance peut donner deux exécutions, donc la cible doit être idempotente. L'en-tête `X-CloudScheduler-ScheduleTime`, constant d'une tentative à l'autre, sert justement à dédupliquer.
- **Limites.** 5 000 tâches par région, charge utile de 1 Mo, et 30 minutes au plus pour une exécution à cible HTTP, au-delà desquelles la tentative est considérée en échec puis réessayée.
- **Facturation** à la tâche et non à l'exécution : 0,10 $ par tâche et par tranche de 31 jours, au prorata des jours. Chaque compte de facturation dispose de 3 tâches gratuites par mois — mesurées au niveau du compte, pas du projet. Une tâche en pause reste comptée.

> [!TIP]
> Passer par un sujet Pub/Sub plutôt que d'appeler directement le service découple l'horaire du consommateur : on peut changer, dupliquer ou mettre en attente le traitement sans toucher à la tâche planifiée.

## À quoi ça sert

- Lancer un traitement récurrent : rapport quotidien, purge de données, rafraîchissement d'un cache, synchronisation avec un système tiers.
- Démarrer un **job [Cloud Run](#cloud-run)** ou une exécution [Workflows](#workflows) à heure fixe, sans écrire le moindre code de planification.
- Réveiller périodiquement un service qui descend à zéro, ou sonder une ressource externe à intervalle régulier.
- Remplacer les `crontab` dispersées sur des VM par une planification déclarative, versionnée et visible dans la console.

**À éviter** dès que l'horaire dépend d'un calcul, d'un calendrier métier ou de l'état d'une exécution précédente : il n'y a ni dépendance entre tâches, ni rattrapage des occurrences manquées, ni vue de l'historique au-delà des journaux. Un orchestrateur comme [Airflow](#managed-service-for-apache-airflow) ou un [workflow](#workflows) qui boucle convient mieux. À éviter aussi pour différer un travail unique déclenché par l'application : c'est le rôle d'une tâche datée dans [Cloud Tasks](#cloud-tasks).

## Alternatives en logiciel libre

- **cron** et **anacron** : l'original, sur n'importe quelle machine Unix ; même syntaxe d'horaire, mais aucun réessai ni journal centralisé.
- **Timers systemd** (LGPL 2.1) : planification intégrée à la gestion des services, avec horaires calendaires, rattrapage des occurrences manquées et journal.
- **CronJob Kubernetes** (Apache 2.0) : le même modèle dans un cluster, chaque occurrence créant un *Job* isolé, avec politique de réessai et historique.
- **Cronicle** (MIT) : ordonnanceur distribué avec interface web, catalogue de tâches, journaux et alertes.
- **Apache Airflow** (Apache 2.0) : quand la planification s'accompagne de dépendances entre traitements et de rattrapage.
