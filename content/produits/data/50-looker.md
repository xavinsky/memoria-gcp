---
title: Looker
subgroup: BI
icon: produits/looker
schema:
  size: [760, 350]
  zones:
    - {label: Projet GCP, x: 168, y: 16, w: 400, h: 318}
  nodes:
    git: {label: Dépôt Git, sub: "projet LookML", external: true, x: 16, y: 147, w: 140}
    looker: {label: Looker, sub: "instance + modèle LookML", icon: produits/looker, focus: true, x: 196, y: 140, w: 250, h: 70}
    bq: {label: BigQuery, sub: "entrepôt de données", icon: produits/bigquery, x: 196, y: 260, w: 250}
    users: {label: Analystes, sub: "explorations", external: true, x: 600, y: 60, w: 146}
    ds: {label: Data Studio, sub: "rapports", external: true, x: 600, y: 155, w: 146}
    app: {label: Application, sub: "iframe signée", external: true, x: 600, y: 250, w: 146}
  flows:
    - {from: git, to: looker, control: true, text: "Les développeurs versionnent le projet LookML ; l'instance déploie le modèle depuis la branche de production"}
    - {from: users, to: looker, to_offset: -12, text: "Les analystes explorent le modèle, enregistrent des Looks et composent des tableaux de bord"}
    - {from: looker, to: bq, from_offset: 60, to_offset: 60, text: "Le générateur SQL traduit chaque exploration en requête : les données restent dans l'entrepôt, rien n'est copié dans l'instance"}
    - {from: looker, to: bq, from_offset: -60, to_offset: -60, text: "Les tables dérivées persistantes (PDT) sont matérialisées dans un schéma de travail de l'entrepôt"}
    - {from: looker, to: ds, from_offset: 12, text: "Le connecteur BI expose le modèle sémantique à Data Studio et à Connected Sheets"}
    - {from: looker, to: app, from_offset: 30, text: "Tableau de bord embarqué : l'application affiche une iframe signée, filtrée selon l'utilisateur"}
captures:
  - image: https://docs.cloud.google.com/static/looker/docs/images/explore-viz-quick-guide-2408.png
    page: https://docs.cloud.google.com/looker/docs/creating-visualizations
    legende: "Une exploration : filtres, graphique en barres empilées avec son panneau d'édition, puis la table de résultats"
  - image: https://docs.cloud.google.com/static/looker/docs/images/looker-ide-2506.png
    page: https://docs.cloud.google.com/looker/docs/looker-ide
    legende: "IDE LookML en mode développement : fichiers du projet, une vue en cours d'édition et l'aide contextuelle"
docs:
  Page produit: https://cloud.google.com/looker
  Documentation: https://docs.cloud.google.com/looker/docs
  Looker (Google Cloud core): https://docs.cloud.google.com/looker/docs/looker-core-overview
  Introduction à LookML: https://docs.cloud.google.com/looker/docs/what-is-lookml
  Référence LookML: https://docs.cloud.google.com/looker/docs/reference/lookml-quick-reference
  Looker embarqué: https://docs.cloud.google.com/looker/docs/embed-overview
  API et SDK: https://docs.cloud.google.com/looker/docs/api-sdk
  APIs disponibles: https://docs.cloud.google.com/looker/docs/reference/available-apis
  API REST des instances: https://docs.cloud.google.com/looker/docs/reference/rest
  Commandes gcloud looker: https://docs.cloud.google.com/sdk/gcloud/reference/looker
  Bonnes pratiques: https://docs.cloud.google.com/looker/docs/best-practices/home
  Tarifs: https://cloud.google.com/looker/pricing
  Notes de version: https://docs.cloud.google.com/looker/docs/release-notes
---

## Ce que c'est

Plateforme de *business intelligence* bâtie sur un **modèle sémantique** : les indicateurs sont définis une fois en LookML, et toutes les requêtes en découlent. Les données restent dans la base interrogée, elles ne sont pas recopiées dans l'instance.

- **LookML** (*Looker Modeling Language*) décrit le modèle dans des fichiers versionnés en Git : les *views* définissent dimensions, mesures et calculs d'une table, les *models* déclarent la connexion et les jointures, les *explores* les points d'entrée offerts aux utilisateurs. Le langage est déclaratif, indépendant du dialecte SQL, et encourage l'écriture d'une expression SQL en un seul endroit.
- **Générateur SQL.** Quand un utilisateur choisit des dimensions, des mesures et des filtres dans une **exploration**, Looker en déduit la requête SQL, l'exécute sur la base et renvoie le résultat sous forme de table et de graphique. Un résultat enregistré est un *Look*, assemblé ensuite en tableaux de bord.
- **Tables dérivées persistantes** (PDT) : Looker matérialise une requête du modèle dans un schéma de travail de l'entrepôt et la rafraîchit selon un *datagroup*.
- **Développement.** Un environnement de développement par utilisateur, une validation du LookML, un IDE intégré et une extension VS Code ; le passage en production suit les branches du dépôt Git.
- **Looker (Google Cloud core)** est la forme provisionnée et administrée depuis la console Google Cloud, en éditions **Standard** (jusqu'à 50 utilisateurs internes), **Enterprise** (utilisateurs illimités, VPC Service Controls, Private Service Connect) et **Embed** (intégration signée, thèmes personnalisés, quotas d'API les plus élevés). L'édition se choisit à la création de l'instance et ne se change plus ensuite. Looker existe aussi hébergé par Looker ou par le client.
- **Embarquer Looker** : une iframe signée porte une visualisation, un tableau de bord ou une exploration entière dans une application, avec le SDK d'intégration pour piloter l'échange. Les droits de l'utilisateur hôte sont transmis dans l'URL signée.
- **Ouverture** : API REST pour tout ce que fait l'interface, SDK en plusieurs langages, *Action Hub* pour pousser des résultats vers des outils tiers, *extension framework* pour des applications internes, planifications et alertes sur seuil.

## À quoi ça sert

- Donner une définition unique et gouvernée des indicateurs de l'entreprise, sur laquelle tout le monde s'appuie.
- Analyse en libre-service : les métiers explorent sans écrire de SQL, sur un périmètre et des droits maîtrisés.
- Analytique opérationnelle : tableaux de bord suivis au quotidien, alertes, envois planifiés, actions déclenchées depuis un résultat.
- Analytique embarquée : exposer des tableaux de bord aux clients d'un produit, aux couleurs de l'application.
- Couche de présentation au-dessus de [BigQuery](#bigquery), mais aussi de Cloud SQL, Spanner, AlloyDB ou d'un entrepôt tiers.

**À éviter** pour un rapport ponctuel, une source unique ou un jeu de données déjà agrégé : la modélisation LookML ne se rentabilise que sur un patrimoine partagé et durable ; préférer [Data Studio](#data-studio). À éviter aussi comme moteur de calcul : Looker délègue tout à la base, un modèle posé sur un entrepôt mal partitionné produit des requêtes coûteuses.

> [!TIP]
> Un projet LookML est du code : branches, revues et tests s'y appliquent. Traiter le modèle comme un dépôt applicatif évite la dérive des définitions d'indicateurs.

## Alternatives en logiciel libre

- **Cube** : couche sémantique en amont des outils de visualisation, la plus proche de LookML dans l'esprit (licence Apache 2.0 pour le cœur).
- **dbt Core** : définit les transformations et les métriques en SQL versionné ; complète plutôt qu'il ne remplace la partie visualisation.
- **Apache Superset** : exploration et tableaux de bord sur un entrepôt SQL, avec un modèle de jeux de données plus léger.
- **Metabase** (édition open source) : questions en libre-service et tableaux de bord, orienté simplicité.
- **Lightdash** : construit ses explorations à partir des modèles dbt, ce qui en fait le rapprochement le plus direct avec la démarche Looker.
- **Grafana** : tableaux de bord opérationnels et alertes, quand l'usage penche vers la supervision.
