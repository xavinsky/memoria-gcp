---
title: Cloud Run
subgroup: Serverless
icon: produits/cloud-run
aka: Cloud Functions (devenu Cloud Run functions)
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 10, w: 578, h: 282}
  nodes:
    users: {label: Utilisateurs, sub: "web, API", external: true, x: 8, y: 122, w: 140}
    cb: {label: Cloud Build, sub: "image du service", icon: categories/devops, x: 186, y: 30, w: 176}
    lb: {label: Load balancer, sub: "HTTPS, domaine", icon: categories/networking, x: 186, y: 122, w: 176}
    sched: {label: Cloud Scheduler, sub: "tâches planifiées", icon: categories/integration-services, x: 186, y: 214, w: 176}
    ar: {label: Artifact Registry, sub: "image, digest", icon: categories/devops, x: 420, y: 30, w: 190}
    run: {label: Cloud Run, sub: "service, révisions", icon: produits/cloud-run, focus: true, x: 420, y: 118, w: 180, h: 64}
    sql: {label: Cloud SQL, sub: "adresse IP privée", icon: produits/cloud-sql, x: 420, y: 214, w: 190}
  flows:
    - {from: cb, to: ar, text: "Le build construit l'image du service et la pousse dans Artifact Registry."}
    - {from: ar, to: run, text: "Le déploiement crée une révision immuable à partir de l'image, épinglée par son digest."}
    - {from: users, to: lb, text: "Les requêtes HTTPS arrivent sur le domaine personnalisé porté par le load balancer."}
    - {from: lb, to: run, to_offset: -20, text: "Cloud Run répartit ensuite les requêtes entre les révisions selon les pourcentages de trafic configurés."}
    - {from: sched, to: run, to_offset: 20, control: true, text: "Cloud Scheduler déclenche à heure fixe l'exécution d'un job, qui tourne jusqu'au bout puis s'arrête."}
    - {from: run, to: sql, text: "Le service atteint la base par son adresse IP privée, par sortie VPC directe."}
docs:
  Page produit: https://cloud.google.com/run
  Documentation: https://docs.cloud.google.com/run/docs
  Vue d'ensemble: https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run
  Modèle de ressources: https://docs.cloud.google.com/run/docs/resource-model
  Contrat d'exécution du conteneur: https://docs.cloud.google.com/run/docs/container-contract
  Mise à l'échelle automatique: https://docs.cloud.google.com/run/docs/about-instance-autoscaling
  Requêtes simultanées: https://docs.cloud.google.com/run/docs/about-concurrency
  Déploiements progressifs et retours arrière: https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration
  GPU: https://docs.cloud.google.com/run/docs/configuring/services/gpu
  Sortie VPC directe: https://docs.cloud.google.com/run/docs/configuring/connecting-vpc
  Contrôle d'accès: https://docs.cloud.google.com/run/docs/securing/managing-access
  Fonctions: https://docs.cloud.google.com/run/docs/functions/comparison
  API REST: https://docs.cloud.google.com/run/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/run
  Client Python: https://docs.cloud.google.com/python/docs/reference/run/latest
  Quotas et limites: https://docs.cloud.google.com/run/quotas
  Tarifs: https://cloud.google.com/run/pricing
  Notes de version: https://docs.cloud.google.com/run/docs/release-notes
---

## Ce que c'est

Plateforme d'exécution de conteneurs sans serveur à administrer : on fournit une image (ou un simple répertoire de code source, que Google construit avec les *buildpacks*), Cloud Run s'occupe du reste — mise à l'échelle, certificat TLS, journaux, identité.

- **Quatre formes de ressources.** Un **service** répond à des requêtes HTTP sur un point d'entrée HTTPS stable. Un **job** exécute un travail qui se termine, lancé à la main, par un planificateur ou depuis un workflow ; un *job tableau* démarre plusieurs tâches indépendantes en parallèle. Un **worker pool** traite en continu des charges sans requête entrante, typiquement la consommation d'une file (Pub/Sub, Kafka, RabbitMQ) ; il ne s'ajuste pas tout seul, sauf par l'autoscaling sur métriques externes. Une **instance** [!PREVERSION] est un processus unique, adressable individuellement et durable, pour un agent ou un environnement de développement.
- **Fonctions.** Les *Cloud Run functions* sont l'ancien produit Cloud Functions : une fonction est aujourd'hui un service Cloud Run déployé depuis le code source, avec un déclencheur HTTP ou CloudEvents. Elles héritent de tout le reste : jusqu'à 1 000 requêtes simultanées par instance, 60 minutes de délai, GPU, montages de volumes, répartition du trafic. La 1re génération, pilotée par l'API Cloud Functions v1, reste à part et n'accepte qu'une requête par instance.
- **Révisions et trafic.** Chaque déploiement ou changement de configuration crée une **révision** immuable. Le trafic se répartit entre révisions par pourcentages : déploiement progressif (1 %, puis davantage), retour arrière instantané, et *tags* de révision qui donnent une URL dédiée pour tester une révision sans trafic. Une révision qui ne reçoit rien ne coûte rien ; au-delà de 1 000 révisions, les plus anciennes sont supprimées.
- **Mise à l'échelle.** L'autoscaler vise 60 % d'utilisation du processeur et de la concurrence, en moyennant sur 1 et 10 minutes. Par défaut une révision descend à **zéro instance** et monte jusqu'à **100** ; on relève le plafond, on fixe des **instances minimales** pour garder des instances chaudes, ou on passe en mise à l'échelle manuelle à nombre d'instances fixe. Il n'y a pas de mise à l'échelle sur la mémoire.
- **Concurrence.** Une instance traite plusieurs requêtes à la fois : le maximum vaut 80 par vCPU au déploiement par `gcloud` ou Terraform, 80 depuis la console, et plafonne à 1 000. Abaisser ce nombre multiplie les instances et le coût ; `--concurrency=1` convient à un code qui ne supporte pas le parallélisme.
- **Ressources et durée.** Jusqu'à 8 vCPU et 32 Gio de mémoire par instance, délai de requête configurable jusqu'à 60 minutes (5 minutes par défaut). Le système de fichiers est un calque en mémoire, perdu à l'arrêt : persister passe par Cloud Storage, un montage NFS, ou un signal `SIGTERM` capté pour vider les tampons.
- **GPU.** Une carte NVIDIA L4 (24 Gio de VRAM) ou RTX PRO 6000 Blackwell (96 Gio), un GPU au maximum par instance, pilotes déjà installés, démarrage en 5 secondes environ, dans un petit nombre de régions. La facturation à l'instance est obligatoire ; la **redondance zonale**, active par défaut, réserve de la capacité GPU dans plusieurs zones de la région, à un tarif plus élevé.
- **Réseau.** En entrée, le service est public, restreint au trafic interne au VPC, ou placé derrière un load balancer interne ou externe ; Identity-Aware Proxy peut n'admettre que des utilisateurs authentifiés. En sortie, la **sortie VPC directe** est la méthode recommandée pour atteindre des adresses privées : pas de VM à maintenir, étiquettes réseau par révision, latence plus basse que les connecteurs d'accès VPC sans serveur [!DECONSEILLE], qui imposent des VM de connexion à dimensionner, et facturation limitée au trafic.
- **Identité et appel.** Chaque révision tourne sous un compte de service, que les bibliothèques clientes utilisent pour s'authentifier auprès des APIs Google Cloud. Côté appelant, le rôle **Cloud Run Invoker** (`roles/run.invoker`) autorise l'invocation ; il est vérifié par défaut, et rendre un service public consiste à désactiver ce contrôle plutôt qu'à accorder le rôle à `allUsers`.
- **Facturation** au vCPU-seconde et au Gio-seconde, arrondie à 100 ms. En **facturation à la requête**, une instance qui ne traite rien n'est pas facturée mais chaque requête l'est ; en **facturation à l'instance**, on paie toute la durée de vie de l'instance, sans frais par requête. Le palier gratuit mensuel couvre 180 000 vCPU-secondes, 360 000 Gio-secondes et 2 millions de requêtes.

> [!TIP]
> La concurrence est le premier levier de coût d'un service Cloud Run : passer de 1 à 80 requêtes simultanées divise le nombre d'instances par autant, à condition que le code soit réellement parallélisable.

## À quoi ça sert

- Sites, applications web et APIs HTTP ou gRPC, y compris derrière un domaine propre et un CDN.
- Microservices privés qui s'appellent entre eux par jeton d'identité, sans exposition publique.
- Traitement d'événements : abonnements *push* Pub/Sub, événements Eventarc, déclencheurs Cloud Storage.
- Travaux ponctuels ou planifiés avec les jobs : migrations de schéma, traitement en parallèle de tous les fichiers d'un bucket, inférence par lots.
- Inférence de modèles d'IA sur GPU, avec descente à zéro entre deux vagues de trafic.

**À éviter** quand l'application a besoin d'un état local durable, de ports autres que HTTP, ou d'un contrôle fin sur les machines : préférer [Compute Engine](#compute-engine) pour une VM, [GKE](#gke) dès qu'il faut des charges avec état, des opérateurs Kubernetes ou une topologie réseau particulière. À éviter aussi pour un travail continu qui ne descend jamais à zéro et monopolise plusieurs vCPU en permanence : un groupe d'instances géré ou un pool de nœuds revient moins cher à l'heure.

## Alternatives en logiciel libre

- **Knative** : le projet dont Cloud Run reprend le modèle — service, révision, répartition du trafic, descente à zéro — au-dessus de Kubernetes ; l'équivalent le plus direct.
- **Fission** : plateforme de fonctions sur Kubernetes, pour la partie *Cloud Run functions*.
- **Dokku** et **CapRover** : hébergement d'applications par `git push` sur une seule machine, pour des besoins plus modestes.
- **Cloud Native Buildpacks** : la brique qui transforme un répertoire de code source en image, utilisable indépendamment.
- **KEDA** : mise à l'échelle sur événements (longueur de file Kafka, Pub/Sub, RabbitMQ), l'équivalent de l'autoscaling des worker pools.
