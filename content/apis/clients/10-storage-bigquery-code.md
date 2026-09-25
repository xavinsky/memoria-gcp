---
title: Cloud Storage et BigQuery en Python
---

Deux bibliothèques couvrent l'essentiel des échanges de données : `google-cloud-storage` pour les objets de [Cloud Storage](#cloud-storage), `google-cloud-bigquery` pour les requêtes et chargements [BigQuery](#bigquery). Toutes deux passent par l'API JSON en HTTP, lisent les identifiants par ADC (voir [Authentification dans le code](#authentification-code)) et relancent d'elles-mêmes les erreurs transitoires. Les exemples suivent `google-cloud-storage` 3.14, `google-cloud-bigquery` 3.45 et `google-cloud-bigquery-storage` 2.41. Les commandes équivalentes sont dans [gcloud storage](#gcloud-storage) et [bq : requêtes et jobs](#bq-requetes-jobs).

## Cloud Storage : les appels courants

| Besoin | Appel | Remarque |
|---|---|---|
| Client, bucket, objet | `storage.Client()`, `client.bucket("BUCKET")`, `bucket.blob("chemin/objet")` | `bucket()` et `blob()` ne font aucun appel réseau |
| Envoyer un fichier | `blob.upload_from_filename(path, content_type=...)` | Aussi `upload_from_file(f)` et `upload_from_string(data, content_type=...)` |
| Lire un objet | `blob.download_as_bytes()`, `blob.download_to_filename(path)` | `start=`, `end=` pour une plage d'octets |
| Lire ou écrire en flux | `with blob.open("rb") as f:` ou `blob.open("w")` | Lecture par blocs, écriture en *resumable upload* ; blocs de 40 Mio par défaut |
| Lister | `client.list_blobs("BUCKET", prefix="raw/", delimiter="/")` | Itérateur paginé ; `.prefixes` donne les « dossiers » une fois l'itérateur parcouru |
| Écriture conditionnelle | `if_generation_match=0` (création seule) ou `=blob.generation` | Échec `412 PreconditionFailed` si l'objet a changé |
| Métadonnées | `bucket.get_blob(name)` ou `blob.reload()` | `size`, `generation`, `crc32c`, `updated`, `metadata` |
| Transferts parallèles | `transfer_manager.upload_many_from_filenames(...)`, `download_many_to_path(...)` | Processus parallèles, 8 par défaut |
| Gros fichier en morceaux | `transfer_manager.download_chunks_concurrently(blob, path)` | Morceaux de 32 Mio lus en parallèle |
| URL signée | `blob.generate_signed_url(version="v4", expiration=..., ...)` | 7 jours au plus |

Un envoi de plus de 8 Mio passe en *resumable upload* : le fichier part par blocs de 100 Mio, ou de `chunk_size` s'il est fixé sur l'objet (`bucket.blob(name, chunk_size=...)`, multiple de 256 Kio). Un bloc plus petit coûte plus de requêtes mais reprend plus vite après une coupure.

```python
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

client = storage.Client(project="PROJECT_ID")
bucket = client.bucket("BUCKET")

blob = bucket.blob("exports/2026-09-24/ventes.csv")
blob.upload_from_filename("ventes.csv", content_type="text/csv", if_generation_match=0)

# Lecture-modification-écriture sans écraser un autre écrivain
compteur = bucket.get_blob("etat/compteur.json")
try:
    compteur.upload_from_string(
        '{"n": 43}', content_type="application/json", if_generation_match=compteur.generation,
    )
except PreconditionFailed:
    pass  # un autre processus a écrit entre-temps : relire et recommencer

for b in client.list_blobs("BUCKET", prefix="exports/", match_glob="**.csv"):
    print(b.name, b.size)

with bucket.blob("logs/gros.jsonl").open("r", encoding="utf-8") as f:   # lecture en flux
    for ligne in f:
        ...
```

## Relances et préconditions

Le client relance les codes 408, 429, 500, 502, 503 et 504, avec un délai exponentiel : 1 s au départ, multiplié par 2, plafonné à 60 s, pendant 120 s au total. Les lectures, listes et suppressions sont relancées d'office. Les envois (`upload_*`) aussi : sans précondition, une nouvelle tentative peut écraser l'écriture d'un autre processus arrivée entre les deux. `if_generation_match` rend chaque écriture idempotente, donc sûre à relancer. Le paramètre `retry=` règle la politique par appel (`retry=None` la désactive, `DEFAULT_RETRY.with_deadline(300)` l'allonge) ; `timeout=` (60 s par défaut) borne chaque requête HTTP. Voir [Erreurs, quotas et relances](#erreurs-quotas-relances).

## URL signée sans clé

Une URL signée donne un accès temporaire à un objet sans compte Google. La signature exige une identité de compte de service, mais pas de fichier de clé : la bibliothèque sait faire signer par l'API IAM Credentials (`signBlob`). Deux façons de faire :

```python
import datetime
import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request

# 1. Sur Cloud Run ou une VM : le compte de service attaché signe lui-même
creds, _ = google.auth.default()
creds.refresh(Request())
url = bucket.blob("rapports/r.pdf").generate_signed_url(
    version="v4", expiration=datetime.timedelta(minutes=15), method="GET",
    service_account_email=creds.service_account_email, access_token=creds.token,
)

# 2. Depuis un poste : emprunt d'identité d'un compte de service
signataire = impersonated_credentials.Credentials(
    source_credentials=creds, target_principal="signer@PROJECT_ID.iam.gserviceaccount.com",
    target_scopes=["https://www.googleapis.com/auth/cloud-platform"], lifetime=900,
)
url_put = bucket.blob("depots/photo.jpg").generate_signed_url(
    version="v4", expiration=datetime.timedelta(minutes=10), method="PUT",
    content_type="image/jpeg", credentials=signataire,
)
```

L'appelant a besoin de `roles/iam.serviceAccountTokenCreator` sur le compte de service signataire, y compris sur lui-même dans le premier cas ; le signataire a besoin de droits de lecture ou d'écriture sur l'objet. Une URL `PUT` signée avec `content_type` n'accepte que ce type en en-tête `Content-Type`.

## BigQuery : requêtes et résultats

| Besoin | Appel | Remarque |
|---|---|---|
| Requête courte, résultat direct | `client.query_and_wait(sql, job_config=...)` | Rend un `RowIterator` ; avec `default_job_creation_mode="JOB_CREATION_OPTIONAL"` sur le client, pas de job créé pour les requêtes courtes |
| Requête suivie comme job | `job = client.query(sql, job_config=...)`, puis `job.result()` | `job.job_id`, `job.location`, `job.total_bytes_billed`, `job.cache_hit` |
| Paramètres | `QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("pays", "STRING", "FR")])` | `@pays` dans le SQL ; `ArrayQueryParameter` pour `IN UNNEST(@liste)` |
| Plafond de coût | `QueryJobConfig(maximum_bytes_billed=10 * 1024**3)` | La requête échoue sans être facturée si elle dépasse |
| Estimer avant d'exécuter | `QueryJobConfig(dry_run=True, use_query_cache=False)` | `job.total_bytes_processed`, aucun coût |
| Écrire le résultat | `QueryJobConfig(destination="PROJECT_ID.DATASET.table", write_disposition="WRITE_TRUNCATE")` | Sinon, table temporaire en cache 24 h |
| Étiquettes de coût | `QueryJobConfig(labels={"app": "rapports"})` | Ventilation dans la facturation et `INFORMATION_SCHEMA.JOBS` |
| Lire une table sans requête | `client.list_rows("PROJECT_ID.DATASET.table", selected_fields=..., max_results=...)` | Lecture gratuite (`tabledata.list`) ; la conversion par l'API Storage Read, elle, est facturée |
| Vers pandas ou Arrow | `rows.to_dataframe()`, `rows.to_arrow()` | Par l'API Storage Read si `google-cloud-bigquery-storage` est installé |
| Par morceaux | `rows.to_dataframe_iterable()`, `rows.to_arrow_iterable()` | Mémoire bornée pour un gros résultat |

Un `RowIterator` se parcourt directement : la bibliothèque charge les pages (`page_size=`) à mesure, et `rows.total_rows` donne le total. `to_dataframe()` et `to_arrow()` passent par l'**API Storage Read** (gRPC, flux parallèles en Arrow) quand `create_bqstorage_client=True`, la valeur par défaut, et que la bibliothèque est installée ; c'est bien plus rapide que la pagination REST pour plus de quelques dizaines de milliers de lignes. Cette API est facturée au volume lu et demande `bigquery.readsessions.create` (`roles/bigquery.readSessionUser`).

```python
from google.cloud import bigquery

client = bigquery.Client(project="PROJECT_ID", location="EU",
                         default_job_creation_mode="JOB_CREATION_OPTIONAL")
sql = """
    SELECT client_id, SUM(montant) AS total
    FROM `PROJECT_ID.DATASET.ventes`
    WHERE date_vente BETWEEN @debut AND @fin
    GROUP BY client_id
"""
params = [bigquery.ScalarQueryParameter("debut", "DATE", "2026-09-01"),
          bigquery.ScalarQueryParameter("fin", "DATE", "2026-09-30")]

essai = client.query(sql, job_config=bigquery.QueryJobConfig(
    query_parameters=params, dry_run=True, use_query_cache=False))
print(f"{essai.total_bytes_processed / 1e9:.1f} Go lus")

config = bigquery.QueryJobConfig(query_parameters=params, labels={"app": "rapports"},
                                 maximum_bytes_billed=20 * 1024**3)
df = client.query_and_wait(sql, job_config=config).to_dataframe()
```

## BigQuery : charger et insérer

| Source | Méthode | Coût et garanties |
|---|---|---|
| Fichiers dans Cloud Storage | `client.load_table_from_uri("gs://BUCKET/raw/*.parquet", table, job_config=LoadJobConfig(...))` | Gratuit (pool de slots partagé) ; atomique par job |
| DataFrame pandas | `client.load_table_from_dataframe(df, table, job_config=...)` | Converti en Parquet puis chargé ; même job de chargement |
| Flux continu | API **Storage Write** (gRPC) : `bigquery_storage_v1.BigQueryWriteClient` | Recommandée pour tout nouveau flux ; au moins une fois sur le flux par défaut, exactement une fois avec un flux `COMMITTED` et des *offsets* |
| Quelques lignes, code existant | `client.insert_rows_json(table, lignes)` | API Storage Write (REST), méthode `tabledata.insertAll` ; facturée plus cher, dédoublonnage au mieux sur une minute |

```python
config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    time_partitioning=bigquery.TimePartitioning(field="date_vente"),
)
job = client.load_table_from_uri("gs://BUCKET/raw/ventes/*.parquet",
                                 "PROJECT_ID.DATASET.ventes", job_config=config)
job.result()   # lève une exception si le job échoue ; job.errors pour le détail
```

Écriture en flux par l'API Storage Write, au format Arrow, sur le flux par défaut de la table :

```python
import pyarrow as pa
from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types, writer

ecrivain = bigquery_storage_v1.BigQueryWriteClient()
modele = types.AppendRowsRequest(
    write_stream=ecrivain.write_stream_path("PROJECT_ID", "DATASET", "evenements", "_default"))
table = pa.table({"id": ["e1", "e2"], "valeur": [1.5, 2.0]})
modele.arrow_rows.writer_schema.serialized_schema = table.schema.serialize().to_pybytes()

flux = writer.AppendRowsStream(ecrivain, modele)
lot = types.AppendRowsRequest()
lot.arrow_rows.rows.serialized_record_batch = table.to_batches()[0].serialize().to_pybytes()
flux.send(lot).result()
flux.close()
```

Le client Python de l'API Storage Write est de bas niveau : pas de gestion de schéma ni de reconnexion au-delà du flux. Pour un flux Pub/Sub → BigQuery sans transformation, un abonnement BigQuery ou Dataflow évite ce code (voir [Streaming](#streaming)).

## pandas et BigQuery DataFrames

`to_dataframe()` rapatrie tout le résultat dans la mémoire du processus : c'est le bon outil pour un résultat déjà agrégé. Pour travailler en syntaxe pandas sur une table entière, **BigQuery DataFrames** (`pip install bigframes`) traduit les opérations en SQL exécuté dans BigQuery ; seul `to_pandas()` ou `peek()` ramène des lignes.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = "PROJECT_ID"
bpd.options.bigquery.location = "EU"
ventes = bpd.read_gbq("PROJECT_ID.DATASET.ventes")
par_pays = ventes.groupby("pays")["montant"].sum()   # calculé dans BigQuery
print(par_pays.to_pandas())
```

## Pièges

- **`SELECT *` sur une grosse table.** BigQuery facture les colonnes lues, pas les lignes rendues : `LIMIT` ne réduit pas le coût, sauf sur une table en *clustering*. Nommer les colonnes, filtrer la partition, et poser `maximum_bytes_billed` sur les clients de production. Pour un simple aperçu, `list_rows(max_results=...)` est gratuit.
- **Mauvais emplacement.** Un job s'exécute là où sont ses données ; une requête qui joint un dataset `EU` et un dataset `US`, ou un chargement vers une autre région que le bucket multirégional, échoue. `client.get_job(job_id)` sans `location` rend `404 Not found` pour un job en région simple (hors multirégions `US` et `EU`) : passer `location=` ou le fixer sur le client.
- **DataFrame trop gros.** Un résultat de plusieurs Go en `to_dataframe()` sature la mémoire d'une instance Cloud Run. Agréger dans le SQL, lire par morceaux (`to_dataframe_iterable()`), ou écrire le résultat dans une table et l'exporter.
- **Pagination REST lente.** Sans `google-cloud-bigquery-storage`, la conversion en DataFrame repasse par la pagination REST, page par page ; la bibliothèque le signale par un avertissement. Installer le paquet (ou l'extra `google-cloud-bigquery[bqstorage,pandas]`).
- **`insert_rows_json` pour un flux massif.** Plus cher, dédoublonnage approximatif et quotas propres : réserver cette méthode aux faibles volumes, et passer à l'API Storage Write gRPC ou à un chargement par lots.
- **Écritures concurrentes sur un objet.** Deux processus qui écrivent le même nom d'objet se remplacent sans erreur. `if_generation_match` transforme ce conflit silencieux en `412` à traiter.
- **Clients recréés à chaque requête.** Créer `storage.Client` et `bigquery.Client` une fois par processus, en variable de module : chacun porte son pool de connexions et son cache de jetons.
