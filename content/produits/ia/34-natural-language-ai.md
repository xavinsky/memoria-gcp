---
title: Natural Language AI
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 162, y: 16, w: 590, h: 268}
  nodes:
    src: {label: Avis clients, sub: "formulaires, chat", external: true, x: 8, y: 120, w: 126}
    ps: {label: Pub/Sub, sub: "flux d'avis", icon: categories/data-analytics, x: 184, y: 114, w: 160}
    nl: {label: Natural Language API, sub: "sentiment, entités", icon: categories/ai-machine-learning, focus: true, x: 378, y: 26, w: 230, h: 62}
    run: {label: Cloud Run, sub: "abonnement push", icon: produits/cloud-run, x: 378, y: 114, w: 180}
    bq: {label: BigQuery, sub: "table d'analyses", icon: produits/bigquery, x: 378, y: 210, w: 180}
    lk: {label: Looker, sub: "tableaux de bord", icon: produits/looker, x: 592, y: 210, w: 154}
  flows:
    - {from: src, to: ps, text: "Chaque avis déposé est publié dans un sujet Pub/Sub"}
    - {from: ps, to: run, text: "Abonnement push : Pub/Sub appelle le service à chaque message"}
    - {from: run, to: nl, text: "annotateText renvoie sentiment, entités et modération en une seule requête"}
    - {from: run, to: bq, text: "Le texte et les scores sont insérés dans la table d'analyses"}
    - {from: bq, to: lk, text: "Tableaux de bord et requêtes SQL des équipes produit"}
deprecie: "Un modèle Gemini couvre les mêmes tâches avec plus de souplesse. L'API garde un intérêt sur de gros volumes de textes courts, où le coût par caractère l'emporte."
docs:
  Page produit: https://cloud.google.com/natural-language
  Documentation: https://docs.cloud.google.com/natural-language/docs
  Concepts de l'API: https://docs.cloud.google.com/natural-language/docs/basics
  API REST: https://docs.cloud.google.com/natural-language/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/ml/language
  Bibliothèques clientes: https://docs.cloud.google.com/natural-language/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/language/latest
  Catégories de classification: https://docs.cloud.google.com/natural-language/docs/categories
  Langues prises en charge: https://docs.cloud.google.com/natural-language/docs/languages
  Quotas et limites: https://docs.cloud.google.com/natural-language/quotas
  Tarifs: https://cloud.google.com/products/natural-language/pricing
  Notes de version: https://docs.cloud.google.com/natural-language/docs/release-notes
---

## Ce que c'est

*Natural Language AI* désigne l'offre d'analyse de texte ; l'API appelée depuis le code est la **Cloud Natural Language API**. Elle prend un document — texte brut ou HTML, passé en ligne ou par une URI `gs://` — et renvoie des annotations. Tous les appels sont **synchrones** : il n'y a pas de mode par lots ni d'opération longue.

- **Méthodes** : `analyzeSentiment` (polarité et intensité, pour le document et pour chaque phrase), `analyzeEntities` (personnes, lieux, organisations, dates, montants, numéros), `classifyText` (taxonomie fixe de 1 091 catégories), `moderateText` (catégories nuisibles et sensibles), et `annotateText` qui combine plusieurs fonctions en un appel.
- **Deux versions**. La **v2** porte le sentiment, les entités, la classification et la modération ; la **v1** ajoute l'analyse syntaxique (`analyzeSyntax` : segmentation, nature grammaticale, arbre de dépendances) et le sentiment par entité, absents de la v2.
- **La langue est détectée** si elle n'est pas fournie ; chaque réponse renvoie `language_code`. Une langue hors du périmètre provoque une erreur en v1 ; en v2, la réponse l'indique (`language_supported` à `false`) et le texte est traité au mieux.
- **Limites par requête** : 1 Mo de texte, 100 000 jetons analysés, 5 000 mentions d'entités.
- **Facturation par unité de 1 000 caractères** Unicode arrondie au supérieur, balises comprises, par palier mensuel : 1 $ les 1 000 unités pour le sentiment et les entités, 0,50 $ pour la syntaxe, 2 $ pour le sentiment par entité et pour la classification. La modération se compte par tranches de 100 caractères, à 5 $ les 1 000 unités. Un `annotateText` est facturé comme la somme des fonctions demandées.

> [!TIP]
> `classifyText` exige un texte d'au moins 20 mots : la fonction n'est pas faite pour des titres, des étiquettes ou des messages courts.

## À quoi ça sert

- Mesurer le sentiment d'avis clients, de tickets de support ou de messages sociaux, à grand volume et à coût fixé.
- Extraire des entités d'un corpus pour l'indexer ou le relier à un référentiel.
- Classer des contenus dans une taxonomie stable, pour la recommandation ou le ciblage.
- Filtrer les contenus nuisibles avant publication.
- Alimenter une table [BigQuery](#bigquery) de métriques calculées sur du texte.

**À éviter** dès que la tâche demande une catégorie maison, une extraction de champs qui n'entrent pas dans les types d'entités prévus, une nuance de ton ou une explication : un modèle Gemini avec une sortie structurée imposée fait tout cela sans entraînement. Le fonds documentaire de l'API est d'ailleurs stable, sa dernière note de version datant de 2023. L'API reste préférable pour du **volume élevé de textes courts** où le coût par 1 000 caractères bat largement le coût par jeton, quand il faut une note de sentiment comparable dans le temps, et quand la taxonomie fixe suffit.

## Alternatives en logiciel libre

- **spaCy** (MIT) : segmentation, nature grammaticale, dépendances, entités nommées, pour une cinquantaine de langues ; l'équivalent le plus direct des fonctions v1.
- **Stanza** (Apache 2.0) : chaîne de traitement de Stanford, plus de 70 langues, annotations au format Universal Dependencies.
- **Flair** (MIT) : reconnaissance d'entités et classification par plongements contextuels, état de l'art sur plusieurs langues.
- **Transformers** et les modèles **CamemBERT**, **XLM-RoBERTa** : classification et analyse de sentiment à affiner sur ses propres étiquettes.
- **Detoxify** (Apache 2.0) : détection de contenus toxiques, à la place de `moderateText`.
