---
title: Authentifier un appel à une API
subgroup: Identités et accès
---

## Choisir la méthode

Un appel aux API Google Cloud porte soit un **jeton OAuth 2.0 court** (une heure par défaut), obtenu à partir d'une identité, soit une **clé API** pour les API qui l'acceptent. La méthode dépend de l'endroit où tourne le code ; dans tous les cas où une identité est en jeu, le chemin recommandé ne fait circuler aucun secret longue durée.

| Où tourne le code | Méthode | Ce qui circule |
|---|---|---|
| Poste de développement, bibliothèques clientes | **ADC** avec les identifiants de l'utilisateur : `gcloud auth application-default login` | Fichier ADC local, jetons courts |
| Poste de développement, tester sous l'identité de l'application | **ADC par emprunt d'identité** d'un compte de service : `--impersonate-service-account` | Jetons courts du compte de service ; aucune clé |
| Appel `curl` ponctuel | **Jeton court** en en-tête `Authorization: Bearer $(gcloud auth print-access-token)` | Un jeton d'une heure |
| Sur Google Cloud : VM, Cloud Run, Cloud Run functions, Cloud Build | **Compte de service attaché** à la ressource, lu par ADC sur le serveur de métadonnées | Rien : les jetons sont fournis par la plateforme |
| Pod GKE | **Workload Identity Federation for GKE** : le compte de service Kubernetes devient un principal | Rien |
| Hors de Google Cloud : autre cloud, sur site, CI | **[Workload Identity Federation](#workload-identity-federation)** : fichier de configuration d'identifiants lu par ADC | Le jeton du fournisseur externe, échangé contre un jeton Google |
| API qui accepte les clés, sans identité à prouver | **Clé API** restreinte | La chaîne de la clé |
| Aucun des cas précédents | **Clé de compte de service**, en dernier recours | Une clé privée valable jusqu'à sa suppression |

C'est l'arbre de décision de la documentation ([Authentication methods](https://docs.cloud.google.com/docs/authentication)) : la clé de compte de service n'y apparaît qu'en toute dernière branche, pour une charge de travail hors de Google Cloud dont le fournisseur d'identité ne se fédère pas. Pour une CI GitHub Actions ou GitLab, voir [Déployer sans clé](#deployer-sans-cle).

## ADC

Les *Application Default Credentials* ne sont pas un type d'identifiant mais une **stratégie de recherche** des bibliothèques clientes, dans cet ordre :

1. la variable `GOOGLE_APPLICATION_CREDENTIALS`, qui pointe vers un fichier de configuration de fédération (personnel ou charge de travail) ou vers une clé de compte de service ;
2. le fichier écrit par `gcloud auth application-default login` (`~/.config/gcloud/application_default_credentials.json` sous Linux et macOS) ;
3. le compte de service attaché, fourni par le serveur de métadonnées.

L'ordre de recherche ne dit rien de la qualité de chaque source. En production sur Google Cloud, c'est le compte de service attaché qui doit répondre ; sur un poste, le fichier local. Le même code tourne dans les deux cas sans modification :

```python
from google.cloud import storage

client = storage.Client(project="PROJECT_ID")  # identifiants trouvés par ADC
```

```bash
# Poste de développement : ADC avec son propre compte
gcloud auth application-default login

# ... ou sous l'identité d'un compte de service, sans clé
gcloud auth application-default login \
  --impersonate-service-account=app-sa@PROJECT_ID.iam.gserviceaccount.com
```

> [!WARNING]
> Les identifiants de `gcloud` (`gcloud auth login`) et ceux d'ADC (`gcloud auth application-default login`) sont deux jeux distincts. La CLI n'utilise pas ADC : se connecter à l'un ne configure pas l'autre.

## Jeton court pour `curl`

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://cloudresourcemanager.googleapis.com/v3/projects/PROJECT_ID"

# Même appel sous l'identité d'un compte de service
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token \
    --impersonate-service-account=app-sa@PROJECT_ID.iam.gserviceaccount.com)" \
  "https://cloudresourcemanager.googleapis.com/v3/projects/PROJECT_ID"
```

Certaines API refusent un jeton d'utilisateur sans **projet de quota** : l'en-tête `x-goog-user-project: PROJECT_ID` désigne le projet facturé, qui demande la permission `serviceusage.services.use` (rôle *Service Usage Consumer*). Dans une application, `gcloud auth application-default print-access-token` donne le jeton qu'ADC utiliserait.

## Clé API restreinte

Une clé API **standard** n'identifie aucun principal : elle rattache l'appel à un projet pour la facturation et les quotas, et IAM ne vérifie rien. Elle ne sert qu'aux API qui l'acceptent (Maps, Natural Language, API Gemini...).

Console : **API et services → Identifiants → Créer des identifiants → Clé API**. La console et `gcloud` imposent au moins une **restriction d'API** (l'API REST, elle, crée une clé sans restriction si on n'en précise pas) ; ajouter aussi une **restriction d'application** (adresses IP, référents HTTP, application Android ou iOS). Une clé sans restriction est utilisable par quiconque la trouve, contre toutes les API qui acceptent les clés.

```bash
export API_KEY=VALEUR_DE_LA_CLE
curl -s -X POST -H "Content-Type: application/json" -H "x-goog-api-key: ${API_KEY}" \
  --data-binary @request.json \
  "https://language.googleapis.com/v1/documents:analyzeEntities"
```

L'en-tête `x-goog-api-key` est préférable au paramètre `?key=API_KEY`, qui finit dans les journaux des proxys et l'historique des navigateurs.

[!DECONSEILLE] Une **clé d'autorisation** est une clé API liée à un compte de service : l'appel est traité comme s'il venait de ce compte, à la manière d'un jeton d'accès longue durée. Elle sert à l'exploration rapide, par exemple Vertex AI en mode express ou l'API Gemini ; la contrainte `iam.managed.disableServiceAccountApiKeyCreation`, active par défaut, en limite la création, et la documentation déconseille de s'en servir en production pour les API qui créent ou gèrent des ressources : un compte de service dédié, par ADC, reste la voie normale.

## Compte de service dédié

Chaque application reçoit son propre compte de service, avec les seuls rôles dont elle a besoin (voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques)). Le compte s'utilise de deux façons, sans jamais produire de clé.

```bash
gcloud iam service-accounts create app-sa --display-name="Application de facturation"

# 1) Attaché à la ressource : le code obtient ses jetons par le serveur de métadonnées
gcloud run deploy facturation --image=IMAGE --region=REGION \
  --service-account=app-sa@PROJECT_ID.iam.gserviceaccount.com

# 2) Emprunté par un humain ou un pipeline, pour des jetons courts
gcloud iam service-accounts add-iam-policy-binding app-sa@PROJECT_ID.iam.gserviceaccount.com \
  --member="group:equipe-facturation@example.com" --role="roles/iam.serviceAccountTokenCreator"
gcloud config set auth/impersonate_service_account app-sa@PROJECT_ID.iam.gserviceaccount.com
```

- **Attacher** un compte à une ressource demande `roles/iam.serviceAccountUser` sur ce compte (permission `iam.serviceAccounts.actAs`) : qui peut attacher un compte peut agir avec ses droits.
- **Emprunter** demande `roles/iam.serviceAccountTokenCreator` sur le compte et l'API *IAM Service Account Credentials* activée. Chaque jeton émis est tracé dans Cloud Audit Logs avec l'identité de l'appelant, ce qu'une clé partagée ne permet pas.
- `--impersonate-service-account` vaut pour une seule commande ; la propriété `auth/impersonate_service_account` pour toutes les commandes de la configuration active.

### Clé de compte de service, en dernier recours

Une clé JSON ne se justifie que pour une charge de travail hors de Google Cloud dont le fournisseur d'identité ne peut pas être fédéré. Sa création est bloquée par la contrainte d'organisation `iam.managed.disableServiceAccountKeyCreation`, appliquée par défaut aux organisations créées depuis le 3 mai 2024 : il faut une exception explicite, projet par projet.

```bash
gcloud iam service-accounts keys create ~/key.json \
  --iam-account=app-sa@PROJECT_ID.iam.gserviceaccount.com

# Lue par ADC dans le code
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key.json"

# Identité active de gcloud
gcloud auth login --cred-file="$HOME/key.json"
```

> [!WARNING]
> Une clé de compte de service est un secret longue durée : elle reste valable jusqu'à sa suppression, s'utilise sans aucune authentification préalable et finit souvent dans un dépôt ou un dossier de téléchargements. Si elle est inévitable : une durée de vie maximale par la contrainte `iam.serviceAccountKeyExpiryHours`, la désactivation automatique des clés publiées par `iam.serviceAccountKeyExposureResponse` réglée sur `DISABLE_KEY`, une rotation planifiée, et jamais le rôle Éditeur dans un projet qui autorise les clés.

Commandes associées dans [gcloud : contexte et configuration](#gcloud-config).

## Alternatives en logiciel libre

- **SPIFFE** et **SPIRE** (Apache 2.0) : identité de charge de travail attestée par la plateforme et délivrée en certificats X.509 ou JWT courts, renouvelés automatiquement ; l'équivalent du compte de service attaché, sur n'importe quelle infrastructure.
- **OpenBao** (MPL 2.0) : ses méthodes d'authentification (Kubernetes, JWT/OIDC, cloud) échangent une identité de plateforme contre un jeton court et des secrets dynamiques, comme l'emprunt d'identité ou la fédération ; Vault, dont il dérive, est sous BSL.
- **Keycloak** (Apache 2.0) : serveur OAuth 2.0 et OIDC, avec *client credentials* pour les services et échange de jetons (RFC 8693), le standard sur lequel repose Workload Identity Federation.
- **Dex** (Apache 2.0) : fournisseur OIDC léger qui fédère des annuaires amont (LDAP, SAML, GitHub) et émet des jetons d'identité pour les services en aval.
- **step-ca** (Apache 2.0) : autorité de certification qui délivre des certificats clients courts à partir d'une identité de plateforme (jeton OIDC, instance cloud, Kubernetes), pour l'authentification par certificat plutôt que par clé statique.
