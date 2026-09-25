---
title: "Streaming : Pub/Sub, Dataflow, BigQuery"
---

Le pipeline de flux de référence sur Google Cloud tient en trois services : [Pub/Sub](#pubsub) reçoit les événements et absorbe les pics, [Dataflow](#dataflow) les transforme et les agrège par fenêtres de temps, [BigQuery](#bigquery) les rend interrogeables quelques secondes plus tard. Tout l'enjeu de conception est ailleurs : **quand émettre un résultat** alors que les données arrivent en désordre et en retard, et **combien de fois** chaque événement est compté.

![Pipeline de streaming de référence](../../svg/streaming-pipeline.svg)

Dataflow lit un abonnement *pull* dédié, écrit dans BigQuery par la Storage Write API, envoie vers [Bigtable](#bigtable) ce qui doit être relu par clé à la milliseconde, et route les messages qu'il ne sait pas traiter vers une destination d'erreurs. Quand les messages n'ont besoin d'aucune transformation, un abonnement BigQuery écrit directement dans la table, sans job à exploiter.

## Faut-il Dataflow ?

| Besoin | Solution | Ce qu'on perd ou gagne |
|---|---|---|
| Fenêtres, agrégats, jointures de flux, enrichissement | **Pub/Sub → Dataflow → BigQuery** | Toute la sémantique de Beam ; un job à dimensionner et à surveiller |
| Chaque message devient une ligne, sans calcul | **Abonnement BigQuery** de Pub/Sub | Aucun job ; transformations légères seulement (*Single Message Transform*) ; livraison au moins une fois |
| L'application produit elle-même les lignes | **Storage Write API** : flux par défaut, ou flux *committed* avec *offsets* | Pas de bus de messages ; au moins une fois par défaut, exactement une fois avec les *offsets* |
| L'écosystème parle déjà Kafka | [Managed Service for Apache Kafka](#managed-service-for-apache-kafka), connecteur BigQuery de Kafka Connect ou Dataflow | Garde l'API Kafka ; partitions et cluster à dimensionner |
| Lecture par clé à faible latence (profil, compteur, dernier état) | **Bigtable** comme destination, par Dataflow | Latence de la milliseconde ; pas d'analyse ad hoc, garder aussi une copie dans BigQuery |
| Transformation SQL sur des données déjà dans BigQuery | **Requêtes continues** BigQuery, sortie vers une table, Pub/Sub, Bigtable ou Spanner | Pas de code Beam ; réservation en édition Enterprise ou Enterprise Plus obligatoire |
| Archiver les messages bruts en fichiers | **Abonnement Cloud Storage** de Pub/Sub | Aucun job ; fichiers à charger ou à lire en table externe (voir [Batch : ETL ou ELT](#batch-etl-elt)) |

```bash
# Raccourci sans Dataflow : le sujet écrit directement dans une table existante
gcloud pubsub subscriptions create SUBSCRIPTION --topic=TOPIC \
  --bigquery-table=PROJECT_ID.DATASET.evenements --write-metadata
```

Avec `--write-metadata`, la table reçoit aussi `message_id`, `publish_time` et les attributs : c'est la colonne `message_id` qui permet de dédoublonner ensuite.

## Fenêtres

Un flux n'a pas de fin : pour calculer un total ou une moyenne, Beam le découpe en **fenêtres** selon l'**heure de l'événement** (*event time*), pas l'heure d'arrivée. Par défaut, l'horodatage d'un message Pub/Sub est son heure de publication ; `timestamp_attribute` de `ReadFromPubSub` prend à la place un attribut posé par le producteur.

![Types de fenêtres sur un même flux d'événements](../../svg/fenetres-beam.svg)

| Fenêtre | Beam Python | Découpage | Usage type |
|---|---|---|---|
| **Fixe** (*tumbling*) | `window.FixedWindows(60)` | Intervalles égaux, disjoints | Total par minute, par heure |
| **Glissante** (*hopping*, *sliding*) | `window.SlidingWindows(120, 60)` | Taille et période ; un événement tombe dans plusieurs fenêtres | Moyenne mobile recalculée à intervalle régulier |
| **Session** | `window.Sessions(600)` | Se ferme après un écart sans événement ; calculée **par clé** | Visite d'un utilisateur, activité d'un appareil |
| **Globale** | `window.GlobalWindows()` | Une seule fenêtre, sans fin | Fenêtre par défaut, adaptée au batch ; en flux, exige un déclencheur explicite |

Les noms diffèrent selon l'interface : la documentation Dataflow parle de *tumbling* et *hopping*, Beam de *fixed* et *sliding*.

## Filigrane, déclencheurs et données en retard

- **Filigrane** (*watermark*) : l'estimation, par le pipeline, de l'instant jusqu'auquel toutes les données sont arrivées. Il est fourni par la source ; le connecteur Pub/Sub de Dataflow s'appuie sur l'âge du plus vieux message non acquitté. Une source inactive parmi plusieurs retient le filigrane de tout le pipeline.
- **Déclencheur** (*trigger*) : décide quand une fenêtre émet un résultat (un *pane*). Le déclencheur par défaut émet une fois, quand le filigrane dépasse la fin de la fenêtre. `AfterWatermark(early=..., late=...)` ajoute des résultats provisoires et des corrections ; `AfterProcessingTime` et `AfterCount` réagissent au temps écoulé ou au nombre d'éléments.
- **Retard autorisé** (*allowed lateness*) : durée pendant laquelle une fenêtre reste ouverte après le filigrane. Il vaut **zéro** par défaut : un événement en retard est alors jeté sans erreur.
- **Mode d'accumulation** : `ACCUMULATING` réémet le total depuis le début de la fenêtre, `DISCARDING` n'émet que ce qui est arrivé depuis le résultat précédent.

> [!WARNING]
> Chaque *pane* émis devient une ligne dans BigQuery. En `DISCARDING`, la valeur juste s'obtient par `SUM` sur la fenêtre ; en `ACCUMULATING`, il faut ne garder que la dernière ligne de chaque fenêtre. Un `AfterCount(50)` seul laisse aussi en attente, sans fin, une fenêtre qui n'a reçu que 32 éléments : le combiner avec une condition de temps.

## Doublons, ordre et erreurs

**Exactement une fois dans Dataflow.** Pub/Sub livre *au moins une fois* : un message peut revenir, même après acquittement. Le mode par défaut de Dataflow, *exactly-once*, dédoublonne sur l'ID de message Pub/Sub. Si un producteur publie deux fois le même événement, les ID diffèrent : `id_label` fait dédoublonner sur un attribut métier, à condition que les deux publications aient lieu à moins de dix minutes d'écart. Les effets de bord (appel d'API, écriture hors connecteur) peuvent, eux, se produire plusieurs fois.

**Au moins une fois, moins cher.** L'option `streaming_mode_at_least_once` réduit coût et latence, au prix de doublons rares (en général moins de 1 %). Elle convient aux pipelines sans agrégat (conversion de format, journaux, CDC) et à ceux qui dédoublonnent en aval. Aligner alors le connecteur BigQuery : `STORAGE_API_AT_LEAST_ONCE` (en Python, `use_at_least_once=True` avec la méthode `STORAGE_WRITE_API`). L'abonnement BigQuery, lui, ne garantit qu'une livraison au moins une fois : dédoublonner dans BigQuery sur `message_id`.

**Ordre.** Pub/Sub garantit l'ordre entre messages qui portent la même **clé d'ordonnancement**, publiés dans une même région, sur un abonnement où l'ordre est activé ; le débit de publication est limité à 1 Mo/s par clé. Avec Dataflow, l'ordre n'est pas conservé et l'option dégrade les performances : raisonner en heure d'événement et en fenêtres plutôt qu'en ordre d'arrivée.

**Erreurs.** Pour un abonnement lu par un client ou écrit vers BigQuery, un **sujet de lettres mortes** reçoit le message après 5 à 100 tentatives ; l'agent de service Pub/Sub doit pouvoir publier dans ce sujet et s'abonner à l'abonnement d'origine. Avec Dataflow, ne pas utiliser de sujet de lettres mortes : Dataflow acquitte après la première étape et envoie des refus pour des raisons internes. Le pattern se code dans le pipeline, par une sortie secondaire vers une table ou un bucket d'erreurs.

> [!WARNING]
> Trois réglages Pub/Sub à ne pas combiner avec Dataflow : la livraison *exactly-once* de Pub/Sub, qui bride le parallélisme alors que Dataflow dédoublonne déjà, la politique de relance à délai exponentiel (utiliser « relancer immédiatement ») et un abonnement partagé entre deux pipelines (un abonnement par pipeline).

## Exemple Apache Beam

Total des ventes par produit et par minute, avec corrections pendant dix minutes pour les ventes en retard :

```python
import json

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms import trigger, window


class VersLigne(beam.DoFn):
    def process(self, element, fenetre=beam.DoFn.WindowParam):
        produit, total = element
        yield {"debut_fenetre": fenetre.start, "produit": produit, "total": total}


options = PipelineOptions(
    streaming=True, runner="DataflowRunner",
    project="PROJECT_ID", region="REGION", temp_location="gs://BUCKET/tmp",
)

with beam.Pipeline(options=options) as p:
    (
        p
        | "Lire" >> beam.io.ReadFromPubSub(
            subscription="projects/PROJECT_ID/subscriptions/SUBSCRIPTION",
            timestamp_attribute="event_time",  # heure de l'événement, pas de publication
            id_label="vente_id",               # dédoublonnage sur un identifiant métier
        )
        | "Décoder" >> beam.Map(json.loads)
        | "Clé" >> beam.Map(lambda v: (v["produit"], v["montant"]))
        | "Fenêtrer" >> beam.WindowInto(
            window.FixedWindows(60),
            trigger=trigger.AfterWatermark(late=trigger.AfterCount(1)),
            accumulation_mode=trigger.AccumulationMode.DISCARDING,
            allowed_lateness=600,
        )
        | "Sommer" >> beam.CombinePerKey(sum)
        | "Ligne" >> beam.ParDo(VersLigne())
        | "Écrire" >> beam.io.WriteToBigQuery(
            "PROJECT_ID:DATASET.ventes_minute",
            schema="debut_fenetre:TIMESTAMP,produit:STRING,total:FLOAT64",
            method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API,
            triggering_frequency=5,
        )
    )
```

En `DISCARDING`, une vente en retard produit une ligne de correction pour la même fenêtre : le total se lit par `SUM(total) ... GROUP BY debut_fenetre, produit`. En Python, la Storage Write API passe par une transformation multilangage : un `TIMESTAMP` doit être un `Timestamp` Beam (c'est le cas de `fenetre.start`), et certains types comme `DATETIME` ne sont pas pris en charge.

## Diagnostic

Un pipeline de flux se surveille sur quatre signaux, détaillés dans la fiche [Dataflow](#dataflow) :

- **Fraîcheur des données** : écart entre l'heure de traitement et l'heure de l'événement. Une courbe qui monte en continu signale un débit inférieur au débit entrant.
- **Retard du système** (`system_lag`, et `per_stage_system_lag` par étape) : temps maximal pendant lequel un élément attend ou est en cours de traitement. Il localise l'étape lente.
- **Backlog** : volume et durée estimée du retard à résorber côté source.
- **Clés chaudes** : une clé surreprésentée est traitée en série par un seul worker. Le diagnostic de goulot d'étranglement l'indique (*Hot keys or insufficient key parallelism*) ; l'option `--dataflow_service_options=enable_hot_key_logging` fait écrire la clé dans les journaux. Remèdes : redistribuer la clé (suffixe aléatoire, puis second regroupement), ou `with_hot_key_fanout` sur `CombinePerKey`.

> [!TIP]
> Pour retraiter des messages, ne pas faire de *seek* sur l'abonnement d'un job en cours : créer un instantané, un nouvel abonnement à partir de cet instantané, drainer le job, puis le relancer sur le nouvel abonnement.

## Reprise après incident

Un job en continu ne se termine jamais de lui-même : chaque arrêt, correction ou panne passe par l'une de ces opérations.

| Opération | Commande | Effet sur les données | Usage |
|---|---|---|---|
| **Drainer** | `gcloud dataflow jobs drain JOB_ID` | Cesse de lire la source, termine les éléments en mémoire, ferme aussitôt les fenêtres ouvertes avec des résultats partiels | Arrêt sans perte ; en continu seulement |
| **Annuler** | `gcloud dataflow jobs cancel JOB_ID` | Arrêt immédiat ; les éléments lus mais pas encore écrits sont perdus ; le job ne redémarre pas | Données rejouées de toute façon, ou job bloqué |
| **Mettre à jour** | Relancer le pipeline avec `--update` et le même `--job_name` | Le nouveau code reprend l'état et les éléments en mémoire de l'ancien job | Correction de code sans perte d'état |
| **Instantané, puis nouveau job** | `gcloud dataflow snapshots create --snapshot-sources=true`, puis `--create_from_snapshot` | État du pipeline restauré, source Pub/Sub relue depuis son instantané | Panne de zone, retour arrière après une mise à jour |
| ***Seek* Pub/Sub** | `gcloud pubsub subscriptions seek` vers un instantané ou une date | Rejoue des messages acquittés, ou purge un arriéré | Retraitement après un bogue, sur un nouvel abonnement |

- **Contrôle de compatibilité.** Une mise à jour ne remplace l'ancien job que si l'état et les données en mémoire peuvent passer de l'un à l'autre ; sinon l'ancien job continue et le nouveau renvoie une erreur. Le contrôle échoue quand une étape est renommée ou supprimée sans `--transform_name_mapping`, qu'une entrée secondaire est ajoutée ou retirée, qu'un *coder* change, qu'une opération avec état disparaît, ou que le job change de zone. L'option `--dataflow_service_options=graph_validate_only` fait le contrôle sans toucher au job en cours. Avec Streaming Engine, le nombre minimal et maximal de workers se modifie sans nouveau job (`gcloud dataflow jobs update-options`).
- **Drainer, puis relancer.** Une fenêtre fermée en partie par le drainage se déclenche une seconde fois au redémarrage, avec les éléments arrivés ensuite : l'écriture doit tolérer deux résultats pour une même fenêtre. Le drainage ne débloque pas un job bloqué : c'est une mise à jour avec le code corrigé qui le débloque.
- **Panne de zone.** Si la logique ne dépend pas des données déjà traitées, relancer le job sur le même abonnement suffit ; avec des fenêtres, un *seek* à la date de la panne recalcule les mêmes résultats. Si elle en dépend (longues fenêtres, compteurs cumulés), il faut un instantané Dataflow pris avant la panne : des instantanés réguliers réduisent le RTO. Le détail est dans la fiche [Dataflow](#dataflow), la stratégie d'ensemble dans [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Alternatives en logiciel libre

- **Apache Kafka** (Apache 2.0) : le journal d'événements à la place de Pub/Sub, avec partitions, rétention longue et relecture par *offset* ; brokers, partitions et rééquilibrage restent à dimensionner.
- **Apache Pulsar** (Apache 2.0) : sujets et abonnements multiples, acquittement message par message et stockage à plusieurs niveaux ; le modèle le plus proche de Pub/Sub.
- **Apache Flink** (Apache 2.0) : le moteur de flux avec état de référence ; heure d'événement, filigranes, retard autorisé et exactement une fois par points de reprise y sont natifs, mais le dimensionnement et les points de sauvegarde sont à gérer.
- **Apache Beam** (Apache 2.0) sur le *runner* Flink ou Spark : le pipeline de cette page tourne tel quel ; les connecteurs d'E/S, l'exactement une fois et le dédoublonnage `id_label` dépendent alors du *runner* et de la source.
- **Spark Structured Streaming** (Apache 2.0) : flux traités en micro-lots, avec fenêtres et filigranes ; pertinent quand l'équipe écrit déjà du Spark.
- **RisingWave** (Apache 2.0) : base de flux compatible PostgreSQL, où des vues matérialisées en SQL se tiennent à jour au fil des événements ; l'équivalent des requêtes continues, sans code Beam.
- **Apache Druid** et **Apache Pinot** (Apache 2.0) : ingestion directe depuis Kafka et requêtes analytiques en quelques secondes ; ils tiennent la place de BigQuery en bout de chaîne quand la latence de lecture prime.
