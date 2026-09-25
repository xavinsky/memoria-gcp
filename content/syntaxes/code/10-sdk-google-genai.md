---
title: "SDK google-genai : appels à Gemini"
subgroup: IA
type: syntax
---

Appels du SDK `google-genai` (`pip install google-genai`, version 2.25) vers Gemini sur [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform). Imports supposés : `from google import genai`, `from google.genai import types`. Identifiants de modèle : voir [Choisir un modèle génératif](#choisir-un-modele).

### Client

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Client Agent Platform explicite | `client = genai.Client(enterprise=True, project="PROJECT_ID", location="global")` | Requêtes vers `aiplatform.googleapis.com`, authentification par ADC ; `vertexai=True` est accepté aussi |
| Client configuré par l'environnement | `GOOGLE_GENAI_USE_ENTERPRISE=true`, `GOOGLE_CLOUD_PROJECT=PROJECT_ID`, `GOOGLE_CLOUD_LOCATION=global`, puis `genai.Client()` | Forme à préférer dans un conteneur |
| Choisir la résidence | `location="eu"` (ou `us`, `europe-west3`) | Traitement dans cette juridiction ; `global` n'en garantit aucune |
| Rester sur l'API stable | `http_options=types.HttpOptions(api_version="v1")` | Le SDK appelle `v1beta1` par défaut |
| Relancer sur 408, 429 et 5xx | `http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=5, initial_delay=1.0, max_delay=60.0), timeout=120_000)` | Délai exponentiel ; `timeout` en **millisecondes** ; sans `retry_options`, aucune relance |
| Fermer le client | `client.close()`, ou `with genai.Client(...) as client:` | Libère le pool de connexions ; créer un seul client par processus |
| Client asynchrone | `client.aio.models.generate_content(...)` avec `await` ; `await client.aio.aclose()` | Mêmes méthodes sous `client.aio` |
| Attraper les erreurs | `except genai.errors.ClientError as e:` (4xx), `genai.errors.ServerError` (5xx) | `e.code`, `e.message` ; 429 = capacité saturée |

### Générer

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Génération simple | `r = client.models.generate_content(model="gemini-3.5-flash", contents="...")` [*] | `r.text` ; vide si la réponse est bloquée, coupée ou réduite à des appels de fonction |
| Consommation de jetons | `r.usage_metadata.prompt_token_count`, `.candidates_token_count`, `.thoughts_token_count`, `.total_token_count` | Base de la facture ; `.traffic_type` dit PayGo ou débit provisionné |
| Motif d'arrêt | `r.candidates[0].finish_reason`, `r.prompt_feedback` | `STOP`, `MAX_TOKENS`, `SAFETY`… à lire avant de conclure à un bug |
| Instructions système | `config=types.GenerateContentConfig(system_instruction="...")` | Rôle et règles, hors du fil de conversation |
| Paramètres d'échantillonnage | `GenerateContentConfig(temperature=0.2, top_p=0.95, max_output_tokens=2048, stop_sequences=["FIN"], seed=42)` | `max_output_tokens` inclut les jetons de réflexion |
| Niveau de réflexion | `GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="LOW"))` | `MINIMAL`, `LOW`, `MEDIUM`, `HIGH` selon le modèle ; 3.8 Flash refuse `MINIMAL` |
| Voir le résumé de réflexion | `ThinkingConfig(include_thoughts=True)` | Parties marquées `part.thought == True` dans la réponse |
| Sortie JSON validée | `GenerateContentConfig(response_mime_type="application/json", response_schema=Facture)` (classe Pydantic) | `r.parsed` est une instance de `Facture` ; pas de `parsed` en flux |
| Schéma JSON brut | `response_json_schema={"type": "object", ...}` | Même contrainte, sans Pydantic |
| Filtres de contenu | `safety_settings=[types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH")]` | Seuils `BLOCK_LOW_AND_ABOVE`, `BLOCK_MEDIUM_AND_ABOVE`, `BLOCK_ONLY_HIGH`, `BLOCK_NONE`, `OFF` |
| Étiqueter pour la facturation | `GenerateContentConfig(labels={"app": "support", "env": "prod"})` | Ventilation dans l'export de facturation |
| Réponse en flux | `for chunk in client.models.generate_content_stream(model=..., contents=..., config=...): print(chunk.text or "", end="")` | Premier jeton plus tôt ; même coût |

> [!TIP]
> [*] Gemini 3.8 Flash, sorti récemment, peut être testé à la place de 3.5 Flash : il est plus capable, mais sa disponibilité est courte (pas de date de retrait garantie, préavis d'au moins 45 jours), et il n'est servi que sur global, us et eu.

```python
from pydantic import BaseModel

class Facture(BaseModel):
    fournisseur: str
    montant_ttc: float

r = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=[
        types.Part.from_uri(file_uri="gs://BUCKET/factures/f-001.pdf", mime_type="application/pdf"),
        "Extrais le fournisseur et le montant TTC.",
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=Facture,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        labels={"app": "compta"},
    ),
)
facture: Facture = r.parsed
```

### Multimodal et conversation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Fichier dans Cloud Storage | `types.Part.from_uri(file_uri="gs://BUCKET/doc.pdf", mime_type="application/pdf")` | Lu avec l'identité de l'agent de service `service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com` |
| Octets en ligne | `types.Part.from_bytes(data=open("photo.jpg", "rb").read(), mime_type="image/jpeg")` | 7 Mo au plus en ligne ; au-delà, passer par Cloud Storage |
| Texte explicite | `types.Part.from_text(text="...")` | Pour construire un `types.Content(role="user", parts=[...])` |
| API Files | `client.files.upload(file="doc.pdf")` | **Gemini Developer API seulement** : erreur avec `enterprise=True`, utiliser Cloud Storage |
| Ouvrir une conversation | `chat = client.chats.create(model="gemini-3.5-flash", config=config)` | Historique tenu par le SDK, renvoyé (donc refacturé) à chaque tour |
| Envoyer un message | `chat.send_message("...")`, `chat.send_message_stream("...")` | Même réponse que `generate_content` |
| Relire l'historique | `chat.get_history()` | Liste de `Content` ; `history=` de `chats.create` pour reprendre une conversation |

### Outils et ancrage

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Appel de fonction automatique | `GenerateContentConfig(tools=[stock_article])` (fonction Python typée, avec *docstring*) | Le SDK exécute la fonction et relance le modèle, jusqu'à 10 appels par défaut |
| Plafonner ou couper l'automatique | `automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=3)` (ou `disable=True`) | Avec `disable=True`, les appels reviennent dans `r.function_calls` |
| Déclarer une fonction à la main | `types.FunctionDeclaration(name=..., description=..., parameters_json_schema={...})` dans `types.Tool(function_declarations=[...])` | `r.function_calls` : `.name`, `.args` ; exécution par l'application |
| Renvoyer le résultat d'une fonction | `types.Part.from_function_response(name=appel.name, response={"stock": 12})` | Réinjecter aussi `r.candidates[0].content` entier, signatures de réflexion comprises |
| Forcer ou interdire l'appel | `tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="ANY", allowed_function_names=["stock_article"]))` | `AUTO` (défaut), `ANY`, `NONE`, `VALIDATED` |
| Ancrage sur Google Search | `tools=[types.Tool(google_search=types.GoogleSearch())]` | Sources dans `r.candidates[0].grounding_metadata` ; ne se combine pas avec des fonctions |
| Lire une page web citée | `tools=[types.Tool(url_context=types.UrlContext())]` | Le modèle récupère les URL du prompt |
| Exécution de code | `tools=[types.Tool(code_execution=types.ToolCodeExecution())]` | Le modèle écrit et exécute du Python dans un bac à sable |

```python
def stock_article(sku: str) -> dict:
    """Renvoie le stock disponible d'un article à partir de son SKU."""
    return {"sku": sku, "stock": 12}

chat = client.chats.create(
    model="gemini-3.5-flash",
    config=types.GenerateContentConfig(
        tools=[stock_article],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=3),
    ),
)
print(chat.send_message("Reste-t-il du A-42 ?").text)
```

### Jetons, embeddings, cache, lots

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Compter les jetons avant l'envoi | `client.models.count_tokens(model="gemini-3.5-flash", contents=...)` | `.total_tokens` ; `compute_tokens` détaille les jetons |
| Embedding d'un texte | `client.models.embed_content(model="gemini-embedding-2", contents="...", config=types.EmbedContentConfig(output_dimensionality=768))` | `r.embeddings[0].values` ; 3 072 dimensions par défaut |
| Préciser la tâche avec `gemini-embedding-2` | `contents="task: search result \| query: QUESTION"` ; documents : `"title: TITRE \| text: CONTENU"` | La tâche se donne en préfixe du texte ; `task_type=` sert à `gemini-embedding-001` |
| Créer un cache explicite | `cache = client.caches.create(model="gemini-3.5-flash", config=types.CreateCachedContentConfig(contents=[...], system_instruction="...", ttl="3600s"))` | Jetons en cache facturés −90 % ; stockage facturé à la durée |
| Utiliser le cache | `GenerateContentConfig(cached_content=cache.name)` | `usage_metadata.cached_content_token_count` le confirme |
| Prolonger, supprimer le cache | `client.caches.update(name=cache.name, config=types.UpdateCachedContentConfig(ttl="7200s"))`, `client.caches.delete(name=cache.name)` | Supprimer dès qu'il ne sert plus |
| Lancer un lot | `job = client.batches.create(model="gemini-3.5-flash-lite", src="bq://PROJECT_ID.DATASET.prompts", config=types.CreateBatchJobConfig(dest="bq://PROJECT_ID.DATASET.reponses"))` | −50 % ; `src` et `dest` acceptent aussi `gs://BUCKET/...jsonl` |
| Suivre un lot | `client.batches.get(name=job.name).state` | `JOB_STATE_RUNNING`, `JOB_STATE_SUCCEEDED`, `JOB_STATE_FAILED`… ; `client.batches.cancel(name=...)` |

```python
import asyncio

async def resumer(textes: list[str]) -> list[str]:
    async with genai.Client(enterprise=True, project="PROJECT_ID", location="global").aio as aclient:
        reponses = await asyncio.gather(*[
            aclient.models.generate_content(model="gemini-3.5-flash-lite", contents=f"Résume : {t}")
            for t in textes
        ])
    return [r.text for r in reponses]
```

> [!WARNING]
> `asyncio.gather` sur des milliers de requêtes déclenche des erreurs 429 : borner la concurrence (`asyncio.Semaphore`), ou passer en lot si la réponse n'est pas attendue en temps réel.

Contexte : [Appeler Gemini depuis du code](#appeler-gemini), [Choisir un modèle génératif](#choisir-un-modele), [Authentifier un appel à une API](#authentifier-un-appel).
