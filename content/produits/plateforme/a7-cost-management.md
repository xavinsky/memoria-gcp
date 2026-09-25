---
title: Cost Management
subgroup: Exploitation
icon: categories/management-tools
schema:
  size: [760, 340]
  zones:
    - {label: Organisation GCP, x: 150, y: 16, w: 598, h: 308}
  nodes:
    fin: {label: Équipe finance, sub: "alerte par e-mail", external: true, x: 8, y: 150, w: 140}
    proj: {label: Projets et ressources, sub: "consommation horaire", x: 170, y: 44, w: 180}
    budget: {label: Budget, sub: "seuils 50/90/100 %", icon: categories/management-tools, x: 170, y: 240, w: 170}
    cm: {label: Cost Management, sub: "compte de facturation", icon: categories/management-tools, focus: true, x: 400, y: 130, w: 190, h: 64}
    bq: {label: BigQuery, sub: "export de facturation", icon: produits/bigquery, x: 560, y: 40, w: 186}
    pubsub: {label: Pub/Sub, sub: "notification programmée", icon: categories/data-analytics, x: 390, y: 240, w: 196}
    looker: {label: Looker, sub: "rapport de coût", icon: produits/looker, x: 600, y: 240, w: 146}
  flows:
    - {from: proj, to: cm, text: "Chaque ressource consommée émet des lignes d'usage horaires, rattachées au projet puis au compte de facturation auquel il est lié."}
    - {from: budget, to: cm, control: true, text: "Un budget porte une portée — compte, projets, services, étiquettes — et des seuils exprimés en pourcentage du montant prévu."}
    - {from: cm, to: fin, text: "Le franchissement d'un seuil, sur la dépense constatée ou sur la dépense prévue, avertit les administrateurs de facturation."}
    - {from: cm, to: pubsub, text: "La même alerte part sur un sujet Pub/Sub, ce qui permet d'automatiser une réaction : arrêt d'un environnement, coupure d'un bac à sable."}
    - {from: cm, to: bq, text: "L'export de facturation alimente en continu des tables BigQuery : usage standard, usage détaillé par ressource et grille tarifaire."}
    - {from: bq, to: looker, text: "Ces tables sont la source des rapports de répartition : par équipe, par étiquette, par environnement, avec les remises réparties."}
captures:
  - image: https://docs.cloud.google.com/static/billing/docs/images/billing-reports3.png
    page: https://docs.cloud.google.com/billing/docs/how-to/reports
    legende: "Rapport de facturation : dépense cumulée du mois, prévision de fin de mois et économies réalisées"
  - image: https://docs.cloud.google.com/static/billing/docs/images/finops-hub-dashboard.png
    page: https://docs.cloud.google.com/billing/docs/how-to/finops-hub
    legende: "FinOps hub : score d'optimisation, économies réalisées et gaspillage potentiel du compte de facturation"
docs:
  Page produit: https://cloud.google.com/cost-management
  Documentation: https://docs.cloud.google.com/billing/docs
  Concepts de la facturation: https://docs.cloud.google.com/billing/docs/concepts
  Budgets et alertes: https://docs.cloud.google.com/billing/docs/how-to/budgets
  Notifications programmatiques: https://docs.cloud.google.com/billing/docs/how-to/budgets-programmatic-notifications
  Rapports de facturation: https://docs.cloud.google.com/billing/docs/how-to/reports
  Table des coûts: https://docs.cloud.google.com/billing/docs/how-to/cost-table
  Répartition des coûts: https://docs.cloud.google.com/billing/docs/how-to/cost-breakdown
  Grille tarifaire: https://docs.cloud.google.com/billing/docs/how-to/pricing-table
  Analyse des engagements: https://docs.cloud.google.com/billing/docs/how-to/cud-analysis
  FinOps hub: https://docs.cloud.google.com/billing/docs/how-to/finops-hub
  Export vers BigQuery: https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery
  Exemples de requêtes: https://docs.cloud.google.com/billing/docs/how-to/bq-examples
  Contrôle des accès: https://docs.cloud.google.com/billing/docs/how-to/billing-access
  API REST: https://docs.cloud.google.com/billing/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/billing
  Notes de version: https://docs.cloud.google.com/billing/docs/release-notes
---

## Ce que c'est

Ensemble des outils de suivi et de maîtrise de la dépense attachés au **compte de facturation** Cloud Billing : rapports, budgets, export de données, analyse des engagements. Le compte de facturation est l'objet central — il porte le moyen de paiement et la devise, et chaque projet lui est rattaché ; la dépense est toujours imputée au projet qui consomme, puis consolidée au compte.

- **Rapports.** Le rapport de facturation trace la dépense dans le temps, avec regroupement par projet, service, SKU, région, étiquette ou balise, filtres sur la période et le type de remise, et prévision de fin de mois. La **table des coûts** reprend ligne à ligne ce qui compose une facture ; la **répartition des coûts** montre l'effet des remises et des crédits sur le coût brut ; la **grille tarifaire** donne les prix négociés du compte.
- **Budgets et alertes.** Un budget porte une **portée** (tout le compte, une liste de projets, des services, des étiquettes), un montant fixe ou calé sur le mois précédent, et des **seuils** en pourcentage. Chaque seuil franchi — sur la dépense constatée ou sur la dépense prévue — déclenche un message aux administrateurs de facturation, et, s'il est configuré, un message sur un sujet [Pub/Sub](#pubsub) qui permet d'automatiser une réaction.
- **Export vers BigQuery.** Trois exports principaux alimentent des tables dans [BigQuery](#bigquery) : **usage standard** (`gcp_billing_export_v1_…`), **usage détaillé** avec la granularité par ressource (`gcp_billing_export_resource_v1_…`) et **tarifs**. Un export au format **FOCUS**, la spécification FinOps de description des coûts entre fournisseurs, s'y ajoute. C'est la seule voie pour croiser la dépense avec des données d'entreprise et pour garder un historique au-delà de ce que montrent les rapports.
- **Engagements et remises.** Les **remises sur engagement d'usage** (fondées sur la dépense ou sur les ressources) et les remises pour usage soutenu apparaissent dans les rapports, avec un rapport dédié qui mesure le taux de couverture et le taux d'utilisation des engagements souscrits.
- **FinOps hub.** Tableau de bord d'optimisation du compte de facturation : score, économies déjà réalisées, gaspillage potentiel et principales recommandations, alimentées par [Active Assist](#active-assist).
- **Répartition analytique.** Les **étiquettes** posées sur les projets et les ressources, et les **balises** définies au niveau de l'organisation, sont ce qui permet d'attribuer une dépense à une équipe ou à un produit. Elles n'ont d'effet qu'à partir du moment où elles sont posées : la dépense passée ne se réétiquette pas.
- **Facturation.** Les outils sont gratuits ; seul le stockage et l'interrogation des tables d'export dans [BigQuery](#bigquery) sont facturés.

> [!WARNING]
> Une alerte de budget n'arrête rien. Seul le plafond de dépense (*spend cap*) [!PREVERSION] met en pause un service éligible — Gemini API, Agent Platform, Cloud Run — et laisse facturer les ressources persistantes. Hors de ce cas, l'alerte informe ; c'est au destinataire, ou à une automatisation branchée sur [Pub/Sub](#pubsub), d'agir. Couper la facturation d'un projet à partir d'un message de budget est possible, mais détruit les ressources qui ne survivent pas à la déliaison : à réserver aux environnements jetables.

## À quoi ça sert

- Savoir où part la dépense, à la granularité du SKU et de la ressource, et la rattacher à une équipe par les étiquettes.
- Être averti avant la fin du mois quand la trajectoire de dépense dépasse le budget prévu.
- Bâtir une refacturation interne à partir des tables d'export dans [BigQuery](#bigquery), restituée dans [Looker](#looker) ou [Data Studio](#data-studio).
- Mesurer si les engagements souscrits sont bien consommés, et décider d'en reprendre ou non.
- Comparer une facture à la grille tarifaire du compte, et retrouver la ligne d'usage qui explique un écart.
- Automatiser une réaction sur un environnement non productif : arrêt des VM, réduction d'un cluster, coupure d'un bac à sable.

**À éviter** comme source unique de suivi en temps réel : les lignes d'usage arrivent avec plusieurs heures de retard, et une alerte de budget n'est pas un garde-fou instantané. Pour empêcher techniquement une consommation, ce sont les quotas ([Cloud Quotas](#cloud-quotas)) et les politiques d'organisation qui agissent. À éviter aussi de traiter les rapports de la console comme un entrepôt : dès qu'il s'agit d'historique long, de jointures avec des données métier ou de calculs de refacturation, c'est l'export BigQuery qu'il faut, pas l'interface.

## Alternatives en logiciel libre

- **OpenCost** (Apache 2.0) : spécification et implémentation CNCF de l'allocation de coût dans Kubernetes — par espace de noms, par charge de travail, par étiquette. L'équivalent le plus direct pour la partie conteneurs, y compris sur [GKE](#gke).
- **Infracost** (Apache 2.0) : estimation du coût d'un changement Terraform avant application, avec commentaire dans la *merge request* — la prévention que les budgets ne font qu'a posteriori.
- **Cloud Custodian** (Apache 2.0) : règles déclaratives qui inventorient, étiquettent, arrêtent ou suppriment les ressources selon des critères d'usage, pour automatiser ce qu'une alerte de budget se contente de signaler.
- **Apache Superset** (Apache 2.0) et **Grafana** (AGPL v3) : tableaux de bord bâtis sur les tables d'export de facturation, à la place des rapports de la console.
- **Steampipe** (AGPL v3) : interrogation en SQL de l'inventaire d'un compte cloud, base commode pour des rapports d'usage et de ressources oubliées.
- **FOCUS** (spécification sous licence CC BY 4.0) : le format ouvert de description des coûts que l'export Google Cloud sait produire, ce qui permet de comparer des fournisseurs avec les mêmes outils.
