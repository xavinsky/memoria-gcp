---
title: Model Garden
subgroup: Plateforme et modèles
icon: produits/vertex-ai
aka: Vertex AI Model Garden
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 160, y: 10, w: 590, h: 280}
  nodes:
    dev: {label: Développeur, sub: "console, SDK", external: true, x: 10, y: 120, w: 130}
    gcs: {label: Cloud Storage, sub: "jeu de réglage", icon: produits/cloud-storage, x: 180, y: 30, w: 200}
    mg: {label: Model Garden, sub: "catalogue de modèles", icon: produits/vertex-ai, focus: true, x: 180, y: 112, w: 200, h: 64}
    app: {label: Cloud Run, sub: "application", icon: produits/cloud-run, x: 180, y: 226, w: 200}
    tune: {label: Managed Training, sub: "réglage du modèle", icon: produits/vertex-ai, x: 470, y: 30, w: 260}
    ep: {label: Endpoint, sub: "conteneur vLLM, GPU", icon: produits/vertex-ai, x: 470, y: 112, w: 260, h: 64}
    maas: {label: API Gemini, sub: "modèle géré, sans endpoint", icon: produits/vertex-ai, x: 470, y: 226, w: 260}
  flows:
    - {from: dev, to: mg, control: true, text: "Recherche d'un modèle dans le catalogue par tâche, fournisseur et fonctionnalité, puis lecture de sa fiche"}
    - {from: gcs, to: tune, text: "Dépôt du jeu de données de réglage"}
    - {from: mg, to: tune, from_offset: -16, text: "Réglage fin du modèle ouvert choisi, sur l'infrastructure gérée"}
    - {from: mg, to: ep, from_offset: 16, text: "Déploiement du modèle sur un endpoint, avec le conteneur de service fourni (vLLM, Hex-LLM)"}
    - {from: app, to: ep, from_offset: -16, to_offset: 16, text: "L'application interroge son endpoint dédié : machines réservées, facturées tant qu'il est déployé"}
    - {from: app, to: maas, text: "Ou appel d'un modèle géré à l'API, facturé aux jetons, sans infrastructure à réserver"}
captures:
  - image: https://docs.cloud.google.com/static/gemini-enterprise-agent-platform/models/model-garden/images/try-out-gemma.png
    page: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/quickstart
    legende: "Panneau d'essai d'un modèle Gemma depuis sa fiche dans Model Garden"
docs:
  Page produit: https://cloud.google.com/model-garden
  Documentation: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/explore-models
  Démarrage rapide: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/quickstart
  Utiliser un modèle: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/use-models
  Déployer et interroger: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/deploy-and-inference-tutorial
  Modèles partenaires: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models
  Modèles Hugging Face: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/use-hugging-face-models
  Service avec vLLM: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/vllm/use-vllm
  Restreindre l'accès aux modèles: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/control-model-access
  Quotas et limites: https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/quotas
  Tarifs: https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing
  Notes de version: https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
---

## Ce que c'est

Catalogue de modèles d'apprentissage automatique de [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) : il sert à découvrir, essayer, personnaliser et déployer des modèles de Google, de ses partenaires et de la communauté, depuis un seul endroit et selon un schéma de déploiement identique d'un modèle à l'autre.

- **Trois familles** : les **modèles de fondation** préentraînés multitâches, appelables tels quels ou personnalisables ; les **modèles réglables**, affinés par un notebook ou un pipeline ; les **solutions par tâche**, prêtes à l'emploi et souvent personnalisables avec ses propres données.
- **Deux modes de consommation**. Le *modèle en tant que service* : l'appel passe par l'API de la plateforme, sans machine à réserver, facturé aux jetons — c'est le cas des modèles Gemini et de modèles partenaires. Le **déploiement** : le modèle ouvert est servi sur un **endpoint** dédié, avec un conteneur de service fourni (vLLM, Hex-LLM pour les TPU, xDiT pour l'image et la vidéo) et le coût des machines et accélérateurs associés.
- **Recherche** dans le catalogue par tâche, collection (modèles gérés par Google, par un partenaire ou par soi), fournisseur et fonctionnalité ; chaque modèle a une **fiche** qui documente son usage, ses licences et ses options de déploiement.
- **Analyse de sécurité** : Google teste les conteneurs de service et de réglage qu'il fournit et les analyse en continu ; les modèles des partenaires mis en avant passent par une vérification d'empreinte, ceux du Hub Hugging Face sont analysés par Hugging Face (logiciels malveillants, fichiers *pickle*, secrets). Un modèle jugé dangereux est bloqué au déploiement, un modèle suspect reste signalé mais déployable.
- **Contrôle d'accès** : une règle d'administration Model Garden, posée au niveau de l'organisation, du dossier ou du projet, restreint les modèles utilisables à une liste validée.

> [!TIP]
> Un modèle ouvert déployé sur un endpoint coûte le prix des machines, qu'il serve ou non des requêtes ; un modèle géré appelé à l'API ne coûte que les jetons. Pour un trafic faible ou intermittent, le second gagne presque toujours.

## À quoi ça sert

- Comparer et essayer plusieurs modèles avant de choisir, depuis la console, sans écrire de code de service.
- Déployer un modèle ouvert (Gemma, Llama, Qwen, modèles du Hub Hugging Face) sur un endpoint géré, avec un conteneur de service optimisé déjà prêt.
- Régler finement un modèle ouvert sur ses propres données, puis le déployer par le même chemin.
- Encadrer ce que les équipes ont le droit d'utiliser : catalogue restreint à des modèles validés.

**À éviter** pour héberger un modèle sur une infrastructure que l'on maîtrise ligne à ligne, ou pour mutualiser des GPU déjà réservés entre plusieurs charges : un déploiement vLLM sur GKE donne ce contrôle. À éviter aussi comme registre des modèles maison : c'est le rôle de Model Registry, dans [Agent Platform](#gemini-enterprise-agent-platform).

## Alternatives en logiciel libre

- **Hugging Face Hub** avec les bibliothèques `transformers` et `huggingface_hub` : le catalogue de référence des modèles ouverts, avec fiches, versions et licences.
- **vLLM** : serveur d'inférence pour les grands modèles de langage, celui que Model Garden emploie lui-même dans ses conteneurs de service.
- **Ollama** : récupération et exécution locales de modèles ouverts en une commande, pour le poste de développement et les petits serveurs.
- **KServe**, **BentoML** : déploiement de modèles sur Kubernetes derrière une API stable, l'équivalent d'un endpoint.
- **MLflow Model Registry** : catalogue et versionnement de modèles maison, à côté du catalogue de modèles publics.
