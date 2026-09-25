---
title: Erreurs, quotas et relances
---

Les bibliothèques clientes Python traduisent toutes les erreurs d'API en exceptions de **`google.api_core.exceptions`**, qu'elles passent par gRPC ou par REST, et relancent d'elles-mêmes une partie des appels. Cette section dit quelles erreurs relancer, comment régler ces relances, comment rendre un appel sûr à relancer, et comment distinguer un quota d'un débit trop élevé. La nature des quotas, leur consultation et leur relèvement sont traités dans [Quotas et limites](#quotas-et-limites). Les exemples suivent `google-api-core` 2.38.

## Les exceptions

Chaque classe porte un code HTTP (`e.code`) et, pour gRPC, un statut (`e.grpc_status_code`). On attrape la plus précise possible, ou la classe mère `GoogleAPICallError`.

| Exception | HTTP | Statut gRPC | Cause habituelle | Relancer ? |
|---|---|---|---|---|
| `InvalidArgument`, `FailedPrecondition`, `OutOfRange` (sous `BadRequest`) | 400 | `INVALID_ARGUMENT`, `FAILED_PRECONDITION`, `OUT_OF_RANGE` | Requête mal formée, état de la ressource incompatible | Non : corriger la requête |
| `Unauthenticated` | 401 | `UNAUTHENTICATED` | Jeton absent, expiré ou invalide | Non (le client renouvelle déjà le jeton) |
| `PermissionDenied` (sous `Forbidden`) | 403 | `PERMISSION_DENIED` | Rôle manquant, API désactivée, projet de quota refusé | Non |
| `NotFound` | 404 | `NOT_FOUND` | Ressource ou emplacement inexistant | Non |
| `AlreadyExists` (sous `Conflict`) | 409 | `ALREADY_EXISTS` | Création d'une ressource qui existe | Non ; souvent le signe qu'une tentative précédente a réussi |
| `Aborted` (sous `Conflict`) | 409 | `ABORTED` | Conflit de concurrence, transaction annulée | Oui, toute la transaction |
| `ResourceExhausted` (sous `TooManyRequests`) | 429 | `RESOURCE_EXHAUSTED` | Quota de débit, capacité partagée saturée | Oui, avec délai ; pas pour un quota journalier |
| `InternalServerError` | 500 | `INTERNAL` | Erreur passagère du service | Oui |
| `ServiceUnavailable` | 503 | `UNAVAILABLE` | Service ou connexion momentanément indisponible | Oui |
| `DeadlineExceeded` (sous `GatewayTimeout`) | 504 | `DEADLINE_EXCEEDED` | Délai du client dépassé | Seulement si l'appel est idempotent |
| `RetryError` | — | — | Budget de relance épuisé ; `e.cause` porte la dernière erreur | Non : remonter |

Le prédicat `google.api_core.retry.if_transient_error` retient `InternalServerError`, `TooManyRequests`, `ServiceUnavailable` et les erreurs de connexion.

## Relances par défaut

Chaque bibliothèque fixe sa politique, méthode par méthode :

| Bibliothèque | Relance par défaut | Exemple |
|---|---|---|
| Clients générés (gRPC : Pub/Sub, Secret Manager, Tasks...) | Politique propre à chaque méthode, lisible dans `transports/base.py` du client ; aucune relance sur les méthodes non idempotentes | Pub/Sub `publish` : `Aborted`, `Cancelled`, `DeadlineExceeded`, `InternalServerError`, `ResourceExhausted`, `ServiceUnavailable`, `Unknown`, 600 s au total. Secret Manager `access_secret_version` : `ResourceExhausted` et `ServiceUnavailable`, 60 s ; `add_secret_version` : aucune |
| [Cloud Storage](#cloud-storage) (`google-cloud-storage` 3.x) | `DEFAULT_RETRY` : 408, 429, 500, 502, 503, 504 et erreurs réseau, délai de 1 à 60 s, 120 s au total | Envoi, téléchargement et suppression relancés ; `rewrite` seulement si une précondition `if_generation_match` est donnée (`ConditionalRetryPolicy`) |
| [BigQuery](#bigquery) (`google-cloud-bigquery`) | `DEFAULT_RETRY` sur les raisons `rateLimitExceeded`, `backendError`, `internalError`, `badGateway`, 600 s ; `job_retry` relance toute la requête sur `jobRateLimitExceeded`, `jobBackendError`, `jobInternalError` | `quotaExceeded` n'est jamais relancé ; `job_retry` ne s'applique pas si un `job_id` explicite est fourni |

Quand le budget est épuisé, `Retry` lève `RetryError` ; une erreur hors prédicat remonte telle quelle dès la première tentative.

## Régler `retry` et `timeout`

Toute méthode accepte `retry=` et `timeout=`. `retry=None` coupe les relances.

```python
import logging
from google.api_core import exceptions
from google.api_core.retry import Retry, if_exception_type
from google.cloud import secretmanager

journal = logging.getLogger(__name__)
client = secretmanager.SecretManagerServiceClient()
NOM = "projects/PROJECT_ID/secrets/SECRET/versions/latest"

relance = Retry(
    initial=0.5,            # premier délai maximal, en secondes
    maximum=30.0,           # plafond d'un délai
    multiplier=2.0,         # croissance du plafond à chaque tentative
    timeout=90.0,           # budget total des tentatives
    predicate=if_exception_type(exceptions.ResourceExhausted, exceptions.ServiceUnavailable,
                                exceptions.InternalServerError),
    on_error=lambda e: journal.warning("tentative en échec : %r", e),
)
reponse = client.access_secret_version(
    name=NOM, retry=relance, timeout=20.0,
)
```

- **Délai.** Chaque attente est tirée au hasard entre 0 et un plafond qui part de `initial`, est multiplié par `multiplier` et borné par `maximum` : c'est le délai exponentiel tronqué avec gigue complète (*full jitter*), qui évite que des clients synchronisés relancent tous au même instant. `deadline=` est l'ancien nom de `timeout=` dans `Retry`.
- **`timeout=` de la méthode.** Pour un client généré, c'est le délai de l'appel, décompté depuis la première tentative : chaque tentative reçoit le temps restant. Pour Cloud Storage et BigQuery, c'est le délai de chaque requête HTTP ; le budget total est `Retry(timeout=...)`.
- **Hors des clients.** `Retry` décore aussi une fonction à soi (`@Retry(predicate=...)`), par exemple un appel REST fait avec `AuthorizedSession` (voir [Authentification côté code](#authentification-code)).
- Pub/Sub règle la relance des publications sur le client : `PublisherClient(publisher_options=types.PublisherOptions(retry=..., timeout=...))`.

## Idempotence : ce qui se relance sans risque

Un appel qui a expiré côté client a pu réussir côté serveur. Le relancer n'est sûr que s'il est idempotent, ou rendu tel.

| Appel | Risque d'une relance | Rendre la relance sûre |
|---|---|---|
| Lecture (`get`, `list`, téléchargement) | Aucun | — |
| Écriture d'objet Cloud Storage | Écraser une version plus récente | `if_generation_match=0` (créer seulement si absent) ou la génération lue |
| Requête BigQuery qui écrit | Double insertion | `job_id` déterministe (un second job de même id est refusé en `Conflict`), ou `MERGE` |
| Insertion en flux BigQuery (`insert_rows_json`) | Lignes en double | `row_ids` : dédoublonnage au mieux sur une courte fenêtre ; Storage Write API en mode *committed* avec *offsets* pour l'exactement une fois |
| Publication Pub/Sub | Message publié deux fois | Consommateur idempotent, identifiant métier en attribut |
| Création Compute Engine | Deux opérations lancées | `request_id` (UUID) identique à chaque tentative : le service ignore le doublon |
| Création de ressource, en général | Seconde tentative en `AlreadyExists` | Traiter `AlreadyExists` comme un succès après vérification |
| Nouvelle version de secret, transaction non idempotente | Double effet | Pas de relance automatique ; relire l'état avant de rejouer |

## Lire l'erreur : quota, débit ou droit

Les API Google joignent à l'erreur un détail `ErrorInfo` : `reason`, `domain` (`googleapis.com` pour les raisons communes) et `metadata` (service, `consumer`, `quota_metric`, `quota_limit`...). La bibliothèque l'expose en `e.reason`, `e.domain` et `e.metadata` ; `e.details` contient les autres détails, par exemple `RetryInfo` (délai conseillé) ou `RequestInfo` (identifiant de requête à fournir au support). Les API REST historiques comme BigQuery donnent leur raison dans `e.errors[0]["reason"]`.

| Raison | Code | Cause | Action |
|---|---|---|---|
| `RATE_LIMIT_EXCEEDED` | 429 | Quota de débit (par minute, par utilisateur...) atteint | Relancer avec délai, lisser le débit ; préférence de quota si c'est structurel |
| `RESOURCE_QUOTA_EXCEEDED` | 429 ou 403 | Quota d'allocation ou de volume atteint | Ne pas relancer : libérer ou demander du quota |
| `SERVICE_DISABLED` | 403 | API non activée dans le projet consommateur | `gcloud services enable SERVICE` sur ce projet |
| `USER_PROJECT_DENIED` | 403 | Projet de quota absent ou sans `serviceusage.services.use` | Fixer le projet de quota (voir [Authentification côté code](#authentification-code)) |
| `IAM_PERMISSION_DENIED` | 403 | Permission manquante | Accorder le rôle ; ne pas relancer |
| `ACCESS_TOKEN_SCOPE_INSUFFICIENT` | 403 | Scopes du jeton trop étroits (VM restreinte) | Scope `cloud-platform` |
| BigQuery `rateLimitExceeded` / `quotaExceeded` | 403 | Débit à court terme / quota ou limite de volume | Relancer / regrouper et attendre |

```python
try:
    client.access_secret_version(name=NOM)
except exceptions.ResourceExhausted as e:
    if e.reason == "RATE_LIMIT_EXCEEDED":
        ...   # débit : relance différée, lissage
    else:
        raise  # quota épuisé : inutile d'insister
except exceptions.PermissionDenied as e:
    journal.error("refus %s sur %s", e.reason, (e.metadata or {}).get("service"))
    raise
```

## Lisser le débit plutôt que relancer

- **Regrouper.** Un appel qui traite cent éléments consomme en général une unité de quota de requêtes, pas cent : lots de publication Pub/Sub (`types.BatchSettings(max_messages=100, max_bytes=1_000_000, max_latency=0.01)` par défaut), chargement BigQuery par fichier plutôt que ligne à ligne, API *batch* des services qui en proposent.
- **Limiter côté client.** Un plafond d'appels par seconde, calé sous le quota, évite de découvrir la limite par des 429. Pub/Sub le fait pour ses envois en attente avec `PublishFlowControl(message_limit=..., byte_limit=..., limit_exceeded_behavior=LimitExceededBehavior.BLOCK)` ; pour les autres API, une file de travail ([Cloud Tasks](#cloud-tasks) a un débit de distribution réglable) ou un sémaphore dans le code.
- **Couper le circuit.** Quand les erreurs persistent au-delà des relances, un disjoncteur (*circuit breaker*) cesse d'appeler le service pendant un temps et répond par un repli (cache, réponse dégradée, file d'attente), au lieu d'ajouter de la charge à un service saturé.

## Journaliser avec la trace

Une erreur se diagnostique à partir de la requête qui l'a déclenchée. Sur Cloud Run, l'en-tête `X-Cloud-Trace-Context` porte l'identifiant de trace ; un journal JSON écrit sur la sortie standard avec le champ `logging.googleapis.com/trace` est rattaché à la requête dans [Cloud Logging](#cloud-logging).

```python
import json

def journaliser_erreur(e: exceptions.GoogleAPICallError, en_tete_trace: str | None):
    entree = {
        "severity": "ERROR",
        "message": f"{type(e).__name__}: {e.message}",
        "code": e.code, "reason": e.reason, "metadata": e.metadata,
    }
    if en_tete_trace:
        entree["logging.googleapis.com/trace"] = f"projects/PROJECT_ID/traces/{en_tete_trace.split('/')[0]}"
    print(json.dumps(entree, default=str), flush=True)
```

## Pièges

- **Relancer ce qui ne passera pas.** Un 400, 403 ou 404 relancé ne fait que retarder l'échec et consommer du quota. Un `quotaExceeded` BigQuery ou un quota journalier ne se libère qu'à la remise à zéro.
- **Relances empilées.** Une boucle maison autour d'une méthode qui relance déjà multiplie les tentatives (5 × 5 = 25) et les délais. Régler `retry=` de la méthode plutôt que d'ajouter une boucle.
- **Relance sans gigue.** Des centaines d'instances qui relancent toutes après exactement une seconde recréent le pic qui a provoqué le 429. `Retry` tire ses délais au hasard ; une boucle écrite à la main doit en faire autant.
- **`DeadlineExceeded` pris pour un échec.** L'opération a pu aboutir : relire l'état avant de rejouer une écriture non idempotente.
- **Délais trop longs en ligne.** Un budget de relance de 600 s dans un service web garde la requête de l'utilisateur ouverte bien au-delà de son propre délai. En temps réel : peu de tentatives, `timeout` court, repli ; en traitement par lots : budget large.
- **Erreur avalée.** Attraper `GoogleAPICallError` sans journaliser `reason` ni `metadata` perd la seule information qui distingue un quota d'un droit manquant.
