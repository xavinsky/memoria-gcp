---
title: Entraîner et servir un modèle
---

Un modèle maison passe par trois étapes sur [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) : un **job d'entraînement** exécute un conteneur sur des machines louées le temps du job, **Model Registry** garde les versions du modèle produit, puis le modèle répond soit **en ligne** depuis un *endpoint*, soit **par lots** dans un job asynchrone. Deux décisions pèsent sur le coût : comment obtenir les accélérateurs à l'entraînement, et combien de nœuds restent allumés pour servir.

![Architecture de référence : entraîner, enregistrer, servir](../../svg/entrainer-servir.svg)

Les noms changent selon l'interface. La documentation parle de **Managed Training** et de *serverless training* (ex-Vertex AI Training, *custom training*), la console d'**Agent Platform** ; le SDK Python reste le paquet `google-cloud-aiplatform`, importé en `from google.cloud import aiplatform`, et l'API se nomme `aiplatform.googleapis.com`. Pour des données déjà dans BigQuery et un modèle classique, [BigQuery ML](#bigquery-ml) évite tout ce circuit (voir [Choisir une approche ML](#choisir-une-approche-ml)).

## Où entraîner

| Option | Ce qu'on fournit | Capacité | Facturation | Pour quoi |
|---|---|---|---|---|
| **Job serverless** (`CustomJob`) | Script Python dans un conteneur prédéfini, ou image personnalisée | Machines créées au lancement, supprimées à la fin | Durée du job, par machine et accélérateur, plus frais de gestion | Cas général : expérimentation, réentraînement périodique |
| **Ressource persistante** | Les mêmes jobs, envoyés sur un pool gardé allumé | Garantie tant que le pool existe, démarrage sans provisionnement | Tout le temps où le pool tourne, job ou pas | Beaucoup de jobs courts, capacité critique en période de pointe |
| **Managed Training Clusters** | Jobs Slurm, recettes Llama et Gemma | Cluster réservé (A3, A4…), réparation automatique des nœuds | Capacité réservée | Pré-entraînement et réglage à grande échelle ; accès par l'équipe commerciale |
| **Ray on Agent Platform** | Code Ray existant | Cluster Ray gardé jusqu'à sa suppression | Nœuds du cluster | Équipe déjà sur Ray, calcul distribué Python |
| **[GKE](#gke)** | Manifestes, Kueue, JobSet | Pools de nœuds GPU ou TPU que l'on gère | Nœuds (Spot possible) | Parc d'accélérateurs mutualisé entre équipes, portabilité Kubernetes |
| **[Batch](#batch)** ou VM [Compute Engine](#compute-engine), [Cloud TPU](#cloud-tpu) | Script ou conteneur, tout le reste à la main | Instances que l'on obtient soi-même | Ressources Compute Engine seules | Entraînement ponctuel sans outillage ML, contrôle complet de la VM |

Le job serverless couvre la plupart des besoins. Il se décline en trois ressources : `CustomJob` exécute le code et laisse les artefacts dans Cloud Storage ; `HyperparameterTuningJob` relance le code en *trials* avec des valeurs d'hyperparamètres différentes ; `CustomTrainingJob` (un *training pipeline*) enchaîne le job et l'import du modèle dans le registre.

- **Conteneur.** Un conteneur prédéfini (TensorFlow, PyTorch, scikit-learn, XGBoost) reçoit un fichier Python ou une distribution source ; une image personnalisée dans [Artifact Registry](#artifact-registry) accepte n'importe quel cadre et version. Le code lit ses données dans BigQuery ou Cloud Storage, et écrit le modèle dans le dossier donné par la variable `AIP_MODEL_DIR`.
- **Distribué.** Plusieurs *worker pools* dont l'ordre fixe le rôle : le premier porte le réplica principal (`replicaCount` à 1), le deuxième les workers, le troisième les serveurs de paramètres ou le *Reduction Server* (algorithme *all-reduce* pour GPU NVIDIA), le quatrième les évaluateurs. Le code lit la topologie dans `CLUSTER_SPEC` ou `TF_CONFIG`. Sur TPU VM, un seul pool d'un seul réplica.
- **Réglage d'hyperparamètres.** On déclare les plages de valeurs et la métrique à optimiser ; le code reçoit chaque valeur en argument de ligne de commande et renvoie la métrique par le paquet `cloudml-hypertune`. La recherche est bayésienne par défaut (grille ou aléatoire au choix), bornée par un nombre maximal de *trials* et de *trials* parallèles ; la facture suit leur durée cumulée.

### Obtenir les accélérateurs

| Stratégie (`scheduling.strategy`) | Principe | Contraintes |
|---|---|---|
| À la demande | Machines prises au lancement | Échec si la zone manque de capacité |
| `SPOT` | Capacité excédentaire à prix réduit, reprise à tout moment | Job relancé jusqu'à six fois après une préemption : écrire des points de contrôle ; pas de pod TPU |
| `FLEX_START` (Dynamic Workload Scheduler) | Le job attend que tous ses GPU soient libres ensemble, puis s'exécute sans interruption | GPU L4, A100, H100, H200 ou B200 ; job de 7 jours au plus ; attente bornée par `maxWaitDuration` (1 jour par défaut) ; consomme le quota `preemptible` |
| Réservation Compute Engine | Capacité réservée consommée par le job | Propriétés identiques à la réservation (type de machine exact) ; réservation facturée qu'on l'utilise ou non |

> [!WARNING]
> Les quotas GPU d'Agent Platform sont distincts de ceux de Compute Engine, par région et par modèle, séparés entre entraînement et service. Sur H100, le quota par défaut vaut 0 dans les régions qui en proposent, et le modèle n'existe pas dans la plupart des autres. Demander l'augmentation avant d'écrire le pipeline, et choisir la région d'après la [disponibilité des accélérateurs](#cloud-gpus).

À accélérateurs et contraintes de résidence égaux, une région à forte part d'énergie décarbonée ([CFE publiée par région](https://cloud.google.com/sustainability/region-carbon)) réduit l'empreinte d'un entraînement ; un job par lots peut aussi être lancé aux heures où cette part est la plus haute ([Well-Architected Framework, efficacité énergétique de l'IA](https://docs.cloud.google.com/architecture/framework/sustainability/ai-ml-energy-efficiency)). Le rapport [Carbon Footprint](#carbon-footprint) mesure ensuite les émissions par projet et par service.

## Model Registry

Le registre donne une ressource `Model` par modèle et une **version** par import. Chaque version porte un artefact et le conteneur qui le servira.

- **Alias.** Référence nommée et mobile vers une version, comme une étiquette Docker ou une branche Git : `prod`, `candidat`. La première version reçoit l'alias `default`, qui doit toujours désigner une version : c'est elle qu'on obtient sans préciser de numéro. Un alias déjà posé ailleurs se déplace sur la nouvelle version. Les *labels*, eux, classent sans désigner.
- **Sources.** Modèles importés depuis Cloud Storage, modèles AutoML, et modèles [BigQuery ML](#bigquery-ml) inscrits sans export.
- **Depuis une version** : évaluation, déploiement sur un endpoint, job d'inférence par lots.

## Servir en ligne

Un modèle se **déploie** sur un endpoint : la plateforme lui attache des nœuds (`DeployedModel`) qui restent allumés. Un endpoint peut porter plusieurs versions et répartir le trafic entre elles, pour un canari ou un test A/B.

| Type d'endpoint | Réseau | Délai max | Charge utile | Autres différences |
|---|---|---|---|---|
| **Public dédié** (recommandé) | Internet, plan réseau isolé | Jusqu'à 1 h | 10 Mo | gRPC, *streaming* SSE, API Chat Completions pour Model Garden ; pas de VPC Service Controls |
| **Public partagé** | Internet, plan partagé | 60 s | 1,5 Mo | 30 000 requêtes par minute ; seul type accepté pour Gemini réglé et AutoML |
| **Privé dédié par [Private Service Connect](#private-service-connect)** (recommandé) | Règle de transfert dans le VPC client, plusieurs projets consommateurs | Jusqu'à 1 h | 10 Mo | gRPC, *streaming*, VPC Service Controls |
| **Privé** (accès aux services privés) | Appairage VPC | 60 s | 10 Mo | HTTP seul, pas de répartition de trafic ni de journaux d'accès |

- **Autoscaling.** Entre `min_replica_count` et `max_replica_count`, sur une cible de 60 % d'utilisation CPU ou GPU (la plus haute des deux), ou sur des métriques dédiées : nombre de requêtes, cache KV et file d'attente de vLLM, taille d'un abonnement Pub/Sub. Le minimum vaut 1.
- [!PREVERSION] **Mise à zéro** (*Scale To Zero*) : `min_replica_count=0` sur tout endpoint sauf le public partagé, un modèle par endpoint. Une requête arrivée pendant la remontée reçoit un **429** et n'est pas traitée ; un modèle resté à zéro pendant 30 jours est retiré de l'endpoint.
- **Facturation** au nœud-heure, par tranches de 30 secondes, dès qu'un modèle est déployé et même sans requête. Spot et réservations s'appliquent aussi au service.
- **Co-hébergement.** Un `DeploymentResourcePool` fait partager une même VM à plusieurs modèles peu sollicités ; ils se disputent alors CPU et mémoire. Sur GKE, un même GPU se partage entre conteneurs par [GPU multi-instance](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/timesharing-gpus) (jusqu'à sept partitions isolées), par partage de temps ou par NVIDIA MPS.

## Servir par lots

Un `BatchPredictionJob` s'adresse au modèle **sans le déployer** : il lit des JSON Lines, TFRecord, CSV, une liste de fichiers ou une table BigQuery, et écrit dans Cloud Storage ou BigQuery. Entrée, sortie et modèle doivent être dans la même région ou multirégion. Le job n'a pas d'autoscaling : le nombre de nœuds est fixé au départ (`starting_replica_count`), et rien n'est facturé entre deux jobs. Préférer JSON Lines ou BigQuery au CSV, que la plateforme ne découpe pas entre les nœuds.

## Modèles ouverts et alternatives

Un modèle ouvert de [Model Garden](#model-garden) (Gemma, Llama, Qwen, Hub Hugging Face) se déploie sur un endpoint dédié avec un conteneur de service fourni, vLLM le plus souvent. Deux autres hôtes se présentent, et pour Gemini ou un modèle partenaire l'appel à l'API gérée évite toute infrastructure (voir [Choisir un modèle](#choisir-un-modele)).

| Solution | Latence | Trafic adapté | Coût au repos | Contrôle |
|---|---|---|---|---|
| **Endpoint Agent Platform** | Millisecondes, nœuds chauds | Continu | Au moins un nœud en permanence | Conteneur prédéfini ou personnalisé, répartition du trafic, journaux, surveillance intégrée |
| [!PREVERSION] **Endpoint avec mise à zéro** | Premier appel refusé (429) le temps de la remontée | Heures ouvrées, longues pauses | Nul | Risque de pénurie au redémarrage sans réservation |
| **Inférence par lots** | Minutes à heures | Volumes accumulés | Nul | Nœuds fixés au lancement |
| **[Cloud Run](#cloud-run) avec GPU** | Démarrage d'environ 5 s, plus le chargement du modèle | Intermittent, par pics | Nul (montée à zéro) | Un GPU par instance, L4 (24 Go) ou RTX PRO 6000 (96 Go), dans quelques régions ; conteneur à écrire |
| **[GKE](#gke)** avec vLLM | Millisecondes | Fort et régulier, plusieurs modèles | Nœuds du pool (Spot possible) | Total : GKE Inference Gateway, HPA sur métriques personnalisées, LoRA ; un cluster à exploiter |
| **API gérée** (modèle en tant que service) | Variable, sans infrastructure | Tous | Nul, facturé aux jetons | Catalogue imposé |

- **Quantification.** Des poids en 8 ou 4 bits réduisent la mémoire GPU nécessaire : la documentation GKE sert ainsi Llama 2 13B (GPTQ) ou Gemma 7B (AWQ) sur un seul L4 au lieu de deux. La qualité peut baisser : la mesurer sur le jeu d'évaluation avant de choisir le matériel ([bonnes pratiques d'inférence sur GKE](https://docs.cloud.google.com/kubernetes-engine/docs/best-practices/machine-learning/inference/llm-optimization)).
- **Dimensionnement.** Sur GKE, [Inference Quickstart](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/machine-learning/inference/inference-quickstart) (`gcloud container ai profiles list`) propose, par modèle, des configurations mesurées par Google (accélérateur, serveur de modèle, latence, débit, coût) et génère les manifestes, ce qui évite de tester chaque combinaison à la main.

## Exemple avec le SDK Python

Entraînement en Spot dans une image maison, import dans le registre avec l'alias `candidat`, déploiement sur un endpoint dédié, puis nettoyage. Les conteneurs prédéfinis d'entraînement ont une date de fin de disponibilité (consulter [la liste](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/training/pre-built-containers)) : une image personnalisée qui épingle la version de scikit-learn du conteneur de service évite le problème.

```python
from google.cloud import aiplatform
from google.cloud.aiplatform.compat.types import custom_job

aiplatform.init(project="PROJECT_ID", location="REGION", staging_bucket="gs://BUCKET")

job = aiplatform.CustomContainerTrainingJob(
    display_name="churn-train",
    # Image maison : scikit-learn 1.6, écrit model.joblib dans $AIP_MODEL_DIR
    container_uri="REGION-docker.pkg.dev/PROJECT_ID/ml/churn-train:1.0",
    model_serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-6:latest",
)
model = job.run(
    model_display_name="churn",
    model_version_aliases=["candidat"],
    machine_type="n2-standard-8",
    scheduling_strategy=custom_job.Scheduling.Strategy.SPOT,
)

endpoint = aiplatform.Endpoint.create(display_name="churn", dedicated_endpoint_enabled=True)
model.deploy(endpoint=endpoint, machine_type="n2-standard-4",
             min_replica_count=1, max_replica_count=3, traffic_percentage=100)

reponse = endpoint.predict(instances=[[0.3, 12, 1]], use_dedicated_endpoint=True)
print(reponse.predictions)

endpoint.delete(force=True)  # retire les modèles déployés : les nœuds cessent d'être facturés
```

Pour un GPU, ajouter `accelerator_type="NVIDIA_L4", accelerator_count=1` avec `machine_type="g2-standard-8"`, à `run()` comme à `deploy()`. Le module `vertexai` du même paquet porte les modèles ouverts (`from vertexai import model_garden`, puis `model_garden.OpenModel(...).deploy()`) ; les appels à Gemini passent par le SDK `google-genai` (voir [Appeler Gemini](#appeler-gemini)).

## Pièges

- **Endpoint oublié.** Un modèle déployé facture ses nœuds jour et nuit, qu'il reçoive des requêtes ou non ; seul le retrait du modèle arrête la facture. Pour des prédictions quotidiennes, le job par lots coûte une fraction du prix.
- **Quota calculé sur le maximum.** L'autoscaling est plafonné par le quota de service : la somme des `max_replica_count` du projet doit tenir dans le quota par CPU et par GPU, sinon certains déploiements ne montent plus en charge. Un réplica `a2-highgpu-2g` compte 24 CPU et 2 GPU.
- **Région.** Données, job, modèle et endpoint vivent dans une région ; le job par lots refuse une entrée située ailleurs, et chaque GPU n'existe que dans certaines régions, pour l'entraînement comme pour le service.
- **Spot sans point de contrôle.** Un job préempté repart du début s'il n'a rien sauvegardé : écrire l'état du modèle dans Cloud Storage à intervalle régulier.
- **Ressources gardées allumées.** Ressource persistante, cluster Ray, réservation : tous se facturent tant qu'ils existent. Les supprimer en fin de campagne, ou activer l'autoscaling de la ressource persistante.
- **Endpoint public dédié et VPC Service Controls.** Ils sont incompatibles : dans un périmètre, passer par un endpoint privé Private Service Connect.
- **Un seul nœud en production.** Avec `min_replica_count=1`, le modèle tient sur une VM, donc dans une zone. Pour la haute disponibilité, la documentation recommande au moins deux nœuds ([configurer le calcul de l'inférence](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/predictions/configure-compute)).
- **Job sans compte de service.** Sans `service_account`, le conteneur d'entraînement s'exécute avec l'agent de service *Custom Code* du projet, qui accède à BigQuery et à Cloud Storage. Passer un compte de service dédié à `run()` borne le job aux seules données qu'il doit lire ([compte de service personnalisé](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/custom-service-account)).
- **Expériences et production dans le même projet.** Les quotas d'accélérateurs sont par projet : une campagne d'expériences peut prendre tous les GPU dont le réentraînement de production a besoin. Séparer les projets (`ml-dev`, `ml-staging`, `ml-prod`), ainsi que les buckets et datasets d'expérimentation ([Well-Architected Framework, performance](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/performance-optimization)).

## Alternatives en logiciel libre

- **Kubeflow Trainer** (Apache 2.0) : jobs d'entraînement distribués PyTorch, JAX ou DeepSpeed sur Kubernetes, l'équivalent de `CustomJob` et de ses *worker pools* ; **Katib** (Apache 2.0) règle les hyperparamètres par recherche bayésienne, en grille ou aléatoire.
- **Kueue** (Apache 2.0) : files d'attente et quotas d'accélérateurs partagés entre équipes, qui n'admettent un job que lorsque toutes ses ressources sont libres, le principe de `FLEX_START`.
- **Ray** (Apache 2.0) avec l'opérateur **KubeRay** (Apache 2.0) : Ray Train, Tune et Serve sur son propre cluster Kubernetes, à la place de Ray on Agent Platform.
- **Slurm** (GPL v2) : l'ordonnanceur des Managed Training Clusters, à installer sur ses propres nœuds GPU.
- **SkyPilot** (Apache 2.0) : lance un entraînement ou un service là où des GPU sont disponibles, cloud ou cluster, avec instances Spot et reprise automatique après préemption.
- **MLflow** (Apache 2.0) : registre de modèles avec versions et alias, l'équivalent de Model Registry.
- **KServe** (Apache 2.0) : endpoints d'inférence sur Kubernetes, mise à l'échelle jusqu'à zéro par Knative et déploiement canari par répartition du trafic ; **vLLM** (Apache 2.0) pour les grands modèles de langage, **Triton Inference Server** (BSD 3-Clause) pour plusieurs cadres et modèles sur un même GPU.
