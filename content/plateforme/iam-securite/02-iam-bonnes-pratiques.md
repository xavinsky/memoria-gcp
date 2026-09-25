---
title: "IAM : rôles, comptes de service, moindre privilège"
subgroup: Identités et accès
---

Une autorisation [IAM](#cloud-iam) tient en une phrase : tel **principal** reçoit tel **rôle** sur telle **ressource**, et l'hérite pour tout ce qu'elle contient. Tout le travail de conception consiste à garder ces liaisons peu nombreuses, lisibles et au plus juste : des groupes plutôt que des personnes, un compte de service par charge de travail, des rôles prédéfinis étroits posés au plus bas niveau utile, et des garde-fous (refus, frontières) qui tiennent même quand une liaison est trop large. C'est le principe de moindre privilège que le pilier sécurité du Well-Architected Framework place au cœur du *zero trust* ([Implement zero trust](https://docs.cloud.google.com/architecture/framework/security/implement-zero-trust)).

![Évaluation d'un appel par IAM et héritage des stratégies](../../svg/evaluation-iam.svg)

IAM évalue ensemble trois types de stratégies ; on peut les lire comme trois étapes. Une stratégie **Principal Access Boundary** dit si le principal est *éligible* à la ressource, une **stratégie de refus** retire des permissions, une **stratégie d'autorisation** en accorde. Refus et autorisations s'héritent de l'organisation jusqu'à la ressource ; seules les autorisations ouvrent un accès. Les [règles d'administration](#hierarchie-des-ressources) et les [périmètres VPC Service Controls](#perimetres-vpc-sc) forment des contrôles distincts, évalués en plus.

## Principaux

| Principal | Identifiant dans une liaison | Usage |
|---|---|---|
| Compte Google géré ([Cloud Identity](#cloud-identity) ou Workspace) | `user:alice@example.com` | Un humain ; à éviter dans les liaisons, sauf exception |
| Groupe Google | `group:data-eng@example.com` | **La cible normale** des rôles humains ; la composition se gère dans l'annuaire |
| Compte de service | `serviceAccount:app@PROJECT_ID.iam…` | Une charge de travail ; un par application |
| [Agent de service](#lexterm-agent-de-service) | `serviceAccount:service-PROJECT_NUMBER@gcp-sa-…` | Compte géré par Google qui agit pour un produit (chiffrement CMEK, lecture d'un bucket) ; ne pas lui retirer son rôle d'agent |
| Identité fédérée de personnel | `principal://…/workforcePools/POOL/subject/SUJET` | Employé authentifié par un fournisseur externe, sans compte Google (voir [Identités des utilisateurs](#identites-des-utilisateurs)) |
| Identité fédérée de charge de travail | `principalSet://…/workloadIdentityPools/POOL/attribute.NOM/VALEUR` | Pipeline, autre cloud, pod GKE ([Workload Identity Federation](#workload-identity-federation)) |
| Ensemble de principaux | `domain:example.com`, `principalSet://…/type/ServiceAccount`, `allUsers` | Tout un domaine, tous les comptes de service d'un projet, ou le public : rarement justifié |

Les stratégies de refus utilisent une autre syntaxe (`principal://goog/subject/alice@example.com`, `principalSet://goog/group/data-eng@example.com`) : recopier un identifiant d'une stratégie d'autorisation dans une règle de refus ne fonctionne pas.

## Rôles

| Sorte | Exemples | Quand |
|---|---|---|
| **Prédéfini** | `roles/bigquery.dataEditor`, `roles/run.invoker` | Par défaut : maintenu par Google, mis à jour quand le service évolue |
| **Personnalisé** | `organizations/ORG_ID/roles/lecteurFacturation` | Quand aucun rôle prédéfini ne colle ; 300 par organisation et 300 par projet ; nouvelles permissions à reporter à la main |
| [!DECONSEILLE] **De base** | Admin, Writer, Reader [!PREVERSION] ; Owner, Editor, Viewer (anciens rôles de base) | Bacs à sable seulement : des milliers de permissions sur tous les services ; ailleurs, rôles prédéfinis |

Un rôle personnalisé se construit à partir d'un rôle prédéfini, en retirant des permissions, rarement en partant de zéro. Le rôle **Owner** permet en plus de modifier les stratégies : pour déléguer la gestion des accès sans donner l'accès aux données, *Project IAM Admin* ou *Folder IAM Admin* suffisent.

## Liaisons et héritage

- **Des groupes, pas des personnes.** Une arrivée ou un départ se traite dans l'annuaire, sans relire les stratégies ; le plan de groupes de la [fondation d'entreprise](https://docs.cloud.google.com/architecture/blueprints/security-foundations/authentication-authorization) (`grp-gcp-org-admin`, `grp-gcp-billing-viewer`, `grp-gcp-security-reviewer`...) sert de point de départ.
- **Le plus bas niveau utile.** Un rôle accordé sur un projet vaut pour toutes ses ressources, sur un dossier pour tous ses projets. On donne à une équipe ses rôles sur le dossier de son environnement, à une application ses rôles sur le bucket ou le sujet qu'elle lit. Le découpage en dossiers est décrit dans [Hiérarchie des ressources](#hierarchie-des-ressources).
- **Tout en code.** Les liaisons vivent dans le dépôt d'infrastructure et passent en revue comme le reste (voir [Fondations en code](#fondations-en-code)) ; la console sert à lire, pas à accorder.

```python
import pulumi_gcp as gcp

dossier = gcp.organizations.Folder("donnees-prod",
    display_name="donnees-prod", parent="organizations/ORG_ID")

# Non autoritatif : ajoute cette liaison sans toucher aux autres liaisons du dossier
gcp.folder.IAMMember("data-eng-bq-editor",
    folder=dossier.name,                      # "folders/FOLDER_ID"
    role="roles/bigquery.dataEditor",
    member="group:data-eng@example.com")

# Accès qui s'éteint seul, pour une astreinte
gcp.folder.IAMMember("astreinte-logs",
    folder=dossier.name,
    role="roles/logging.viewer",
    member="group:astreinte@example.com",
    condition=gcp.folder.IAMMemberConditionArgs(
        title="fin-astreinte",
        expression='request.time < timestamp("2026-12-31T23:59:59Z")'))
```

`IAMMember` ajoute une liaison, `IAMBinding` fixe la liste complète des membres d'un rôle, `IAMPolicy` remplace toute la stratégie : ne jamais mélanger `IAMPolicy` avec les deux autres sur une même ressource, et le réserver aux ressources entièrement gérées par la pile.

## Garde-fous

| Mécanisme | Attaché à | Ce qu'il fait | Usage type |
|---|---|---|---|
| [Condition IAM](#lexterm-condition-iam) | Une liaison d'autorisation | N'accorde le rôle que si l'expression CEL est vraie : date, préfixe de nom, tag | Accès temporaire ; rôle limité aux ressources taguées `env=dev` |
| [Stratégie de refus](#lexterm-strategie-de-refus-deny-policy) | Organisation, dossier ou projet | Retire des permissions, quels que soient les rôles ; exceptions nommées possibles | Interdire à tous sauf un groupe la création de clés ou la suppression de projets |
| **Principal Access Boundary** | Un ensemble de principaux (domaine, pool, projet) | Limite les ressources auxquelles ces principaux sont éligibles | Empêcher les comptes de l'organisation d'agir dans une organisation tierce (hameçonnage, exfiltration) |
| **Privileged Access Manager** | Organisation, dossier ou projet | Rôles accordés sur demande, pour une durée bornée, avec justification et approbation | Accès à la production pour un dépannage ; accès d'urgence |

- **Conditions.** Les attributs de ressource (`resource.name`, `resource.type`, `resource.matchTag('ORG_ID/env', 'prod')`) et de requête (`request.time`, niveaux d'accès pour IAP) sont les plus utiles. Seuls certains types de ressources acceptent une liaison conditionnelle ; au besoin, poser la condition sur le projet. Une liaison sans condition l'emporte toujours : ajouter une condition à un rôle déjà accordé sans condition ne change rien.
- **Refus.** Jusqu'à 500 règles par ressource, conditionnées seulement par des tags. Les permissions s'y écrivent en forme complète (`iam.googleapis.com/serviceAccountKeys.create`), et toutes ne sont pas refusables : vérifier la liste des permissions prises en charge.
- **Frontières.** Une stratégie PAB porte jusqu'à 500 règles et ne bloque que les permissions de sa **version d'application** ; la valeur `latest` suit les nouvelles versions, au risque de couper des accès sans prévenir. Elle échoue en position fermée : un principal tout juste créé peut être refusé quelques minutes.
- **Accès juste-à-temps.** Privileged Access Manager crée des **droits** (*entitlements*) : qui peut demander, quels rôles, quelle durée maximale, quels approbateurs. À l'expiration, les rôles sont retirés et tout est tracé dans Cloud Audit Logs. Il accepte les rôles prédéfinis, personnalisés et les nouveaux rôles de base, pas Owner, Editor ni Viewer. L'approbation à plusieurs niveaux et la personnalisation du périmètre demandé exigent Security Command Center Enterprise ou Premium.

## Comptes de service

- **Un compte par charge de travail**, nommé et décrit d'après ce qu'il fait ; les journaux d'audit donnent le compte, pas l'application qui l'utilise.
- **Aucun compte par défaut en production.** Les comptes par défaut de Compute Engine ou App Engine reçoivent le rôle Editor à leur création, sauf si la contrainte `iam.automaticIamGrantsForDefaultServiceAccounts` est appliquée ; `iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts` interdit en plus de leur accorder Editor ou Owner plus tard.
- **Aucune clé.** Attachement à la ressource, [emprunt d'identité](#lexterm-emprunt-d-identite-impersonation) ou fédération (voir [Authentifier un appel à une API](#authentifier-un-appel)). Les contraintes `iam.managed.disableServiceAccountKeyCreation` et `iam.managed.disableServiceAccountKeyUpload`, appliquées à la racine, font de la clé une exception accordée projet par projet.
- **Les droits d'agir sur un compte, sur le compte lui-même.** `roles/iam.serviceAccountUser` (attacher) et `roles/iam.serviceAccountTokenCreator` (emprunter) accordés sur un projet ou un dossier valent pour **tous** ses comptes de service, y compris les plus privilégiés. Un utilisateur ne doit pas pouvoir emprunter un compte plus puissant que lui.
- **Jetons courts.** L'emprunt donne des jetons d'une heure, extensibles à douze heures par la contrainte `iam.allowServiceAccountCredentialLifetimeExtension`.
- **Comptes inutilisés** : les repérer par les *service account insights*, les désactiver, attendre, puis les supprimer ; supprimer un compte encore utilisé casse la charge de travail, et le recréer sous le même nom ne rend pas les liaisons.

## Réduire et surveiller

- **Recommandations de rôles.** Le *recommender* IAM compare les permissions accordées à celles utilisées sur 90 jours et propose de retirer ou de remplacer un rôle, sans jamais augmenter l'accès (sauf pour un agent de service, dont il ne traite que les rôles de base). La période d'observation se réduit à 30 ou 60 jours pour les recommandations de projet. Les recommandations sur les rôles de base sont gratuites ; celles sur les autres rôles, ou sur des ressources comme les buckets et les datasets, demandent Security Command Center Premium ou Enterprise.
- **Policy Intelligence.** *Policy Analyzer* répond à « qui a accès à quoi », *Policy Troubleshooter* à « pourquoi cet accès est refusé », *Policy Simulator* montre l'effet d'une modification d'autorisation, de refus ou de frontière avant de l'appliquer.
- **Journaux d'audit.** Les modifications de stratégies (`SetIamPolicy`) sont dans les journaux d'activité d'administration, toujours actifs. Les journaux d'accès aux données de l'API IAM sont désactivés par défaut : les activer pour tracer qui a obtenu un jeton de quel compte de service. Les exporter vers un bucket ou BigQuery pour la conservation longue (voir [Détection et conformité](#detection-et-conformite)).

## Pièges

- **Propagation.** Une modification de stratégie prend en général deux minutes, parfois sept ou plus ; un changement de composition de groupe, plusieurs minutes, parfois des heures. Un retrait d'accès n'est donc pas immédiat, et un script qui accorde un rôle puis l'utilise aussitôt doit réessayer.
- **Conditions ignorées.** Owner, Editor et Viewer ne prennent pas de condition, pas plus que `allUsers` et `allAuthenticatedUsers`. Dans Cloud Storage, une liaison conditionnelle exige l'accès uniforme au niveau du bucket.
- **Limites de taille.** Une stratégie d'autorisation compte au plus 1 500 principaux (un groupe compte pour un) et 250 groupes ou domaines : au-delà, c'est le signe qu'il manque des groupes.
- **Rôles de base hérités.** Un Editor accordé sur l'organisation « pour dépanner » donne l'écriture sur tous les projets, et la création de clés de compte de service partout où elle n'est pas bloquée.
- **Stratégie autoritative dans l'IaC.** Un `IAMPolicy` ou un `IAMBinding` écrase les liaisons ajoutées ailleurs, y compris celles des agents de service : c'est une panne silencieuse du service concerné.

## Alternatives en logiciel libre

- **Open Policy Agent** (Apache 2.0) : moteur de décision généraliste, règles en Rego évaluées à côté de l'application ; il couvre à la fois les conditions et les refus, avec Gatekeeper pour Kubernetes.
- **Cedar** (Apache 2.0) : langage de politiques d'autorisation avec des règles `permit` et `forbid`, où un `forbid` l'emporte toujours, comme une stratégie de refus sur une autorisation ; analysable formellement.
- **OpenFGA** (Apache 2.0) et **SpiceDB** (Apache 2.0) : autorisation par relations inspirée de Zanzibar, le système interne de Google ; l'héritage le long d'une hiérarchie d'objets s'y exprime directement.
- **Cerbos** (Apache 2.0) : point de décision sans état, politiques en YAML avec conditions CEL, le même langage d'expression que les conditions IAM.
- **Casbin** (Apache 2.0) : bibliothèque RBAC et ABAC intégrée au processus applicatif, avec rôles hiérarchiques et règles de refus.
- **RBAC Kubernetes** (Apache 2.0) : rôles, liaisons et comptes de service à l'échelle d'un cluster ; même modèle principal, rôle, portée, sans héritage au-delà de l'espace de noms.
