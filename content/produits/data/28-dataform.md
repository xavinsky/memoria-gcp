---
title: Dataform
subgroup: Analytique
icon: categories/data-analytics
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 290}
  nodes:
    git: {label: Dépôt Git, sub: "GitHub, GitLab", external: true, x: 10, y: 126, w: 150}
    raw: {label: BigQuery, sub: "tables sources", icon: produits/bigquery, x: 195, y: 30, w: 210}
    df: {label: Dataform, sub: "dépôt, SQLX, graphe", icon: categories/data-analytics, focus: true, x: 195, y: 120, w: 210, h: 70}
    out: {label: BigQuery, sub: "tables, vues, assertions", icon: produits/bigquery, x: 195, y: 236, w: 210}
    sched: {label: Workflow config, sub: "release + planning", icon: categories/data-analytics, x: 480, y: 30, w: 210}
    agent: {label: Data Engineering Agent, sub: "prompts, correctifs", icon: categories/agents, x: 480, y: 126, w: 230}
    bi: {label: Looker, sub: "tableaux de bord", icon: produits/looker, x: 480, y: 236, w: 210}
  flows:
    - {from: raw, to: df, text: "Le workflow déclare ses sources : des tables BigQuery déjà chargées, jamais créées par Dataform"}
    - {from: git, to: df, text: "L'espace de développement est une copie de travail versionnée, poussée vers la branche distante"}
    - {from: agent, to: df, control: true, text: "L'agent d'ingénierie des données écrit et corrige les fichiers SQLX à partir de prompts en français"}
    - {from: sched, to: df, to_offset: -20, control: true, text: "Une configuration de workflow déclenche l'exécution planifiée d'une configuration de release"}
    - {from: df, to: out, text: "Dataform compile les SQLX en requêtes et les lance dans BigQuery, dans l'ordre du graphe de dépendances"}
    - {from: out, to: bi, text: "Les tables et vues produites alimentent le reporting"}
docs:
  Page produit: https://cloud.google.com/dataform
  Documentation: https://docs.cloud.google.com/dataform/docs
  Présentation: https://docs.cloud.google.com/dataform/docs/overview
  Workflows: https://docs.cloud.google.com/dataform/docs/sql-workflows
  Référence Dataform core: https://docs.cloud.google.com/dataform/docs/reference/dataform-core-reference
  API REST: https://docs.cloud.google.com/dataform/reference/rest
  Bibliothèques clientes: https://docs.cloud.google.com/dataform/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/dataform/latest
  CLI Dataform: https://docs.cloud.google.com/dataform/docs/use-dataform-cli
  Serveur MCP: https://docs.cloud.google.com/dataform/docs/use-dataform-mcp
  Quotas et limites: https://docs.cloud.google.com/dataform/docs/quotas
  Tarifs: https://cloud.google.com/dataform/pricing
  Notes de version: https://docs.cloud.google.com/dataform/docs/release-notes
---

## Ce que c'est

Service de **transformation SQL** dans [BigQuery](#bigquery) : le *T* d'un pipeline ELT. Le code d'un entrepôt — tables, vues, tests — vit dans un dépôt versionné, et Dataform l'exécute dans le bon ordre.

- **Dataform core** : une extension de SQL écrite dans des fichiers **SQLX**. Chaque fichier contient un bloc `config` (type d'objet, description, schéma cible) et une requête `SELECT` ; Dataform en déduit le `CREATE OR REPLACE` correspondant.
- **Types d'objets** : déclaration de source, table, table incrémentale, vue, vue matérialisée, **assertion** (test de qualité), opération SQL brute, *includes* JavaScript pour factoriser variables et fonctions.
- **Dépendances** : une requête référence une autre table par `ref()` au lieu de son nom complet. Le graphe orienté acyclique qui en découle est visualisable (*Compiled graph*) et fixe l'ordre d'exécution.
- **Dépôts et espaces de travail** : un dépôt contient le code et peut être relié à un fournisseur Git tiers ; chaque développeur travaille dans un **espace de développement**, compile, teste, puis pousse ses commits.
- **Exécution** : manuelle sur tout le workflow, sur une sélection d'actions ou sur un **tag** ; planifiée par une **configuration de release** (qui produit un résultat de compilation) puis une **configuration de workflow** (qui choisit les actions et l'horaire). Les exécutions passent par un compte de service dédié au dépôt.
- **Environnements** : les *compilation overrides* d'un espace de travail ou d'une release redirigent la sortie vers un autre projet ou un autre suffixe de schéma, ce qui isole développement, recette et production.
- **Facturation** : le service est **gratuit** ; seules les requêtes lancées dans BigQuery et les journaux Cloud Logging sont facturés.

## À quoi ça sert

- Construire des couches successives dans BigQuery — brut, nettoyé, métier — avec des dépendances explicites plutôt qu'un empilement de requêtes planifiées.
- Faire entrer l'entrepôt dans une chaîne de revue : branches, *pull requests*, revue de code, environnements isolés.
- Tester les données en continu : les assertions s'exécutent après les tables qu'elles contrôlent et font échouer le workflow sur une ligne non conforme.
- Documenter les tables et les colonnes dans le même fichier que la requête qui les produit, et publier ces descriptions dans [Knowledge Catalog](#knowledge-catalog).

**À éviter** hors de BigQuery : Dataform ne sait compiler que du GoogleSQL et n'exécute rien ailleurs. Pour déplacer ou capter des données avant transformation, voir [Datastream](#datastream) ou [Cloud Data Fusion](#cloud-data-fusion) ; pour une transformation en Python ou sur des fichiers, [Managed Service for Apache Spark](#managed-service-for-apache-spark).

> [!TIP]
> Une table incrémentale ne retraite que les nouvelles lignes ; l'option **Run with full refresh** la reconstruit depuis zéro. C'est le réflexe après un changement de logique, sous peine de garder indéfiniment les lignes calculées par l'ancienne version.

## Alternatives en logiciel libre

- **dbt Core** (licence Apache 2.0) : le modèle dont Dataform est le plus proche — modèles SQL, `ref()`, tests, documentation, et des adaptateurs pour bien d'autres entrepôts que BigQuery.
- **SQLMesh** : transformation SQL avec environnements virtuels et détection des changements de colonne ; évite les reconstructions inutiles.
- **Apache Airflow** : orchestration générique, à compléter par un outil de transformation ; couvre la planification, pas la modélisation SQL.
- **Dagster** : orchestration orientée *assets*, avec lignage et contrôles de qualité intégrés.
