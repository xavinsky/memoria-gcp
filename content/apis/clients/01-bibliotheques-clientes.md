---
title: Bibliothèques clientes Python
---

Les API Google Cloud s'appellent en Python par les **Cloud Client Libraries**, un paquet `google-cloud-*` par service. La plupart sont générées à partir des définitions protobuf de l'API (générateur *GAPIC*) et partagent la même structure : un client par service, des méthodes qui prennent une requête, des *pagers* pour les listes et des objets `Operation` pour les traitements longs. Les exemples suivent `google-api-core` 2.38 et les versions de septembre 2026 ; Python 3.10 au minimum. L'authentification est traitée dans [Authentifier un appel à une API](#authentifier-un-appel), les erreurs et les relances dans [Erreurs, quotas et relances](#erreurs-quotas-relances), Gemini dans [Appeler Gemini depuis du code](#appeler-gemini).

## Deux familles de bibliothèques

| | Cloud Client Libraries | Google API Client Library |
|---|---|---|
| Paquet | `google-cloud-storage`, `google-cloud-secret-manager`... | `google-api-python-client` (un seul paquet) |
| Import | `from google.cloud import secretmanager` | `from googleapiclient.discovery import build` |
| Construction | Générée par API, types protobuf (*proto-plus*) | Générique, construite depuis le **document de découverte** de l'API ; dictionnaires JSON |
| Protocole | gRPC ou REST selon la bibliothèque | REST seulement |
| État | Recommandée pour tout code neuf | Maintenance : corrections critiques seulement |
| Quand l'utiliser | Dès qu'un paquet `google-cloud-*` existe pour l'API | API Google Workspace (Drive, Sheets, Admin SDK, Gmail) ; API Cloud dont le paquet manque ou reste en 0.x (Cloud SQL Admin : `build("sqladmin", "v1beta4")`) |

Google recommande les Cloud Client Libraries partout où elles existent ([Client libraries explained](https://docs.cloud.google.com/apis/docs/client-libraries-explained)). Une bibliothèque en version 0.x est en *preview* : son interface peut changer d'une version mineure à l'autre. La liste des API servies par le client de découverte est dans son [index des API](https://googleapis.github.io/google-api-python-client/docs/dyn/). Sans bibliothèque du tout, voir [Appeler une API REST sans bibliothèque](#api-rest-directe).

## Paquets des services courants

| Service | Paquet pip | Import | Remarque |
|---|---|---|---|
| [Cloud Storage](#cloud-storage) | `google-cloud-storage` | `from google.cloud import storage` | Écrite à la main, JSON sur HTTP ; voir [Storage et BigQuery](#storage-bigquery-code) |
| [BigQuery](#bigquery) | `google-cloud-bigquery`, `google-cloud-bigquery-storage` | `from google.cloud import bigquery` | REST pour les jobs ; lecture massive par la Storage Read API en gRPC |
| [Pub/Sub](#pubsub) | `google-cloud-pubsub` | `from google.cloud import pubsub_v1` | Surcouche GAPIC : mise en lots à la publication, flux à l'abonnement |
| [Firestore](#firestore) | `google-cloud-firestore` | `from google.cloud import firestore` | Voir [Pub/Sub, Firestore, secrets](#pubsub-firestore-secrets-code) |
| [Secret Manager](#secret-manager) | `google-cloud-secret-manager` | `from google.cloud import secretmanager` | GAPIC pur ; sert d'exemple ci-dessous |
| [Cloud Tasks](#cloud-tasks) | `google-cloud-tasks` | `from google.cloud import tasks_v2` | |
| Cloud Run (administration) | `google-cloud-run` | `from google.cloud import run_v2` | Encore en 0.x |
| Compute Engine | `google-cloud-compute` | `from google.cloud import compute_v1` | REST seulement ; opérations `ExtendedOperation` |
| Cloud Logging | `google-cloud-logging` | `import google.cloud.logging` | `Client().setup_logging()` branche le module `logging` |
| Resource Manager | `google-cloud-resource-manager` | `from google.cloud import resourcemanager_v3` | Projets, dossiers, tags |
| API ML | `google-cloud-speech`, `-vision`, `-translate`... | `speech_v2`, `vision`, `translate_v3` | Voir [Speech-to-Text et Text-to-Speech](#speech-to-text-tts) |
| Gemini | `google-genai` | `from google import genai` | SDK distinct ; voir [SDK google-genai](#sdk-google-genai) |

**Installer et figer.** Un fichier `requirements.txt` borne chaque paquet sur sa version majeure (`google-cloud-secret-manager>=2.30,<3`) et un fichier de verrouillage (`pip-compile`, `uv lock`) fixe les versions exactes, `protobuf` et `grpcio` compris : ce sont eux qui entrent en conflit quand plusieurs bibliothèques se côtoient. Il n'existe pas de nomenclature commune (BOM) côté Python.

## Construire un client

```python
from google.api_core.client_options import ClientOptions
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()             # ADC, point de terminaison mondial

regional = secretmanager.SecretManagerServiceClient(transport="rest", client_options=ClientOptions(
    api_endpoint="secretmanager.europe-west1.rep.googleapis.com",  # point de terminaison régional
    quota_project_id="PROJECT_ID",                                 # projet facturé pour les quotas
))
```

| Paramètre | Rôle |
|---|---|
| `credentials=` | Identifiants explicites ; par défaut ADC |
| `transport=` | `"grpc"` (défaut des clients GAPIC), `"rest"`, `"grpc_asyncio"` pour le client asynchrone |
| `client_options.api_endpoint` | Autre hôte : régional (`SERVICE.REGION.rep.googleapis.com`), Private Service Connect, émulateur |
| `client_options.quota_project_id` | Projet de quota, envoyé en en-tête `x-goog-user-project` |
| `client_options.universe_domain` | Univers autre que `googleapis.com` (cloud souverain) ; aussi `GOOGLE_CLOUD_UNIVERSE_DOMAIN` |
| `client_options.api_key` | Clé API, pour les rares API qui l'acceptent |

Les bibliothèques écrites à la main (`storage.Client`, `bigquery.Client`, `firestore.Client`) prennent en plus `project=` ; BigQuery prend `location=`. Un point de terminaison régional garantit que la requête est traitée dans la région ; les régions disponibles sont listées dans la documentation du service et dans le champ `endpoints` de son document de découverte.

**gRPC ou REST.** gRPC (protobuf sur HTTP/2) est le plus efficace et le seul à porter les flux bidirectionnels. REST passe là où gRPC bloque : proxy d'entreprise qui ne laisse pas passer HTTP/2, environnement où `grpcio` s'installe mal, image minimale, ou `fork` sans précaution. Le client asynchrone ne dispose en général que de `grpc_asyncio`.

## Appeler une méthode

Chaque méthode accepte soit un objet requête (ou un dictionnaire), soit les **paramètres aplatis** les plus courants, jamais les deux à la fois (`ValueError`). Les chemins de ressource se construisent par des méthodes de classe.

```python
from google.api_core import retry

nom = client.secret_version_path("PROJECT_ID", "db-password", "latest")
valeur = client.access_secret_version(name=nom, timeout=10).payload.data.decode()

# Objet requête : tous les champs, dont ceux absents des paramètres aplatis
pager = client.list_secrets(request={"parent": "projects/PROJECT_ID", "page_size": 100, "filter": "labels.env=prod"})

# Masque de champs : seuls les champs nommés sont modifiés
client.update_secret(
    secret={"name": client.secret_path("PROJECT_ID", "db-password"), "labels": {"env": "prod"}},
    update_mask={"paths": ["labels"]},
    retry=retry.Retry(initial=1.0, maximum=30.0, timeout=120.0),
)
```

`timeout`, en **secondes**, borne la durée totale de l'appel, relances comprises ; `retry` remplace la politique de relance par défaut de la méthode. Chaque version d'API a son module : `secretmanager` est l'alias du module stable `secretmanager_v1`, les fonctions en *preview* sont dans `secretmanager_v1beta2`, qu'on importe explicitement. Pour certains services, deux versions stables coexistent (`speech` et `speech_v2`) et n'ont pas les mêmes méthodes.

## Pagination

Une méthode `list_*` renvoie un *pager* : itérer dessus parcourt les éléments et appelle les pages suivantes au fil de l'eau. `.pages` donne les réponses brutes, page par page ; `page_size` fixe la taille demandée, que le serveur peut réduire.

```python
for secret in client.list_secrets(parent="projects/PROJECT_ID"):
    print(secret.name)

for page in client.list_secrets(request={"parent": "projects/PROJECT_ID", "page_size": 500}).pages:
    traiter_lot(page.secrets)
```

Les bibliothèques écrites à la main suivent le même principe : `storage.Client.list_blobs(..., page_size=)` et `bigquery.Client.list_rows(..., page_size=)` renvoient des itérateurs dotés de `.pages`.

**Client asynchrone.** Chaque client GAPIC a son pendant `...AsyncClient`, aux mêmes méthodes en coroutines ; le pager s'obtient par `await` puis se parcourt par `async for`.

```python
async def noms_des_secrets():
    async with secretmanager.SecretManagerServiceAsyncClient() as client:
        return [s.name async for s in await client.list_secrets(parent="projects/PROJECT_ID")]
```

## Opérations longues

Une méthode qui crée ou modifie une ressource lourde renvoie un `google.api_core.operation.Operation` au lieu du résultat.

```python
from google.cloud import run_v2

services = run_v2.ServicesClient()
operation = services.create_service(
    parent="projects/PROJECT_ID/locations/REGION",
    service_id="api",
    service=run_v2.Service(template=run_v2.RevisionTemplate(containers=[run_v2.Container(image="IMAGE")])),
)
print(operation.operation.name)           # nom de l'opération, à journaliser pour la reprendre
service = operation.result(timeout=600)   # attend, lève l'erreur de l'opération si elle échoue
```

| Méthode | Effet |
|---|---|
| `result(timeout=)` | Interroge le serveur jusqu'à la fin, renvoie la réponse typée ; `TimeoutError` passé le délai, sans annuler l'opération |
| `done()`, `metadata`, `cancel()` | Sonde sans bloquer ; `metadata` porte l'avancement quand l'API en publie ; l'annulation n'est pas honorée par toutes les API |
| `add_done_callback(fn)` | Rappel à la fin, exécuté dans un fil séparé |

`google-cloud-compute` renvoie un `ExtendedOperation` : même `result()`, qui lève l'erreur à la fin, et en plus `error_code` et `error_message` pour lire un échec sans exception.

## Réutilisation, journaux, traces

- **Un client par processus**, créé au démarrage et réutilisé : chaque instance ouvre son canal gRPC ou son pool HTTP et récupère ses jetons. Les clients gRPC se partagent entre fils d'exécution.
- **Après `fork`** : gRPC ne supporte pas qu'un canal ouvert traverse `os.fork()`. Avec `multiprocessing`, Gunicorn en *preload* ou Celery, créer les clients dans chaque processus enfant, après le `fork` ([Multiprocessing](https://docs.cloud.google.com/python/docs/reference/spanner/latest/multiprocessing)).
- **Journaux de débogage** : `GOOGLE_SDK_PYTHON_LOGGING_SCOPE=google` (ou `google.cloud.secretmanager_v1`) émet requêtes et réponses en journal structuré, sans modifier le code. Pour le transport lui-même : `GRPC_VERBOSITY=debug` et `GRPC_TRACE=http,call_error`. Ces journaux contiennent des données de la requête : ne pas les laisser actifs en production.
- **OpenTelemetry** : BigQuery produit des *spans* dès que `opentelemetry-api` est installé ; Pub/Sub sur option (`PublisherOptions(enable_open_telemetry_tracing=True)`) ; Cloud Storage avec `ENABLE_GCS_PYTHON_CLIENT_OTEL_TRACES=true`. Pour les clients GAPIC, le traçage par méthode est expérimental (`GOOGLE_SDK_EXPERIMENTAL_PYTHON_TRACING_ENABLED=true`, `ClientOptions(tracer_provider=...)`) ; l'instrumentation générique `opentelemetry-instrumentation-grpc` ou `-requests` couvre tous les clients.

## Pièges

- **Client créé à chaque requête.** Dans une fonction Cloud Run, le créer au niveau du module, pas dans le gestionnaire : sinon chaque appel paie l'ouverture du canal et l'obtention d'un jeton.
- **`request=` et paramètres aplatis mêlés.** `list_secrets(request={...}, parent=...)` lève `ValueError`. Choisir l'une des deux formes.
- **Liste tronquée.** Lire seulement `pager.secrets` ou la première page de `.pages` ne renvoie qu'une page. Itérer sur le pager lui-même.
- **Masque oublié.** Selon l'API, une méthode `update_*` sans `update_mask` est refusée (Secret Manager l'exige) ou applique tous les champs renseignés de l'objet envoyé. Toujours nommer les champs modifiés.
- **`result()` sans délai.** Sans `timeout`, `operation.result()` suit la politique de sondage par défaut (900 secondes dans `google-api-core`, sauf réglage propre à la méthode), trop courte pour une création lourde ou trop longue pour une requête web. Fixer un délai adapté et journaliser `operation.operation.name`.
- **Point de terminaison et ressource incohérents.** Un secret régional (`projects/PROJECT_ID/locations/REGION/secrets/...`) ne se lit que par le point de terminaison de sa région ; l'hôte mondial renvoie une erreur.

