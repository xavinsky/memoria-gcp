---
title: "Terraform sur Google Cloud : état, identités, pipeline"
---

Un Terraform qui tient dans la durée sur Google Cloud repose sur trois décisions prises dès le premier projet : **où vit l'[état](#lexterm-etat-terraform-state)** (un bucket [Cloud Storage](#cloud-storage) versionné, un état par composant et par environnement), **sous quelle identité** s'exécutent les `plan` et les `apply` (un compte de service emprunté, jamais une clé), et **qui a le droit d'appliquer** (la CI sur une branche protégée, ou [Infrastructure Manager](#infrastructure-manager)). Tout ce qui suit vaut aussi pour OpenTofu, qui lit la même configuration.

## Découpage du code et des états

| Couche | Contenu | Rythme de changement | Qui applique |
|---|---|---|---|
| **Amorçage** | Projet d'administration, bucket d'état, comptes de service Terraform, pool Workload Identity Federation | Une fois, puis rarement | Un administrateur ; état local migré ensuite vers le bucket |
| **Organisation** | Dossiers, stratégies d'organisation, IAM d'organisation, journaux centralisés | Rare | Compte de service de l'organisation |
| **Réseau** | VPC partagé, sous-réseaux, DNS, interconnexions | Rare | Compte de service réseau, limité au projet hôte |
| **Projets** | Création des projets par une *project factory*, API activées, budgets | À chaque nouvelle équipe | Compte de service des projets |
| **Applications** | Cloud Run, bases, buckets, IAM de l'application, par environnement | Fréquent | Compte de service de l'application, un par environnement |

- **Un état par composant et par environnement.** La recommandation de Google est de ne pas dépasser 100 ressources par état, idéalement quelques dizaines : chaque `plan` relit toutes les ressources de l'état. Un dossier `environments/dev`, `environments/prod`… par service, chacun avec son `backend.tf`, qui instancie un module commun.
- **Pas d'espaces de travail multiples** (*workspaces*) pour séparer les environnements : un seul backend partagé devient un point de défaillance unique, et le code se remplit de `terraform.workspace == "prod" ? … : …`.
- **Communication entre états** par les sorties : la couche réseau exporte l'identifiant du VPC, la couche application le lit avec la source de données `terraform_remote_state`.
- **Versions figées.** Chaque module racine fixe la version mineure du fournisseur (`~> 8.4` accepte les correctifs 8.4.x) et versionne son `.terraform.lock.hcl`. Les versions se relisent régulièrement, par exemple avec Dependabot.

## Backend et fournisseur

```hcl
terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 8.4" }
  }
  backend "gcs" {
    bucket                      = "PROJECT_ADMIN-tfstate"
    prefix                      = "reseau/prod"            # un préfixe par état
    impersonate_service_account = "terraform-reseau@PROJECT_ADMIN.iam.gserviceaccount.com"
  }
}

provider "google" {
  project                     = var.project_id
  region                      = "europe-west1"
  impersonate_service_account = "terraform-reseau@PROJECT_ADMIN.iam.gserviceaccount.com"
  default_labels              = { gere-par = "terraform" }
}
```

- **Verrouillage.** Le backend `gcs` verrouille l'état pendant chaque opération, sans table annexe. Le bucket doit exister avant `terraform init` : on le crée dans la couche d'amorçage, avec un état local qu'on migre ensuite (`terraform init -migrate-state`).
- **Versionnage.** HashiCorp recommande fortement d'activer Object Versioning sur le bucket d'état, pour récupérer une version après une erreur ; une règle de cycle de vie supprime les versions trop anciennes.
- **Chiffrement.** Le bucket est chiffré au repos par défaut. `kms_encryption_key` chiffre l'état avec une clé [Cloud KMS](#cloud-kms) (l'agent de service Cloud Storage doit avoir `roles/cloudkms.cryptoKeyEncrypterDecrypter` sur la clé) ; `encryption_key` ou la variable `GOOGLE_ENCRYPTION_KEY` prennent une clé fournie par le client. Un état chiffré par une clé perdue ou détruite est irrécupérable. OpenTofu peut en plus chiffrer le fichier lui-même, côté client, avant son envoi au backend.
- **Accès au bucket.** Seuls la CI et un ou deux administrateurs lisent le bucket : l'état contient les attributs de toutes les ressources, secrets compris.

```hcl
# Couche d'amorçage : le bucket d'état lui-même
resource "google_storage_bucket" "etat" {
  name                        = "PROJECT_ADMIN-tfstate"
  location                    = "EU"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning { enabled = true }
  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
  lifecycle { prevent_destroy = true }
}
```

## Identités

- **En local** : `gcloud auth application-default login` produit les identifiants [ADC](#lexterm-adc-application-default-credentials) de l'utilisateur, et `impersonate_service_account` fait exécuter les appels sous le compte de service Terraform. L'utilisateur n'a besoin que de `roles/iam.serviceAccountTokenCreator` sur ce compte, pas des rôles d'administration eux-mêmes ; les quotas et les droits sont ceux du compte emprunté (voir [Authentifier un appel](#authentifier-un-appel)).
- **En CI hors Google Cloud** (GitHub Actions, GitLab CI) : Workload Identity Federation échange le jeton OIDC du pipeline contre un jeton Google, sans clé JSON (voir [Déployer sans clé](#deployer-sans-cle)). Si le fournisseur `google` emprunte ensuite un compte de service, le principal fédéré doit avoir `roles/iam.serviceAccountTokenCreator` sur ce compte.
- **En CI sur Google Cloud** : [Cloud Build](#cloud-build) s'exécute sous le compte de service choisi pour le déclencheur ; les identifiants sont injectés, rien à télécharger.
- **Séparer les pouvoirs.** Un compte de service par couche, limité à son périmètre (le compte réseau n'a de droits que sur le projet hôte). Un compte en lecture pour les `plan` des *pull requests*, un compte d'écriture réservé à l'`apply` sur la branche protégée.

## Pipeline

Le principe : `plan` sur chaque *pull request*, relu par un humain ; `apply` du plan enregistré après la fusion, jamais d'`apply` depuis un poste.

```yaml
# .github/workflows/terraform.yml (extrait)
permissions: { contents: read, id-token: write }
steps:
  - uses: actions/checkout@v7
  - uses: google-github-actions/auth@v3
    with:
      workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
  - uses: hashicorp/setup-terraform@v4
  - run: terraform init -input=false
  - run: terraform plan -input=false -out=tfplan
  - if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    run: terraform apply -input=false tfplan
```

- **Contrôle de conformité avant l'`apply`.** `gcloud beta terraform vet` [!PREVERSION] (composant `terraform-tools`) confronte le plan JSON à une bibliothèque de contraintes et renvoie le code 2 en cas de violation : `terraform show -json tfplan > tfplan.json`, puis `gcloud beta terraform vet tfplan.json --policy-library=POLICY_DIR`. Conftest ou OPA lisent le même JSON avec des règles Rego. Les stratégies d'organisation restent le garde-fou final, appliqué par l'API quel que soit l'outil.
- **Avec Infrastructure Manager**, la CI ne lance pas Terraform elle-même : `gcloud infra-manager previews create` remplace le `plan`, `gcloud infra-manager deployments apply` l'`apply`, sous un compte de service qui porte `roles/config.agent`. Le module `im_cloudbuild_workspace` (dépôt `terraform-google-modules/bootstrap`) crée les deux déclencheurs Cloud Build : prévisualisation sur *pull request*, déploiement à la fusion. La configuration ne doit pas contenir de bloc `backend`, et Terraform est limité à la version 1.5.7.

## Modules de Google

- **Cloud Foundation Toolkit** (CFT) : les modules de l'organisation GitHub `terraform-google-modules`, publiés dans le registre Terraform (`terraform-google-modules/project-factory/google`, `…/network/google`), et les *blueprints* qui les assemblent — `terraform-example-foundation` pour une fondation d'organisation sécurisée. Ils s'utilisent comme dépendances versionnées.
- **Cloud Foundation Fabric** (dépôt `GoogleCloudPlatform/cloud-foundation-fabric`) : des modules plus minces, proches des ressources du fournisseur, et **FAST**, une fondation d'organisation par étapes. Le dépôt est fait pour être cloné puis repris dans ses propres dépôts, pas référencé comme une bibliothèque.

## Reprendre l'existant

```hcl
import {
  id = "projects/PROJECT_ID/global/networks/reseau-principal"
  to = google_compute_network.principal
}
```

- **Blocs `import`** (Terraform 1.5 et plus) : l'import se prévisualise au `plan` et s'exécute à l'`apply`. `terraform plan -generate-config-out=genere.tf` écrit les blocs `resource` correspondants, à relire. Le format de l'`id` est donné dans la section *Import* de chaque ressource du fournisseur. `terraform import ADRESSE ID` fait la même chose ressource par ressource, hors revue.
- [!PREVERSION] **Export en masse** : `gcloud beta resource-config bulk-export --project=PROJECT_ID --resource-format=terraform --path=DOSSIER` (composant `config-connector`, API Cloud Asset) produit le HCL de tout un projet, un dossier ou une organisation ; `gcloud beta resource-config list-resource-types` liste les types couverts.
- **Infrastructure Manager** : `--import-existing-resources` sur `deployments apply` importe une ressource au lieu d'échouer sur un conflit 409, pour les types pris en charge.
- Google recommande de n'importer qu'avec une approbation explicite, et de recréer plutôt qu'importer quand c'est peu coûteux : une ressource importée garde une configuration dont on ne connaît pas toujours l'origine.

## Pièges

- **Secrets dans l'état.** `google_service_account_key`, `tls_private_key` ou un mot de passe passé à `google_sql_user` finissent en clair dans l'état ; `sensitive` ne les masque qu'à l'affichage. Les arguments *write-only* (`password_wo` de `google_sql_user`, `secret_data_wo` de `google_secret_manager_secret_version`) ne sont jamais écrits dans l'état, mais demandent Terraform 1.11 ou plus. Sinon, créer le secret dans [Secret Manager](#secret-manager) par Terraform et y ajouter la valeur hors de Terraform.
- **API activées à terme.** `google_project_service` rend la main avant que l'API soit toujours utilisable : la ressource suivante échoue avec « API has not been used in project … or it is disabled », surtout dans un projet qui vient d'être créé. Relancer, ou faire dépendre les ressources de l'activation. `disable_on_destroy = false` évite qu'un `destroy` coupe une API dont d'autres dépendent.
- **Propagation IAM.** Une liaison de rôle s'applique en général en deux minutes, parfois sept ou plus : un `apply` qui crée un rôle puis l'utilise aussitôt peut échouer en 403 et réussir à la relance.
- **Ressources IAM exclusives.** `google_project_iam_policy` et `google_project_iam_binding` réécrivent toute la stratégie ou tout le rôle, et retirent au passage les rôles posés par Google pour ses agents de service. Préférer `google_project_iam_member`, qui ajoute une liaison sans toucher aux autres (voir [IAM](#cloud-iam)).
- **Protections contre la suppression, à deux niveaux.** `deletion_protection` du fournisseur (vrai par défaut sur les clusters GKE et les instances Cloud SQL) bloque seulement Terraform ; `deletion_protection_enabled` d'une instance Cloud SQL protège côté Google, contre la console et `gcloud` aussi. `google_project` porte `deletion_policy = "PREVENT"` par défaut. Pour le reste, `lifecycle { prevent_destroy = true }`.
- **Le bucket d'état dans le projet qu'il gère.** Un `destroy` du projet emporte l'état qui le décrivait. Le bucket vit dans le projet d'administration de la couche d'amorçage.

## Alternatives en logiciel libre

- **OpenTofu** (MPL 2.0) : même HCL, même fournisseur `google`, même backend `gcs` ; il chiffre en plus l'état côté client, avec une clé Cloud KMS par son fournisseur de clés `gcp_kms`.
- **Atlantis** (Apache 2.0) : exécute `plan` sur chaque pull request et `apply` sur commentaire, en publiant le résultat dans le fil ; serveur et identité sont à héberger soi-même.
- **Terragrunt** (MIT) : génère les blocs `backend` et `provider` par environnement et enchaîne les états dépendants.
- **TFLint** (MPL 2.0) et son jeu de règles Google (MPL 2.0) : détecte avant le `plan` les valeurs que l'API refuserait, comme un type de machine inexistant.
- **Trivy** et **Checkov** (Apache 2.0) : analyse statique du code HCL (bucket public, chiffrement absent, rôle primitif), en complément des règles Rego évaluées par **Conftest** (Apache 2.0) sur le plan.
- **Infracost** (Apache 2.0) : estime en pull request l'écart de coût mensuel introduit par le plan, ressources Google Cloud comprises.
- **Tofu Controller** (Apache 2.0) : exécute OpenTofu depuis Flux, avec détection et correction périodique de la dérive, pour ceux qui veulent un modèle GitOps sans quitter HCL.
