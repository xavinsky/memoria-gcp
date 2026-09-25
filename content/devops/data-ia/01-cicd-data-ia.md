---
title: "CI/CD pour la data et l'IA"
---

Une chaîne data ou ML se livre comme une application : le code vit dans Git, la CI le teste, un artefact versionné est produit une fois puis promu d'un environnement à l'autre. Ce qui change, c'est la **nature de l'artefact** — du SQL compilé, des fichiers Python déposés dans un bucket, un modèle de job, un YAML de pipeline — et le fait que les tests sérieux demandent des données. Pour les images et les services, voir [La chaîne CI/CD](#chaine-cicd) ; ici, les briques propres à la data et à l'IA.

![Chaîne CI/CD data et IA : quatre artefacts, quatre cibles](../../svg/cicd-data-ia.svg)

## Matrice : artefact, version, test, déploiement

| Artefact | Versionné par | Testé par | Déployé par | Environnements |
|---|---|---|---|---|
| **Transformations SQL** [Dataform](#dataform) | Commit Git ; la release compile une branche, un tag ou un SHA | `dataform compile` (graphe, syntaxe), tests unitaires, `dataform run --dry-run`, assertions à l'exécution | Configuration de release (compilation) puis configuration de workflow (exécution planifiée) | *Compilation overrides* : projet, suffixe de schéma, préfixe de table |
| **Modèles dbt Core** | Commit Git | `dbt build` : modèles et tests dans l'ordre du graphe | Job [Cloud Run](#cloud-run) ou tâche Airflow qui lance `dbt build` | Cibles (*targets*) de `profiles.yml` |
| **DAG Airflow** | Commit Git ; copie des `.py` dans le bucket | `pytest` avec `DagBag`, environnement local `composer-dev`, environnement de test | Synchronisation vers le dossier `dags/` du bucket de l'environnement | Un environnement [Managed Airflow](#managed-service-for-apache-airflow) par étape, variables Airflow |
| **Pipeline Beam** [Dataflow](#dataflow) | Image étiquetée par commit + fichier de spécification JSON | `TestPipeline` sur le DirectRunner, puis job réel en staging | `gcloud dataflow flex-template run` ; en flux, job de remplacement avec `--update` | Paramètres du modèle |
| **Schéma BigQuery** | Scripts DDL numérotés | Exécution à blanc (*dry run*), puis application en staging | Scripts appliqués dans l'ordre par la CI, opérations Dataform ou Flyway | Nom du projet et du dataset en paramètre |
| **Pipeline ML** (KFP) | Modèle de pipeline dans un dépôt Artifact Registry au format KFP, étiqueté | Tests des composants, run sur un échantillon en préproduction | Planification pointée sur une version du modèle (voir [MLOps](#mlops)) | Paramètres du pipeline, compte de service par projet |

## Dataform : le cycle intégré et ce que la CI ajoute

Dataform porte son propre cycle Git. Chaque développeur travaille dans un **espace de développement** (*development workspace*) relié à une branche du dépôt distant (GitHub et GitLab par [Developer Connect](#developer-connect), HTTPS ou SSH ; Bitbucket par Developer Connect ou SSH). Il exécute à la main, pousse, ouvre une *pull request*. Une fois la fusion faite, la **configuration de release** compile la branche `main` à sa fréquence et produit un résultat de compilation ; la **configuration de workflow** l'exécute selon son horaire, avec un compte de service dédié.

Trois façons de séparer les environnements, du plus léger au plus isolé :

- **Par schéma** : les *workspace compilation overrides* ajoutent un suffixe (`analytics_dev`) aux exécutions manuelles ; la release de production n'en met pas. Les développeurs partagent le même schéma de dev et peuvent s'écraser.
- **Par schéma et projet** : un projet de dev, un schéma par développeur grâce à la variable `${workspaceName}` dans le suffixe.
- **Par projet** : une release par environnement (dev, staging, prod), chacune avec son projet cible ; ou une copie du dépôt Dataform par projet, pour régler les droits IAM étape par étape.

Les *overrides* d'espace de travail ne se planifient pas : seule une release alimente une configuration de workflow. La CLI libre (`npm i -g @dataform/cli`) reprend les mêmes réglages en options (`--schema-suffix`, `--table-prefix`, `--default-database`, `--vars`), ce qui permet de vérifier une *pull request* hors de la console :

```yaml
# .github/workflows/dataform.yml — contrôle d'une pull request
on:
  pull_request:
    branches: [main]
permissions:
  contents: read
  id-token: write
jobs:
  verifier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
          service_account: dataform-ci@PROJECT_ID.iam.gserviceaccount.com
      - run: npm i -g @dataform/cli
      - run: echo '{"projectId":"PROJECT_ID","location":"EU"}' > .df-credentials.json
      - run: dataform compile
      - run: dataform test
      - run: dataform run --dry-run
```

Le fichier `.df-credentials.json` sans clé indique à la CLI d'utiliser les ADC, fournies ici par [Workload Identity Federation](#deployer-sans-cle). `dataform test` lance les **tests unitaires** : un fichier `type: "test"` fournit des lignes simulées pour chaque dépendance (`input "source" { SELECT ... }`) et le résultat attendu ; Dataform core 3.0.56 au minimum, 100 lignes par entrée au plus. Les **assertions** (`nonNull`, `uniqueKey`, `rowConditions`, ou requête libre) contrôlent, elles, les vraies données après chaque table et font échouer le workflow.

> [!TIP]
> La release ne recompile `main` qu'à sa fréquence. Pour livrer juste après la fusion, la CI peut créer elle-même un résultat de compilation par l'API (`compilationResults.create`, avec ses *overrides*) puis l'exécuter (`workflowInvocations.create`) ; il n'existe pas de groupe de commandes `gcloud dataform`.

**dbt Core** (Apache 2.0, adaptateur `dbt-bigquery`) couvre le même besoin avec un outillage indépendant de Google : `ref()`, tests, documentation, et des cibles par environnement. Il n'a pas de service d'exécution géré sur Google Cloud : il tourne dans un job Cloud Run, une tâche Airflow ou la CI. Le choix entre les deux se fait surtout sur l'existant de l'équipe (voir [Choisir le moteur de traitement](#choisir-un-moteur)).

## DAG Airflow : tester, puis synchroniser le bucket

Un environnement Managed Airflow lit ses DAG dans le dossier `dags/` de son bucket et les propage aux composants en quelques minutes. Déployer revient donc à copier des fichiers ; toute la valeur de la chaîne est dans les tests qui précèdent.

- **Test d'import** : charger tous les fichiers dans un `DagBag` et exiger `import_errors == {}`. Il attrape les erreurs de syntaxe, les imports manquants et les cycles. En Airflow 3, `from airflow.dag_processing.dagbag import DagBag` ; en Airflow 2, `from airflow.models import DagBag`.
- **Environnement local** : l'outil *Composer Local Development CLI* (`composer-dev create`, `start`, `run-airflow-cmd`) lance dans Docker ou Podman l'image Airflow d'une version donnée du service, avec la liste de paquets PyPI d'un environnement existant. Les appels partent avec le compte de la gcloud CLI, pas avec le compte de service de l'environnement.
- **Environnement de test** : Airflow n'isole pas les DAG entre eux. La documentation recommande un environnement de test distinct de la production ; sur un même environnement, préfixer les identifiants de tâche par le nom de branche.

```yaml
# cloudbuild.yaml — déclenché sur main, vers l'environnement de dev
steps:
  - id: tests
    name: python:3.11-slim            # même version que l'image Airflow visée
    entrypoint: bash
    env: ["PYTHONDONTWRITEBYTECODE=1"]
    args: ["-c", "pip install -r requirements.txt -c constraints.txt pytest && python -m pytest tests/"]
  - id: synchroniser
    name: gcr.io/google.com/cloudsdktool/cloud-sdk:slim
    entrypoint: gcloud
    args: ["storage", "rsync", "dags/", "${_DAGS_BUCKET}/dags",
           "--recursive", "--delete-unmatched-destination-objects"]
substitutions:
  _DAGS_BUCKET: gs://BUCKET
options:
  logging: CLOUD_LOGGING_ONLY
```

`gcloud composer environments storage dags import --source=dags/` fait aussi l'affaire pour ajouter ou remplacer des fichiers, mais ne supprime jamais un DAG retiré du dépôt : `rsync` avec suppression garde le bucket identique à Git. Le bucket s'obtient par `gcloud composer environments describe ENV --location REGION --format="get(config.dagGcsPrefix)"`.

## Dataflow : un modèle Flex par commit

Un **modèle Flex** (*Flex Template*) réunit une image de conteneur qui contient le pipeline et un fichier de spécification JSON, dans Cloud Storage, qui pointe vers l'image et décrit les paramètres. La CI le construit en une commande ; l'étiquette de l'image et le nom du fichier portent le SHA du commit :

```bash
gcloud dataflow flex-template build gs://BUCKET/modeles/ventes-$SHORT_SHA.json \
  --image-gcr-path "REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/ventes:$SHORT_SHA" \
  --sdk-language PYTHON --flex-template-base-image PYTHON3 \
  --metadata-file metadata.json --py-path . \
  --env FLEX_TEMPLATE_PYTHON_PY_FILE=pipeline.py \
  --env FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE=requirements.txt
```

Chaque environnement lance ensuite le même fichier avec ses paramètres : `gcloud dataflow flex-template run JOB --template-file-gcs-location gs://BUCKET/modeles/ventes-SHA.json --region REGION --parameters ...`. Un pipeline de lots se relance simplement. Un pipeline de flux se remplace par un **job de remplacement** : même nom de job, même région, option `--update`, et `--transform-name-mappings` si des étapes ont été renommées. Un premier lancement avec `--additional-experiments=graph_validate_only` vérifie la compatibilité sans rien remplacer.

## Schémas BigQuery

BigQuery n'a pas d'outil de migration intégré ; les instructions DDL sont gratuites et se versionnent comme du code. Ce qui se fait en place : ajouter une colonne `NULLABLE` ou `REPEATED` (toujours en fin de schéma), la renommer (`RENAME COLUMN`), la supprimer (`DROP COLUMN`), élargir un type (`SET DATA TYPE`, par exemple `INT64` vers `NUMERIC`), relâcher un `REQUIRED`. Ajouter une colonne `REQUIRED`, rétrécir un type ou modifier un champ dans un tableau de `STRUCT` passe par une nouvelle table (`CREATE OR REPLACE TABLE ... AS SELECT`).

- **Scripts numérotés** appliqués par la CI avec `bq query --use_legacy_sql=false`, écrits pour être rejoués sans effet (`ADD COLUMN IF NOT EXISTS`).
- **Opérations Dataform** (`type: "operations"`) quand l'entrepôt est déjà dans Dataform : la migration passe dans le graphe, avant les tables qui en dépendent.
- **Flyway** (édition Community, Apache 2.0) a un module BigQuery et tient l'historique des migrations appliquées. Liquibase, lui, est distribué sous *Functional Source License*, qui n'est pas une licence libre.

## Promotion entre projets

Un artefact construit une fois, dans un projet d'outillage, est promu tel quel : même image, même spécification JSON, même version de modèle KFP, même commit Dataform. Seuls changent les paramètres (projet, dataset ou suffixe, bucket) et l'identité d'exécution : un compte de service par pipeline et par projet, qui doit pouvoir lire le dépôt Artifact Registry partagé. La promotion elle-même — approbation, passage de staging à prod — se pilote par la CI ou par [Cloud Deploy](#cloud-deploy), qui sait aussi livrer un job Cloud Run.

## Pièges

- **Tester sur la production.** Une assertion ou un `dry run` sur les tables de prod est utile ; une exécution de test qui écrit dans les datasets de prod, non. Un suffixe de schéma ou un projet de CI suffit à l'éviter.
- **Changer la logique d'une table incrémentale sans reconstruction.** Les lignes déjà calculées gardent l'ancienne logique : prévoir un `dataform run --full-refresh` (ou *Run with full refresh*) dans la livraison.
- **Laisser des DAG fantômes.** Un fichier retiré du dépôt reste dans le bucket sans synchronisation avec suppression, et un DAG supprimé laisse ses métadonnées dans l'interface Airflow.
- **Mettre du travail au niveau du module d'un DAG.** Il s'exécute à chaque analyse du fichier, pendant les tests comme en production.
- **Pointer la production sur `latest`.** Un modèle Flex, une image ou un modèle KFP désignés par une étiquette mobile changent sous les pieds du job suivant ; en production, référencer le SHA ou le condensé.
- **Mettre à jour un job de flux sans validation.** Un graphe incompatible fait échouer le remplacement ; `graph_validate_only` le dit avant. Les jobs de lots, eux, ne se mettent pas à jour.

## Alternatives en logiciel libre

- **dbt Core** (Apache 2.0) et **Flyway** Community (Apache 2.0), déjà décrits plus haut ; Airflow et Kubeflow Pipelines (Apache 2.0) sont eux-mêmes libres et tournent aussi hors de Google Cloud.
- **SQLMesh** (Apache 2.0) : transformations SQL avec un `plan` qui montre l'effet d'une modification avant de l'appliquer et des environnements virtuels par branche, sans recopier les tables ; adaptateur BigQuery disponible.
- **SQLFluff** (MIT) : analyse et formatage du SQL, dialecte BigQuery et gabarits dbt compris, à placer en étape de contrôle de pull request.
- **Great Expectations** (Apache 2.0) : assertions sur les données elles-mêmes (nullité, unicité, plages, distributions), exécutées dans le pipeline avant la promotion, en complément des assertions Dataform.
- **DVC** (Apache 2.0) : versionne jeux de données et modèles à côté du code, dans un bucket Cloud Storage, et rejoue un pipeline à l'identique à partir d'un commit.
- **MLflow** (Apache 2.0) : suivi des expériences et registre de modèles avec alias par étape, face au suivi d'expériences et au registre de modèles de Google Cloud.
