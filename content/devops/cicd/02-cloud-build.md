---
title: "Cloud Build : builds, déclencheurs, pools privés"
id: cloud-build-builds
---

[Cloud Build](#cloud-build) exécute une suite d'étapes, chacune dans un conteneur, sur une machine créée pour le build. Trois décisions pèsent sur un projet : **ce que dit le fichier de build** (étapes, secrets, artefacts), **qui déclenche et sous quelle identité**, et **où le build tourne** : pool par défaut, ouvert sur internet, ou pool privé dans le réseau de l'entreprise.

## Anatomie de `cloudbuild.yaml`

| Champ | Rôle |
|---|---|
| `steps` | Étapes exécutées dans l'ordre ; chacune donne une image (`name`) et des `args`, ou un `script`. `id` et `waitFor` créent du parallélisme ; `allowFailure` et `allowExitCodes` tolèrent un échec |
| `images` | Images Docker poussées vers Artifact Registry **après** la dernière étape ; une image listée mais non produite fait échouer le build |
| `artifacts` | Fichiers vers Cloud Storage (`objects`) ou paquets vers Artifact Registry (`mavenArtifacts`, `pythonPackages`, `npmPackages`, `goModules`) |
| `substitutions` | Variables maison, préfixées d'un tiret bas (`_REGION`), à côté des variables fournies : `$PROJECT_ID`, `$BUILD_ID`, `$COMMIT_SHA`, `$SHORT_SHA`, `$BRANCH_NAME`, `$TAG_NAME` |
| `availableSecrets` | Versions de secrets [Secret Manager](#secret-manager) exposées en variables d'environnement aux seules étapes qui les listent dans `secretEnv` |
| `serviceAccount` | Compte de service du build lancé à la main ; un déclencheur impose le sien |
| `options` | `machineType`, `diskSizeGb` (jusqu'à 4 000 Go), `logging`, `pool`, `automapSubstitutions`, `dynamicSubstitutions`, `requestedVerifyOption` |
| `timeout`, `queueTtl` | Durée maximale du build (60 minutes par défaut, 24 heures au plus) et de son attente en file |

Build d'une image, tests compris, puis création d'une release [Cloud Deploy](#cloud-deploy-livrer) avec l'image désignée par son *digest* :

```yaml
steps:
- id: tests
  name: python:3.12-slim
  script: |
    pip install -r requirements.txt
    python -m pytest
- id: image
  name: gcr.io/cloud-builders/docker
  script: |
    docker pull "$_IMAGE:latest" || true
    docker build --cache-from "$_IMAGE:latest" --build-arg BUILDKIT_INLINE_CACHE=1 \
      -t "$_IMAGE:$SHORT_SHA" -t "$_IMAGE:latest" .
    docker push --all-tags "$_IMAGE"
    docker inspect --format='{{index .RepoDigests 0}}' "$_IMAGE:$SHORT_SHA" > /workspace/image.txt
- id: release
  name: gcr.io/google.com/cloudsdktool/cloud-sdk
  script: |
    gcloud deploy releases create "rel-$SHORT_SHA" \
      --delivery-pipeline=web --region="$_REGION" \
      --images="web=$(cat /workspace/image.txt)"
images: ['${_IMAGE}:${SHORT_SHA}']   # résultats du build et provenance
substitutions:
  _REGION: europe-west1
  _IMAGE: ${_REGION}-docker.pkg.dev/${PROJECT_ID}/app/web
serviceAccount: projects/PROJECT_ID/serviceAccounts/build-web@PROJECT_ID.iam.gserviceaccount.com
options:
  automapSubstitutions: true   # substitutions visibles comme variables dans les scripts
  dynamicSubstitutions: true   # _IMAGE référence _REGION et PROJECT_ID
  logging: CLOUD_LOGGING_ONLY
  machineType: E2_HIGHCPU_8
```

Les étapes partagent `/workspace` : c'est par un fichier que le *digest* passe d'une étape à l'autre. L'image est poussée par `docker push` dans une étape, parce que le champ `images` ne pousse qu'une fois toutes les étapes terminées ; elle reste listée dans `images` pour figurer dans les résultats du build et dans sa provenance. Pour un secret, la syntaxe est plus contrainte : il n'est lisible que dans `args`, par un `bash -c` et une variable doublée `$$` que Cloud Build ne remplace pas.

```yaml
- name: gcr.io/cloud-builders/docker
  entrypoint: bash
  args: ['-c', 'docker login --username=$$REG_USER --password=$$REG_PASSWORD registry.example.com']
  secretEnv: ['REG_USER', 'REG_PASSWORD']
availableSecrets:
  secretManager:
  - versionName: projects/PROJECT_ID/secrets/reg-user/versions/latest
    env: REG_USER
  - versionName: projects/PROJECT_ID/secrets/reg-password/versions/latest
    env: REG_PASSWORD
```

Le compte de service du build doit avoir `roles/secretmanager.secretAccessor` sur ces secrets.

## Déclencheurs

| Événement | Usage type | Dépôt requis |
|---|---|---|
| *Push* sur une branche (`--branch-pattern`, expression RE2) | Build et déploiement en dev à chaque fusion | Developer Connect ou 2ᵉ génération |
| *Push* d'un tag (`--tag-pattern`) | Version publiée, image étiquetée | Developer Connect ou 2ᵉ génération |
| *Pull request* (`--pull-request-pattern`, sur la branche cible) | Tests et analyse avant fusion | Developer Connect ou 2ᵉ génération |
| Manuel | Relance, tâche d'exploitation | 2ᵉ génération |
| Message Pub/Sub | Build sur un événement Google Cloud, par exemple une nouvelle image de base | 2ᵉ génération |
| Webhook entrant | Forge ou outil non pris en charge | 2ᵉ génération |

Un déclencheur filtre aussi par chemins (`--included-files`, `--ignored-files`), utile dans un *monorepo*. Sur une PR GitHub, `--comment-control` exige qu'un propriétaire ou un collaborateur du dépôt commente `/gcbrun` avant le build : pour toute PR (`COMMENTS_ENABLED`, la valeur par défaut) ou pour les seuls contributeurs externes (`COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY`). C'est ce qui empêche une PR venue d'un *fork* d'exécuter son code avec le compte de service du projet. `--include-logs-with-status` renvoie les journaux dans le *check run* GitHub.

La connexion au dépôt passe par [Developer Connect](#developer-connect) ou par les dépôts Cloud Build de 2ᵉ génération ; les deux couvrent GitHub, GitLab et Bitbucket, en version cloud ou auto-hébergée (voir [Connecter un dépôt](#connecter-un-depot)). Connexion, dépôt et déclencheur doivent être dans la **même région**.

```bash
gcloud builds triggers create github --name=web-main --region=europe-west1 \
  --repository=projects/PROJECT_ID/locations/europe-west1/connections/github/repositories/web \
  --branch-pattern='^main$' --build-config=cloudbuild.yaml \
  --service-account=projects/PROJECT_ID/serviceAccounts/build-web@PROJECT_ID.iam.gserviceaccount.com
```

**Approbation.** `--require-approval` met chaque build du déclencheur en attente ; un titulaire de `roles/cloudbuild.builds.approver` le lance ou le rejette dans la console ou par `gcloud builds approve BUILD_ID`. C'est un verrou sur un build entier, par exemple un déclencheur qui applique du Terraform en prod ; l'approbation par environnement relève de Cloud Deploy.

## Compte de service

Sans compte explicite, Cloud Build choisit selon le projet et les règles d'administration : le **compte de service Compute Engine par défaut** (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) ou le **compte de service Cloud Build hérité** (`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`). Les deux ont des droits larges sur le projet. Les contraintes `constraints/cloudbuild.useComputeServiceAccount` et `constraints/cloudbuild.useBuildServiceAccount` fixent ce choix pour une organisation.

Google recommande un **compte de service choisi par l'utilisateur** ; en pratique, un par déclencheur, avec les seuls rôles de son pipeline : écriture sur un dépôt Artifact Registry, `roles/clouddeploy.releaser` et `iam.serviceAccounts.actAs` sur le compte d'exécution Cloud Deploy, accès à ses secrets. Deux conséquences pratiques :

- un compte choisi par l'utilisateur impose de fixer où vont les journaux : `logging: CLOUD_LOGGING_ONLY`, ou `GCS_ONLY` avec un `logsBucket` du projet ;
- le compte d'un déclencheur l'emporte sur `serviceAccount` du fichier de build, qui ne sert qu'aux builds lancés à la main.

## Pool par défaut ou pool privé

| | Pool par défaut | Pool privé |
|---|---|---|
| Réseau | Internet public, aucune adresse privée | Appairage avec un VPC ou un Shared VPC, plage d'adresses internes fixe, adresse publique supprimable (`NO_PUBLIC_EGRESS`) |
| VPC Service Controls | Non | Oui |
| Types de machines | `e2-standard-2` par défaut, `E2_MEDIUM`, `E2_HIGHCPU_8`, `E2_HIGHCPU_32` ; `N1_HIGHCPU_8` et `N1_HIGHCPU_32` au prix des E2 | 64, en familles E2, N2D et C3 |
| Builds simultanés | 30 | Plus de 100, selon les quotas de CPU par région |
| Région | `global` ou une région | Celle du pool |
| Facturation | À la minute de build (0,006 $ la minute en `e2-standard-2`), à la seconde près, sans compter l'attente en file ; 2 500 minutes gratuites par mois et par compte de facturation sur `e2-standard-2` | À la minute de build, sans palier gratuit ; le pool redescend à zéro |

Le pool privé s'impose dès qu'un build doit atteindre une ressource sans adresse publique (base de données, dépôt d'artefacts interne, cluster GKE à point de terminaison privé) ou rester dans un périmètre VPC Service Controls. La contrainte `constraints/cloudbuild.allowedWorkerPools` interdit alors le pool par défaut à toute l'organisation.

```bash
gcloud builds worker-pools create pool-ci --region=europe-west1 \
  --peered-network=projects/HOST_PROJECT_ID/global/networks/VPC \
  --worker-machine-type=e2-standard-8 --no-public-egress
```

Le build choisit ensuite le pool par `options.pool.name: projects/PROJECT_ID/locations/europe-west1/workerPools/pool-ci`, et le déclencheur doit être créé dans la région du pool.

> [!WARNING]
> Un pool privé contrôle ses adresses **internes**, pas son adresse publique de sortie. Pour qu'un service externe voie une IP fixe dans sa liste d'autorisation, le trafic doit passer par une VM proxy du VPC ; `--no-public-egress` coupe, lui, tout accès à internet, y compris Docker Hub et PyPI.

## Builds sans fichier, cache et vitesse

- `gcloud builds submit --tag IMAGE` construit le `Dockerfile` du répertoire courant ; `gcloud builds submit --pack image=IMAGE` passe par les *buildpacks* de Google (`gcr.io/buildpacks/builder`), sans `Dockerfile`, pour les langages qu'ils reconnaissent. Sans fichier de configuration explicite, `gcloud builds submit` cherche `cloudbuild.yaml`.
- `$SHORT_SHA`, `$BRANCH_NAME` et les autres variables de dépôt ne sont remplies que par un déclencheur : un `gcloud builds submit` doit les passer par `--substitutions`.
- **Cache de couches.** Chaque build démarre sur une machine vierge. `--cache-from` sur l'image précédente évite de refaire les couches inchangées ; avec BuildKit, l'image source doit avoir été construite avec `BUILDKIT_INLINE_CACHE=1`. Le projet kaniko [!DECONSEILLE] de Google est archivé : `gcloud builds submit --tag` ne s'en sert que si la propriété `builds/use_kaniko` est activée, ce qui n'est pas à recommander pour un pipeline neuf.
- **Machine plus grosse** : `E2_HIGHCPU_8` ou `E2_HIGHCPU_32` pour une compilation, au prix d'un démarrage un peu plus long.

## Pièges

- **Désactiver le contrôle par commentaire** (`COMMENTS_DISABLED`) sur un dépôt ouvert aux contributions. Un build de PR tourne avec le compte de service du déclencheur : une PR venue d'un *fork* lirait les secrets qu'il atteint.
- **Oublier la région.** Sans `--region`, un build tourne en `global`, donc sur le pool par défaut ; un dépôt de 2ᵉ génération exige une région.
- **Écrire un secret dans une variable de substitution** : elle apparaît dans l'historique du build. Utiliser `availableSecrets`.
- **Compter sur `images` pour une étape de déploiement.** `images` pousse après la dernière étape : l'étape qui déploie ne trouve pas encore l'image.
- **Poser une politique de conservation sur le bucket de journaux** d'un compte de service choisi par l'utilisateur : elle peut empêcher Cloud Build d'y écrire.
- **Tout faire avec un seul déclencheur et un seul compte.** Séparer au moins le déclencheur de PR (tests, sans droit de déploiement) et celui de la branche principale (push et release).

## Alternatives en logiciel libre

- **Tekton** (Apache 2.0) : *Tasks* et *Steps* en conteneurs sur un cluster Kubernetes, le même modèle que `cloudbuild.yaml` ; **Tekton Triggers** joue le rôle des déclencheurs. Le cluster et sa capacité sont à gérer.
- **Jenkins** (MIT) : pipelines décrits dans un `Jenkinsfile`, agents statiques ou lancés à la demande dans Kubernetes ; très extensible, plus lourd à exploiter qu'un service sans serveur.
- **GitLab CI** avec **GitLab Runner** (MIT) et **Woodpecker CI** (Apache 2.0) : intégration continue attachée à la forge, étapes en conteneurs, déclencheurs sur *push*, *tag* et *merge request*.
- **Argo Workflows** (Apache 2.0) : graphes de tâches en conteneurs sur Kubernetes, pour les builds très parallèles ou les enchaînements conditionnels.
- **Concourse** (Apache 2.0) : pipelines déclaratifs pilotés par des ressources, chaque tâche dans un conteneur éphémère.
- **BuildKit** et **Buildah** (Apache 2.0), **Cloud Native Buildpacks** (Apache 2.0) : la seule partie « produire une image », avec ou sans `Dockerfile`, dans n'importe lequel des moteurs ci-dessus.
