---
title: Customer Experience Agent Studio
subgroup: Agents
icon: categories/agents
aka: Dialogflow CX
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 8, w: 580, h: 284}
  nodes:
    dev: {label: Équipe CX, sub: "constructeur visuel", external: true, x: 8, y: 26, w: 136}
    cust: {label: Clients, sub: "voix, chat", external: true, x: 8, y: 110, w: 136}
    human: {label: Conseiller, sub: escalade, external: true, x: 8, y: 216, w: 136}
    cx: {label: CX Agent Studio, sub: "agent racine + sous-agents", icon: categories/agents, focus: true, x: 190, y: 100, w: 230, h: 72}
    tools: {label: Cloud Run, sub: "outil OpenAPI, webhook", icon: produits/cloud-run, x: 470, y: 26, w: 260}
    ds: {label: Agent Search, sub: "base de connaissances", icon: categories/agents, x: 470, y: 110, w: 260}
    bq: {label: BigQuery, sub: "historique, évaluation", icon: produits/bigquery, x: 470, y: 194, w: 260}
  flows:
    - {from: dev, to: cx, to_offset: -20, control: true, text: "Construction de l'arbre d'agents, des instructions et des outils dans le constructeur visuel, puis déploiement d'une version sur un canal"}
    - {from: cust, to: cx, text: "Le client arrive par un canal déployé : widget web, téléphonie, plateforme de centre de contact"}
    - {from: cx, to: ds, text: "L'agent récupère la réponse dans la base de connaissances et la cite"}
    - {from: cx, to: tools, from_offset: -20, text: "Appel d'un outil : API métier décrite en OpenAPI, webhook, serveur MCP"}
    - {from: cx, to: bq, from_offset: 20, text: "Export de l'historique des conversations, base des évaluations et des tableaux de bord"}
    - {from: cx, to: human, from_offset: 20, text: "Transfert au conseiller humain quand l'escalade est déclenchée, avec le contexte de la conversation"}
captures:
  - image: https://docs.cloud.google.com/static/gemini-enterprise-cx/cx-agent-studio/images/get-started-agent-hierarchy.png
    page: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/quick/create-agent
    legende: "Hiérarchie d'un agent racine et de ses sous-agents dans le constructeur"
  - image: https://docs.cloud.google.com/static/gemini-enterprise-cx/cx-agent-studio/images/tracing.png
    page: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/simulator
    legende: "Simulateur : une question, les étapes d'exécution de l'agent (raisonnement, appel d'outil) avec leur durée, puis la réponse"
docs:
  Page produit: https://cloud.google.com/gemini-enterprise-cx/cx-agent-studio
  Documentation: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio
  Gemini Enterprise for CX: https://docs.cloud.google.com/gemini-enterprise-cx
  Mise en route: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/quick/setup
  Agents et sous-agents: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/agent
  Instructions: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/instruction
  Outils: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool
  Déploiement: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy
  Évaluation: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/evaluation
  Serveur MCP: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/mcp
  Bibliothèques clientes: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/libraries
  Dialogflow CX: https://docs.cloud.google.com/dialogflow/cx/docs
  Tarifs: https://cloud.google.com/products/conversational-agents/pricing
---

## Ce que c'est

Atelier de construction d'agents conversationnels à faible code, brique de **Gemini Enterprise for Customer Experience**. Une interface guidée sert à décrire l'agent, et le moteur mène la conversation au moment de l'exécution. La documentation le présente comme l'évolution de **Dialogflow CX**, et renvoie vers Dialogflow CX et Dialogflow ES pour les agents conversationnels historiques.

- **Construit sur l'Agent Development Kit** (ADK) : le même modèle d'agents, avec des simplifications, des intégrations et des garde-fous ajoutés pour l'usage en entreprise, sans exiger d'écrire du code.
- **Système multi-agents** : l'ensemble forme une **application d'agents**, arbre hiérarchique dont la racine — l'*agent de pilotage* — reçoit l'utilisateur, comprend l'objectif et délègue à des **sous-agents** spécialisés, qui peuvent eux-mêmes en appeler d'autres.
- **Instructions et outils** : chaque agent porte ses instructions en langage naturel et la liste des outils qu'il peut appeler. Des fonctions assistées par Gemini réécrivent les instructions dans une structure XML, en améliorent la clarté, ou génèrent l'ossature d'un agent à partir d'une description.
- **Comportement déterministe et génératif mêlés** : les parcours contraints coexistent avec la conversation libre, pour garder la main sur les étapes qui l'exigent.
- **Voix** : architecture de diffusion bidirectionnelle pour des échanges vocaux à faible latence ; les appels d'outils sont réellement asynchrones, la conversation continue pendant que l'outil travaille.
- **Exploitation** : garde-fous (*guardrails*), transfert à un conseiller, historique des conversations, jeux de tests et évaluations, journal des modifications détaillé, retour arrière en un clic et alertes de conflit pour le travail à plusieurs.
- **Déploiement par canal** : widget web, API, téléphonie Google, plateformes de centre de contact et opérateurs tiers (Twilio, Five9, AudioCodes), avec répartition du trafic entre versions.

## À quoi ça sert

- Agent de service client en libre-service, écrit et maintenu par une équipe métier plutôt que par des développeurs.
- Serveur vocal interactif moderne : accueil téléphonique conversationnel, qualification, passage au conseiller avec le contexte.
- Agent commercial ou d'assistance branché sur les API métier, capable d'agir et pas seulement de répondre.
- Reprise d'un agent Dialogflow CX existant sur un socle qui apporte évaluation, versions et canaux gérés.

**À éviter** quand l'agent doit s'intégrer à du code applicatif, être testé et livré par la chaîne CI/CD du dépôt : écrire l'agent avec l'ADK et le déployer sur Agent Runtime dans [Agent Platform](#gemini-enterprise-agent-platform). À éviter aussi pour un assistant interne aux salariés, branché sur les outils de l'entreprise : c'est le terrain de [Gemini Enterprise app](#gemini-enterprise-app).

## Alternatives en logiciel libre

- **Rasa** (Rasa Open Source) : le cadre libre de référence pour les agents conversationnels, avec gestion explicite du dialogue, actions personnalisées et jeux de tests.
- **Botpress** : constructeur visuel de flux conversationnels, le plus proche de l'atelier graphique.
- **Agent Development Kit** (ADK) : le cadre d'agents de Google est lui-même publié en open source ; il sert de socle à cet atelier et s'exécute où l'on veut.
- **LangGraph** (LangChain) : orchestration d'agents comme un graphe d'états, pour reproduire un système multi-agents avec des parcours contraints.
- **Asterisk** ou **FreeSWITCH**, couplés à un moteur de reconnaissance vocale libre (**Whisper**) et à une synthèse vocale libre, pour le volet téléphonie.
