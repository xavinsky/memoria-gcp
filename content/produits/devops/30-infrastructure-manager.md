---
title: Infrastructure Manager
subgroup: Infrastructure as Code
icon: categories/devops
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 176, y: 16, w: 572, h: 268}
  nodes:
    repo: {label: Dépôt Terraform, sub: "modules, variables", external: true, x: 8, y: 122, w: 150, h: 60}
    cb: {label: Cloud Build, sub: "exécution éphémère", icon: categories/devops, x: 238, y: 30, w: 230}
    im: {label: Infrastructure Manager, sub: "déploiements, révisions", icon: categories/devops, focus: true, x: 238, y: 120, w: 230, h: 64}
    sa: {label: Compte de service, sub: "roles/config.agent", icon: categories/security-identity, x: 238, y: 216, w: 230}
    res: {label: Ressources du projet, sub: "VPC, GKE, Cloud SQL", icon: categories/management-tools, x: 528, y: 80, w: 210, h: 60}
    gcs: {label: Cloud Storage, sub: "état, journaux, copie", icon: produits/cloud-storage, x: 528, y: 200, w: 210}
  flows:
    - {from: repo, to: im, text: "La configuration Terraform vient d'un dépôt Git, d'un bucket Cloud Storage ou d'un répertoire local ; son point d'entrée doit être un module racine, sans bloc backend."}
    - {from: sa, to: im, control: true, text: "Terraform s'exécute sous l'identité d'un compte de service dédié, porteur du rôle Infra Manager Agent et des droits sur les ressources visées."}
    - {from: im, to: res, control: true, from_side: right, from_offset: -14, to_side: left, to_offset: 12, text: "Une prévisualisation exécute terraform plan et liste créations, modifications et suppressions, sans rien toucher."}
    - {from: im, to: cb, control: true, text: "Chaque déploiement crée un job Cloud Build éphémère, sur une image maintenue par Google, qui enchaîne terraform init, validate puis apply."}
    - {from: cb, to: res, from_side: right, to_side: left, to_offset: -12, text: "Le plan est appliqué : les ressources du projet sont créées, modifiées ou supprimées pour rejoindre l'état décrit."}
    - {from: im, to: gcs, from_offset: 14, text: "Le service crée un bucket où il dépose, pour chaque révision, les journaux, une copie de la configuration et le fichier d'état Terraform."}
docs:
  Documentation: https://docs.cloud.google.com/infrastructure-manager/docs
  Vue d'ensemble: https://docs.cloud.google.com/infrastructure-manager/docs/overview
  Terraform et Infra Manager: https://docs.cloud.google.com/infrastructure-manager/docs/infra-manager-terraform
  Déployer des ressources: https://docs.cloud.google.com/infrastructure-manager/docs/deploy-resources
  Prévisualiser un déploiement: https://docs.cloud.google.com/infrastructure-manager/docs/preview-deployment
  Déploiements et révisions: https://docs.cloud.google.com/infrastructure-manager/docs/deployments-revisions
  Fichier d'état: https://docs.cloud.google.com/infrastructure-manager/docs/state-file
  Configurer le compte de service: https://docs.cloud.google.com/infrastructure-manager/docs/configure-service-account
  Automatiser depuis un dépôt Git: https://docs.cloud.google.com/infrastructure-manager/docs/automate-git
  API REST: https://docs.cloud.google.com/infrastructure-manager/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/infra-manager
  Client Python: https://docs.cloud.google.com/python/docs/reference/config/latest
  Quotas et limites: https://docs.cloud.google.com/infrastructure-manager/docs/quotas
  Tarifs: https://cloud.google.com/infrastructure-manager/pricing
  Notes de version: https://docs.cloud.google.com/infrastructure-manager/docs/release-notes
---

## Ce que c'est

Terraform exécuté et entretenu par Google Cloud : on fournit la configuration, le service se charge du moteur, de l'état et des journaux. La documentation l'abrège en **Infra Manager** et appelle *blueprint* une configuration Terraform.

- **Déploiement et révisions.** Le déploiement est l'unité de gestion ; chaque application d'une configuration en produit une **révision**, qui conserve ses journaux, la configuration employée, la liste des ressources produites et le fichier d'état. Un même déploiement peut provisionner dans plusieurs régions et plusieurs projets.
- **Sources acceptées** : bucket Cloud Storage (versionné par Object Versioning), dépôt Git, ou répertoire local. Le point d'entrée doit être un module racine Terraform valide ; les blocs `backend` sont interdits, la génération de code Terraform n'est pas acceptée, et les *provisioners* [!DECONSEILLE] sont à éviter : Terraform les réserve aux cas qu'aucune ressource déclarative ne couvre.
- **Prévisualisation.** `gcloud infra-manager previews create` exécute un `terraform plan` et décrit les actions prévues, pour une création comme pour une mise à jour.
- **Exécution.** Le service crée un job [Cloud Build](#cloud-build) éphémère, sur une image qu'il maintient, qui télécharge le module, puis enchaîne `terraform init`, `terraform validate` et `terraform apply` — ou `terraform destroy` à la suppression. Certaines pannes passagères sont réessayées automatiquement, un nombre limité de fois. La version de Terraform se choisit par déploiement avec `--tf-version-constraint` ; elle peut être relevée lors d'une mise à jour, jamais abaissée.
- **État verrouillé.** Le fichier d'état vit dans un bucket `gs://PROJECT_NUMBER-LOCATION-blueprint-config` créé par le service. Pour l'inspecter ou le corriger — importer une ressource, en retirer une — il faut verrouiller le déploiement (`deployments lock`), télécharger l'état par une URL signée, le modifier, le réimporter, puis déverrouiller. Le verrou empêche toute autre opération pendant ce temps.
- **Compte de service.** Créer, mettre à jour ou supprimer un déploiement exige un compte de service : c'est sous son identité que Terraform s'exécute. Il porte le rôle **Infra Manager Agent** (`roles/config.agent`) et les droits sur les ressources visées ; l'utilisateur, lui, doit avoir `roles/iam.serviceAccountUser` sur ce compte. Consulter un déploiement n'en demande pas.
- **Facturation** : rien pour le service, tout pour ce qu'il consomme — minutes Cloud Build et stockage Cloud Storage.

## À quoi ça sert

- Tenir l'infrastructure d'un projet en Terraform sans héberger soi-même l'état, les verrous ni les *runners*.
- Faire du GitOps d'infrastructure : branché sur un dépôt par un déclencheur Cloud Build, une pull request produit une prévisualisation, la fusion applique la révision.
- Donner une trace auditable : chaque révision garde sa configuration, ses journaux et son état, consultables depuis la console ou `gcloud`.
- Restreindre le pouvoir d'application à un compte de service, plutôt que de distribuer des droits de création à chaque développeur.

**À éviter** pour déployer des applications sur les ressources ainsi créées : Infra Manager s'arrête à l'infrastructure, le déploiement applicatif relève de Cloud Build et Cloud Deploy. À éviter également quand l'équipe pilote déjà tout depuis Kubernetes — [Config Connector](#config-connector) y répond mieux — ou quand la chaîne Terraform existante repose sur des espaces de travail, des greffons et des *provisioners* que le service n'accepte pas.

> [!WARNING]
> Une révision peut remplacer ou supprimer une ressource ; le service ne migre pas les données et ne garantit aucune continuité de service. Réappliquer la révision précédente ne ramène pas les données perdues.

## Alternatives en logiciel libre

- **OpenTofu** : fork de Terraform sous licence MPL-2.0, hébergé par la Linux Foundation ; c'est l'équivalent libre du moteur. Terraform lui-même est sous licence BSL : source disponible, mais pas un logiciel libre.
- **Atlantis** : licence Apache 2.0, exécute `plan` sur chaque pull request et `apply` à la fusion, en commentant le fil — exactement le rôle de la prévisualisation et de l'automatisation par dépôt.
- **Terragrunt** : licence MIT, couche d'organisation au-dessus d'OpenTofu ou Terraform pour les environnements multiples.
- **Pulumi** : licence Apache 2.0 pour le moteur et les fournisseurs, infrastructure décrite dans un vrai langage de programmation ; le service d'état hébergé est payant, mais un backend local ou sur object storage fonctionne.
- **Crossplane** : licence Apache 2.0, projet CNCF, même intention depuis Kubernetes plutôt que depuis un moteur Terraform.
- **Ansible** : licence GPLv3, approche procédurale et sans état, adaptée quand la configuration des machines compte autant que la création des ressources.
