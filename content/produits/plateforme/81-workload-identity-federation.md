---
title: Workload Identity Federation
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 230, y: 16, w: 520, h: 290}
  nodes:
    gha: {label: GitHub Actions, sub: "jeton OIDC du workflow", external: true, x: 8, y: 130, w: 210}
    sts: {label: Security Token Service, sub: "échange de jetons", icon: categories/security-identity, x: 250, y: 40, w: 230}
    pool: {label: Pool d'identités, sub: "fournisseur, mappages", icon: categories/security-identity, focus: true, x: 250, y: 130, w: 230, h: 64}
    sa: {label: Compte de service, sub: "emprunt d'identité", icon: categories/security-identity, x: 250, y: 226, w: 230}
    ar: {label: Artifact Registry, sub: "image du service", icon: categories/devops, x: 540, y: 88, w: 210}
    run: {label: Cloud Run, sub: "révision déployée", icon: produits/cloud-run, x: 540, y: 196, w: 210}
  flows:
    - {from: gha, to: sts, text: "Le workflow demande à GitHub un jeton OIDC qui identifie le dépôt, la branche et l'environnement, puis le présente au Security Token Service."}
    - {from: sts, to: pool, text: "Le fournisseur du pool vérifie la signature du jeton, applique la condition d'attribut (dépôt appartenant à l'organisation) et remplit google.subject par mappage."}
    - {from: pool, to: sa, text: "Le jeton fédéré sert à emprunter l'identité d'un compte de service, grâce au rôle Workload Identity User ; il en sort un jeton OAuth 2.0 valable une heure."}
    - {from: sa, to: ar, from_offset: -14, text: "Le pipeline pousse l'image du service dans Artifact Registry avec ce jeton."}
    - {from: sa, to: run, from_offset: 14, text: "Puis il déploie la révision Cloud Run ; le jeton expire de lui-même et rien de durable n'est stocké côté GitHub."}
docs:
  Vue d'ensemble: https://docs.cloud.google.com/iam/docs/workload-identity-federation
  Pipelines de déploiement: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
  AWS et Azure: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds
  Kubernetes: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-kubernetes
  Gérer pools et fournisseurs: https://docs.cloud.google.com/iam/docs/manage-workload-identity-pools-providers
  Bonnes pratiques: https://docs.cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation
  Se passer des clés de compte de service: https://docs.cloud.google.com/iam/docs/migrate-from-service-account-keys
  Identifiants de principaux: https://docs.cloud.google.com/iam/docs/principal-identifiers
  Fédération d'identité de personnel: https://docs.cloud.google.com/iam/docs/workforce-identity-federation
  Documentation IAM: https://docs.cloud.google.com/iam/docs
  API REST (Security Token Service): https://docs.cloud.google.com/iam/docs/reference/sts/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/iam/workload-identity-pools
  Quotas et limites: https://docs.cloud.google.com/iam/quotas
  Notes de version: https://docs.cloud.google.com/iam/docs/release-notes
---

## Ce que c'est

Le mécanisme qui laisse une charge de travail extérieure à Google Cloud obtenir des jetons Google Cloud à partir des identifiants qu'elle possède déjà, sans jamais détenir de clé de compte de service. Il suit la spécification **OAuth 2.0 Token Exchange** : un jeton émis par un fournisseur d'identité tiers est échangé contre un jeton d'accès de courte durée.

- **Pool d'identités de charge de travail.** Le conteneur qui décrit un ensemble d'identités externes. La recommandation est d'en créer un par environnement extérieur — développement, préproduction, production — plutôt qu'un pool unique.
- **Fournisseur.** La relation avec un émetteur de jetons : AWS, Microsoft Entra ID, GitHub, GitLab, un cluster Kubernetes, Okta, AD FS sur site, Terraform, ou tout fournisseur **OIDC** ou **SAML 2.0**. Les charges qui s'authentifient par **certificat client X.509** sont aussi prises en charge. Pour un émetteur sans point de terminaison public, on téléverse directement les **JWKS** dans le pool.
- **Mappages d'attributs.** Des expressions CEL qui dérivent les attributs du jeton Google à partir des *claims* du jeton externe. `google.subject` est obligatoire et unique (127 caractères au plus) ; `google.groups` et jusqu'à **50 attributs personnalisés** `attribute.NOM` servent ensuite à écrire les liaisons IAM. Les fonctions CEL usuelles sont disponibles : `contains`, `extract`, `split`, `join`, ternaire.
- **Condition d'attribut.** Une expression CEL évaluée à l'entrée : si elle est fausse, le jeton est rejeté. C'est elle qui empêche n'importe quel dépôt GitHub public d'entrer dans le pool — `assertion.repository_owner == 'ORGANISATION'` — et qui évite le problème du *confused deputy* quand le même fournisseur sert plusieurs clouds.
- **Deux façons d'accorder l'accès.** L'**accès direct** accorde les rôles au principal fédéré lui-même, par un identifiant `principal://…/subject/…` ou `principalSet://…/attribute.NOM/VALEUR` : c'est la méthode recommandée. L'**emprunt d'identité** d'un compte de service reste l'alternative pour les quelques APIs qui ne gèrent pas encore les identités fédérées ; il suppose le rôle `roles/iam.workloadIdentityUser`.
- **Côté pipelines.** Rien à configurer chez le fournisseur : GitHub Actions expose un jeton OIDC qui identifie le workflow et le dépôt, GitLab un jeton d'identité qui porte le projet, la branche et l'environnement, HCP Terraform un jeton par espace de travail, Azure DevOps un jeton par projet. Pour GitLab, le *claim* `sub` contient à la fois le projet et la référence Git, ce qui permet de restreindre l'accès à une branche précise ; pour GitHub, `repository`, `repository_owner` et `ref` jouent le même rôle.
- **Fédération d'identité de personnel.** Le pendant côté humains : un *workforce identity pool* fait entrer les employés d'un fournisseur d'identité externe dans la console et les APIs, sans créer de compte Google pour chacun.

> [!TIP]
> Avant d'ouvrir le pool, écrire la condition d'attribut. Un fournisseur GitHub sans condition accepte le jeton de **n'importe quel** dépôt GitHub : le mappage seul ne filtre rien.

## À quoi ça sert

- Donner à un pipeline GitHub Actions ou GitLab CI le droit de pousser une image dans [Artifact Registry](#artifact-registry) et de déployer sur [Cloud Run](#cloud-run), sans secret dans le dépôt ni rotation à organiser.
- Laisser une application hébergée sur AWS ou Azure lire un jeu de données [BigQuery](#bigquery) avec son rôle IAM d'origine ou son identité managée.
- Rattacher un cluster Kubernetes sur site à un projet Google Cloud, chaque compte de service Kubernetes devenant un principal fédéré distinct.
- Connecter des machines d'un parc sur site, authentifiées par certificat X.509 émis par la PKI interne, à des APIs Google Cloud.
- Supprimer les clés de compte de service existantes : la contrainte d'organisation gérée `iam.managed.disableServiceAccountKeyCreation` verrouille la porte une fois la migration faite.
- Restreindre l'accès à une branche : une liaison sur `principalSet://…/attribute.ref/refs/heads/main` n'autorise que les exécutions de la branche principale à toucher la production.

**À éviter** pour une charge de travail qui tourne déjà dans Google Cloud : une VM [Compute Engine](#compute-engine), un service [Cloud Run](#cloud-run) ou un pod [GKE](#gke) obtiennent des jetons par le compte de service attaché, sans pool ni fournisseur. À éviter aussi pour authentifier des personnes : la fédération de charge de travail ne gère pas d'interface de connexion, c'est la fédération d'identité de personnel ou [Cloud Identity](#cloud-identity) qui s'en occupe. Enfin, quelques APIs Google Cloud ne reconnaissent pas encore les principaux fédérés : là, il faut repasser par l'emprunt d'identité d'un compte de service.

## Alternatives en logiciel libre

- **SPIFFE et SPIRE** : le standard d'identité de charge de travail le plus proche — une identité vérifiable (SVID) délivrée à un processus d'après ce qu'il est, sans secret préalable ; SPIRE sait d'ailleurs fédérer avec des domaines de confiance tiers.
- **OpenBao** (licence MPL-2.0) : l'authentification JWT/OIDC échange un jeton de fournisseur externe contre un jeton court, exactement le même schéma.
- **Dex** : passerelle OIDC qui agrège des fournisseurs amont (LDAP, SAML, GitHub) et émet des jetons pour les consommateurs en aval.
- **Keycloak** : serveur d'identité complet qui sait aussi faire de l'échange de jetons standard entre domaines de confiance.
- **cert-manager** et **step-ca** : pour la variante par certificat X.509, ils délivrent et renouvellent les certificats clients que la charge de travail présentera.
