---
title: "BigQuery ML : syntaxe"
id: sql-bigquery-ml
subgroup: BigQuery ML
type: syntax
---

Instructions et fonctions de BigQuery ML, du `CREATE MODEL` aux fonctions `AI.*`. Le choix du type de modèle, la tarification et les pièges sont dans [BigQuery ML](#bigquery-ml).

### Entraîner un modèle

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer ou remplacer un modèle | ``CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODELE` OPTIONS (MODEL_TYPE = 'LOGISTIC_REG', INPUT_LABEL_COLS = ['resilie']) AS SELECT * FROM DATASET.TABLE`` | Toutes les colonnes du `SELECT` autres que l'étiquette servent de variables ; aussi `CREATE MODEL IF NOT EXISTS` |
| Régression linéaire | `MODEL_TYPE = 'LINEAR_REG'` | Poids lisibles par `ML.WEIGHTS` |
| Classification binaire ou multiclasse | `MODEL_TYPE = 'LOGISTIC_REG', AUTO_CLASS_WEIGHTS = TRUE` | Pondère les classes rares |
| Arbres boostés (XGBoost) | `MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER'` ou `'BOOSTED_TREE_REGRESSOR'`, `MAX_TREE_DEPTH = 6, SUBSAMPLE = 0.8` | Aussi `RANDOM_FOREST_*`, `DNN_*` ; entraînés sur Agent Platform |
| AutoML tabulaire | `MODEL_TYPE = 'AUTOML_CLASSIFIER'` ou `'AUTOML_REGRESSOR'`, `BUDGET_HOURS = 1.0` | Recherche automatique du modèle, dans la limite du budget d'heures |
| Segmentation | `MODEL_TYPE = 'KMEANS', NUM_CLUSTERS = 5` | Sans étiquette ; `ML.PREDICT` renvoie `centroid_id`, `ML.CENTROIDS` les centres |
| Recommandation | `MODEL_TYPE = 'MATRIX_FACTORIZATION', FEEDBACK_TYPE = 'IMPLICIT', USER_COL = 'client', ITEM_COL = 'produit', RATING_COL = 'nb_vues'` | `EXPLICIT` pour des notes ; prédiction par `ML.RECOMMEND` ; réservation obligatoire |
| Série temporelle | `MODEL_TYPE = 'ARIMA_PLUS', TIME_SERIES_TIMESTAMP_COL = 'jour', TIME_SERIES_DATA_COL = 'ventes', TIME_SERIES_ID_COL = 'magasin', HORIZON = 90, HOLIDAY_REGION = 'FR'` | Une série par valeur de `TIME_SERIES_ID_COL` ; `ARIMA_PLUS_XREG` ajoute des covariables |
| Découpage entraînement / évaluation | `DATA_SPLIT_METHOD = 'RANDOM', DATA_SPLIT_EVAL_FRACTION = 0.2` | Défaut `AUTO_SPLIT` : tout en entraînement sous 500 lignes, 20 % d'évaluation jusqu'à 50 000, puis 10 000 lignes |
| Découpage chronologique | `DATA_SPLIT_METHOD = 'SEQ', DATA_SPLIT_COL = 'jour', DATA_SPLIT_EVAL_FRACTION = 0.2` | Les lignes les plus récentes servent à l'évaluation |
| Découpage fourni par une colonne | `DATA_SPLIT_METHOD = 'CUSTOM', DATA_SPLIT_COL = 'is_eval'` | Colonne `BOOL` : `TRUE` ou `NULL` en évaluation |
| Réglage d'hyperparamètres | `NUM_TRIALS = 20, MAX_PARALLEL_TRIALS = 4, L2_REG = HPARAM_RANGE(0, 10)` | Essais comparés par `ML.TRIAL_INFO` |
| Prétraitement enregistré avec le modèle | ``CREATE MODEL ... TRANSFORM (ML.STANDARD_SCALER(age) OVER () AS age_n, ML.QUANTILE_BUCKETIZE(panier, 10) OVER () AS panier_q, * EXCEPT (age, panier)) OPTIONS (...) AS SELECT ...`` | Réappliqué tel quel par `ML.EVALUATE` et `ML.PREDICT` |
| Enregistrer dans Model Registry | `OPTIONS (..., MODEL_REGISTRY = 'VERTEX_AI', VERTEX_AI_MODEL_ID = 'churn')` | Des modèles BigQuery qui partagent le même `VERTEX_AI_MODEL_ID` deviennent des versions d'un même modèle ; un `CREATE OR REPLACE` remplace sa version |
| Enregistrer un modèle existant | ``ALTER MODEL `PROJECT_ID.DATASET.MODELE` SET OPTIONS (vertex_ai_model_id = 'churn')`` | Même effet après coup ; l'identifiant ne se change plus ensuite |

### Évaluer, prédire, expliquer

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Métriques sur les données d'évaluation | ``SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.MODELE`)`` | Précision, rappel, F1, `roc_auc`, `log_loss` en classification ; erreurs et R² en régression |
| Métriques sur un autre jeu | ``ML.EVALUATE(MODEL `...`, (SELECT * FROM DATASET.TEST), STRUCT(0.6 AS threshold))`` | Seuil de décision personnalisé en classification binaire |
| Matrice de confusion, courbe ROC | ``ML.CONFUSION_MATRIX(MODEL `...`)``, ``ML.ROC_CURVE(MODEL `...`)`` | Pour les classifieurs |
| Suivre l'entraînement | ``SELECT * FROM ML.TRAINING_INFO(MODEL `...`)`` | Perte par itération, durée |
| Prédire | ``SELECT * FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.MODELE`, (SELECT * FROM DATASET.NOUVEAUX))`` | Colonnes d'entrée, plus `predicted_<étiquette>` et, en classification, `predicted_<étiquette>_probs` |
| Prédire avec un seuil | ``ML.PREDICT(MODEL `...`, TABLE DATASET.NOUVEAUX, STRUCT(0.7 AS threshold))`` | Défaut 0,5 en classification binaire |
| Expliquer chaque prédiction | ``ML.EXPLAIN_PREDICT(MODEL `...`, (SELECT ...), STRUCT(3 AS top_k_features))`` | Contribution des variables les plus influentes par ligne (5 par défaut) |
| Importance globale (explicabilité) | ``SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `...`)`` | Exige `ENABLE_GLOBAL_EXPLAIN = TRUE` à l'entraînement |
| Importance des variables d'un arbre | ``SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `...`)`` | Arbres boostés et forêts aléatoires : `importance_weight`, `importance_gain`, `importance_cover` par variable |
| Recommander | ``SELECT * FROM ML.RECOMMEND(MODEL `...`, (SELECT client FROM DATASET.CIBLES))`` | Note prédite pour chaque couple utilisateur-article |
| Prévoir | ``SELECT * FROM ML.FORECAST(MODEL `...`, STRUCT(30 AS horizon, 0.9 AS confidence_level))`` | Valeur prévue et intervalle de confiance ; horizon 3 par défaut |
| Détecter des anomalies dans une série | ``ML.DETECT_ANOMALIES(MODEL `...`, STRUCT(0.95 AS anomaly_prob_threshold))`` | Colonne `is_anomaly` ; sans table, porte sur l'historique d'entraînement (`DECOMPOSE_TIME_SERIES` laissé à `TRUE`) |
| Détecter des anomalies (k-means, PCA, autoencodeur) | ``ML.DETECT_ANOMALIES(MODEL `...`, STRUCT(0.02 AS contamination), TABLE DATASET.NOUVEAUX)`` | `contamination` : part d'anomalies attendue dans les données d'entraînement |
| Prévoir sans entraîner | `SELECT * FROM AI.FORECAST(TABLE DATASET.SERIES, data_col => 'ventes', timestamp_col => 'jour', id_cols => ['magasin'], horizon => 30)` | TimesFM 2.5 par défaut ; aussi `AI.DETECT_ANOMALIES` |
| Exporter le modèle | ``EXPORT MODEL `PROJECT_ID.DATASET.MODELE` OPTIONS (URI = 'gs://BUCKET/modeles/churn/')`` | TensorFlow SavedModel, ou *Booster* XGBoost pour les arbres ; `TRIAL_ID` pour un essai précis |

### Modèles distants et IA générative

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Modèle distant sur Gemini | ``CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.gemini` REMOTE WITH CONNECTION DEFAULT OPTIONS (ENDPOINT = 'gemini-3.5-flash')`` | Le compte de service de la connexion doit avoir Agent Platform User (`roles/aiplatform.user`) |
| Modèle distant sur un modèle d'embedding | `` ... REMOTE WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID` OPTIONS (ENDPOINT = 'text-embedding-005') `` | Entrée de `AI.GENERATE_EMBEDDING` |
| Modèle ouvert déployé par BigQuery | `... REMOTE WITH CONNECTION DEFAULT OPTIONS (HUGGING_FACE_MODEL_ID = 'ORG/MODELE')` | Ou `MODEL_GARDEN_MODEL_NAME` ; `ENDPOINT_IDLE_TTL` libère l'endpoint inactif |
| Modèle distant sur une API ML | `... OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_TRANSLATE_V3')` | Aussi `CLOUD_AI_VISION_V1`, `CLOUD_AI_NATURAL_LANGUAGE_V1`, `CLOUD_AI_DOCUMENT_V1`, `CLOUD_AI_SPEECH_TO_TEXT_V2` |
| Générer du texte ligne par ligne | `SELECT AI.GENERATE(CONCAT('Résume : ', texte), endpoint => 'gemini-3.5-flash').result FROM DATASET.AVIS` | `STRUCT` avec `result`, `full_response` et `status` ; sans `endpoint`, BigQuery choisit un Gemini stable ; sans connexion, identifiants de l'utilisateur |
| Sortie structurée | `AI.GENERATE(('Extrais produit et motif : ', texte), output_schema => 'produit STRING, motif STRING, urgent BOOL')` | `result` remplacé par les champs typés ; le *prompt* peut être un `STRUCT` de chaînes et d'`ObjectRef` |
| Régler le modèle | `model_params => JSON '{"generation_config": {"temperature": 0, "thinking_config": {"thinking_budget": 0}}}'` | Corps `generateContent` sauf `contents` ; limite les jetons de réflexion facturés |
| Générer sur une table via un modèle distant | ``SELECT * FROM AI.GENERATE_TEXT(MODEL `PROJECT_ID.DATASET.gemini`, (SELECT texte AS prompt FROM DATASET.AVIS), STRUCT(256 AS max_output_tokens, 0.2 AS temperature))`` | La colonne d'entrée doit s'appeler `prompt` ; sortie `result`, `statistics`, `status` |
| Extraire une table typée | ``AI.GENERATE_TABLE(MODEL `...`, (SELECT ... AS prompt ...), STRUCT('nom STRING, age INT64' AS output_schema))`` | Une colonne par champ du schéma ; modèles Gemini seulement |
| Filtrer en langage naturel | `SELECT * FROM DATASET.AVIS WHERE AI.IF(('Cet avis signale un défaut de livraison : ', texte))` | `BOOL` ; `NULL` en cas d'erreur de ligne |
| Classer dans des catégories | `AI.CLASSIFY(texte, categories => ['livraison', 'facturation', 'qualité', 'autre'])` | `STRING` ; `output_mode => 'multi'` rend un `ARRAY<STRING>` |
| Noter | `AI.SCORE(('Note de 1 à 10 la satisfaction du client : ', texte))` | `FLOAT64`, à trier ou filtrer |
| Résumer un groupe de lignes | `SELECT produit, AI.AGG(texte, 'Résume les plaintes récurrentes') FROM DATASET.AVIS GROUP BY produit` | Agrégat : un texte par groupe |
| Faire échouer au-delà d'un taux d'erreurs | `AI.IF(..., max_error_ratio => 0.05)` | Par défaut 1,0 : les lignes en erreur rendent `NULL` sans faire échouer la requête |
| Embedding d'une valeur | `SELECT AI.EMBED(texte, endpoint => 'text-embedding-005').result FROM DATASET.DOCS` | `ARRAY<FLOAT64>` ; `task_type => 'RETRIEVAL_DOCUMENT'` ou `'RETRIEVAL_QUERY'` |
| Embeddings d'une table | ``SELECT * FROM AI.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.emb`, (SELECT id, texte AS content FROM DATASET.DOCS), STRUCT(256 AS output_dimensionality))`` | La colonne d'entrée doit s'appeler `content` ; sortie `embedding`, `statistics`, `status` |

### Recherche vectorielle

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Rechercher les voisins d'un lot de requêtes | `SELECT query.id, base.id, distance FROM VECTOR_SEARCH(TABLE DATASET.DOCS_EMB, 'embedding', (SELECT id, embedding FROM DATASET.QUESTIONS), top_k => 5, distance_type => 'COSINE')` | Colonnes `query`, `base` (des `STRUCT`) et `distance` ; `top_k` 10 par défaut, distance `EUCLIDEAN` par défaut |
| Préfiltrer la base | `VECTOR_SEARCH((SELECT * FROM DATASET.DOCS_EMB WHERE langue = 'fr'), 'embedding', ...)` | Seuls `SELECT`, `FROM` et `WHERE` sont admis dans la requête de base |
| Créer un index vectoriel | `CREATE VECTOR INDEX idx ON DATASET.DOCS_EMB(embedding) STORING (langue) OPTIONS (index_type = 'IVF', distance_type = 'COSINE', ivf_options = '{"num_lists": 1000}')` | Recherche approchée ; `TREE_AH` (ScaNN) en alternative ; un index par table ; colonnes stockées pour préfiltrer |
| Régler le compromis rappel / vitesse | `options => '{"fraction_lists_to_search": 0.1}'` | Plus de listes lues : meilleur rappel, plus lent |
| Forcer la recherche exacte | `options => '{"use_brute_force": true}'` | Ignore l'index |
| Rechercher sur une colonne à embeddings autonomes | `AI.SEARCH(TABLE DATASET.DOCS, 'texte', 'délai de remboursement', mode => 'HYBRID', top_k => 5)` | Colonne source (et non la colonne vectorielle) d'une table à embeddings générés par `AI.EMBED` ; `mode` vaut `AUTO` par défaut, hybride si l'index vectoriel a des colonnes lexicales |
| Supprimer l'index | `DROP VECTOR INDEX idx ON DATASET.DOCS_EMB` | — |

> [!TIP]
> Les fonctions génératives s'appliquent à chaque ligne : tester sur un `LIMIT 10`, puis estimer le volume avec `AI.COUNT_TOKENS` avant de lancer la requête sur la table entière. Une ligne en erreur (quota, filtre de sécurité) rend `NULL` ou un `status` non vide sans faire échouer la requête.

Contexte : [BigQuery ML](#bigquery-ml), [RAG](#rag), [Entraîner et servir un modèle](#entrainer-et-servir), [MLOps](#mlops), [BigQuery : DDL](#bigquery-ddl).
