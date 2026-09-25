---
title: La chaîne CI/CD sur Google Cloud
---

Du commit à la production, la chaîne native de Google Cloud répartit le travail entre des services spécialisés. [Cloud Build](#cloud-build) construit et teste, [Artifact Registry](#artifact-registry) stocke l'image, [Artifact Analysis](#artifact-analysis) l'analyse, [Cloud Deploy](#cloud-deploy) la promeut d'environnement en environnement et [Binary Authorization](#binary-authorization) refuse au déploiement ce qui n'est pas passé par la chaîne. Deux choix structurent tout le reste : **qui fait l'intégration continue** (Cloud Build ou la forge) et **comment les projets sont découpés** entre environnements.

![Chaîne CI/CD de référence, du dépôt Git à la production](../../svg/chaine-cicd.svg)

Un *push* ou une *pull request* sur le dépôt déclenche un build. Cloud Build lit ses identifiants dans [Secret Manager](#secret-manager), lance les tests, construit l'image et la pousse dans Artifact Registry, qui l'analyse à la réception. La dernière étape du build crée une *release* Cloud Deploy : un instantané des manifestes rendus pour chaque cible, où l'image est désignée par son [*digest*](#lexterm-digest). Cloud Deploy déploie cette même image en dev, puis la promeut vers staging et prod. Tous les services écrivent leurs journaux dans [Cloud Logging](#cloud-logging).

## Qui fait quoi

| Étape | Service | Ce qu'il fait | Ce qu'il ne fait pas |
|---|---|---|---|
| Connexion au dépôt | [Developer Connect](#developer-connect) ou dépôts Cloud Build de 2ᵉ génération | Relie GitHub, GitLab ou Bitbucket au projet, pose le webhook | Héberger le code (c'est [Secure Source Manager](#secure-source-manager)) |
| Intégration continue | **Cloud Build** | Étapes en conteneurs : tests, analyse, build, push ; déclencheurs sur *push*, *tag*, PR | Enchaîner des environnements, promouvoir, revenir en arrière |
| Stockage | **Artifact Registry** | Images et paquets par dépôt régional, droits IAM par dépôt, règles de nettoyage | Décider ce qui peut être déployé |
| Analyse | **Artifact Analysis** | Vulnérabilités à la poussée puis en continu, SBOM, provenance, attestations | Auditer le code maison ou la configuration |
| Livraison continue | **Cloud Deploy** | Pipeline de cibles, promotion, approbation, canary, vérification, retour arrière | Construire l'image, réconcilier en continu un dépôt Git (*GitOps*) |
| Contrôle d'admission | **Binary Authorization** | Refuse sur GKE ou Cloud Run une image sans les attestations exigées | Juger le contenu du manifeste (privilèges, ressources) |
| Secrets | **Secret Manager** | Jetons de forge, mots de passe de registre, secrets d'application par environnement | Chiffrer des données (c'est [Cloud KMS](#cloud-kms)) |
| Exécution | [Cloud Run](#cloud-run), [GKE](#gke) | Font tourner l'image ; Cloud Run résout un tag en *digest* à la création de chaque révision | — |

Le détail de chaque maillon est dans [Cloud Build : builds, déclencheurs, pools privés](#cloud-build-builds), [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer) et [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Chaîne native ou forge et Google Cloud

La forge (GitHub, GitLab) sait aussi faire l'intégration continue et déployer sur Google Cloud. Les deux s'assemblent : l'intégration continue peut rester dans la forge et la livraison passer par Cloud Deploy, qui ne demande qu'un appel `gcloud deploy releases create` en fin de job.

| Critère | Cloud Build + Cloud Deploy | GitHub Actions ou GitLab CI vers Google Cloud |
|---|---|---|
| Identité vers Google Cloud | Compte de service du build, sans clé ni fédération | [Workload Identity Federation](#workload-identity-federation) : jeton OIDC du job échangé contre un jeton Google (voir [Déployer sans clé](#deployer-sans-cle)) |
| Accès à un réseau privé | Pool privé appairé au VPC, VPC Service Controls | *Runner* auto-hébergé dans le VPC, à exploiter |
| Environnements successifs | Cibles, promotion, approbation, canary, retour arrière en une commande | Environnements et règles de protection de la forge ; canary et retour arrière à écrire |
| Chaîne logicielle | Provenance SLSA niveau 3 signée, lue par Binary Authorization | Attestations de la forge, à relier soi-même à Binary Authorization |
| Revue et visibilité | Statut du build renvoyé sur la PR, journaux dans la console Google Cloud | Tout dans l'interface de la forge, à côté du code et de la revue |
| Écosystème | Builders officiels et images publiques | Catalogue d'actions et de composants, matrices de jobs |
| Coût | Minutes de build, dont 2 500 gratuites par mois sur `e2-standard-2` ; 5 $ par pipeline Cloud Deploy multicible actif au-delà du premier | Minutes de *runner* de la forge, ou machines auto-hébergées |

- **Tout Google Cloud** quand les builds doivent atteindre des ressources privées, rester dans un périmètre VPC Service Controls, ou produire une provenance exigée par Binary Authorization.
- **La forge pour l'intégration continue, Cloud Deploy pour la livraison** quand l'équipe vit dans GitHub ou GitLab mais doit enchaîner plusieurs environnements avec approbation et canary. GitHub Actions dispose des actions `google-github-actions/auth` et `create-cloud-deploy-release`, GitLab.com de composants CI/CD Google (Artifact Registry, Cloud Run, Cloud Deploy).
- **La forge seule** pour un service unique déployé sur un seul environnement : une étape `gcloud run deploy` après l'authentification fédérée suffit.

## Environnements et projets

Le découpage le plus sûr isole chaque environnement dans son **propre projet** et regroupe l'outillage dans un projet CI/CD :

- **Projet CI/CD** : déclencheurs et pools Cloud Build, dépôt Artifact Registry, pipeline et cibles Cloud Deploy. Les cibles doivent vivre dans le projet et la région du pipeline, mais désignent des services ou des clusters dans d'autres projets.
- **Un projet par environnement** (dev, staging, prod) : services Cloud Run ou clusters GKE, secrets d'exécution, bases de données. Les droits de prod ne sont accordés qu'au compte de service qui déploie en prod.
- **Une image, promue.** La même image, désignée par son *digest*, passe de dev à prod ; seule la configuration change, par profils Skaffold ou paramètres de déploiement. Reconstruire pour la prod ferait déployer un artefact qui n'a pas été testé.
- **Un compte de service d'exécution par cible**, déclaré dans `executionConfigs` : celui de dev n'a aucun rôle dans le projet de prod.

Chaque projet d'exécution doit pouvoir tirer l'image du dépôt central : l'agent de service Cloud Run du projet reçoit le rôle de lecteur sur le dépôt.

```bash
gcloud artifacts repositories add-iam-policy-binding REPOSITORY \
  --project=CICD_PROJECT_ID --location=REGION \
  --member=serviceAccount:service-PROD_PROJECT_NUMBER@serverless-robot-prod.iam.gserviceaccount.com \
  --role=roles/artifactregistry.reader
```

## Pièges

- **Laisser tourner les builds sous le compte de service par défaut.** Selon l'ancienneté du projet et les règles d'administration, c'est le compte de service Compute Engine par défaut ou le compte de service Cloud Build hérité, tous deux très larges. Créer un compte par déclencheur, avec les seuls rôles utiles.
- **Déployer par tag mouvant.** `:latest` ne dit pas ce qui tourne en prod, et Binary Authorization ne juge qu'un *digest* : passer l'image `@sha256:...` à Cloud Deploy.
- **Construire une image par environnement.** Le test en staging ne vaut plus rien pour la prod. Construire une fois, promouvoir le même *digest*.
- **Mettre dev et prod dans le même projet.** Un rôle accordé au projet pour dev ouvre aussi la prod, et les quotas sont partagés.
- **Enchaîner les environnements dans `cloudbuild.yaml`.** Trois étapes `gcloud run deploy` n'offrent ni approbation, ni trace par environnement, ni retour arrière : c'est le rôle de Cloud Deploy.
- **Oublier le nettoyage d'Artifact Registry.** Chaque commit dépose une image, facturée au stockage et, si l'analyse est activée, à l'analyse.

## Alternatives en logiciel libre

- **GitLab CE** (MIT) : forge, intégration continue, registre d'images et environnements dans un seul logiciel, avec des *runners* à exploiter soi-même ; les approbations de déploiement et les règles de protection les plus fines relèvent de l'édition Enterprise, qui n'est pas libre.
- **Forgejo** (GPL v3+) et **Gitea** (MIT) : forges légères avec un moteur d'actions dont la syntaxe suit celle de GitHub Actions ; la livraison entre environnements reste à construire à côté.
- **Jenkins** (MIT) : serveur d'automatisation extensible par greffons, qui couvre intégration et livraison dans un même `Jenkinsfile` ; contrôleur, agents et greffons sont à maintenir.
- **Tekton** (Apache 2.0) : pipelines Kubernetes où chaque étape est un conteneur, le modèle le plus proche de Cloud Build.
- **Argo CD** et **Flux** (Apache 2.0) : livraison GitOps, où le cluster se rapproche en continu d'un dépôt de manifestes, là où Cloud Deploy pousse une *release* figée cible par cible.
- **Harbor** (Apache 2.0) : registre d'images avec analyse de vulnérabilités et signature, face au couple Artifact Registry et Artifact Analysis.
- **Kyverno** (Apache 2.0) avec **Sigstore** `cosign` (Apache 2.0) : vérification des signatures et des attestations à l'admission dans le cluster, le rôle de Binary Authorization, limité à Kubernetes.
