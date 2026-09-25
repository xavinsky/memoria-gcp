---
title: Déployer depuis GitHub Actions ou GitLab CI sans clé
---

Un pipeline qui tourne hors de Google Cloud n'a besoin d'aucune clé de compte de service. GitHub Actions et GitLab CI délivrent à chaque job un [jeton OIDC](#lexterm-oidc-openid-connect) signé qui dit quel dépôt, quelle branche et quel environnement l'exécutent ; la [fédération d'identité de charge de travail](#workload-identity-federation) l'échange contre un jeton Google de courte durée. Rien à stocker dans la forge, rien à faire tourner, et un droit qui se restreint à un dépôt, une branche ou un environnement précis. La clé JSON décrite dans [Authentifier un appel à une API](#authentifier-un-appel) n'a pas sa place dans une CI.

![Échange du jeton OIDC contre un jeton Google Cloud](../../svg/echange-jeton-wif.svg)

1. Le job demande un [JWT](#lexterm-jwt-json-web-token) à l'émetteur de sa plateforme (`https://token.actions.githubusercontent.com`, `https://gitlab.com`) ; le jeton vit quelques minutes.
2. Il le présente au **Security Token Service** avec l'audience du fournisseur. STS vérifie la signature, applique les **mappages d'attributs**, puis la **condition d'attribut** : si elle est fausse, le jeton est rejeté.
3. STS rend un **jeton fédéré**, qui porte l'identité du principal fédéré. Pour les API qui l'acceptent, il suffit : c'est l'**accès direct**.
4. Sinon, le jeton fédéré sert à [emprunter](#lexterm-emprunt-d-identite-impersonation) un compte de service auprès d'IAM Credentials, qui rend un jeton d'accès OAuth 2.0 d'une heure par défaut.

## Accès direct ou compte de service

| | Accès direct | Emprunt d'un compte de service |
|---|---|---|
| Qui reçoit les rôles | Le principal fédéré : `principal://…/subject/SUJET` ou `principalSet://…/attribute.NOM/VALEUR` | Le compte de service ; le principal fédéré reçoit `roles/iam.workloadIdentityUser` sur ce compte |
| Jeton obtenu | Jeton fédéré | Jeton d'accès du compte, ou jeton d'identité |
| Limites | Quelques API refusent les principaux fédérés, dont **Cloud Run** | Aucune ; un compte de plus à gérer |
| Action GitHub `auth` | Sans `service_account` | Avec `service_account` |

Google recommande l'accès direct. Il convient à la poussée dans [Artifact Registry](#artifact-registry), à la lecture d'un secret ou d'un bucket. Le déploiement sur [Cloud Run](#cloud-run) passe, lui, par un compte de service : c'est ce que montrent les exemples ci-dessous.

## Pool et fournisseur

Dans un projet dédié à l'administration des identités, un pool par organisation GitHub ou par groupe GitLab, et un fournisseur OIDC qui n'admet que les jetons de cette organisation. Les API IAM, Resource Manager, Service Account Credentials et Security Token Service doivent être activées.

```bash
gcloud iam workload-identity-pools create github --project=PROJECT_ID \
  --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github-org --project=PROJECT_ID \
  --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner_id == 'OWNER_ID'"

# Compte de déploiement, empruntable par le seul environnement production d'un dépôt
gcloud iam service-accounts create deployer --project=PROJECT_ID
gcloud iam service-accounts add-iam-policy-binding deployer@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/subject/repo:ORG/REPO:environment:production"

# Droits du compte : pousser l'image, déployer, agir en tant que compte d'exécution du service
gcloud artifacts repositories add-iam-policy-binding REPOSITORY --location=REGION \
  --role=roles/artifactregistry.writer --member=serviceAccount:deployer@PROJECT_ID.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding PROJECT_ID \
  --role=roles/run.developer --member=serviceAccount:deployer@PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts add-iam-policy-binding app-runtime@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.serviceAccountUser --member=serviceAccount:deployer@PROJECT_ID.iam.gserviceaccount.com
```

- **Identifiants numériques.** `repository_owner_id` et `repository_id` ne sont jamais réattribués ; un nom d'organisation ou de dépôt supprimé peut être repris par un tiers, qui hériterait de la confiance. `gh api /orgs/ORG --jq .id` donne l'identifiant d'une organisation.
- **Format du `sub`.** Il vaut `repo:ORG/REPO:environment:NOM` pour un job attaché à un environnement, `repo:ORG/REPO:ref:refs/heads/BRANCHE` sinon, `repo:ORG/REPO:pull_request` pour une *pull request*. Un dépôt créé, renommé ou transféré après le 15 juillet 2026, ou qui a activé l'option, utilise le format immuable `repo:ORG@OWNER_ID/REPO@REPO_ID:…` : la liaison doit reprendre exactement ce format.
- **Accès direct.** La même liaison sans compte de service s'écrit sur la ressource, par exemple `--member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository_id/REPO_ID"` avec `roles/artifactregistry.writer` sur le dépôt d'images. Les identifiants de principal prennent le **numéro** du projet, pas son ID.

## Workflow GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production          # sub = repo:ORG/REPO:environment:production
    permissions:
      contents: read
      id-token: write                # autorise la demande du jeton OIDC
    env:
      IMAGE: REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/app:${{ github.sha }}
    steps:
      - uses: actions/checkout@v7    # avant auth : le fichier d'identifiants va dans l'espace de travail
      - uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github-org
          service_account: deployer@PROJECT_ID.iam.gserviceaccount.com
      - uses: google-github-actions/setup-gcloud@v3
      - run: |
          gcloud auth configure-docker REGION-docker.pkg.dev --quiet
          docker build -t "$IMAGE" . && docker push "$IMAGE"
      - uses: google-github-actions/deploy-cloudrun@v3
        with:
          service: app
          region: REGION
          image: ${{ env.IMAGE }}
          flags: --service-account=app-runtime@PROJECT_ID.iam.gserviceaccount.com
```

L'action `auth` écrit un fichier de configuration d'identifiants (`type: external_account`) et exporte `GOOGLE_APPLICATION_CREDENTIALS` et `CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE` : `gcloud`, les bibliothèques clientes et Terraform s'en servent sans autre réglage, et le fichier est supprimé en fin de job. `token_format: access_token` produit en plus un jeton explicite pour un outil qui n'accepte qu'un *bearer*, ce qui exige `service_account`.

> [!TIP]
> Une image construite par `docker build` dans GitHub n'a pas de provenance Cloud Build : une règle [Binary Authorization](#binary-authorization) qui exige l'attestor `built-by-cloud-build` la refuse. Pour garder cette chaîne de confiance, le job lance le build dans Cloud Build (`gcloud builds submit`) ou se limite au déploiement d'une image produite par un déclencheur Cloud Build (voir [Sécuriser la chaîne logicielle](#securiser-la-chaine)).

## GitLab CI

Le fournisseur reprend les identifiants stables de GitLab : `namespace_id` pour le groupe, `project_id` pour le projet, `ref_protected` pour une branche protégée. Le `sub` vaut `project_path:GROUPE/PROJET:ref_type:branch:ref:main`.

```bash
gcloud iam workload-identity-pools providers create-oidc gitlab-group --project=PROJECT_ID \
  --location=global --workload-identity-pool=gitlab --issuer-uri="https://gitlab.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.project_id=assertion.project_id,attribute.namespace_id=assertion.namespace_id,attribute.ref_protected=assertion.ref_protected" \
  --attribute-condition="assertion.namespace_id == 'GROUP_ID'"
gcloud iam service-accounts add-iam-policy-binding deployer@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab/subject/project_path:GROUPE/PROJET:ref_type:branch:ref:main"
```

```yaml
# .gitlab-ci.yml : déployer une image déjà construite par Cloud Build
deploy:
  image: gcr.io/google.com/cloudsdktool/google-cloud-cli:stable
  environment: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  id_tokens:
    GCP_ID_TOKEN:
      aud: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab/providers/gitlab-group
  script:
    - echo "$GCP_ID_TOKEN" > "$CI_PROJECT_DIR/.ci_id_token"
    - >-
      gcloud iam workload-identity-pools create-cred-config
      projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab/providers/gitlab-group
      --service-account=deployer@PROJECT_ID.iam.gserviceaccount.com
      --credential-source-file="$CI_PROJECT_DIR/.ci_id_token"
      --output-file="$CI_PROJECT_DIR/.gcp_credentials.json"
    - gcloud auth login --cred-file="$CI_PROJECT_DIR/.gcp_credentials.json"
    - >-
      gcloud run deploy app --project=PROJECT_ID --region=REGION
      --image=REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/app:$CI_COMMIT_SHA
      --service-account=app-runtime@PROJECT_ID.iam.gserviceaccount.com
```

L'audience du jeton (`aud`) doit être l'une de celles qu'accepte le fournisseur ; par défaut, c'est l'URL du fournisseur ci-dessus. Pour une instance GitLab auto-hébergée, l'émetteur est l'URL de l'instance ; si Google ne peut pas y lire les clés publiques, on les téléverse avec `--jwk-json-path`.

## Sécurité

- **Condition d'attribut obligatoire.** GitHub et GitLab.com n'ont qu'un émetteur pour tous leurs clients : un fournisseur sans condition accepte le jeton de n'importe quel dépôt public. La condition porte sur un identifiant numérique (`repository_owner_id`, `namespace_id`), le mappage seul ne filtre rien.
- **Lier au plus étroit.** Un compte de production empruntable par un seul `sub` (environnement `production`, ou branche `main`), jamais par tout le pool (`principalSet://…/workloadIdentityPools/POOL_ID/*`).
- **Protéger l'environnement côté forge.** Sur GitHub, des règles de protection d'environnement (branches autorisées, relecteurs requis) décident qui peut obtenir un `sub` en `environment:production` ; sur GitLab, branches et environnements protégés, que `ref_protected` et `environment_protected` reflètent dans le jeton.
- **Un compte par environnement.** Développement, préproduction et production ont chacun leur compte de service et leurs rôles ; un job de *pull request* n'en emprunte aucun qui puisse déployer.
- **Aucune clé.** Une fois les pipelines migrés, la contrainte d'organisation `iam.disableServiceAccountKeyCreation` empêche d'en recréer.

## Pièges

- **`id-token: write` absent.** L'action `auth` échoue faute de jeton. Déclarer `permissions` au niveau du job retire aussi les droits par défaut : garder `contents: read` pour `actions/checkout`.
- **Attribut non mappé.** Une condition ou une liaison qui cite `attribute.ref` sans mappage correspondant ne correspond jamais : tout attribut utilisé doit être déclaré dans `--attribute-mapping`.
- **Propagation.** Un pool, un fournisseur ou une liaison IAM tout juste créés peuvent mettre jusqu'à cinq minutes à être pris en compte : une erreur immédiate ne prouve pas une configuration fausse.
- **ID au lieu du numéro de projet** dans `workload_identity_provider` ou dans un identifiant `principal://` : l'échange échoue.
- **Accès direct sur Cloud Run.** Accorder `roles/run.developer` au principal fédéré ne suffit pas : Cloud Run ne gère pas l'accès direct, il faut emprunter un compte de service.
- **Oubli du compte d'exécution.** Déployer un service exige `roles/iam.serviceAccountUser` sur le compte sous lequel il tourne ; sans option `--service-account`, c'est le compte Compute Engine par défaut, souvent trop large.
- **Identifiants figés à la création.** Les ID de pool et de fournisseur ne se changent pas, et le préfixe `gcp-` est réservé. `google.subject` ne dépasse pas 127 caractères.

## Alternatives en logiciel libre

La fédération d'identité de charge de travail est propre à Google Cloud ; les projets ci-dessous reprennent le même mécanisme — un jeton OIDC signé, échangé contre un accès de courte durée — hors de Google Cloud.

- **OpenBao** (MPL 2.0) : sa méthode d'authentification JWT/OIDC valide le jeton d'un job GitHub Actions ou GitLab CI, avec des conditions sur ses revendications (dépôt, branche, environnement), puis délivre un jeton et des secrets à durée limitée ; le pendant du couple pool et fournisseur.
- **SPIFFE** et **SPIRE** (Apache 2.0) : identité de charge de travail attestée par la plateforme, délivrée en certificat X.509 ou en JWT ; le fournisseur de découverte OIDC de SPIRE permet de fédérer ces JWT auprès d'un fournisseur cloud, Google Cloud compris.
- **Keycloak** (Apache 2.0) : fournisseur d'identité qui fédère des fournisseurs OIDC externes et implémente l'échange de jetons (RFC 8693), le protocole du Security Token Service ; plus lourd, pensé d'abord pour les utilisateurs.
- **Dex** (Apache 2.0) : fournisseur OIDC fédérateur plus léger, qui délivre des jetons à des applications et des clusters Kubernetes à partir d'identités amont.
- **Sigstore Fulcio** (Apache 2.0) : même jeton OIDC de job, échangé contre un certificat de signature de quelques minutes ; l'usage le plus répandu de ce mécanisme dans les chaînes CI libres.
