---
title: "MCP et A2A : outils et agents interopérables"
---

Deux protocoles ouverts, deux relations. **MCP** (*Model Context Protocol*) relie un agent à ses **outils et données** : l'agent est client, le serveur expose des capacités décrites par un schéma. **A2A** (*Agent2Agent*) relie un agent à un **autre agent**, traité comme un pair opaque : on lui confie une tâche, on reçoit des messages et des artefacts, sans voir ses outils ni sa mémoire. La documentation d'A2A résume l'écart : MCP approfondit un agent, A2A étend la portée du système. Un même agent ADK fait souvent les deux.

![Un agent ADK entre serveurs MCP et agents A2A](../../svg/mcp-a2a.svg)

## MCP ou A2A

| Critère | MCP | A2A |
|---|---|---|
| Ce qu'on appelle | Un **outil**, une ressource : entrée et sortie structurées, souvent sans état | Un **agent** : il raisonne, choisit ses outils, tient un dialogue sur plusieurs tours |
| Découverte | `tools/list`, `resources/list`, `prompts/list` ; `server/discover` pour les versions et capacités | **Carte d'agent** (*Agent Card*) en JSON, à `/.well-known/agent-card.json` ou dans un registre |
| Unité d'échange | Appel d'outil (`tools/call`) et son résultat | **Tâche** avec un état, des **messages** faits de *parts* (texte, fichier, données JSON) et des **artefacts** produits |
| Durée | Appel court ; l'extension officielle `tasks` pour un traitement long | Tâche longue native : états `WORKING`, `INPUT_REQUIRED`, `AUTH_REQUIRED`, flux SSE, notifications *push* par webhook |
| Transport | stdio (local), *Streamable HTTP* (distant) ; JSON-RPC | JSON-RPC 2.0 sur HTTP, gRPC ou HTTP/REST ; HTTPS obligatoire en production |
| Authentification | OAuth 2.1 pour les transports HTTP | Schémas déclarés dans la carte (clé API, OAuth 2, OIDC, mTLS), jetons dans les en-têtes HTTP |
| Dans ADK | `McpToolset` consomme, `to_mcp_server()` expose un agent comme un outil MCP | `RemoteA2aAgent` consomme, `to_a2a()` expose un agent |
| Choisir quand | L'appelant décide quoi faire, le serveur exécute | Le travail relève d'une autre équipe, d'un autre cadre (LangGraph, CrewAI), ou demande son propre raisonnement |

Un sous-agent du même programme n'a besoin d'aucun des deux : A2A ajoute un aller-retour réseau et une sérialisation qui ne se justifient que pour un agent déployé à part (voir [Construire un agent](#construire-un-agent)).

## MCP

- **Rôles.** L'**hôte** est l'application d'IA (un agent ADK, un IDE, Gemini CLI) ; il ouvre un **client** par serveur ; le **serveur** expose un service.
- **Primitives du serveur.** Les **outils** sont des actions décrites par un schéma JSON d'entrée ; les **ressources** des données en lecture (fichier, schéma de base) ; les **prompts** des modèles de messages. Le serveur peut demander une information à l'utilisateur (*elicitation*) en renvoyant un résultat `input_required` que le client complète en rejouant la requête.
- **Transports.** stdio : le client lance le serveur en sous-processus sur la même machine. Streamable HTTP : un point de terminaison unique qui reçoit des POST et répond en JSON ou en flux SSE propre à la requête. Le transport HTTP+SSE [!DECONSEILLE] est déprécié : Streamable HTTP le remplace.
- **Révision 2026-07-28 de la spécification.** Le protocole est sans état : pas de poignée de main `initialize`, pas d'en-tête `Mcp-Session-Id`, chaque requête porte sa version et les capacités du client dans `_meta`. Un état qui doit durer d'un appel à l'autre passe par un identifiant fourni par le serveur, en argument d'outil. Les serveurs distants de Google Cloud implémentent cette révision.

**L'offre MCP de Google Cloud :**

| Brique | Ce que c'est | Exploitation |
|---|---|---|
| **Serveurs MCP distants Google Cloud** | Un point de terminaison géré par produit, `https://SERVICE.googleapis.com/mcp` : BigQuery, AlloyDB, Cloud SQL, Spanner, Firestore, Bigtable, GKE, Cloud Run, Compute Engine, Cloud Logging, Cloud Monitoring, Pub/Sub, Agent Search, IAM et d'autres | Rien à déployer : activer l'API du produit (`gcloud services enable bigquery.googleapis.com`), donner `roles/mcp.toolUser` plus les rôles du produit. Certains serveurs découpent leurs outils en *toolsets*, chacun avec son point de terminaison |
| **MCP Toolbox for Databases** | Serveur MCP open source : sources, outils (requêtes SQL paramétrées) et *toolsets* déclarés dans `tools.yaml` ; bases Google Cloud et une vingtaine d'autres (PostgreSQL, MySQL, MongoDB, Neo4j…) | À déployer soi-même : Cloud Run, GKE, Docker. Côté ADK, `ToolboxToolset` (extra `google-adk[toolbox]`) |
| **Serveur MCP maison** | FastMCP ou SDK MCP, hébergé sur [Cloud Run](#cloud-run) ; ou une API existante publiée en MCP par [Apigee](#apigee) | Service à exploiter comme une API |
| **Agent Registry** | Catalogue des serveurs MCP, outils, agents et points de terminaison autorisés, dans [Agent Platform](#gemini-enterprise-agent-platform) | Sert de liste blanche à Agent Gateway, qui applique les règles d'accès (voir [Déployer un agent](#deployer-un-agent)) |

Un serveur distant Google expose des outils généraux (`execute_sql` exécute tout le SQL de BigQuery) ; MCP Toolbox expose des requêtes écrites à l'avance, que le modèle ne fait que paramétrer. Pour un agent en production face à des utilisateurs, la seconde forme laisse moins de latitude au modèle.

```python
import google.auth
from google.auth.transport.requests import Request
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery"])


def entetes(_contexte) -> dict[str, str]:
    if not credentials.valid:
        credentials.refresh(Request())
    return {"Authorization": f"Bearer {credentials.token}", "x-goog-user-project": "PROJECT_ID"}


bigquery = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="https://bigquery.googleapis.com/mcp"),
    header_provider=entetes,
    tool_filter=["list_table_ids", "get_table_info", "execute_sql_readonly"],
)

root_agent = Agent(
    name="analyste",
    model="gemini-3.5-flash",  # [*]
    instruction="Réponds aux questions sur le dataset DATASET en interrogeant BigQuery.",
    tools=[bigquery],
)
```

Les identifiants par défaut (ADC) sont ceux de l'identité qui exécute l'agent : compte de service ou identité d'agent en production, jamais le compte d'un développeur. `tool_filter` ne garde que les outils de lecture ; `execute_sql_readonly` n'accepte que des `SELECT`. `McpToolset` demande l'extra `pip install "google-adk[mcp]"`.

> [!TIP]
> [\*] Gemini 3.8 Flash (`gemini-3.8-flash`), le plus récent des Flash, peut être testé à la place de 3.5 Flash : il est plus capable, mais sa disponibilité est courte (pas de date de retrait garantie, préavis d'au moins 45 jours), il ne se règle pas, et il n'est servi que sur `global`, `us` et `eu` (voir [Choisir un modèle](#choisir-un-modele)).

## A2A

A2A est un standard ouvert hébergé par la Linux Foundation, en version 1.0 ; la définition Protobuf fait foi. Un serveur A2A publie sa **carte d'agent** : nom, description, version, interfaces (URL et liaison de protocole), capacités (`streaming`, `push_notifications`, carte étendue après authentification), **compétences** (*skills*) avec des exemples, schémas de sécurité et types MIME acceptés. Le client envoie un message (`SendMessage`, ou `SendStreamingMessage` pour un flux SSE), qui crée ou poursuit une **tâche** ; il la suit par `GetTask` ou `SubscribeToTask` et l'annule par `CancelTask`. Une tâche termine en `COMPLETED`, `FAILED`, `CANCELED` ou `REJECTED`, ou s'interrompt en `INPUT_REQUIRED` et `AUTH_REQUIRED` pour attendre l'appelant.

```python
# assistant_stock/serveur.py : l'agent « stock » exposé en A2A, carte générée depuis l'agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from assistant_stock.agent import root_agent

a2a_app = to_a2a(root_agent, port=8001)  # uvicorn assistant_stock.serveur:a2a_app --port 8001
```

```python
# Côté client : l'agent distant devient un sous-agent du coordinateur
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

stock = RemoteA2aAgent(
    name="stock",
    description="Agent de la logistique : stock et délais de réapprovisionnement.",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = Agent(
    name="service_client",
    model="gemini-3.5-flash",  # [*]
    instruction="Réponds aux clients ; pour toute question de stock, délègue à l'agent stock.",
    sub_agents=[stock],
)
```

`to_a2a()` n'ouvre pas de port : `port` (et `host`, `protocol`) doivent correspondre à l'adresse réellement servie, sinon la carte publiée pointe ailleurs. `adk api_server --a2a DOSSIER` sert à la place tous les agents du dossier qui ont un fichier `agent.json` ; `adk deploy cloud_run --a2a` publie le point de terminaison A2A sur Cloud Run. L'extra `google-adk[a2a]` installe le SDK `a2a-sdk`. Côté plateforme, Agent Runtime héberge des agents A2A [!PREVERSION], et un agent A2A s'enregistre dans [Gemini Enterprise app](#gemini-enterprise-app) ou s'importe depuis Agent Registry.

## Sécurité

- **Une identité par agent, des droits minimaux.** L'agent appelle un serveur MCP avec sa propre identité, jamais celle d'un développeur ; ses actions sont alors attribuées et bornées. Sur les serveurs Google, une stratégie de refus IAM sur la permission `mcp.tools.call` avec l'attribut `tool.isReadOnly` interdit tout outil d'écriture sur un projet sensible ; `tool.name` et `resource.service` ciblent un outil ou un produit.
- **Empoisonnement d'outils** (*tool poisoning*). La description d'un outil entre dans le contexte du modèle : un serveur tiers peut y cacher des consignes. La spécification demande de considérer les annotations d'outils comme non fiables si le serveur ne l'est pas. Ne brancher que des serveurs connus, les inscrire dans Agent Registry, figer la liste d'outils avec `tool_filter`.
- **Injection indirecte.** Un résultat d'outil (page web, ticket, document) peut contenir des instructions. Model Armor filtre les requêtes et réponses MCP des serveurs Google qui le prennent en charge, les échanges qui traversent Agent Gateway, et, dans ADK, les entrées et sorties du modèle par `ModelArmorPlugin` (voir [Évaluer et sécuriser](#evaluer-et-securiser)).
- **Confirmation humaine.** Un outil qui modifie ou supprime passe par `require_confirmation=True` (sur `FunctionTool` comme sur `McpToolset`) ; la spécification MCP recommande au client de montrer les arguments avant l'appel.
- **Jetons.** Un serveur MCP ne doit accepter que des jetons émis pour lui (vérification de l'audience) et ne jamais les transmettre tels quels à une API en aval (*token passthrough*, interdit par la spécification). En A2A, l'identité voyage dans les en-têtes HTTP, jamais dans le message ; un besoin d'identifiants en cours de tâche passe par l'état `AUTH_REQUIRED`.
- **Serveurs stdio.** Un serveur local s'exécute avec les droits de l'utilisateur qui lance l'hôte : c'est du code tiers installé sur la machine, à traiter comme tel.

## Alternatives en logiciel libre

MCP et A2A sont eux-mêmes des standards ouverts : la spécification MCP est sous Apache 2.0 et MIT, celle d'A2A sous Apache 2.0. Ce qui se remplace, ce sont les briques gérées autour.

- **SDK MCP officiels** (MIT et Apache 2.0) et **FastMCP** (Apache 2.0) : écrire serveurs et clients MCP ; FastMCP ajoute la composition de serveurs, le mode proxy, l'authentification OAuth et la génération d'un serveur depuis une spécification OpenAPI.
- **SDK A2A** (Apache 2.0) : cartes d'agent, tâches et flux en Python, JavaScript, Java, Go, .NET et Rust, pour exposer un agent de n'importe quel cadre.
- **MCP Toolbox for Databases** (Apache 2.0) : déjà décrit plus haut ; il s'exécute hors de Google Cloud, devant n'importe quelle base PostgreSQL ou MySQL.
- **agentgateway** (Apache 2.0, projet de la Linux Foundation) : proxy MCP et A2A avec fédération de serveurs d'outils, authentification JWT ou OAuth, règles d'accès par outil (moteur CEL), limites de débit et traces OpenTelemetry ; l'équivalent le plus direct d'Agent Gateway.
- **ContextForge** (Apache 2.0) : passerelle et registre qui fédère serveurs MCP, agents A2A et API REST ou gRPC derrière un point de terminaison unique, avec greffons de filtrage ; couvre à la fois Agent Registry et Agent Gateway.
- **MCP Registry** (Apache 2.0 et MIT) : le registre communautaire des serveurs MCP, avec une API standard, déployable en interne pour tenir sa propre liste de serveurs autorisés.
