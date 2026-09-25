---
title: Déployer un agent
---

Déployer un agent, c'est répondre à trois questions : **où tourne la boucle** (Agent Runtime, Cloud Run ou GKE), **par où arrivent les utilisateurs** (Gemini Enterprise app, un canal de centre de contact, une interface maison) et **avec quelle identité l'agent agit**. Agent Runtime est le service géré d'[Agent Platform](#gemini-enterprise-agent-platform) conçu pour les agents : sessions, mémoire, identité d'agent et traces y sont intégrées. Cloud Run et GKE font tourner le même code ADK dans un conteneur dont on gère soi-même les services annexes.

![Architecture de production d'un agent sur Google Cloud](../../svg/agent-production.svg)

Les salariés passent par Gemini Enterprise, les clients par une interface sur Cloud Run ; les deux appellent l'agent sur Agent Runtime. L'agent appelle Gemini directement, garde ses conversations dans Sessions et Memory Bank, atteint ses outils MCP, ses API et les autres agents à travers Agent Gateway, et les ressources privées par une interface Private Service Connect. La CI/CD déploie chaque version, et les traces partent vers Cloud Trace.

## Choisir la cible

| Critère | Agent Runtime | [Cloud Run](#cloud-run) | [GKE](#gke) |
|---|---|---|---|
| Ce qu'on déploie | Code ADK, LangChain, LangGraph, AG2, LlamaIndex ; ou conteneur qui respecte le contrat d'exécution (HTTP sur le port 8080) | Conteneur : serveur d'API ADK (FastAPI) généré, ou application maison | Conteneur et manifestes Kubernetes |
| Commande | `adk deploy agent_engine`, `agents-cli deploy`, SDK `client.runtimes.create()` | `adk deploy cloud_run`, `gcloud run deploy` | `adk deploy gke` |
| Sessions et mémoire | Gérées : Sessions, Memory Bank | À brancher : `--session_service_uri` vers Agent Platform Sessions (`agentengine://ID`) ou une base SQL ; en mémoire par défaut | Idem Cloud Run |
| Mise à l'échelle | `min_instances` de 0 à 10 (1 par défaut), `max_instances` de 1 à 1 000 (100), 1 à 8 vCPU et 1 à 32 Gio par conteneur, `container_concurrency` 9 par défaut | Autoscaling de Cloud Run, jusqu'à zéro instance | Autoscaling des pods et des nœuds, GPU disponibles |
| Identité | Identité d'agent (SPIFFE), ou compte de service | Compte de service du service ; identité d'agent prise en charge | Workload Identity Federation for GKE |
| Réseau privé | Interface Private Service Connect vers un VPC ; VPC Service Controls | Sortie VPC directe ; VPC Service Controls | Réseau du cluster |
| Exposition | Enregistrement dans Gemini Enterprise app ; *playground* de la console ; A2A [!PREVERSION] | URL HTTPS, point de terminaison A2A (`--a2a`) | Service, load balancer |
| Facturation | vCPU-heure et Gio-heure allouées, à la seconde ; l'attente entre deux tours n'est pas facturée | Tarif Cloud Run | Nœuds du cluster |
| Quand la choisir | Par défaut pour un agent en production, et obligatoire pour un agent ADK publié dans Gemini Enterprise | L'agent fait partie d'une application web, ou il faut maîtriser le serveur HTTP | Cluster existant, modèle ouvert servi à côté (vLLM), contraintes de plateforme |

Les outils et l'API gardent le nom Agent Engine : la commande est `adk deploy agent_engine`, le fichier de configuration `.agent_engine_config.json`, la ressource d'API `reasoningEngines` (URL `REGION-aiplatform.googleapis.com`). Le SDK Python est `google-cloud-agentplatform` (module `agentplatform`, `client.runtimes`) ; une partie de la documentation utilise `google-cloud-aiplatform` (module `vertexai`, `client.agent_engines`).

```bash
# Agent Runtime, avec une identité d'agent propre
echo '{"identity_type": "AGENT_IDENTITY"}' > assistant_stock/.agent_engine_config.json
adk deploy agent_engine --project=PROJECT_ID --region=REGION \
  --display_name="Assistant stock" --otel_to_cloud assistant_stock
# nouvelle version du même agent : ajouter --agent_engine_id=RESOURCE_ID

# Cloud Run, sessions conservées dans Agent Platform Sessions, accès authentifié
adk deploy cloud_run --project=PROJECT_ID --region=REGION \
  --session_service_uri=agentengine://RESOURCE_ID assistant_stock \
  -- --no-allow-unauthenticated
```

```python
# Appeler l'agent déployé sur Agent Runtime (pip install google-cloud-agentplatform)
import agentplatform

client = agentplatform.Client(project="PROJECT_ID", location="REGION")
agent = client.runtimes.get(name="projects/PROJECT_ID/locations/REGION/reasoningEngines/RESOURCE_ID")

async for event in agent.async_stream_query(user_id="u-42", message="Stock de A-1024 ?"):
    print(event)
```

Sans le SDK, le même appel est un POST sur `…/reasoningEngines/RESOURCE_ID:streamQuery` (ou `:query`) avec `{"class_method": "async_stream_query", "input": {...}}`. Pour une chaîne complète, **Agents CLI** (`agents-cli scaffold enhance`, `agents-cli infra setup-cicd`, `agents-cli deploy`) génère le Terraform et une CI Cloud Build ou GitHub Actions ; le déploiement se fait aussi depuis un dépôt relié par [Developer Connect](#developer-connect).

## Exposer l'agent

| Public | Canal | Mise en œuvre |
|---|---|---|
| Salariés | [Gemini Enterprise app](#gemini-enterprise-app) | Un administrateur enregistre l'agent ADK hébergé sur Agent Runtime (console, API REST, ou `agents-cli publish gemini-enterprise`). L'agent reçoit l'adresse e-mail de l'utilisateur ; une ressource d'autorisation OAuth lui permet d'agir pour son compte. Les agents A2A s'enregistrent aussi |
| Clients au téléphone ou en chat | [Customer Experience Agent Studio](#customer-experience-agent-studio) | L'agent conversationnel se construit dans l'atelier, avec ses canaux (téléphonie, widget web, centres de contact) ; la logique métier de l'agent ADK s'y branche en outil OpenAPI ou MCP servi par Cloud Run |
| Application maison | Interface sur Cloud Run, ou application existante | Le serveur appelle Agent Runtime par le SDK ou REST, en flux ; il gère lui-même l'authentification des utilisateurs et transmet un `user_id` stable pour les sessions |

> [!WARNING]
> Les réglages Model Armor de la console Gemini Enterprise ne protègent pas les agents ADK enregistrés : le filtrage se configure dans le code de l'agent (`ModelArmorPlugin`) ou sur Agent Gateway.

## Identité et sécurité

- **Identité d'agent.** Avec `identity_type` à `AGENT_IDENTITY`, l'agent reçoit un principal propre, dérivé de l'ID de sa ressource (format ci-dessous), et un certificat X.509 renouvelé automatiquement. Ses jetons sont liés au certificat : ils ne se rejouent pas hors de l'environnement d'exécution, et aucune clé longue durée n'existe. On lui accorde des rôles comme à tout principal. Sans ce réglage, l'agent utilise l'agent de service `service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`, commun à tous les agents du projet, ou un compte de service désigné par `service_account`.

  ```bash
  gcloud projects add-iam-policy-binding PROJECT_ID --role=roles/bigquery.dataViewer \
    --member="principal://agents.global.org-ORGANIZATION_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/REGION/reasoningEngines/RESOURCE_ID"
  ```

- **Identifiants tiers.** L'*auth manager* d'Agent Identity conserve clés API et clients OAuth, et mène le consentement de l'utilisateur quand l'agent agit en son nom ; les journaux d'audit portent alors les deux identités.
- **Secrets.** Une variable d'environnement peut référencer [Secret Manager](#secret-manager) (`{"secret": SECRET_ID, "version": VERSION}`) ; avec une identité d'agent, c'est l'agent de service Agent Platform qui lit le secret au déploiement et doit avoir `roles/secretmanager.secretAccessor`.
- **Réseau.** L'interface [Private Service Connect](#private-service-connect) (`psc_interface_config`, sur un rattachement réseau) donne accès aux bases et API internes. [VPC Service Controls](#vpc-service-controls) couvre Agent Runtime, Sessions, Memory Bank, l'évaluation et Code Execution ; avec VPC Service Controls ou une interface PSC, `max_instances` est limité à 100. Dans un périmètre, `adk deploy --worker_pool` construit l'image sur un pool privé Cloud Build.
- **Agent Gateway.** Point d'entrée et de sortie de tout le trafic des agents : il n'autorise que les destinations inscrites dans Agent Registry et accordées par une stratégie IAM (tout est refusé par défaut), applique Model Armor aux requêtes et réponses et des règles de gouvernance sémantique écrites en langage naturel.
- **Posture.** [AI Protection](https://docs.cloud.google.com/security-command-center/docs/ai-protection-overview), dans [Security Command Center](#security-command-center), inventorie les ressources d'IA du projet ou de l'organisation : modèles, endpoints, sources de données, serveurs MCP inscrits dans Agent Registry. Le niveau Premium y ajoute la détection des agents Agent Runtime aux droits excessifs, les vulnérabilités et secrets en clair des agents déployés, et les chemins d'attaque qui passent par eux.

## Observabilité

- **Traces.** `--otel_to_cloud`, ou la variable `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`, envoie à [Cloud Trace](#cloud-trace) un *span* par appel de modèle et d'outil, avec les métriques. `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY` y ajoute les *prompts*, les réponses et l'identifiant utilisateur : données personnelles, à couvrir par le consentement et la politique de conservation. L'API Telemetry (OTLP) doit être activée.
- **Journaux.** Ce que l'agent écrit sur la sortie standard et la sortie d'erreur arrive dans [Cloud Logging](#cloud-logging) sous `reasoning_engine_stdout` et `reasoning_engine_stderr`, en texte ; le module `logging` de Python branché sur Cloud Logging produit des journaux structurés.
- **Qualité.** Le service d'évaluation rejoue des jeux de test et évalue le trafic réel ; le service de retours relie l'avis de l'utilisateur à la trace de la conversation (voir [Évaluer et sécuriser](#evaluer-et-securiser)).
- **Objectifs de service (SLO).** Chiffrer ce que l'utilisateur perçoit, puis alerter sur la consommation du budget d'erreur. Exemples du [Well-Architected Framework](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/reliability) : 99,9 % d'appels réussis, délai avant le premier jeton sous 500 ms pour 99 % des requêtes, moins de 0,1 % de réponses nuisibles ; pour un agent, s'y ajoute le taux de tâches menées à bien.

## Coûts

| Poste | Unité (tarifs consultés le 24 septembre 2026) |
|---|---|
| Modèle | Jetons d'entrée et de sortie à chaque tour de la boucle : le plus souvent le poste principal (voir [Choisir un modèle](#choisir-un-modele)) |
| Agent Runtime, Code Execution | 0,085 $ par vCPU-heure et 0,009 $ par Gio-heure, à la seconde ; 50 vCPU-heures et 100 Gio-heures gratuites par mois |
| Sessions, Memory Bank | Stockage à 0,30 $ par Gio-mois ; une vCPU-heure par million d'écritures et par trois millions de lectures |
| Agent Gateway (sortie) | Une vCPU-heure par 15 000 appels ou autorisations |
| Gemini Enterprise app | Postes utilisateurs selon l'édition, en plus du coût de l'agent |

La facture totale ne dit pas si l'agent est rentable : suivre un coût unitaire, par conversation ou par tâche menée à bien, à partir des jetons de chaque trace et des étiquettes de facturation, et le rapporter à la valeur métier visée ([Well-Architected Framework, optimisation des coûts](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/cost-optimization)).

## Pièges

- **Des sessions en mémoire.** Sur Cloud Run et GKE, sans `--session_service_uri` ni `--artifact_service_uri`, sessions et artefacts disparaissent au recyclage d'une instance.
- **Le démarrage à froid.** Une requête qui arrive sans instance libre attend son démarrage : de l'ordre de 4,7 s contre 0,4 s à chaud dans l'exemple de la documentation. Régler `min_instances` sur le trafic de base ; pour un agent asynchrone comme ADK, monter `container_concurrency` à un multiple de 9 (36 pour commencer), sans aller jusqu'au manque de mémoire.
- **Des droits qui survivent à l'agent.** Supprimer un agent ne retire pas les liaisons IAM de son identité, et un agent redéployé sous un nouvel ID reçoit un nouveau principal : les anciennes liaisons ne s'appliquent plus et restent à nettoyer.
- **L'agent de service par défaut.** Partagé par tous les agents du projet, il cumule les droits de chacun : identité d'agent ou compte de service dédié dès qu'un agent touche des données.
- **Une interface de développement en production.** `adk web` et `adk deploy cloud_run --with_ui` servent au test ; `--allow-unauthenticated` ouvre l'agent à Internet.
- **Des variables réservées.** Ne pas définir `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `PORT`, `GOOGLE_APPLICATION_CREDENTIALS` ni de nom commençant par `GOOGLE_CLOUD_AGENT_ENGINE` dans `env_vars` : Agent Runtime les fournit.
- **Les révisions accumulées.** Chaque mise à jour du code ou de l'environnement crée une révision immuable ; la répartition du trafic entre révisions [!PREVERSION] (API `v1beta1`) sert au déploiement progressif, dans la limite de 950 révisions par agent et 6 000 par projet et région. Supprimer les anciennes.
- **Une version d'ADK qui dérive.** `adk deploy` embarque par défaut la version d'ADK installée sur le poste qui déploie ; la figer (`--adk_version`) dans la CI.

## Alternatives en logiciel libre

- **kagent** (Apache 2.0, projet de la CNCF) : agents, outils MCP et modèles déclarés comme ressources Kubernetes, exécutés par ADK ; le plus proche d'Agent Runtime, sur un cluster qu'on exploite soi-même.
- **Knative Serving** (Apache 2.0) : conteneurs HTTP mis à l'échelle jusqu'à zéro sur Kubernetes, le modèle d'exécution de Cloud Run pour un serveur d'API ADK.
- **Mem0** (Apache 2.0) : mémoire à long terme extraite des conversations par un modèle et rangée dans une base vectorielle, l'équivalent de Memory Bank ; les sessions elles-mêmes vont dans PostgreSQL par le `DatabaseSessionService` d'ADK.
- **agentgateway** (Apache 2.0) : proxy de sortie des agents, qui n'autorise que les serveurs MCP, agents A2A et modèles déclarés (voir [MCP et A2A](#protocoles-mcp-a2a)).
- **SPIRE** (Apache 2.0), l'implémentation de SPIFFE : identités de charge de travail par certificats X.509 courts et renouvelés, sans clé longue durée, soit le mécanisme sur lequel repose l'identité d'agent. **Keycloak** (Apache 2.0) gère OAuth et le consentement quand l'agent agit pour un utilisateur.
- **OpenTelemetry** (Apache 2.0) avec **Langfuse** (MIT, hors répertoires `ee`) : traces des appels de modèle et d'outils selon les conventions GenAI, puis exploration, coûts et retours utilisateurs dans une interface auto-hébergée ; face à Cloud Trace et au service de retours.
