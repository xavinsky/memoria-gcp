---
title: Gemini Enterprise Agent Platform
subgroup: Plateforme et modèles
icon: produits/vertex-ai
aka: Vertex AI
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 10, y: 8, w: 740, h: 282}
  nodes:
    pipe: {label: Pipelines, sub: "orchestration MLOps", icon: produits/vertex-ai, x: 26, y: 32, w: 196}
    bq: {label: BigQuery, sub: "jeu d'entraînement", icon: produits/bigquery, x: 26, y: 112, w: 196}
    gcs: {label: Cloud Storage, sub: "conteneur, artefacts", icon: produits/cloud-storage, x: 26, y: 210, w: 196}
    train: {label: Managed Training, sub: "job d'entraînement", icon: produits/vertex-ai, focus: true, x: 272, y: 90, w: 200, h: 60}
    reg: {label: Model Registry, sub: "versions du modèle", icon: produits/vertex-ai, x: 272, y: 206, w: 200}
    ep: {label: Endpoint, sub: "inférence en ligne", icon: produits/vertex-ai, x: 530, y: 149, w: 200}
    run: {label: Cloud Run, sub: "application", icon: produits/cloud-run, x: 530, y: 26, w: 200}
  flows:
    - {from: bq, to: train, to_offset: -20, text: "Lecture du jeu d'entraînement, directement ou via un dataset géré"}
    - {from: gcs, to: train, from_side: right, to_side: left, to_offset: 20, text: "Le job récupère son code et son conteneur, et y dépose les artefacts du modèle"}
    - {from: pipe, to: train, to_side: top, control: true, text: "Un pipeline enchaîne préparation, entraînement, évaluation et déploiement à chaque nouvelle version"}
    - {from: train, to: reg, text: "Le modèle entraîné est importé dans le registre, qui en garde les versions"}
    - {from: reg, to: ep, text: "Déploiement d'une version sur un endpoint : machines et accélérateurs réservés au service du modèle"}
    - {from: run, to: ep, text: "L'application appelle l'endpoint en ligne (REST ou gRPC) pour chaque inférence"}
captures:
  - image: https://docs.cloud.google.com/static/gemini-enterprise-agent-platform/images/agent-engine-dashboard.png
    page: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/manage-deployed-agents
    legende: "Tableau de bord des agents déployés sur Agent Runtime"
docs:
  Page produit: https://cloud.google.com/products/gemini-enterprise-agent-platform
  Documentation: https://docs.cloud.google.com/gemini-enterprise-agent-platform
  Vue d'ensemble: https://docs.cloud.google.com/gemini-enterprise-agent-platform/overview
  Machine learning: https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning
  Changements de noms: https://docs.cloud.google.com/gemini-enterprise-agent-platform/vertex-ai-name-changes
  API REST: https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/ai
  Bibliothèques clientes: https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/start/client-libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/aiplatform/latest
  Quotas et limites: https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/quotas
  Tarifs: https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing
  Notes de version: https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
---

## Ce que c'est

Plateforme unifiée d'apprentissage automatique et d'agents : elle couvre le cycle de vie complet, de l'accès aux modèles de fondation jusqu'au déploiement et à la surveillance en production. La documentation l'organise en quatre piliers.

- **Build** — construire. **Agent Development Kit** (ADK), cadre modulaire et indépendant du modèle ; **Agent Studio**, atelier visuel à faible code ; **Agent Garden**, bibliothèque d'agents et de modèles de départ ; **Model Garden** (voir [Model Garden](#model-garden)) ; **RAG Engine** et **Vector Search** pour brancher des données privées sur un modèle ; **Managed Agents API**, pilotée par configuration, qui exécute l'agent dans un bac à sable géré.
- **Scale** — mettre à l'échelle. **Agent Runtime** est le runtime managé où l'on déploie un agent ; **Sessions** conserve l'état d'une conversation, **Memory Bank** la mémoire persistante d'un utilisateur d'une session à l'autre, **Code Execution** exécute du Python généré dans un bac à sable.
- **Govern** — gouverner. **Agent Registry** catalogue agents, outils et serveurs MCP ; **Agent Identity** donne une identité propre à chaque agent ; **Agent Gateway** est le point d'application des règles sur les appels d'outils ; s'y ajoutent les politiques de protection du contenu et l'analyse de vulnérabilités.
- **Optimize** — évaluer et affiner. Service d'évaluation (*autoraters* multi-tours, évaluation en ligne sur le trafic réel), simulation de conversations, traçage unifié, optimisation automatique des instructions.

Le **cycle ML classique** reste au cœur de la plateforme : *datasets* gérés, **Managed Training** (jobs d'entraînement sur infrastructure gérée, PyTorch, TensorFlow, scikit-learn, XGBoost, entraînement distribué et réglage d'hyperparamètres), **Model Registry** qui versionne les modèles, **endpoints** pour l'inférence en ligne et **batch inference** pour l'inférence asynchrone, **Pipelines** pour enchaîner les étapes, **Feature Store**, **Model Monitoring**, notebooks **Colab Enterprise** et **Workbench**.

La facturation suit les ressources consommées : temps de calcul des jobs d'entraînement, nœuds d'un endpoint tant que le modèle y est déployé, jetons pour les modèles gérés appelés à l'API.

> [!WARNING]
> Un modèle déployé sur un endpoint est facturé à l'heure de nœud, même sans trafic : ce sont des machines réservées. Retirer le modèle (*undeploy*) arrête la facturation ; retirer les modèles des endpoints de test fait partie du ménage de fin de projet.

## À quoi ça sert

- Entraîner, versionner et servir des modèles maison, avec une chaîne MLOps reproductible (pipelines, registre, évaluation, surveillance).
- Appeler les modèles Gemini et les autres modèles du catalogue depuis une application, sans gérer de serveur d'inférence.
- Construire des agents : outillage (ADK, Agent Studio), exécution (Agent Runtime, sessions, mémoire), gouvernance (identité, passerelle) et évaluation.
- Brancher des données privées sur un modèle en RAG, via RAG Engine, Vector Search ou [Agent Search](#agent-search).

**À éviter** quand les données sont déjà dans un entrepôt et que le besoin s'exprime en SQL : BigQuery ML entraîne et appelle les modèles sans sortir de l'entrepôt (voir [BigQuery](#bigquery)). Pour servir un modèle ouvert à coût maîtrisé sur une infrastructure que l'on administre déjà, un déploiement vLLM sur GKE revient souvent moins cher qu'un endpoint géré. Pour donner un assistant clé en main aux salariés, sans développement, préférer [Gemini Enterprise app](#gemini-enterprise-app).

## Alternatives en logiciel libre

- **Kubeflow** : la pile ML sur Kubernetes — Kubeflow Pipelines répond aux pipelines, Katib au réglage d'hyperparamètres, KServe au service des modèles.
- **MLflow** : suivi des expériences, registre de modèles et packaging ; l'équivalent d'Experiments et de Model Registry.
- **Ray** (Ray Train, Ray Serve, Ray Tune) : entraînement distribué et service de modèles, la brique la plus proche de Managed Training.
- **KServe**, **BentoML** : serveurs d'inférence sur Kubernetes, pour l'équivalent d'un endpoint.
- **vLLM** : moteur de service pour les grands modèles de langage, avec *continuous batching* et *paged attention* ; **Ollama** pour le même usage sur un poste ou un petit serveur.
- **LangChain**, **LlamaIndex**, **Haystack** : cadres d'orchestration d'agents et de RAG, face à ADK et RAG Engine.
- **Feast** : *feature store* open source.
