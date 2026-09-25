---
title: Config Connector
subgroup: Infrastructure as Code
icon: categories/devops
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 176, y: 16, w: 572, h: 268}
    - {label: Cluster GKE, x: 196, y: 40, w: 290, h: 200}
  nodes:
    git: {label: Dépôt Git, sub: "manifestes YAML", external: true, x: 8, y: 140, w: 150}
    sync: {label: Config Sync, sub: "application continue", icon: categories/containers, x: 216, y: 62, w: 210}
    cc: {label: Config Connector, sub: "opérateur et CRD", icon: categories/devops, focus: true, x: 216, y: 150, w: 210, h: 64}
    res: {label: Ressources du projet, sub: "Cloud SQL, Pub/Sub, GCS", icon: categories/management-tools, x: 528, y: 80, w: 210, h: 60}
    wi: {label: Workload Identity, sub: "compte de service IAM", icon: categories/security-identity, x: 528, y: 210, w: 210}
  flows:
    - {from: git, to: sync, text: "Les ressources Google Cloud sont décrites en YAML Kubernetes et versionnées dans le même dépôt que les manifestes applicatifs."}
    - {from: sync, to: cc, text: "Config Sync, Argo CD ou un simple kubectl apply pose les objets dans le cluster : un SQLInstance, un PubSubTopic, un StorageBucket sont des ressources personnalisées."}
    - {from: wi, to: cc, control: true, to_offset: 16, text: "Le contrôleur agit sous l'identité d'un compte de service IAM obtenue par Workload Identity Federation for GKE : ses rôles bornent ce que le cluster peut créer."}
    - {from: cc, to: res, from_offset: -16, text: "Le contrôleur appelle les APIs Google Cloud pour amener chaque ressource à l'état décrit dans son champ spec, le namespace désignant le projet visé."}
    - {from: res, to: cc, from_side: bottom, to_side: top, text: "Il relit l'état réel, le recopie dans le champ status, et corrige au passage suivant toute dérive faite à la main : la réconciliation est continue."}
docs:
  Documentation: https://docs.cloud.google.com/config-connector/docs
  Vue d'ensemble: https://docs.cloud.google.com/config-connector/docs/overview
  Choisir un mode d'installation: https://docs.cloud.google.com/config-connector/docs/concepts/installation-types
  Installation manuelle: https://docs.cloud.google.com/config-connector/docs/how-to/install-manually
  Add-on GKE: https://docs.cloud.google.com/config-connector/docs/how-to/install-upgrade-uninstall
  Premiers pas: https://docs.cloud.google.com/config-connector/docs/how-to/getting-started
  CRD et objets: https://docs.cloud.google.com/config-connector/docs/concepts/resources
  Namespaces et projets: https://docs.cloud.google.com/config-connector/docs/concepts/namespaces-and-projects
  Ressources disponibles: https://docs.cloud.google.com/config-connector/docs/reference/overview
  Secrets: https://docs.cloud.google.com/config-connector/docs/how-to/secrets
  Gérer et supprimer des ressources: https://docs.cloud.google.com/config-connector/docs/how-to/managing-deleting-resources
  Config Controller: https://docs.cloud.google.com/kubernetes-engine/config-controller/docs/overview
  Dépannage: https://docs.cloud.google.com/config-connector/docs/troubleshooting
  Notes de version: https://docs.cloud.google.com/config-connector/docs/release-notes
---

## Ce que c'est

Extension Kubernetes open source qui rend les ressources Google Cloud pilotables depuis un cluster : on les déclare en YAML, on les applique avec `kubectl`, un contrôleur les crée et les maintient.

- **CRD et contrôleurs.** Le produit installe une collection de *Custom Resource Definitions* — une par type de ressource Google Cloud — et les contrôleurs qui les servent. Créer un objet `kind: SQLInstance` crée une instance Cloud SQL. `kubectl get crds --selector cnrm.cloud.google.com/managed-by-kcc=true` liste ce que la version installée sait gérer.
- **spec et status.** Le champ `spec` porte l'état voulu, le champ `status` l'état réel, relu périodiquement ; `status.conditions` dit si la ressource est prête et pourquoi elle ne l'est pas. Le nom de l'objet sert par défaut de nom à la ressource Google Cloud, `spec.resourceID` permet d'en imposer un autre.
- **Namespace et projet.** Le namespace dans lequel l'objet est créé détermine le projet Google Cloud qui contiendra la ressource.
- **Réconciliation asynchrone.** Le contrôleur rapproche l'état déclaré de l'état réel en continu, sous l'identité du **compte de service IAM de Config Connector**, jamais sous celle de la personne qui a appliqué le manifeste. Pouvoir créer un objet dans un namespace surveillé, c'est donc pouvoir agir sur le cloud avec cette identité : la sécurité du dispositif tient au contrôle de qui peut écrire dans le cluster, comme pour l'identité d'un pipeline CI/CD.
- **Trois installations.** L'**installation manuelle** de l'opérateur est la voie recommandée : elle laisse choisir le mode *namespaced* (conseillé) ou *cluster*, et la version. **Config Controller** est un plan de contrôle hébergé qui embarque Config Connector et Config Sync, mis à jour par Google, au prix d'une restriction sur les charges de travail que le cluster accepte. L'**add-on GKE**, activable à la création du cluster, n'existe que sur GKE Standard, pas en Autopilot, et accuse souvent douze mois ou plus de retard sur la version courante.
- **Authentification.** Sur GKE, Workload Identity Federation for GKE permet à un ServiceAccount Kubernetes d'emprunter le compte de service IAM ; ailleurs — sur site, autre cloud — on passe par Cloud Identity.
- **Facturation** : le composant est gratuit et publié sous licence Apache 2.0. On paie le cluster qui l'héberge et les ressources qu'il crée.

## À quoi ça sert

- Décrire l'infrastructure dans le même dépôt et le même format que les applications, pour une équipe dont Kubernetes est déjà l'outil de travail.
- Corriger automatiquement les dérives : toute modification faite à la main dans la console est ramenée à l'état déclaré au cycle suivant, ce qu'un `terraform apply` ponctuel ne fait pas.
- Faire du GitOps complet : un dépôt, un opérateur de synchronisation, et plus personne n'a besoin de droits d'écriture directs sur le projet.
- Reprendre des ressources existantes sous gestion déclarative sans les recréer.

**À éviter** quand il n'y a pas de cluster Kubernetes : faire tourner un cluster pour le seul plaisir de créer des buckets coûte plus cher que [Infrastructure Manager](#infrastructure-manager). À éviter aussi pour créer le cluster lui-même — problème d'amorçage, que Config Controller résout en hébergeant le plan de contrôle — et pour les ressources sans CRD correspondante, qu'il faut alors traiter autrement.

> [!WARNING]
> Par défaut, supprimer un objet Kubernetes supprime la ressource Google Cloud correspondante. Pour qu'elle survive au `kubectl delete`, poser l'annotation `cnrm.cloud.google.com/deletion-policy: abandon`.

## Alternatives en logiciel libre

Config Connector est lui-même libre, sous licence Apache 2.0 ; la question ne porte donc que sur les équivalents hors Google Cloud.

- **Crossplane** : licence Apache 2.0, projet CNCF, même principe pour plusieurs fournisseurs à la fois, avec en plus des **compositions** qui exposent aux équipes des ressources maison plutôt que les ressources brutes.
- **AWS Controllers for Kubernetes** et **Azure Service Operator** : les homologues directs chez les deux autres fournisseurs.
- **Argo CD**, **Flux** : licence Apache 2.0, la brique GitOps qui applique les manifestes au cluster, à la place de Config Sync.
- **Kubernetes Cluster API** : licence Apache 2.0, pour la seule création de clusters de manière déclarative depuis un cluster d'amorçage.
- **OpenTofu** avec un opérateur de rapprochement périodique : approche plus classique, si le format Terraform est déjà celui de l'équipe.
