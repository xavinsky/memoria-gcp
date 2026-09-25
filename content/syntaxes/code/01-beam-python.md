---
title: Apache Beam en Python
subgroup: Données
type: syntax
---

Appels du SDK Apache Beam (`pip install "apache-beam[gcp]"`, version 2.76), exécutés en local par le *DirectRunner* ou sur [Dataflow](#dataflow). Imports supposés : `import apache_beam as beam`, `from apache_beam.transforms import window, trigger`.

### Options du pipeline

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Construire les options depuis la ligne de commande | `options = PipelineOptions(argv)` (`from apache_beam.options.pipeline_options import PipelineOptions`) | Chaque `--option=valeur` est lue ; une option inconnue est ignorée avec un simple avertissement : une faute de frappe passe inaperçue |
| Lancer sur Dataflow | `--runner=DataflowRunner --project=PROJECT_ID --region=REGION --temp_location=gs://BUCKET/tmp` | Job Dataflow ; sans `--temp_location`, le lancement échoue |
| Exécuter en local | `--runner=DirectRunner` (valeur par défaut) | Exécution sur le poste, pour les tests ; le DirectRunner confie le pipeline au runner local *Prism* quand il le prend en charge ; lent sur gros volumes |
| Mode flux | `--streaming` | Obligatoire pour une source non bornée comme Pub/Sub |
| Compte de service des workers | `--service_account_email=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com` | Remplace le compte Compute Engine par défaut ; il lui faut `roles/dataflow.worker` |
| Sous-réseau des workers | `--subnetwork=regions/REGION/subnetworks/SUBNET` | Ajouter l'URL complète du projet hôte pour un VPC partagé |
| Workers sans IP publique | `--no_use_public_ips` ; en argument Python, `PipelineOptions(use_public_ips=False)` | Il faut alors l'accès privé à Google, et Cloud NAT pour sortir vers Internet. `no_use_public_ips=True` en argument Python est ignoré sans erreur |
| Plafonner l'autoscaling | `--max_num_workers=20` (`--num_workers=` pour le départ) | Borne le coût ; aussi un quota à prévoir |
| Dépendances Python | `--requirements_file=requirements.txt` ou `--setup_file=./setup.py` | Installées sur chaque worker au démarrage ; une image personnalisée (`--sdk_container_image=`) démarre plus vite |
| Garder les imports globaux | `--save_main_session` | Les imports du module principal sont disponibles dans les `DoFn` |
| Option expérimentale | `--experiments=OPTION` (répétable) | Ex. `--experiments=no_use_multiple_sdk_containers` |
| Option de service Dataflow | `--dataflow_service_options=OPTION` | Ex. `enable_hot_key_logging`, `streaming_mode_at_least_once`, `enable_google_cloud_profiler` |
| Remplacer un job de flux en cours | `--update --job_name=NOM_EXISTANT` (`--transform_name_mapping='{"Ancien":"Nouveau"}'`) | Job de remplacement qui reprend l'état ; noms d'étapes stables exigés |
| Lot à coût réduit | `--flexrs_goal=COST_OPTIMIZED` | FlexRS : démarrage différé jusqu'à 6 h, mélange de VM préemptibles et standard |

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(
    runner="DataflowRunner", project="PROJECT_ID", region="REGION",
    temp_location="gs://BUCKET/tmp", job_name="ventes-quotidiennes",
    service_account_email="dataflow@PROJECT_ID.iam.gserviceaccount.com",
    subnetwork="regions/REGION/subnetworks/SUBNET", use_public_ips=False,
    max_num_workers=10, save_main_session=True,
)
with beam.Pipeline(options=options) as p:   # la sortie du bloc lance le pipeline et attend sa fin
    (p | beam.io.ReadFromText("gs://BUCKET/in/*.csv", skip_header_lines=1)
       | beam.Map(lambda ligne: ligne.split(","))
       | beam.Map(lambda champs: ",".join(champs[:3]))
       | beam.io.WriteToText("gs://BUCKET/out/ventes", file_name_suffix=".csv"))
```

### Transformations de base

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer une collection en mémoire | `p \| beam.Create([1, 2, 3])` | `PCollection` bornée ; pratique pour les tests |
| Transformer un élément en un autre | `\| beam.Map(fn)`, `\| beam.MapTuple(lambda k, v: ...)` | Un élément en sortie par élément en entrée |
| Transformer un élément en zéro ou plusieurs | `\| beam.FlatMap(lambda ligne: ligne.split())` | La fonction renvoie un itérable, aplati |
| Filtrer | `\| beam.Filter(lambda x: x["montant"] > 0)` | Garde les éléments pour lesquels la fonction est vraie |
| Nommer une étape | `\| "Nettoyer" >> beam.Map(fn)` | Nom visible dans le graphe Dataflow ; unique, et stable pour `--update` |
| Regrouper par clé | `\| beam.GroupByKey()` | `(clé, itérable de valeurs)` ; en flux, exige une fenêtre ou un déclencheur |
| Agréger par clé | `\| beam.CombinePerKey(sum)` | `(clé, total)`, avec pré-agrégation sur chaque worker, bien moins de données échangées que `GroupByKey` |
| Agréger toute la collection | `\| beam.CombineGlobally(sum)` | Un seul élément ; en flux fenêtré, ajouter `.without_defaults()` |
| Agrégats prêts à l'emploi | `beam.combiners.Count.PerKey()`, `Mean.PerKey()`, `Top.Of(10)`, `Count.Globally()` | Module `beam.combiners` |
| Dédoublonner | `\| beam.Distinct()` | Éléments uniques (par fenêtre) |
| Fusionner des collections | `(pc1, pc2) \| beam.Flatten()` | Une collection ; mêmes types et fenêtrage |
| Jointure par clé | `{"cmd": pc1, "cli": pc2} \| beam.CoGroupByKey()` | `(clé, {"cmd": [...], "cli": [...]})` |
| Répartir en N collections | `pc \| beam.Partition(lambda x, n: 0 if x["pays"] == "FR" else 1, 2)` | Tuple de 2 `PCollection` |
| Casser la fusion d'étapes | `\| beam.Reshuffle()` | Redistribue le travail après un `FlatMap` qui démultiplie les éléments |
| Clé chaude dans un agrégat | `beam.CombinePerKey(sum).with_hot_key_fanout(16)` | Pré-agrège une clé surreprésentée sur plusieurs workers |

### ParDo, entrées annexes et sorties multiples

```python
class Enrichir(beam.DoFn):
    def setup(self):                      # une fois par instance : client, modèle, connexion
        from google.cloud import storage
        self.client = storage.Client()

    def process(self, element, taux):
        if element["devise"] not in taux:
            yield beam.pvalue.TaggedOutput("rejets", element)   # sortie secondaire
            return
        yield {**element, "montant_eur": element["montant"] * taux[element["devise"]]}

    def teardown(self):                   # au mieux : pas appelé si le worker s'arrête brutalement
        self.client.close()

taux = p | "Taux" >> beam.Create([("USD", 0.92), ("GBP", 1.17)])
resultat = (ventes
            | beam.ParDo(Enrichir(), taux=beam.pvalue.AsDict(taux))
                  .with_outputs("rejets", main="ok"))
resultat.ok | "EcrireOK" >> beam.io.WriteToText("gs://BUCKET/out/ok")
resultat.rejets | "EcrireRejets" >> beam.io.WriteToText("gs://BUCKET/out/rejets")
```

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Entrée annexe en dictionnaire | `beam.ParDo(fn, taux=beam.pvalue.AsDict(pc_paires))` | Dictionnaire complet passé à chaque appel ; doit tenir en mémoire |
| Entrée annexe en liste, en valeur unique | `beam.pvalue.AsList(pc)`, `beam.pvalue.AsSingleton(pc)` | `AsSingleton` échoue si la collection a plusieurs éléments, ou aucun sans `default_value` |
| Sortie secondaire | `yield beam.pvalue.TaggedOutput("rejets", x)` puis `.with_outputs("rejets", main="ok")` | Collections `resultat.ok` et `resultat.rejets` : la file d'erreurs du pipeline |
| Regrouper les appels par lot | `def start_bundle(self)` / `def finish_bundle(self)` | Début et fin de chaque lot d'éléments (*bundle*) |
| Lire l'horodatage ou la fenêtre | `def process(self, el, ts=beam.DoFn.TimestampParam, w=beam.DoFn.WindowParam)` | Horodatage d'événement et fenêtre de l'élément |

### Entrées et sorties

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lire des fichiers texte | `beam.io.ReadFromText("gs://BUCKET/in/*.csv", skip_header_lines=1)` | Une ligne par élément ; motif glob accepté |
| Écrire des fichiers texte | `beam.io.WriteToText("gs://BUCKET/out/res", file_name_suffix=".json", num_shards=0)` | Fichiers `res-00000-of-000NN.json` ; `num_shards=0` laisse le service choisir |
| Lire du Parquet | `beam.io.ReadFromParquet("gs://BUCKET/in/*.parquet", columns=["id", "montant"])` | Un dictionnaire par ligne ; `columns` limite la lecture |
| Lire un abonnement Pub/Sub | `beam.io.ReadFromPubSub(subscription="projects/PROJECT_ID/subscriptions/SUBSCRIPTION")` | `bytes` par message ; mode flux exigé |
| Garder les attributs du message | `ReadFromPubSub(..., with_attributes=True)` | Objets `PubsubMessage` (`.data`, `.attributes`, `.message_id`) |
| Horodater par l'heure de l'événement | `ReadFromPubSub(..., timestamp_attribute="ts")` | L'attribut `ts` (millisecondes epoch ou RFC 3339) fixe l'horodatage ; sinon, heure de publication |
| Dédoublonner à la lecture | `ReadFromPubSub(..., id_label="event_id")` | Dédoublonne sur l'ID métier porté par cet attribut (DataflowRunner) |
| Publier dans Pub/Sub | `beam.io.WriteToPubSub(topic="projects/PROJECT_ID/topics/TOPIC")` | Les éléments doivent être des `bytes` (ou `PubsubMessage` avec `with_attributes=True`) |
| Lire une requête BigQuery | `beam.io.ReadFromBigQuery(query="SELECT ...", use_standard_sql=True)` | Dictionnaires ; **sans `use_standard_sql=True`, la requête est lue en SQL ancien** |
| Lire une table par la Storage Read API | `ReadFromBigQuery(table="PROJECT_ID:DATASET.TABLE", method=ReadFromBigQuery.Method.DIRECT_READ, selected_fields=["id"], row_restriction="pays = 'FR'")` | Pas d'export intermédiaire dans Cloud Storage ; `EXPORT` est la méthode par défaut |
| Écrire dans BigQuery | `beam.io.WriteToBigQuery("PROJECT_ID:DATASET.TABLE", schema="id:STRING,montant:NUMERIC,ts:TIMESTAMP", method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API)` | Écriture par la Storage Write API, exactement une fois ; `FILE_LOADS` par défaut en lot, `STREAMING_INSERTS` par défaut en flux |
| Créer la table si besoin, écraser | `create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE` | Défauts : `CREATE_IF_NEEDED` (schéma requis) et `WRITE_APPEND` |
| Écrire au moins une fois, moins cher | `WriteToBigQuery(..., method=...STORAGE_WRITE_API, use_at_least_once=True)` | Doublons possibles ; à associer au mode `streaming_mode_at_least_once` |
| Fréquence de validation en flux | `WriteToBigQuery(..., triggering_frequency=5)` | Secondes entre deux validations : quelques secondes en Storage Write API, plutôt 300 à 600 en `FILE_LOADS` (quota de jobs de chargement) |

### Fenêtres, déclencheurs, horodatages

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Fenêtre fixe | `\| beam.WindowInto(window.FixedWindows(60))` | Fenêtres disjointes d'une minute, sur l'heure de l'événement |
| Fenêtre glissante | `\| beam.WindowInto(window.SlidingWindows(size=300, period=60))` | Fenêtres de 5 min recalculées chaque minute ; un élément dans 5 fenêtres |
| Fenêtre de session | `\| beam.WindowInto(window.Sessions(gap_size=600))` | Fermée après 10 min sans événement, par clé |
| Résultats provisoires et corrections | `trigger=trigger.AfterWatermark(early=trigger.AfterProcessingTime(30), late=trigger.AfterCount(1))` | Un résultat toutes les 30 s avant le filigrane, un par élément tardif ensuite |
| Accepter les retards | `allowed_lateness=3600` | Fenêtre gardée 1 h après le filigrane ; défaut 0 : les éléments tardifs sont jetés |
| Mode d'accumulation | `accumulation_mode=trigger.AccumulationMode.ACCUMULATING` (ou `DISCARDING`) | Réémet le total cumulé, ou seulement le delta depuis le résultat précédent ; obligatoire avec un déclencheur |
| Émettre toutes les N secondes en fenêtre globale | `trigger=trigger.Repeatedly(trigger.AfterProcessingTime(60))` | Résultat périodique sans fin de fenêtre |
| Horodater un élément | `\| beam.Map(lambda e: window.TimestampedValue(e, e["ts_epoch"]))` | Horodatage d'événement en secondes epoch, à faire avant `WindowInto` en lot |

```python
comptes = (
    p
    | beam.io.ReadFromPubSub(subscription="projects/PROJECT_ID/subscriptions/SUBSCRIPTION",
                             timestamp_attribute="ts")
    | beam.Map(json.loads)
    | beam.WindowInto(
        window.FixedWindows(60),
        trigger=trigger.AfterWatermark(late=trigger.AfterCount(1)),
        allowed_lateness=600,
        accumulation_mode=trigger.AccumulationMode.ACCUMULATING,
    )
    | beam.Map(lambda e: (e["page"], 1))
    | beam.CombinePerKey(sum)
    | beam.Map(lambda kv: {"page": kv[0], "vues": kv[1]})
    | beam.io.WriteToBigQuery("PROJECT_ID:DATASET.vues_minute", schema="page:STRING,vues:INTEGER",
                             method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API,
                             triggering_frequency=5)
)
```

> [!WARNING]
> En `ACCUMULATING`, chaque correction tardive ajoute une ligne avec le total mis à jour : dans BigQuery, ne garder que la dernière ligne de chaque fenêtre. Voir [Streaming](#streaming).

### Lancer et piloter

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Construire un modèle Flex | `gcloud dataflow flex-template build gs://BUCKET/modeles/job.json --image-gcr-path=REGION-docker.pkg.dev/PROJECT_ID/REPO/job:TAG --sdk-language=PYTHON --flex-template-base-image=PYTHON3 --py-path=. --env=FLEX_TEMPLATE_PYTHON_PY_FILE=pipeline.py --env=FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE=requirements.txt --metadata-file=metadata.json` | Image construite par Cloud Build et fichier de spécification JSON dans Cloud Storage |
| Lancer un modèle Flex | `gcloud dataflow flex-template run JOB_NAME --template-file-gcs-location=gs://BUCKET/modeles/job.json --region=REGION --parameters=input=gs://BUCKET/in/*.csv` | Job lancé sans environnement Python local |
| Remplacer un job de flux par un modèle | `gcloud dataflow flex-template run JOB_NAME ... --update --transform-name-mappings=Ancien=Nouveau` | Même nom de job et même région ; `--additional-experiments=graph_validate_only` vérifie sans remplacer |
| Arrêter un job de flux proprement | `gcloud dataflow jobs drain JOB_ID --region=REGION` | Finit les fenêtres en cours sans lire de nouveaux messages |
| Arrêter immédiatement | `gcloud dataflow jobs cancel JOB_ID --region=REGION` | Données en vol perdues |

> [!TIP]
> Tester les transformations avec `TestPipeline` et `assert_that(sortie, equal_to([...]))` (`apache_beam.testing`) sur le DirectRunner : aucun job, aucun coût, et les erreurs de sérialisation apparaissent avant le déploiement.

Contexte : [Dataflow](#dataflow), [Streaming](#streaming), [Batch : ETL ou ELT](#batch-etl-elt), [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).
