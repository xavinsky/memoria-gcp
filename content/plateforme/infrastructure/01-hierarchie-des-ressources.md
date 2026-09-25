---
title: "Organiser l'environnement : organisation, dossiers, projets"
subgroup: Fondations
---

Avant la première application, une entreprise pose sa **zone d'atterrissage** (*landing zone*) : l'organisation, l'arborescence des dossiers, les projets partagés, les [règles d'administration](#lexterm-regle-d-administration-organization-policy) de base, les groupes qui reçoivent les rôles et la centralisation des journaux. Tout ce qui est posé haut dans la [hiérarchie](#lexterm-hierarchie-des-ressources) s'hérite vers le bas : c'est ici qu'une erreur coûte le plus cher à corriger. La méthode suit le [guide de conception des zones d'atterrissage](https://docs.cloud.google.com/architecture/landing-zones) et l'[enterprise foundations blueprint](https://docs.cloud.google.com/architecture/blueprints/security-foundations) de Google, dont les noms sont repris ci-dessous ; les principes d'ensemble sont dans [Well-Architected Framework](#well-architected).

![Hiérarchie de référence : un dossier d'amorçage, un dossier commun, un dossier réseau, puis un dossier par environnement](../../svg/hierarchie-ressources.svg)

## Préalables : identité et organisation

- **L'organisation naît de l'annuaire.** La ressource organisation est créée automatiquement dès qu'un compte [Cloud Identity](#cloud-identity) ou Google Workspace est associé à un domaine vérifié. L'édition gratuite de Cloud Identity suffit. Une seule organisation par entreprise ; une deuxième ne se justifie que pour tester des changements d'IAM ou de hiérarchie à l'écart, ou pour une filiale destinée à être cédée.
- **Comptes personnels.** Des collaborateurs ont souvent déjà des comptes Google personnels créés avec leur adresse professionnelle. Les rapatrier en comptes gérés avant d'accorder le moindre rôle (voir [Identités des utilisateurs](#identites-des-utilisateurs)).
- **Super administrateurs.** Le compte super administrateur de Cloud Identity contourne l'authentification unique, par construction : il sert à réparer une fédération en panne. Deux ou trois comptes distincts des comptes de travail (`alice-admin@DOMAINE`), une clé de sécurité physique obligatoire, aucune utilisation au quotidien. Le rôle **Administrateur de l'organisation** (`roles/resourcemanager.organizationAdmin`) est délégué à un groupe, sans les super administrateurs dedans ([bonnes pratiques](https://docs.cloud.google.com/resource-manager/docs/super-admin-best-practices)).
- **Droits accordés à tout le domaine.** À la création de l'organisation, tous les utilisateurs du domaine reçoivent **Créateur de projets** (`roles/resourcemanager.projectCreator`) et **Créateur de comptes de facturation** (`roles/billing.creator`) sur l'organisation. Retirer ces deux liaisons dès que la [*project factory*](#lexterm-project-factory) existe : les projets se créent alors par le pipeline, pas à la main.
- **Contacts essentiels.** *Essential Contacts*, configuré sur l'organisation, envoie les notifications importantes de Google (suspension de compte, évolution des conditions, avis de sécurité) à des groupes surveillés plutôt qu'à la personne qui a ouvert le compte.

## Choisir le découpage des dossiers

Google recommande de **ne pas calquer l'organigramme** : la hiérarchie sert à appliquer des stratégies d'accès et des règles d'administration, et un dossier ne se justifie que si son contenu partage ces stratégies. Le guide de Google pose deux questions : les entités (filiales, régions) ont-elles des exigences de conformité très différentes ? Sinon, les équipes produit ont-elles besoin d'une large autonomie sur leurs propres règles ?

| Premier niveau | Quand le choisir | Avantages | Inconvénients |
|---|---|---|---|
| **Environnement** (production, hors production, développement) | Équipe sécurité centrale ; règles plus strictes en production ; rôles différents selon l'environnement | Une règle ou un rôle posé une fois vaut pour toute la production ; c'est le choix du blueprint | Les équipes sont dispersées dans trois dossiers ; déléguer à une équipe demande un sous-dossier par environnement |
| **Entité** (filiale, région, entité juridique) | Entités autonomes, conformité propre (données en Europe, secteur régulé), cessions ou acquisitions probables | Règles de localisation et d'accès isolées par entité ; une filiale se détache avec son dossier | Règles communes à répéter dans chaque branche ; services partagés à placer ailleurs |
| **Équipe ou produit** | Équipes qui possèdent tout le cycle de vie de leur produit, sans équipe sécurité centrale | Autonomie et délégation simples : un dossier, un groupe d'administrateurs | Aucune séparation par environnement au sommet ; la production d'une équipe hérite des mêmes règles que son développement |
| **Hybride** (le cas le plus courant) | Presque toujours : le niveau qui pèse le plus sur les règles et les accès en premier, l'autre en dessous | Environnement puis application, ou entité puis environnement : les deux axes sont couverts | Un niveau de plus ; ne pas dépasser trois niveaux sans raison |

- **Dossiers hors de l'axe principal.** Quel que soit le découpage, un dossier d'**amorçage** (*bootstrap*) sous l'organisation, pour ce qui déploie l'infrastructure, et un dossier **commun** pour les services partagés entre environnements. Des services partagés mais instanciés par environnement (un projet de secrets par environnement) vont dans un sous-dossier de chaque environnement.
- **Limites.** Dix niveaux de dossiers au plus, 300 sous-dossiers directs par dossier, et six créations de dossier par minute et par projet appelant, autant de déplacements ([limites de Resource Manager](https://docs.cloud.google.com/resource-manager/docs/limits)).
- **La facturation ne suit pas la hiérarchie.** Un projet est lié à un [compte de facturation](#lexterm-compte-de-facturation) indépendamment de son dossier ; les rapports de facturation savent regrouper les coûts par dossier (voir [Facturation et budgets](#facturation-et-budgets)).

## Les projets

Un projet est à la fois une frontière d'IAM, de [quotas](#lexterm-quota), d'API activées et de facturation. Le blueprint en tire la règle : **un projet par application et par environnement**, plus quelques projets partagés.

| Projet (nom du blueprint) | Dossier | Contenu |
|---|---|---|
| `prj-b-seed` | Amorçage | Bucket d'état de l'IaC, comptes de service du pipeline des fondations |
| `prj-b-cicd` | Amorçage | Pipeline qui déploie les fondations (voir [Construire les fondations en code](#fondations-en-code)) |
| `prj-c-logging` | Commun | Destination des puits agrégés : buckets de journaux, Log Analytics |
| `prj-c-billing-export` | Commun | Dataset [BigQuery](#bigquery) de l'export de facturation |
| `prj-c-scc`, `prj-c-kms`, `prj-c-secrets` | Commun | Configuration de [Security Command Center](#security-command-center), clés [Cloud KMS](#cloud-kms) et secrets de niveau organisation |
| `prj-net-{env}-svpc` | Réseau | Projet hôte du [Shared VPC](#lexterm-shared-vpc) de chaque environnement (voir [Concevoir le réseau](#concevoir-le-reseau)) |
| `prj-{env}-{appli}`, `prj-{env}-secrets` | Un par environnement | Ressources de l'application, projet de service du Shared VPC ; secrets et clés propres à l'environnement |

- **ID de projet.** Six à trente caractères, minuscules, chiffres et tirets, commençant par une lettre. Il est **définitif** et ne peut jamais être réutilisé, même après suppression du projet. Il apparaît dans le nom de nombreuses ressources : aucune information sensible dedans.
- **Convention de nommage.** Celle du blueprint : `fldr-ENVIRONNEMENT` pour les dossiers, `prj-CODE-DESCRIPTION-XXXX` pour les projets, où `CODE` vaut `b`, `c`, `p`, `n`, `d` ou `net` et `XXXX` est un suffixe aléatoire de quatre caractères qui évite les collisions et rend les noms difficiles à deviner ; `vpc-p-svpc` pour un réseau, `sn-p-svpc-euwest1` pour un sous-réseau.

## Étiquettes et tags

Deux mécanismes de métadonnées coexistent, qui ne servent pas à la même chose.

| | Étiquette (*label*) | [Tag](#lexterm-tag) |
|---|---|---|
| Nature | Métadonnée posée sur la ressource | Clé et valeur sont des ressources, définies dans l'organisation ou un projet, avec leur propre IAM |
| Héritage | Aucun | Hérité par les descendants dans la hiérarchie |
| Conditions IAM et règles d'administration | Non | Oui : conditions des stratégies d'autorisation et de refus, règles d'administration conditionnelles |
| Facturation | Filtre des rapports, colonne de l'export BigQuery | Idem, avec l'héritage en plus |
| Longueur | 63 caractères | 256 caractères |

- **Étiquettes de gouvernance** sur chaque projet, celles du blueprint : `application`, `businesscode`, `billingcode`, `primarycontact`, `secondarycontact`, `environment`, `envcode`, `vpc`. Une étiquette n'accepte pas `@` : le contact s'écrit sans le domaine.
- **Tag `environment`.** Une clé de tag nommée `environment` avec les valeurs `production`, `staging`, `development` ou `test`, posée sur le dossier ou le projet, affiche un badge d'environnement dans le sélecteur de projets de la console.
- **Exceptions par tag.** Une règle d'administration peut être levée ou imposée sur les seules ressources qui portent un tag donné (`exception=public-web`, par exemple), plutôt que de multiplier les dossiers.

## Règles d'administration de base

Les règles d'administration interdisent une configuration quels que soient les rôles IAM du demandeur. Les organisations créées depuis le 3 mai 2024 reçoivent d'office un socle (*security baseline*) : pas de création ni d'import de clés de compte de service, pas de rôle Éditeur pour les comptes de service par défaut, partage limité au domaine, accès uniforme aux buckets. `gcloud org-policies list --organization=ORGANIZATION_ID` montre ce qui est en vigueur. Le blueprint pose en plus, sur l'organisation :

| Contrainte | Effet |
|---|---|
| `iam.disableServiceAccountKeyCreation`, `iam.disableServiceAccountKeyUpload` | Aucune clé de compte de service : fédération d'identité ou emprunt d'identité à la place (voir [Déployer sans clé](#deployer-sans-cle)) |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | Les comptes de service par défaut ne reçoivent pas le rôle Éditeur |
| `iam.allowedPolicyMemberDomains` | Rôles accordables aux seules identités de l'organisation (ID client Workspace ou Cloud Identity) |
| `essentialcontacts.allowedContactDomains` | Contacts essentiels limités aux domaines de l'entreprise |
| `storage.uniformBucketLevelAccess`, `storage.publicAccessPrevention` | Pas d'ACL par objet, pas de bucket ouvert à `allUsers` |
| `compute.skipDefaultNetworkCreation` | Pas de réseau `default` ni de ses règles de pare-feu permissives dans les nouveaux projets |
| `compute.vmExternalIpAccess`, `compute.requireOsLogin`, `compute.disableSerialPortAccess` | Pas d'IP publique sur les VM, accès SSH par OS Login, pas de port série |
| `sql.restrictPublicIp`, `sql.restrictAuthorizedNetworks` | Pas d'IP publique ni de réseaux autorisés sur Cloud SQL |
| `compute.restrictXpnProjectLienRemoval` | Un projet hôte Shared VPC ne peut pas être supprimé par erreur |
| `gcp.resourceLocations` | Ressources créées dans les seules régions admises, par exemple `in:europe-locations` |

- **Exceptions étroites.** Un service Cloud Run public (`allUsers`) est bloqué par `iam.allowedPolicyMemberDomains`, un bucket servi par Cloud CDN par `storage.publicAccessPrevention`. L'exception se pose sur le projet concerné ou par tag, jamais en levant la règle sur l'organisation.
- **Tester avant d'imposer.** Une règle en **mode simulation** (*dry-run*) journalise les violations dans les journaux d'audit sans rien refuser ([tester les règles](https://docs.cloud.google.com/organization-policy/test-policies)) : l'appliquer d'abord ainsi sur un environnement qui tourne.
- **Localisation.** `gcp.resourceLocations` ne contrôle que le lieu de création des ressources qui ont une localisation, pas les ressources globales, et Google précise que ce n'est pas un engagement de stockage des données.

## IAM : des groupes, au niveau des dossiers

- **Des groupes, jamais des personnes.** Chaque fonction a son groupe, alimenté par l'annuaire de l'entreprise, et c'est le groupe qui reçoit les rôles. Les groupes du blueprint : `grp-gcp-org-admin`, `grp-gcp-billing-admin`, `grp-gcp-billing-viewer`, `grp-gcp-audit-viewer`, `grp-gcp-security-reviewer`, `grp-gcp-network-viewer`, `grp-gcp-scc-admin`, `grp-gcp-secrets-admin`, `grp-gcp-kms-admin`.
- **Lecture pour les humains, écriture pour le pipeline.** Les ressources de la fondation ne sont modifiées que par le pipeline ; les groupes humains n'ont que des rôles de lecture sur elles. Les deux premiers groupes sont très privilégiés et ne servent pas au quotidien.
- **Au bon niveau.** Les rôles communs à un environnement se posent sur son dossier (le groupe des développeurs d'une application a des rôles larges sur `development`, lecture seule sur `production`), les rôles propres à une application sur son projet. Pas de rôles de base (Propriétaire, Éditeur, Lecteur) : voir [Bonnes pratiques IAM](#iam-bonnes-pratiques).
- **Surveiller les changements.** Une alerte sur les appels `SetIamPolicy` signale toute modification d'une stratégie d'autorisation.

## Journaux centralisés

Un [puits](#lexterm-puits-de-journaux-sink) **agrégé** posé sur l'organisation, avec `--include-children`, recopie les journaux de tous les projets vers le projet `prj-c-logging` ; un puits *interceptant* (`--intercept-children`) empêche en plus les projets de les router eux-mêmes.

```bash
gcloud logging sinks create audit-org \
  logging.googleapis.com/projects/PROJECT_LOGGING/locations/REGION/buckets/audit \
  --organization=ORGANIZATION_ID --include-children \
  --log-filter='logName:"cloudaudit.googleapis.com"'
# puis : roles/logging.bucketWriter pour l'identité d'écriture du puits sur le bucket de destination
```

Les journaux d'audit des activités d'administration, des événements système et des refus de règles sont toujours produits. Ceux d'**accès aux données** sont désactivés par défaut dans le blueprint, pour leur volume et leur coût : ne les activer que pour les services et les environnements qui manipulent des données sensibles (voir [Observabilité](#observabilite) et [Détection et conformité](#detection-et-conformite)).

## Liste de contrôle

1. Compte Cloud Identity ou Workspace sur le domaine, comptes personnels rapatriés, fédération avec l'annuaire de l'entreprise.
2. Super administrateurs séparés, avec clé de sécurité ; Administrateur de l'organisation délégué à un groupe.
3. Groupes par fonction créés dans l'annuaire.
4. Dossiers d'amorçage et commun, puis l'axe principal (environnement, entité ou équipe).
5. Projet d'amorçage, bucket d'état et pipeline des fondations ; tout ce qui suit passe par le code.
6. Règles d'administration de base sur l'organisation, en simulation d'abord pour les plus contraignantes.
7. `Créateur de projets` et `Créateur de comptes de facturation` retirés au domaine.
8. Puits agrégé vers le projet de journalisation, contacts essentiels, export de facturation vers BigQuery.
9. Projets hôtes Shared VPC par environnement.
10. *Project factory* : un projet par application et par environnement, étiquettes et tag `environment` compris.

## Pièges

- **Calquer l'organigramme.** Une réorganisation interne oblige alors à déplacer des projets, et un projet déplacé change de règles et de rôles hérités d'un coup.
- **Un projet pour tous les environnements.** Impossible ensuite de donner aux développeurs des droits larges sur le développement sans les leur donner sur la production, ou de séparer les quotas.
- **Laisser le réseau `default`.** Il crée un sous-réseau dans chaque région et des règles de pare-feu permissives, dans chaque projet où l'API Compute Engine est activée.
- **Poser une règle sur l'organisation en production sans simulation.** Une contrainte de localisation ou de domaine peut bloquer des déploiements en cours ou des services publics légitimes.
- **Supprimer un projet pour « faire de la place ».** Un projet supprimé reste trente jours en suppression réversible, compte toujours dans le quota de projets, et son ID n'est jamais réutilisable.
- **Oublier les quotas de projets.** Le nombre de projets créés par un utilisateur, un compte de service ou une organisation est limité, tout comme le nombre de projets liés à un compte de facturation ; une *project factory* bute vite dessus. Les augmentations se demandent à l'avance.

## Alternatives en logiciel libre

- **OpenStack Keystone** (Apache 2.0) : le service d'identité d'OpenStack organise un cloud privé en domaines et projets imbriqués, avec rôles hérités ; c'est la même hiérarchie de responsabilité, sans règles d'administration équivalentes.
- **Keycloak** (Apache 2.0) : fournisseur d'identité avec groupes, fédération SAML et OIDC ; il tient le rôle de l'annuaire que Cloud Identity synchronise, pas celui de la hiérarchie des ressources.
- **Open Policy Agent** (Apache 2.0) et **Gatekeeper** (Apache 2.0) : des règles écrites en Rego qui refusent une configuration à l'admission Kubernetes ou dans une chaîne d'IaC, dans le rôle des règles d'administration.
- **Kyverno** (Apache 2.0) : le même rôle de garde-fou pour Kubernetes, avec des règles en YAML qui valident, modifient ou génèrent des ressources.
- **Capsule** (Apache 2.0) : regroupe des espaces de noms Kubernetes en locataires avec quotas, règles et rôles communs, à la manière de dossiers pour un cluster partagé.
- **Cloud Custodian** (Apache 2.0) : règles de gouvernance en YAML exécutées sur les ressources existantes, Google Cloud compris ; il détecte et corrige après coup ce qu'une règle d'administration aurait refusé.
