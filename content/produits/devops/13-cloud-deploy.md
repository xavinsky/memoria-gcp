---
title: Cloud Deploy
subgroup: CI/CD
icon: categories/devops
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 166, y: 16, w: 580, h: 268}
  nodes:
    cb: {label: Cloud Build, sub: intégration continue, icon: categories/devops, x: 176, y: 36, w: 186}
    ar: {label: Artifact Registry, sub: image versionnée, icon: categories/devops, x: 176, y: 150, w: 186}
    cd: {label: Cloud Deploy, sub: pipeline de livraison, icon: categories/devops, focus: true, x: 388, y: 120, w: 182, h: 60}
    dev: {label: Cible dev, sub: GKE, icon: produits/gke, x: 584, y: 36, w: 150}
    stg: {label: Cible staging, sub: GKE, icon: produits/gke, x: 584, y: 124, w: 150}
    prod: {label: Cible prod, sub: Cloud Run, icon: produits/cloud-run, x: 584, y: 212, w: 150}
  flows:
    - {from: cb, to: ar, text: "Le build publie l'image de l'application dans Artifact Registry"}
    - {from: cb, to: cd, from_side: right, to_side: top, control: true, text: "En fin de build, gcloud deploy releases create crée une release sur le pipeline"}
    - {from: ar, to: cd, text: "La release reprend les références d'images passées à sa création et rend les manifestes avec Skaffold"}
    - {from: cd, to: dev, from_side: right, to_side: left, text: "Le premier rollout déploie la release sur la cible dev"}
    - {from: dev, to: stg, control: true, text: "La promotion crée un nouveau rollout vers la cible suivante"}
    - {from: stg, to: prod, control: true, text: "Après approbation, la release est promue en production, par paliers canary"}
captures:
  - image: https://docs.cloud.google.com/static/deploy/images/automation_qs_pipeline_viz1.png
    page: https://docs.cloud.google.com/deploy/docs/deploy-app-automation
    legende: "Page d'un pipeline de livraison : enchaînement des cibles, métriques de déploiement et liste des releases"
  - image: https://docs.cloud.google.com/static/deploy/images/run_rollouts_success.png
    page: https://docs.cloud.google.com/deploy/docs/deploy-app-run
    legende: "Détail d'une release et liste de ses rollouts, un par cible"
docs:
  Page produit: https://cloud.google.com/deploy
  Documentation: https://docs.cloud.google.com/deploy/docs
  Vue d'ensemble: https://docs.cloud.google.com/deploy/docs/overview
  Architecture du service: https://docs.cloud.google.com/deploy/docs/architecture
  Fichiers de configuration: https://docs.cloud.google.com/deploy/docs/config-files
  Stratégies de déploiement: https://docs.cloud.google.com/deploy/docs/deployment-strategies
  Déploiement canary: https://docs.cloud.google.com/deploy/docs/deployment-strategies/canary
  Retour arrière: https://docs.cloud.google.com/deploy/docs/roll-back
  Automatisation: https://docs.cloud.google.com/deploy/docs/automation
  Vérification du déploiement: https://docs.cloud.google.com/deploy/docs/verify-deployment
  API REST: https://docs.cloud.google.com/deploy/docs/api/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/deploy
  Bibliothèques clientes: https://docs.cloud.google.com/deploy/docs/api/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/clouddeploy/latest
  Quotas et limites: https://docs.cloud.google.com/deploy/quotas
  Tarifs: https://cloud.google.com/deploy/pricing
  Notes de version: https://docs.cloud.google.com/deploy/docs/release-notes
---

## Ce que c'est

Service de livraison continue managé : il déploie une application sur une suite d'environnements, dans un ordre de promotion défini.

- **Quatre ressources.** Le *pipeline de livraison* (`DeliveryPipeline`) nomme la séquence des cibles. La *cible* (`Target`) désigne un environnement d'exécution : cluster GKE, cluster rattaché (*GKE attached cluster*), service, *job* ou *worker pool* Cloud Run. La *release* fige un état de l'application — manifestes rendus pour chaque cible, avec les références d'images telles qu'on les passe — un tag reste un tag, d'où l'intérêt de passer `IMAGE@sha256:...`. Le *rollout* est le déploiement d'une release sur une cible ; il en faut un par cible.
- **Configuration en YAML**, appliquée par `gcloud deploy apply` : pipeline et cibles dans le même fichier ou dans des fichiers séparés. Une même cible peut servir à plusieurs pipelines, mais ne peut apparaître qu'une fois dans un pipeline donné.
- **Skaffold** fait le rendu et le déploiement : c'est lui qui transforme les manifestes source en manifestes concrets par cible (profils, `kustomize`, `helm`), puis les applique. Le rendu et le déploiement s'exécutent dans [Cloud Build](#cloud-build), dans la région du pipeline.
- **Promotion.** Le premier appel crée la release et le rollout vers la première cible. Chaque promotion crée un nouveau rollout vers la cible suivante. Une cible peut exiger une approbation (`requireApproval`), qui émet un message Pub/Sub exploitable par un outil de tickets.
- **Stratégies.** *Standard* : la cible est mise à jour d'un coup. *Canary* : le déploiement est progressif, par paliers de pourcentage que l'on choisit (25, 50, 75, puis `stable`) ; chaque palier est une *phase* du rollout. Le canary existe en trois formes — automatique, automatique personnalisé, entièrement personnalisé — et fonctionne sur toutes les cibles : GKE (service networking ou Gateway API) et Cloud Run, qui répartit lui-même le trafic entre révisions. Les deux stratégies acceptent le déploiement parallèle vers plusieurs cibles (*multi-target*).
- **Retour arrière.** `gcloud deploy targets rollback` crée un nouveau rollout à partir d'une release antérieure — par défaut la dernière dont le déploiement sur cette cible a réussi, ou celle que l'on désigne avec `--release`.
- **Automatisation.** Une ressource `Automation` attachée au pipeline peut promouvoir une release après un rollout réussi ou selon un calendrier cron, faire avancer les phases d'un canary avec un temps d'attente par palier, et réessayer un rollout en échec puis revenir en arrière après un nombre d'essais donné.
- **Vérification et *hooks*.** Un rollout peut inclure un *job* de vérification (`verify`) et des étapes avant et après déploiement (`predeploy`, `postdeploy`).
- **Facturation** au pipeline actif et multicible : 5 $ par mois et par pipeline qui référence plus d'une cible et pour lequel au moins une release ou un rollout a été créé dans le mois ; le premier est gratuit par compte de facturation, et un pipeline à cible unique n'est pas facturé. S'y ajoutent les minutes de Cloud Build consommées par le rendu et le déploiement.

> [!TIP]
> Le premier déploiement d'une application sur une cible ne peut pas être un canary : il n'y a pas de version à remplacer progressivement. Les phases canary sont sautées, et le rollout passe directement à la phase `stable`.

## À quoi ça sert

- Enchaîner *dev*, *staging* et *prod* avec une progression explicite, des approbations et une trace de chaque déploiement.
- Déployer progressivement sur Cloud Run ou GKE sans écrire soi-même la mécanique de répartition du trafic.
- Revenir à une version antérieure en une commande, avec exactement les paramètres du dernier déploiement réussi.
- Brancher une livraison continue derrière n'importe quelle intégration continue : l'appel qui crée la release peut venir de Cloud Build, de GitHub Actions, de GitLab CI ou d'un simple script.

**À éviter** quand le déploiement se résume à une seule cible : le pipeline ajoute la configuration Skaffold, les ressources et l'exécution Cloud Build sans rien apporter — une étape `gcloud run deploy` dans le build suffit. À éviter aussi pour du déploiement par réconciliation d'un dépôt Git (*GitOps*) : Cloud Deploy pousse un rollout, il ne surveille pas en continu l'écart entre le dépôt et le cluster ; c'est le terrain d'Argo CD ou de Flux.

## Alternatives en logiciel libre

- **Argo CD** : livraison continue GitOps sur Kubernetes, avec réconciliation permanente entre le dépôt et le cluster ; **Argo Rollouts** y ajoute les stratégies canary et bleu-vert, avec analyse automatique des métriques.
- **Flux** : l'autre implémentation GitOps de la CNCF, avec **Flagger** pour le déploiement progressif et le retour arrière automatique.
- **Spinnaker** : plateforme de livraison multi-cloud, la plus proche du modèle de Cloud Deploy — pipelines, environnements successifs, approbations manuelles, stratégies de déploiement.
- **Skaffold** : justement le moteur de rendu et de déploiement utilisé par Cloud Deploy, utilisable seul pour la boucle de développement locale et pour déployer.
- **Helm** et **Kustomize** : gabarits et variantes de manifestes par environnement, la brique que Skaffold orchestre.
- **Keptn** : orchestration de livraison pilotée par les objectifs de niveau de service, pour la partie vérification et décision de promotion.
