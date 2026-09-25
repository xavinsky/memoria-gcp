---
title: "MLOps : pipelines, suivi, surveillance"
---

Un modèle en production se dégrade sans que son code change : les données qu'il reçoit s'écartent de celles de l'entraînement. Le *MLOps* répond par une boucle : un **pipeline** rejoue préparation, entraînement, évaluation et enregistrement ; le **registre** décide quelle version sert ; la **surveillance** compare le trafic réel à la référence et relance le pipeline. La chaîne CI/CD, elle, teste et publie le pipeline lui-même.

![Boucle MLOps : du dépôt Git au réentraînement](../../svg/boucle-mlops.svg)

Toutes les briques appartiennent à [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform), sous des noms de la forme « Agent Platform Pipelines » (ex-Vertex AI Pipelines), « Experiments », « Feature Store ». Le SDK reste `google-cloud-aiplatform` (`from google.cloud import aiplatform`) ; les pipelines s'écrivent avec le SDK Kubeflow Pipelines, `kfp`. L'entraînement et le service sont détaillés dans [Entraîner et servir un modèle](#entrainer-et-servir).

## Niveaux de maturité

Le guide d'architecture de Google distingue trois niveaux ([MLOps : livraison continue et pipelines d'automatisation](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)).

| Niveau | Ce qui est automatisé | Déclencheur | Ce qu'on livre | Suffit quand |
|---|---|---|---|---|
| **0 — manuel** | Rien : notebooks exécutés à la main, modèle remis aux équipes qui le servent | Décision humaine | Un modèle | Quelques modèles, réentraînés une ou deux fois par an |
| **1 — pipeline automatisé** | Préparation, entraînement, validation des données et du modèle, enregistrement : *entraînement continu* | Planification, arrivée de données, alerte de surveillance | Le pipeline, qui produit les modèles | Les données bougent, le code change peu |
| **2 — CI/CD du pipeline** | En plus, construction, tests et déploiement du pipeline et de ses composants à chaque commit | Commit, puis les déclencheurs du niveau 1 | Pipeline, composants, service | Plusieurs équipes font évoluer les modèles et les caractéristiques |

Passer du niveau 0 au niveau 1 apporte l'essentiel : un entraînement rejouable, tracé et déclenché sans intervention. Le niveau 2 se justifie quand le pipeline change aussi souvent que les données.

## Les briques

| Brique | Rôle | À retenir |
|---|---|---|
| **Pipelines** | Exécute un graphe acyclique (*DAG*) de tâches conteneurisées, défini avec le SDK KFP (v2.0 ou plus) ou TFX, compilé en YAML | Serverless : chaque tâche tourne en job d'entraînement (`e2-standard-4` par défaut). 0,03 $ par exécution, plus les ressources consommées. Pas de commande `gcloud` : SDK, REST ou console |
| **Google Cloud Pipeline Components** | Composants prêts à l'emploi : `CustomTrainingJobOp`, `ModelUploadOp`, `ModelBatchPredictOp`, `ModelDeployOp`, `ModelEvaluationClassificationOp`, `BigqueryQueryJobOp`, Dataflow, Spark | Délèguent le calcul au service visé ; le pipeline ne fait qu'attendre |
| **ML Metadata** | Enregistre paramètres, artefacts et exécutions de chaque run : c'est le graphe de **lignage** | Alimenté sans code par Pipelines ; synchronisable avec [Knowledge Catalog](#knowledge-catalog). 10 $ par Gio et par mois |
| **Experiments**, **TensorBoard** | Comparent les runs : paramètres, métriques, courbes d'apprentissage | Experiments sans surcoût ; TensorBoard facturé au stockage (10 $ par Gio et par mois) |
| **Model Registry** | Versions et alias (`candidat`, `prod`) | L'alias est le point de décision : la promotion déplace un alias, le déploiement suit |
| **Model Evaluation** | Compare les sorties d'un job par lots à une vérité terrain (précision, rappel, AuPRC, matrice de confusion) | Composant de pipeline ou console ; les résultats s'attachent à la version du modèle |
| **Feature Store** | Couche de métadonnées au-dessus de tables BigQuery : les données hors ligne restent dans BigQuery, le service en ligne passe par un *online store* | Choisir le service en ligne **Bigtable** : le service « Optimized » [!DECONSEILLE] est déprécié, arrêté le 17 février 2027. Tarif au nœud-heure pour le service en ligne |
| **Model Monitoring** | Détecte le biais entraînement-service (*training-serving skew*) et la dérive (*drift*) des entrées et des sorties | v1 (GA) configurée sur un endpoint, alertes par e-mail, 3,50 $ par Go analysé ; v2 [!PREVERSION] (sans frais propres) attachée à une version du modèle, y compris un modèle servi hors d'Agent Platform (GKE…) et inscrit sans artefact, divergence de Jensen-Shannon ou L-infini, attributions, alertes par e-mail ou canal Cloud Monitoring |

> [!TIP]
> Le biais entraînement-service vient souvent de deux calculs des caractéristiques : un en SQL pour l'entraînement, un autre dans l'application au moment de la requête. Les calculer une fois dans BigQuery et les servir par Feature Store supprime cet écart à la source.

## Qui orchestre

Agent Platform Pipelines n'est pas un orchestrateur généraliste : il connaît les artefacts, le lignage et le cache des étapes ML, pas les capteurs de fichiers ni le rattrapage sur des dates passées (voir [Orchestrer les pipelines](#orchestration)).

- **Pipelines seul** quand l'entraînement se suffit à lui-même : planification intégrée (`create_schedule`, format cron avec fuseau), ou déclenchement par Pub/Sub à travers une fonction [Cloud Run](#cloud-run).
- **[Managed Service for Apache Airflow](#managed-service-for-apache-airflow) au-dessus** quand le réentraînement est une étape d'une chaîne data plus large : le DAG attend la fin des chargements, puis lance le pipeline avec `RunPipelineJobOperator`.
- **[Workflows](#workflows)** pour un enchaînement court d'appels d'API (déclencher un run, attendre, notifier), par son connecteur Agent Platform.
- **[BigQuery ML](#bigquery-ml)** avec des requêtes planifiées ou Dataform, quand le modèle vit dans l'entrepôt : aucun pipeline à écrire.

## CI/CD pour le ML

L'intégration continue porte sur le **code du pipeline**, pas sur le modèle : tests unitaires des transformations et des composants, construction des images dans [Artifact Registry](#artifact-registry), compilation du pipeline, puis dépôt du YAML comme **modèle de pipeline** versionné dans un dépôt Artifact Registry au format KFP. Un run sur un échantillon, dans un projet de préproduction, valide l'ensemble.

- **Qui construit.** Un déclencheur [Cloud Build](#cloud-build) sur le dépôt, ou GitHub Actions et GitLab CI authentifiés par [Workload Identity Federation](#workload-identity-federation), sans clé de compte de service. Le détail de ces chaînes relève de l'onglet DevOps.
- **Livraison du pipeline.** Le déploiement en production crée la planification sur la nouvelle version du modèle de pipeline, désignée par son étiquette ou son condensé (`template_path` de la forme `URI:ETIQUETTE` ou `URI@sha256:...`), et supprime l'ancienne.
- **Livraison du modèle.** Le pipeline enregistre une version avec l'alias `candidat` ; la comparaison avec la version `prod` (métriques d'évaluation, validation humaine si besoin) déplace l'alias, puis un déploiement répartit le trafic, par exemple 10 % sur la nouvelle version le temps de vérifier. Avant cette bascule, un test automatisé de l'endpoint en préproduction vérifie les prédictions, la latence et le débit sous charge (Locust, k6) ([Well-Architected Framework, excellence opérationnelle](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/operational-excellence)). Un modèle servi sur Cloud Run ou GKE peut suivre la promotion de [Cloud Deploy](#cloud-deploy).
- **Identité.** Un compte de service dédié par pipeline, passé à `submit()` : sans lui, les runs prennent le compte de service par défaut de Compute Engine, souvent trop large.

## Un pipeline KFP minimal

Préparation depuis BigQuery, entraînement, puis enregistrement dans le registre seulement si le score dépasse un seuil :

```python
from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output

IMAGE = "python:3.12"


@dsl.component(base_image=IMAGE, packages_to_install=["google-cloud-bigquery[pandas]"])
def preparer(table: str, jeu: Output[Dataset]):
    from google.cloud import bigquery
    bigquery.Client().query(f"SELECT * FROM `{table}`").to_dataframe().to_csv(jeu.path, index=False)


@dsl.component(base_image=IMAGE, packages_to_install=["pandas", "scikit-learn==1.6.1", "joblib"])
def entrainer(jeu: Input[Dataset], modele: Output[Model], metriques: Output[Metrics]) -> float:
    import os
    import joblib
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(jeu.path)
    X_tr, X_te, y_tr, y_te = train_test_split(df.drop(columns="label"), df["label"], test_size=0.2)
    clf = LogisticRegression(max_iter=1000).fit(X_tr, y_tr)
    score = float(clf.score(X_te, y_te))
    metriques.log_metric("accuracy", score)
    os.makedirs(modele.path, exist_ok=True)
    joblib.dump(clf, os.path.join(modele.path, "model.joblib"))
    return score


@dsl.component(base_image=IMAGE, packages_to_install=["google-cloud-aiplatform"])
def enregistrer(modele: Input[Model], project: str, region: str, parent: str):
    from google.cloud import aiplatform
    aiplatform.init(project=project, location=region)
    aiplatform.Model.upload(
        display_name="churn",
        artifact_uri=modele.uri,  # dossier gs:// qui contient model.joblib
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-6:latest",
        parent_model=parent or None,  # nouvelle version d'un modèle existant
        is_default_version=False,
        version_aliases=["candidat"],
    )


@dsl.pipeline(name="churn-entrainement")
def pipeline(project: str, region: str, table: str, parent: str = "", seuil: float = 0.8):
    prep = preparer(table=table).set_caching_options(False)  # la table change, pas son nom
    train = entrainer(jeu=prep.outputs["jeu"]).set_cpu_limit("8").set_memory_limit("32G")
    with dsl.If(train.outputs["Output"] >= seuil, name="assez-bon"):
        enregistrer(modele=train.outputs["modele"], project=project, region=region, parent=parent)


compiler.Compiler().compile(pipeline, "churn.yaml")
```

Exécution unique, ou planification hebdomadaire :

```python
from google.cloud import aiplatform

aiplatform.init(project="PROJECT_ID", location="REGION")
job = aiplatform.PipelineJob(
    display_name="churn-entrainement",
    template_path="churn.yaml",
    pipeline_root="gs://BUCKET/pipelines",
    parameter_values={"project": "PROJECT_ID", "region": "REGION",
                      "table": "PROJECT_ID.DATASET.churn"},
)
job.submit(service_account="pipelines@PROJECT_ID.iam.gserviceaccount.com")
# ou bien :
# job.create_schedule(display_name="churn-hebdo", cron="TZ=Europe/Paris 0 3 * * 1",
#                     max_concurrent_run_count=1,
#                     service_account="pipelines@PROJECT_ID.iam.gserviceaccount.com")
```

La valeur de retour d'un composant s'appelle `Output` dans `outputs` ; `dsl.Condition` [!DECONSEILLE] est dépréciée au profit de `dsl.If`. Les métriques écrites par `log_metric` s'affichent dans la console et se comparent entre runs. `set_retry(num_retries=...)` relance une tâche après une erreur passagère ([relances](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/pipelines/configure-retries)) ; `PipelineJob(failure_policy="fast")` cesse de planifier de nouvelles tâches dès le premier échec, là où la politique par défaut (`slow`) exécute tout ce qui peut encore l'être ([politique d'échec](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/pipelines/configure-failure-policy)).

## Pièges

- **Cache des étapes.** Une étape dont les entrées, la définition et l'image n'ont pas changé est sautée et son résultat réutilisé. Une étape qui lit une table par son nom rendra les données d'hier : désactiver le cache sur la lecture (`set_caching_options(False)`) ou passer la date en paramètre.
- **Surveillance sans journaux.** Model Monitoring compare le trafic à une référence : il faut journaliser les requêtes dans BigQuery (option de l'endpoint) et fournir le jeu d'entraînement. Un taux d'échantillonnage limite le volume analysé, donc la facture.
- **Alerte sans suite.** Une dérive détectée qui n'envoie qu'un e-mail ne ferme pas la boucle : router l'alerte vers un canal Cloud Monitoring de type Pub/Sub, qui déclenche le pipeline, avec un seuil qui ne relance pas l'entraînement à chaque variation.
- **Réentraîner sur des données non vérifiées.** Un pipeline automatique apprend aussi bien d'une extraction cassée ou de données empoisonnées (*data poisoning*) que de données saines. Placer une étape de validation avant l'entraînement : schéma, plages, taux de nulls, distribution comparée à la référence, par les [analyses de qualité des données](https://docs.cloud.google.com/bigquery/docs/data-quality-scan) de Knowledge Catalog sur les tables BigQuery ou par TensorFlow Data Validation, et arrêter le run sous le seuil ([Well-Architected Framework, sécurité](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/security)).
- **Métadonnées qui s'accumulent.** ML Metadata et TensorBoard se facturent au Gio stocké ; supprimer les runs et expériences obsolètes.
- **Région du `pipeline_root`.** Le bucket des artefacts, le pipeline, les données et le modèle doivent être dans la même région, comme pour l'entraînement.
- **Promotion automatique sans garde-fou.** Déplacer l'alias `prod` sur la seule foi d'une métrique globale expose aux régressions sur un segment : comparer aussi sur des tranches de données, et garder une part de trafic sur l'ancienne version le temps de vérifier.

## Alternatives en logiciel libre

- **Kubeflow Pipelines** (Apache 2.0) : le même SDK `kfp` et le même YAML compilé, exécutés sur son propre cluster Kubernetes ; les Google Cloud Pipeline Components, qui appellent des services Google, n'y ont pas d'équivalent direct.
- **MLflow** (Apache 2.0) : suivi des expériences, registre de modèles avec alias et évaluation ; l'équivalent d'Experiments, de Model Registry et de Model Evaluation.
- **Feast** (Apache 2.0) : *feature store* sur le même principe que Feature Store, données hors ligne dans l'entrepôt (BigQuery compris) et magasin en ligne au choix (Redis, PostgreSQL, Bigtable…).
- **Evidently** (Apache 2.0) : rapports, tests et surveillance de la dérive des données et des prédictions, l'équivalent de Model Monitoring.
- **TFX** (Apache 2.0) : déjà cité ; ses composants valident les données (TensorFlow Data Validation) et le modèle (TensorFlow Model Analysis) au sein du pipeline.
- **Flyte**, **ZenML**, **Metaflow** (Apache 2.0) : orchestrateurs de pipelines ML, avec cache des étapes, versionnement des artefacts et exécution sur Kubernetes ou dans le cloud.
- **DVC** (Apache 2.0) : versionnement des jeux de données et des modèles à côté du code dans Git, pour rejouer un entraînement à l'identique.
