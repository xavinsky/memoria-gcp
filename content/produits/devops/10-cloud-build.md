---
title: Cloud Build
subgroup: CI/CD
icon: categories/devops
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 166, y: 16, w: 584, h: 268}
  nodes:
    git: {label: GitHub / GitLab, sub: dépôt source, external: true, x: 10, y: 115, w: 150}
    dc: {label: Developer Connect, sub: connexion au dépôt, icon: categories/developer-tools, x: 180, y: 36, w: 186}
    trig: {label: Déclencheur, sub: push ou pull request, icon: categories/devops, x: 180, y: 180, w: 186}
    cb: {label: Cloud Build, sub: cloudbuild.yaml, icon: categories/devops, focus: true, x: 384, y: 120, w: 150, h: 60}
    ar: {label: Artifact Registry, sub: image du build, icon: categories/devops, x: 552, y: 36, w: 186}
    run: {label: Cloud Run, sub: service mis à jour, icon: produits/cloud-run, x: 552, y: 200, w: 186}
  flows:
    - {from: git, to: dc, from_side: right, to_side: left, control: true, text: "Le dépôt GitHub ou GitLab est relié au projet par une connexion Developer Connect"}
    - {from: dc, to: trig, control: true, text: "Le déclencheur s'abonne aux événements du dépôt : poussée sur une branche, tag, pull request"}
    - {from: trig, to: cb, text: "L'événement lance un build, avec les substitutions du déclencheur comme paramètres"}
    - {from: cb, to: ar, to_offset: -45, text: "Les étapes de cloudbuild.yaml construisent l'image et la poussent dans Artifact Registry"}
    - {from: cb, to: run, to_offset: -45, text: "Une dernière étape déploie la nouvelle révision du service"}
    - {from: ar, to: run, from_offset: 45, to_offset: 45, text: "Cloud Run tire l'image par son digest au démarrage de la révision"}
captures:
  - image: https://docs.cloud.google.com/build/images/docker-build-history.png
    page: https://docs.cloud.google.com/build/docs/build-push-docker-image
    legende: "Historique des builds : état, source et branche de chaque exécution"
  - image: https://docs.cloud.google.com/build/images/docker-artifacts.png
    page: https://docs.cloud.google.com/build/docs/build-push-docker-image
    legende: "Onglet des artefacts d'un build : journal et image produite dans Artifact Registry"
docs:
  Page produit: https://cloud.google.com/build
  Documentation: https://docs.cloud.google.com/build/docs
  Vue d'ensemble: https://docs.cloud.google.com/build/docs/overview
  Schéma du fichier de build: https://docs.cloud.google.com/build/docs/build-config-file-schema
  Déclencheurs: https://docs.cloud.google.com/build/docs/automating-builds/create-manage-triggers
  Substitutions: https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values
  Connexions aux dépôts: https://docs.cloud.google.com/build/docs/repositories
  Pools privés: https://docs.cloud.google.com/build/docs/private-pools/private-pools-overview
  Provenance de build: https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance
  API REST: https://docs.cloud.google.com/build/docs/api/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/builds
  Bibliothèques clientes: https://docs.cloud.google.com/build/docs/api/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/cloudbuild/latest
  Quotas et limites: https://docs.cloud.google.com/build/quotas
  Tarifs: https://cloud.google.com/build/pricing
  Notes de version: https://docs.cloud.google.com/build/docs/release-notes
---

## Ce que c'est

Service d'exécution de builds managé. Il récupère une source, enchaîne des étapes décrites dans un fichier de configuration et produit des artefacts : images de conteneurs, archives Java, binaires.

- **Étapes en conteneurs.** Un build est une suite d'étapes, chacune exécutée comme un `docker run` d'une image de *builder*. Les étapes partagent un espace de travail `/workspace` et un réseau Docker local nommé `cloudbuild`, ce qui leur permet de se passer des fichiers et de communiquer entre elles. On utilise les builders officiels, ceux de la communauté, ou n'importe quelle image publique (Ubuntu, Gradle, Maven).
- **Configuration.** `cloudbuild.yaml` (ou JSON) décrit `steps`, `images` à pousser, `artifacts`, `substitutions`, `options`, `timeout`, `availableSecrets`. À défaut, un simple `Dockerfile` ou un buildpack suffit.
- **Substitutions.** Variables résolues au moment du build. Les substitutions par défaut couvrent le contexte (`$PROJECT_ID`, `$BUILD_ID`, `$LOCATION`), le déclencheur (`$TRIGGER_NAME`, `$COMMIT_SHA`, `$SHORT_SHA`, `$BRANCH_NAME`, `$TAG_NAME`, `$REF_NAME`) et les *pull requests* (`$_PR_NUMBER`, `$_BASE_BRANCH`, `$_HEAD_BRANCH`). Les substitutions maison commencent par un tiret bas : `${_REPOSITORY}`.
- **Déclencheurs.** Un déclencheur lance un build sur un événement : poussée de branche ou de tag, *pull request*, message Pub/Sub, webhook entrant, ou appel manuel. Il porte son propre filtre (branche, chemins de fichiers), son compte de service et ses substitutions.
- **Connexion aux dépôts.** Deux mécanismes coexistent : **[Developer Connect](#developer-connect)**, la couche de connexion aux forges commune à plusieurs services Google Cloud, et les *Cloud Build repositories (2e génération)*, gérables par API, `gcloud` et Terraform. Les deux couvrent GitHub, GitHub Enterprise, GitLab, GitLab Enterprise Edition, Bitbucket Cloud et Bitbucket Data Center. Seule la 2e génération permet les déclencheurs manuels, Pub/Sub et webhook.
- **Pools d'exécution.** Le *pool par défaut* est un environnement hébergé avec accès à l'internet public, 5 types de machines et 30 builds simultanés au maximum. Un *pool privé* est un pool de workers dédié, créé dans une région, capable d'atteindre un VPC par appairage de réseaux privés, compatible avec VPC Service Controls, avec des plages d'adresses internes statiques, la possibilité de supprimer les adresses IP publiques, 64 types de machines et plus de 100 builds simultanés.
- **Chaîne logicielle.** Cloud Build satisfait le niveau 3 de SLSA et produit une *provenance* de build signée, stockée par [Artifact Analysis](#artifact-analysis), que [Binary Authorization](#binary-authorization) peut exiger au déploiement.
- **Facturation** à la minute de build, au prorata des secondes, selon le type de machine ; le temps d'attente en file n'est pas facturé. Chaque compte de facturation dispose de 2 500 minutes gratuites par mois sur `e2-standard-2` en pool par défaut.

> [!WARNING]
> Un build lancé sans région explicite s'exécute en `global`, donc sur le pool par défaut. Pour utiliser un pool privé, il faut choisir la région du pool sur le déclencheur et désigner le pool dans `options.pool`.

## À quoi ça sert

- Construire et pousser des images de conteneurs à chaque commit, puis les déployer sur Cloud Run ou GKE.
- Exécuter des tests, des analyses statiques et des contrôles de qualité avant publication.
- Servir de moteur d'exécution à d'autres services : [Cloud Deploy](#cloud-deploy) s'en sert pour le rendu et le déploiement, Terraform et les pipelines d'infrastructure y tournent aussi.
- Atteindre des ressources privées (bases de données internes, dépôts d'artefacts d'entreprise, réseau on-premises) depuis un build, via un pool privé appairé au VPC.

**À éviter** comme orchestrateur de livraison : Cloud Build ne connaît ni les environnements successifs, ni la promotion, ni le retour arrière. Enchaîner `gcloud run deploy` dans une étape de build convient pour un seul environnement ; dès qu'il y a *dev*, *staging* et *prod*, confier la livraison à [Cloud Deploy](#cloud-deploy). À éviter aussi pour des builds très longs ou très nombreux sur une flotte que l'on administre déjà : un runner GitLab CI ou GitHub Actions auto-hébergé sur GKE revient souvent moins cher à la minute.

## Alternatives en logiciel libre

- **Tekton** : moteur de pipelines CI/CD sur Kubernetes, dont les *Tasks* et *Steps* reprennent exactement le modèle « une étape = un conteneur » de Cloud Build ; c'est l'équivalent le plus direct.
- **Jenkins** : serveur d'automatisation historique, très extensible ; son modèle de *pipeline as code* (`Jenkinsfile`) couvre le même terrain, avec des agents à administrer.
- **GitLab CI** et **Woodpecker CI** : intégration continue attachée à la forge, déclencheurs sur commit et *merge request* comme les déclencheurs Cloud Build.
- **Argo Workflows** : moteur de workflows en conteneurs sur Kubernetes, pour les enchaînements complexes ou parallèles.
- **Buildpacks (Cloud Native Buildpacks)**, **Buildah**, **BuildKit** : construction d'images sans démon Docker privilégié, pour la partie « produire une image » du build.
- **Concourse** : pipelines déclaratifs orientés ressources, avec reconstruction complète à chaque exécution.
