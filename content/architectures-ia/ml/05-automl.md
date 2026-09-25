---
title: "AutoML : entraîner sans code"
---

AutoML entraîne un modèle à partir d'un *dataset* étiqueté, sans code d'entraînement : [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) choisit le prétraitement, l'architecture et les hyperparamètres, puis assemble les meilleurs candidats. Il couvre deux familles de données : les **images** (classification, détection d'objets) et les **tableaux** (classification, régression, prévision). Le modèle obtenu entre dans Model Registry comme un modèle maison et se sert de la même façon (voir [Entraîner et servir](#entrainer-et-servir)). La documentation parle d'*AutoML on Gemini Enterprise Agent Platform* ; le SDK et l'API gardent les noms `aiplatform` et `AutoML*TrainingJob`. Pour situer AutoML parmi les autres approches, voir [Choisir une approche ML](#choisir-une-approche-ml).

## Ce que couvre AutoML

| Tâche | Données | Minimum | Budget d'entraînement | Service | Export hors Google Cloud | Statut (septembre 2026) |
|---|---|---|---|---|---|---|
| Classification d'images, une ou plusieurs étiquettes | JPEG, PNG, GIF, BMP, ICO dans Cloud Storage, listés en JSON Lines ou CSV | 10 images par étiquette ; 1 000 recommandées | 8 à 800 nœuds-heures, 192 par défaut | Endpoint en ligne, lots | Modèle *Edge* seulement : TF Lite, Edge TPU, conteneur TF SavedModel, Core ML, TensorFlow.js | Disponible |
| Détection d'objets | Mêmes formats, boîtes englobantes relatives à l'image | 10 images annotées par étiquette ; 1 000 annotations recommandées | 20 à 900 nœuds-heures, 216 par défaut | Endpoint en ligne, lots | Modèle Edge : TF Lite, conteneur, TensorFlow.js | Disponible ; modèles Edge [!DECONSEILLE] en maintenance : pour l'embarqué, un modèle open source |
| Classification, régression sur tableau | Table BigQuery ou CSV, 2 à 1 000 colonnes, 100 Go au plus | 1 000 lignes ; cible de 2 à 500 classes | 1 à 72 nœuds-heures | Endpoint en ligne, lots | Conteneur Docker (CPU x86 avec AVX) | Disponible |
| Prévision (séries temporelles) | Format long : cible, date, identifiant de série ; 3 à 100 colonnes, 3 000 pas par série | 1 000 lignes | Budget en nœuds-heures, comme le tabulaire | **Lots seulement** | Non | Disponible |
| Texte (classification, extraction d'entités, sentiment) | — | — | — | — | — | **Non disponible** : passer par le [réglage de Gemini](#choisir-un-modele) |
| Vidéo | — | — | — | — | — | **Non disponible** : passer par le réglage de Gemini sur vidéo |

Sources : [aperçu d'AutoML](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/training/automl-training-overview) et [dépréciations](https://docs.cloud.google.com/vertex-ai/docs/deprecations), consultés en septembre 2026.

- **Pour le tabulaire, deux autres chemins.** Les **Tabular Workflows** sont les mêmes algorithmes sous forme de pipelines [Agent Platform Pipelines](#mlops), dont chaque étape se règle : découpage, ingénierie des variables, recherche d'architecture, ensemble, distillation. *End-to-End AutoML* (classification, régression) est en GA et accepte plusieurs To et 1 000 colonnes ; *Forecasting* [!PREVERSION] apporte la prévision en ligne. Et BigQuery ML entraîne le même AutoML en SQL (`AUTOML_CLASSIFIER`, `AUTOML_REGRESSOR`, voir [BigQuery ML](#bigquery-ml)).
- **Modèles *Cloud* ou *Edge*.** Un modèle d'image *Cloud* (`CLOUD`, `CLOUD_1`, `CLOUD_HIGH_ACCURACY_1`, `CLOUD_LOW_LATENCY_1`) se sert seulement sur Agent Platform. Un modèle *Edge* (`MOBILE_TF_LOW_LATENCY_1`, `MOBILE_TF_VERSATILE_1`, `MOBILE_TF_HIGH_ACCURACY_1`) s'exporte vers un appareil, un navigateur ou un conteneur, mais ne se sert pas sur Agent Platform ; son budget va de 1 à 100 nœuds-heures. La détection d'objets Edge ne reçoit que les correctifs critiques : Google conseille de passer à un modèle open source.

## Préparer le dataset

Un *dataset* Agent Platform référence les données. Pour une image, un fichier d'import (JSON Lines ou CSV) donne l'URI Cloud Storage, l'étiquette ou les boîtes, et éventuellement le jeu visé (`ml_use`). Pour un tableau, le dataset pointe vers une table BigQuery ou des CSV, sans copie : un instantané est pris au lancement de l'entraînement.

- **Images.** Au plus 30 Mo par image à l'entraînement, 1,5 Mo à la prédiction, envoyée en base64. Viser environ 1 000 exemples par étiquette, et au plus 100 fois plus d'images pour l'étiquette la plus fréquente que pour la plus rare. Ajouter une étiquette `None_of_the_above` avec des images hors catégories. En détection, le petit côté d'une image est ramené à 1 024 pixels, et les boîtes devenues plus petites que 8 × 8 pixels sont supprimées. Les images doivent ressembler à celles de la production : mêmes angles, même flou, même éclairage. L'agent de service Agent Platform doit lire le bucket (Storage Object Viewer).
- **Tableau.** Une ligne par exemple (format large) pour la classification et la régression, une ligne par série et par instant (format long) pour la prévision, à intervalle constant. Noms de colonnes alphanumériques, sans `_` initial. Une **colonne de pondération** (0 à 10 000, 0 exclut la ligne) donne plus de poids à une classe rare ou à des clients importants ; elle ne s'applique pas au jeu de test.

Le **découpage** en entraînement, validation et test se choisit au lancement :

| Méthode | Principe | Quand |
|---|---|---|
| Aléatoire (défaut) | 80 / 10 / 10, aléatoire mais déterministe : mêmes données, même découpage | Données stables dans le temps, classes équilibrées |
| Manuel | Colonne `TRAIN` / `VALIDATE` / `TEST` / `UNASSIGNED` (tableau), étiquette `ml_use` (images) | Tester sur des magasins, des clients ou des appareils absents de l'entraînement |
| Filtre (images) | Une expression de filtre par jeu | Découpage selon des étiquettes de données |
| Chronologique (tableau) | Colonne de date : les lignes anciennes entraînent, les récentes testent | Toute donnée datée ; au moins une vingtaine de dates distinctes |
| Prévision | Chronologique par défaut ; les lignes dont l'horizon chevauche deux jeux sont écartées | Imposé par la nature de la tâche |

AutoML ne fait **pas d'échantillonnage stratifié** : avec une classe rare, le jeu de test peut n'en contenir presque aucun exemple. Le découpage manuel règle ce cas.

## Entraîner : budget, objectif, arrêt anticipé

- **Budget en nœuds-heures.** Exprimé en milli-nœuds-heures dans l'API (`budget_milli_node_hours=1000` pour un nœud-heure). C'est un plafond de coût, pas une durée : 192 nœuds-heures correspondent à un jour sur 8 nœuds. Un budget jugé insuffisant pour le volume de données fait échouer le lancement. En BigQuery ML, `BUDGET_HOURS` va de 1 à 72.
- **Arrêt anticipé.** Actif par défaut : l'entraînement s'arrête quand les essais n'améliorent plus le modèle, et le coût reste sous le budget. `disable_early_stopping=True` consomme tout le budget.
- **Objectif d'optimisation** (tableau). Classification binaire : `maximize-au-roc` par défaut, `maximize-au-prc` quand la classe positive est rare, `minimize-log-loss` pour des probabilités bien calibrées, `maximize-precision-at-recall` ou `maximize-recall-at-precision` avec une valeur cible. Multiclasse : `minimize-log-loss` seulement. Régression : `minimize-rmse` par défaut, `minimize-mae` pour atténuer les valeurs extrêmes, `minimize-rmsle` pour une erreur relative. Prévision : RMSE par défaut, MAE, RMSLE, RMSPE, `minimize-wape-mae`, ou `minimize-quantile-loss` avec des quantiles pour mesurer l'incertitude.
- **Ce qui est entraîné** (tableau). Réseaux de neurones et arbres boostés sont essayés sur le jeu d'entraînement et comparés sur la validation ; un modèle d'évaluation, entraîné sur entraînement et validation, est mesuré sur le test ; le modèle servi est réentraîné sur les trois jeux. En prévision, la méthode se choisit : TiDE, TFT, AutoML (L2L) ou Seq2Seq+. Les colonnes connues à l'avance (prix planifié, jour férié) se déclarent `available_at_forecast`, les autres `unavailable_at_forecast`.
- **Durée.** Plusieurs heures dans la plupart des cas ; un courriel signale la fin. Pour une prévision sur 12 millions de lignes à horizon 6, la documentation cite 3 à 6 heures.

```python
from google.cloud import aiplatform

aiplatform.init(project="PROJECT_ID", location="REGION")

ds = aiplatform.TabularDataset.create(
    display_name="clients", bq_source="bq://PROJECT_ID.DATASET.clients_historique")

job = aiplatform.AutoMLTabularTrainingJob(
    display_name="churn-automl",
    optimization_prediction_type="classification",
    optimization_objective="maximize-au-prc",          # résiliation : classe rare
    column_specs={"anciennete_jours": "numeric", "panier_moyen": "numeric",
                  "offre": "categorical", "region": "categorical"},  # client_id exclu
)
model = job.run(
    dataset=ds, target_column="resilie",
    timestamp_split_column_name="date_observation",    # RFC 3339 ; test = lignes récentes
    training_fraction_split=0.8, validation_fraction_split=0.1, test_fraction_split=0.1,
    budget_milli_node_hours=4000,                       # 4 nœuds-heures au plus
    model_display_name="churn",
)

ev = model.list_model_evaluations()[0]
print(ev.metrics["auPrc"], ev.metrics["confusionMatrix"])

model.batch_predict(
    job_display_name="churn-lot",
    bigquery_source="bq://PROJECT_ID.DATASET.clients_actifs",
    bigquery_destination_prefix="bq://PROJECT_ID.DATASET",
)
```

Vérifié avec `google-cloud-aiplatform` 1.165. Sans `column_specs`, le SDK déclare **toutes** les colonnes en `auto`, identifiants et dates compris. Les images passent par `aiplatform.ImageDataset.create(..., import_schema_uri=aiplatform.schema.dataset.ioformat.image.single_label_classification)`, puis `AutoMLImageTrainingJob(prediction_type="classification" | "object_detection", model_type=...)`, et la prévision par `TimeSeriesDataset` et `AutoMLForecastingTrainingJob`. Les classes `AutoMLTextTrainingJob` et `AutoMLVideoTrainingJob` existent encore dans le SDK, mais le service ne les accepte plus.

## Évaluer

Les métriques sont calculées sur le jeu de test et visibles dans l'onglet *Evaluate* du modèle, globalement et par étiquette (*evaluation slices*).

| Tâche | Métriques | À regarder aussi |
|---|---|---|
| Classification d'images | AUC PR (précision moyenne), *log loss*, précision et rappel par seuil de confiance | Matrice de confusion ; images vraies positives, fausses positives et fausses négatives par étiquette, avec un badge *Outlier* pour celles éloignées de l'entraînement (*preview*) |
| Détection d'objets | Précision moyenne (mAP) des boîtes, à un seuil d'IoU ; précision, rappel, F1 par seuil de confiance | Métriques par étiquette |
| Classification sur tableau | AUC PR, AUC ROC, *log loss*, F1, précision et rappel par seuil | Matrice de confusion, importance des variables |
| Régression | MAE, MAPE, RMSE, RMSLE, R² | Importance des variables |
| Prévision | MAE, MAPE (absente si la cible contient des zéros), RMSE, RMSLE, R² ; avec des quantiles, *pinball loss* et quantile observé | Importance des variables |

- **Seuil de décision.** Le modèle renvoie des scores ; le seuil qui transforme un score en décision se choisit sur la courbe précision-rappel, d'après le coût d'un faux positif et d'un faux négatif.
- **Importance des variables.** En pourcentage par colonne, sur le modèle entier. Une colonne qui domine (un identifiant, une date, une variable connue seulement après coup) signale une fuite d'étiquette. Les attributions **par prédiction** (`explain`, valeurs de Shapley) passent par Vertex Explainable AI [!DECONSEILLE], déprécié et arrêté le 16 mars 2027 : la documentation renvoie vers SHAP ou LIME.
- **Exporter les prédictions du test.** `export_evaluated_data_items=True` écrit dans BigQuery chaque ligne de test avec sa prédiction, pour une analyse d'erreurs par segment.
- **Comparer avec une référence.** Un modèle AutoML ne vaut que comparé à une référence simple sur le même jeu de test : régression logistique ou arbres boostés en [BigQuery ML](#bigquery-ml), `ARIMA_PLUS` pour une prévision.

## Déployer et exporter

- **En ligne.** Le modèle se déploie sur un endpoint public partagé ; une image se déploie par **nombre de nœuds**, un modèle tabulaire par type de machine (`n1-standard-2` par défaut) et nombre de nœuds, avec autoscaling. Les nœuds sont facturés tant que le modèle est déployé, même sans requête. Détails des endpoints dans [Entraîner et servir](#entrainer-et-servir).
- **Par lots.** `batch_predict` sans déploiement : JSON Lines d'URI pour les images, table BigQuery ou CSV pour le tableau. Seul mode possible pour la prévision AutoML.
- **Export tabulaire.** Classification et régression seulement : le modèle s'exporte dans Cloud Storage et se sert dans un conteneur Docker fourni par Google, sur un serveur x86 avec AVX, ailleurs que sur Google Cloud. Pas d'explications sur un modèle exporté.
- **Export Edge.** `model.export_model(export_format_id="tflite", artifact_destination="gs://BUCKET/export/")` ; autres formats : `tf-saved-model` et `tf-js`, plus `edgetpu-tflite` et `core-ml` pour la classification seulement. L'exécution se fait alors sur l'appareil, hors d'Agent Platform.

## Coût

| Poste | Images | Tableau (classification, régression) | Prévision |
|---|---|---|---|
| Entraînement | 3,465 $ par nœud-heure ; 18 $ pour un modèle Edge | 21,252 $ par nœud-heure | 21,252 $ par nœud-heure |
| Endpoint en ligne | 1,375 $ par nœud-heure (classification), 2,002 $ (détection) | Tarif des modèles maison, selon la machine | Non disponible |
| Lots | 2,222 $ par nœud-heure | Tarif des modèles maison | 0,20 $ pour 1 000 points prévus (premier million du mois), dégressif au-delà |

Tarifs de base publiés par la [page de tarification](https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing), consultée en septembre 2026. Un point prévu est un pas de l'horizon pour une série : un horizon de 7 jours sur 1 000 séries fait 7 000 points. Ordres de grandeur :

- Classification d'images au budget par défaut : au plus 192 × 3,465 ≈ 665 $ ; un endpoint d'un nœud gardé un mois, environ 1 000 $.
- Tabulaire : 21 $ pour un nœud-heure, 1 530 $ au budget maximal de 72.
- Un entraînement qui échoue n'est pas facturé ; un entraînement annulé l'est.

## AutoML ou autre chose

| Situation | Choix | Pourquoi |
|---|---|---|
| Données dans BigQuery, équipe SQL, besoin de référence rapide | [BigQuery ML](#bigquery-ml), arbres boostés d'abord | Aucune donnée à déplacer, coût à la requête ; `AUTOML_CLASSIFIER` si la référence ne suffit pas |
| [!PREVERSION] Prédiction tabulaire ponctuelle, peu de variables, sans entraînement | `AI.PREDICT` (TabFM) | Rien à entraîner ni à servir ; 50 variables et 10 classes au plus |
| Images étiquetées, équipe sans spécialiste | AutoML image | Meilleur rapport effort-qualité, service géré |
| Image lue ou décrite, pas de catégorie maison | Gemini ou [Vision AI](#vision-ai) | Aucun entraînement ; voir [Choisir un modèle](#choisir-un-modele) |
| Texte ou vidéo à classer | Gemini par *prompt*, puis réglage supervisé | AutoML ne couvre plus ces données |
| Pipeline tabulaire à contrôler étape par étape, données de plusieurs To | Tabular Workflow for End-to-End AutoML | Même moteur, étapes réglables, distillation |
| Architecture, perte ou prétraitement particuliers, modèle portable | [Entraînement personnalisé](#entrainer-et-servir) | Contrôle total ; AutoML ne livre pas de code ni de modèle réutilisable ailleurs, hors exports ci-dessus |
| Détection embarquée sur appareil | Modèle open source (YOLO, famille EfficientDet) entraîné en job personnalisé | La détection Edge d'AutoML est en maintenance |

## Pièges

- **Laisser le SDK choisir les colonnes.** Sans `column_specs`, un identifiant, une date d'extraction ou une variable calculée après l'événement entrent comme variables : métriques excellentes, modèle inutilisable. Lister les colonnes et relire l'importance des variables.
- **Découpage aléatoire sur des données datées.** Le test contient alors des lignes contemporaines de l'entraînement. Utiliser le découpage chronologique ou manuel.
- **Classe rare sans découpage manuel.** Pas de stratification : quelques exemples positifs peuvent manquer au test, et les métriques ne veulent plus rien dire.
- **Oublier l'endpoint.** Un nœud d'image déployé coûte environ 1 000 $ par mois sans une seule requête. Préférer les lots pour des scores quotidiens, et `endpoint.undeploy_all()` en fin d'essai.
- **Viser un modèle Edge de détection.** Il est en maintenance ; pour un usage embarqué neuf, entraîner un modèle ouvert.
- **Dépendre des attributions par prédiction.** Vertex Explainable AI s'arrête le 16 mars 2027 ; prévoir SHAP côté application si l'explication de chaque décision est exigée.
- **Chercher le modèle BigQuery ML dans la console AutoML.** Un modèle `AUTOML_*` entraîné depuis BigQuery n'y apparaît pas et ne sert ni en ligne ni par lots côté AutoML : les prédictions passent par `ML.PREDICT`.

## Alternatives en logiciel libre

- **AutoGluon** (Apache 2.0, actif) : empilement de modèles automatique sur tableau, images, texte et séries temporelles ; tourne partout, y compris dans un job personnalisé d'Agent Platform.
- **FLAML** (MIT, Microsoft, actif) : recherche d'hyperparamètres économe sous budget de temps, sur LightGBM, XGBoost et scikit-learn ; léger, s'intègre à un code existant plutôt que de le remplacer.
- **H2O-3 AutoML** (Apache 2.0, actif) : AutoML tabulaire distribué sur la JVM, avec classement des modèles et ensembles ; accès en Python, R ou interface web.
- **mljar-supervised** (MIT, actif) : AutoML tabulaire avec rapports d'explication générés pour chaque modèle.
- **auto-sklearn** (BSD 3-Clause) : optimisation bayésienne sur scikit-learn, Linux uniquement ; **dormant**, sans version depuis 0.15.0 (février 2023) ni commit de fond depuis avril 2023.
- **AutoKeras** (Apache 2.0) : recherche d'architecture de réseaux sur images et texte, au-dessus de Keras ; l'équivalent le plus proche d'AutoML image.
- **statsforecast** (Apache 2.0) : AutoARIMA, ETS et Theta sur des milliers de séries, la référence rapide avant une prévision AutoML.
