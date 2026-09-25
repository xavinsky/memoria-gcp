---
title: "SDK Agent Platform : entraînement, modèles, endpoints"
subgroup: IA
type: syntax
---

Deux paquets Python couvrent [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) hors appels à Gemini. `google-cloud-aiplatform` (version 1.165, `from google.cloud import aiplatform`) porte l'entraînement, le registre de modèles, les endpoints, les pipelines et Experiments. `google-cloud-agentplatform` (version 2.2, `import agentplatform`) porte Agent Runtime et le service d'évaluation, par un client `agentplatform.Client` ; une partie de la documentation écrit ces appels avec `vertexai.Client` et `client.agent_engines` [!DECONSEILLE] du paquet `google-cloud-aiplatform`, que le SDK signale comme déprécié au profit d'`agentplatform.Client`. Gemini lui-même s'appelle par le SDK `google-genai` (voir [SDK google-genai](#sdk-google-genai)).

### Initialisation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Fixer projet, région, bucket de travail | `aiplatform.init(project="PROJECT_ID", location="REGION", staging_bucket="gs://BUCKET")` | Valeurs par défaut de tous les appels suivants |
| Compte de service et réseau par défaut | `aiplatform.init(..., service_account="SA@PROJECT_ID.iam.gserviceaccount.com", network="projects/PROJECT_NUMBER/global/networks/VPC")` | Appliqués aux jobs lancés ensuite |
| Chiffrement CMEK par défaut | `aiplatform.init(..., encryption_spec_key_name="projects/PROJECT_ID/locations/REGION/keyRings/KR/cryptoKeys/KEY")` | Ressources créées chiffrées par cette clé |
| Rattacher les runs à une expérience | `aiplatform.init(..., experiment="churn")` | Crée l'expérience si elle n'existe pas |

### Entraînement

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Job depuis un script local | `aiplatform.CustomJob.from_local_script(display_name="train", script_path="train.py", container_uri=IMAGE_PREBUILT, requirements=["pandas"], machine_type="n2-standard-8")` | Script empaqueté dans le bucket de travail, exécuté dans un conteneur prédéfini |
| Job depuis une image maison | `aiplatform.CustomJob(display_name="train", worker_pool_specs=[{"machine_spec": {"machine_type": "n2-standard-8"}, "replica_count": 1, "container_spec": {"image_uri": "REGION-docker.pkg.dev/PROJECT_ID/ml/train:1.0", "args": ["--epochs=10"]}}])` | Contrôle total du conteneur ; plusieurs pools pour le distribué |
| Lancer le job | `job.run(service_account="SA@PROJECT_ID.iam.gserviceaccount.com", timeout=7200, sync=True)` | `sync=False` rend la main tout de suite ; `job.wait()` pour attendre |
| Lancer en Spot | `job.run(..., scheduling_strategy=custom_job.Scheduling.Strategy.SPOT)` (`from google.cloud.aiplatform.compat.types import custom_job`) | VM préemptibles moins chères ; prévoir des points de contrôle |
| Ajouter un GPU | `machine_type="g2-standard-8", accelerator_type="NVIDIA_L4", accelerator_count=1` | Quota GPU d'Agent Platform, distinct de celui de Compute Engine |
| Entraîner et inscrire au registre | `aiplatform.CustomContainerTrainingJob(display_name=..., container_uri=IMAGE_TRAIN, model_serving_container_image_uri=IMAGE_SERVE).run(model_display_name="churn", machine_type=...)` | Renvoie un `Model` inscrit au registre ; le code écrit dans `$AIP_MODEL_DIR` |
| Variante avec script Python | `aiplatform.CustomTrainingJob(display_name=..., script_path="train.py", container_uri=..., model_serving_container_image_uri=...)` | Même chaîne, sans image d'entraînement à construire |
| Recherche d'hyperparamètres | `aiplatform.HyperparameterTuningJob(display_name=..., custom_job=job, metric_spec={"auc": "maximize"}, parameter_spec={"lr": hpt.DoubleParameterSpec(min=1e-4, max=1e-1, scale="log")}, max_trial_count=20, parallel_trial_count=4).run()` | `from google.cloud.aiplatform import hyperparameter_tuning as hpt` ; le code rapporte la métrique par `cloudml-hypertune` |

### Registre de modèles

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Importer un modèle entraîné ailleurs | `aiplatform.Model.upload(display_name="churn", artifact_uri="gs://BUCKET/modeles/churn/", serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-6:latest")` | Nouveau `Model`, version 1 |
| Ajouter une version | `aiplatform.Model.upload(..., parent_model="projects/PROJECT_ID/locations/REGION/models/MODEL_ID", is_default_version=False, version_aliases=["candidat"])` | Nouvelle version sans toucher à l'alias `default` |
| Charger une version par alias | `aiplatform.Model("MODEL_ID@candidat")` (ou `@3` pour un numéro) | Sans suffixe : la version `default` |
| Lister les versions | `aiplatform.models.ModelRegistry("MODEL_ID").list_versions()` | ID, alias, dates de chaque version |
| Déplacer un alias | `registry.add_version_aliases(new_aliases=["prod"], version="3")`, `registry.remove_version_aliases(target_aliases=["prod"], version="2")` | L'alias pointe sur une seule version à la fois |
| Chercher un modèle | `aiplatform.Model.list(filter='display_name="churn"')` | Liste de `Model` |

### Endpoints

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un endpoint dédié | `endpoint = aiplatform.Endpoint.create(display_name="churn", dedicated_endpoint_enabled=True)` | Endpoint public avec son propre nom DNS ; incompatible avec VPC Service Controls |
| Déployer un modèle | `model.deploy(endpoint=endpoint, machine_type="n2-standard-4", min_replica_count=2, max_replica_count=5, traffic_percentage=100)` | Nœuds facturés en continu tant que le modèle est déployé |
| Journaliser requêtes et réponses | `Endpoint.create(..., enable_request_response_logging=True, request_response_logging_sampling_rate=0.1, request_response_logging_bq_destination_table="bq://PROJECT_ID.DATASET.TABLE")` | Échantillon dans BigQuery, pour le suivi de dérive |
| Déployer en canari | `nouveau.deploy(endpoint=endpoint, machine_type=..., traffic_percentage=10)` | 10 % vers le nouveau modèle, le reste réparti sur les existants |
| Régler la répartition | `endpoint.update(traffic_split={"DEPLOYED_ID_1": 90, "DEPLOYED_ID_2": 10})` | IDs de `endpoint.list_models()` ; total de 100 |
| Prédire | `endpoint.predict(instances=[[0.3, 12, 1]], use_dedicated_endpoint=True).predictions` | Format d'instance imposé par le conteneur de service |
| Retirer un modèle | `endpoint.undeploy(deployed_model_id="DEPLOYED_ID")`, `endpoint.undeploy_all()` | Arrête la facturation des nœuds de ce modèle |
| Supprimer l'endpoint | `endpoint.delete(force=True)` | `force=True` retire d'abord les modèles déployés |
| Retrouver un endpoint | `aiplatform.Endpoint("ENDPOINT_ID")`, `aiplatform.Endpoint.list(filter='display_name="churn"')` | Objet utilisable pour `predict` |

### Prédictions par lots

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lot depuis BigQuery | `model.batch_predict(job_display_name="churn-lot", bigquery_source="bq://PROJECT_ID.DATASET.clients", bigquery_destination_prefix="bq://PROJECT_ID.DATASET", machine_type="n2-standard-4", max_replica_count=10)` | Nouvelle table de prédictions ; aucun endpoint nécessaire |
| Lot depuis Cloud Storage | `model.batch_predict(..., gcs_source="gs://BUCKET/in/*.jsonl", instances_format="jsonl", gcs_destination_prefix="gs://BUCKET/out/")` | Fichiers de prédictions ; même région que le modèle exigée |
| Sans objet `Model` | `aiplatform.BatchPredictionJob.create(job_display_name=..., model_name="MODEL_ID@prod", ...)` | Même job, modèle désigné par nom ou alias |

### Pipelines et expériences

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Soumettre un pipeline compilé | `aiplatform.PipelineJob(display_name=..., template_path="pipeline.yaml", pipeline_root="gs://BUCKET/pipelines", parameter_values={...}).submit(service_account="SA@PROJECT_ID.iam.gserviceaccount.com")` | Run asynchrone ; `.run()` attend la fin |
| Désactiver le cache des étapes | `PipelineJob(..., enable_caching=False)` | Toutes les étapes s'exécutent à nouveau |
| Arrêter au premier échec | `PipelineJob(..., failure_policy="fast")` | Défaut `slow` : exécute tout ce qui peut encore l'être |
| Planifier | `job.create_schedule(display_name="hebdo", cron="TZ=Europe/Paris 0 3 * * 1", max_concurrent_run_count=1, service_account=...)` | Planification gérée par la plateforme |
| Démarrer un run d'expérience | `aiplatform.start_run("run-2026-09-24")` | Run rattaché à l'expérience de `init` ; `resume=True` pour reprendre |
| Journaliser paramètres et métriques | `aiplatform.log_params({"lr": 0.01, "depth": 6})`, `aiplatform.log_metrics({"auc": 0.91})` | Visibles et comparables dans la console |
| Courbe d'apprentissage | `aiplatform.log_time_series_metrics({"loss": 0.4}, step=10)` | Exige une instance TensorBoard associée à l'expérience |
| Journalisation automatique | `aiplatform.autolog()` | Capte paramètres et métriques de scikit-learn, XGBoost, Keras… |
| Clore le run, comparer | `aiplatform.end_run()`, `aiplatform.get_experiment_df("churn")` | DataFrame pandas, une ligne par run |

### Agent Runtime et évaluation (`agentplatform`)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Client | `client = agentplatform.Client(project="PROJECT_ID", location="REGION")` | Sous-services `runtimes`, `sessions`, `memory_banks`, `evals`, `prompts`… |
| Envelopper un agent ADK | `from agentplatform.frameworks import AdkApp` ; `app = AdkApp(agent=root_agent)` | Testable en local : `async for e in app.async_stream_query(user_id="u1", message="...")` |
| Déployer | `remote = client.runtimes.create(agent=app, config={"staging_bucket": "gs://BUCKET", "requirements": ["google-cloud-agentplatform[agent_engines,adk]"], "display_name": "support"})` | Ressource `reasoningEngines` ; `remote.api_resource.name` donne son nom complet |
| Identité, mise à l'échelle | `config={..., "identity_type": types.IdentityType.AGENT_IDENTITY, "min_instances": 0, "max_instances": 10, "env_vars": {"MODE": "prod"}}` | `from agentplatform import types` ; `service_account=` pour un compte désigné |
| Déployer depuis des sources | `client.runtimes.create(config={"source_packages": ["agent/"], "entrypoint_module": "agent.agent", "entrypoint_object": "root_agent", "requirements_file": "agent/requirements.txt"})` | Pas d'objet sérialisé : le service construit l'agent depuis le code |
| Récupérer et appeler | `agent = client.runtimes.get(name="projects/PROJECT_ID/locations/REGION/reasoningEngines/RESOURCE_ID")`, puis `agent.async_stream_query(user_id=..., message=...)` | `agent.operation_schemas()` liste les méthodes exposées |
| Mettre à jour, lister, supprimer | `client.runtimes.update(name=..., agent=app, config={...})`, `client.runtimes.list()`, `client.runtimes.delete(name=..., force=True)` | `force=True` supprime aussi sessions et mémoires |
| Évaluer des réponses | `client.evals.evaluate(dataset=df, metrics=[types.RubricMetric.GENERAL_QUALITY, types.RubricMetric.GROUNDING])` | `df` pandas avec colonnes `prompt`, `response` ; `pip install "google-cloud-agentplatform[evaluation]"` |
| Générer les réponses à évaluer | `client.evals.run_inference(src=df, model="gemini-3.5-flash")` (ou `agent=` un nom de ressource) | Jeu d'évaluation complété, à passer à `evaluate` |

```python
from google.cloud import aiplatform

aiplatform.init(project="PROJECT_ID", location="REGION", staging_bucket="gs://BUCKET",
                experiment="churn")

aiplatform.start_run("xgb-depth6")
aiplatform.log_params({"max_depth": 6, "eta": 0.1})
# ... entraînement local ...
aiplatform.log_metrics({"auc": 0.91})
aiplatform.end_run()

v2 = aiplatform.Model.upload(
    display_name="churn", artifact_uri="gs://BUCKET/modeles/churn/v2/",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.2-1:latest",
    parent_model="projects/PROJECT_ID/locations/REGION/models/MODEL_ID",
    is_default_version=False, version_aliases=["candidat"],
)
endpoint = aiplatform.Endpoint("ENDPOINT_ID")
v2.deploy(endpoint=endpoint, machine_type="n2-standard-4",
          min_replica_count=2, max_replica_count=4, traffic_percentage=10)
```

> [!WARNING]
> Un modèle déployé facture ses nœuds jour et nuit, même sans requête. Pour un besoin quotidien, `batch_predict` coûte une fraction du prix ; en fin d'essai, `endpoint.undeploy_all()` ou `endpoint.delete(force=True)`.

Contexte : [Entraîner et servir un modèle](#entrainer-et-servir), [MLOps](#mlops), [Déployer un agent](#deployer-un-agent), [Évaluer et sécuriser](#evaluer-et-securiser).
