---
title: Régler un modèle Gemini
---

Le réglage (*tuning*) modifie le comportement d'un modèle Gemini à partir de ses propres exemples. C'est le dernier échelon de l'adaptation, après le prompting et le RAG (voir [Choisir un modèle génératif](#choisir-un-modele)) : on n'y monte que lorsqu'une évaluation montre que les échelons précédents ne suffisent pas. Le réglage de Gemini n'existe que dans [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) ; la Gemini Developer API et AI Studio n'en proposent pas.

## Quand régler

- **Oui** : un format, un ton ou une classification que le prompt ne tient pas de façon régulière ; des erreurs récurrentes qui résistent aux consignes ; un comportement difficile à décrire mais facile à montrer ; de longs exemples *few-shot* répétés à chaque appel, que le réglage permet de retirer du prompt.
- **Non** : pour apprendre des faits ou des données qui changent (c'est le rôle du [RAG](#rag)) ; sans jeu d'évaluation pour prouver le gain ; sur un modèle proche de son retrait.
- La documentation recommande d'analyser les erreurs du modèle avant d'ajouter des exemples : la qualité des étiquettes compte plus que leur nombre. Un modèle de base plus récent rend parfois le réglage inutile ; on le teste d'abord sans réglage.

## Méthodes et modèles

État en septembre 2026 (pages *Introduction to tuning* et *Model versions and lifecycle*) :

| Méthode | Modèles Gemini réglables | Statut | Données |
|---|---|---|---|
| **Supervisé** (*supervised fine-tuning*) | `gemini-3.5-flash` (retrait au plus tôt le 19 mai 2027), `gemini-3.1-flash-lite` (au plus tôt le 7 mai 2027) ; `gemini-2.5-pro`, `-flash`, `-flash-lite` (retrait le 20 octobre 2026) | GA | Paires entrée → sortie : texte, image, audio, vidéo, documents, appels de fonctions |
| [!DECONSEILLE] **Par préférence** (*preference tuning*) | `gemini-2.5-flash`, `gemini-2.5-flash-lite` seulement | GA, modèles retirés le 20 octobre 2026 : pas de nouveau projet, passer au supervisé ou au renforcement sur 3.5 Flash | Un prompt, une réponse préférée, une réponse rejetée ; texte seul |
| [!PREVERSION] **Par renforcement** (*reinforcement learning fine-tuning*) | `gemini-3.5-flash`, `gemini-3.1-flash-lite` | API `v1beta1` | Des prompts et une fonction de récompense ; texte, image, audio, vidéo (3.5 Flash) |
| **Continu** (*continuous tuning*) | Tous les modèles du réglage supervisé | GA | Nouvel entraînement à partir d'un modèle réglé ou d'un point de contrôle : supervisé → supervisé, supervisé → renforcement, renforcement → renforcement |

Ne se règlent pas : Gemini 3.5 Flash-Lite, 3.6 à 3.8 Flash, 3.1 Pro. Le réglage par renforcement note chaque réponse générée par une fonction de récompense, bornée à [-1, 1] : correspondance de chaîne avec une valeur attendue, modèle Gemini juge, code Python exécuté par le service, ou service [Cloud Run](#cloud-run) de son choix, combinables jusqu'à 16 avec des poids. Les conditions *Pre-GA* excluent les données confidentielles et l'usage en production. La **distillation**, où un grand modèle enseignant produit les réponses qui entraînent un petit modèle, n'existe que pour les modèles ouverts (voir plus bas).

## Matrice de choix

| Méthode | Besoin | Données minimales | Coût du réglage |
|---|---|---|---|
| **Supervisé** | Comportement fixe : format, classification, extraction, style, appel d'outils | 100 exemples pour commencer, 100 à 500 recommandés, des milliers si besoin | Jetons du jeu × *epochs* : 10 $ par million sur 3.5 Flash, 3 $ sur 3.1 Flash-Lite |
| **Préférence** | Qualité jugée par comparaison (ton, utilité), sans sortie exacte | Paires notées 1 (préférée) et 0 (rejetée), après un réglage supervisé sur les réponses préférées | Jetons du prompt × 2, plus ceux des deux réponses : 5 $ par million sur 2.5 Flash |
| **Renforcement** | Objectif vérifiable par programme : raisonnement, respect de consignes complexes, calcul | Jusqu'à 5 000 prompts, avec les valeurs attendues dans `references` | 10 $ par million de jetons de la phase d'entraînement sur 3.5 Flash, plus les appels du juge ou de Cloud Run |
| **Modèle ouvert géré** | Posséder les poids, servir hors de Google | Paires prompt → réponse ou conversations, séquences de 8 192 jetons pour la plupart des modèles | Par million de jetons (Gemma 3 27B : 6,83 $), puis un endpoint dédié facturé à l'heure |

![Cycle de réglage d'un modèle Gemini](../../svg/cycle-reglage-gemini.svg)

## Préparer le jeu de données

Un fichier JSONL par jeu, déposé dans [Cloud Storage](#cloud-storage) (la région du bucket est libre), une conversation par ligne, au format de `generateContent` :

```json
{"systemInstruction": {"parts": [{"text": "Classe le ticket : materiel, logiciel, acces."}]}, "contents": [{"role": "user", "parts": [{"text": "Mon badge n'ouvre plus la porte du 2e."}]}, {"role": "model", "parts": [{"text": "acces"}]}]}
```

- `role` vaut `user` ou `model` ; une conversation multi-tours alterne les deux. `tools`, `functionCall` et `functionResponse` servent à régler l'appel de fonctions. Les images, l'audio et les PDF passent par `fileData` avec une URI `gs://`.
- **Limites** (3.5 Flash et 3.1 Flash-Lite) : 131 072 jetons d'entrée et de sortie par exemple ; fichier de 1 Go ; 10 millions d'exemples texte ou 300 000 multimodaux ; jeu de validation de 5 000 exemples, ou 30 % du jeu d'entraînement quand il dépasse 1 000 exemples. Le renforcement se limite à 5 000 exemples de 32 768 jetons d'entrée.
- **Validation** : un jeu séparé, fortement recommandé ; sans lui, rien ne signale le surapprentissage. Un troisième jeu, de test, jamais vu par le réglage, sert à l'évaluation finale.
- **Format de production** : les exemples reprennent exactement les consignes, les champs et leur ordre du trafic réel. Un modèle réglé sur `question:` puis `contexte:` ne reconnaît pas la tâche si la production inverse les deux.

## Lancer le réglage

Depuis la console, **Agent Platform Studio** → **Create tuned model** ; depuis Python, `client.tunings.tune` du SDK `google-genai` (2.25, qui marque ce module comme expérimental). Le client vise la région du job, et un second client la multirégion de service :

```python
import time
from google import genai
from google.genai import types

client = genai.Client(enterprise=True, project="PROJECT_ID", location="europe-west4")
job = client.tunings.tune(
    base_model="gemini-3.5-flash",
    training_dataset=types.TuningDataset(gcs_uri="gs://BUCKET/reglage/train.jsonl"),
    config=types.CreateTuningJobConfig(
        tuned_model_display_name="tri-tickets-v1",
        validation_dataset=types.TuningValidationDataset(gcs_uri="gs://BUCKET/reglage/validation.jsonl"),
        labels={"app": "support"},
    ),
)
while not job.has_ended:
    time.sleep(60)
    job = client.tunings.get(name=job.name)

stats = job.tuning_data_stats.supervised_tuning_data_stats
print(job.state, job.tuned_model.endpoint, stats.total_billable_token_count)

inference = genai.Client(enterprise=True, project="PROJECT_ID", location="eu")
reponse = inference.models.generate_content(
    model=job.tuned_model.endpoint,  # projects/…/locations/eu/endpoints/…
    contents="Ticket : l'imprimante du 3e affiche l'erreur E-42.",
    config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="MINIMAL")),
)
```

`method="PREFERENCE_TUNING"` ou `"REINFORCEMENT_TUNING"` dans la configuration choisit une autre méthode ; `base_model` qui désigne un modèle réglé (`projects/…/models/ID@VERSION`) lance un réglage continu, avec `pre_tuned_model_checkpoint_id` pour partir d'un point de contrôle précis.

| Hyperparamètre | Paramètre du SDK | Effet |
|---|---|---|
| *Epochs* | `epoch_count` | Passages complets sur le jeu ; la valeur par défaut s'ajuste à sa taille |
| Taille de l'adaptateur | `adapter_size` | Nombre de paramètres entraînés : 1, 2, 4, 8 ou 16 (8 au plus sur 2.5 Pro). Plus grand, il apprend des tâches plus complexes mais demande plus de données et de temps |
| Multiplicateur du taux d'apprentissage | `learning_rate_multiplier` | 1 par défaut ; plus haut pour converger plus vite, plus bas contre le surapprentissage (de 0,25 à 4 en renforcement) |
| Points de contrôle | `export_last_checkpoint_only` | Faux par défaut : un point de contrôle par *epoch* jusqu'à 10 *epochs*, une dizaine répartis au-delà, chacun déployé sur son propre endpoint pendant le réglage |

Le premier job se lance avec les valeurs par défaut, calibrées par Google pour chaque modèle. Les métriques s'affichent en direct dans l'onglet **Monitor** : `/train_total_loss` et `/train_fraction_of_correct_next_step_preds` (précision par jeton) sur le jeu d'entraînement, leurs équivalents `/eval_…` sur la validation. Une perte de validation qui remonte pendant que celle d'entraînement baisse signale le surapprentissage : on désigne alors comme défaut le point de contrôle d'avant la remontée. Deux pertes qui restent hautes signalent un sous-apprentissage : plus d'*epochs* ou plus d'exemples, par réglage continu. Le quota porte sur le nombre de jobs simultanés, un par défaut, partagé entre toutes les régions et tous les modèles.

## Évaluer contre le modèle de base

La précision par jeton ne mesure pas la qualité de la tâche. On compare le modèle réglé au modèle de base **avec son meilleur prompt** (consignes et *few-shot* compris), sur le jeu de test, par le service d'évaluation décrit dans [Évaluer et sécuriser](#evaluer-et-securiser) : `run_inference` accepte le nom complet de l'endpoint réglé comme `model`, puis `evaluate()` note les deux jeux de réponses sur les mêmes métriques. Correspondance exacte pour une classification ou une extraction, rubriques pour un style. La comparaison inclut le coût et la latence par requête. Pour Gemini 2.5, `evaluation_config` lance l'évaluation pendant le réglage (*preview*, `us-central1`, facturée comme une inférence par lots).

## Déployer et appeler

Le job enregistre le modèle dans Model Registry et le déploie lui-même sur un **endpoint public partagé**, seul type accepté pour un Gemini réglé : pas d'endpoint dédié, privé ou [Private Service Connect](#private-service-connect). Pour 3.5 Flash et 3.1 Flash-Lite, le modèle réglé est servi par l'endpoint multirégional qui correspond à la région du job : `us` (`aiplatform.us.rep.googleapis.com`) pour `us-central1`, `eu` pour `europe-west4`. L'appel est celui du modèle de base, avec le nom de l'endpoint à la place de l'ID du modèle. Le cache implicite s'applique aux modèles réglés (la documentation liste 3.1 Flash-Lite, pas 3.5 Flash) ; le cache explicite ne leur est pas proposé.

## Coût

- **Réglage** : jetons d'entraînement = jetons du jeu × *epochs*. 2 000 exemples de 1 500 jetons sur trois *epochs* font 9 millions de jetons, soit 90 $ sur 3.5 Flash. Chaque nouvelle version et chaque réglage continu se paient à nouveau.
- **Inférence** : à partir de Gemini 3, le jeton d'un endpoint réglé coûte **1,5 fois** celui du modèle de base ; sur Gemini 2.5, le même prix. Pour un trafic dominé par l'entrée, le prompt doit donc raccourcir d'au moins un tiers pour que l'appel réglé coûte moins cher ; le gain vient surtout des exemples *few-shot* et des longues consignes qu'on retire.
- **Autour** : stockage du jeu dans Cloud Storage, appels du juge et de Cloud Run en renforcement, évaluations. Le réglage supervisé est exclu des SLA.

## Régions et résidence des données

- Le job tourne en `us-central1` ou `europe-west4`, seules régions de réglage listées pour les modèles Gemini 3. Le jeu transformé et le modèle réglé sont stockés dans la région du job ; le calcul peut être déporté vers une autre région de la même juridiction (États-Unis ou Union européenne), de façon transparente. Le service reste dans la multirégion correspondante.
- **Identité** : le job s'exécute sous l'agent de service de réglage du projet, ou sous un compte de service désigné, qui reçoit alors `roles/aiplatform.tuningServiceAgent`, l'agent de service ayant `roles/iam.serviceAccountTokenCreator` sur lui.

> [!WARNING]
> Pour le réglage de Gemini 3.5 Flash et 3.1 Flash-Lite, la page du réglage supervisé indique que CMEK n'est pas pris en charge, alors que le tableau des contrôles de sécurité annonce résidence, CMEK et VPC Service Controls pour le réglage de 3.5 Flash (sans Access Transparency) et ne mentionne pas 3.1 Flash-Lite. Vérifier avec Google avant de dépendre de CMEK. Un réglage continu doit reprendre la clé CMEK du modèle de départ.

## Quand le modèle de base est retiré

Un modèle réglé ne se transporte pas vers une nouvelle version de Gemini : il meurt avec son modèle de base. La procédure de migration de Google est la suivante : évaluer d'abord le nouveau modèle **sans réglage**, qui suffit parfois ; sinon relancer un job sur le nouveau modèle avec les hyperparamètres par défaut, sans reprendre ceux de l'ancienne version ; comparer au modèle réglé en place sur le jeu de test ; basculer. Le réglage devient ainsi une étape de pipeline (voir [MLOps](#mlops)) : jeux versionnés, job, évaluation, seuil de décision. Au 24 septembre 2026, tout modèle réglé sur Gemini 2.5 est à refaire avant le 20 octobre ; un réglage par préférence n'a pas d'équivalent sur Gemini 3 et se remplace par un réglage supervisé sur les réponses préférées, ou par renforcement avec un juge.

## Régler un modèle ouvert

Quand il faut posséder les poids, le choix passe par [Model Garden](#model-garden) :

- **Réglage géré** (Vertex AI SDK, `vertexai.tuning.sft`) : Gemma 4 (E2B à 31B) en LoRA, Gemma 3, Qwen 3 à 3.6, Llama 3.1 à 3.3 et 4 Scout, GLM 4.7 Flash, en réglage complet ou LoRA selon le modèle. Formats `prompt`/`completion`, `messages` ou `contents`. Le job se lance de préférence sur `global`, qui choisit une région disposant d'accélérateurs. La **distillation** (par `google-genai`) fait produire les réponses par DeepSeek ou Qwen en MaaS pour entraîner un Qwen 3 ou un Gemma 3.
- **Entraînement personnalisé** : les notebooks des fiches de modèle règlent Gemma par PEFT (LoRA, QLoRA) ou Axolotl dans un job [Managed Training](#entrainer-et-servir), puis déploient les poids sur un endpoint dédié. C'est la voie pour une méthode, un modèle ou un matériel que le réglage géré ne couvre pas.

Le modèle ouvert réglé se sert sur un endpoint facturé à l'heure tant qu'il existe, là où Gemini réglé se paie au jeton.

## Pièges

- **Régler pour apprendre des faits.** Le modèle réglé récite mal et vieillit à chaque mise à jour des données ; les connaissances passent par le RAG, le réglage par le comportement.
- **Sortie structurée sur un modèle réglé.** La documentation signale une baisse de qualité avec `response_schema` : le réglage se fait sans génération contrôlée. Apprendre le format JSON par les exemples et appeler le modèle réglé sans schéma.
- **Réflexion laissée par défaut.** Le réglage apprend la réponse sans le raisonnement : appeler le modèle réglé avec `thinking_level="MINIMAL"` (Gemini 3) ou un budget de 0 (2.5), ce qui améliore la qualité et réduit le coût.
- **Mauvais endpoint.** L'ID `gemini-3.5-flash` appelle le modèle de base, sans erreur. Un client sur `global` ou sur `us-central1` n'atteint pas un endpoint servi en `us` ou `eu`.
- **Jeu de test contaminé.** Un exemple présent à la fois dans l'entraînement et dans le test gonfle le score ; dédoublonner avant le découpage.
- **Exemples perdus en silence.** Les statistiques du job (`tuning_data_stats`) comptent les exemples tronqués et écartés, avec la raison ; les lire avant d'interpréter les métriques.
- **Préférence sur un modèle en fin de vie.** Seuls 2.5 Flash et Flash-Lite l'acceptent, retirés le 20 octobre 2026 : ne pas lancer de nouveau projet sur cette méthode.
- **Hyperparamètres recopiés.** Ceux d'un réglage sur 2.5 ne valent pas pour 3.5 ; repartir des valeurs par défaut.

## Alternatives en logiciel libre

Tous ces outils règlent des modèles aux poids libres (Gemma 4, Qwen3, Mistral) sur ses propres GPU ; aucun ne règle Gemini, dont les poids ne sont pas publiés.

- **TRL** (Apache 2.0, Hugging Face) : les trois méthodes de la plateforme, `SFTTrainer` pour le supervisé, `DPOTrainer` et `KTOTrainer` pour la préférence, `GRPOTrainer` et `RLOOTrainer` pour le renforcement avec des fonctions de récompense écrites en Python, plus un `DistillationTrainer`.
- **PEFT** (Apache 2.0, Hugging Face) : LoRA, QLoRA et autres adaptateurs ; le rang de LoRA joue le rôle de la taille d'adaptateur. L'adaptateur se garde et se charge à part du modèle de base, ce qui permet de servir plusieurs réglages sur les mêmes poids.
- **Unsloth** (Apache 2.0 pour la bibliothèque, AGPL-3.0 pour l'interface Studio, dépendance `unsloth-zoo` en LGPL-3.0) : LoRA, QLoRA et GRPO accélérés et économes en mémoire, pour régler un modèle de taille moyenne sur un seul GPU.
- **Axolotl** (Apache 2.0) : un fichier YAML décrit le modèle, le jeu et la méthode (supervisé, DPO, GRPO, LoRA, QLoRA), exécutés sur un ou plusieurs GPU ; Model Garden l'emploie dans un notebook de réglage de Gemma 3.
- **LLaMA-Factory** (Apache 2.0) : interface web et ligne de commande pour le supervisé, la préférence et LoRA sur plus d'une centaine de modèles, au plus près de la console de réglage.
- **verl** (Apache 2.0) et **OpenRLHF** (Apache 2.0) : réglage par renforcement distribué sur plusieurs nœuds, pour les gros modèles et les longues boucles d'échantillonnage.
