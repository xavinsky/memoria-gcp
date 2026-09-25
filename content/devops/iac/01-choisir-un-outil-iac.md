---
title: Choisir un outil d'Infrastructure as Code
---

L'outil se choisit d'abord sur **la manière dont l'équipe écrit déjà** : du HCL et des modules Terraform, un langage généraliste (Python, TypeScript, Go), ou des manifestes Kubernetes appliqués par un opérateur [GitOps](#lexterm-gitops). La question suivante est **qui exécute** : sa propre chaîne CI, un service géré par Google, ou un contrôleur qui réconcilie en continu. Le script `gcloud` reste l'outil de l'amorçage et du ponctuel, pas d'une infrastructure qui vit.

> [!TIP]
> Pour un nouveau projet, ce site recommande **Pulumi en Python** : licence libre (Apache 2.0), même langage que le reste du code, même couverture que Terraform puisque le fournisseur `pulumi_gcp` est construit sur le fournisseur Terraform `google-beta`. Terraform ou OpenTofu restent le bon choix pour reprendre une base HCL existante ou les modules de Google (Cloud Foundation Toolkit, Fabric). Les fondations d'une organisation en Pulumi sont décrites dans [Construire les fondations en code](#fondations-en-code).

![Arbre de décision : de la manière d'écrire à l'outil d'IaC](../../svg/choix-outil-iac.svg)

## Matrice de choix

| Outil | Langage | État | Dérive | GitOps | Exécution | Licence |
|---|---|---|---|---|---|---|
| **Terraform** (fournisseurs `google` et `google-beta`) | HCL, modules du registre | Fichier d'état, backend `gcs` verrouillé | Détectée au `plan` (`-refresh-only`), corrigée au prochain `apply` | Par la CI : `plan` sur la *pull request*, `apply` à la fusion | Soi-même : poste, [Cloud Build](#cloud-build), GitHub Actions, HCP Terraform | BSL 1.1 (source disponible, pas libre) ; fournisseurs en MPL-2.0 |
| **OpenTofu** | HCL, mêmes fournisseurs et modules | Idem, plus chiffrement natif de l'état (clé Cloud KMS possible) | Idem | Idem | Soi-même | MPL-2.0, Linux Foundation, projet *sandbox* de la CNCF |
| **[Infrastructure Manager](#infrastructure-manager)** | HCL, Terraform ≤ 1.5.7 | Géré par Google, une révision par application | Visible dans une prévisualisation | Déclencheurs Cloud Build : prévisualisation sur PR, déploiement à la fusion | Google, dans un job Cloud Build éphémère, sous un compte de service | Service gratuit ; Cloud Build et Cloud Storage facturés |
| **Pulumi** (fournisseur `gcp`) | Python, TypeScript, Go, C#, Java, YAML | Pulumi Cloud ou backend DIY (`gs://BUCKET`) | `pulumi refresh`, `pulumi preview --refresh` | Par la CI, ou Pulumi Deployments (service de Pulumi Cloud) | Soi-même ou Pulumi Cloud | Apache 2.0 (moteur et fournisseurs) |
| **[Config Connector](#config-connector)** | Manifestes YAML (KRM), `kubectl` | Dans le cluster : `spec` voulu, `status` relu | **Corrigée en continu** par le contrôleur | Natif : Config Sync, Argo CD, Flux | Contrôleur dans un cluster [GKE](#gke) | Apache 2.0 ; cluster facturé |
| **Config Controller** (`gcloud anthos config controller`) | Idem | Idem | Idem | Config Sync et Policy Controller inclus | Plan de contrôle hébergé et mis à jour par Google | Cluster GKE de l'instance facturé |
| **Script `gcloud`** | Bash, commandes impératives | Aucun | Aucune détection | Non | Soi-même | — |

- **Un seul moteur sous deux interfaces.** Le fournisseur Pulumi `gcp` est construit (*bridged*) à partir du fournisseur Terraform `google-beta` : la couverture des ressources et leurs arguments sont les mêmes. Infrastructure Manager exécute Terraform lui-même. Choisir entre les trois revient à choisir un langage et un mode d'exécution, pas une couverture.
- **Réconciliation ou application ponctuelle.** Terraform, OpenTofu, Pulumi et Infrastructure Manager n'agissent que quand on les lance ; une modification faite dans la console reste en place jusqu'au prochain `apply`. Config Connector rapproche l'état réel de l'état déclaré à chaque cycle, sans intervention.
- [!DECONSEILLE] **[Cloud Deployment Manager](#cloud-deployment-manager)** n'entre pas dans le choix : il est fermé aux nouveaux utilisateurs, et les clients existants y ont accès jusqu'au 30 juin 2027, date de son arrêt. Ses configurations YAML et ses modèles Jinja ou Python se portent en HCL vers Infrastructure Manager ; les ressources déjà créées continuent de fonctionner et se réimportent dans un état Terraform (voir [Terraform sur Google Cloud](#terraform-sur-gcp)).

## Questions qui départagent

- **Terraform ou OpenTofu ?** Les deux lisent le même HCL et utilisent le même fournisseur `google`, publié en MPL-2.0. Terraform est sous Business Source License depuis sa version 1.6.0 : usage en production permis, sauf pour proposer un service concurrent des offres payantes d'IBM (propriétaire de HashiCorp). OpenTofu est libre et chiffre nativement l'état et les plans. Une équipe qui dépend de HCP Terraform reste sur Terraform ; une équipe qui veut un outil libre ou le chiffrement de l'état passe à OpenTofu.
- **Infrastructure Manager ou Terraform dans sa CI ?** Infrastructure Manager supprime le bucket d'état, les verrous et les *runners* à maintenir, et concentre le droit d'appliquer sur un compte de service. En contrepartie : Terraform limité à la version 1.5.7 (pas d'arguments *write-only*, qui demandent la 1.11), pas de bloc `backend`, pas de génération de code Terraform, pas d'espaces de travail multiples. Une chaîne qui repose sur une version récente de Terraform, sur OpenTofu ou sur Terragrunt reste dans sa propre CI.
- **Pulumi ou Terraform ?** Pulumi par défaut, et en particulier quand l'infrastructure est écrite par des développeurs qui veulent des boucles, des fonctions, des tests unitaires et les paquets de leur langage, ou quand l'infrastructure se crée depuis une application (Automation API). Terraform quand l'équipe est une équipe plateforme habituée au HCL, ou quand elle veut réutiliser les modules de Google (Cloud Foundation Toolkit, Fabric). En Python, le paquet est `pulumi_gcp`.
- **Config Connector ou Terraform ?** Config Connector quand Kubernetes est déjà l'outil de travail de l'équipe et que la correction automatique des dérives compte. Il ne sait pas créer le cluster qui l'héberge : un premier cluster, ou Config Controller, doit exister avant lui. Sans cluster, faire tourner un plan de contrôle pour créer des buckets coûte plus cher qu'Infrastructure Manager.
- **Quand un script `gcloud` suffit ?** Pour l'amorçage (créer le projet d'administration, le bucket d'état, le compte de service de la CI), un environnement jetable ou une opération ponctuelle. Dès qu'il faut mettre à jour, supprimer proprement ou reproduire un environnement, l'absence d'état oblige à réécrire à la main la logique d'idempotence.

```python
# Pulumi en Python : un bucket, état dans Cloud Storage (pulumi login gs://BUCKET)
import pulumi
import pulumi_gcp as gcp

bucket = gcp.storage.Bucket(
    "donnees",
    location="EU",
    uniform_bucket_level_access=True,
    public_access_prevention="enforced",
)
pulumi.export("bucket_url", bucket.url)
```

## Pièges

- **Deux outils sur la même ressource.** Une ressource gérée à la fois par Terraform et par Config Connector, ou par Terraform et à la main, oscille entre deux états voulus. Fixer une règle par couche : par exemple Terraform pour l'organisation, les projets et le réseau, Config Connector pour les ressources propres aux applications.
- [!DECONSEILLE] **Le fournisseur Pulumi `google-native`.** Il est sans maintenance et son dépôt est archivé ; Pulumi indique d'utiliser le fournisseur `gcp`, pour les nouveaux projets comme pour les existants.
- [!DECONSEILLE] **CDK for Terraform.** HashiCorp le déclare obsolète, sans maintenance ni support, bien que la page IaC de Google le cite. Pour écrire en Python, prendre Pulumi.
- **Choisir sur la couverture.** Tous les outils déclaratifs suivent l'API de Google avec un décalage, et les ressources récentes arrivent d'abord dans `google-beta`. Vérifier que les ressources visées existent dans le fournisseur, ou comme CRD dans la version installée de Config Connector, avant d'écrire une ligne.
- [!DECONSEILLE] **L'add-on Config Connector de GKE.** Il n'existe que sur GKE Standard et accuse souvent douze mois de retard sur la version courante ; l'installation manuelle de l'opérateur est la voie recommandée.
- **Supprimer un déploiement Deployment Manager pour « nettoyer ».** La suppression emporte toutes les ressources du manifeste. Pour une migration, importer d'abord les ressources dans l'état du nouvel outil, puis supprimer le déploiement hérité avec `--delete-policy=abandon`, qui retire les ressources du manifeste sans les détruire.

## Alternatives en logiciel libre

- **OpenTofu** (MPL 2.0) et **Pulumi** (Apache 2.0 pour le moteur et le fournisseur `gcp`), déjà comparés plus haut ; Config Connector est lui-même publié sous Apache 2.0. Terraform, sous BSL, n'est pas libre.
- **Crossplane** (Apache 2.0) : même réconciliation continue que Config Connector, pour plusieurs fournisseurs à la fois, avec des compositions qui exposent aux équipes des ressources maison.
- **Ansible** (GPL v3) et sa collection `google.cloud` : approche procédurale sans fichier d'état, adaptée quand la configuration des machines compte autant que la création des ressources ; la dérive n'est pas détectée.
- **Terragrunt** (MIT) : couche au-dessus d'OpenTofu ou Terraform pour factoriser backends, fournisseurs et variables entre environnements et piloter les dépendances entre états.
- **Terramate** (MPL 2.0) : découpage en *stacks*, génération de code et exécution des seules *stacks* modifiées, pour les dépôts OpenTofu à nombreux états.
