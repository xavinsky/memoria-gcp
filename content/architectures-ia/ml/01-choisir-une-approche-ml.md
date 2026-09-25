---
title: Choisir une approche ML
---

Une approche de *machine learning* se choisit d'abord sur la **nature de la tâche**. Une tâche de perception standard (lire un texte, transcrire, traduire, étiqueter une image) relève d'une API préentraînée. Une question ouverte sur du texte, une image ou un document relève d'un modèle de fondation. Une prédiction sur ses propres données demande un modèle entraîné sur ces données. Viennent ensuite **qui construit** (analystes SQL, équipe sans spécialiste, *data scientists*), **où sont les données** et le **mode de service** attendu.

![Arbre de décision : de la tâche à l'approche ML](../../svg/choix-approche-ml.svg)

## Matrice de choix

| Approche | Données d'entraînement | Compétences | Service | Coût | Contrôle |
|---|---|---|---|---|---|
| **API ML préentraînée** : [Vision AI](#vision-ai), [Speech-to-Text](#speech-to-text), [Translation AI](#translation-ai), [Natural Language AI](#natural-language-ai), [Document AI](#document-ai) ; mise en œuvre dans APIs & SDK ([parole](#speech-to-text-tts), [image et vidéo](#vision-video), [langue](#natural-language-translation), [documents](#document-ai-code)) | Aucune ; adaptation légère (*PhraseSet*, glossaire, schéma du Custom Extractor) | Appel REST ou bibliothèque cliente ; aussi en SQL depuis BigQuery | Synchrone, ou lots en opération longue | À l'unité : image, page, minute, caractère | Sorties fixes : catégories, boîtes, scores, horodatages |
| **Gemini par *prompt*** (voir [Choisir un modèle](#choisir-un-modele)) | Aucune ; quelques exemples dans le *prompt* | *Prompt*, SDK `google-genai`, ou SQL (`AI.GENERATE`) | Appel à l'API, aucune machine à réserver | Aux jetons d'entrée et de sortie | Consignes, schéma de sortie, ancrage ; poids non modifiables |
| **Réglage supervisé de Gemini** (voir [Régler un modèle Gemini](#regler-gemini)) | Exemples étiquetés entrée → sortie, 100 ou plus selon la documentation | Préparation d'un jeu JSONL ou d'une table, job de réglage | Appel au modèle réglé, comme un modèle géré | Job de réglage, puis inférence aux jetons | Comportement, format et style figés sur la tâche |
| **[BigQuery ML](#bigquery-ml)** | Table étiquetée dans BigQuery | SQL | Prédiction par lots en SQL ; en ligne après enregistrement dans Model Registry | Octets lus (à la demande) ou slots Enterprise | Type de modèle, hyperparamètres, clause `TRANSFORM` |
| **[AutoML](#automl)** ([Agent Platform](#gemini-enterprise-agent-platform)) | *Dataset* étiqueté : images (classification, détection d'objets) ou tableau (classification, régression, prévision) | Console ou SDK, sans code d'entraînement | *Endpoint* en ligne ou inférence par lots | Calcul de l'entraînement, puis nœuds de l'endpoint | Faible : le service choisit l'architecture et les hyperparamètres |
| **Entraînement personnalisé** (voir [Entraîner et servir](#entrainer-et-servir)) | Toutes données, tous volumes | Python : PyTorch, TensorFlow, scikit-learn, XGBoost ; conteneurs | Endpoint, lots, ou service sur GKE ou Cloud Run | Machines et accélérateurs à la durée, plus l'endpoint | Total : architecture, fonction de perte, code de service |

- **Deux chemins pour Gemini.** Depuis une application, le SDK `google-genai` (voir [Appeler Gemini](#appeler-gemini)). Depuis l'entrepôt, les fonctions `AI.GENERATE`, `AI.CLASSIFY` ou `AI.IF` de BigQuery appliquent le même modèle à chaque ligne d'une table, sans pipeline.
- **Les API aussi s'appellent en SQL.** Un modèle distant BigQuery rend Vision, Translation, Natural Language, Document AI et Speech-to-Text appelables par `ML.ANNOTATE_IMAGE`, `ML.TRANSLATE`, `ML.UNDERSTAND_TEXT`, `ML.PROCESS_DOCUMENT` et `ML.TRANSCRIBE`. Le choix de l'API ne dépend donc pas de l'endroit où sont les données.
- **Tabulaire sans entraînement.** `AI.PREDICT` [!PREVERSION] de BigQuery fait de la régression ou de la classification avec **TabFM**, un modèle de fondation pour données tabulaires : la requête reçoit une table d'exemples et une table à prédire, sans `CREATE MODEL`. Il accepte jusqu'à 50 variables et 10 classes.

## Questions qui départagent

- **API dédiée ou Gemini ?** L'API gagne pour une sortie **structurée et stable** (coordonnées, scores, horodatage au mot), un tarif à l'unité prévisible, une faible latence et des volumes de plusieurs millions d'éléments. Gemini gagne dès que la question est ouverte, que la catégorie est maison ou que le format de sortie change d'un projet à l'autre. Chaque fiche d'API détaille la frontière dans sa section « À éviter ».
- ***Prompt* ou réglage ?** Commencer par le *prompt*, avec un jeu d'évaluation (voir [Évaluer et sécuriser](#evaluer-et-securiser)). Le réglage supervisé se justifie quand des erreurs récurrentes résistent au *prompt*, qu'un format ou un style doit être tenu sans faille, ou que de longues consignes et des exemples répétés à chaque appel coûtent cher en jetons. La documentation recommande d'analyser les erreurs avant d'ajouter des exemples : la qualité des étiquettes compte plus que leur nombre.
- **Réglage ou RAG ?** Le réglage apprend un comportement, pas des faits. Des connaissances qui changent (catalogue, procédures, documentation interne) se branchent au moment de l'appel par [RAG](#rag) ; un modèle réglé sur elles serait périmé à la prochaine mise à jour.
- **BigQuery ML ou Agent Platform ?** BigQuery ML quand les données sont dans BigQuery, que l'équipe écrit du SQL et que les prédictions se consomment par lots, dans des tables. Agent Platform quand il faut une prédiction en ligne à faible latence, une architecture sur mesure, des GPU ou un cycle MLOps complet (voir [MLOps](#mlops)). Les deux se rejoignent : un modèle BigQuery ML s'enregistre dans Model Registry et se déploie sur un endpoint, sauf les modèles XGBoost importés et les modèles ARIMA_PLUS.
- **AutoML ou code ?** AutoML donne vite une première référence sur des images ou un tableau, sans spécialiste. Le code s'impose pour une architecture ou une fonction de perte particulière, un prétraitement complexe, un modèle portable hors de Google Cloud, ou une donnée qu'AutoML ne couvre pas. Pour du texte, le *prompt* ou le réglage de Gemini tiennent ce rôle.
- **Quel volume d'étiquettes ?** Aucune : API ou *prompt*. Quelques dizaines : exemples dans le *prompt*, traduction adaptative. Une centaine ou plus : réglage de Gemini. Des milliers de lignes dans une table : BigQuery ML ou AutoML. Au-delà, ou pour des données non structurées massives : entraînement personnalisé.

## Préparer les caractéristiques

Pour un modèle entraîné sur ses propres données, le choix des caractéristiques (*features*) pèse souvent plus que celui du modèle. Il part de la connaissance métier : quelle information un expert regarderait pour trancher, et sous quelle forme le modèle peut l'exploiter.

| Technique | Ce qu'elle fait | Exemple | Fonction BigQuery ML |
|---|---|---|---|
| **Découpage en intervalles** (*bucketing*) | Remplace une valeur continue par sa plage, quand la relation avec l'étiquette n'est pas linéaire | Âge en tranches, heure en créneaux | `ML.BUCKETIZE`, `ML.QUANTILE_BUCKETIZE` |
| **Croisement** (*feature cross*) | Combine deux catégories ou intervalles en une seule caractéristique, pour qu'un modèle linéaire apprenne leur interaction | Jour de la semaine × créneau horaire | `ML.FEATURE_CROSS` |
| **Mise à l'échelle** (normalisation) | Ramène chaque nombre à une plage comparable (score Z, min-max) ; l'entraînement converge plus vite | Montant, distance | `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER` |
| **Encodage des catégories** | Transforme une chaîne en vecteur : *one-hot* pour un vocabulaire fini, hachage vers un nombre fixe de compartiments pour un vocabulaire très large | Pays, code produit | `ML.ONE_HOT_ENCODER`, `ML.HASH_BUCKETIZE` |
| **Enrichissement externe** | Joint des informations que la table ne contient pas | Météo, jours fériés, données par zone géographique | Jointure SQL avant `CREATE MODEL` |

- **Où les calculer.** Dans BigQuery ML, la clause `TRANSFORM` enregistre ces fonctions avec le modèle et les réapplique à la prédiction (voir [BigQuery ML](#bigquery-ml) et la [syntaxe](#sql-bigquery-ml)). Pour un modèle servi en ligne, calculer les caractéristiques une fois dans BigQuery et les servir par Feature Store évite deux calculs qui divergent (voir [MLOps](#mlops)).
- **Caractéristiques datées.** `ML.FEATURES_AT_TIME` lit chaque caractéristique telle qu'elle était à une date de coupure : un exemple d'entraînement ne voit pas de valeur postérieure à l'événement qu'il doit prédire.

## Données ou réglage ?

Un modèle qui prédit mal a deux familles de causes : des données d'entraînement qui ne représentent pas le problème métier, qu'aucun réglage ne corrige, ou un modèle mal réglé sur des données correctes. La comparaison de la perte (*loss*) sur les données d'entraînement et sur les données de validation départage ; pour un modèle BigQuery ML, `ML.TRAINING_INFO` donne les deux à chaque itération (`loss`, `eval_loss`).

| Symptôme | Diagnostic | Ce qui corrige |
|---|---|---|
| Mauvais sur l'entraînement comme sur la validation | **Sous-apprentissage** (*underfitting*) : le modèle ne capte pas la structure des données | Caractéristiques plus informatives, modèle plus riche, plus d'*epochs* ou un taux d'apprentissage plus élevé, régularisation plus faible |
| Bon sur l'entraînement ; la perte de validation remonte après un certain nombre d'itérations | **Surapprentissage** (*overfitting*) : le modèle mémorise le jeu d'entraînement | Régularisation plus forte, arrêt anticipé (*early stopping*), moins de caractéristiques, plus d'exemples variés |
| Perte qui oscille ou explose | Taux d'apprentissage trop élevé, valeurs aberrantes ou `NaN` dans les données | Baisser le taux d'apprentissage, valider les données contre un schéma |
| Bon sur l'entraînement et la validation, mauvais en production | Données non représentatives : fuite d'étiquette, biais d'échantillonnage, ou [biais entraînement-service](#mlops) | Refaire le jeu de données ; aucun hyperparamètre n'y change rien |

- **Les leviers de réglage.** La régularisation L2 pénalise les grands poids et les rapproche de zéro ; la régularisation L1 ramène à exactement zéro le poids des caractéristiques peu utiles, ce qui les retire du modèle. L'arrêt anticipé interrompt l'entraînement quand la perte de validation cesse de baisser. Une *epoch* est un passage complet sur le jeu d'entraînement ; le taux d'apprentissage règle l'ampleur de chaque correction des poids : trop bas, l'entraînement traîne, trop haut, il ne converge pas.
- **Dans BigQuery ML** (modèles linéaires et logistiques) : `L1_REG`, `L2_REG`, `EARLY_STOP` (actif par défaut : arrêt dès qu'une itération améliore la perte de moins de `MIN_REL_PROGRESS`, 1 %), `MAX_ITERATIONS` (passages complets sur les données, 20 par défaut) et `LEARN_RATE`. Le réglage automatique d'hyperparamètres les explore (voir la [syntaxe](#sql-bigquery-ml)).
- **Fuite d'étiquette** (*label leakage*) : une caractéristique n'est connue qu'après le résultat, ou en est un substitut — par exemple un indicateur « a parlé à un conseiller » renseigné seulement après l'achat qu'on veut prédire. La validation contient la même fuite, donc ses métriques sont excellentes ; en production, la caractéristique manque au moment de prédire.
- **Biais d'échantillonnage** : les exemples ne sont pas tirés au hasard dans la population visée (une seule région, une saison, les seuls clients qui ont répondu à une enquête). Le jeu de validation, découpé dans les mêmes données, hérite du biais : il ne peut pas le révéler. Seul un échantillon tiré de la population réelle, ou la surveillance en production, le montre.

## Pièges

- **Entraîner un modèle pour ce qu'une API fait déjà.** Un classifieur d'images maison pour de l'OCR, une transcription entraînée sur quelques heures d'audio : l'API préentraînée fait mieux, sans données ni endpoint. Le vocabulaire métier se règle par adaptation (*PhraseSet*, glossaire).
- **Sortir les données de BigQuery pour une régression.** Exporter une table vers un notebook pour entraîner un modèle linéaire ou un arbre boosté ajoute un transfert, une copie à gouverner et un job à exploiter, là où un `CREATE MODEL` suffit.
- **Oublier l'endpoint.** Un modèle AutoML ou personnalisé déployé en ligne se facture tant que l'endpoint existe, même sans trafic. Pour des prédictions périodiques, l'inférence par lots ne réserve aucune machine.
- **Compter sur BigQuery ML en édition Standard.** BigQuery ML n'est pas disponible dans une réservation Standard ; il faut la tarification à la demande ou une réservation Enterprise ou Enterprise Plus.
- **Comparer des approches sans jeu d'évaluation.** Un *prompt*, un modèle réglé et un modèle AutoML ne se départagent que sur le même jeu de test, avec une métrique fixée avant l'essai.
- **Payer au jeton une classification de masse.** Des millions de textes courts à classer dans une taxonomie fixe coûtent beaucoup moins cher avec Natural Language AI, ou avec un modèle BigQuery ML entraîné sur des *embeddings*, qu'avec un appel à Gemini par ligne ; pour `AI.CLASSIFY`, le mode optimisé (en *preview*) entraîne un modèle distillé sur un échantillon et évite l'appel au modèle pour la plupart des lignes.

## Alternatives en logiciel libre

Chaque approche de la matrice a son équivalent libre ; la différence tient surtout à l'exploitation, puisque le service, les machines et les mises à jour reviennent à l'équipe.

- **Transformers** (Apache 2.0) et les modèles préentraînés du Hub Hugging Face : l'équivalent des API ML, modèle à choisir et à servir soi-même ; les fiches des API ([Vision AI](#vision-ai), [Speech-to-Text](#speech-to-text)…) citent les modèles libres par tâche.
- Modèles génératifs aux poids libres (Gemma 4, Qwen3, Mistral) à la place de Gemini, par *prompt* ou par réglage LoRA : voir [Choisir un modèle](#choisir-un-modele).
- **scikit-learn** (BSD 3-Clause), **XGBoost** (Apache 2.0), **LightGBM** (MIT) : les modèles tabulaires de BigQuery ML, en Python sur des données extraites de l'entrepôt.
- **AutoGluon** (Apache 2.0) et **FLAML** (MIT) : AutoML, choix du modèle et des hyperparamètres automatiques ; AutoGluon traite aussi images, texte et séries temporelles.
- **PyTorch** (BSD 3-Clause) : le cadre de l'entraînement personnalisé (voir [Entraîner et servir](#entrainer-et-servir)).
- **TimesFM 2.5** (Apache 2.0) : le modèle de fondation de Google pour séries temporelles, qui prévoit sans entraînement. TimesFM 3.0 est sous licence non commerciale, et les poids de TabPFN, modèle de fondation tabulaire, sous licence propre : ni l'un ni l'autre n'est libre.
