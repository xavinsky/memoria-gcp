---
title: Carbon Footprint
subgroup: Exploitation
icon: categories/management-tools
schema:
  size: [760, 320]
  zones:
    - {label: Compte de facturation, x: 8, y: 16, w: 640, h: 288}
  nodes:
    svc: {label: Services consommés, sub: "calcul, stockage, réseau", x: 28, y: 44, w: 175}
    region: {label: Région, sub: "mix électrique local", x: 28, y: 130, w: 150}
    dash: {label: Tableau de bord, sub: "tCO2e par mois", icon: categories/management-tools, x: 270, y: 36, w: 180}
    cf: {label: Carbon Footprint, sub: "scopes 1, 2 et 3", icon: categories/management-tools, focus: true, x: 270, y: 110, w: 190, h: 64}
    bq: {label: BigQuery, sub: "table carbon_footprint", icon: produits/bigquery, x: 270, y: 224, w: 190}
    looker: {label: Data Studio, sub: "suivi mensuel", icon: produits/looker, x: 490, y: 224, w: 150}
    rse: {label: Rapport RSE, sub: "bilan annuel", external: true, x: 650, y: 110, w: 104}
  flows:
    - {from: svc, to: cf, text: "La consommation de chaque service est convertie en énergie, puis en émissions, au prorata de la part d'infrastructure attribuable à la charge."}
    - {from: region, to: cf, text: "L'intensité carbone du réseau électrique de la région et l'efficacité énergétique du centre de données entrent dans le calcul."}
    - {from: cf, to: dash, text: "Le tableau de bord du compte de facturation répartit les émissions par mois, par projet, par service et par région."}
    - {from: cf, to: bq, text: "Un transfert planifié écrit chaque mois une table partitionnée carbon_footprint, avec les trois scopes du protocole GHG."}
    - {from: bq, to: looker, text: "Les données alimentent un suivi périodique, croisé avec la dépense et avec l'activité réelle de l'entreprise."}
    - {from: looker, to: rse, text: "Le résultat consolidé rejoint le reporting extra-financier de l'organisation."}
docs:
  Page produit: https://cloud.google.com/carbon-footprint
  Documentation: https://docs.cloud.google.com/carbon-footprint/docs/view-carbon-data
  Méthodologie: https://docs.cloud.google.com/carbon-footprint/docs/methodology
  Export vers BigQuery: https://docs.cloud.google.com/carbon-footprint/docs/export
  Schéma des données: https://docs.cloud.google.com/carbon-footprint/docs/data-schema
  Services couverts: https://docs.cloud.google.com/carbon-footprint/docs/covered-services
  Tableau de bord personnalisé: https://docs.cloud.google.com/carbon-footprint/docs/custom-dashboard
  Contrôle des accès: https://docs.cloud.google.com/carbon-footprint/docs/iam
  API: https://docs.cloud.google.com/carbon-footprint/docs/api
  Problèmes connus: https://docs.cloud.google.com/carbon-footprint/docs/issues
  Notes de version: https://docs.cloud.google.com/carbon-footprint/docs/release-notes
---

## Ce que c'est

Rapport d'émissions de gaz à effet de serre associé à l'usage de Google Cloud, rattaché à un **compte de facturation**. Il ne mesure rien directement : il répartit les émissions de l'infrastructure de Google entre les clients, au prorata de la consommation facturée, selon une méthodologie publiée et alignée sur le **GHG Protocol**.

- **Trois scopes.** Le **scope 1** couvre les combustions directes de Google, le **scope 2** l'électricité achetée, le **scope 3** la chaîne de valeur, dont la fabrication et le transport du matériel. Le scope 2 est donné sous deux formes : **basé sur le marché** (tenant compte des contrats d'achat d'énergie renouvelable) et **basé sur la localisation** (intensité carbone réelle du réseau électrique régional).
- **Ce qui entre dans le calcul.** La consommation de chaque service, la part d'infrastructure qui lui est attribuable, l'efficacité énergétique du centre de données et l'intensité carbone horaire du réseau de la région. Le choix de la région pèse donc directement sur le résultat, à charge identique.
- **Granularité.** Mois, projet, service et région, en tonnes équivalent CO2 (tCO2e) dans le tableau de bord, en kilogrammes (kgCO2e) dans l'export. Chaque ligne porte la version du modèle de calcul utilisé.
- **Délai.** Les données d'un mois deviennent disponibles jusqu'à 21 jours après sa fin. Ce n'est pas un indicateur d'exploitation courante.
- **Export.** Un transfert planifié par BigQuery Data Transfer Service crée une table mensuelle partitionnée `carbon_footprint` dans le jeu de données choisi, alimentée le 15 de chaque mois. Un remplissage rétroactif permet de remonter jusqu'à janvier 2021.
- **Accès.** La lecture demande la permission `billing.accounts.getCarbonInformation` sur le compte de facturation, distincte des droits de consultation des coûts.
- **Périmètre.** Seuls les services couverts sont comptabilisés ; la liste figure dans la méthodologie et s'étend au fil des versions du modèle.
- **Facturation.** Le rapport et son export sont gratuits ; seules les tables créées dans [BigQuery](#bigquery) sont facturées.

> [!TIP]
> Le levier le plus immédiat n'est pas de consommer moins mais de consommer ailleurs : à charge égale, l'écart d'intensité carbone entre deux régions Google Cloud se compte en facteurs, pas en pourcentages. Le comparer avant de choisir une région coûte moins cher que de migrer ensuite.

## À quoi ça sert

- Alimenter un bilan d'émissions d'entreprise avec une source rattachée au fournisseur plutôt qu'à une estimation maison.
- Comparer des régions avant de placer une charge, ou justifier le déplacement d'un traitement par lots vers une région moins carbonée.
- Attribuer les émissions à une équipe ou à un produit, en s'appuyant sur le même découpage par projet que la facturation.
- Suivre l'effet d'une optimisation d'infrastructure — arrêt de ressources inutilisées, redimensionnement — sur les émissions et non seulement sur la facture.
- Répondre à une demande de reporting extra-financier avec une série mensuelle historisée dans [BigQuery](#bigquery).

**À éviter** comme instrument de pilotage au jour le jour : la donnée arrive avec trois semaines de retard et au pas mensuel, ce qui exclut toute boucle de rétroaction courte. À éviter aussi comme bilan carbone complet d'un système d'information : le périmètre s'arrête aux services Google Cloud couverts — ni les postes de travail, ni les réseaux d'accès, ni les équipements sur site, ni les fournisseurs tiers n'y figurent. Enfin, les chiffres sont des estimations issues d'un modèle d'allocation : ils se comparent dans le temps et entre régions, mais ne se confrontent pas terme à terme à ceux d'un autre fournisseur, dont la méthodologie diffère.

## Alternatives en logiciel libre

- **Cloud Carbon Footprint** (Apache 2.0) : outil de Thoughtworks qui estime les émissions à partir des exports de facturation de Google Cloud, AWS et Azure, avec une méthodologie publiée — l'équivalent le plus direct, et le seul qui couvre plusieurs fournisseurs de la même façon.
- **Kepler** (Apache 2.0) : mesure de la consommation énergétique des pods Kubernetes par eBPF et compteurs matériels, exposée en métriques Prometheus. Une mesure, là où Carbon Footprint fait une répartition.
- **Scaphandre** (Apache 2.0) : agent de mesure de consommation électrique par processus sur une machine physique ou virtuelle.
- **Green Metrics Tool** (AGPL v3) : banc de mesure de la consommation d'une application conteneurisée sur un scénario reproductible.
- **Boavizta** (AGPL v3) : base de données et API d'impacts environnementaux du matériel, y compris la fabrication — la partie scope 3 que les mesures d'énergie ne couvrent pas.
- **Electricity Maps** publie des données d'intensité carbone horaire par réseau électrique ; la bibliothèque cliente est libre, les données elles-mêmes sont sous licence propre.
