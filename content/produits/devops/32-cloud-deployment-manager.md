---
title: Cloud Deployment Manager
subgroup: Infrastructure as Code
icon: categories/devops
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 16, w: 568, h: 268}
  nodes:
    cfg: {label: Configuration YAML, sub: "modèles Jinja, Python", external: true, x: 8, y: 50, w: 168}
    tf: {label: Dépôt Terraform, sub: "modules HCL", external: true, x: 8, y: 200, w: 150}
    dm: {label: Deployment Manager, sub: "déploiement, manifeste", icon: categories/devops, focus: true, x: 240, y: 46, w: 230, h: 64}
    im: {label: Infrastructure Manager, sub: "reprise des ressources", icon: categories/devops, x: 240, y: 200, w: 230}
    res: {label: Ressources du projet, sub: "VM, buckets, réseaux", icon: categories/management-tools, x: 528, y: 118, w: 210, h: 60}
  flows:
    - {from: cfg, to: dm, text: "Les ressources sont décrites en YAML, avec des modèles Jinja ou Python pour les parties répétitives et les valeurs calculées."}
    - {from: dm, to: res, to_offset: -14, text: "La création du déploiement appelle les APIs des services visés et enregistre un manifeste : la liste des ressources que le déploiement possède."}
    - {from: dm, to: res, from_offset: 16, to_side: top, text: "Une mise à jour applique l'écart entre l'ancienne et la nouvelle configuration ; supprimer le déploiement supprime les ressources qu'il possède."}
    - {from: dm, to: im, control: true, text: "La voie de sortie : porter la configuration vers Infrastructure Manager, ou vers un autre outil de déploiement."}
    - {from: tf, to: im, text: "La configuration équivalente s'écrit en HCL Terraform, versionnée dans un dépôt Git ou un bucket Cloud Storage."}
    - {from: im, to: res, to_offset: 18, text: "Infrastructure Manager reprend les ressources dans son propre état Terraform et en assure le cycle de vie."}
deprecie: "Produit en fin de vie : plus aucun support, et un nouveau projet ne peut plus l'activer. La voie recommandée est [Infrastructure Manager](#infrastructure-manager)."
docs:
  Documentation: https://docs.cloud.google.com/deployment-manager/docs
  Fin de support: https://docs.cloud.google.com/deployment-manager/docs/deprecations
  Fondamentaux: https://docs.cloud.google.com/deployment-manager/docs/fundamentals
  Démarrage rapide: https://docs.cloud.google.com/deployment-manager/docs/manage-cloud-resources-deployment
  Référence de syntaxe: https://docs.cloud.google.com/deployment-manager/docs/configuration/syntax-reference
  Types de ressources acceptés: https://docs.cloud.google.com/deployment-manager/docs/configuration/supported-resource-types
  Créer un modèle: https://docs.cloud.google.com/deployment-manager/docs/configuration/templates/create-basic-template
  Mettre à jour un déploiement: https://docs.cloud.google.com/deployment-manager/docs/deployments/updating-deployments
  Supprimer un déploiement: https://docs.cloud.google.com/deployment-manager/docs/deployments/deleting-deployments
  API REST: https://docs.cloud.google.com/deployment-manager/docs/reference/latest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/deployment-manager
  Bibliothèques clientes: https://docs.cloud.google.com/deployment-manager/docs/reference/latest/libraries
  Notes de version: https://docs.cloud.google.com/deployment-manager/docs/release-notes
---

## Ce que c'est

> [!WARNING]
> Cloud Deployment Manager est hors support : ni nouvelle fonctionnalité, ni correctif non critique, et les tickets de support sont rejetés automatiquement sauf blocage lié à une migration. Un nouvel utilisateur ne peut pas activer l'API Deployment Manager V2 ni créer un premier déploiement : la tentative renvoie vers Infrastructure Manager. Les clients existants gardent l'accès par la console, la CLI et l'API **jusqu'au 30 juin 2027**, à leurs risques ; le service est arrêté ensuite. La voie de migration recommandée est [Infrastructure Manager](#infrastructure-manager), ou une autre technologie de déploiement. Les ressources déjà créées continuent de fonctionner et restent administrables par les outils Google Cloud ordinaires, pas par `gcloud deployment-manager`.

Service déclaratif historique de Google Cloud : on décrit un ensemble de ressources dans une configuration, le service les crée et les tient à jour comme un tout.

- **Configuration.** Un fichier YAML liste les ressources, chacune avec son type (`compute.v1.instance`, `storage.v1.bucket`…), son nom et ses propriétés. Les références entre ressources (`$(ref.NAME.selfLink)`) laissent le service déduire l'ordre de création.
- **Modèles.** Les parties répétitives sortent dans des modèles **Jinja** ou **Python**, paramétrés et réutilisables, avec des variables d'environnement propres au déploiement. Les types composites [!DECONSEILLE] sont obsolètes : un modèle Jinja ou Python fait le même travail.
- **Déploiement et manifeste.** Le déploiement est l'unité de gestion ; son manifeste enregistre la configuration étendue et la liste des ressources possédées. Une mise à jour applique l'écart entre deux configurations ; la suppression du déploiement supprime ses ressources.
- **Couverture.** Le service atteint les types de ressources Google Cloud pris en charge, et les fournisseurs de types pour le reste.

Face à lui, [Infrastructure Manager](#infrastructure-manager) repose sur Terraform et HCL : configuration déclarative aussi, mais modules Terraform au lieu de modèles Jinja ou Python, et un état Terraform géré par Google.

## À quoi ça sert

- Maintenir les déploiements existants d'une organisation qui en possède déjà, le temps de la migration : consulter, mettre à jour, et surtout supprimer proprement.
- Lire et comprendre une configuration YAML héritée pour la porter en HCL.

**À éviter** pour tout nouveau travail : le service n'accepte plus de nouveaux utilisateurs et s'arrêtera le 30 juin 2027. Écrire en Terraform et déployer avec [Infrastructure Manager](#infrastructure-manager) ; piloter depuis Kubernetes avec [Config Connector](#config-connector) si le cluster est déjà l'outil central.

> [!TIP]
> Avant de supprimer un déploiement hérité, vérifier ce qu'il possède : `gcloud deployment-manager deployments describe NAME` liste les ressources du manifeste. La suppression du déploiement emporte tout ce qui y figure, base de données comprise.

## Alternatives en logiciel libre

- **OpenTofu** : licence MPL-2.0, sous l'égide de la Linux Foundation ; le moteur qu'utilise Infrastructure Manager, en version libre. Terraform est sous licence BSL : source disponible, pas libre.
- **Pulumi** : licence Apache 2.0 pour le moteur et les fournisseurs ; infrastructure décrite en Python, TypeScript ou Go — la transition la plus naturelle pour qui écrivait déjà ses modèles en Python.
- **Crossplane** : licence Apache 2.0, projet CNCF, pour piloter les ressources depuis Kubernetes.
- **Ansible** : licence GPLv3, avec ses modules `google.cloud` ; approche procédurale et sans fichier d'état, proche de l'esprit d'un script de déploiement.
- **Kubernetes Resource Model** et **kpt** : licence Apache 2.0, gabarits et transformations de manifestes déclaratifs, si la cible est Config Connector.
