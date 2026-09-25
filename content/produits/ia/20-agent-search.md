---
title: Agent Search
subgroup: Agents
icon: categories/agents
aka: Vertex AI Search, AI Applications
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 146, y: 8, w: 604, h: 284}
  nodes:
    users: {label: Utilisateurs, sub: recherche, external: true, x: 8, y: 216, w: 126}
    agent: {label: Agent, sub: "outil de récupération", icon: produits/vertex-ai, x: 164, y: 26, w: 200}
    gcs: {label: Cloud Storage, sub: "PDF, HTML", icon: produits/cloud-storage, x: 164, y: 101, w: 200}
    bq: {label: BigQuery, sub: "tables structurées", icon: produits/bigquery, x: 164, y: 176, w: 200}
    as: {label: Agent Search, sub: "data store + app", icon: categories/agents, focus: true, x: 430, y: 100, w: 220, h: 72}
    run: {label: Cloud Run, sub: "application web", icon: produits/cloud-run, x: 430, y: 216, w: 220}
  flows:
    - {from: gcs, to: as, text: "Import des documents non structurés : analyse de mise en page, OCR, découpage et vectorisation"}
    - {from: bq, to: as, to_offset: 22, text: "Import des données structurées d'une table, avec leur schéma et leurs métadonnées"}
    - {from: users, to: run, text: "L'utilisateur saisit une requête en langage naturel dans l'application"}
    - {from: run, to: as, from_side: top, from_offset: -60, to_side: bottom, to_offset: -60, text: "Appel de l'API de recherche ou de réponse : résultats classés, puis réponse générée avec citations"}
    - {from: run, to: as, from_side: top, from_offset: 60, to_side: bottom, to_offset: 60, control: true, text: "Renvoi des événements utilisateur (clics, conversions) qui affinent le classement au fil du temps"}
    - {from: agent, to: as, to_offset: -22, text: "Un agent utilise le même index comme outil de récupération pour ancrer ses réponses"}
docs:
  Page produit: https://cloud.google.com/products/gemini-enterprise-agent-platform/agent-search
  Documentation: https://docs.cloud.google.com/generative-ai-app-builder/docs
  Introduction à la recherche personnalisée: https://docs.cloud.google.com/generative-ai-app-builder/docs/about-generic-search
  Fonctionnalités avancées: https://docs.cloud.google.com/generative-ai-app-builder/docs/about-advanced-features
  Créer un data store: https://docs.cloud.google.com/generative-ai-app-builder/docs/create-data-store-es
  Réponses générées: https://docs.cloud.google.com/generative-ai-app-builder/docs/answer
  Widget de recherche: https://docs.cloud.google.com/generative-ai-app-builder/docs/add-widget
  API REST: https://docs.cloud.google.com/generative-ai-app-builder/docs/reference/rest
  API RPC: https://docs.cloud.google.com/generative-ai-app-builder/docs/reference/rpc
  Bibliothèques clientes: https://docs.cloud.google.com/generative-ai-app-builder/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/discoveryengine/latest
  Quotas et limites: https://docs.cloud.google.com/generative-ai-app-builder/quotas
  Tarifs: https://cloud.google.com/generative-ai-app-builder/pricing
  Notes de version: https://docs.cloud.google.com/generative-ai-app-builder/docs/release-notes
---

## Ce que c'est

Moteur de recherche et de recommandation géré, à brancher sur ses propres données : on déclare des sources, le service les indexe, puis une API renvoie des résultats classés et, si on le demande, une réponse rédigée avec ses citations. C'est la brique de récupération sur laquelle s'appuient les applications RAG et les agents.

- **Data store** : le réservoir indexé. Il accepte un **site web public** (après vérification du domaine), des **données non structurées** — PDF, HTML, texte, images — depuis Cloud Storage ou BigQuery, et des **données structurées** — tables BigQuery, JSON dans Cloud Storage. Des connecteurs alimentent les data stores depuis des applications tierces.
- **Application** (*app*, appelée *engine* dans l'API) : elle relie un ou plusieurs data stores et porte le réglage du comportement. Plusieurs data stores sur une même application, c'est la **recherche mixte** (*blended search*), qui interroge tout le contenu d'un coup.
- **Indexation** : extraction de mots-clés, vecteurs d'embeddings pour le sens, traitement des métadonnées, analyse avancée des documents (tableaux, images, graphiques, OCR et analyse de mise en page).
- **Requête et classement** : compréhension de l'intention en langage naturel, traduction d'une contrainte exprimée en toutes lettres en filtre, désambiguïsation par le graphe de connaissances, correction orthographique et synonymes ; puis un classement qui mêle correspondance de mots-clés, similarité sémantique, signaux web pour les sites, règles de promotion ou de rétrogradation (*boost*, *bury*) et personnalisation apprise des **événements utilisateur**.
- **Restitution** : liste de résultats avec extraits et segments, ou **réponse générée** par un modèle à partir des meilleurs résultats, avec citations, questions de suivi et requêtes liées. L'intégration se fait par l'API ou par un **widget** déposé dans une page.
- **Variantes par métier** : recherche personnalisée (générique), recherche et recommandations **média**, recherche **santé** sur des ressources FHIR, recommandations personnalisées.

> [!TIP]
> L'API sous-jacente est **Discovery Engine** : les appels `curl` et les bibliothèques clientes visent `discoveryengine.googleapis.com`, et la page de la console s'appelle *AI Applications*. Ce sont bien le même produit.

## À quoi ça sert

- Moteur de recherche interne ou public sur un corpus documentaire, sans construire de chaîne d'indexation.
- Brique de récupération d'une application RAG : l'API `answer` rend la réponse et ses sources, sans code de découpage, de vectorisation ni de classement à écrire.
- Outil de récupération d'un agent, pour ancrer ses réponses dans les documents de l'entreprise.
- Recommandations de contenu à partir des événements utilisateur.

**À éviter** quand on veut maîtriser le découpage, le modèle d'embeddings et la fonction de classement : Vector Search ou une base vectorielle laissent ce contrôle. À éviter aussi pour une recherche par mots-clés sur quelques milliers de lignes déjà stockées en base : un index de recherche plein texte de PostgreSQL suffit (voir [Choisir une base de données](#choisir-une-base)). Pour un assistant prêt à l'emploi destiné aux salariés, avec son interface et ses connecteurs, préférer [Gemini Enterprise app](#gemini-enterprise-app).

## Alternatives en logiciel libre

- **OpenSearch** : moteur de recherche distribué, recherche lexicale et vectorielle (k-NN), classement personnalisable ; la base la plus proche en périmètre.
- **Qdrant**, **Weaviate**, **Milvus** : bases vectorielles pour la recherche sémantique, avec filtrage sur métadonnées et recherche hybride.
- **Haystack**, **LlamaIndex** : cadres qui assemblent la chaîne complète — ingestion, découpage, embeddings, récupération, génération avec citations — soit l'équivalent de l'API de réponse.
- **Apache Solr** : moteur plein texte mûr, pour un besoin de recherche classique avec facettes.
- **PostgreSQL** avec `tsvector` et **pgvector** : recherche plein texte et vectorielle dans la base applicative, quand le volume ne justifie pas un moteur dédié.
