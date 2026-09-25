---
title: Construire un agent avec ADK
---

Un agent, c'est un **modèle**, des **instructions**, des **outils** et une **boucle**. À chaque tour, le modèle reçoit l'historique de la conversation et la description des outils : il répond, ou demande l'appel d'un outil. Le code exécute l'outil, ajoute le résultat à l'historique et rappelle le modèle, jusqu'à la réponse finale. L'*Agent Development Kit* (ADK) fournit cette boucle, les outils, la mémoire de conversation et l'outillage de test. Il est open source (Apache 2.0), existe en Python, TypeScript, Go, Java et Kotlin, et accepte d'autres modèles que Gemini. La version courante est ADK 2 (`google-adk` 2.9.2 sur PyPI, consulté le 24 septembre 2026) : agents, outils et fonctions y sont les nœuds d'un graphe d'exécution.

![Boucle d'un agent ADK et délégation](../../svg/agent-adk-boucle.svg)

Le *Runner* pilote la boucle : il transmet le message à l'agent, fait appeler le modèle, exécute les outils demandés et enregistre chaque étape comme un **événement** de la session. L'agent peut aussi déléguer : à un sous-agent du même processus, à un *workflow* aux étapes fixes, ou à un agent distant par le protocole A2A (voir [MCP et A2A](#protocoles-mcp-a2a)).

## Les briques d'ADK

| Brique | En Python | Ce qu'elle apporte |
|---|---|---|
| **Agent LLM** | `Agent` (alias de `LlmAgent`) : `model`, `instruction`, `description`, `tools`, `sub_agents` | L'unité de base. `output_key` range la réponse finale dans l'état de la session ; `output_schema` impose une réponse JSON |
| **Outil fonction** | Une fonction Python ; `FunctionTool(f, require_confirmation=True)` pour exiger une validation | Nom, *docstring* et annotations de type deviennent le schéma que lit le modèle ; `LongRunningFunctionTool` met l'agent en pause le temps d'une opération longue |
| **Outils intégrés** | `google_search`, `BuiltInCodeExecutor` (paramètre `code_executor`), outil Agent Search | Recherche web, exécution de code et recherche d'entreprise ([Agent Search](#agent-search)) exécutées côté modèle |
| **API REST** | `OpenAPIToolset(spec_str=..., spec_str_type="yaml")` | Un outil par opération de la spécification OpenAPI 3 |
| **Serveur MCP** | `McpToolset` (extra `google-adk[mcp]`), `ToolboxToolset` pour MCP Toolbox | Les outils d'un serveur MCP, local ou distant (voir [MCP et A2A](#protocoles-mcp-a2a)) |
| **Agent comme outil** | `AgentTool(agent)` | Le parent appelle l'agent comme une fonction et garde la main |
| **Sous-agents** | `sub_agents=[...]`, avec `mode="chat"`, `"task"` ou `"single_turn"` | Le modèle délègue par un appel `transfer_to_agent` ; le mode fixe si le sous-agent parle à l'utilisateur et quand il rend la main |
| **Workflow** | `Workflow(edges=[...])` ; `SequentialAgent`, `ParallelAgent`, `LoopAgent` | Un graphe de nœuds (agents, fonctions, outils) au routage explicite ; les trois agents de flux restent disponibles pour les enchaînements simples |
| **Session et état** | `SessionService` : en mémoire, base SQL (SQLAlchemy), `VertexAiSessionService` | Historique d'une conversation ; l'état se partage par préfixe : aucun (session), `user:`, `app:`, `temp:` (une seule invocation) |
| **Mémoire** | `MemoryService` : en mémoire, `VertexAiMemoryBankService` ; outils `load_memory`, `preload_memory` | Ce que l'agent retient d'une session à l'autre ; Memory Bank en extrait les faits utiles par un modèle |
| **Callbacks** | `before_` et `after_` `agent`, `model`, `tool` | Code exécuté à chaque étape. Renvoyer un objet court-circuite l'étape : garde-fou, cache, réponse simulée |
| **Plugins** | `App(root_agent=..., plugins=[...])` | Un comportement appliqué à tous les agents de l'application, par exemple le filtrage Model Armor |

Deux limites des outils intégrés : l'exécution de code par l'API Gemini ne se combine pas avec d'autres outils dans un même agent, et les outils intégrés ne fonctionnent pas dans un sous-agent (seuls `GoogleSearchTool` et `VertexAiSearchTool` y font exception en Python). Le contournement : isoler l'outil dans un agent dédié et l'appeler par `AgentTool`.

## Un agent minimal

```text
assistant_stock/
├── __init__.py    # from . import agent
├── agent.py
└── .env
```

```python
# assistant_stock/agent.py
from google.adk.agents import Agent


def stock_produit(sku: str) -> dict:
    """Renvoie le stock disponible d'un produit.

    Args:
        sku: référence du produit, par exemple "A-1024".
    """
    stocks = {"A-1024": 12, "B-2048": 0}  # à remplacer par l'appel au système de stock
    if sku not in stocks:
        return {"status": "error", "error_message": f"Référence {sku} inconnue."}
    return {"status": "success", "sku": sku, "quantite": stocks[sku]}


root_agent = Agent(
    name="assistant_stock",
    model="gemini-3.5-flash",  # [*]
    description="Répond aux questions sur le stock des produits.",
    instruction=(
        "Tu réponds aux questions sur le stock. Appelle stock_produit pour chaque "
        "référence citée et n'invente jamais une quantité."
    ),
    tools=[stock_produit],
)
```

```ini
# assistant_stock/.env : Gemini par Agent Platform plutôt que par une clé API
GOOGLE_GENAI_USE_ENTERPRISE=TRUE     # ou GOOGLE_GENAI_USE_VERTEXAI=TRUE, même effet
GOOGLE_CLOUD_PROJECT=PROJECT_ID
GOOGLE_CLOUD_LOCATION=global         # Gemini 3.5 Flash : global, us, eu ou une région
```

```bash
pip install google-adk
adk run assistant_stock              # conversation dans le terminal
adk web --port 8000                  # interface de test, lancée depuis le dossier parent
adk eval assistant_stock assistant_stock/stock.evalset.json
```

`root_agent` est le seul nom imposé. Le dictionnaire renvoyé porte une clé `status` et un message d'erreur lisible : c'est le modèle, pas du code, qui interprète le résultat. `adk web` affiche chaque événement, appel d'outil et changement d'état, mais ne sert qu'au développement. `gemini-3.5-flash` est le Flash GA à date de retrait publiée, au plus tôt le 19 mai 2027, dans la liste des modèles (consultée le 24 septembre 2026) [\*] ; l'alias `gemini-flash-latest` des exemples ADK peut ne pas fonctionner sur un point de terminaison régional (voir [Choisir un modèle](#choisir-un-modele)).

> [!TIP]
> [\*] Gemini 3.8 Flash (`gemini-3.8-flash`), le plus récent des Flash, peut être testé à la place de 3.5 Flash : il est plus capable, mais sa disponibilité est courte (pas de date de retrait garantie, préavis d'au moins 45 jours), il ne se règle pas, et il n'est servi que sur `global`, `us` et `eu` (voir [Choisir un modèle](#choisir-un-modele)).

**Évaluer.** Un fichier `*.evalset.json` décrit des conversations de référence : requêtes, outils attendus, réponse attendue. `adk eval` (ou `pytest` avec `AgentEvaluator`) les rejoue et calcule des critères : `tool_trajectory_avg_score` compare la suite d'appels d'outils (seuil par défaut 1,0, soit une correspondance exacte), `response_match_score` la réponse par similarité ROUGE-1 (seuil par défaut 0,8), `final_response_match_v2` la fait juger par un modèle. Les deux premiers sont rapides et stables, faits pour la CI ; l'évaluation à plus grande échelle est traitée dans [Évaluer et sécuriser](#evaluer-et-securiser).

## Déléguer : sous-agent, agent comme outil ou A2A

| Mécanisme | Qui garde la main | Contexte partagé | Quand l'utiliser |
|---|---|---|---|
| **`AgentTool`** | Le parent : il reçoit le résultat et continue | Seulement la requête passée à l'outil | Tâche ponctuelle et bornée : recherche, extraction, calcul dans un agent dédié |
| **Sous-agent** (`sub_agents`) | Le sous-agent, jusqu'au retour : manuel en `chat`, automatique en `task` et `single_turn` | La session entière, dont l'état | Domaines distincts d'un même produit (facturation, livraison), avec une `description` précise pour chacun |
| **`Workflow`** ou agents de flux | Le graphe : l'ordre est codé | État de session, ou sortie d'un nœud passée au suivant | Étapes dont l'ordre ne doit pas dépendre du modèle ; mélange d'appels au modèle et de code déterministe |
| **Agent distant** (`RemoteA2aAgent`) | L'agent distant, pour la tâche envoyée | Aucun : seulement les messages et les artefacts | Agent d'une autre équipe, d'un autre langage ou d'un autre cadre, déployé à part |

Le coordinateur choisit un sous-agent sur sa `description` : deux descriptions voisines donnent un routage aléatoire. Les sous-agents en `single_turn` peuvent tourner en parallèle, sans interaction avec l'utilisateur.

## Agent, workflow ou orchestrateur

| Situation | Choix | Pourquoi |
|---|---|---|
| Suite fixe d'appels d'API, sans décision en langage naturel | [Workflows](#workflows) | Déterministe, relances et attentes gérées, facturé au pas ; aucun modèle à évaluer |
| Pipeline de données planifié, dépendances, reprise sur une date passée | [Managed Service for Apache Airflow](#managed-service-for-apache-airflow) | Planification et *backfill* (voir [Orchestration](#orchestration)) |
| Étapes fixes dont une demande du langage : résumer, classer, extraire | Workflows ou Airflow qui appellent Gemini, ou `Workflow` ADK | Le modèle est une étape, pas le pilote : coût et durée prévisibles |
| Parcours imposé avec quelques branchements décidés par le modèle | `Workflow` ADK avec nœuds de routage | Le code tient l'ordre, le modèle tranche aux embranchements |
| Demande ouverte, outils choisis selon la question, dialogue | `Agent` avec outils | C'est le cas d'usage de la boucle |
| Plusieurs domaines, plusieurs équipes | Coordinateur et sous-agents, puis A2A entre services | Un agent par domaine garde des instructions courtes et testables |

**Autres cadres.** Agent Runtime, le service de déploiement d'[Agent Platform](#gemini-enterprise-agent-platform), intègre ADK complètement ; LangChain, LangGraph, AG2 et LlamaIndex [!PREVERSION] y ont des modèles prêts à l'emploi dans le SDK ; CrewAI et tout autre cadre passent par un conteneur qui respecte le contrat d'exécution (HTTP sur le port 8080). Sans code, Agent Studio sur Agent Platform et [Customer Experience Agent Studio](#customer-experience-agent-studio), construit sur ADK, couvrent le même terrain. Le déploiement est traité dans [Déployer un agent](#deployer-un-agent).

## Pièges

- **Des outils mal décrits.** La *docstring* est tout ce que le modèle sait de l'outil. Deux outils aux noms ou descriptions proches, un paramètre au sens ambigu, et le modèle se trompe d'outil ou invente l'argument. Une erreur doit revenir en clair dans le résultat, pas en exception muette.
- **Trop d'outils.** Chaque description occupe le contexte à chaque appel. Au-delà d'une dizaine d'outils, les découper entre sous-agents ou filtrer ceux d'un serveur MCP (`tool_filter`).
- **Des boucles sans fin.** `RunConfig(max_llm_calls=...)` borne les appels au modèle par exécution (500 par défaut, ou la variable `ADK_MAX_LLM_CALLS`) ; `LoopAgent` n'a pas de limite tant que `max_iterations` n'est pas fixé.
- **Le coût.** Chaque tour d'outil est un nouvel appel au modèle avec tout l'historique : une question qui déclenche cinq outils coûte au moins six appels. `include_contents="none"` sur un sous-agent lui évite de recevoir l'historique ; le cache de contexte et un modèle plus léger pour les sous-agents simples réduisent la facture.
- **Le non-déterminisme.** Deux exécutions de la même question peuvent emprunter des chemins différents. Tester la trajectoire d'outils en CI, pas seulement le texte final ; confier au code ce qui doit toujours se passer dans le même ordre.
- **Des actions irréversibles.** Un outil qui écrit, paie ou supprime demande `require_confirmation=True`, ou une validation humaine hors de l'agent.
- **`output_schema` avec des outils.** Les deux ensemble ne sont pris en charge nativement que par certains modèles, dont Gemini 3 ; sinon, confier la mise en forme à un sous-agent sans outil.
- **Attraper toutes les exceptions dans un outil.** En ADK 2, un `except Exception:` large masque l'erreur au framework et désactive ses relances automatiques (`RetryConfig`).

## Alternatives en logiciel libre

- **ADK** lui-même (Apache 2.0) : le cadre tourne hors de Google Cloud et avec d'autres modèles ; seuls les services gérés de session, de mémoire et d'évaluation sont à remplacer, par exemple une base SQL pour les sessions.
- **LangGraph** (MIT) : l'agent comme graphe d'états explicite, avec points de reprise persistants et interruption pour une validation humaine ; le plus proche du `Workflow` ADK. **LangChain** (MIT) lui fournit les intégrations de modèles et d'outils.
- **CrewAI** (MIT) : équipes d'agents à rôles et tâches déclarés, plus directives que la délégation par `description` d'ADK.
- **AG2** (Apache 2.0) : systèmes multi-agents organisés en conversations entre agents, humain compris, plutôt qu'en graphe.
- **Pydantic AI** (MIT) : agents typés, sorties validées par Pydantic et dépendances injectées dans les outils ; l'équivalent d'`output_schema` et des outils fonctions.
- **smolagents** (Apache 2.0) : agents minimalistes dont les actions sont écrites en code Python, à exécuter dans un bac à sable.
- **Microsoft Agent Framework** (MIT) : agents et workflows en graphe, en Python et en .NET, avec MCP et A2A.
