---
title: BigQuery ML
---

BigQuery ML entraîne, évalue et appelle des modèles en **SQL**, sans sortir les données de l'entrepôt. Un modèle est un objet de dataset, comme une table ou une vue : il porte la région du dataset et ses droits. Trois usages se partagent la même syntaxe : les **modèles entraînés** sur une table (régression, classification, segmentation, recommandation, séries temporelles), les **modèles importés** entraînés ailleurs, et les **modèles distants** qui délèguent l'inférence à [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) ou à une API ML. Pour savoir si BigQuery ML est la bonne approche, voir [Choisir une approche ML](#choisir-une-approche-ml).

## Quel type de modèle

| Besoin | `MODEL_TYPE` ou fonction | Entraînement | Remarques |
|---|---|---|---|
| Prédire une valeur numérique | `LINEAR_REG` | BigQuery | Référence rapide et explicable (`ML.WEIGHTS`) |
| Classer en 2 à 50 classes | `LOGISTIC_REG` | BigQuery | `AUTO_CLASS_WEIGHTS` pour des classes déséquilibrées |
| Classification ou régression plus précise sur tableau | `BOOSTED_TREE_CLASSIFIER` / `_REGRESSOR` (XGBoost), `RANDOM_FOREST_*` | Agent Platform | Souvent le meilleur rapport qualité-effort sur des données tabulaires |
| Variables creuses, nombreuses catégories | `DNN_*`, `DNN_LINEAR_COMBINED_*` (*Wide & Deep*) | Agent Platform | Réseaux TensorFlow ; poids consultables seulement après `EXPORT MODEL` |
| Meilleur modèle tabulaire sans réglage | `AUTOML_CLASSIFIER` / `_REGRESSOR` | Agent Platform (AutoML) | Ingénierie des variables et hyperparamètres automatiques ; environ 1 000 slots `ML_EXTERNAL` en éditions |
| Segmenter des clients, des appareils | `KMEANS` | BigQuery | Sans étiquette ; `ML.DETECT_ANOMALIES` repère les points éloignés des centroïdes |
| Recommander des produits | `MATRIX_FACTORIZATION` | BigQuery | Retours explicites (notes) ou implicites (clics) ; **éditions uniquement**, pas à la demande |
| Réduire les dimensions, détecter des anomalies | `PCA`, `AUTOENCODER` | BigQuery, Agent Platform | Leur sortie sert aussi d'*embedding* (`AI.GENERATE_EMBEDDING`) |
| Prévoir une série temporelle | `ARIMA_PLUS`, `ARIMA_PLUS_XREG` (avec covariables) | BigQuery | Saisonnalité, jours fériés (`HOLIDAY_REGION`), anomalies ; des milliers de séries par `TIME_SERIES_ID_COL` |
| Prévoir sans entraîner | `AI.FORECAST` (TimesFM) | Aucun | Modèle de fondation préentraîné pour séries temporelles |
| [!PREVERSION] Classer ou régresser sans entraîner | `AI.PREDICT` (TabFM) | Aucun | 50 variables et 10 classes au plus |
| Expliquer la variation d'un indicateur | `CONTRIBUTION_ANALYSIS` | BigQuery | Quelles dimensions expliquent l'écart d'un indicateur entre des données de test et de contrôle (deux périodes, par exemple) |
| Réutiliser un modèle entraîné ailleurs | `ONNX`, `TENSORFLOW`, `TENSORFLOW_LITE`, `XGBOOST` | Hors BigQuery | Chargé depuis Cloud Storage ; prédiction dans BigQuery ; 450 Mo au plus pour ONNX |
| Appeler un modèle servi ailleurs | Modèle distant (`REMOTE WITH CONNECTION`) | Hors BigQuery | Gemini, modèles partenaires et ouverts, endpoint Agent Platform, API ML |

Les modèles marqués « Agent Platform » sont préparés par BigQuery puis entraînés sur l'infrastructure d'Agent Platform : ils ne se simulent pas à blanc (*dry run*) et leur coût d'entraînement s'ajoute à celui de BigQuery.

## Le cycle en SQL

```sql
-- 1. Entraîner : la clause TRANSFORM est enregistrée avec le modèle
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.churn`
  TRANSFORM (
    ML.STANDARD_SCALER(anciennete_jours) OVER () AS anciennete,
    ML.QUANTILE_BUCKETIZE(panier_moyen, 10) OVER () AS panier,
    offre, region, resilie
  )
  OPTIONS (
    MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
    INPUT_LABEL_COLS = ['resilie'],
    DATA_SPLIT_METHOD = 'RANDOM', DATA_SPLIT_EVAL_FRACTION = 0.2,
    MODEL_REGISTRY = 'VERTEX_AI', VERTEX_AI_MODEL_ID = 'churn'
  )
AS SELECT anciennete_jours, panier_moyen, offre, region, resilie
FROM `PROJECT_ID.DATASET.clients_historique`;

-- 2. Évaluer : précision, rappel, F1, log_loss, roc_auc
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.churn`);

-- 3. Prédire sur les données brutes : TRANSFORM est réappliqué automatiquement
SELECT client_id, predicted_resilie, predicted_resilie_probs
FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.churn`,
  (SELECT * FROM `PROJECT_ID.DATASET.clients_actifs`));

-- 4. Expliquer chaque prédiction par ses trois variables les plus influentes
SELECT * FROM ML.EXPLAIN_PREDICT(MODEL `PROJECT_ID.DATASET.churn`,
  (SELECT * FROM `PROJECT_ID.DATASET.clients_actifs`),
  STRUCT(3 AS top_k_features));
```

- **Prétraitement.** Sans `TRANSFORM`, BigQuery ML standardise les nombres et encode les catégories en *one-hot* pour la plupart des modèles (pas pour les arbres). Avec `TRANSFORM`, les fonctions `ML.*` (mise à l'échelle, découpage en quantiles, *one-hot*, croisement de variables, *TF-IDF*) sont calculées à l'entraînement et **réappliquées à l'identique** lors de `ML.EVALUATE` et `ML.PREDICT` : aucune dérive entre entraînement et service. Un modèle `TRANSFORM_ONLY` isole ces règles pour les réutiliser entre plusieurs modèles.
- **Autres fonctions du cycle** : `ML.CONFUSION_MATRIX` et `ML.ROC_CURVE` pour la classification, `ML.GLOBAL_EXPLAIN` et `ML.FEATURE_IMPORTANCE` pour l'importance globale des variables, `ML.RECOMMEND` pour la factorisation de matrices, `ML.VALIDATE_DATA_DRIFT` et `ML.VALIDATE_DATA_SKEW` pour surveiller les données, `ML.TRIAL_INFO` après un réglage d'hyperparamètres (`NUM_TRIALS`).
- **Séries temporelles** :

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ventes_prev`
  OPTIONS (MODEL_TYPE = 'ARIMA_PLUS', TIME_SERIES_TIMESTAMP_COL = 'jour',
           TIME_SERIES_DATA_COL = 'ventes', TIME_SERIES_ID_COL = 'magasin',
           HOLIDAY_REGION = 'FR')
AS SELECT jour, magasin, ventes FROM `PROJECT_ID.DATASET.ventes_jour`;

SELECT * FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.ventes_prev`,
  STRUCT(30 AS horizon, 0.9 AS confidence_level));
```

## IA générative en SQL

Les fonctions `AI.*` envoient chaque ligne à un modèle Gemini d'Agent Platform et rendent la réponse comme une colonne. Sans connexion précisée, elles utilisent les identifiants de l'utilisateur, qui doit avoir le rôle Agent Platform User (`roles/aiplatform.user`).

| Fonction | Usage |
|---|---|
| `AI.GENERATE` | Scalaire, la plus souple : texte, image, audio, vidéo ou PDF en entrée, texte ou `STRUCT` typé en sortie (`output_schema`) |
| `AI.GENERATE_TEXT`, `AI.GENERATE_TABLE` | Table en entrée, sur un modèle distant ; modèles partenaires et ouverts, modèle Gemini réglé |
| `AI.GENERATE_BOOL`, `_INT`, `_DOUBLE` | Une seule valeur typée à extraire |
| `AI.IF`, `AI.CLASSIFY`, `AI.SCORE`, `AI.AGG` | Fonctions gérées : filtrer, classer, noter, résumer ; BigQuery choisit le modèle et construit le *prompt* |
| `AI.EMBED`, `AI.GENERATE_EMBEDDING` | *Embeddings* de texte, d'images ou de vidéos |
| `AI.COUNT_TOKENS` | Estimer les jetons avant de lancer la requête |
| `ML.ANNOTATE_IMAGE`, `ML.TRANSLATE`, `ML.UNDERSTAND_TEXT`, `ML.PROCESS_DOCUMENT`, `ML.TRANSCRIBE` | Appeler Vision, Translation, Natural Language, Document AI ou Speech-to-Text |

`ML.GENERATE_TEXT` et `ML.GENERATE_EMBEDDING` restent acceptées ; la documentation recommande leurs équivalents `AI.GENERATE_TEXT` et `AI.GENERATE_EMBEDDING`, aux colonnes de sortie simplifiées.

```sql
-- Extraction structurée depuis des avis clients
SELECT avis_id,
  AI.GENERATE(
    ('Extrais le produit cité et le motif de réclamation : ', texte),
    endpoint => 'gemini-3.5-flash',
    output_schema => 'produit STRING, motif STRING, urgent BOOL') AS extrait
FROM `PROJECT_ID.DATASET.avis`;

-- Classement dans des catégories maison
SELECT avis_id, AI.CLASSIFY(texte, ['livraison', 'facturation', 'qualité', 'autre']) AS categorie
FROM `PROJECT_ID.DATASET.avis`;
```

`AI.GENERATE` utilise par défaut un modèle Gemini stable choisi par BigQuery (`gemini-2.5-flash` à la date de consultation, septembre 2026, un modèle retiré le 20 octobre 2026 : passer explicitement `endpoint => 'gemini-3.5-flash'` plutôt que de dépendre du défaut) ; les modèles plus récents, dont `gemini-3.5-flash`, ne sont servis que sur les *endpoints* multirégionaux `us`, `eu` ou `global`. Avec les modèles qui raisonnent, les jetons de réflexion sont facturés : `model_params` règle `thinkingConfig`.

## Embeddings et recherche vectorielle

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.emb`
  REMOTE WITH CONNECTION DEFAULT
  OPTIONS (ENDPOINT = 'gemini-embedding-001');

-- Indexer le corpus : la colonne à vectoriser doit s'appeler content
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.docs_emb` AS
SELECT * FROM AI.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.emb`,
  (SELECT doc_id, texte AS content FROM `PROJECT_ID.DATASET.docs`));

-- Les cinq documents les plus proches d'une question
SELECT base.doc_id, base.content, distance
FROM VECTOR_SEARCH(TABLE `PROJECT_ID.DATASET.docs_emb`, 'embedding',
  (SELECT embedding FROM AI.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.emb`,
     (SELECT 'délai de remboursement' AS content))),
  top_k => 5, distance_type => 'COSINE');
```

Sans index, `VECTOR_SEARCH` compare la requête à toutes les lignes : résultat exact, coût proportionnel à la table. `CREATE VECTOR INDEX` (IVF ou ScaNN) passe en recherche approchée, plus rapide mais au rappel un peu moindre ; l'index n'est pas disponible en édition Standard. La **génération autonome d'*embeddings*** maintient une colonne vectorielle à jour quand la source change, et `AI.SEARCH` l'interroge sans appel explicite au modèle. C'est la brique d'un RAG entièrement dans l'entrepôt (voir [RAG](#rag)).

## Registre et service en ligne

`MODEL_REGISTRY = 'VERTEX_AI'` enregistre le modèle dans Model Registry dès la fin de l'entraînement ; `ALTER MODEL` fait de même pour un modèle existant. Le modèle y est versionné, comparé et déployable sur un endpoint pour des prédictions en ligne, sans conteneur à écrire. Tous les types s'enregistrent, mais les modèles XGBoost importés, `ARIMA_PLUS` et `ARIMA_PLUS_XREG` ne se déploient pas. `EXPORT MODEL` écrit le modèle dans Cloud Storage pour le servir ailleurs. Le cycle MLOps complet est dans [MLOps](#mlops).

## Tarification

| Opération | À la demande | Éditions |
|---|---|---|
| `CREATE MODEL` interne (linéaire, logistique, k-means, PCA, ARIMA, contribution) | 312,50 $ par Tio lu (us-central1) | Slots de l'affectation `QUERY` |
| `CREATE MODEL` externe (arbres, DNN, AutoML) | 6,25 $ par Tio pour le prétraitement, plus le coût d'entraînement d'Agent Platform | Slots d'une affectation `ML_EXTERNAL`, non préemptibles |
| Évaluation, inspection, prédiction | Tarif des requêtes, 6,25 $ par Tio ; incluses dans le Tio gratuit mensuel | Slots |
| Modèles distants et fonctions `AI.*` | Octets lus, plus les jetons ou unités facturés par Agent Platform ou l'API appelée | Idem |

BigQuery ML n'est pas disponible dans une réservation Standard : Enterprise, Enterprise Plus ou la tarification à la demande. La factorisation de matrices exige une réservation. L'entraînement s'arrête à 50 itérations pour les modèles itératifs. Les coûts Agent Platform d'une requête se retrouvent dans Cloud Billing par le libellé `bigquery_job_id_prefix`.

## Pièges

- **Le réglage automatique d'ARIMA multiplie le volume facturé.** Avec `auto_arima`, chaque modèle candidat relit les données : jusqu'à 42 fois le volume du `SELECT` pour `AUTO_ARIMA_MAX_ORDER = 5`. Réduire l'ordre maximal ou agréger la série avant l'entraînement.
- **Évaluer sur les données d'entraînement.** `NO_SPLIT` ou une séparation aléatoire sur des données datées gonflent les métriques. Pour une prédiction dans le temps, `DATA_SPLIT_METHOD = 'SEQ'` avec une colonne de date.
- **Laisser une fonction `AI.*` échouer en silence.** Une ligne qui dépasse le quota renvoie `NULL`, et la requête réussit quand même. Vérifier la colonne `status`, ou fixer `max_error_ratio` sur `AI.IF`, `AI.CLASSIFY` et `AI.SCORE`.
- **Lancer un `AI.GENERATE` sur une table entière sans compter.** Chaque ligne est un appel au modèle, facturé aux jetons : tester sur un `LIMIT`, estimer avec `AI.COUNT_TOKENS`, et préférer une fonction gérée ou un modèle léger pour les gros volumes.
- **Utiliser l'endpoint `global` avec une contrainte de résidence.** Le traitement peut alors avoir lieu dans n'importe quelle région : fixer un endpoint `us` ou `eu` explicite.
- **Oublier les droits de la connexion.** Le compte de service d'une connexion de ressource cloud doit avoir Agent Platform User sur le projet du modèle distant, et l'agent de service Vertex AI (`roles/aiplatform.serviceAgent`) pour un modèle réglé ou une table d'objets.

## Alternatives en logiciel libre

L'entraînement et l'appel de modèles génératifs en SQL dans l'entrepôt n'ont pas d'équivalent libre répandu : l'ensemble se recompose à partir de briques séparées.

- **Apache Spark MLlib** (Apache 2.0) : apprentissage distribué au plus près des données d'un lac, avec des pipelines de transformation réappliqués à la prédiction comme la clause `TRANSFORM` ; en Python ou en Scala plutôt qu'en SQL.
- **scikit-learn** (BSD 3-Clause) et **XGBoost** (Apache 2.0) : les mêmes familles de modèles (linéaire, logistique, k-means, ACP, arbres boostés), sur des données extraites de l'entrepôt.
- **statsforecast** (Apache 2.0) : AutoARIMA, ETS et modèles saisonniers sur des milliers de séries en parallèle, l'équivalent d'`ARIMA_PLUS` ; **TimesFM 2.5** (Apache 2.0) pour la prévision sans entraînement d'`AI.FORECAST`.
- **ONNX Runtime** (MIT) : exécution des modèles exportés au format ONNX depuis PyTorch, scikit-learn ou XGBoost, l'équivalent des modèles importés.
- **PostgreSQL** avec **pgvector** (licence PostgreSQL) : embeddings stockés et recherche vectorielle en SQL, comme `VECTOR_SEARCH` ; les vecteurs se calculent hors de la base (voir [RAG](#rag)).
