---
title: Appeler une API REST sans bibliothèque
---

Toute API Google Cloud expose une interface REST : JSON sur HTTPS, un jeton OAuth 2.0 en en-tête, des conventions communes pour la pagination, les opérations longues et les erreurs. L'appeler directement se justifie quand aucune bibliothèque cliente ne couvre la méthode, pour une fonction en *preview* que la bibliothèque n'expose pas encore, ou pour une fonction légère où `requests` et `google-auth` suffisent. Dans les autres cas, la [bibliothèque cliente](#bibliotheques-clientes) apporte types, relances et pagination sans effort. Les méthodes d'authentification sont décrites dans [Authentifier un appel à une API](#authentifier-un-appel).

## Trouver l'URL et la méthode

| Source | Ce qu'on y lit |
|---|---|
| Référence REST du service (`docs.cloud.google.com/SERVICE/docs/reference/rest`) | Ressources, méthodes, verbe HTTP, chemin, corps, paramètres de requête |
| Document de découverte : `https://SERVICE.googleapis.com/$discovery/rest?version=v1` | La même description en JSON : `rootUrl`, chemins (`v1/{+parent}/secrets`), paramètres, schémas, et les points de terminaison régionaux dans `endpoints` |
| [APIs Explorer](https://developers.google.com/apis-explorer) | Essai d'une méthode depuis le navigateur |
| `gcloud ... --log-http` | La requête HTTP exacte qu'émet une commande `gcloud` |

L'URL se compose de l'hôte, de la version et du nom de ressource : `https://secretmanager.googleapis.com/v1/projects/PROJECT_ID/secrets`. Les méthodes personnalisées ajoutent un suffixe après deux-points (`.../versions/latest:access`, `.../operations/OP:wait`). Un point de terminaison régional remplace l'hôte : `https://secretmanager.REGION.rep.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/secrets`.

## Avec `curl`

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "x-goog-user-project: PROJECT_ID" \
  "https://secretmanager.googleapis.com/v1/projects/PROJECT_ID/secrets?pageSize=50"
```

Avec des identifiants d'utilisateur, certaines API exigent un **projet de quota** : l'en-tête `x-goog-user-project` le désigne et demande la permission `serviceusage.services.use` sur ce projet. Pour tester avec le jeton qu'utiliserait l'application : `gcloud auth application-default print-access-token`.

## Avec `AuthorizedSession`

`google.auth.default()` trouve les identifiants par ADC ; `AuthorizedSession`, une `requests.Session`, ajoute le jeton à chaque requête et le renouvelle quand il expire.

```python
import google.auth
from google.auth.transport.requests import AuthorizedSession

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
    quota_project_id="PROJECT_ID",        # optionnel : ajoute l'en-tête x-goog-user-project
)
session = AuthorizedSession(credentials)
reponse = session.get("https://secretmanager.googleapis.com/v1/projects/PROJECT_ID/secrets", timeout=30)
```

Le *scope* `cloud-platform` couvre toutes les API Google Cloud ; IAM décide ensuite de ce que le principal peut faire. Le préciser évite l'erreur d'un compte de service emprunté ou fédéré créé sans *scope*.

## Conventions communes

| Besoin | Paramètre ou champ | Remarque |
|---|---|---|
| Pagination | `pageSize`, `pageToken` en requête ; `nextPageToken` en réponse | Page suivante tant que `nextPageToken` est présent et non vide ; le serveur peut renvoyer moins que `pageSize` |
| Réponse partielle | `fields=secrets(name,labels),nextPageToken` ou en-tête `X-Goog-FieldMask` | Réduit la réponse aux champs cités |
| Mise à jour partielle | `PATCH` avec `updateMask=labels,annotations` en requête | Seuls les champs cités sont modifiés |
| Opération longue | Réponse `{"name": ..., "done": false, "metadata": {...}}` | Sonder `GET https://SERVICE.googleapis.com/v1/OPERATION_NAME` jusqu'à `done: true`, puis lire `response` ou `error` |
| Attente côté serveur | `POST .../operations/OP:wait` quand l'API le propose (Cloud Run v2) | Bloque jusqu'à la fin ou jusqu'au délai du serveur |
| Projet de quota | En-tête `X-Goog-User-Project` | Permission `serviceusage.services.use` sur le projet |

Une erreur revient avec le code HTTP et un corps `google.rpc.Status` ([AIP-193](https://google.aip.dev/193)) :

```json
{"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded for ...",
  "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "RATE_LIMIT_EXCEEDED",
               "domain": "googleapis.com", "metadata": {"service": "secretmanager.googleapis.com"}}]}}
```

`status` et `details[].reason` sont stables et se testent dans le code ; `message` est destiné à un humain et peut changer. Les codes à relancer et la stratégie de relance sont dans [Erreurs, quotas et relances](#erreurs-quotas-relances).

## Exemple complet

Lister les secrets d'un projet page par page, modifier une étiquette, puis attendre une opération longue de Cloud Run :

```python
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
session = AuthorizedSession(credentials)


class ErreurApi(Exception):
    def __init__(self, reponse):
        erreur = reponse.json().get("error", {}) if reponse.content else {}
        self.code, self.status = reponse.status_code, erreur.get("status", "")
        super().__init__(f"{self.code} {self.status}: {erreur.get('message', reponse.text)}")


def appeler(methode, url, **kwargs):
    reponse = session.request(methode, url, timeout=30, **kwargs)
    if not reponse.ok:
        raise ErreurApi(reponse)
    return reponse.json() if reponse.content else {}


def lister(url, cle, **params):
    """Parcourt toutes les pages d'une méthode list."""
    while True:
        page = appeler("GET", url, params=params)
        yield from page.get(cle, [])
        if not page.get("nextPageToken"):
            return
        params["pageToken"] = page["nextPageToken"]


def attendre(url_base, operation, echeance=600):
    """Sonde une opération longue jusqu'à sa fin, avec un délai croissant."""
    fin, delai = time.monotonic() + echeance, 1.0
    while not operation.get("done"):
        if time.monotonic() > fin:
            raise TimeoutError(operation["name"])
        time.sleep(delai)
        delai = min(delai * 2, 30.0)
        operation = appeler("GET", f"{url_base}/{operation['name']}")
    if "error" in operation:
        raise RuntimeError(operation["error"])
    return operation.get("response")


SM = "https://secretmanager.googleapis.com/v1"
for secret in lister(f"{SM}/projects/PROJECT_ID/secrets", "secrets",
                     pageSize=100, fields="secrets(name,labels),nextPageToken"):
    print(secret["name"], secret.get("labels", {}))

appeler("PATCH", f"{SM}/projects/PROJECT_ID/secrets/db-password",
        params={"updateMask": "labels"}, json={"labels": {"env": "prod"}})

RUN = "https://run.googleapis.com/v2"
operation = appeler("DELETE", f"{RUN}/projects/PROJECT_ID/locations/REGION/services/api")
attendre(RUN, operation)
```

`AuthorizedSession` ne relance que sur 401, pour renouveler le jeton. Pour relancer sur 429 et 503, monter un adaptateur `requests` : `session.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429, 503], allowed_methods=None)))` (`from requests.adapters import HTTPAdapter`, `from urllib3.util import Retry`), en veillant à ce que les méthodes relancées soient idempotentes.

## Pièges

- **`fields` sans `nextPageToken`.** Une réponse partielle qui omet `nextPageToken` fait croire qu'il n'y a qu'une page. Toujours l'inclure dans `fields` d'une méthode de liste.
- **`PATCH` sans `updateMask`.** Selon l'API, la requête est refusée ou applique tous les champs présents dans le corps. Nommer explicitement les champs modifiés.
- **Nom de paramètre en `snake_case`.** L'URL et le JSON REST sont en `camelCase` (`pageSize`, `updateMask`) ; les noms `page_size` ou `update_mask` des bibliothèques clientes sont ignorés ou refusés.
- **Valeur binaire mal décodée.** Les champs `bytes` sont encodés en base64 dans le JSON : la charge d'un secret lue par `:access` se décode par `base64.b64decode(r["payload"]["data"])`.
- **Jeton copié dans le code.** Un jeton de `print-access-token` expire au bout d'une heure et ne se renouvelle pas. Dans une application, passer par `google.auth.default()`, jamais par un jeton figé ni une clé de compte de service.
- **Opération sondée sur le mauvais hôte.** Le nom d'opération se relit sur l'hôte et la version de l'API qui l'a renvoyée, régional compris. Journaliser le nom complet pour reprendre le suivi après un redémarrage.
- **Oubli du projet de quota.** Une erreur 403 qui réclame un projet de quota avec des identifiants d'utilisateur se corrige par `x-goog-user-project` (ou `quota_project_id=`), pas en élargissant les rôles.
- **Version *preview* en production.** Un chemin `v1beta` ou `v2alpha` peut changer sans préavis. Rester sur la version stable quand elle offre la méthode.
