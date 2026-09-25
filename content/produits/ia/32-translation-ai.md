---
title: Translation AI
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 160, y: 16, w: 486, h: 268}
  nodes:
    auth: {label: Contenus, sub: "pages, documents", external: true, x: 8, y: 46, w: 122}
    gcs: {label: Cloud Storage, sub: "sources, glossaire", icon: produits/cloud-storage, x: 184, y: 40, w: 190}
    tr: {label: Cloud Translation, sub: "NMT, LLM, glossaire", icon: categories/ai-machine-learning, focus: true, x: 420, y: 112, w: 210, h: 66}
    out: {label: Cloud Storage, sub: "documents traduits", icon: produits/cloud-storage, x: 184, y: 210, w: 190}
    run: {label: Cloud Run, sub: "site multilingue", icon: produits/cloud-run, x: 420, y: 210, w: 210}
    visit: {label: Visiteurs, sub: "navigateur", external: true, x: 660, y: 210, w: 96}
  flows:
    - {from: auth, to: gcs, text: "Dépôt des documents à traduire et du glossaire de l'entreprise"}
    - {from: gcs, to: tr, offset: -12, text: "batchTranslateDocument lit les fichiers gs:// : une opération longue par lot"}
    - {from: tr, to: out, offset: 12, text: "Les documents traduits sont écrits dans le bucket de sortie, mise en forme conservée"}
    - {from: visit, to: run, text: "Un visiteur demande une page dans une autre langue"}
    - {from: run, to: tr, text: "translateText traduit le texte à la volée, en synchrone, avec le glossaire"}
docs:
  Page produit: https://cloud.google.com/translate
  Documentation: https://docs.cloud.google.com/translate/docs
  Panorama des offres: https://docs.cloud.google.com/translate/docs/overview
  API REST: https://docs.cloud.google.com/translate/docs/reference/rest
  Bibliothèques clientes: https://docs.cloud.google.com/translate/docs/reference/libraries/v3/overview-v3
  Client Python: https://docs.cloud.google.com/python/docs/reference/translate/latest
  Langues prises en charge: https://docs.cloud.google.com/translate/docs/languages
  Traduction de documents: https://docs.cloud.google.com/translate/docs/advanced/translate-documents
  Traduction par lots: https://docs.cloud.google.com/translate/docs/advanced/batch-translation
  Quotas et limites: https://docs.cloud.google.com/translate/quotas
  Tarifs: https://cloud.google.com/products/translate/pricing
  Notes de version: https://docs.cloud.google.com/translate/docs/release-notes
---

## Ce que c'est

*Translation AI* regroupe les offres de traduction de Google Cloud ; le service appelé depuis le code est la **Cloud Translation API**, en deux éditions.

- **Basic (v2)** : un seul appel `translate`, le modèle de traduction automatique neuronale (*NMT*) générique, détection de la langue source. Requête limitée à 100 Ko.
- **Advanced (v3)** : ressources régionalisées et fonctions supplémentaires — **glossaires** (terminologie imposée), traduction de **documents** avec conservation de la mise en forme (PDF, DOCX, PPTX, XLSX, Google Workspace), traduction par lots depuis Cloud Storage, translittération et romanisation, modèles personnalisés.
- **Choix du modèle** (paramètre `model` de l'édition Advanced ; Basic accepte aussi le Translation LLM standard par son nom de ressource complet) : `nmt` pour du texte courant, le **Translation LLM** pour du conversationnel et du contexte multiphrase, et le mode **adaptatif**, qui aligne le style sur quelques dizaines de paires d'exemples sans entraînement préalable.
- **Deux modes d'exécution.** Synchrone pour `translateText` et `translateDocument` ; **opération longue** pour `batchTranslateText` et `batchTranslateDocument`, qui lisent des fichiers dans un bucket (100 fichiers par requête au plus) et écrivent les traductions dans un autre.
- **Limites** : 30 000 points de code par requête en Advanced, 5 000 recommandés pour la latence ; 6 millions de caractères par minute et par projet sur le modèle générique ; 2 400 pages par minute pour la traduction de documents.
- **Facturation au caractère envoyé** : 500 000 caractères gratuits par mois puis 20 $ par million en NMT, 80 $ par million pour un modèle personnalisé, 0,08 $ la page en traduction de documents. Le Translation LLM et la traduction adaptative sont facturés en entrée et en sortie (10 $ et 25 $ par million de caractères).

> [!TIP]
> Un glossaire s'applique aussi bien au NMT qu'au Translation LLM et à la traduction adaptative, à condition d'activer `contextual_translation_enabled`. C'est le moyen le plus court de figer des noms de produits et un vocabulaire maison.

## À quoi ça sert

- Localiser un site, une application ou un catalogue, à la volée ou par lots.
- Traduire des documents bureautiques sans perdre leur mise en page.
- Traduire des interactions en temps réel : chat, support, centre de contacts.
- Sous-titrer et doubler des vidéos, en amont de [Speech-to-Text](#speech-to-text) et [Text-to-Speech](#text-to-speech).

**À éviter** quand la traduction ne peut pas être séparée du reste du travail : réécrire, résumer dans une autre langue, adapter le ton d'un document entier, traduire en respectant une consigne de style longue. Un modèle Gemini fait cela en un appel. L'API dédiée reste préférable pour du volume à coût prévisible et à faible latence, pour une terminologie imposée par glossaire, pour la conservation du format d'un document, et pour les 189 langues couvertes — un modèle généraliste en couvre moins, et de façon inégale.

## Alternatives en logiciel libre

- **OPUS-MT** (modèles sous Apache 2.0) : plus d'un millier de modèles de paires de langues, légers, exécutables sur processeur avec Transformers.
- [!SOMMEIL] **Marian NMT** (MIT) : le moteur de traduction C++ sur lequel les modèles OPUS-MT ont été entraînés.
- **Argos Translate** (MIT) : traduction hors ligne bâtie sur OPUS-MT, avec paquets de langues installables.
- **LibreTranslate** (AGPL 3.0) : API HTTP auto-hébergée par-dessus Argos Translate ; l'équivalent le plus direct en usage.
- **MADLAD-400** (Apache 2.0) : modèle multilingue à très large couverture, servi par Transformers ou CTranslate2.
- **Apertium** (GPL) : traduction à base de règles, prévisible et vérifiable, pour les langues proches et les langues peu dotées.
