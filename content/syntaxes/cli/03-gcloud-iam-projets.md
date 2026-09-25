---
title: "gcloud : projets, API et IAM"
subgroup: gcloud
type: syntax
---

Un principal s'écrit `user:EMAIL`, `group:EMAIL`, `serviceAccount:EMAIL` ou `domain:DOMAINE`. Un rôle prédéfini s'écrit `roles/SERVICE.ROLE`, un rôle personnalisé `projects/PROJECT_ID/roles/ROLE_ID` ou `organizations/ORG_ID/roles/ROLE_ID`.

### Projets, dossiers et facturation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un projet dans un dossier | `gcloud projects create PROJECT_ID --folder=FOLDER_ID --labels=env=dev` | ID de 6 à 30 caractères, minuscules, chiffres et tirets, non modifiable ; `--organization=ORG_ID` pour le placer à la racine |
| Décrire un projet | `gcloud projects describe PROJECT_ID` | Numéro, parent, état (`ACTIVE`, `DELETE_REQUESTED`), labels |
| Lister les projets d'un dossier | `gcloud projects list --filter="parent.id=FOLDER_ID"` | Projets directement sous ce dossier, pas ceux des sous-dossiers |
| Remonter la hiérarchie | `gcloud projects get-ancestors PROJECT_ID` | Projet, dossiers parents, organisation |
| Supprimer un projet | `gcloud projects delete PROJECT_ID` | Projet arrêté puis supprimé définitivement après 30 jours |
| Restaurer un projet supprimé | `gcloud projects undelete PROJECT_ID` | Possible pendant les 30 jours qui précèdent la suppression définitive |
| [!PREVERSION] Déplacer un projet | `gcloud beta projects move PROJECT_ID --folder=FOLDER_ID` | Le projet hérite ensuite des stratégies du nouveau parent |
| Trouver l'organisation | `gcloud organizations list` | Nom de domaine et `ID` numérique |
| Créer un dossier | `gcloud resource-manager folders create --display-name=NOM --organization=ORG_ID` | `--folder=FOLDER_ID` pour un sous-dossier |
| Lister les dossiers | `gcloud resource-manager folders list --organization=ORG_ID` | Premier niveau seulement ; répéter avec `--folder` pour descendre |
| Lister les comptes de facturation | `gcloud billing accounts list` | ID de la forme `XXXXXX-XXXXXX-XXXXXX`, statut ouvert ou fermé |
| Rattacher un projet à la facturation | `gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID` | Exige `roles/billing.user` sur le compte de facturation et le droit de modifier la facturation du projet |
| Vérifier la facturation d'un projet | `gcloud billing projects describe PROJECT_ID` | `billingEnabled: true` et le compte rattaché |
| Détacher la facturation | `gcloud billing projects unlink PROJECT_ID` | Les ressources payantes du projet s'arrêtent |

### API (services)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Activer des API | `gcloud services enable run.googleapis.com artifactregistry.googleapis.com` | Plusieurs services en une commande ; quelques minutes de propagation possibles |
| Lister les API activées | `gcloud services list --enabled` | Nom et titre de chaque service |
| Chercher le nom d'une API | `gcloud services list --available --filter="name:bigquery"` | Services activables dont le nom contient ce mot |
| Désactiver une API | `gcloud services disable SERVICE.googleapis.com` | Refusé si d'autres API activées en dépendent ou si l'API a servi récemment ; `--force` passe outre et désactive aussi les API dépendantes |
| [!PREVERSION] Créer l'agent de service d'une API | `gcloud beta services identity create --service=SERVICE.googleapis.com --project=PROJECT_ID` | Adresse de l'agent de service, à qui donner un rôle avant la première utilisation (CMEK, par exemple) |

### Stratégie d'autorisation (IAM)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Donner un rôle sur un projet | `gcloud projects add-iam-policy-binding PROJECT_ID --member=group:GROUPE@DOMAINE --role=roles/bigquery.dataViewer` | Liaison ajoutée ; la stratégie complète s'affiche en retour |
| Donner un rôle sur un dossier | `gcloud resource-manager folders add-iam-policy-binding FOLDER_ID --member=... --role=...` | Hérité par tous les projets du dossier |
| Donner un rôle sur l'organisation | `gcloud organizations add-iam-policy-binding ORG_ID --member=... --role=...` | Hérité par toute l'organisation |
| Rôle temporaire (condition) | `gcloud projects add-iam-policy-binding PROJECT_ID --member=user:EMAIL --role=roles/compute.admin --condition='expression=request.time < timestamp("2026-12-31T23:59:59Z"),title=jusqua-fin-2026'` | Liaison conditionnelle en CEL ; interdit sur les rôles de base (`owner`, `editor`, `viewer`) |
| Condition dont l'expression contient une virgule | `--condition='^;^title=env-prod;expression=resource.matchTag("ORG_ID/env", "prod")'` | `^;^` change le séparateur des paires clé=valeur ; ici, accès limité aux ressources portant le tag `env=prod` |
| Ajouter sans condition dans une stratégie qui en a | `--condition=None` | Sans cette valeur, gcloud demande quelle condition utiliser, ou échoue en mode `--quiet` |
| Retirer un rôle | `gcloud projects remove-iam-policy-binding PROJECT_ID --member=user:EMAIL --role=ROLE` | `--all` retire aussi toutes les variantes conditionnelles de la liaison |
| Qui a un rôle donné | `gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" --filter="bindings.role=roles/owner" --format="value(bindings.members)"` | Un principal par ligne |
| Quels rôles a un principal | `gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" --filter="bindings.members=user:EMAIL" --format="value(bindings.role)"` | Liaisons directes sur le projet seulement, sans l'héritage ni les groupes |
| Exporter puis réécrire la stratégie | `gcloud projects get-iam-policy PROJECT_ID --format=json > policy.json` puis `gcloud projects set-iam-policy PROJECT_ID policy.json` | Remplace la stratégie entière ; l'`etag` du fichier fait échouer l'écriture si elle a changé entre-temps |
| Pourquoi un accès est accordé ou refusé | `gcloud policy-intelligence troubleshoot-policy iam //cloudresourcemanager.googleapis.com/projects/PROJECT_ID --principal-email=EMAIL --permission=PERMISSION` | Liaisons examinées sur toute la hiérarchie, avec leur verdict |

> [!WARNING]
> `set-iam-policy` écrase toute la stratégie : un fichier obsolète retire des accès sans prévenir. Pour ajouter ou retirer un accès, préférer `add-` et `remove-iam-policy-binding`, qui relisent la stratégie à chaque appel.

### Comptes de service

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un compte de service | `gcloud iam service-accounts create SA_NAME --display-name="Pipeline ventes"` | Adresse `SA_NAME@PROJECT_ID.iam.gserviceaccount.com` ; aucun rôle par défaut |
| Lister les comptes de service | `gcloud iam service-accounts list --format="table(email, disabled)"` | Inclut les comptes de service par défaut du projet |
| Lister les clés gérées par l'utilisateur | `gcloud iam service-accounts keys list --iam-account=SA@PROJECT_ID.iam.gserviceaccount.com --managed-by=user` | Clés téléchargées, donc à auditer ; `system` : clés gérées par Google |
| Supprimer une clé | `gcloud iam service-accounts keys delete KEY_ID --iam-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Les applications qui l'utilisent perdent l'accès aussitôt |
| Autoriser l'emprunt d'identité | `gcloud iam service-accounts add-iam-policy-binding SA@PROJECT_ID.iam.gserviceaccount.com --member=user:EMAIL --role=roles/iam.serviceAccountTokenCreator` | Rôle donné **sur le compte de service**, pas sur le projet : l'utilisateur peut émettre des jetons courts pour ce seul compte |
| Autoriser l'attachement à une ressource | `gcloud iam service-accounts add-iam-policy-binding SA@PROJECT_ID.iam.gserviceaccount.com --member=user:EMAIL --role=roles/iam.serviceAccountUser` | Permet de déployer une VM, un service Cloud Run ou un job avec ce compte de service |
| Obtenir un jeton en tant que compte de service | `gcloud auth print-access-token --impersonate-service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Jeton court, sans clé |
| Désactiver un compte de service | `gcloud iam service-accounts disable SA@PROJECT_ID.iam.gserviceaccount.com` | Réversible par `enable` ; à faire avant une suppression pour vérifier que rien ne casse |

> [!WARNING]
> Ne pas créer de clé de compte de service (`gcloud iam service-accounts keys create`) : une clé est un secret longue durée qui fuit facilement. Emprunter l'identité depuis un poste, attacher le compte de service à la ressource dans Google Cloud, et utiliser la [fédération d'identité de charge de travail](#workload-identity-federation) depuis l'extérieur. La contrainte `iam.managed.disableServiceAccountKeyCreation` bloque leur création.

### Rôles

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Permissions d'un rôle | `gcloud iam roles describe roles/storage.objectViewer` | `includedPermissions`, titre, niveau de publication |
| Chercher un rôle prédéfini | `gcloud iam roles list --filter="name:bigquery" --format="table(name, title)"` | Sans `--project` ni `--organization`, la commande liste les rôles prédéfinis |
| Rôles attribuables sur une ressource | `gcloud iam list-grantable-roles //cloudresourcemanager.googleapis.com/projects/PROJECT_ID` | Rôles applicables à ce type de ressource |
| Créer un rôle personnalisé | `gcloud iam roles create ROLE_ID --project=PROJECT_ID --title="Lecteur des jobs" --permissions=bigquery.jobs.get,bigquery.jobs.list --stage=GA` | Rôle `projects/PROJECT_ID/roles/ROLE_ID` ; `--file=role.yaml` pour une définition en fichier |
| Ajouter des permissions à un rôle personnalisé | `gcloud iam roles update ROLE_ID --project=PROJECT_ID --add-permissions=bigquery.jobs.create` | `--remove-permissions` pour en retirer |
| Partir d'un rôle prédéfini | `gcloud iam roles copy --source=roles/viewer --destination=ROLE_ID --dest-project=PROJECT_ID` | Copie à élaguer ensuite |
| Supprimer un rôle personnalisé | `gcloud iam roles delete ROLE_ID --project=PROJECT_ID` | Récupérable par `gcloud iam roles undelete` pendant 7 jours ; les liaisons qui le citent restent mais n'ont plus d'effet |

### Règles d'administration

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Règles définies sur un projet | `gcloud org-policies list --project=PROJECT_ID` | Contraintes qui ont une règle à ce niveau ; `--show-unset` pour toutes |
| Règle effective (héritage compris) | `gcloud org-policies describe iam.managed.disableServiceAccountKeyCreation --project=PROJECT_ID --effective` | Résultat de la hiérarchie pour cette contrainte |
| Appliquer une règle depuis un fichier | `gcloud org-policies set-policy policy.yaml` | Fichier YAML : `name: projects/PROJECT_ID/policies/CONTRAINTE`, puis `spec:` → `rules:` → `- enforce: true` pour une contrainte booléenne |
| Revenir à la règle héritée | `gcloud org-policies reset CONTRAINTE --project=PROJECT_ID` | La règle du parent s'applique de nouveau |

### Audit à l'échelle de l'organisation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Qui a un rôle, partout | `gcloud asset search-all-iam-policies --scope=organizations/ORG_ID --query="policy:roles/owner"` | Liaisons trouvées sur toutes les ressources de l'organisation ; exige `cloudasset.assets.searchAllIamPolicies` |
| Tous les accès d'un principal | `gcloud asset search-all-iam-policies --scope=organizations/ORG_ID --query="policy:EMAIL"` | Ressource, rôle et condition de chaque liaison qui le cite |
| Liaisons accordant une permission | `gcloud asset search-all-iam-policies --scope=folders/FOLDER_ID --query="policy.role.permissions:storage.buckets.delete"` | Rôles qui contiennent la permission, où qu'ils soient attribués |
| Accès donnés à des comptes personnels | `gcloud asset search-all-iam-policies --scope=organizations/ORG_ID --query="memberTypes:user"` | Liaisons à des utilisateurs individuels plutôt qu'à des groupes |
| Accès effectifs d'un principal | `gcloud asset analyze-iam-policy --organization=ORG_ID --identity=user:EMAIL` | Ressources accessibles, en tenant compte de l'héritage et des groupes |
| Qui peut agir en tant qu'un compte de service | `gcloud asset analyze-iam-policy --organization=ORG_ID --full-resource-name=//iam.googleapis.com/projects/PROJECT_ID/serviceAccounts/SA_EMAIL --permissions=iam.serviceAccounts.actAs` | Principaux qui détiennent la permission sur ce compte |

Contexte : [bonnes pratiques IAM](#iam-bonnes-pratiques), [hiérarchie des ressources](#hierarchie-des-ressources), [Cloud IAM](#cloud-iam), [filtres et formats](#gcloud-filtres-formats), [authentifier un appel](#authentifier-un-appel).
