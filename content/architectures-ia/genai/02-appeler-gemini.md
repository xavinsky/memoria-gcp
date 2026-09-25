---
title: Appeler Gemini depuis du code
---

En Python, Gemini s'appelle avec le SDK **`google-genai`** (`pip install google-genai`), le même pour la Gemini Developer API et pour [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform). Les modules `vertexai.generative_models` [!DECONSEILLE] de `google-cloud-aiplatform` sont dépréciés : tout code neuf part de `google-genai`. Les exemples ci-dessous suivent la version 2.25 du SDK (septembre 2026) ; le choix du modèle est traité dans [Choisir un modèle génératif](#choisir-un-modele).

## Le client

```python
from google import genai
from google.genai import types

client = genai.Client(enterprise=True, project="PROJECT_ID", location="global")
```

- `enterprise=True` envoie les requêtes vers Agent Platform (`aiplatform.googleapis.com`) au lieu de la Developer API. Le SDK accepte aussi `vertexai=True`, la forme qu'emploie une bonne partie de la documentation.
- Sans argument, `genai.Client()` lit les variables `GOOGLE_GENAI_USE_ENTERPRISE=true` (ou `GOOGLE_GENAI_USE_VERTEXAI=true`), `GOOGLE_CLOUD_PROJECT` et `GOOGLE_CLOUD_LOCATION`. C'est la forme à préférer dans un conteneur : la configuration vient de l'environnement.
- `location` vaut `global`, une multirégion (`us`, `eu`) ou une région (`europe-west3`). Le SDK choisit l'hôte correspondant ; ce choix fixe la résidence du traitement.
- **Authentification** : le client utilise les *Application Default Credentials* (ADC) du poste ou du compte de service attaché (voir [Authentifier un appel à une API](#authentifier-un-appel)). Le principal a besoin de `roles/aiplatform.user`. Une clé API est acceptée pour un essai, pas pour la production.
- Le SDK appelle l'API `v1beta1` par défaut, pour exposer les fonctions en *preview* ; `http_options=types.HttpOptions(api_version="v1")` le cantonne à l'API stable.

## Fonctionnalités et paramètres

| Besoin | Paramètre ou méthode du SDK | Remarque |
|---|---|---|
| Génération simple | `client.models.generate_content(model=, contents=, config=)` | `response.text`, `response.usage_metadata` |
| Réponse en flux | `client.models.generate_content_stream(...)` | Réduit le délai avant le premier jeton, pas le coût |
| Instructions système | `GenerateContentConfig(system_instruction=...)` | Rôle, ton, règles ; hors du fil de conversation |
| Conversation | `client.chats.create(model=...)`, puis `chat.send_message(...)` | L'historique est renvoyé à chaque tour, donc refacturé |
| Réflexion | `thinking_config=types.ThinkingConfig(thinking_level="LOW")` | Gemini 3 : `MINIMAL`, `LOW`, `MEDIUM`, `HIGH` selon le modèle ; jetons de réflexion facturés en sortie |
| Sortie structurée | `response_mime_type="application/json"` avec `response_schema=` (classe Pydantic) ou `response_json_schema=` (JSON Schema) | `response.parsed` rend l'objet validé ; ne pas répéter le schéma dans le prompt |
| Appel de fonctions | `tools=[types.Tool(function_declarations=[...])]`, `tool_config=` | `response.function_calls` ; exécution par l'application |
| Fichier Cloud Storage | `types.Part.from_uri(file_uri="gs://...", mime_type=...)` | Jusqu'à 30 Mo par image et 50 Mo par PDF depuis Cloud Storage, 7 Mo en ligne |
| Ancrage Google Search | `tools=[types.Tool(google_search=types.GoogleSearch())]` | Sources dans `candidates[0].grounding_metadata` |
| Cache de contexte | `client.caches.create(...)`, puis `cached_content=cache.name` | Implicite et automatique ; explicite pour garantir la remise |
| Inférence par lots | `client.batches.create(model=, src="bq://..." ou "gs://...")` | −50 %, résultat sous 24 h en général |
| Compter les jetons | `client.models.count_tokens(...)`, `compute_tokens(...)` | Avant l'envoi, pour tenir une limite ou estimer un coût |
| Filtres de contenu | `safety_settings=[types.SafetySetting(...)]` | Voir [Évaluer et sécuriser](#evaluer-et-securiser) |
| Model Armor | `model_armor_config=types.ModelArmorConfig(...)` | Exclusif avec `safety_settings` |
| Étiquettes de coût | `labels={"app": "support"}` | Ventilation dans l'export de facturation |
| Nouvelles tentatives | `HttpOptions(retry_options=types.HttpRetryOptions(...), timeout=...)` | Sur le client ou par requête |
| Embeddings | `client.models.embed_content(model="gemini-embedding-2", contents=...)` | `EmbedContentConfig(output_dimensionality=768)` ; la tâche se donne en préfixe du texte (`task: search result \| query: ...`), pas par `task_type` |

## Exemples

Génération avec instructions système, puis en flux :

```python
config = types.GenerateContentConfig(
    system_instruction="Tu es l'assistant du support. Réponds en français, en trois phrases au plus.",
    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    max_output_tokens=1024,
    labels={"app": "support"},
)
response = client.models.generate_content(  # [*]
    model="gemini-3.5-flash", contents="Comment réinitialiser mon mot de passe ?", config=config,
)
print(response.text, response.usage_metadata.total_token_count)

for chunk in client.models.generate_content_stream(
    model="gemini-3.5-flash", contents="Rédige la procédure détaillée.", config=config,
):
    print(chunk.text or "", end="")
```

> [!TIP]
> [\*] Gemini 3.8 Flash (`gemini-3.8-flash`), le plus récent des Flash, peut être testé à la place de 3.5 Flash : il est plus capable, mais sa disponibilité est courte (pas de date de retrait garantie, préavis d'au moins 45 jours), il ne se règle pas, et il n'est servi que sur `global`, `us` et `eu` (voir [Choisir un modèle](#choisir-un-modele)).

Extraction structurée d'un PDF stocké dans [Cloud Storage](#cloud-storage) — l'agent de service de la plateforme doit pouvoir lire l'objet :

```python
from pydantic import BaseModel

class Facture(BaseModel):
    fournisseur: str
    montant_ttc: float
    echeance: str

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=[
        types.Part.from_uri(file_uri="gs://BUCKET/factures/f-001.pdf", mime_type="application/pdf"),
        "Extrais le fournisseur, le montant TTC et la date d'échéance.",
    ],
    config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Facture),
)
facture: Facture = response.parsed
```

Appel de fonction déclarée à la main, en deux allers-retours :

```python
stock = types.FunctionDeclaration(
    name="stock_article",
    description="Renvoie le stock disponible d'un article.",
    parameters_json_schema={"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]},
)
config = types.GenerateContentConfig(tools=[types.Tool(function_declarations=[stock])])
contents = [types.Content(role="user", parts=[types.Part.from_text(text="Reste-t-il du A-42 ?")])]

response = client.models.generate_content(model="gemini-3.5-flash", contents=contents, config=config)  # [*]
contents.append(response.candidates[0].content)          # tour du modèle complet, signatures comprises
reponses = [
    types.Part.from_function_response(name=appel.name, response={"stock": lire_stock(**appel.args)})
    for appel in response.function_calls or []
]
contents.append(types.Content(role="user", parts=reponses))
final = client.models.generate_content(model="gemini-3.5-flash", contents=contents, config=config)
```

Passer une fonction Python dans `tools=` déclenche l'appel automatique (*automatic function calling*) : le SDK exécute la fonction et relance le modèle. Pratique en conversation, mais sans contrôle sur ce qui est exécuté ; pour un agent complet, ADK prend le relais (voir [Construire un agent](#construire-un-agent)).

Cache explicite d'un gros document réutilisé par de nombreuses requêtes :

```python
cache = client.caches.create(
    model="gemini-3.5-flash",
    config=types.CreateCachedContentConfig(
        contents=[types.Content(role="user", parts=[
            types.Part.from_uri(file_uri="gs://BUCKET/contrats/cadre.pdf", mime_type="application/pdf"),
        ])],
        system_instruction="Tu réponds uniquement à partir du contrat fourni.",
        ttl="3600s",
    ),
)
response = client.models.generate_content(
    model="gemini-3.5-flash", contents="Quel est le préavis de résiliation ?",
    config=types.GenerateContentConfig(cached_content=cache.name),
)
```

Le cache implicite est actif par défaut et s'applique dès 4 096 jetons de préfixe commun sur Gemini 3 (6 144 pour 3.7 et 3.8 Flash) : placer le contenu stable en tête du prompt suffit souvent. Le cache explicite garantit la remise de 90 %, mais son stockage est facturé à la durée ; le supprimer (`client.caches.delete`) dès qu'il ne sert plus. En amont du modèle, un cache des réponses de l'application, par clé exacte ou sémantique (index vectoriel dans [Memorystore](#memorystore)), évite tout appel pour une question déjà traitée ([Well-Architected Framework, efficacité énergétique de l'IA](https://docs.cloud.google.com/architecture/framework/sustainability/ai-ml-energy-efficiency)).

Inférence par lots, depuis une table [BigQuery](#bigquery) :

```python
job = client.batches.create(
    model="gemini-3.5-flash-lite",
    src="bq://PROJECT_ID.DATASET.prompts",
    config=types.CreateBatchJobConfig(dest="bq://PROJECT_ID.DATASET.reponses"),
)
print(client.batches.get(name=job.name).state)
```

Un lot contient jusqu'à 200 000 requêtes (fichier JSONL de 1 Go au plus depuis Cloud Storage). Le service relance lui-même les requêtes en échec ; les remises du lot et du cache ne se cumulent pas, celle du cache l'emporte.

## Débit, quotas et erreurs 429

| Option | Principe | Pour quoi |
|---|---|---|
| **Standard PayGo** (défaut) | Capacité partagée ; débit de référence en jetons par minute fixé par palier, selon les dépenses de l'organisation sur 30 jours ; dépassements servis au mieux | Trafic courant et variable |
| **Priority PayGo** | Tarif majoré, traitement prioritaire ; en-tête `X-Vertex-AI-LLM-Shared-Request-Type: priority` ; `global`, `us`, `eu` | Application critique sans engagement |
| [!PREVERSION] **Flex PayGo** | −50 %, latence et délestage plus élevés ; en-tête `...: flex` ; `global` seulement, délai jusqu'à 30 min | Traitements synchrones non urgents |
| **Provisioned Throughput** | Débit réservé en GSU, engagement d'une semaine à un an ; débordement facturé en PayGo | Charge de base constante, SLA |
| **Inférence par lots** | Pool partagé, pas de quota prédéfini ; mise en file possible | Gros volumes asynchrones |

Le palier Standard PayGo s'applique à chaque modèle séparément et se mesure sur l'endpoint `global`, qui puise dans la capacité de plusieurs régions. `usage_metadata.traffic_type` indique si une réponse a été servie en PayGo (`ON_DEMAND`, `ON_DEMAND_PRIORITY`, `ON_DEMAND_FLEX`) ou sur le débit provisionné. Le [tableau de bord d'observabilité des modèles](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-observability) de la console suit, par modèle et par emplacement, les requêtes par seconde, le débit de jetons, la latence du premier jeton et les taux d'erreur des appels à l'API ; ces métriques Cloud Monitoring servent aussi aux alertes. Les modèles auto-déployés n'y figurent pas.

Une **erreur 429** (`RESOURCE_EXHAUSTED`) signale une capacité partagée saturée ou un débit provisionné dépassé. Dans l'ordre : passer par `global` si la résidence le permet, lisser le trafic à la seconde (les pics brefs sont limités même sous la moyenne), monter progressivement en charge, relancer avec un délai exponentiel, puis réserver du débit.

```python
client = genai.Client(
    enterprise=True, project="PROJECT_ID", location="global",
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=1.0, max_delay=60.0),
        timeout=120_000,  # millisecondes
    ),
)
```

Sans `retry_options`, le client Python 2.25 ne relance rien : c'est ce que montre son code source (`retry_args(None)` arrête à la première tentative), même si la page *Retry strategy* annonce des relances par défaut. Le déclarer explicitement lève l'ambiguïté. Les codes relancés par défaut sont 408, 429 et 5xx ; 400, 401 et 403 ne se relancent pas. Les erreurs remontent en `errors.ClientError` (4xx) et `errors.ServerError` (5xx), avec `e.code` et `e.message`.

## Pièges

- **Signatures de réflexion perdues.** Avec Gemini 3, le tour du modèle contient des signatures de réflexion à renvoyer telles quelles avec le résultat des fonctions. Reconstruire ce tour à la main, ou n'en garder que la partie `function_call`, produit une erreur 400. Toujours réinjecter `response.candidates[0].content` entier.
- **`response.text` vide.** Une réponse bloquée par un filtre, arrêtée par `MAX_TOKENS` ou réduite à des appels de fonction n'a pas de texte. Lire `candidates[0].finish_reason` et `prompt_feedback` avant de conclure à un bug.
- **Réflexion qui mange la sortie.** Les jetons de réflexion comptent dans `max_output_tokens` et sont facturés : une limite trop basse coupe la réponse avant qu'elle commence. Surveiller `thoughts_token_count`.
- **Relances en rafale.** Une boucle de relance sans délai ni plafond aggrave la saturation. En temps réel, peu de tentatives et un échec rapide ; en Flex, allonger le délai d'attente plutôt que relancer ; pour un lot, ne rien relancer soi-même.
- **Aucun repli.** Quand les erreurs persistent malgré les relances, un disjoncteur (*circuit breaker*) cesse d'appeler le modèle saturé et bascule sur un repli prévu : modèle plus léger, autre emplacement compatible avec la résidence, réponse en cache ou message dégradé ([Well-Architected Framework, fiabilité](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/reliability)). Le repli se teste et s'évalue comme le chemin principal.
- **Client recréé à chaque requête.** Créer le client une fois par processus et le fermer (`client.close()`, ou bloc `with`) : chaque instance ouvre son propre pool de connexions.
- **Recherche et fonctions dans la même requête.** L'ancrage Google Search ne se combine pas avec l'appel de fonctions ni avec l'outil de récupération de RAG Engine dans un même `generateContent` : plusieurs outils ne sont acceptés que s'ils sont tous des outils de recherche. Séparer les appels, ou confier l'orchestration à un agent.
- **Endpoint et modèle incompatibles.** Tous les modèles ne sont pas sur tous les endpoints : Gemini 3.8 Flash n'existe qu'en `global`, `us` et `eu`, pas en région. Une erreur 404 sur un modèle valide vient souvent de là.
- **Fichier Cloud Storage illisible.** La lecture d'un `gs://` se fait avec l'identité de la plateforme, pas celle de l'appelant : accorder `roles/storage.objectViewer` sur le bucket à l'agent de service `service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com`, et, si un périmètre [VPC Service Controls](#vpc-service-controls) protège le projet, y inclure aussi le projet du bucket.

## Alternatives en logiciel libre

L'équivalent libre de cet appel est un modèle aux poids libres (voir [Choisir un modèle](#choisir-un-modele)) servi derrière une API compatible OpenAI.

- **vLLM** (Apache 2.0) : serveur compatible OpenAI avec cache automatique des préfixes (l'équivalent du cache implicite), sortie structurée par schéma JSON, appel de fonctions et inférence par lots hors ligne ; la capacité et les quotas sont ceux de ses propres GPU.
- **Ollama** (MIT) et **llama.cpp** (MIT) : la même API compatible OpenAI sur un poste ou un petit serveur, avec sortie contrainte par schéma JSON.
- **LiteLLM** (MIT, hors répertoire `enterprise`) : une interface unique vers une centaine de fournisseurs, Gemini et serveurs locaux compris ; en proxy, il ajoute clés virtuelles, budgets, limites de débit, relances et bascule d'un modèle à l'autre.
- **Outlines** (Apache 2.0) : génération contrainte au niveau des jetons par schéma JSON, expression régulière ou grammaire ; la sortie respecte le format par construction.
- **Instructor** (MIT) : sortie structurée validée par Pydantic, avec nouvelle tentative quand la validation échoue, sur la plupart des API de modèles ; l'équivalent de `response_schema` et `response.parsed`.
