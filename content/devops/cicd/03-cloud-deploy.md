---
title: "Cloud Deploy : livrer et promouvoir"
id: cloud-deploy-livrer
---

[Cloud Deploy](#cloud-deploy) prend une image déjà construite et la fait avancer dans une suite d'environnements. Le pipeline décrit l'ordre des cibles et la stratégie propre à chacune ; une *release* fige l'application pour toutes les cibles ; chaque déploiement sur une cible est un *rollout*. L'intégration continue, Cloud Build ou la forge, ne fait qu'un appel : `gcloud deploy releases create`.

![Pipeline à trois cibles avec canary en prod](../../svg/cloud-deploy-pipeline.svg)

La release part en dev dès sa création. Une automatisation la promeut en staging quand le rollout de dev réussit ; staging lance ses tests de vérification. La promotion en prod attend une approbation, puis déploie en canary : 25 % du trafic, 50 %, puis `stable` à 100 %, chaque palier avançant à la main ou par automatisation.

## Ressources

| Ressource | Ce qu'elle porte |
|---|---|
| `DeliveryPipeline` | Liste ordonnée de cibles (`serialPipeline.stages`), avec par étape les profils Skaffold et la stratégie |
| `Target` | Un environnement d'exécution, l'exigence d'approbation (`requireApproval`), l'environnement d'exécution (`executionConfigs` : compte de service, pool Cloud Build, bucket) |
| Release | Manifestes rendus pour chaque cible, images, versions des outils ; immuable |
| Rollout | Déploiement d'une release sur une cible, découpé en **phases** (une seule en standard, une par palier en canary), elles-mêmes faites de **jobs** : `predeploy`, `deploy`, `verify`, `analysis`, `postdeploy` |
| `Automation` | Règles de promotion, d'avancée de phase, de réparation, attachées à un pipeline |
| `DeployPolicy` | Interdiction de rollouts sur des fenêtres de temps (gel des mises en production) |
| `CustomTargetType` | Rendu et déploiement vers une plateforme que Cloud Deploy ne connaît pas |

Pipeline et cibles se déclarent en YAML et s'enregistrent par `gcloud deploy apply --file=clouddeploy.yaml --region=REGION`. Les cibles vivent dans le projet et la région du pipeline, mais désignent des services ou des clusters d'autres projets (voir [La chaîne CI/CD](#chaine-cicd)).

## Cibles

| Cible | Déclaration | Canary | À savoir |
|---|---|---|---|
| Service, *job* ou *worker pool* [Cloud Run](#cloud-run) | `run.location: projects/P/locations/R` | Services et *worker pools*, pas les *jobs* | Un seul service, *job* ou *worker pool* par cible ; Cloud Run répartit lui-même le trafic entre révisions |
| Cluster [GKE](#gke) | `gke.cluster`, avec `dnsEndpoint`, `internalIp` ou `proxyUrl` pour un plan de contrôle privé | Par *service networking* ou par Gateway API | La vérification peut tourner dans le cluster |
| Cluster rattaché (*GKE attached cluster*) | `anthosCluster.membership` | Comme GKE | Clusters AWS, Azure ou sur site, joints par la passerelle Connect |
| Cible personnalisée | `customTarget.customTargetType` | Canary entièrement personnalisé | Tâches conteneurisées de rendu et de déploiement : Terraform, un autre cloud, une API |
| Multicible | `multiTarget.targetIds` | Oui | Déploiement parallèle sur plusieurs cibles enfants ; l'approbation se pose sur la multicible |

## Configuration

`clouddeploy.yaml` : trois étapes, des tests en staging, un canary en prod. Les cibles dev et staging se déclarent comme prod, sans approbation.

```yaml
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata:
  name: web
serialPipeline:
  stages:
  - targetId: dev
  - targetId: staging
    strategy:
      standard:
        verify:
          tasks:
          - type: container
            image: europe-west1-docker.pkg.dev/CICD_PROJECT_ID/app/tests-e2e
            command: ["/bin/sh"]
            args: ["-c", "pytest tests/e2e --base-url=$SERVICE_URL"]
            env:
              SERVICE_URL: "${{ rollout.metadata.cloud_run.service_url }}"
  - targetId: prod
    strategy:
      canary:
        runtimeConfig:
          cloudRun:
            automaticTrafficControl: true
        canaryDeployment:
          percentages: [25, 50]
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: prod
requireApproval: true
run:
  location: projects/PROD_PROJECT_ID/locations/europe-west1
executionConfigs:
- usages: [RENDER, DEPLOY]
  serviceAccount: deploy-prod@CICD_PROJECT_ID.iam.gserviceaccount.com
```

`skaffold.yaml` et le service Cloud Run à rendre ; `web` est le nom que `--images=web=...` remplace par l'image réelle :

```yaml
apiVersion: skaffold/v4beta7
kind: Config
metadata:
  name: web
manifests:
  rawYaml:
  - service.yaml
deploy:
  cloudrun: {}   # projet et région viennent de la cible
---
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: web
spec:
  template:
    spec:
      containers:
      - image: web
```

Une configuration qui varie selon l'environnement (nombre d'instances, variables) passe par des **profils Skaffold** nommés dans `stages[].profiles`, ou par des **paramètres de déploiement** (`deployParameters`) posés sur le pipeline, la cible ou la release. Sans `skaffold.yaml`, `--from-run-manifest=service.yaml` ou `--from-k8s-manifest=...` le fait générer à la création de la release.

Cloud Deploy exécute rendu et déploiement dans Cloud Build, avec son propre *fork* de Skaffold (version affichée `cd-skaffold`) : le `skaffold.yaml` reste le format de configuration. La documentation annonce aussi le retrait de Skaffold de la gcloud CLI après le 15 janvier 2027 et l'archivage du dépôt Skaffold public le 29 janvier 2027 (consulté en septembre 2026) : pour tester un rendu en local, Skaffold s'installera alors séparément.

## Stratégies de déploiement

| Stratégie | Principe | Quand |
|---|---|---|
| **Standard** | La cible passe d'un coup à la nouvelle version | Dev, staging, services internes |
| **Canary automatisé** | Paliers de pourcentages entiers (`percentages`), phases `canary-N` puis `stable` ; Cloud Deploy règle le trafic | Prod sur Cloud Run ou GKE, cas courant |
| **Canary automatisé personnalisé** | Chaque phase choisit son nom, son pourcentage, son profil Skaffold, sa vérification ; Cloud Deploy règle toujours le trafic | Tests différents selon le palier |
| **Canary personnalisé** | Comme ci-dessus, mais les manifestes de chaque phase répartissent eux-mêmes le trafic | Cible personnalisée, maillage de services maison |
| **Déploiement parallèle** | Une multicible déploie sur ses cibles enfants en même temps, en standard ou en canary | Plusieurs régions de prod |

Cloud Deploy n'a pas de stratégie **bleu-vert** nommée. Sur Cloud Run, l'équivalent se fait hors Cloud Deploy : `gcloud run deploy --no-traffic --tag=vert` crée une révision joignable par son URL taguée, puis `gcloud run services update-traffic --to-tags=vert=100` bascule tout le trafic. Dans Cloud Deploy, un canary personnalisé avec un premier palier bas et une vérification sur la nouvelle révision s'en rapproche.

## Promotion, approbation, automatisation

- **Promotion manuelle** : `gcloud deploy releases promote --release=REL --delivery-pipeline=web --region=REGION`, vers la cible suivante ou vers `--to-target`.
- **Approbation** : un rollout vers une cible `requireApproval: true` attend qu'un titulaire de `roles/clouddeploy.approver` lance `gcloud deploy rollouts approve` ou `reject`. La demande est publiée sur le sujet Pub/Sub `clouddeploy-approvals`, que l'on branche sur un outil de tickets (voir [Notifications et tickets](#notifications-tickets)).
- **Avancée d'un canary** : `gcloud deploy rollouts advance ROLLOUT --release=REL --delivery-pipeline=web --region=REGION`.
- **Gel** : une `DeployPolicy` bloque les rollouts sur des fenêtres ponctuelles ou hebdomadaires ; `roles/clouddeploy.policyOverrider` et `--override-deploy-policies` permettent une exception tracée.

L'automatisation remplace ces gestes par des règles. Le compte de service de l'automatisation doit pouvoir emprunter le compte d'exécution (`iam.serviceAccounts.actAs`).

```yaml
apiVersion: deploy.cloud.google.com/v1
kind: Automation
metadata:
  name: web/promouvoir-dev          # PIPELINE/AUTOMATISATION
serviceAccount: deploy-auto@CICD_PROJECT_ID.iam.gserviceaccount.com
selector:
  targets:
  - id: dev
rules:
- promoteReleaseRule:
    id: dev-vers-staging
    destinationTargetId: "@next"
---
apiVersion: deploy.cloud.google.com/v1
kind: Automation
metadata:
  name: web/canary-prod
serviceAccount: deploy-auto@CICD_PROJECT_ID.iam.gserviceaccount.com
selector:
  targets:
  - id: prod
rules:
- advanceRolloutRule:
    id: avancer-canary
    sourcePhases: ["canary-25", "canary-50"]
    wait: 30m
- repairRolloutRule:
    id: reparer
    repairPhases:
    - retry:
        attempts: 2
        wait: 1m
    - rollback:
        destinationPhase: stable
```

`timedPromoteReleaseRule` promeut selon un calendrier cron (fuseau IANA), par exemple chaque lundi à 9 h. Le `wait` des règles de promotion et d'avancée va jusqu'à 14 jours (`20160m`).

## Vérification, *hooks* et analyse

Dans un rollout, les jobs s'enchaînent ainsi : `predeploy`, `deploy`, `verify`, `analysis`, `postdeploy`. Tous se décrivent par des **tâches** conteneurisées (`type: container`, `image`, `command`, `args`, `env`), avec des paramètres système comme `${{ rollout.metadata.cloud_run.service_url }}` ou `${{ target.id }}`.

- **`verify`** : tests contre la version déployée ; un code de sortie non nul fait échouer le rollout. Sur GKE, la vérification peut tourner dans le cluster de l'application.
- **`predeploy`, `postdeploy`** : migration de schéma avant, purge de cache ou notification après. En canary, `predeploy` s'exécute au début de la première phase.
- **`analysis`** : pendant une durée (`duration: 300s`), surveille des règles d'alerte [Cloud Monitoring](#cloud-monitoring) (`googleCloud.alertPolicyChecks`) ; si l'une se déclenche, le rollout échoue, ce qu'une `repairRolloutRule` transforme en retour arrière. Un conteneur maison couvre un autre système de métriques, comme Prometheus ou Datadog.

## Retour arrière

`gcloud deploy targets rollback prod --delivery-pipeline=web --region=REGION` crée un **nouveau rollout** à partir de la dernière release déployée avec succès sur la cible, ou de celle désignée par `--release`. Les manifestes rendus sont ceux de cette release, stockés à sa création : rien n'est reconstruit. `gcloud deploy releases abandon` empêche ensuite toute promotion d'une release fautive.

## Pièges

- **Attendre un canary au premier déploiement.** Sans version en place, les phases canary sont sautées et le rollout passe à `stable` après confirmation.
- **Oublier `actAs`.** Celui qui crée la release doit avoir `roles/clouddeploy.releaser` et pouvoir emprunter les comptes de rendu et de déploiement ; l'automatisation aussi.
- **Laisser le compte d'exécution par défaut.** Sans `executionConfigs`, rendu et déploiement tournent sous le compte de service Compute Engine par défaut, pour toutes les cibles.
- **Déclarer un `executionConfigs` pour `RENDER` et `DEPLOY` seulement** alors que la cible a une vérification ou des *hooks* : il faut aussi `VERIFY`, `PREDEPLOY`, `POSTDEPLOY` ou `ANALYSIS`, dans le même bloc ou un autre.
- **Changer de région par erreur.** Pipeline, cibles, automatisations et releases sont régionaux ; la région du pipeline n'a pas à être celle des services déployés.
- **Utiliser Cloud Deploy pour un seul environnement**, ou pour du *GitOps* : pour une cible unique, `gcloud run deploy` suffit ; pour une réconciliation continue d'un dépôt, voir Argo CD ou Flux dans la fiche [Cloud Deploy](#cloud-deploy).

## Alternatives en logiciel libre

- **Argo CD** (Apache 2.0) : réconciliation continue entre un dépôt de manifestes et le cluster ; **Argo Rollouts** (Apache 2.0) apporte canary et bleu-vert avec analyse de métriques et retour arrière automatique. Limité à Kubernetes, sans Cloud Run.
- **Flux** (Apache 2.0) et **Flagger** (Apache 2.0) : même approche GitOps, Flagger pilotant le déploiement progressif à partir des métriques d'un maillage de services ou d'un Ingress.
- **Kargo** (Apache 2.0) : promotion d'un lot d'artefacts versionnés (*freight*) d'étape en étape, avec approbation et vérification, au-dessus d'Argo CD ; le modèle le plus proche des releases et des promotions de Cloud Deploy.
- **Spinnaker** (Apache 2.0) : pipelines de livraison multi-cloud, environnements successifs, approbations manuelles et analyse canary automatique ; nombreux microservices à exploiter.
- **Skaffold** (Apache 2.0) : le moteur de rendu et de déploiement de Cloud Deploy, utilisable seul ; il déploie, mais ne gère ni cibles successives ni approbation.
- **Helm** et **Kustomize** (Apache 2.0) : gabarits et variantes de manifestes par environnement, que Skaffold, Argo CD et Flux savent tous rendre.
