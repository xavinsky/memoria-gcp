---
title: Data Studio
subgroup: BI
icon: categories/business-intelligence
aka: Looker Studio
schema:
  size: [760, 330]
  zones:
    - {label: Google Cloud, x: 16, y: 40, w: 250, h: 200}
  nodes:
    bq: {label: BigQuery, sub: "tables, vues", icon: produits/bigquery, x: 36, y: 70, w: 210}
    looker: {label: Looker, sub: "modèle LookML", icon: produits/looker, x: 36, y: 150, w: 210}
    ext: {label: Sources tierces, sub: "Sheets, Ads, CSV", external: true, x: 36, y: 266, w: 210}
    ds: {label: Data Studio, sub: "sources + rapports", icon: produits/looker, focus: true, x: 330, y: 150, w: 220, h: 70}
    viewers: {label: Lecteurs, sub: "rapport partagé", external: true, x: 620, y: 60, w: 130}
    site: {label: Site web, sub: "rapport intégré", external: true, x: 620, y: 160, w: 130}
    mail: {label: Messagerie, sub: "envoi planifié", external: true, x: 620, y: 260, w: 140}
  flows:
    - {from: bq, to: ds, to_side: top, text: "Le connecteur BigQuery interroge les tables en direct ; BI Engine accélère les rapports les plus consultés"}
    - {from: looker, to: ds, text: "Le connecteur Looker expose le modèle LookML : les mesures gardent la définition du modèle sémantique"}
    - {from: ext, to: ds, to_side: bottom, text: "Sheets, Google Ads, Analytics, bases SQL, fichiers CSV et connecteurs communautaires"}
    - {from: ds, to: viewers, from_offset: -20, text: "Le rapport est partagé par lien ou par e-mail ; les lecteurs filtrent sans droits sur la source"}
    - {from: ds, to: site, text: "Le rapport est intégré dans une page web par une iframe ou un code d'intégration"}
    - {from: ds, to: mail, from_offset: 20, text: "Livraison planifiée : le rapport part en PDF selon un calendrier"}
captures:
  - image: https://docs.cloud.google.com/static/data-studio/images/add-data-to-report.png
    page: https://docs.cloud.google.com/data-studio/quick-start-guide
    legende: "Éditeur de rapport : barre d'outils d'ajout de graphiques et panneau d'ajout de données, onglets « Se connecter aux données » et « Mes sources de données »"
docs:
  Page produit: https://cloud.google.com/data-studio
  Documentation: https://docs.cloud.google.com/data-studio
  Prise en main: https://docs.cloud.google.com/data-studio/quick-start-guide
  Sources de données: https://docs.cloud.google.com/data-studio/about-data-sources
  Connecteurs disponibles: https://docs.cloud.google.com/data-studio/available-connectors
  Connecteurs communautaires: https://docs.cloud.google.com/data-studio/about-community-connectors
  Champs calculés: https://docs.cloud.google.com/data-studio/about-calculated-fields
  Liste des fonctions: https://docs.cloud.google.com/data-studio/function-list
  Types de graphiques: https://docs.cloud.google.com/data-studio/types-of-charts
  Data Studio Pro: https://docs.cloud.google.com/data-studio/about-pro
  Documentation développeur: https://developers.google.com/data-studio
  Tarifs: https://cloud.google.com/looker/pricing
  Notes de version: https://docs.cloud.google.com/data-studio/release-notes
---

## Ce que c'est

Outil de rapports et de tableaux de bord accessible à tout titulaire d'un compte Google, sur `datastudio.google.com`. L'édition se fait par glisser-déposer dans un canevas, sans écrire de code.

- **Sources de données.** Un rapport s'appuie sur des sources, chacune produite par un **connecteur** : connecteurs Google (BigQuery, Cloud SQL, Cloud Storage, Sheets, Ads, Analytics, Search Console, YouTube), connecteurs partenaires et **connecteurs communautaires** écrits en Apps Script. Plus de mille sources sont atteignables au total. La source expose des **dimensions** et des **métriques**, que l'on complète par des champs calculés.
- **Connecteur Looker.** Une source peut pointer vers une exploration [Looker](#looker) : les mesures conservent alors la définition du modèle sémantique au lieu d'être recalculées dans le rapport.
- **Fusion de données** (*blending*) : jusqu'à cinq sources jointes dans un même graphique sur des clés communes.
- **Rapports** : pages, graphiques (séries temporelles, barres, tableaux croisés, cartes géographiques), contrôles interactifs de filtre et de période, thèmes et mise en forme. Un rapport se partage par lien, s'intègre en iframe dans une page web, et s'envoie par e-mail à échéance régulière.
- **Identifiants.** Une source s'interroge soit avec les identifiants du **propriétaire** — les lecteurs voient les données sans avoir de droits dessus — soit avec ceux du **lecteur**. Ce choix détermine toute la sécurité du rapport.
- **Data Studio Pro**, l'abonnement payant, ajoute la propriété des contenus par l'organisation (rattachés à un projet Google Cloud et gérés par IAM), les espaces de travail d'équipe, les liens de rapport personnels, jusqu'à 200 planifications d'envoi et la livraison vers Google Chat, les alertes sur seuil, les clés de chiffrement gérées par le client, la résidence des données, l'application mobile Looker, Gemini dans Data Studio et l'accès au support Cloud Customer Care.

> [!WARNING]
> Un rapport interrogeant BigQuery avec les identifiants du propriétaire facture les requêtes au projet de celui-ci, à chaque ouverture et à chaque changement de filtre. Prévoir la mise en cache, des tables agrégées ou BI Engine.

## À quoi ça sert

- Tableau de bord rapide sur une source unique ou un jeu déjà agrégé : suivi de campagne, trafic d'un site, indicateurs d'une équipe.
- Restitution publique ou externe : un rapport intégré dans une page web, ouvrable sans compte Google.
- Prototypage d'une visualisation avant de l'industrialiser ailleurs.
- Couche de présentation gratuite au-dessus de [BigQuery](#bigquery) pour des besoins ponctuels.

**À éviter** dès qu'il faut une définition partagée et gouvernée des indicateurs, des droits fins par utilisateur ou des dizaines de rapports cohérents entre eux : c'est le terrain de [Looker](#looker). À éviter aussi comme outil de transformation : les champs calculés et la fusion ne remplacent pas un modèle préparé dans l'entrepôt, et un rapport posé sur une table brute volumineuse devient vite lent et coûteux.

**Connected Sheets** est à préférer quand le public travaille dans Google Sheets et veut construire ses propres analyses : la feuille se connecte à une table, une vue ou une requête enregistrée BigQuery, et ses tableaux croisés, formules et graphiques portent sur toute la table, chaque calcul étant exécuté par BigQuery et facturé au projet choisi. Ni SQL ni nouvel outil à apprendre. Data Studio reste le bon choix pour un rapport mis en forme, diffusé largement ou intégré à une page web. Limites de lignes et droits : voir [Partager des données](#partager-des-donnees).

## Alternatives en logiciel libre

- **Metabase** (édition open source) : questions en libre-service, tableaux de bord et partage par lien ; l'équivalent le plus direct.
- **Apache Superset** : exploration SQL, bibliothèque de visualisations riche, tableaux de bord filtrables.
- **Grafana** : tableaux de bord et alertes, fort sur les séries temporelles et les sources hétérogènes.
- **Redash** : rapports construits à partir de requêtes SQL enregistrées, avec planification.
- **Evidence** : rapports générés depuis des fichiers Markdown et SQL, versionnés comme du code.
