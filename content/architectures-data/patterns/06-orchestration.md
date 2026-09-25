---
title: Orchestrer les pipelines
---

Un orchestrateur décide **quand** un traitement démarre et **dans quel ordre** ses étapes s'enchaînent ; il ne fait pas le calcul lui-même, qu'il confie à BigQuery, Dataflow, Spark ou Cloud Run. Le choix se fait d'abord sur le **déclencheur** (un horaire ou un événement), puis sur la **forme de l'enchaînement** : une seule action, une suite d'appels d'API, un graphe SQL dans BigQuery, ou un graphe de tâches qui traverse plusieurs systèmes et doit pouvoir être rejoué sur le passé.

![Arbre de décision : du déclencheur à l'orchestrateur](../../svg/choix-orchestrateur.svg)

## Matrice de choix

| Outil | Déclenchement | Définition | Dépendances | Réessais et rattrapage | Coût au repos | Cas typique |
|---|---|---|---|---|---|---|
| **[Cloud Scheduler](#cloud-scheduler)** | Horaire `unix-cron` | Une tâche, une cible (HTTP, Pub/Sub) | Aucune | Réessais ; pas de rattrapage | 0,10 $ par tâche et par mois, 3 gratuites par compte de facturation | Démarrer un job, un workflow, un DAG à heure fixe |
| **Requête planifiée BigQuery** | Horaire, 5 minutes au plus court | Une requête GoogleSQL | Aucune entre requêtes | Relance manuelle sur une plage de dates passée | Rien, la requête est facturée | Agrégat quotidien, table de rapport |
| **[Dataform](#dataform)** | Horaire (configuration de workflow) ou appel d'API | Fichiers SQLX, `ref()` | Graphe déduit du SQL, dans BigQuery seulement | Assertions qui arrêtent le graphe ; tables incrémentales | Rien, les requêtes sont facturées | Couches brut, nettoyé, métier dans BigQuery |
| **[Workflows](#workflows)** | Appel HTTP, Cloud Scheduler, Eventarc | YAML ou JSON, étapes et connecteurs | Séquence, conditions, branches parallèles | `try`/`retry` par étape ; pas de rattrapage | Rien, facturé à l'étape exécutée | Enchaîner quelques API, attendre un rappel |
| **[Eventarc](#eventarc)** | Événement Google Cloud (objet déposé, journal d'audit, message) | Déclencheur filtré vers une cible | Aucune : il route, la cible enchaîne | Réessais pendant 24 heures | Rien au-delà du transport Pub/Sub | Réagir à l'arrivée d'un fichier |
| **[Managed Airflow](#managed-service-for-apache-airflow)** | Horaire, manuel, API, événement (*assets* en Airflow 3) | DAG Python, opérateurs | Graphe riche, capteurs, dépendances entre DAG, systèmes tiers | Réessais par tâche, *catchup* et *backfill* | Environnement facturé en continu (DCU-heures) | Pipeline multisystème avec historique à rejouer |
| **[Agent Platform Pipelines](#gemini-enterprise-agent-platform)** | Manuel, API, planification | Kubeflow Pipelines ou TFX | Étapes ML, artefacts et lignage | Cache des étapes déjà calculées | Rien, facturé à l'exécution | Entraîner, évaluer, déployer un modèle |

La CLI (`gcloud composer`) et les URL de documentation de Managed Service for Apache Airflow emploient le nom Cloud Composer.

## Critères qui départagent

- **Complexité du graphe.** Trois étapes en séquence tiennent dans un workflow. Des dizaines de tâches avec branches, capteurs qui attendent un fichier ou une partition, dépendances entre pipelines d'équipes différentes : c'est le terrain d'Airflow. Un graphe entièrement fait de SQL BigQuery relève de Dataform, qui déduit l'ordre des `ref()` au lieu de le faire écrire.
- **Systèmes traversés.** Workflows appelle toute API HTTP et dispose de connecteurs pour les services Google Cloud. Airflow ajoute des *providers* pour les autres clouds, les bases, les outils SaaS et les systèmes sur site, et peut piloter des ressources éphémères (créer un cluster, lancer le job, le supprimer).
- **Coût au repos.** Un environnement Airflow repose sur un cluster GKE et une base de métadonnées qui tournent en permanence : son coût de base court 24 heures sur 24, même pour un DAG quotidien de dix minutes. Workflows, Scheduler, Dataform et les requêtes planifiées ne coûtent rien entre deux exécutions. En dessous de quelques pipelines, l'écart est net.
- **Horaire ou événement.** Un traitement qui suit l'arrivée des données (fichier déposé, message publié) part d'[Eventarc](#eventarc) vers Cloud Run ou Workflows, sans attendre la prochaine échéance. Un DAG Airflow peut aussi être déclenché par l'API Airflow depuis une fonction, mais Airflow n'est pas fait pour réagir à un flux continu : c'est le rôle du [streaming](#streaming).
- **Rattrapage et historique.** Rejouer un mois de traitements sur les bonnes dates est natif dans Airflow : chaque exécution porte sa **date logique**, que les tâches reçoivent par les gabarits `{{ ds }}`. Workflows et Cloud Scheduler n'ont pas cette notion ; il faut boucler soi-même sur les dates.
- **Attente longue.** Une validation humaine ou une réponse d'un système tiers qui arrive dans trois jours : un workflow attend un rappel jusqu'à un an, pour quelques étapes facturées.

## Un DAG Airflow minimal

Charger les fichiers Parquet du jour dans une partition, puis lancer une procédure d'agrégation. Le fichier se dépose dans le dossier `dags/` du bucket de l'environnement.

```python
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

with DAG(
    dag_id="ventes_quotidiennes",
    schedule="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:
    charger = GCSToBigQueryOperator(
        task_id="charger_brut",
        bucket="BUCKET",
        source_objects=["ventes/{{ ds_nodash }}/*.parquet"],
        source_format="PARQUET",
        # Décorateur de partition + WRITE_TRUNCATE : une relance remplace le jour, sans doublon
        destination_project_dataset_table="PROJECT_ID.DATASET.ventes_brutes${{ ds_nodash }}",
        write_disposition="WRITE_TRUNCATE",
    )
    agreger = BigQueryInsertJobOperator(
        task_id="agreger",
        location="REGION",
        configuration={
            "query": {
                "query": "CALL DATASET.agreger_ventes(DATE '{{ ds }}')",
                "useLegacySql": False,
            }
        },
    )
    charger >> agreger
```

Chaque tâche fait une seule chose et ne dépend que de sa date logique, jamais de l'heure courante : c'est ce qui rend les relances et les rattrapages sûrs.

## Un workflow minimal

Le même enchaînement sans environnement permanent : un chargement BigQuery par connecteur, qui attend la fin du job, puis une exécution Dataform par l'API.

```yaml
main:
  params: [args]
  steps:
    - init:
        assign:
          - project: ${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}
          # AAAAMMJJ : argument d'une relance, sinon la date du jour (UTC)
          - aujourdhui: ${text.replace_all(text.substring(time.format(sys.now()), 0, 10), "-", "")}
          - jour: ${default(map.get(args, "jour"), aujourdhui)}
          - repository: ${"projects/" + project + "/locations/REGION/repositories/REPOSITORY"}
    - charger_brut:
        call: googleapis.bigquery.v2.jobs.insert
        args:
          projectId: ${project}
          body:
            configuration:
              load:
                sourceUris: ${["gs://BUCKET/ventes/" + jour + "/*.parquet"]}
                sourceFormat: PARQUET
                destinationTable:
                  projectId: ${project}
                  datasetId: DATASET
                  tableId: ${"ventes_brutes$" + jour}
                writeDisposition: WRITE_TRUNCATE
    - compiler:
        try:
          call: http.post
          args:
            url: ${"https://dataform.googleapis.com/v1/" + repository + "/compilationResults"}
            auth:
              type: OAuth2
            body:
              gitCommitish: main
          result: compilation
        retry: ${http.default_retry}
    - transformer:
        call: http.post
        args:
          url: ${"https://dataform.googleapis.com/v1/" + repository + "/workflowInvocations"}
          auth:
            type: OAuth2
          body:
            compilationResult: ${compilation.body.name}
        result: invocation
    - fin:
        return: ${invocation.body.name}
```

```bash
gcloud workflows deploy ventes-quotidiennes --location=REGION \
  --source=workflow.yaml --service-account=SA_EMAIL
gcloud scheduler jobs create http ventes-quotidiennes --location=REGION \
  --schedule="0 3 * * *" --time-zone="Europe/Paris" \
  --uri="https://workflowexecutions.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/workflows/ventes-quotidiennes/executions" \
  --message-body='{"argument": "{}"}' \
  --oauth-service-account-email=SA_EMAIL
```

L'appel à `workflowInvocations` rend la main dès que l'exécution Dataform est créée : pour attendre son résultat, ajouter une boucle qui interroge l'invocation jusqu'à un état final. Le calcul de la date dans `init` montre la limite du modèle : sans date logique, le workflow la déduit de l'heure d'exécution, et un rattrapage se fait en lançant des exécutions à la main, une par jour, avec l'argument `{"jour": "20260901"}`.

## Combinaisons courantes

- **Cloud Scheduler → Workflows → BigQuery et Dataform** : la chaîne quotidienne la plus économique, sans rien qui tourne entre deux passages.
- **Eventarc (objet déposé dans Cloud Storage) → Workflows** : charger un fichier dès son arrivée, puis déclencher la suite. Un seul traitement suffit ? Eventarc vers un service ou un job Cloud Run.
- **Airflow → Dataflow, Spark, Dataform, BigQuery** : Airflow ordonne, chaque moteur calcule. Le graphe SQL reste dans Dataform, qu'une tâche Airflow déclenche, plutôt que d'éclater des dizaines de requêtes en tâches.
- **Requête planifiée seule** : une table d'agrégat qui ne dépend de rien d'autre. Dès que deux requêtes dépendent l'une de l'autre, passer à Dataform.
- **Agent Platform Pipelines** pour l'entraînement et le déploiement de modèles, déclenché par Airflow ou Workflows quand il s'insère dans une chaîne data plus large.

## Pièges

- **Travail au niveau du module** : Airflow relit chaque fichier de DAG en boucle. Une requête, un appel réseau ou une lecture de fichier écrits hors des tâches s'exécutent à chaque analyse, même quand le DAG ne tourne pas.
- **Rattrapage involontaire** : en Airflow 2, `catchup` vaut `True` par défaut ; un DAG publié avec une `start_date` lointaine lance aussitôt une exécution par intervalle manqué. Airflow 3 inverse ce défaut. Le fixer explicitement dans chaque DAG.
- **Relances non idempotentes** : Cloud Scheduler, Eventarc et les réessais de tâches livrent **au moins une fois**. Un `INSERT` ou un `WRITE_APPEND` relancé double les lignes ; écrire par partition avec remplacement, ou par `MERGE`.
- **Calcul dans l'orchestrateur** : une transformation de données dans un `PythonOperator` s'exécute sur les *workers* de l'environnement, qui ne sont pas dimensionnés pour ça. Déléguer à BigQuery, Dataflow ou un job Cloud Run.
- **Coût des sondages** : un connecteur Workflows qui attend un job long l'interroge à intervalle régulier, et chaque sondage compte comme une étape facturée. Un capteur Airflow en mode classique occupe un *worker* pendant toute l'attente ; préférer les opérateurs différables, que le *triggerer* surveille sans bloquer de *worker*.

> [!TIP]
> Un environnement Airflow est facturé tant qu'il existe : pour arrêter la facturation, on le supprime. Un **instantané** d'environnement (dossiers `dags/`, `data/` et `plugins/`, configuration, paquets PyPI, sauvegarde de la base Airflow) permet d'en recréer un identique plus tard, par exemple pour un environnement de test utilisé quelques jours par mois.

## Alternatives en logiciel libre

- **Apache Airflow** (Apache 2.0) : le moteur même de Managed Airflow, installé sur Kubernetes avec son chart Helm ; les DAG de cette page tournent sans modification, mais base de métadonnées, *workers* et mises à jour sont à exploiter.
- **Dagster** (Apache 2.0) : orchestration centrée sur les actifs de données produits plutôt que sur les tâches, avec partitions et *backfills* natifs ; proche de la logique de Dataform étendue à tous les systèmes.
- **Prefect** (Apache 2.0) : workflows en Python ordinaire, sans graphe déclaré à l'avance ; convient aux chaînes dynamiques, avec moins de rattrapage sur dates logiques qu'Airflow.
- **Kestra** (Apache 2.0) : workflows déclarés en YAML avec déclencheurs horaires et événementiels (fichier déposé, message, webhook) ; il couvre à la fois le terrain de Workflows avec Eventarc et celui d'Airflow.
- **Argo Workflows** (Apache 2.0) : DAG de conteneurs sur Kubernetes, décrits en YAML ; chaque étape tourne dans son propre pod, sans environnement permanent autre que le cluster.
- **Temporal** (MIT) : workflows durables écrits dans un vrai langage, avec réessais, signaux et attentes de plusieurs jours ; l'équivalent des attentes longues de Workflows, au prix d'un serveur et d'une base à exploiter.
- **Kubeflow Pipelines** (Apache 2.0) : pipelines de ML sur Kubernetes, avec artefacts, lignage et cache des étapes ; c'est le format qu'exécute Agent Platform Pipelines.
