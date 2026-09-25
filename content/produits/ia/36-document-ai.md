---
title: Document AI
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 168, y: 16, w: 578, h: 268}
  nodes:
    four: {label: Fournisseurs, sub: "factures PDF", external: true, x: 8, y: 46, w: 114}
    gcs: {label: Cloud Storage, sub: "PDF entrants", icon: produits/cloud-storage, x: 192, y: 40, w: 180}
    bq: {label: BigQuery, sub: "table d'objets, SQL", icon: produits/bigquery, x: 192, y: 200, w: 180}
    doc: {label: Document AI, sub: "Invoice Parser", icon: categories/ai-machine-learning, focus: true, x: 440, y: 190, w: 200, h: 66}
    compta: {label: Comptabilité, sub: "requêtes SQL", external: true, x: 8, y: 200, w: 146}
  flows:
    - {from: four, to: gcs, text: "Dépôt des factures PDF dans un bucket"}
    - {from: gcs, to: bq, text: "Une table d'objets BigQuery référence les fichiers du bucket et leurs métadonnées"}
    - {from: bq, to: doc, offset: -14, text: "ML.PROCESS_DOCUMENT appelle le processeur par un modèle distant déclaré en SQL"}
    - {from: doc, to: bq, offset: 14, text: "Les entités extraites reviennent en colonnes typées, jointes aux tables existantes"}
    - {from: bq, to: compta, text: "Requêtes SQL sur les montants, les dates et les fournisseurs"}
captures:
  - image: https://docs.cloud.google.com/static/document-ai/docs/images/create/form-parser-kvp.png
    page: https://docs.cloud.google.com/document-ai/docs/form-parser
    legende: "Analyse d'un formulaire manuscrit par Form Parser : les paires clé-valeur extraites à gauche, encadrées sur le document à droite"
  - image: https://docs.cloud.google.com/static/document-ai/docs/images/create/cde-with-genai-20.png
    page: https://docs.cloud.google.com/document-ai/docs/ce-with-genai
    legende: "Custom Extractor : les champs d'une facture (échéance, numéro, total) extraits et surlignés sur le document"
docs:
  Page produit: https://cloud.google.com/document-ai
  Documentation: https://docs.cloud.google.com/document-ai/docs
  Liste des processeurs: https://docs.cloud.google.com/document-ai/docs/processors-list
  API REST: https://docs.cloud.google.com/document-ai/docs/reference/rest
  Bibliothèques clientes: https://docs.cloud.google.com/document-ai/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/documentai/latest
  Envoyer une requête: https://docs.cloud.google.com/document-ai/docs/send-request
  Formats acceptés: https://docs.cloud.google.com/document-ai/docs/file-types
  Intégration BigQuery: https://docs.cloud.google.com/document-ai/docs/big-query-integration
  Quotas: https://docs.cloud.google.com/document-ai/quotas
  Limites: https://docs.cloud.google.com/document-ai/limits
  Tarifs: https://cloud.google.com/products/document-ai/pricing
  Notes de version: https://docs.cloud.google.com/document-ai/docs/release-notes
---

## Ce que c'est

Plateforme d'**extraction de données documentaires**. On crée un **processeur** dans un projet et une région, puis on lui envoie des documents ; il renvoie un objet `Document` normalisé : texte, mise en page (pages, blocs, paragraphes, lignes, jetons, tableaux), entités typées et coordonnées de chaque élément.

- **Familles de processeurs.** *Numériser* : Enterprise Document OCR, plus de 200 langues, manuscrit compris, avec évaluation de la qualité du scan. *Structurer* : Form Parser (paires clé/valeur et tableaux), Layout Parser (découpage en fragments pour du RAG). *Extraire* : Custom Extractor, bâti sur Gemini, avec un **schéma de document** défini par l'utilisateur et affinable sur des exemples annotés. *Classer* : Custom Classifier et Custom Splitter, pour trier et découper un lot hétérogène. *Prêts à l'emploi* : facture, note de frais, bulletin de paie, relevé bancaire, formulaire W2, pièces d'identité.
- **Deux modes d'appel.** `process` en **synchrone** : un fichier de 40 Mo au plus (20 Mo pour le Layout Parser), 15 pages pour la plupart des processeurs, 30 en mode sans image. `batchProcess` en **opération longue** : jusqu'à 5 000 fichiers et 1 Go par requête, lus dans Cloud Storage et écrits dans un bucket de sortie ; le plafond de pages dépend du processeur (500 pour l'OCR et le Layout Parser, 200 pour l'Invoice Parser et le Custom Extractor). Les lots aboutissent en général en 12 à 24 heures et sont annulés au-delà de 24 heures.
- **Entrées** : PDF, TIFF, GIF, JPEG, PNG, BMP, WebP, et HTML, DOCX, PPTX, XLSX pour le Layout Parser. Les scans doivent être à 200 dpi au minimum, 300 dpi de préférence.
- **Intégration SQL** : un **modèle distant** BigQuery déclaré avec `remote_service_type = 'CLOUD_AI_DOCUMENT_V1'` rend le processeur appelable depuis `ML.PROCESS_DOCUMENT` sur une table d'objets.
- **Capacité** : les processeurs génératifs sont servis sur un palier *provisioned* garanti et un palier *best effort* sans engagement de service ; la capacité réservée s'achète à l'heure.
- **Facturation à la page** traitée, selon le processeur : 1,50 $ les 1 000 pages pour l'OCR (1 000 pages gratuites par mois), 30 $ les 1 000 pages pour le Custom Extractor et le Form Parser, 10 $ pour le Layout Parser, 5 $ pour les classifieurs. Les processeurs spécialisés se facturent au document, par tranches de 10 pages : 0,10 $ pour une facture ou une note de frais. Un processeur personnalisé déployé coûte en plus 0,05 $ l'heure d'hébergement.

> [!WARNING]
> Un processeur personnalisé déployé est facturé même sans trafic — environ 438 $ par an et par version. Annuler le déploiement des versions qui ne servent plus.

## À quoi ça sert

- Automatiser une chaîne comptable : factures fournisseurs, notes de frais, relevés, rapprochement avec l'ERP.
- Instruire des dossiers : prêts, assurances, ressources humaines, avec vérification de pièces d'identité.
- Numériser et rendre cherchable un fonds d'archives papier.
- Préparer un corpus pour du RAG : le Layout Parser découpe en fragments qui respectent la structure du document.
- Extraire des champs en SQL depuis [BigQuery](#bigquery), sans pipeline dédié.

**À éviter** pour du texte dans une photo de scène, une enseigne ou une capture d'écran : [Vision AI](#vision-ai) est prévu pour cela et coûte moins cher. À éviter aussi pour quelques dizaines de documents aux champs simples, ou pour une extraction dont le schéma change souvent : un appel direct à un modèle Gemini avec un PDF et un schéma JSON donne le même résultat sans processeur à créer ni à déployer. Document AI reste préférable quand il faut les **coordonnées** de chaque champ dans la page (surlignage, contrôle humain, piste d'audit), une mise en page fidèle avec tableaux et cases à cocher, un lot de plusieurs milliers de fichiers en une requête, un tarif à la page, la résidence des données en Union européenne, ou un processeur prêt à l'emploi sur un document normalisé.

## Alternatives en logiciel libre

- **OCRmyPDF** (MPL 2.0) sur **Tesseract** (Apache 2.0) : couche de texte ajoutée à un PDF scanné, la brique de numérisation.
- **PaddleOCR** avec **PP-Structure** (Apache 2.0) : OCR, analyse de mise en page et reconnaissance de tableaux ; le plus proche du Form Parser.
- **Docling** (MIT) et **unstructured** (Apache 2.0) : conversion de PDF, DOCX et HTML en documents structurés et en fragments pour du RAG, à la place du Layout Parser.
- **LayoutParser** (Apache 2.0) : détection des régions d'une page par modèles de vision, avec des modèles préentraînés sur des corpus documentaires.
- **Donut** (MIT) : extraction de champs de bout en bout, sans OCR préalable, à affiner sur ses propres documents.
- **Label Studio** (Apache 2.0) : annotation des documents d'entraînement, à la place de l'atelier d'annotation intégré.
