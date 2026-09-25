---
title: Choisir un modèle génératif
---

Le choix se fait en deux temps. D'abord **quel modèle** : un Gemini géré par Google, un modèle partenaire ou ouvert appelé en *modèle en tant que service* (MaaS), ou un modèle ouvert déployé sur ses propres machines. Ensuite **comment l'adapter** : on épuise le prompting, puis on apporte des connaissances par le RAG, et on ne règle les poids qu'en dernier recours. Tout se trouve dans [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) (ex-Vertex AI) et son catalogue [Model Garden](#model-garden).

## La famille Gemini

État du catalogue en septembre 2026 (pages *Google models* et *Model versions and lifecycle* de la documentation). Tous ces modèles acceptent en entrée du texte, des images, de l'audio, de la vidéo et des PDF, produisent du texte, et ont une fenêtre de contexte de 1 048 576 jetons pour 65 536 jetons de sortie.

| Modèle | ID | Statut | Emplacements | Réglage | Profil |
|---|---|---|---|---|---|
| [!DECONSEILLE] Gemini 3.8 Flash | `gemini-3.8-flash` | GA, disponibilité courte : pas de date de retrait garantie, préavis d'au moins 45 jours | `global`, `us`, `eu` | Non | Le plus capable des Flash (agents au long cours, code, raisonnement multi-étapes) : à tester face à 3.5 Flash, mais pas une base durable |
| [!DECONSEILLE] Gemini 3.7 Flash, 3.6 Flash | `gemini-3.7-flash`, `gemini-3.6-flash` | GA, disponibilité courte, remplacement désigné : 3.8 Flash | `global`, `us`, `eu` | Non | Versions précédentes de la même lignée, à disponibilité courte : pas une base durable ; 3.5 Flash pour la production |
| Gemini 3.5 Flash | `gemini-3.5-flash` | GA, retrait au plus tôt le 19 mai 2027 | `global`, `us`, `eu`, quelques régions (`europe-west2`, `europe-west3`, Asie) | Supervisé ; par renforcement [!PREVERSION] | **Modèle par défaut** : production à horizon garanti, réglable |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | GA, retrait au plus tôt le 21 juillet 2027 | `global`, `us`, `eu` | Non | Gros volumes, faible latence, coût minimal |
| Gemini 3.1 Flash-Lite | `gemini-3.1-flash-lite` | GA, retrait au plus tôt le 7 mai 2027 | `global`, `us`, `eu` | Supervisé ; par renforcement [!PREVERSION] | Gros volumes quand il faut régler le modèle |
| [!PREVERSION] Gemini 3.1 Pro | `gemini-3.1-pro-preview` | Pré-GA, sans date de retrait | `global` | Non | Raisonnement le plus poussé, gros dépôts de code |
| [!DECONSEILLE] Gemini 2.5 Pro, Flash, Flash-Lite | `gemini-2.5-pro`… | GA, **retrait le 20 octobre 2026** | Nombreuses régions | Supervisé ; préférences (Flash, Flash-Lite) | Existant à migrer vers 3.5 Flash ou 3.1 Flash-Lite |

Deux régimes de disponibilité coexistent. Les modèles « au moins 12 mois » ont une date de retrait publiée, qui peut reculer mais jamais avancer. Les modèles « à disponibilité courte » (3.6, 3.7, 3.8 Flash) restent actifs jusqu'à ce qu'une date de retrait soit annoncée, avec au moins 45 jours de préavis. Le modèle le plus récent n'est donc pas toujours le meilleur choix pour une application qu'on ne veut pas retoucher avant un an : 3.5 Flash est le modèle par défaut, et 3.8 Flash, plus capable, se teste à sa place sur un jeu d'évaluation avant d'accepter sa durée de vie incertaine.

**Modèles spécialisés** de la même plateforme :

- **Image** : `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image` et `gemini-3-pro-image` génèrent et retouchent des images par la même API `generateContent`.
- **Embeddings** : `gemini-embedding-2` (GA) projette texte, images, audio, vidéo et documents dans un même espace vectoriel, en 3 072 dimensions réductibles par `output_dimensionality`, pour 8 192 jetons d'entrée ; `gemini-embedding-001` reste le modèle texte seul. C'est la brique de la recherche sémantique du [RAG](#rag).
- **Temps réel** : la Live API ouvre une session WebSocket bidirectionnelle audio et vidéo ; `gemini-3.8-live` est GA (`us`, `eu`, `us-central1`) ; `gemini-live-2.5-flash-native-audio` [!DECONSEILLE] est retiré le 13 décembre 2026, à remplacer par 3.8 Live. Gemini 3.5 Transcribe [!PREVERSION] ne fait que la transcription, en flux ou sur fichier.
- **Vidéo et musique** : Veo 3.1 (`veo-3.1-generate-001`, variante `fast`), Gemini Omni Flash [!PREVERSION], Lyria.

## Modèles partenaires et ouverts

| Mode | Modèles proposés | Appel | Facturation |
|---|---|---|---|
| **Gemini** (Google) | Famille ci-dessus | `generateContent`, SDK `google-genai` | Jetons, ou débit provisionné |
| **Partenaire en MaaS** | Anthropic Claude (Opus 5.5, Opus 5, Sonnet 5, Fable 5, Haiku 4.5…), xAI Grok 4.x, Mistral (Medium 3, Small 3.1, OCR, Codestral 2), AI21 Jamba [!PREVERSION] | API de l'éditeur exposée par la plateforme : format Messages d'Anthropic par `rawPredict`, API compatible OpenAI pour Grok | Jetons, au tarif de l'éditeur ; activation et acceptation des conditions dans Model Garden |
| **Ouvert en MaaS** | Llama 3.3 et 4 (Maverick, Scout), DeepSeek (R1, V3.1, V3.2, OCR), Qwen3, gpt-oss 20B et 120B, Kimi K2, GLM, MiniMax M2, Gemma 4 26B, embeddings E5 | API *Chat Completions* compatible OpenAI | Jetons, sans machine réservée ; accès à accorder aux utilisateurs |
| **Ouvert auto-déployé** | Gemma, Llama, Qwen, modèles du Hub Hugging Face, poids réglés par soi | *Endpoint* dédié, conteneur vLLM, Hex-LLM (TPU), SGLang, TGI, ou vLLM sur [GKE](#gke) | Machines et accélérateurs, facturés tant que l'endpoint existe |

Le MaaS convient au prototypage, au trafic variable et à qui ne veut pas gérer de GPU. L'auto-déploiement se justifie pour des poids personnalisés, un trafic élevé et prévisible (coût par jeton plus bas à pleine charge), le choix exact du matériel, ou une exigence d'isolement que le service mutualisé ne couvre pas. Le déploiement d'un endpoint est détaillé dans [Entraîner et servir un modèle](#entrainer-et-servir).

Pour les modèles ouverts en MaaS, prompts et réponses ne sont pas partagés avec des tiers ; pour les partenaires comme pour les ouverts, la journalisation des prompts est désactivée par défaut. Les emplacements varient d'un modèle à l'autre : Claude 4.7 et suivants sont proposés sur les endpoints `global`, `us` et `eu`, mais le débit provisionné n'existe pas sur `global`.

## Adapter le modèle

![Arbre de décision : du modèle de base au modèle adapté](../../svg/adaptation-modele.svg)

On monte d'un échelon seulement quand l'évaluation (voir [Évaluer et sécuriser](#evaluer-et-securiser)) montre que le précédent ne suffit pas. Chaque échelon coûte plus cher à construire et à maintenir.

1. **Prompting** : instructions système, exemples dans le prompt (*few-shot*), sortie structurée par schéma JSON, niveau de réflexion (*thinking*). L'optimiseur de prompts de la plateforme réécrit les instructions système, seul ou à partir d'exemples de réponses jugées insuffisantes ; il sert aussi à reprendre un prompt lors d'un changement de modèle. C'est le point de départ, et souvent le point d'arrivée.
2. **RAG et ancrage** (*grounding*) : quand il manque des **connaissances** — documents internes, données fraîches, référentiel produit —, on les récupère au moment de la requête et on les donne au modèle, avec citations. Ancrage sur Google Search, sur [Agent Search](#agent-search), sur RAG Engine ou sur un index existant (voir [RAG](#rag)). Le réglage n'apprend pas de faits de façon fiable : il ne remplace pas le RAG.
3. **Réglage supervisé** : quand il manque un **comportement** constant — format, ton, classification, extraction, vocabulaire métier — et qu'on dispose de quelques centaines d'exemples entrée → sortie. Le résultat est un modèle réglé, appelé comme le modèle de base et sur le même quota. Il raccourcit aussi les prompts, donc réduit coût et latence.
4. [!DECONSEILLE] **Réglage par préférence** : quand la qualité se juge par comparaison (réponse A meilleure que B) plutôt que par une sortie exacte. Seuls Gemini 2.5 Flash et 2.5 Flash-Lite l'acceptent, et ils sont retirés le 20 octobre 2026. Le réglage par renforcement [!PREVERSION], avec une fonction de récompense écrite par soi, s'applique à Gemini 3.5 Flash et 3.1 Flash-Lite, réglés en `us-central1` ou en `europe-west4` (voir [Régler un modèle Gemini](#regler-gemini)).
5. **Modèle ouvert** : quand il faut posséder les poids, les régler librement (LoRA, QLoRA, réglage complet) ou les servir hors de Google. Gemma 4 est le point d'entrée naturel. Entraîner un modèle génératif de zéro ne se justifie presque jamais.

## Critères de choix

| Critère | Ce qui départage |
|---|---|
| **Qualité** | 3.1 Pro [!PREVERSION] pour le raisonnement difficile ; 3.5 Flash couvre l'essentiel des agents et du code, 3.8 Flash, plus capable, est à tester ; Flash-Lite pour la classification, l'extraction, le routage |
| **Latence** | Flash-Lite, niveau de réflexion bas, sortie courte, *streaming* ; 3.8 Flash n'accepte pas `MINIMAL` (valeurs `LOW`, `MEDIUM` par défaut, `HIGH`) |
| **Coût par jeton** | Flash-Lite < Flash < Pro ; lot et Flex PayGo à −50 % ; cache de contexte −90 % sur les jetons en cache (voir [Appeler Gemini](#appeler-gemini)) |
| **Résidence des données** | Endpoint régional ou multirégional (`us`, `eu`) : le traitement ML reste dans la juridiction. L'endpoint `global` n'en garantit aucune |
| **Contrôles de sécurité** | CMEK, VPC Service Controls, résidence et Access Transparency sur les modèles GA ; **aucun sur les modèles en *preview*** |
| **Taille du contexte** | 1 M de jetons pour toute la famille Gemini ; au-delà d'un corpus qui tient dans le prompt, le RAG coûte moins cher qu'un contexte rempli à chaque appel |
| **Durée de vie** | Date de retrait publiée (3.5 Flash, Flash-Lite) contre disponibilité courte (3.6 à 3.8 Flash) |
| **Réglage** | 3.5 Flash et 3.1 Flash-Lite pour le supervisé et le renforcement ; pas de réglage sur 3.8 Flash ni sur 3.1 Pro |

> [!TIP]
> Comparer deux modèles sur ses propres données avant de choisir : le service d'évaluation note les réponses de plusieurs modèles, Gemini ou partenaires, sur le même jeu de prompts. Un classement public ne dit rien du cas d'usage.

## Pièges

- **Un ID de modèle qui disparaît.** Un appel vers un modèle retiré échoue. Épingler l'ID complet dans la configuration, suivre la table des retraits et planifier la migration comme une mise à jour de dépendance, évaluation comprise. Au 24 septembre 2026, toute la génération 2.5 doit être migrée avant le 20 octobre.
- **L'endpoint `global` pris par défaut.** Il donne la meilleure disponibilité et le moins d'erreurs 429, mais la requête peut être traitée dans n'importe quelle région. Pour une contrainte de résidence, utiliser `us`, `eu` ou une région, et bloquer `global` par la contrainte d'organisation `constraints/gcp.restrictEndpointUsage`. Le réglage et les corpus RAG Engine ne fonctionnent pas sur `global`.
- **Un endpoint multirégional derrière un accès privé à Google.** Les hôtes `aiplatform.us.rep.googleapis.com` et `aiplatform.eu.rep.googleapis.com` ne passent pas par l'accès privé à Google : il faut un endpoint [Private Service Connect](#private-service-connect) vers les API régionales.
- **Une *preview* en production.** Gemini 3.1 Pro [!PREVERSION] : pas de CMEK, pas de VPC Service Controls, pas d'engagement de résidence, et des changements possibles sans préavis.
- **Régler trop tôt.** Un réglage fige une version de modèle et devra être refait à chaque migration. Un meilleur prompt ou un meilleur RAG se transporte d'un modèle à l'autre.
- **Un endpoint auto-déployé laissé allumé.** Il coûte le prix des GPU sans trafic ; pour un usage intermittent, le MaaS revient presque toujours moins cher.

## Alternatives en logiciel libre

Seuls les modèles dont les poids sont publiés sous une licence libre reconnue par l'OSI figurent ici ; la licence se vérifie modèle par modèle, sur sa fiche.

- **Gemma 4** (Apache 2.0) : modèles multimodaux de Google, de E2B à 31B, réglables et exécutables hors de Google Cloud. Les Gemma 1 à 3, ShieldGemma et EmbeddingGemma relèvent des conditions d'utilisation Gemma, qui ne sont pas une licence libre.
- **Qwen3** (Apache 2.0) : Qwen3, Qwen3.5, Qwen3.8 27B, ainsi que les modèles d'embeddings et de reclassement Qwen3. Les plus gros Qwen3.8 (2.4T, Flash-Next) sont sous licence propre.
- **Mistral** (Apache 2.0) : Mistral Small 3.x, Magistral Small, Ministral 3, Devstral Small 2 et Mistral Large 3. Mistral Medium, proposé en MaaS, n'a pas de poids sous licence libre.
- **DeepSeek V3.2 et V4** (MIT), **GLM-5.2** (MIT), **gpt-oss** 20B et 120B (Apache 2.0) : grands modèles de raisonnement aux poids libres, dont plusieurs sont aussi proposés en MaaS. GLM-5.3 a sa propre licence.
- **OLMo 3** (Apache 2.0) : modèle d'Allen AI entièrement ouvert, poids, code d'entraînement et données publiés ; **Granite 4** d'IBM (Apache 2.0) vise les usages d'entreprise.
- **vLLM** (Apache 2.0) et **SGLang** (Apache 2.0) pour servir ces modèles sur GPU, **llama.cpp** (MIT) et **Ollama** (MIT) sur un poste ou un petit serveur ; **TRL**, **PEFT**, **Unsloth** et **Axolotl** (Apache 2.0) pour le réglage supervisé, LoRA ou QLoRA, et le réglage par préférence, à la place du réglage géré.

Poids ouverts mais sans licence libre : Llama 3.3 et 4 (licence communautaire Llama), Kimi K2 (MIT modifié), MiniMax M2 (MIT modifié ou licence propre selon la version).
