---
title: Video Intelligence API
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 160, y: 16, w: 594, h: 268}
  nodes:
    prod: {label: Production, sub: "fichiers vidéo", external: true, x: 8, y: 120, w: 146}
    gcs: {label: Cloud Storage, sub: "vidéos sources", icon: produits/cloud-storage, x: 176, y: 44, w: 168}
    wf: {label: Workflows, sub: "orchestration", icon: categories/integration-services, x: 176, y: 210, w: 168}
    vid: {label: Video Intelligence, sub: "labels, plans, OCR", icon: categories/ai-machine-learning, focus: true, x: 372, y: 112, w: 188, h: 66}
    ann: {label: Cloud Storage, sub: "annotations", icon: produits/cloud-storage, x: 600, y: 44, w: 150}
    bq: {label: BigQuery, sub: "index vidéo", icon: produits/bigquery, x: 600, y: 210, w: 150}
  flows:
    - {from: prod, to: gcs, text: "Dépôt des vidéos dans un bucket : 50 Go et 3 heures au maximum par fichier"}
    - {from: wf, to: vid, control: true, offset: 12, text: "Workflows appelle videos:annotate pour chaque vidéo et suit l'opération longue"}
    - {from: gcs, to: vid, offset: -12, text: "L'API lit la vidéo directement par son URI gs://, sans la recopier"}
    - {from: vid, to: ann, text: "Les annotations horodatées sont écrites en JSON à l'adresse donnée par outputUri"}
    - {from: ann, to: bq, text: "Chargement des annotations dans une table pour rendre le catalogue cherchable"}
deprecie: "Un modèle Gemini raisonne sur la vidéo, ce que cette API ne fait pas. Elle garde un intérêt pour l'annotation massive à vocabulaire fermé et pour un flux en direct."
docs:
  Page produit: https://cloud.google.com/video-intelligence
  Documentation: https://docs.cloud.google.com/video-intelligence/docs
  Liste des fonctions: https://docs.cloud.google.com/video-intelligence/docs/features
  API REST: https://docs.cloud.google.com/video-intelligence/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/ml/video
  Bibliothèques clientes: https://docs.cloud.google.com/video-intelligence/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/videointelligence/latest
  Opérations longues: https://docs.cloud.google.com/video-intelligence/docs/long-running-operations
  Annotation en flux: https://docs.cloud.google.com/video-intelligence/docs/streaming/streaming
  Quotas et limites: https://docs.cloud.google.com/video-intelligence/quotas
  Tarifs: https://cloud.google.com/products/video-intelligence/pricing
  Notes de version: https://docs.cloud.google.com/video-intelligence/docs/release-notes
---

## Ce que c'est

API d'**annotation de vidéos** : on désigne une vidéo et la liste des fonctions à appliquer, le service renvoie des annotations horodatées, au niveau de la vidéo entière, du plan ou de l'image.

- **Fonctions** : détection de labels, changement de plan, contenu explicite, suivi d'objets, détection de texte (OCR à l'écran), reconnaissance de logos, détection de personnes et de visages avec leurs attributs, transcription de la parole (anglais américain uniquement), reconnaissance de célébrités (accès restreint).
- **Deux modes.** *Annotation de fichier* : `videos:annotate` ouvre toujours une **opération longue**, même pour une vidéo courte ; la vidéo est lue par son URI `gs://` ou passée en base64, et le résultat est renvoyé dans l'opération ou écrit dans un bucket via `outputUri`. *Annotation en flux* : une API gRPC bidirectionnelle qui annote un direct au fil de l'eau, pour les labels, les plans, le contenu explicite et le suivi d'objets.
- **Granularité** : chaque annotation porte un intervalle de temps, et pour les objets et le texte une boîte englobante normalisée qui suit le sujet d'une image à l'autre.
- **Limites** : 50 Go et 3 heures par vidéo ; le débit par défaut est de 180 secondes de traitement par minute et par projet, soit environ 3 minutes de vidéo traitées par minute.
- **Facturation à la minute de vidéo**, arrondie à la minute supérieure, et **par fonction demandée** : 1 000 minutes gratuites par mois et par fonction, puis 0,10 $ la minute pour les labels, 0,15 $ pour le suivi d'objets, le texte et les logos, 0,05 $ pour les plans. La détection de plans est gratuite quand elle accompagne la détection de labels.

> [!WARNING]
> Chaque fonction est facturée séparément sur toute la durée de la vidéo : demander cinq fonctions sur un film de deux heures revient à payer cinq fois 120 minutes. Restreindre la liste des fonctions, ou découper la vidéo en segments avec `segments`.

## À quoi ça sert

- Indexer un catalogue vidéo pour le rendre cherchable comme un fonds documentaire.
- Modérer des vidéos déposées par des utilisateurs.
- Découper automatiquement en plans, pour du montage, des vignettes ou des résumés.
- Placer des publicités contextuelles au bon moment, à partir des labels horodatés.
- Charger les annotations dans [BigQuery](#bigquery) pour croiser le catalogue avec l'audience.

**À éviter** quand la question porte sur le *sens* de la vidéo : résumer, répondre à une question, retrouver un moment décrit en langage courant, vérifier une règle métier. Les modèles Gemini prennent la vidéo en entrée et raisonnent dessus, ce que cette API ne fait pas — son fonds documentaire est stable, sa dernière note de version datant de 2021. L'API dédiée reste préférable pour des annotations **exhaustives et régulières** sur un gros catalogue, avec des libellés d'un vocabulaire fermé, un horodatage précis, un suivi d'objet image par image, un tarif à la minute, et pour l'annotation d'un flux en direct.

## Alternatives en logiciel libre

- **PySceneDetect** (BSD) : découpage en plans par analyse de contenu, l'équivalent direct de la détection de changements de plan.
- **Ultralytics YOLO** (AGPL 3.0) avec **ByteTrack** ou **BoT-SORT** : détection et suivi d'objets image par image, avec boîtes englobantes.
- **MMAction2** (Apache 2.0) : reconnaissance d'actions et localisation temporelle dans une vidéo.
- **OpenCLIP** (MIT) : étiquetage et recherche de séquences par similarité, sur des images extraites à intervalle régulier.
- **Whisper** (MIT) : transcription de la bande son, à la place de la fonction de transcription intégrée.
- **FFmpeg** (LGPL/GPL) et **OpenCV** (Apache 2.0) : extraction d'images, découpage et prétraitement, socle de toute chaîne maison.
