---
title: Memoria GCP
---

Memoria GCP est un aide-mémoire en français pour **utiliser l'IA avec les produits Google Cloud** :
choisir les services, les assembler en architecture, les déployer et les exploiter. Chaque page va
droit au but — matrices de choix, schémas, syntaxes, pièges — et renvoie vers la documentation
officielle pour le détail.

## L'objectif

Un modèle ou un agent ne sert à rien seul. En production, il lui faut des données propres et
accessibles, une identité et des droits, un endroit où s'exécuter, une chaîne de livraison, de la
surveillance et un budget tenu. Le site suit donc l'IA de bout en bout :

- **Le modèle** : choisir entre Gemini, un modèle ouvert de [Model Garden](#model-garden),
  [BigQuery ML](#bigquery-ml) ou un modèle entraîné soi-même ; l'appeler, l'ancrer dans ses données,
  l'évaluer, le régler.
- **L'agent** : le construire avec ADK, lui donner des outils par MCP, le faire dialoguer avec
  d'autres agents par A2A, le déployer.
- **Les données** qui l'alimentent : BigQuery, Cloud Storage, pipelines batch et *streaming*,
  gouvernance.
- **La plateforme** qui le porte : calcul, réseau, IAM, sécurité, observabilité, coûts.
- **Le poste du développeur**, où l'IA aide aussi à écrire et à déployer le code :
  [Gemini Code Assist](#gemini-code-assist), [Antigravity](#antigravity).

Les onglets thématiques aident à **choisir et concevoir** ; le catalogue des produits reste neutre
et décrit chaque service sans le comparer aux autres.

## Ce que contient le site

| Onglet | Ce qu'on y trouve | Pour commencer |
|---|---|---|
| Architectures Data | Choix d'une base, organisation de BigQuery, patterns batch, *streaming*, CDC, lakehouse, orchestration, partage | [Choisir une base de données](#choisir-une-base) |
| Architectures IA | Machine learning, IA générative (modèles, RAG, évaluation, réglage), agents (ADK, MCP, A2A) | [Choisir un modèle génératif](#choisir-un-modele) |
| DevOps | Chaîne CI/CD, connexion des dépôts, déploiement sans clé, Infrastructure as Code, outils tiers, poste de développement | [La chaîne CI/CD](#chaine-cicd) |
| Plateforme | Well-Architected Framework, fondations, facturation, résilience, calcul, réseau, IAM et sécurité, exploitation | [Le Well-Architected Framework](#well-architected) |
| Syntaxes | `gcloud`, `bq`, `gcloud storage`, GoogleSQL, BigQuery ML, Apache Beam, SDK `google-genai`, Pulumi, au format objectif → syntaxe → résultat | [gcloud : contexte et configuration](#gcloud-config) |
| APIs & SDK | Bibliothèques clientes Python, authentification, erreurs et quotas, APIs de parole, vision, langue et documents | [Bibliothèques clientes Python](#bibliotheques-clientes) |
| Produits | Une fiche par service : ce que c'est, à quoi ça sert, quand l'éviter, alternatives en logiciel libre, schéma d'intégration, liens vers la documentation | [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) |
| Lexique | Termes, sigles et anciens noms de produits, reliés à la section qui les détaille | [Lexique](#lexique) |
| Refs | Points d'entrée de la documentation officielle | [Documentation Google Cloud](#documentation-google-cloud) |

## Par où commencer

- **Appeler Gemini depuis une application** : [Choisir un modèle génératif](#choisir-un-modele),
  [Appeler Gemini depuis du code](#appeler-gemini), [Authentifier un appel](#authentifier-un-appel),
  [Évaluer et sécuriser](#evaluer-et-securiser).
- **Répondre à partir de ses propres documents** : [RAG](#rag), [Agent Search](#agent-search),
  [Document AI](#document-ai).
- **Construire un agent** : [Construire un agent avec ADK](#construire-un-agent),
  [MCP et A2A](#protocoles-mcp-a2a), [Déployer un agent](#deployer-un-agent).
- **Prédire à partir de données tabulaires** : [Choisir une approche ML](#choisir-une-approche-ml),
  [BigQuery ML](#bigquery-ml), [MLOps](#mlops).
- **Préparer le terrain** : [Organiser l'environnement](#hierarchie-des-ressources),
  [Fondations en code](#fondations-en-code), [Facturation et budgets](#facturation-et-budgets),
  [Quotas et limites](#quotas-et-limites).

## Lire une page

- Le badge [!PREVERSION] signale une fonction ou un produit en préversion : sans engagement de
  disponibilité, à éviter en production.
- Le badge [!DECONSEILLE] signale un élément hors de la pratique standard ou à la pérennité
  incertaine ; le texte dit quoi utiliser à la place.
- Le badge [!SOMMEIL] signale un projet libre sans activité depuis plus d'un an.
- Les valeurs à remplacer sont en majuscules : `PROJECT_ID`, `REGION`, `BUCKET`.
- Les schémas d'intégration des fiches produit numérotent les flux ; la légende sous le schéma
  décrit chaque étape.
- Touche `/` pour la recherche sur tout le site, touche `M` pour masquer ou afficher le menu.

## Sources

Les affirmations techniques — limites chiffrées, garanties, noms d'options — sont vérifiées dans la
documentation officielle de Google Cloud, citée en fin de chaque fiche. Les captures d'écran en
proviennent (licence CC BY 4.0). Memoria GCP est un site indépendant, sans lien avec Google. Le code
et le contenu sont sous licence MIT, sur
[GitHub](https://github.com/xavinsky/memoria-gcp).
