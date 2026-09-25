---
title: Authentification côté code
---

Le choix de la méthode (ADC, compte de service attaché, emprunt d'identité, fédération) est traité dans [Authentifier un appel à une API](#authentifier-un-appel). Cette section en donne la traduction en Python, avec la bibliothèque **`google-auth`** (`pip install google-auth requests`), sur laquelle reposent toutes les bibliothèques clientes : ce que renvoie `google.auth.default()` selon l'environnement, les deux sortes de jetons (**jeton d'accès** pour appeler une API Google, **jeton d'identité** pour appeler son propre service), et la vérification d'un jeton reçu. Les exemples suivent `google-auth` 2.58.

## Ce que renvoie ADC

`credentials, project_id = google.auth.default()` applique l'ordre de recherche d'ADC et renvoie un objet dont la classe dépend de l'environnement. Le code applicatif n'a pas à la tester : un client construit sans `credentials=` fait le même appel.

| Environnement | Source trouvée | Classe renvoyée |
|---|---|---|
| Poste, `gcloud auth application-default login` | Fichier ADC de type `authorized_user` | `google.oauth2.credentials.Credentials` |
| Poste, même commande avec `--impersonate-service-account` | Fichier ADC de type `impersonated_service_account` | `google.auth.impersonated_credentials.Credentials` |
| Cloud Run, Cloud Run functions, VM, GKE avec Workload Identity Federation for GKE | Serveur de métadonnées | `google.auth.compute_engine.Credentials` |
| Hors de Google Cloud, [Workload Identity Federation](#workload-identity-federation) | Fichier `external_account` désigné par `GOOGLE_APPLICATION_CREDENTIALS` | `google.auth.identity_pool.Credentials` (jeton OIDC ou SAML lu dans un fichier ou à une URL, certificat X.509), `aws.Credentials`, `pluggable.Credentials` (exécutable) |
| Clé de compte de service, en dernier recours | Fichier `service_account` | `google.oauth2.service_account.Credentials` |

`project_id` vient de la variable `GOOGLE_CLOUD_PROJECT`, du projet actif de `gcloud` ou du serveur de métadonnées ; il peut valoir `None` avec un fichier de fédération. Le passer explicitement aux clients évite de dépendre de cette déduction.

```python
import google.auth
from google.auth.transport.requests import AuthorizedSession

credentials, project_id = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
    quota_project_id="PROJECT_ID",
)
session = AuthorizedSession(credentials)          # requests.Session qui pose et renouvelle le jeton
r = session.get(f"https://cloudresourcemanager.googleapis.com/v3/projects/{project_id}")
```

- **Scopes.** Les bibliothèques clientes posent elles-mêmes leurs scopes par défaut ; `scopes=` ne sert que pour un appel REST direct. Le scope `cloud-platform` couvre toutes les API Google Cloud : l'autorisation réelle se règle par IAM, pas par le scope.
- **Projet de quota.** Avec des identifiants d'utilisateur, l'appel est imputé au projet de quota. Il se fixe, du plus local au plus global : `client_options={"quota_project_id": "PROJECT_ID"}` sur un client, `quota_project_id=` de `google.auth.default()`, `credentials.with_quota_project("PROJECT_ID")`, la variable `GOOGLE_CLOUD_QUOTA_PROJECT`, puis la valeur écrite dans le fichier ADC par `gcloud auth application-default set-quota-project`. Le principal a besoin de `serviceusage.services.use` sur ce projet.

## Emprunter une identité dans le code

Un programme qui tourne sous une identité et doit agir sous une autre (un outil d'administration, un traitement multi-projets) emprunte le compte de service cible au lieu d'en télécharger la clé. Il faut `roles/iam.serviceAccountTokenCreator` sur le compte cible et l'API *IAM Service Account Credentials* activée.

```python
from google.auth import impersonated_credentials
from google.cloud import storage

source, _ = google.auth.default()
cible = impersonated_credentials.Credentials(
    source_credentials=source,
    target_principal="app-sa@PROJECT_ID.iam.gserviceaccount.com",
    target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
    lifetime=3600,                       # secondes, une heure au plus par défaut
)
client = storage.Client(project="PROJECT_ID", credentials=cible)
```

`delegates=[...]` décrit une chaîne d'emprunts, chaque maillon ayant le rôle *Token Creator* sur le suivant. Au-delà d'une heure, et jusqu'à 12 heures, la durée demande la contrainte d'organisation `constraints/iam.allowServiceAccountCredentialLifetimeExtension` pour ce compte.

## Jeton d'identité : appeler Cloud Run, une fonction ou IAP

Un service [Cloud Run](#cloud-run) ou une fonction Cloud Run qui exige l'authentification attend un **jeton d'identité** OIDC signé par Google, pas un jeton d'accès. Son champ `aud` (*audience*) désigne le destinataire ; il vit une heure.

| Destinataire | Audience | En-tête | Rôle de l'appelant |
|---|---|---|---|
| Service Cloud Run, fonction Cloud Run | URL du service (`https://SERVICE-HASH-REGION.a.run.app`), ou une audience personnalisée déclarée sur le service | `Authorization: Bearer`, ou `X-Serverless-Authorization` si l'application utilise déjà `Authorization` | `roles/run.invoker` |
| Ressource derrière [IAP](#identity-aware-proxy) | ID client OAuth 2.0 utilisé par IAP | `Authorization: Bearer`, ou `Proxy-Authorization: Bearer` | *IAP-secured Web App User* |

L'URL du service reste l'audience même pour un appel vers une URL d'étiquette de trafic ; un domaine personnalisé ne peut pas servir d'audience. Le schéma service à service est toujours le même : chaque service appelant a son compte de service attaché, qui reçoit `roles/run.invoker` sur le seul service appelé, et obtient ses jetons par le serveur de métadonnées.

```python
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2 import id_token

AUDIENCE = "https://facturation-abc123-ew.a.run.app"

# Identifiants qui produisent des jetons d'identité et se renouvellent seuls
jetons = id_token.fetch_id_token_credentials(AUDIENCE, request=Request())
facturation = AuthorizedSession(jetons)          # créée une fois par processus
r = facturation.post(f"{AUDIENCE}/factures", json={"client": "C-42"}, timeout=30)
```

`id_token.fetch_id_token(Request(), AUDIENCE)` renvoie directement la chaîne du jeton, sans cache. `fetch_id_token_credentials` lit une clé ou un emprunt désignés par `GOOGLE_APPLICATION_CREDENTIALS`, sinon le serveur de métadonnées ; il ne sait pas produire de jeton d'identité à partir d'identifiants d'utilisateur ni du fichier ADC par défaut. Sur un poste, on emprunte donc un compte de service :

```python
def identifiants_id_token(audience: str):
    creds, _ = google.auth.default()
    if isinstance(creds, impersonated_credentials.Credentials):   # ADC local par emprunt
        return impersonated_credentials.IDTokenCredentials(creds, target_audience=audience, include_email=True)
    return id_token.fetch_id_token_credentials(audience, request=Request())
```

En ligne de commande, `gcloud auth print-identity-token --impersonate-service-account=app-sa@PROJECT_ID.iam.gserviceaccount.com --audiences=AUDIENCE` donne le même jeton pour un test `curl`. Avec Workload Identity Federation, le jeton d'identité s'obtient de la même façon : `impersonated_credentials.Credentials` avec les identifiants fédérés comme source, puis `IDTokenCredentials`.

## Vérifier un jeton reçu

Quand Cloud Run contrôle l'accès par IAM, le jeton est vérifié avant d'atteindre le conteneur. Un service qui reçoit les appels sans ce contrôle (service public, *push* [Pub/Sub](#pubsub), tâche [Cloud Tasks](#cloud-tasks), [Cloud Scheduler](#cloud-scheduler)) vérifie lui-même signature, émetteur, expiration et audience, puis l'identité de l'appelant :

```python
import cachecontrol, requests
from google.oauth2 import id_token
from google.auth.transport.requests import Request

# Sans cache HTTP, chaque vérification retélécharge les certificats publics de Google
_requete = Request(session=cachecontrol.CacheControl(requests.Session()))

def appelant(en_tete_authorization: str) -> str:
    jeton = en_tete_authorization.removeprefix("Bearer ")
    infos = id_token.verify_oauth2_token(jeton, _requete, audience="https://SERVICE-HASH-REGION.a.run.app")
    if not infos.get("email_verified") or infos["email"] != "pubsub-push@PROJECT_ID.iam.gserviceaccount.com":
        raise PermissionError("Appelant non autorisé")
    return infos["email"]
```

`verify_oauth2_token` lève `ValueError` sur un jeton invalide ou expiré. Derrière IAP, l'application vérifie l'en-tête `x-goog-iap-jwt-assertion` avec `id_token.verify_token(jwt, Request(), audience=AUDIENCE_IAP, certs_url="https://www.gstatic.com/iap/verify/public_key")` ; l'audience vaut `/projects/PROJECT_NUMBER/locations/REGION/services/SERVICE` pour Cloud Run, `/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID` derrière un load balancer.

## Durée de vie et renouvellement

- Un jeton d'accès vit une heure, un jeton d'identité aussi. Les objets `Credentials` le conservent (`token`, `expiry`, `valid`) et se renouvellent seuls avant chaque requête dès qu'il reste moins de 3 min 45 s de validité.
- Un client ou une `AuthorizedSession` créés une fois par processus portent ce cache. `credentials.refresh(Request())` ne s'appelle à la main que pour extraire `credentials.token` à destination d'un outil qui n'accepte qu'une chaîne.
- Obtenir un jeton neuf à chaque requête ajoute un aller-retour vers le serveur de métadonnées ou vers IAM, et consomme le quota de l'API *IAM Service Account Credentials* en cas d'emprunt.

| Situation | Code |
|---|---|
| Appeler une API Google avec une bibliothèque cliente | `storage.Client(project="PROJECT_ID")` : ADC implicite |
| Appeler une API Google en REST | `AuthorizedSession(google.auth.default(scopes=[...])[0])` |
| Agir sous un autre compte de service | `impersonated_credentials.Credentials(source_credentials=..., target_principal=...)` |
| Appeler un service Cloud Run ou une fonction | `AuthorizedSession(id_token.fetch_id_token_credentials(URL, Request()))` |
| Même appel depuis un poste | ADC par emprunt, puis `impersonated_credentials.IDTokenCredentials` |
| Appeler une ressource IAP | Comme Cloud Run, avec l'ID client OAuth comme audience |
| Authentifier un appel reçu (push, tâche, service public) | `id_token.verify_oauth2_token(jeton, Request(), audience=...)` puis contrôle de `email` |
| Charge hors de Google Cloud | Fichier de fédération (`gcloud iam workload-identity-pools create-cred-config`) dans `GOOGLE_APPLICATION_CREDENTIALS`, code inchangé |

## Pièges

- **Mauvaise audience.** Un jeton destiné à l'URL d'un autre service ou à un domaine personnalisé est refusé. L'audience est l'URL du service appelé, et la vérification côté serveur doit la fixer : sans `audience=`, `verify_oauth2_token` accepte un jeton émis pour n'importe quel service.
- **Jeton d'accès envoyé à Cloud Run.** Cloud Run attend un jeton d'identité ; `credentials.token` d'identifiants obtenus par `google.auth.default()` est un jeton d'accès, fait pour les API `googleapis.com`.
- **Jeton dans les journaux.** Ne jamais journaliser l'en-tête `Authorization`, `credentials.token` ni une URL qui porte un jeton ; un jeton volé reste valable jusqu'à son expiration. Journaliser l'`email` et le `sub` extraits après vérification.
- **Clé téléchargée « pour aller plus vite ».** Une clé de compte de service copiée sur un poste ou dans une image contourne tout ce qui précède. Sur un poste : `gcloud auth application-default login --impersonate-service-account=...` ; en CI : fédération (voir [Déployer sans clé](#deployer-sans-cle)).
- **Scopes d'une VM.** Sur une VM Compute Engine, les *access scopes* de l'instance plafonnent le jeton du compte attaché : une instance restreinte obtient `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT` malgré les bons rôles. Donner le scope `cloud-platform` à l'instance et régler les droits par IAM.
- **`gcloud auth login` ne suffit pas.** Le code lit ADC, pas les identifiants de la CLI : `DefaultCredentialsError` sur un poste où seul `gcloud auth login` a été fait.
