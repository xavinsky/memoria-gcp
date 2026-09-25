---
title: IAM
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Hiérarchie des ressources, x: 460, y: 16, w: 288, h: 290}
  nodes:
    user: {label: Utilisateur, sub: "compte Google", external: true, x: 8, y: 40, w: 180}
    groupe: {label: Groupe, sub: "équipe applicative", external: true, x: 8, y: 120, w: 180}
    sa: {label: Compte de service, sub: "service Cloud Run", icon: categories/security-identity, x: 8, y: 210, w: 180}
    iam: {label: IAM, sub: "stratégie d'autorisation", icon: categories/security-identity, focus: true, x: 222, y: 120, w: 206, h: 64}
    org: {label: Organisation, sub: "liaisons héritées", icon: categories/management-tools, x: 480, y: 44, w: 248}
    projet: {label: Projet PROJECT_ID, sub: "liaisons de rôles", icon: categories/management-tools, x: 480, y: 134, w: 248}
    bucket: {label: Cloud Storage, sub: "bucket BUCKET", icon: produits/cloud-storage, x: 480, y: 224, w: 248}
  flows:
    - {from: user, to: groupe, control: true, text: "Les comptes des collaborateurs sont rassemblés dans un groupe : c'est au groupe, et non à chaque personne, qu'on accorde les rôles."}
    - {from: groupe, to: iam, from_offset: -16, text: "Une liaison de rôle associe le groupe au rôle Storage Object Viewer dans la stratégie d'autorisation du projet."}
    - {from: sa, to: iam, text: "Le compte de service attaché au service Cloud Run reçoit de la même façon le rôle Storage Object Admin, assorti d'une condition qui le limite à un préfixe d'objets."}
    - {from: iam, to: projet, text: "La stratégie est attachée au projet ; IAM l'évalue à chaque appel d'API, avant même que le service concerné soit sollicité."}
    - {from: org, to: projet, control: true, text: "Les liaisons posées sur l'organisation et sur les dossiers descendent jusqu'au projet : l'accès réel est l'union de toutes les stratégies des ancêtres."}
    - {from: projet, to: bucket, control: true, text: "Le bucket hérite des rôles du projet sans porter de stratégie propre ; la requête passe si la permission storage.objects.get figure dans l'un des rôles accordés."}
captures:
  - image: https://docs.cloud.google.com/static/iam/img/quickstart-roles-add.png
    page: https://docs.cloud.google.com/iam/docs/grant-role-console
    legende: "Attribution d'un rôle à un principal sur un projet : choix du rôle, condition IAM facultative et ajout d'autres rôles"
docs:
  Documentation: https://docs.cloud.google.com/iam/docs
  Vue d'ensemble: https://docs.cloud.google.com/iam/docs/overview
  Rôles et permissions: https://docs.cloud.google.com/iam/docs/roles-overview
  Liste des rôles prédéfinis: https://docs.cloud.google.com/iam/docs/roles-permissions
  Identifiants de principaux: https://docs.cloud.google.com/iam/docs/principal-identifiers
  Comptes de service: https://docs.cloud.google.com/iam/docs/service-account-overview
  Hiérarchie des ressources: https://docs.cloud.google.com/iam/docs/resource-hierarchy-access-control
  Conditions: https://docs.cloud.google.com/iam/docs/conditions-overview
  Stratégies de refus: https://docs.cloud.google.com/iam/docs/deny-overview
  Principal Access Boundary: https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies
  Recommandations de rôles: https://docs.cloud.google.com/policy-intelligence/docs/role-recommendations-overview
  Bonnes pratiques (comptes de service): https://docs.cloud.google.com/iam/docs/best-practices-service-accounts
  API REST: https://docs.cloud.google.com/iam/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/iam
  Client Python: https://docs.cloud.google.com/python/docs/reference/iam/latest
  Quotas et limites: https://docs.cloud.google.com/iam/quotas
  Tarifs: https://cloud.google.com/iam/pricing
  Notes de version: https://docs.cloud.google.com/iam/docs/release-notes
---

## Ce que c'est

Le service d'autorisation de Google Cloud : il décide, pour chaque appel d'API, si un **principal** a le droit d'exécuter une opération sur une **ressource**. Trois notions suffisent à décrire une autorisation — un principal, un rôle, une ressource — et le reste découle de la hiérarchie.

- **Principaux.** Deux familles. Côté humains : comptes Google (gérés par [Cloud Identity](#cloud-identity) ou Google Workspace), groupes, et identités fédérées d'un *workforce identity pool*. Côté charges de travail : **comptes de service** et identités fédérées d'un *workload identity pool*. Les anciens noms d'API parlent encore de *members*.
- **Permissions et rôles.** Une permission s'écrit `service.ressource.verbe` (`storage.objects.get`) et correspond le plus souvent à une méthode de l'API REST. Une permission ne s'accorde jamais directement : elle vient d'un **rôle**. Trois sortes de rôles — **prédéfinis**, maintenus par Google et alignés sur un métier ; **personnalisés**, dont on choisit chaque permission, plus coûteux à entretenir et limités en nombre ; **de base** [!DECONSEILLE] (`roles/admin`, `roles/writer`, `roles/reader`, et les rôles de base historiques `roles/owner`, `roles/editor`, `roles/viewer`), très larges, à réserver aux bacs à sable.
- **Stratégie d'autorisation.** L'objet YAML ou JSON attaché à une ressource, composé de **liaisons de rôles** qui associent un rôle à une liste de principaux. C'est ce que lit IAM pour répondre oui ou non.
- **Héritage.** Les conteneurs — organisation, dossiers, projets — forment la **hiérarchie des ressources**, et une stratégie posée sur un conteneur s'applique à tout ce qu'il contient. L'accès **effectif** d'un principal est donc l'union de la stratégie de la ressource et de celles de tous ses ancêtres ; beaucoup de ressources (un bucket de journaux, par exemple) n'acceptent pas de stratégie propre et ne s'ouvrent que par un ancêtre.
- **Comptes de service.** Un compte identifié par une adresse e-mail, qu'une application utilise pour s'authentifier. On distingue ceux que l'on crée, les comptes **par défaut** créés à l'activation de certains services, et les **agents de service** que Google crée pour agir sur les ressources pour son compte. Le mécanisme normal est l'**attachement** à une ressource (VM, service [Cloud Run](#cloud-run), pod [GKE](#gke)) : le code obtient alors des jetons courts sans qu'aucun secret ne circule. L'**emprunt d'identité** permet à un principal autorisé d'agir comme un compte de service, le temps d'un jeton.
- **Conditions.** Une expression CEL attachée à une liaison de rôle, qui ne l'active que si elle s'évalue à vrai : date d'expiration, préfixe de nom de ressource, tag `env=prod`, adresse IP de la requête. Les conditions valent aussi dans les stratégies de refus et les *Principal Access Boundary*. Toutes les ressources n'acceptent pas les liaisons conditionnelles, et on évite de dépasser une centaine de liaisons conditionnelles par stratégie.
- **Refus et frontières.** Une **stratégie de refus** retire des permissions même à qui détient le rôle qui les contient — un garde-fou qui prime sur l'autorisation. Une stratégie **Principal Access Boundary** décrit à l'inverse le périmètre de ressources qu'un principal est *éligible* à atteindre, quelles que soient les liaisons qui lui sont accordées ailleurs. **Privileged Access Manager** complète le dispositif en accordant des rôles temporaires, sur demande, avec justification ou approbation.
- **Recommandations.** Le *recommender* IAM compare, sur 90 jours, les permissions détenues et les permissions réellement utilisées, puis propose de retirer ou de remplacer un rôle trop large. Les *lateral movement insights* signalent en plus les comptes de service d'un projet capables d'en emprunter d'autres ailleurs.
- **Cohérence.** L'API IAM est à cohérence à terme : un compte de service tout juste créé peut rester introuvable quelques secondes, et une modification de stratégie met un moment à produire son effet sur les contrôles d'accès.
- **Facturation.** L'API IAM est gratuite. Une partie des recommandations de rôles (rôles non basiques, recommandations au niveau des ressources) et certaines fonctions [!PREVERSION] de Privileged Access Manager demandent Security Command Center Premium ou Enterprise.

> [!WARNING]
> Une clé JSON de compte de service est un secret longue durée qui ne s'expire pas tout seul et qui se retrouve vite dans un dépôt Git. Les seuls cas où elle reste nécessaire sont ceux qu'aucune autre méthode ne couvre : ailleurs, préférer l'attachement, l'emprunt d'identité ou [Workload Identity Federation](#workload-identity-federation).

## À quoi ça sert

- Donner à une équipe l'accès à un environnement entier d'une seule liaison, en accordant le rôle au groupe sur le dossier qui contient ses projets.
- Faire tourner chaque charge de travail sous un compte de service dédié, avec les seuls rôles dont elle a besoin : la compromission d'un service ne donne pas les droits des autres.
- Accorder un accès qui s'éteint tout seul, par une condition `request.time < timestamp(...)` — utile pour une astreinte ou un prestataire.
- Cloisonner par étiquette : un rôle d'administration qui ne s'applique qu'aux ressources portant le tag `env=dev`, et une stratégie de refus qui bloque les mêmes permissions sur `env=prod`.
- Réduire progressivement les privilèges d'un projet hérité, en partant des recommandations de retrait de rôles plutôt que d'un audit manuel.
- Séparer les responsabilités : qui administre les clés, qui lit les données, qui déploie — trois rôles distincts sur trois ressources distinctes.

**À éviter** comme mécanisme d'authentification des utilisateurs d'une application : IAM autorise des appels aux APIs Google Cloud, pas des sessions applicatives ; pour les identités des clients d'un produit, c'est [Identity Platform](#identity-platform), et pour ouvrir une application interne à des employés, [Identity-Aware Proxy](#identity-aware-proxy). À éviter aussi comme unique rempart contre l'exfiltration : une stratégie mal posée suffit à exposer un bucket, et c'est le rôle de [VPC Service Controls](#vpc-service-controls) d'ajouter une frontière indépendante de l'identité. Enfin, multiplier les rôles personnalisés coûte cher en maintenance — chaque nouvelle méthode d'API ajoutée par Google devra y être reportée à la main.

## Alternatives en logiciel libre

- **Open Policy Agent** : moteur de décision généraliste, règles écrites en Rego, évaluées à côté de l'application — l'équivalent conceptuel des conditions IAM, avec Gatekeeper comme déclinaison Kubernetes.
- **OpenFGA** : service d'autorisation fine inspiré du modèle Zanzibar de Google, adapté aux relations « tel utilisateur sur tel objet » plutôt qu'aux rôles globaux.
- **Casbin** : bibliothèque d'autorisation multi-modèles (RBAC, ABAC, ACL), intégrée directement dans le processus applicatif.
- **Keycloak** : rôles, groupes et autorisations fines pour des applications, avec une administration proche de celle d'un annuaire d'entreprise.
- **RBAC Kubernetes** : le modèle rôle/liaison/espace de noms, transposable à un cluster ; il reprend l'idée de l'héritage par conteneur, à l'échelle d'un cluster plutôt que d'une organisation.
