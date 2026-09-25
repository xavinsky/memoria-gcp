---
title: "Notifications et tickets : Slack, Jira et les autres"
---

Quatre services émettent les événements qu'une équipe veut voir dans ses outils : [Cloud Monitoring](#cloud-monitoring) (règles d'alerte), [Error Reporting](#error-reporting) (nouvelles erreurs), [Cloud Build](#cloud-build) (état des builds) et [Cloud Deploy](#cloud-deploy) (rollouts, approbations). Deux chemins en sortent : les **canaux de notification** natifs, qui livrent un message tout fait à Slack, PagerDuty ou une adresse e-mail, et **[Pub/Sub](#pubsub)**, qui livre un JSON à un code qu'on écrit soi-même. Cette section traite du branchement ; l'usage en production (astreinte, SLO, runbooks) relève du groupe Exploitation de l'onglet Plateforme.

![Routage des notifications vers la messagerie, l'astreinte et les tickets](../../svg/routage-notifications.svg)

## Ce que chaque service sait émettre

| Source | Mécanisme | Destinations sans code | Vers Pub/Sub |
|---|---|---|---|
| **Cloud Monitoring** | Canaux de notification attachés à une règle d'alerte | E-mail, SMS, application mobile Cloud, Slack, PagerDuty, webhook, Google Chat [!PREVERSION] | Canal de type `pubsub` |
| **Error Reporting** | Canaux de Cloud Monitoring, choisis dans **Configurer les notifications** | E-mail, application mobile, Slack, webhook | Aucun : passer par un webhook |
| **Cloud Build** | Message à chaque changement d'état sur le sujet `cloud-builds`, ou celui de `options.pubsubTopic` | *Notifiers* : images fournies à déployer sur Cloud Run (Slack, SMTP, HTTP, BigQuery, Google Chat, GitHub Issues) | Natif |
| **Cloud Deploy** | Sujets `clouddeploy-resources`, `clouddeploy-operations`, `clouddeploy-approvals`, `clouddeploy-advances`, à créer | Aucune | Natif |

**Jira n'a pas de canal natif.** Deux voies existent. Jira Service Management propose une intégration « Google Cloud's operations suite » : un canal webhook de Cloud Monitoring envoie l'incident, qui devient une **alerte** d'astreinte JSM, ouverte et fermée en même temps que l'incident. Pour un **ticket** Jira (bug, tâche dans un projet), il faut une fonction qui appelle l'API REST de Jira. Microsoft Teams est dans le même cas : Google renvoie vers Power Automate ou une fonction Cloud Run.

## Canal natif ou Pub/Sub et fonction ?

| Besoin | Choix | Pourquoi |
|---|---|---|
| Prévenir un canal Slack d'équipe | Canal **Slack** de Monitoring | Autorisation OAuth en un clic ; inviter `@Google Cloud Monitoring` dans un canal privé |
| Astreinte avec escalade | Canal **PagerDuty**, ou webhook vers JSM | Planning et escalade restent dans l'outil d'astreinte |
| Ticket Jira dédoublonné, avec champs métier | **Pub/Sub + fonction** | Aucun canal ne connaît Jira ; le code décide du projet, du type et de la clé de dédoublonnage |
| Destination sur un réseau privé | **Pub/Sub** | Un webhook n'appelle que des adresses publiques |
| Automatisation qui lit le contenu | **Webhook** ou **Pub/Sub** | Google ne garantit le format que pour ces deux canaux (schéma 1.2) |
| Résultat de build dans Slack ou Chat | **Notifier** Cloud Build | Filtre CEL (`build.status == Build.Status.FAILURE`) et gabarit fournis |
| Approbation Cloud Deploy traitée dans Jira | Sujet `clouddeploy-approvals` + fonction | Crée le ticket, puis `gcloud deploy rollouts approve` une fois le ticket validé |

L'application mobile, PagerDuty, les webhooks et Slack passent par le même service interne de Google : doubler un canal critique par un e-mail ou un canal Pub/Sub.

## Brancher Cloud Monitoring sur Pub/Sub

```bash
gcloud pubsub topics create alertes
gcloud beta monitoring channels create --display-name="Routage alertes" \
  --type=pubsub --channel-labels=topic=projects/PROJECT_ID/topics/alertes
# L'agent de service de Monitoring, créé avec le premier canal Pub/Sub, publie dans le sujet
gcloud pubsub topics add-iam-policy-binding alertes --role=roles/pubsub.publisher \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-monitoring-notification.iam.gserviceaccount.com
```

Le canal s'ajoute ensuite à la règle d'alerte. Chaque message porte un objet `incident` : `incident_id`, `state` (`open` ou `closed`), `policy_name`, `summary`, `url` vers la console. Pour Cloud Build et Cloud Deploy, créer le sujet suffit (`gcloud pubsub topics create cloud-builds`) ; leurs attributs donnent `buildId` et `status`, ou `Action` et `ResourceType`.

## Fonction de routage

La fonction reçoit l'incident par un déclencheur [Eventarc](#eventarc), cherche un ticket portant l'identifiant de l'incident, commente s'il existe, en crée un sinon, puis poste dans Slack par un *incoming webhook*.

```python
import base64, json, os

import functions_framework
import requests

JIRA = os.environ["JIRA_URL"]                                # https://SITE.atlassian.net
AUTH = (os.environ["JIRA_USER"], os.environ["JIRA_TOKEN"])   # jeton injecté depuis Secret Manager
SLACK = os.environ["SLACK_WEBHOOK_URL"]


def adf(texte):
    """Texte au format Atlassian Document Format, exigé par l'API v3."""
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": texte}]}]}


@functions_framework.cloud_event
def router(cloud_event):
    incident = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))["incident"]
    etiquette = "gcp-" + incident["incident_id"]
    texte = f'{incident["summary"]}\n{incident["url"]}'

    r = requests.get(f"{JIRA}/rest/api/3/search/jql", auth=AUTH, timeout=10,
                     params={"jql": f'labels = "{etiquette}"', "fields": "key", "maxResults": 1})
    r.raise_for_status()
    if tickets := r.json()["issues"]:
        cle = tickets[0]["key"]
        requests.post(f"{JIRA}/rest/api/3/issue/{cle}/comment", auth=AUTH, timeout=10,
                      json={"body": adf(f'État {incident["state"]} : {texte}')}).raise_for_status()
    elif incident["state"] == "open":
        r = requests.post(f"{JIRA}/rest/api/3/issue", auth=AUTH, timeout=10, json={"fields": {
            "project": {"key": "OPS"}, "issuetype": {"name": "Bug"}, "labels": [etiquette],
            "summary": f'[GCP] {incident["policy_name"]}', "description": adf(texte)}})
        r.raise_for_status()
        cle = r.json()["key"]
    else:
        return
    requests.post(SLACK, timeout=10, json={"text": f'{cle} : {incident["summary"]}'}).raise_for_status()
```

```bash
echo -n "JETON_API" | gcloud secrets versions add jira-token --data-file=-   # secret créé au préalable
gcloud run deploy routeur-alertes --source . --function router --base-image python314 \
  --region REGION --no-allow-unauthenticated \
  --service-account routeur@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars JIRA_URL=https://SITE.atlassian.net,JIRA_USER=robot@example.com \
  --set-secrets JIRA_TOKEN=jira-token:latest,SLACK_WEBHOOK_URL=slack-webhook:latest
gcloud eventarc triggers create alertes-vers-routeur --location=REGION \
  --destination-run-service=routeur-alertes --destination-run-region=REGION \
  --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
  --transport-topic=projects/PROJECT_ID/topics/alertes \
  --service-account=declencheur@PROJECT_ID.iam.gserviceaccount.com
```

Le compte `routeur` reçoit `roles/secretmanager.secretAccessor` sur les deux secrets, le compte `declencheur` `roles/run.invoker` sur le service. Le fichier `requirements.txt` liste `functions-framework` et `requests`.

## Pièges

- **Tempête d'alertes.** Une condition sans agrégation ouvre un incident par série temporelle : une règle sur 200 VM peut créer 200 tickets. Agréger dans la condition, ou dédoublonner sur `policy_name` plutôt que sur `incident_id`. Côté règle, `renotifyInterval` (de 30 minutes à 24 heures) renvoie des rappels, `notificationRateLimit` est obligatoire sur une alerte basée sur les journaux, et une mise en sourdine (*snooze*) couvre une maintenance.
- **Doublons malgré la recherche.** La recherche JQL n'est pas immédiatement à jour : deux messages rapprochés pour le même incident peuvent créer deux tickets. Pour un dédoublonnage strict, tenir la correspondance incident → ticket dans une base (Firestore) ; avec les relances Eventarc activées, la fonction doit supporter d'être rejouée.
- **Jetons Jira.** Un jeton d'API Atlassian expire au bout d'un an au plus (1 à 365 jours) : le stocker dans [Secret Manager](#secret-manager), sous un compte technique, et suivre sa date d'expiration. Un jeton **à portée** (*scoped*) s'utilise sur `https://api.atlassian.com/ex/jira/CLOUD_ID`, pas sur l'URL du site.
- **URL de webhook Slack.** Elle contient le secret : hors du dépôt, dans Secret Manager ; Slack révoque les URL qu'il trouve publiées.
- **Webhook entrant de Monitoring.** L'adresse doit être publique ; l'authentification se limite à l'authentification de base ou à un jeton en paramètre d'URL (`?auth_token=...`), à vérifier dans le code. Une fonction Cloud Run derrière un webhook doit donc accepter les appels non authentifiés : Pub/Sub évite ce compromis, sauf pour Error Reporting, qui n'a pas de canal Pub/Sub. Les webhooks d'Error Reporting suivent le schéma 1.0, ceux de Monitoring le schéma 1.2.
- **Boucle Cloud Build.** Un déclencheur Pub/Sub branché sur le sujet des notifications relance un build à chaque notification : deux sujets distincts.
- **Abonnement *push* des notifiers.** Il expire après 31 jours sans message ; un projet où l'on construit rarement perd ses notifications en silence. Créer l'abonnement avec `--expiration-period=never`.

## Alternatives en logiciel libre

- **Alertmanager** (Apache 2.0) : regroupement, dédoublonnage, inhibition et routage des alertes vers Slack, Mattermost, Rocket.Chat, PagerDuty, Jira ou un webhook ; le rôle du canal et de la fonction de routage, pour des alertes Prometheus.
- **Zulip** (Apache 2.0) et **Mattermost** (AGPL v3 pour le code source) : messagerie d'équipe auto-hébergée, avec webhooks entrants au format compatible Slack pour la plupart des intégrations.
- **Redmine** (GPL v2) pour le suivi de tickets et de projets, **GLPI** (GPL v3) pour le centre de services et la gestion de parc : tickets créés par leur API REST depuis la même fonction de routage qu'un ticket Jira.
- **Zammad** (AGPL v3) : plateforme de support et de tickets, avec API et webhooks, pour les incidents qui débouchent sur une relation avec des utilisateurs.
- **Apprise** (BSD 2-Clause) : bibliothèque Python qui envoie une même notification vers une centaine de services à partir d'URL ; elle remplace le code d'appel propre à chaque destination dans la fonction.
- **ntfy** (Apache 2.0 ou GPL v2) : notifications *push* sur mobile et poste par simple requête HTTP, pour une alerte individuelle sans outil d'astreinte.
