---
title: Vision AI
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 168, y: 16, w: 578, h: 268}
  nodes:
    users: {label: Utilisateurs, sub: "envoi de photos", external: true, x: 8, y: 46, w: 118}
    run: {label: Cloud Run, sub: "API d'envoi", icon: produits/cloud-run, x: 192, y: 40, w: 180}
    gcs: {label: Cloud Storage, sub: "images, PDF", icon: produits/cloud-storage, x: 192, y: 210, w: 180}
    vis: {label: Cloud Vision API, sub: "labels, SafeSearch, OCR", icon: categories/ai-machine-learning, focus: true, x: 424, y: 112, w: 240, h: 66}
    fs: {label: Firestore, sub: "labels, verdict", icon: categories/databases, x: 424, y: 214, w: 240}
  flows:
    - {from: users, to: run, text: "Envoi d'une photo par le formulaire de l'application"}
    - {from: run, to: gcs, text: "L'image est déposée dans le bucket, sous son nom définitif"}
    - {from: run, to: vis, offset: -12, text: "images:annotate demande labels et SafeSearch en une requête synchrone (20 Mo au plus)"}
    - {from: gcs, to: vis, offset: 12, text: "files:asyncBatchAnnotate traite les PDF et TIFF du bucket : opération longue, résultat JSON écrit à côté"}
    - {from: vis, to: fs, text: "Les annotations et le verdict de modération sont enregistrés avec la fiche de l'image"}
captures:
  - image: https://docs.cloud.google.com/static/vision/docs/images/shanghai_labels.png
    page: https://docs.cloud.google.com/vision/docs/detect-labels-image-command-line
    legende: "Détection de labels : chaque libellé est rendu avec son score de confiance"
  - image: https://docs.cloud.google.com/static/vision/docs/images/shanghai_text.png
    page: https://docs.cloud.google.com/vision/docs/detect-labels-image-command-line
    legende: "Détection de texte sur la même image : l'enseigne est encadrée et rendue dans la hiérarchie page, bloc, paragraphe"
docs:
  Page produit: https://cloud.google.com/vision
  Documentation: https://docs.cloud.google.com/vision/docs
  Liste des fonctions: https://docs.cloud.google.com/vision/docs/features-list
  API REST: https://docs.cloud.google.com/vision/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/ml/vision
  Bibliothèques clientes: https://docs.cloud.google.com/vision/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/vision/latest
  Formats et tailles acceptés: https://docs.cloud.google.com/vision/docs/supported-files
  OCR et texte: https://docs.cloud.google.com/vision/docs/ocr
  Product Search: https://docs.cloud.google.com/vision/product-search/docs
  Quotas et limites: https://docs.cloud.google.com/vision/quotas
  Tarifs: https://cloud.google.com/vision/pricing
  Notes de version: https://docs.cloud.google.com/vision/docs/release-notes
---

## Ce que c'est

*Vision AI* désigne l'offre d'analyse d'images ; l'API appelée depuis le code est la **Cloud Vision API**. Une requête porte une image et une liste de fonctions à appliquer ; la réponse est un JSON d'annotations.

- **Fonctions** : `LABEL_DETECTION` (libellés généraux), `TEXT_DETECTION` et `DOCUMENT_TEXT_DETECTION` (OCR, texte épars ou dense et manuscrit), `OBJECT_LOCALIZATION` (objets et boîtes englobantes), `FACE_DETECTION` (visages, points caractéristiques, indices d'émotion — pas d'identification de personne), `LOGO_DETECTION`, `LANDMARK_DETECTION`, `SAFE_SEARCH_DETECTION` (contenu sensible, en cinq catégories et six niveaux de vraisemblance), `IMAGE_PROPERTIES`, `CROP_HINTS`, `WEB_DETECTION`.
- **Product Search** : un index d'images de catalogue, interrogé par photo, pour retrouver un article de référence.
- **Trois points d'entrée.** `images:annotate` en synchrone, jusqu'à 20 Mo par image et 10 Mo pour la requête JSON entière. `files:annotate` pour un PDF ou un TIFF court. `images:asyncBatchAnnotate` et `files:asyncBatchAnnotate` pour les lots : **opération longue**, les fichiers sont lus dans Cloud Storage et le JSON d'annotations y est écrit.
- **Entrées** : JPEG, PNG, GIF, BMP, WEBP, RAW, ICO, PDF, TIFF. 640×480 suffit pour la plupart des fonctions, 1024×768 pour l'OCR, 1600×1200 pour les visages ; au-delà de 75 millions de pixels, l'image est redimensionnée pour l'OCR.
- **Modèles versionnés** : `builtin/stable`, `builtin/latest` et `builtin/legacy` dans le champ `model` d'une fonction, pour essayer un nouveau modèle avant qu'il ne devienne le défaut.
- **Facturation par unité** = une fonction appliquée à une image ou à une page. Les 1 000 premières unités du mois sont gratuites, puis 1,50 $ les 1 000 unités jusqu'à 5 millions. SafeSearch est gratuit quand il accompagne la détection de labels.

> [!WARNING]
> Pour un PDF, chaque page compte comme une image facturée, et chaque fonction demandée comme une unité distincte : une requête à trois fonctions sur un document de 40 pages coûte 120 unités.

## À quoi ça sert

- Modérer des images envoyées par les utilisateurs, avec SafeSearch.
- Étiqueter et rendre cherchable un fonds photographique.
- Lire du texte dans des photos : panneaux, étiquettes, plaques, captures d'écran.
- Reconnaître des articles de catalogue à partir d'une photo, avec Product Search.

**À éviter** pour un document structuré — facture, formulaire, contrat : [Document AI](#document-ai) lit la mise en page, les tableaux et les champs, là où l'OCR de Vision ne renvoie qu'une hiérarchie page / bloc / paragraphe / mot. À éviter aussi quand la question posée sur l'image est ouverte (« que fait cette personne ? », « ce plan est-il conforme ? ») ou que l'on veut une sortie au format de son choix : c'est le terrain d'un modèle Gemini multimodal. L'API dédiée reste préférable pour des sorties **structurées et stables** — coordonnées de boîtes, scores de confiance, catégories fixes —, pour un tarif à l'unité qui ne dépend pas de la taille de l'image, pour la latence, et pour des volumes de plusieurs millions d'images.

## Alternatives en logiciel libre

- **Tesseract** (Apache 2.0) et **PaddleOCR** (Apache 2.0) : OCR classique, plus de 100 langues ; PaddleOCR gère mieux les scènes naturelles et les langues asiatiques.
- **docTR** (Apache 2.0) : OCR par réseaux de neurones, détection puis reconnaissance, en PyTorch ou TensorFlow.
- **OpenCV** (Apache 2.0) : traitement d'images classique — détection, segmentation, correspondance de points ; la base sur laquelle se construit le reste.
- **Ultralytics YOLO** (AGPL 3.0) et **MMDetection** (Apache 2.0) : détection d'objets et boîtes englobantes, préentraînées sur COCO ou affinées.
- **OpenCLIP** (MIT) : étiquetage et recherche d'images par similarité vectorielle, l'équivalent libre de Product Search.
- **NudeNet** (AGPL 3.0) : classification et floutage de contenu explicite, à la place de SafeSearch.
