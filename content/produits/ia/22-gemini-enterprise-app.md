---
title: Gemini Enterprise app
subgroup: Agents
icon: categories/agents
aka: Google Agentspace
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 250, y: 8, w: 500, h: 284}
  nodes:
    saas: {label: SaaS tiers, sub: "SharePoint, Jira", external: true, x: 8, y: 26, w: 170}
    ws: {label: Google Workspace, sub: "Drive, Agenda", external: true, x: 8, y: 110, w: 170}
    emp: {label: Employés, sub: "web, mobile", external: true, x: 8, y: 216, w: 170}
    ge: {label: Gemini Enterprise, sub: "assistant + recherche", icon: categories/agents, focus: true, x: 270, y: 96, w: 220, h: 76}
    agents: {label: Agents, sub: "galerie, agents maison", icon: categories/agents, x: 540, y: 26, w: 200}
    ap: {label: Agent Platform, sub: "agent ADK déployé", icon: produits/vertex-ai, x: 540, y: 196, w: 200}
  flows:
    - {from: saas, to: ge, to_offset: -22, text: "Un connecteur synchronise chaque type d'entité dans son propre data store, en conservant les droits d'accès de la source"}
    - {from: ws, to: ge, text: "Même chose pour les sources Google : Drive, Gmail, Agenda, Chat"}
    - {from: emp, to: ge, to_offset: 22, text: "Le salarié cherche et dialogue dans l'application web ou mobile ; il ne voit que ce à quoi il a droit"}
    - {from: ge, to: agents, from_offset: -22, text: "L'assistant délègue la tâche à un agent de la galerie ou à un agent construit dans Workflow Builder"}
    - {from: ap, to: ge, to_offset: 22, text: "Un agent développé avec l'ADK et déployé sur Agent Runtime est enregistré dans l'application"}
    - {from: ge, to: saas, from_side: top, to_side: bottom, text: "Action dans l'outil connecté : créer un ticket, modifier un enregistrement, poser un évènement d'agenda"}
captures:
  - image: https://docs.cloud.google.com/static/gemini/enterprise/docs/images/assistant/assistant-sources.png
    page: https://docs.cloud.google.com/gemini/enterprise/docs/assistant-chat
    legende: "Réponse de l'assistant Gemini Enterprise, avec le volet des sources citées"
  - image: https://docs.cloud.google.com/static/gemini/enterprise/docs/images/assistant/assistant-chat.png
    page: https://docs.cloud.google.com/gemini/enterprise/docs/assistant-chat
    legende: "Page d'accueil de Gemini Enterprise : une question saisie, les sources de données connectées et les agents"
docs:
  Page produit: https://cloud.google.com/gemini-enterprise
  Documentation: https://docs.cloud.google.com/gemini/enterprise/docs
  Concepts: https://docs.cloud.google.com/gemini/enterprise/docs/concepts
  Éditions: https://docs.cloud.google.com/gemini/enterprise/docs/editions
  Galerie d'agents: https://docs.cloud.google.com/gemini/enterprise/docs/agent-gallery
  Guide du développeur: https://docs.cloud.google.com/gemini/enterprise/docs/developer-guide
  API REST: https://docs.cloud.google.com/gemini/enterprise/docs/reference/rest
  API RPC: https://docs.cloud.google.com/gemini/enterprise/docs/reference/rpc
  Bibliothèques clientes: https://docs.cloud.google.com/gemini/enterprise/docs/libraries
  Quotas et dépassements: https://docs.cloud.google.com/gemini/enterprise/docs/quotas-and-overages
  Tarifs: https://cloud.google.com/pricing/list
  Notes de version: https://docs.cloud.google.com/gemini/enterprise/docs/release-notes
---

## Ce que c'est

Application destinée aux salariés : moteur de recherche d'entreprise, assistant conversationnel et plateforme d'agents dans une même interface web et mobile. Elle se branche sur les sources de données de l'organisation et rend des réponses ancrées dans ce contenu, en respectant les droits de chacun.

- **Sources et data stores.** Des connecteurs prêts à l'emploi couvrent les applications Google et les applications tierces courantes — SharePoint, Jira Cloud, Confluence Cloud, ServiceNow. Chaque type d'entité d'une source (les tickets, les pièces jointes, les commentaires...) est synchronisé dans son propre **data store**.
- **App.** Une application relie un ou plusieurs data stores et sert la recherche, les réponses et les agents aux utilisateurs. Plusieurs data stores sur une même application, c'est la recherche mixte.
- **Assistant.** La zone de dialogue intégrée répond aux questions et aux relances, cite ses sources, analyse les documents et images déposés, génère du texte et des images, et produit des rapports de recherche.
- **Actions.** Au-delà de la lecture, l'assistant peut écrire dans les sources connectées : créer un évènement d'agenda, modifier un ticket. Les actions s'activent à la création du data store ou après coup.
- **Agents et compétences.** La **galerie d'agents** propose des agents prêts à l'emploi ; **Workflow Builder** sert à en construire ; un agent développé ailleurs, par exemple avec l'ADK sur [Agent Platform](#gemini-enterprise-agent-platform), s'enregistre dans l'application. Les **compétences** (*skills*) sont des instructions réutilisables que les utilisateurs créent et partagent sans écrire de code.
- **Mesure.** Un tableau de bord Looker donne l'usage, la qualité des recherches et l'engagement ; l'observabilité expose les traces d'exécution bout en bout et les journaux d'audit.
- **Éditions et facturation.** Business, Standard, Plus, Frontline et *pay-as-you-go* : l'achat se fait par postes utilisateurs, avec un quota de stockage et d'indexation mutualisé qui dépend de l'édition, et des fonctionnalités qui s'ajoutent d'une édition à l'autre.

> [!WARNING]
> L'indexation conserve les autorisations de la source : un document que l'utilisateur n'a pas le droit de lire ne remonte ni en résultat ni en citation. Les droits mal réglés dans la source se retrouvent tels quels dans l'assistant, en plus visibles.

## À quoi ça sert

- Recherche unique sur l'ensemble du patrimoine documentaire, quel que soit l'outil où il vit.
- Assistant interne : questions sur les procédures, synthèse de documents, rédaction, génération d'images et de rapports.
- Point d'entrée unique des agents de l'entreprise, plutôt qu'un assistant par outil.
- Automatisation de tâches administratives par des actions dans les outils connectés.

**À éviter** pour intégrer de la recherche ou une réponse générée dans une application maison : c'est [Agent Search](#agent-search) qui expose l'API. À éviter aussi pour un agent destiné aux clients, sur un canal public ou téléphonique : voir [Customer Experience Agent Studio](#customer-experience-agent-studio). Enfin, pour une analyse approfondie d'un petit corpus choisi à la main, Gemini Notebook Enterprise est le produit prévu.

## Alternatives en logiciel libre

- **Onyx** (anciennement Danswer) : assistant et recherche d'entreprise open source, avec connecteurs vers les outils SaaS et réponses citées ; l'équivalent le plus direct.
- **LibreChat** (licence MIT) : interface de chat multi-modèles avec documents attachés et RAG, à poser devant un moteur d'inférence local.
- **Haystack**, **LlamaIndex** : pour assembler soi-même la chaîne connecteurs → index → réponses ancrées.
- **Qdrant**, **Weaviate**, **OpenSearch** : l'index de recherche et de vecteurs sous une telle chaîne.
- **Apache Airflow** ou **Meltano** : synchronisation périodique des sources SaaS vers l'index, à la place des connecteurs gérés.
