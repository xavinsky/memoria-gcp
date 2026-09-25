---
title: App Engine
subgroup: Serverless
icon: categories/serverless-computing
deprecie: "Google recommande [Cloud Run](#cloud-run) de préférence à App Engine pour tout nouveau projet ; le service reste ouvert et maintenu pour les applications existantes."
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 176, y: 10, w: 574, h: 282}
  nodes:
    users: {label: Utilisateurs, sub: "*.appspot.com", external: true, x: 8, y: 40, w: 150}
    dev: {label: Développeur, sub: "gcloud app deploy", external: true, x: 8, y: 196, w: 150}
    cb: {label: Cloud Build, sub: "image de la version", icon: categories/devops, x: 240, y: 200, w: 190}
    ae: {label: App Engine, sub: "services, versions", icon: categories/serverless-computing, focus: true, x: 240, y: 110, w: 210, h: 68}
    fs: {label: Firestore, sub: "mode Datastore", icon: categories/databases, x: 530, y: 44, w: 160}
    run: {label: Cloud Run, sub: "cible de migration", icon: produits/cloud-run, x: 530, y: 110, w: 170}
    tasks: {label: Cloud Tasks, sub: "files de tâches", icon: categories/integration-services, x: 530, y: 200, w: 160}
  flows:
    - {from: dev, to: cb, text: "Le déploiement envoie le code source ; Cloud Build en fait l'image d'une nouvelle version."}
    - {from: cb, to: ae, text: "La version rejoint son service sans recevoir de trafic tant qu'on ne l'a pas basculée."}
    - {from: users, to: ae, text: "Les requêtes arrivent sur l'URL appspot.com, réparties entre versions selon la répartition du trafic."}
    - {from: ae, to: fs, from_offset: -18, text: "L'application lit et écrit ses données dans Firestore en mode Datastore."}
    - {from: ae, to: tasks, from_offset: 18, text: "Les traitements différés partent dans une file Cloud Tasks, qui rappelle ensuite l'application."}
    - {from: ae, to: run, control: true, text: "La voie de sortie : porter chaque service vers Cloud Run, qui reprend les mêmes notions de service, de révision et de répartition du trafic."}
captures:
  - image: https://docs.cloud.google.com/static/appengine/docs/images/gae_dashboard_latency_graph.png
    page: https://docs.cloud.google.com/appengine/docs/standard/monitoring-and-alerting-latency
    legende: "Tableau de bord App Engine : sélection du service et de la version, latence des requêtes par centile"
docs:
  Page produit: https://cloud.google.com/appengine
  Documentation: https://docs.cloud.google.com/appengine/docs
  Choisir un environnement: https://docs.cloud.google.com/appengine/docs/the-appengine-environments
  Environnement standard: https://docs.cloud.google.com/appengine/docs/standard/overview
  Environnement flexible: https://docs.cloud.google.com/appengine/docs/flexible/overview
  Comparaison avec Cloud Run: https://docs.cloud.google.com/appengine/migration-center/run/compare-gae-with-run
  Référence app.yaml: https://docs.cloud.google.com/appengine/docs/standard/reference/app-yaml
  Services groupés hérités: https://docs.cloud.google.com/appengine/docs/standard/bundled-services-overview
  Calendrier de support des exécutions: https://docs.cloud.google.com/appengine/docs/standard/lifecycle/support-schedule
  Répartition du trafic: https://docs.cloud.google.com/appengine/docs/standard/splitting-traffic
  Référence dispatch.yaml: https://docs.cloud.google.com/appengine/docs/standard/reference/dispatch-yaml
  API Admin: https://docs.cloud.google.com/appengine/docs/admin-api/apis
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/app
  Quotas: https://docs.cloud.google.com/appengine/docs/standard/quotas
  Tarifs: https://cloud.google.com/appengine/pricing
---

## Ce que c'est

La plateforme d'hébergement d'applications historique de Google Cloud : on pousse du code source accompagné d'un fichier `app.yaml`, App Engine construit l'image, la déploie et l'expose sur une URL en `appspot.com`.

- **Un objet par projet.** Un projet héberge une seule *application* App Engine, dont la région est choisie à la création et ne change plus. L'application contient des **services** (le premier s'appelle `default`), chaque service contient des **versions**, chaque version tourne sur des **instances**. Le trafic d'un service se répartit entre ses versions par pourcentages, et chaque version garde une URL propre pour être testée à part.
- **Environnement standard.** Les instances tournent dans un bac à sable, sur une exécution fournie par Google : Go, Java, Node.js, PHP, Python, Ruby. Le démarrage se compte en secondes, la mise à l'échelle absorbe les pics brutaux et descend à zéro instance. La taille de l'instance se choisit par **classe** — de `F1` (384 Mo, mise à l'échelle automatique) à `B8` (3 Go, mise à l'échelle manuelle ou basique) — et la facturation se fait en heures d'instance.
- **Environnement flexible.** Les instances sont des conteneurs Docker sur des VM Compute Engine, donc un `Dockerfile` maison, des bibliothèques natives, des WebSockets, l'accès SSH pour déboguer et des processus d'arrière-plan. En contrepartie : démarrage et déploiement en minutes, **au moins une instance en permanence**, redémarrage hebdomadaire des VM pour appliquer les correctifs, et facturation au vCPU, à la mémoire et au disque.
- **Mise à l'échelle.** Trois modes : *automatique* (sur le trafic, avec des requêtes de préchauffage configurables), *basique* (une instance démarre à la première requête et s'éteint après inactivité, standard seulement) et *manuelle* (nombre d'instances fixe). Le délai de requête va de 10 minutes en mise à l'échelle automatique à 24 heures en manuelle ou basique côté standard, 60 minutes côté flexible.
- **Configuration en fichiers.** `app.yaml` décrit l'exécution, la classe d'instance, la mise à l'échelle, les gestionnaires d'URL et les variables ; `dispatch.yaml` route les URL vers les services, `cron.yaml` planifie des appels, `index.yaml` déclare les index Datastore.
- [!DECONSEILLE] **Services groupés hérités.** L'environnement standard donne accès à des APIs spécifiques à la plateforme — Memcache, files de tâches, Images, Mail, Datastore — qui n'existent nulle part ailleurs sur Google Cloud. C'est le principal point d'accroche d'une vieille application, et la principale difficulté d'une migration ; leurs équivalents Google Cloud (Memorystore, Cloud Tasks, Firestore) sont à préférer.
- **Cycle de vie des exécutions.** Chaque version de langage a une date de fin de support, puis de dépréciation, puis de décommissionnement, publiées dans le calendrier de support : une application laissée sur une exécution ancienne finit par ne plus se redéployer.

> [!WARNING]
> La région de l'application est définitive. Changer de région suppose un nouveau projet, un nouveau déploiement et une bascule DNS ; c'est souvent l'occasion de passer à Cloud Run, qui se déploie région par région.

## À quoi ça sert

- Maintenir et faire évoluer les applications App Engine déjà en service, nombreuses dans les systèmes d'entreprise : c'est la raison principale de rencontrer le produit aujourd'hui.
- Servir d'appui aux applications qui dépendent des services groupés hérités, tant qu'ils n'ont pas été remplacés par leurs équivalents Google Cloud (Memorystore, Cloud Tasks, Firestore).
- Préparer une migration : comprendre le découpage en services et versions, la répartition du trafic et le contenu de `app.yaml`, qui se transposent presque terme à terme vers Cloud Run.

**À éviter** pour un nouveau projet. La documentation d'App Engine recommande explicitement [Cloud Run](#cloud-run) aux nouveaux utilisateurs de Google Cloud, pour un service plus récent, moins cher et doté de capacités qui manquent ici : GPU, conteneurs auxiliaires, montages de volumes, jusqu'à 1 000 requêtes simultanées par instance, remises sur engagement d'usage. Cloud Run tourne d'ailleurs sur une grande partie de l'infrastructure de l'environnement standard, et reprend les mêmes notions sous d'autres noms — la *version* devient une *révision*.

## Alternatives en logiciel libre

- **Knative** : services, révisions et répartition du trafic sur Kubernetes ; le modèle le plus proche de celui d'App Engine.
- **Dokku** et **CapRover** : déploiement par `git push`, avec détection automatique du langage — l'expérience `gcloud app deploy` sur sa propre machine.
- **Cloud Native Buildpacks** : la construction d'une image à partir d'un répertoire de code source, sans écrire de `Dockerfile`.
- **Coolify** : plateforme d'hébergement auto-hébergée, avec environnements, domaines et certificats gérés.
- **Fission** : pour la part de l'application découpée en petits gestionnaires d'URL, déployés un par un.
