---
title: Knowledge Catalog
subgroup: Analytique
icon: categories/data-analytics
aka: Dataplex Universal Catalog
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 176, y: 16, w: 570, h: 308}
  nodes:
    ext: {label: Bases externes, sub: "Oracle, Collibra", external: true, x: 8, y: 44, w: 156}
    users: {label: Analystes, sub: "recherche sémantique", external: true, x: 8, y: 152, w: 156}
    gcs: {label: Cloud Storage, sub: "PDF, images bruts", icon: produits/cloud-storage, x: 196, y: 40, w: 200}
    kc: {label: Knowledge Catalog, sub: "entrées, aspects, lignage", icon: categories/data-analytics, focus: true, x: 196, y: 140, w: 250, h: 76}
    bq: {label: BigQuery, sub: "datasets, tables", icon: produits/bigquery, x: 196, y: 252, w: 200}
    agent: {label: Agent IA, sub: "MCP, Context API", icon: categories/agents, x: 546, y: 150, w: 180}
  flows:
    - {from: bq, to: kc, text: "Les datasets et tables BigQuery sont catalogués automatiquement : schémas, colonnes, descriptions générées"}
    - {from: gcs, to: kc, to_offset: -40, text: "Les analyses de découverte parcourent les fichiers non structurés et en extraient entités et relations"}
    - {from: ext, to: kc, to_offset: 40, text: "La connectivité gérée importe les métadonnées de systèmes externes sans pipeline à écrire"}
    - {from: kc, to: bq, from_offset: 60, to_offset: 60, control: true, text: "Les analyses de qualité et de profil s'exécutent sur les tables et publient leurs résultats dans le catalogue"}
    - {from: kc, to: users, text: "Recherche en langage naturel : l'analyste retrouve la table pertinente et sa définition métier"}
    - {from: kc, to: agent, text: "Un agent lit le contexte par serveur MCP ou par l'API Context, ce qui ancre ses réponses sur des définitions vérifiées"}
captures:
  - image: https://docs.cloud.google.com/static/knowledge-catalog/images/graph-view-default.png
    page: https://docs.cloud.google.com/knowledge-catalog/docs/lineage-views
    legende: "Vue graphe du lignage : les tables amont et aval d'une table, avec ses colonnes"
  - image: https://docs.cloud.google.com/static/knowledge-catalog/images/analysis-tab.png
    page: https://docs.cloud.google.com/knowledge-catalog/docs/data-profiling-overview
    legende: "Résultats d'une analyse de profil : configuration du scan, statistiques et valeurs les plus fréquentes par colonne"
docs:
  Page produit: https://cloud.google.com/products/knowledge-catalog
  Documentation: https://docs.cloud.google.com/knowledge-catalog/docs
  Présentation: https://docs.cloud.google.com/knowledge-catalog/docs/introduction
  Recherche d'assets: https://docs.cloud.google.com/knowledge-catalog/docs/search-assets
  API REST: https://docs.cloud.google.com/knowledge-catalog/docs/reference/rest
  API REST Data Lineage: https://docs.cloud.google.com/knowledge-catalog/docs/reference/data-lineage/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/dataplex
  Bibliothèques clientes: https://docs.cloud.google.com/knowledge-catalog/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/dataplex/latest
  Quotas et limites: https://docs.cloud.google.com/knowledge-catalog/docs/quotas
  Tarifs: https://cloud.google.com/products/knowledge-catalog/pricing
  Notes de version: https://docs.cloud.google.com/knowledge-catalog/docs/release-notes
---

## Ce que c'est

Catalogue de données et couche de gouvernance : il recense les actifs d'un patrimoine de données, leur attache un sens métier, mesure leur qualité et restitue ce contexte aux humains comme aux agents. L'API, la CLI et les rôles IAM gardent leur préfixe `dataplex`.

- **Métadonnées** : le modèle repose sur des **entrées** (*entries*), regroupées en **groupes d'entrées**, décrites par des **aspects** — des blocs de métadonnées typés par un **type d'aspect**, dont on peut définir les siens. Des **liens d'entrées** relient deux entrées entre elles.
- **Agrégation** : catalogage automatique de BigQuery, AlloyDB, Spanner, Cloud Storage ; **connectivité gérée** pour importer les schémas de systèmes externes (Oracle, PostgreSQL, registres partenaires) ; ingestion des tableaux de bord et du LookML de Looker.
- **Lignage** : suivi des transformations jusqu'au niveau de la colonne, alimenté automatiquement par BigQuery, [Cloud Data Fusion](#cloud-data-fusion), [Datastream](#datastream) et les jobs Spark, et consultable en vue graphe ou en liste.
- **Qualité et profil** : des *scans* planifiés ou à la demande calculent des statistiques par colonne et vérifient des règles de qualité ; les résultats peuvent être publiés dans le catalogue et servir de signal de confiance.
- **Sens métier** : **glossaires** d'entreprise pour normaliser le vocabulaire, descriptions de tables et de colonnes générées par Gemini puis relues, **produits de données** qui empaquettent un ensemble d'actifs avec leur contrat et leur propriétaire.
- **Restitution** : recherche sémantique en langage naturel dans la console, **serveurs MCP** et **API Context** (`LookupContext`) pour fournir ce contexte à une application ou à un agent.
- **Produits de données** (*data products*) : un ensemble d'*assets* choisis et documentés — tables, vues, modèles — publié pour être trouvé et partagé, avec ses règles d'accès ; les *assets* d'un produit sont dans la même région que lui. Les *lakes* et *zones* (regroupement des données par domaine) existent dans l'API, sans être décrits dans la documentation actuelle.
- **Facturation** : à l'unité de calcul (*Data Compute Unit*, DCU), en palier **standard** (découverte) ou **premium** (lignage, qualité, profil), plus le stockage des métadonnées. 100 DCU-heures de palier standard sont offertes chaque mois. Les fonctions assistées par Gemini sont facturées avec Gemini dans BigQuery.

## À quoi ça sert

- Répondre à « où est la donnée dont j'ai besoin, d'où vient-elle et peut-on s'y fier ? » sans passer par un tableur de recensement tenu à la main.
- Analyse d'impact avant un changement de schéma : le lignage au niveau colonne montre ce qui casse en aval.
- Contrôle continu de la qualité : règles versionnées, scans planifiés, alertes sur les écarts.
- Ancrer des agents et des applications d'IA générative sur des définitions vérifiées plutôt que sur des schémas recopiés dans un prompt — c'est ce dont se servent les [agents de données BigQuery](#data-analytics-agents).

**À éviter** comme outil de contrôle d'accès : Knowledge Catalog décrit et gouverne les métadonnées, mais les droits restent portés par IAM, les *policy tags* et la sécurité au niveau ligne ou colonne de BigQuery. Pour le chiffrement et la détection de données sensibles, c'est Sensitive Data Protection. Pour publier des données hors de l'organisation, avec abonnement et contrôle de l'export, c'est le partage BigQuery (voir [Partager des données](#partager-des-donnees)) : Knowledge Catalog sert la découverte interne, et indexe les datasets partagés.

## Alternatives en logiciel libre

- **DataHub** : catalogue et lignage au niveau colonne, avec un modèle de métadonnées extensible ; l'équivalent le plus complet.
- **OpenMetadata** : catalogue, qualité des données, glossaire métier et lignage, avec une intégration native de nombreuses sources.
- **Apache Atlas** : catalogue et lignage de l'écosystème Hadoop, toujours répandu sur les plateformes existantes.
- **Great Expectations** : contrôle de qualité des données par règles, l'équivalent des scans de qualité.
- **OpenLineage** : format et collecteurs de lignage ouverts, que DataHub, OpenMetadata et Marquez savent consommer.
