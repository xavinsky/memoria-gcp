---
title: Pub/Sub, Firestore, Secret Manager et Cloud Tasks en Python
---

Ces quatre services se programment avec des bibliothèques gRPC générées, plus une couche écrite à la main pour [Pub/Sub](#pubsub) (lots, bail des messages) et [Firestore](#firestore) (requêtes, transactions). Les identifiants viennent d'ADC (voir [Authentification dans le code](#authentification-code)) ; les relances par défaut et les erreurs sont traitées dans [Erreurs, quotas et relances](#erreurs-quotas-relances). Les exemples suivent `google-cloud-pubsub` 2.41, `google-cloud-firestore` 2.31, `google-cloud-secret-manager` 2.30 et `google-cloud-tasks` 2.24. L'architecture d'un flux complet est dans [Streaming](#streaming).

## Matrice des clients

| Service | Paquet et classe | Appels principaux |
|---|---|---|
| Pub/Sub, publication | `google-cloud-pubsub` : `pubsub_v1.PublisherClient` | `topic_path`, `publish(topic, data, ordering_key=, **attrs)` → *future*, `resume_publish` |
| Pub/Sub, réception | `pubsub_v1.SubscriberClient` | `subscribe(sub, callback, flow_control=)` (*streaming pull*), `pull`, `acknowledge`, `modify_ack_deadline` |
| Firestore | `google-cloud-firestore` : `firestore.Client`, `firestore.AsyncClient` | `collection().document()`, `get`, `set(merge=)`, `update`, `where(filter=FieldFilter(...))`, `stream`, `transaction`, `batch`, `on_snapshot` |
| Secret Manager | `google-cloud-secret-manager` : `secretmanager.SecretManagerServiceClient` | `secret_version_path`, `access_secret_version`, `add_secret_version` |
| Cloud Tasks | `google-cloud-tasks` : `tasks_v2.CloudTasksClient` | `queue_path`, `task_path`, `create_task(parent=, task=)` |

## Pub/Sub : publier

`publish()` n'envoie rien tout de suite : il ajoute le message à un lot, envoyé dès que l'un des seuils de `BatchSettings` est atteint (par défaut 100 messages, 1 Mo ou 10 ms). Il rend une *future* dont `result()` donne l'identifiant du message, ou lève l'erreur de publication. Les données sont des octets ; les attributs, des chaînes.

```python
from concurrent import futures
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient(
    batch_settings=pubsub_v1.types.BatchSettings(max_messages=500, max_bytes=2_000_000, max_latency=0.05),
    publisher_options=pubsub_v1.types.PublisherOptions(enable_message_ordering=True),
    client_options={"api_endpoint": "europe-west1-pubsub.googleapis.com:443"},
)
topic = publisher.topic_path("PROJECT_ID", "TOPIC")

envois = [
    publisher.publish(topic, b'{"commande": 42}', ordering_key="client-17", source="boutique")
    for _ in range(3)
]
futures.wait(envois)                      # attendre avant de terminer le processus
for f in envois:
    try:
        print(f.result())
    except Exception:
        publisher.resume_publish(topic, "client-17")   # débloque la clé après un échec définitif
```

- **Ordre** : l'ordre n'est garanti que pour une même *ordering key*, publiée dans une même région, et reçue par un abonnement créé avec l'ordre activé. Un point de terminaison régional fixe la région. Le débit est limité à 1 Mo/s par clé.
- **Clé bloquée** : après un échec non relançable, le client refuse les publications suivantes de la clé jusqu'à `resume_publish()`. Avec une clé, les relances n'ont plus de délai total.
- **Contrôle de flux** : `PublisherOptions(flow_control=PublishFlowControl(message_limit=, byte_limit=, limit_exceeded_behavior=LimitExceededBehavior.BLOCK))` freine un producteur plus rapide que le réseau ; par défaut les dépassements sont ignorés et la mémoire grossit.

## Pub/Sub : recevoir

| Mode | Appel | Pour quoi |
|---|---|---|
| *Streaming pull* | `subscriber.subscribe(sub, callback, flow_control=FlowControl(max_messages=...))` | Service qui tourne en continu (GKE, VM, Cloud Run avec instances minimales) |
| Pull synchrone | `subscriber.pull(subscription=sub, max_messages=100)`, puis `acknowledge(subscription=sub, ack_ids=[...])` | Job par lots qui vide un abonnement puis s'arrête |
| *Push* | Pub/Sub appelle une URL HTTPS | Cloud Run ou Cloud Run functions, sans processus à maintenir |

En *streaming pull*, le client prolonge lui-même le délai d'accusé des messages en cours (jusqu'à `max_lease_duration`, une heure par défaut) et lance le rappel dans un pool de threads. `FlowControl` borne le nombre de messages en mémoire (1 000 et 100 Mo par défaut).

```python
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.exceptions import AcknowledgeError

subscriber = pubsub_v1.SubscriberClient()
sub = subscriber.subscription_path("PROJECT_ID", "SUBSCRIPTION")

def traiter(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        enregistrer(message.data, message.attributes, message.delivery_attempt)
    except ValueError:
        message.nack()                         # redistribué, puis lettre morte si configurée
        return
    if message.exactly_once_enabled:
        try:
            message.ack_with_response().result()   # confirmé par le serveur
        except AcknowledgeError as e:
            print("accusé refusé", e.error_code)    # le message sera redistribué
    else:
        message.ack()

flux = subscriber.subscribe(sub, callback=traiter,
                            flow_control=pubsub_v1.types.FlowControl(max_messages=200))
with subscriber:
    try:
        flux.result()                          # bloque ; timeout= pour s'arrêter
    except KeyboardInterrupt:
        flux.cancel()
        flux.result()
```

- **Au moins une fois** : sans option, un message peut arriver deux fois ; le traitement doit être idempotent (clé d'unicité en base, `MERGE`).
- **Exactement une fois** : option de l'abonnement, réservée aux abonnements *pull* (streaming compris), garantie dans une même région. `ack_with_response()` dit si l'accusé a été pris en compte ; les doublons émis côté éditeur restent possibles. Latence plus élevée.
- **Lettres mortes** : `--dead-letter-topic` et `--max-delivery-attempts` (5 à 100) sur l'abonnement. L'agent de service Pub/Sub doit pouvoir publier sur le sujet de lettres mortes et s'abonner à l'abonnement d'origine. `message.delivery_attempt` n'est renseigné que si cette politique existe.

**Push vers Cloud Run.** Pub/Sub envoie un `POST` JSON (`message.data` en base64, `message.attributes`, `message.messageId`) et considère le message acquitté sur une réponse 102, 200, 201, 202 ou 204. Avec un compte de service d'authentification sur l'abonnement, la requête porte un jeton OIDC dont l'audience est, par défaut, l'URL de l'endpoint. Si le service Cloud Run exige l'authentification et que ce compte a `roles/run.invoker`, Cloud Run vérifie le jeton lui-même. Un point de terminaison public doit le vérifier dans le code :

```python
import base64
import flask
from google.auth.transport import requests as g_requests
from google.oauth2 import id_token

app = flask.Flask(__name__)

@app.post("/pubsub")
def recevoir():
    jeton = flask.request.headers.get("Authorization", "").removeprefix("Bearer ")
    claims = id_token.verify_oauth2_token(jeton, g_requests.Request(), audience="https://SERVICE_URL/pubsub")
    if claims.get("email") != "push-sa@PROJECT_ID.iam.gserviceaccount.com":
        flask.abort(403)
    message = flask.request.get_json()["message"]
    enregistrer(base64.b64decode(message.get("data", "")), message.get("attributes", {}), None)
    return "", 204
```

## Firestore

```python
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

db = firestore.Client(project="PROJECT_ID", database="(default)")
commande = db.collection("commandes").document("c-42")

commande.set({"client": "client-17", "statut": "ouverte", "cree": firestore.SERVER_TIMESTAMP})
commande.set({"canal": "web"}, merge=True)                     # fusion, sans écraser le reste
commande.update({"lignes": firestore.Increment(1), "tags": firestore.ArrayUnion(["promo"])})
snap = commande.get()
print(snap.exists, snap.to_dict() if snap.exists else None)

ouvertes = (db.collection("commandes")
            .where(filter=FieldFilter("statut", "==", "ouverte"))
            .where(filter=FieldFilter("montant", ">=", 100))
            .order_by("montant", direction=firestore.Query.DESCENDING)
            .limit(50))
for doc in ouvertes.stream():
    print(doc.id, doc.get("montant"))

@firestore.transactional
def reserver(transaction, ref, quantite):
    stock = ref.get(transaction=transaction).get("stock")    # lectures d'abord
    if stock < quantite:
        raise ValueError("stock insuffisant")
    transaction.update(ref, {"stock": stock - quantite})     # écritures ensuite

reserver(db.transaction(), db.collection("articles").document("A-42"), 3)

lot = db.batch()                                             # écritures atomiques sans lecture
lot.set(db.collection("journal").document(), {"evt": "reservation"})
lot.delete(db.collection("paniers").document("p-9"))
lot.commit()
```

- **`set` / `update`** : `set()` remplace le document, `set(merge=True)` fusionne les champs, `update()` échoue si le document n'existe pas et accepte les chemins pointés (`"adresse.ville"`).
- **Requêtes** : `FieldFilter` s'emploie en argument nommé `filter=` ; `firestore.Or(...)` combine des filtres. Une égalité combinée à une inégalité ou un tri sur un autre champ demande un index composite : l'erreur renvoie le lien qui le crée.
- **Transactions** : la fonction peut être rejouée (5 tentatives par défaut, `db.transaction(max_attempts=...)`) : pas d'effet de bord dedans. Limites : 270 s, 60 s d'inactivité, 10 Mio par requête. En édition Standard, les bibliothèques serveur verrouillent les documents lus (concurrence pessimiste) ; l'édition Enterprise est optimiste par défaut.
- **Gros volumes** : `db.bulk_writer()` parallélise des écritures individuelles, plus rapide que des lots.
- **Asynchrone** : `firestore.AsyncClient` offre les mêmes méthodes en `await`, avec `@firestore.async_transactional`.
- **Écoute** : `ref.on_snapshot(callback)` appelle `callback(snapshots, changements, heure_lecture)` à chaque modification ; `watch.unsubscribe()` y met fin. Pour réagir dans un service sans connexion ouverte, un déclencheur Eventarc sur Firestore convient mieux.

## Secret Manager

```python
import google_crc32c
from google.cloud import secretmanager

secrets = secretmanager.SecretManagerServiceClient()

def lire_secret(nom: str, version: str) -> str:
    reponse = secrets.access_secret_version(
        name=secrets.secret_version_path("PROJECT_ID", nom, version))
    if google_crc32c.value(reponse.payload.data) != reponse.payload.data_crc32c:
        raise RuntimeError("secret corrompu")
    return reponse.payload.data.decode("utf-8")

MOT_DE_PASSE_BASE = lire_secret("db-password", "7")      # lu une fois, au démarrage

nouveau = b"s3cr3t"
secrets.add_secret_version(
    parent=secrets.secret_path("PROJECT_ID", "db-password"),
    payload={"data": nouveau, "data_crc32c": google_crc32c.value(nouveau)},
)
```

La documentation recommande une **version fixée**, lue au démarrage, plutôt que l'alias `latest` : un changement de secret passe alors par le déploiement, qui sait valider et revenir en arrière. `latest` convient à un secret tourné automatiquement si l'application relit le secret après un échec d'authentification. Chaque lecture compte dans un quota par minute : garder la valeur en mémoire, jamais un appel par requête. La lecture demande `roles/secretmanager.secretAccessor` sur le secret, pas sur le projet. Sur Cloud Run, un secret peut aussi être monté en volume ou en variable d'environnement sans code.

## Cloud Tasks

Une tâche [Cloud Tasks](#cloud-tasks) est une requête HTTP mise en file puis envoyée à un gestionnaire, avec relances selon la configuration de la file.

```python
import datetime, json
from google.cloud import tasks_v2
from google.api_core.exceptions import AlreadyExists

taches = tasks_v2.CloudTasksClient()
file = taches.queue_path("PROJECT_ID", "REGION", "QUEUE")

tache = tasks_v2.Task(
    name=taches.task_path("PROJECT_ID", "REGION", "QUEUE", "facture-c-42"),   # dédoublonnage
    http_request=tasks_v2.HttpRequest(
        http_method=tasks_v2.HttpMethod.POST,
        url="https://SERVICE_URL/factures",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"commande": "c-42"}).encode(),
        oidc_token=tasks_v2.OidcToken(
            service_account_email="tasks-invoker@PROJECT_ID.iam.gserviceaccount.com",
            audience="https://SERVICE_URL"),
    ),
    schedule_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    dispatch_deadline=datetime.timedelta(minutes=15),
)
try:
    taches.create_task(parent=file, task=tache)
except AlreadyExists:
    pass   # tâche déjà créée ou exécutée récemment
```

- **Authentification** : le compte du jeton OIDC a `roles/run.invoker` sur le service ; celui qui crée la tâche a `roles/cloudtasks.enqueuer` et le droit `iam.serviceAccounts.actAs` sur ce compte.
- **Délais** : `schedule_time` jusqu'à 30 jours dans le futur ; `dispatch_deadline` de 15 s à 30 min, 10 min par défaut. Au-delà, la tentative compte comme un échec et la tâche est relancée, même si le gestionnaire continue.
- **Dédoublonnage** : une tâche nommée ne peut être recréée tant que son nom n'est pas libéré, jusqu'à 24 h après exécution ou suppression ; la création rend `ALREADY_EXISTS`. Sans nom, aucun dédoublonnage.
- **Réponse du gestionnaire** : un code 2xx termine la tâche, tout autre code la relance. Les en-têtes `X-CloudTasks-TaskName` et `X-CloudTasks-TaskRetryCount` permettent de rendre le traitement idempotent.

## Pièges

- **Processus qui se termine avant l'envoi.** Un script qui publie puis sort sans attendre les *futures* perd les messages encore dans le lot. Toujours `futures.wait(...)` ou `result()` avant la sortie.
- **Rappel Pub/Sub lent ou bloquant.** Le rappel tourne dans un pool de threads limité ; un appel réseau sans délai y bloque la réception. `FlowControl` doit refléter ce que le processus traite vraiment.
- **Abonnement *pull* sur Cloud Run sans instance minimale.** Le *streaming pull* a besoin d'un processus qui tourne en continu : sans instance minimale ni facturation par instance, Cloud Run réduit le CPU hors requête. Un abonnement *push* convient mieux.
- **Ack avant traitement.** Acquitter puis traiter perd le message si le processus tombe entre les deux. Acquitter après l'écriture durable.
- **Ordre attendu sans clé.** Sans *ordering key* et abonnement ordonné, Pub/Sub ne garantit aucun ordre ; un `nack` sur un message ordonné fait aussi redistribuer les suivants de la même clé.
- **Effets de bord dans une transaction Firestore.** Envoyer un e-mail ou publier un message dans la fonction transactionnelle le fait autant de fois que la transaction est rejouée.
- **Secret lu à chaque requête.** Latence, coût et quota épuisé au premier pic de charge. Lire au démarrage et garder en mémoire.
- **Clients recréés à chaque requête.** Chaque client gRPC ouvre ses canaux ; le créer une fois par processus, en variable de module.
