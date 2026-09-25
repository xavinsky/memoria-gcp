---
title: "Construire les fondations en code (Pulumi)"
subgroup: Fondations
---

Les fondations décrites dans [Organiser l'environnement](#hierarchie-des-ressources) — dossiers, règles d'administration, groupes, réseau partagé, projets — se construisent en [IaC](#lexterm-iac-infrastructure-as-code), jamais à la main. L'[enterprise foundations blueprint](https://docs.cloud.google.com/architecture/blueprints/security-foundations/deployment-methodology) de Google va plus loin : les ressources de la fondation ne sont modifiées **que** par un pipeline, et les humains n'ont que des droits de lecture sur elles. Ce site recommande [Pulumi](#lexterm-pulumi) en Python pour l'écrire (voir [Choisir un outil d'IaC](#choisir-un-outil-iac)) ; l'équivalent Terraform, et les modules de Google qui le servent, sont dans [Terraform sur Google Cloud](#terraform-sur-gcp).

![Fondations en couches : chaque couche lit les sorties de la précédente](../../svg/fondations-en-couches.svg)

## Pourquoi le code est indispensable ici

- **Reproductibilité.** La configuration de l'organisation se relit et se reconstruit : un deuxième environnement, une organisation de test ou une filiale reprennent le même code.
- **Revue.** Une règle d'administration ou un rôle sur un dossier touche des centaines de projets. En code, le changement passe par une *pull request* et un `pulumi preview` relu avant d'être appliqué.
- **Dérive.** `pulumi preview --refresh` compare l'état réel à l'état voulu et révèle ce qui a été modifié dans la console.
- **Audit.** L'historique Git dit qui a demandé quoi et pourquoi ; les journaux d'audit ne disent que qui a appliqué.
- **[*Project factory*](#lexterm-project-factory).** Une équipe demande un projet en ajoutant quelques lignes de configuration ; le pipeline le crée avec son dossier, sa facturation, ses API, ses étiquettes et ses groupes, toujours de la même façon.

## Pourquoi Pulumi en Python

- **Licence libre.** Le moteur, le SDK Python et le fournisseur `gcp` sont sous Apache 2.0 ; Terraform est sous BSL. Le CLI, un état dans Cloud Storage et des règles exécutées localement couvrent tout ce qui suit sans service payant.
- **Même couverture que Terraform.** Le fournisseur `pulumi_gcp` (version 9.x) est construit à partir du fournisseur Terraform `google-beta` : mêmes ressources, mêmes arguments, mêmes comportements, y compris les protections contre la suppression.
- **Le langage du reste du site.** Boucles, fonctions, tests unitaires avec `pytest`, paquets Python : une *project factory* est une boucle sur un dictionnaire.
- **Automation API.** Le module `pulumi.automation` pilote les stacks depuis un programme Python, par exemple un portail interne qui crée un projet sur demande sans passer par le CLI.
- **Quand rester en Terraform.** Pour reprendre une fondation existante en HCL, ou pour déployer tel quel `terraform-example-foundation` ou FAST de Cloud Foundation Fabric, les deux fondations de référence de Google.

## Découper en projets Pulumi et en stacks

Un **projet Pulumi** (un dossier avec son `Pulumi.yaml`) par couche, et une **stack** par environnement dans les couches qui en ont. Chaque couche publie ses sorties (`pulumi.export`), que la suivante lit par `StackReference`.

| Couche | Stacks | Contenu | Exécutée sous | Exporte |
|---|---|---|---|---|
| **Amorçage** | une seule | Projet `prj-b-seed`, bucket d'état, clé Cloud KMS, comptes de service des couches, pool [Workload Identity Federation](#workload-identity-federation) | Un administrateur, une fois | Comptes de service, fournisseur WIF |
| **Organisation** | une seule | Dossiers, règles d'administration de l'organisation, IAM des groupes, puits agrégé, contacts essentiels | `sa-org` | ID des dossiers |
| **Réseau** | `dev`, `nonprod`, `prod` | Projet hôte et Shared VPC, sous-réseaux, DNS, connectivité hybride (voir [Concevoir le réseau](#concevoir-le-reseau)) | `sa-reseau` | Réseau, sous-réseaux |
| **Projets** | `dev`, `nonprod`, `prod` | *Project factory* : projets, API, rattachement au Shared VPC, budgets | `sa-projets` | ID des projets |
| **Applications** | une par application et environnement | Cloud Run, bases, buckets, IAM de l'application | Compte de service de l'application | — |

```python
# Couche projets : lire les sorties de la couche organisation (état dans Cloud Storage)
org = pulumi.StackReference("organization/org/org")      # organization/PROJET/STACK
dossiers = org.require_output("dossiers")                  # {"dev": "folders/…", …}
```

- **Rythme et rayon d'action.** Les couches hautes changent rarement mais touchent tout ; les applications changent tous les jours. Les séparer réduit la durée de chaque `preview` et le périmètre de chaque compte de service.
- **Un compte de service par couche**, limité à son périmètre : `sa-reseau` n'a de rôles que sur les projets hôtes, `sa-projets` sur les dossiers d'environnement et le compte de facturation (`roles/billing.user`).
- **Avec un état dans Cloud Storage**, la partie organisation du nom de stack est toujours le mot `organization`.

## L'amorçage

Le bucket d'état et l'identité de la CI doivent exister avant le premier `pulumi login` : c'est le rôle de quelques commandes `gcloud`, lancées une fois par un administrateur, dans le dossier d'amorçage.

```bash
gcloud projects create prj-b-seed-XXXX --folder=FOLDER_BOOTSTRAP_ID
gcloud billing projects link prj-b-seed-XXXX --billing-account=BILLING_ACCOUNT_ID
gcloud services enable storage.googleapis.com cloudkms.googleapis.com iam.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com cloudresourcemanager.googleapis.com \
  cloudbilling.googleapis.com orgpolicy.googleapis.com --project=prj-b-seed-XXXX
gcloud storage buckets create gs://BUCKET_ETAT --project=prj-b-seed-XXXX --location=EU \
  --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://BUCKET_ETAT --versioning
gcloud kms keyrings create pulumi --location=europe-west1 --project=prj-b-seed-XXXX
gcloud kms keys create etat --keyring=pulumi --location=europe-west1 --purpose=encryption \
  --project=prj-b-seed-XXXX
```

La stack d'amorçage prend ensuite le relais : comptes de service des couches et leurs rôles, pool et fournisseur OIDC pour la CI (voir [Déployer sans clé](#deployer-sans-cle)), et le bucket lui-même, repris par `pulumi import` et marqué `protect=True`. Les API de gestion (Resource Manager, Cloud Billing, Organization Policy, IAM) sont activées dans le projet d'amorçage, qui porte les comptes de service des pipelines.

## État et secrets

```bash
pulumi login gs://BUCKET_ETAT
pulumi stack init prod \
  --secrets-provider="gcpkms://projects/prj-b-seed-XXXX/locations/europe-west1/keyRings/pulumi/cryptoKeys/etat"
pulumi config set --secret motDePasseBase VALEUR   # chiffré par la clé KMS, versionnable dans Git
```

| | Cloud Storage (`gs://`) | Pulumi Cloud |
|---|---|---|
| Hébergement | Un bucket de `prj-b-seed`, dans la région choisie | Service SaaS de Pulumi |
| Verrou | Fichier de verrou par stack | Transactionnel |
| Reprise après incident | Versions d'objets du bucket ; pas de reprise transparente d'une mise à jour interrompue | Journal transactionnel des points de contrôle |
| Accès | IAM du bucket et de la clé KMS | Équipes et rôles dans Pulumi Cloud |
| Règles (*policy packs*) | Exécutées localement avec `--policy-pack` | Appliquées à des groupes de stacks, packs prêts à l'emploi (éditions payantes) |
| Coût | Stockage et opérations Cloud Storage | Gratuit pour un usage individuel ou open source, éditions payantes pour les équipes |

- **Secrets.** Avec un état dans Cloud Storage, le fournisseur de secrets par défaut est une phrase de passe à distribuer. `gcpkms://` chiffre à la place la clé de données de la stack par une clé [Cloud KMS](#cloud-kms) de type `ENCRYPT_DECRYPT` : la CI et les administrateurs n'ont besoin que de `roles/cloudkms.cryptoKeyEncrypterDecrypter` sur la clé. Les valeurs chiffrées vivent dans `Pulumi.STACK.yaml`, qui se versionne. Une clé détruite rend ces secrets et ceux de l'état illisibles.
- **Accès au bucket.** Seuls les comptes de service des pipelines et un ou deux administrateurs : l'état contient les attributs de toutes les ressources. Pour les secrets applicatifs eux-mêmes, [Secret Manager](#secret-manager) reste la bonne place ; Pulumi n'y crée que le secret, la valeur arrive hors du code.

## Une *project factory* en Python

```python
import pulumi
import pulumi_gcp as gcp

cfg = pulumi.Config()
org_id = cfg.require("orgId")
billing = cfg.require("billingAccount")
suffixe = cfg.require("suffixe")               # 4 caractères aléatoires, fixés une fois
env = pulumi.get_stack()                       # dev, nonprod, prod
code = {"dev": "d", "nonprod": "n", "prod": "p"}[env]

dossier = gcp.organizations.Folder(
    f"fldr-{env}",
    display_name=f"fldr-{env}",
    parent=f"organizations/{org_id}",
    opts=pulumi.ResourceOptions(protect=True),
)

gcp.orgpolicy.Policy(                          # règle propre à l'environnement
    f"lieux-{env}",
    name=dossier.name.apply(lambda n: f"{n}/policies/gcp.resourceLocations"),
    parent=dossier.name,
    spec={"rules": [{"values": {"allowed_values": ["in:europe-locations"]}}]},
)

APPLIS = {
    "facturation": ["run.googleapis.com", "sqladmin.googleapis.com"],
    "catalogue": ["run.googleapis.com", "firestore.googleapis.com"],
}
projets = {}
for appli, apis in APPLIS.items():
    projet = gcp.organizations.Project(
        f"prj-{code}-{appli}",
        project_id=f"prj-{code}-{appli}-{suffixe}",
        name=f"{appli}-{env}",
        folder_id=dossier.name,
        billing_account=billing,               # liaison au compte de facturation
        labels={"application": appli, "environment": env, "envcode": code},
        deletion_policy="PREVENT",             # valeur par défaut, écrite pour la relecture
    )
    for api in apis:
        gcp.projects.Service(
            f"{appli}-{api.split('.')[0]}",
            project=projet.project_id,
            service=api,
            disable_on_destroy=False,
        )
    projets[appli] = projet.project_id

pulumi.export("dossier", dossier.name)
pulumi.export("projets", projets)
```

- **Ce qui manque volontairement** : le rattachement au Shared VPC (`gcp.compute.SharedVPCServiceProject`), les rôles des groupes sur chaque projet (`gcp.projects.IAMMember`), un budget par projet (`gcp.billing.Budget`, voir [Facturation et budgets](#facturation-et-budgets)). Ils suivent le même modèle, dans la même boucle.
- **Au-delà de quelques projets**, la liste des applications sort du code vers un fichier YAML par équipe, relu en *pull request* par l'équipe plateforme, ou vers un composant Pulumi (`pulumi.ComponentResource`) réutilisé par chaque stack.

## Règles avant l'application

Pulumi Policies (aussi appelé CrossGuard, paquet Python `pulumi_policy`) évalue chaque ressource pendant `preview` et `up`, avant tout appel à Google Cloud. Un pack écrit en Python s'applique à des programmes écrits dans n'importe quel langage.

```python
# politiques/__main__.py — pulumi preview --policy-pack ./politiques
from pulumi_policy import EnforcementLevel, PolicyPack, ResourceValidationPolicy

def etiquettes(args, report_violation):
    if args.resource_type == "gcp:organizations/project:Project":
        manquantes = {"application", "environment"} - set(args.props.get("labels") or {})
        if manquantes:
            report_violation(f"Étiquettes manquantes : {', '.join(sorted(manquantes))}")

PolicyPack(
    name="fondations",
    enforcement_level=EnforcementLevel.MANDATORY,
    policies=[ResourceValidationPolicy(
        name="etiquettes-projet",
        description="Chaque projet porte les étiquettes de gouvernance.",
        validate=etiquettes,
    )],
)
```

Les règles de Pulumi et les règles d'administration se complètent : les premières refusent tôt, dans la *pull request*, avec un message clair ; les secondes refusent à l'API, quel que soit l'outil ou la personne.

## Pipeline

```yaml
# .github/workflows/fondations.yml (extrait) : preview sur PR, up à la fusion
on:
  pull_request:
  push: { branches: [main] }
permissions: { contents: read, id-token: write, pull-requests: write }
jobs:
  pulumi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
          service_account: sa-projets@prj-b-seed-XXXX.iam.gserviceaccount.com
      - uses: actions/setup-python@v7
        with: { python-version: "3.13" }
      - run: pip install -r requirements.txt
      - uses: pulumi/actions@v7
        with:
          command: ${{ github.event_name == 'pull_request' && 'preview' || 'up' }}
          stack-name: prod
          cloud-url: gs://BUCKET_ETAT
          policyPacks: politiques
          comment-on-pr: true
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

- **Preview sur la pull request, up à la fusion**, sur une branche protégée ; jamais de `pulumi up` depuis un poste pour les couches de la fondation. Pour la production, un environnement GitHub avec approbation obligatoire devant l'étape `up`.
- **Deux identités.** Un compte de service limité à la lecture des ressources pour les `preview`, celui qui a les droits d'écriture réservé à l'`up` de la branche principale.
- **Dérive.** Un job planifié lance `pulumi preview --refresh` avec `expect-no-changes: true` et échoue dès qu'une ressource a été modifiée hors du code.
- **Sur Google Cloud**, le même enchaînement tourne dans [Cloud Build](#cloud-build), sous le compte de service du déclencheur, sans fédération d'identité.

## Pièges

- **API activées à terme.** `gcp.projects.Service` rend la main avant que l'API soit toujours utilisable dans un projet qui vient d'être créé. Faire dépendre les ressources du service (`opts=pulumi.ResourceOptions(depends_on=[service])`), et relancer si l'erreur « API has not been used in project » persiste.
- **Propagation IAM.** Un rôle accordé est en général effectif en deux minutes, parfois sept ou plus : un `up` qui crée un compte de service, lui donne un rôle et l'utilise aussitôt peut échouer en 403 puis réussir à la relance.
- **Deux protections, deux niveaux.** `protect=True` fait refuser par Pulumi toute suppression ou remplacement de la ressource (le lever demande `pulumi state unprotect`). Les protections du fournisseur agissent en plus : `deletion_policy="PREVENT"` par défaut sur un projet, `deletion_protection=True` par défaut sur un dossier. À poser sur les dossiers, les projets hôtes, le bucket d'état et les clés KMS.
- **Renommer, c'est remplacer.** Changer le nom logique d'une ressource dans le code (le premier argument) ou un argument immuable comme `project_id` fait supprimer puis recréer la ressource. Pour un renommage dans le code, `aliases` garde le lien avec l'existant.
- **Supprimer un projet.** Avec `deletion_policy="DELETE"`, le projet part en suppression réversible pendant trente jours, compte encore dans le quota et son ID n'est jamais réutilisable. `ABANDON` le retire de l'état sans le supprimer.
- **Quotas de projets.** Le compte de service de la *project factory* crée tous les projets : c'est son quota de création, ou celui de l'organisation, qui s'épuise, ainsi que le nombre de projets liés au compte de facturation. Demander les augmentations avant d'ouvrir la *factory* aux équipes.
- **`auto_create_network=False`.** Le fournisseur laisse Google créer le réseau `default` puis le supprime, en laissant l'API Compute Engine activée. La règle d'administration `compute.skipDefaultNetworkCreation` évite sa création même.

## Alternatives en logiciel libre

- **OpenTofu** (MPL 2.0) avec **terraform-example-foundation** (Apache 2.0) : la fondation de référence de Google, en étapes numérotées (`0-bootstrap` à `5-app-infra`), à déployer telle quelle plutôt qu'à réécrire en Pulumi.
- **Cloud Foundation Fabric** et sa fondation **FAST** (Apache 2.0) : modules HCL minces et étapes d'organisation, de réseau et de *project factory* pilotées par des fichiers YAML, à cloner dans ses propres dépôts.
- **Crossplane** (Apache 2.0) : décrit la fondation en ressources Kubernetes réconciliées en continu, et offre aux équipes des « projets » maison par ses compositions.
- **SOPS** (MPL 2.0) : chiffre des fichiers de configuration YAML ou JSON avec une clé Cloud KMS, pour versionner les secrets d'une IaC qui n'a pas de fournisseur de secrets intégré.
- **Open Policy Agent** et **Conftest** (Apache 2.0) : règles Rego évaluées sur la sortie JSON d'un plan ou d'un `preview`, là où Pulumi Policies utilise Python.
