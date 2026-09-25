---
title: Évaluer et sécuriser une application générative
---

Une application générative ne se teste pas comme du code déterministe : la même question produit des réponses différentes, et un changement de modèle ou de prompt peut tout décaler. Deux disciplines s'en chargent. L'**évaluation** mesure la qualité sur un jeu de cas représentatif, avant chaque changement puis en production. La **sécurisation** empile des contrôles indépendants autour du modèle : filtres, Model Armor, ancrage vérifié, gouvernance des données. Les deux s'appuient sur [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform).

## Le service d'évaluation

Le *Gen AI evaluation service* note les réponses d'un ou plusieurs modèles sur un jeu de prompts, avec quatre familles de métriques :

| Méthode | Principe | Quand l'utiliser |
|---|---|---|
| **Rubriques adaptatives** (recommandé) | Un modèle juge génère pour chaque prompt une liste de tests réussi / échoué, puis vérifie la réponse contre chacun ; le score est le taux de réussite | Point de départ : qualité générale, respect des consignes, sans réponse de référence |
| **Rubriques statiques** | Même grille pour tous les prompts, note chiffrée par un modèle juge | Dimension précise et comparable dans le temps : ancrage, sécurité, fluidité |
| **Métriques calculées** | Algorithme déterministe contre une réponse de référence : ROUGE, BLEU, correspondance exacte | Extraction, traduction, classification, quand la vérité terrain existe |
| **Fonctions personnalisées** | Code Python qui renvoie un score | Règle métier : format valide, champ obligatoire, montant cohérent |

Les métriques gérées s'appellent par `types.RubricMetric` : `GENERAL_QUALITY` (défaut), `TEXT_QUALITY`, `INSTRUCTION_FOLLOWING`, `GROUNDING` (chaque phrase étiquetée *supported*, *unsupported*, *contradictory* au regard du contexte fourni), `SAFETY`, et pour les agents `HALLUCINATION`, `TOOL_USE_QUALITY`, `MULTI_TURN_TASK_SUCCESS`. Chaque métrique est versionnée ; en épingler la version (`GENERAL_QUALITY(version="v1")`) garde des scores comparables d'une campagne à l'autre.

L'évaluation passe par le client GenAI du SDK Agent Platform (`pip install google-cloud-aiplatform[evaluation]`, module `vertexai`) :

```python
import pandas as pd
from vertexai import Client, types

eval_client = Client(project="PROJECT_ID", location="REGION")
prompts = pd.DataFrame({"prompt": ["Résume ce ticket : ...", "Quel est le délai de rétractation ?"]})

actuel = eval_client.evals.run_inference(model="gemini-3.5-flash", src=prompts)
candidat = eval_client.evals.run_inference(model="gemini-3.8-flash", src=prompts)  # [*]
resultat = eval_client.evals.evaluate(
    dataset=[actuel, candidat],
    metrics=[types.RubricMetric.GENERAL_QUALITY, types.RubricMetric.INSTRUCTION_FOLLOWING],
)
resultat.show()
```

> [!TIP]
> [\*] Gemini 3.8 Flash (`gemini-3.8-flash`), le plus récent des Flash, peut être testé à la place de 3.5 Flash : il est plus capable, mais sa disponibilité est courte (pas de date de retrait garantie, préavis d'au moins 45 jours), il ne se règle pas, et il n'est servi que sur `global`, `us` et `eu` (voir [Choisir un modèle](#choisir-un-modele)).

- **Ponctuelle ou comparative.** Une évaluation *pointwise* note chaque réponse seule ; une évaluation *pairwise* demande au juge laquelle de deux réponses est la meilleure. Le client GenAI ne propose pas de métriques *pairwise* : on compare deux modèles en passant leurs deux jeux de réponses à `evaluate()`, qui les note sur les mêmes rubriques. Le pipeline AutoSxS garde la comparaison par paires, sur des prédictions déjà produites.
- **Modèle juge** (*autorater*) : les métriques gérées appellent Gemini (par exemple une requête à Gemini 2.5 Flash pour `GROUNDING`, six pour `GENERAL_QUALITY`). Un juge a ses biais : inversion des réponses pour neutraliser la position, échantillonnage multiple pour stabiliser la note, et validation du juge contre quelques centaines de notes humaines avant de lui faire confiance.
- **Autres modèles.** `run_inference` appelle aussi un modèle tiers par LiteLLM, et la console évalue les modèles partenaires activés dans [Model Garden](#model-garden).
- **Volume.** `batch_evaluate()` lance une évaluation asynchrone sur un jeu stocké dans Cloud Storage. L'agent de service `service-PROJECT_NUMBER@gcp-sa-vertex-eval.iam.gserviceaccount.com` appelle les modèles juges.

## Hors ligne et en ligne

| | Hors ligne | En ligne |
|---|---|---|
| **Données** | Jeu de référence versionné : cas nominaux, cas limites, attaques connues, régressions passées | Échantillon du trafic réel |
| **Moment** | Avant chaque changement de modèle, de prompt, de réglage ou de source RAG ; dans la CI | En continu |
| **Outil** | `evaluate()`, `batch_evaluate()`, console | Moniteurs en ligne des agents (échantillonnage de Cloud Trace et Cloud Logging toutes les dix minutes environ, scores exportés vers [Cloud Monitoring](#cloud-monitoring)) ; pour une application sans agent, journal des requêtes vers BigQuery puis évaluation par lots |
| **Décision** | Bloquer la mise en production sous un seuil | Alerter sur une dérive, alimenter le jeu hors ligne |

La journalisation des requêtes et réponses vers [BigQuery](#bigquery) [!PREVERSION] se configure par modèle et par projet, avec un taux d'échantillonnage. Elle est désactivée par défaut, et l'activer rompt la non-conservation des données : réserver les données réelles à un projet et une table sous contrôle. Le déploiement et la surveillance des agents sont détaillés dans [Déployer un agent](#deployer-un-agent).

## Couches de protection

- **Filtres non configurables** : contenus pédopornographiques, données personnelles sensibles (arrêt `SPII`), récitation de contenus protégés (arrêt `RECITATION`). Toujours actifs.
- **Filtres de contenu configurables** : quatre catégories (`HARM_CATEGORY_HATE_SPEECH`, `HARASSMENT`, `SEXUALLY_EXPLICIT`, `DANGEROUS_CONTENT`), chacune avec un seuil (`BLOCK_LOW_AND_ABOVE`, `BLOCK_MEDIUM_AND_ABOVE`, `BLOCK_ONLY_HIGH`, `BLOCK_NONE`, `OFF`) et une méthode (`SEVERITY` par défaut, ou `PROBABILITY`). Une réponse bloquée s'arrête avec `finish_reason = SAFETY` et un contenu vide.
- **Instructions système** : elles orientent le modèle (sujets à refuser, ton, marque), sans rien garantir face à un utilisateur déterminé.
- **Gemini comme filtre** : un appel à un modèle léger (Flash-Lite) qui classe l'entrée ou la sortie selon une politique propre à l'entreprise, pour les cas que les filtres génériques ne couvrent pas.
- **[Sensitive Data Protection](#sensitive-data-protection)** : détection et masquage des données personnelles avant l'envoi au modèle ou avant l'affichage.
- **Model Armor** : service Google Cloud (GA) qui inspecte prompts et réponses contre des **modèles** (*templates*) de filtres : injection de prompt et contournement (*jailbreak*), catégories d'IA responsable, données sensibles (par Sensitive Data Protection), URL malveillantes, texte des PDF. Chaque filtre a un seuil de confiance (`HIGH`, `MEDIUM_AND_ABOVE`, `LOW_AND_ABOVE`) et un mode : inspection seule, journalisée dans Cloud Logging, ou inspection et blocage.

Model Armor se branche de trois façons : par requête (`model_armor_config` du SDK, avec un modèle pour l'entrée et un pour la sortie), pour tout un projet par des **paramètres plancher** (*floor settings*) appliqués à chaque `generateContent`, ou sur Agent Gateway pour tous les agents qui y passent. Il s'intègre aussi à [Apigee](#apigee) et s'appelle directement par son API pour une application hors Google Cloud.

```python
from google.genai import types  # client google-genai : voir Appeler Gemini

response = client.models.generate_content(
    model="gemini-3.5-flash",  # [*]
    contents="Question de l'utilisateur",
    config=types.GenerateContentConfig(model_armor_config=types.ModelArmorConfig(
        prompt_template_name="projects/PROJECT_ID/locations/REGION/templates/entree",
        response_template_name="projects/PROJECT_ID/locations/REGION/templates/sortie",
    )),
)
```

Le compte de service de la plateforme (`service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com`) doit porter `roles/modelarmor.user`. `model_armor_config` exclut `safety_settings` dans la même requête.

## Ancrage et citations

Une réponse ancrée cite ses sources : avec l'ancrage Google Search, Agent Search ou RAG Engine, `grounding_metadata` renvoie les passages utilisés (`grounding_chunks`) et le rattachement de chaque segment de réponse à ses sources (`grounding_supports`). Trois contrôles à combiner :

- **Afficher les citations** et les liens vers les documents, pour que l'utilisateur vérifie. Avec Google Search, les suggestions de recherche renvoyées doivent être affichées, selon les conditions du service.
- **Vérifier à l'exécution** : l'API *check grounding* d'[Agent Search](#agent-search) rend en moins de 500 ms un score de 0 à 1 et les citations de chaque affirmation d'une réponse au regard de faits fournis ; sous un seuil, on refuse ou on reformule.
- **Mesurer hors ligne** avec la métrique `GROUNDING`, sur le contexte réellement récupéré (voir [RAG](#rag)).

## Gouvernance des données

- **Pas d'entraînement sur les données client.** Google n'utilise pas les prompts ni les réponses pour entraîner ou régler un modèle sans autorisation, pour tous les modèles gérés, GA ou *preview*.
- **Rétention.** La surveillance des abus peut journaliser des prompts suspects jusqu'à 90 jours, dans la région du projet, sans CMEK ; une exemption se demande. L'ancrage Google Search conserve les requêtes dérivées trois jours, Google Maps trente jours, sans option pour l'éviter : pour une non-conservation stricte, utiliser *Web Grounding for Enterprise*. Le cache implicite se désactive au niveau du projet.
- **Résidence.** Les données au repos restent dans l'emplacement choisi. Le traitement ML reste dans la juridiction avec un endpoint régional ou `us` / `eu` ; l'endpoint `global` ne donne aucune garantie. L'endpoint `eu` couvre les seuls États membres de l'Union : ni le Royaume-Uni ni la Suisse.
- **Minimisation.** Jeux de réglage, jeux d'évaluation, journaux de requêtes et traces ne gardent que les données utiles ; les données personnelles y entrent pseudonymisées par Sensitive Data Protection, qui peut aussi masquer ce que l'application écrit dans ses journaux ([Well-Architected Framework, sécurité](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/security)).
- **Périmètre.** [VPC Service Controls](#vpc-service-controls) enferme l'API de la plateforme, les buckets et les tables dans un périmètre contre l'exfiltration ; l'accès privé passe par [Private Service Connect](#private-service-connect). Un nouveau périmètre se pose d'abord en [mode simulation](https://docs.cloud.google.com/vpc-service-controls/docs/dry-run-mode) (*dry run*) : les violations sont journalisées sans être bloquées, ce qui révèle les flux légitimes à autoriser.
- **Chiffrement.** CMEK par [Cloud KMS](#cloud-kms) sur l'inférence en ligne, les lots, le cache et le réglage, selon le modèle.
- **Accès.** Une règle d'administration Model Garden limite les modèles utilisables à une liste validée ; `constraints/gcp.restrictEndpointUsage` bloque l'endpoint `global`.

## Matrice risque → contrôle

| Risque | Contrôle principal | En complément |
|---|---|---|
| Injection de prompt, directe ou cachée dans un document récupéré | Model Armor, filtre injection et *jailbreak* sur l'entrée | Contenu récupéré séparé des instructions ; outils à privilèges minimaux |
| Contenu haineux, dangereux, sexuel | Filtres de contenu configurables | Model Armor sur la sortie ; métrique `SAFETY` |
| Fuite de données personnelles | Sensitive Data Protection, ou filtre données sensibles de Model Armor | Filtre `SPII` non configurable |
| Réponse inventée (*hallucination*) | Ancrage (RAG, Google Search) avec citations | *Check grounding* en ligne ; métrique `GROUNDING` hors ligne |
| Hors sujet, contraire à la marque | Instructions système | Gemini comme filtre ; rubriques adaptatives |
| Régression après un changement de modèle | Jeu d'évaluation hors ligne dans la CI | Épinglage des versions de modèle et de métrique ; déploiement progressif sur une part des utilisateurs (répartition du trafic de Cloud Run ou d'Agent Runtime) |
| Dérive en production | Moniteurs en ligne, alertes Cloud Monitoring | Retour utilisateur versé au jeu hors ligne |
| Exfiltration vers un projet tiers | VPC Service Controls | Private Service Connect ; journaux d'audit |
| Traitement hors juridiction | Endpoint régional ou `us` / `eu` | Blocage de `global` par règle d'administration |
| Modèle non validé utilisé par une équipe | Règle d'administration Model Garden | IAM `roles/aiplatform.user` limité aux comptes de service des applications |
| URL malveillante dans une réponse | Filtre URL de Model Armor | Aucun rendu automatique des liens |
| Abus de volume : déni de service, extraction du modèle par requêtes en masse, facture qui s'emballe | Authentification et limites de débit par consommateur ([Apigee](#apigee), [API Gateway](#api-gateway)) | Alertes sur les pics de volume et les motifs de requêtes anormaux ([Well-Architected Framework, sécurité](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/security)) |

## Pièges

- **Filtres désactivés par défaut.** À partir de Gemini 3.5 Flash, le seuil par défaut des filtres configurables est `OFF` : sans `safety_settings`, rien n'est bloqué au-delà des filtres fixes. Fixer explicitement les seuils voulus.
- **Model Armor contourné sans bruit.** Si Model Armor est indisponible, absent de la région ou en erreur, la plateforme poursuit la requête sans l'inspecter. Un modèle Model Armor absent de la région où la requête est routée fait échouer l'appel (`Template not found`) : avec l'endpoint `global`, créer les modèles dans toutes les régions possibles, ou passer par un endpoint régional. L'intégration ne scanne pas les fichiers joints : appeler l'API Model Armor directement pour un PDF.
- **Données sensibles bloquées, non masquées.** Dans l'intégration à la plateforme, un filtre Sensitive Data Protection déclenché bloque la requête en mode blocage : le texte masqué n'est pas transmis au modèle. Pour masquer puis envoyer, appeler Sensitive Data Protection ou Model Armor avant l'appel.
- **Seuils trop stricts.** `LOW_AND_ABOVE` sur les catégories générales bloque beaucoup de contenus légitimes. Commencer par `HIGH` ou `MEDIUM_AND_ABOVE`, en inspection seule, mesurer les faux positifs, puis activer le blocage.
- **Contrôles absents des *preview*.** Résidence, CMEK, VPC Service Controls et Access Transparency ne s'appliquent pas aux modèles en *preview*.
- **Un prompt non versionné.** Un prompt modifié en place change le comportement sans trace ni retour arrière possible. Le versionner avec l'ID du modèle et les paramètres, dans Git ou par la [gestion des prompts](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/prompt-classes) du SDK (`client.prompts.create_version`, restauration d'une version), et rattacher chaque version à ses résultats d'évaluation.
- **Un juge seul.** Un score produit par un modèle juge n'est pas une vérité : garder un échantillon noté par des humains, et ne jamais évaluer un modèle avec lui-même comme seul juge.

## Alternatives en logiciel libre

- **promptfoo** (MIT) : cas de test en YAML, assertions déterministes et par modèle juge, comparaison de modèles et de prompts côte à côte, exécution en CI ; un module de *red teaming* génère des attaques par injection et contournement.
- **DeepEval** (Apache 2.0) : métriques par modèle juge (fidélité au contexte, pertinence, hallucination, rubriques G-Eval) écrites comme des tests `pytest` ; le plus proche des rubriques statiques et de `GROUNDING`.
- **Inspect** (MIT) et **lm-evaluation-harness** (MIT) : évaluations reproductibles de modèles sur des jeux publics ou maison ; Inspect évalue aussi les agents et leurs outils dans des bacs à sable.
- **Langfuse** (MIT, hors répertoires `ee`) : traces de production, évaluation en ligne par modèle juge sur un échantillon, jeux de données et annotation humaine ; l'équivalent des moniteurs en ligne et du retour utilisateur.
- **NeMo Guardrails** (Apache 2.0) et **Guardrails AI** (Apache 2.0) : garde-fous programmables autour du modèle, filtrage des entrées et sorties, détection de *jailbreak*, validation de format, vérification de l'ancrage ; la fonction de Model Armor, exécutée dans l'application. Comme classifieurs, **gpt-oss-safeguard** (Apache 2.0), qui applique une politique écrite par soi, **Qwen3Guard** et **Granite Guardian** (Apache 2.0) ; Llama Guard et ShieldGemma n'ont pas de licence libre.
- **Presidio** (MIT) : détection et anonymisation des données personnelles par règles et reconnaissance d'entités, l'équivalent de Sensitive Data Protection.
- **garak** (Apache 2.0) : scanner de vulnérabilités de modèles de langage (injection, fuite de données, contenu toxique), pour attaquer son application avant la mise en production.
