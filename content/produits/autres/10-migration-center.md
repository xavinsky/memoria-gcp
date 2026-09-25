---
title: Migration Center
subgroup: Migration et hybride
icon: categories/migration
schema:
  size: [760, 330]
  zones:
    - {label: Sur site ou autre cloud, x: 6, y: 16, w: 196, h: 298}
    - {label: Projet GCP, x: 222, y: 16, w: 532, h: 298}
  nodes:
    infra: {label: Parc existant, sub: "vCenter, serveurs, bases", external: true, x: 18, y: 40, w: 172}
    client: {label: Client de découverte, sub: "ou CLI mcdc", external: true, x: 18, y: 138, w: 172}
    imp: {label: Import manuel, sub: "RVTools, CSV, scripts", external: true, x: 18, y: 236, w: 172}
    mc: {label: Migration Center, sub: "inventaire, TCO, vagues", icon: categories/migration, focus: true, x: 252, y: 130, w: 206, h: 70}
    m2vm: {label: Migrate to Virtual Machines, sub: "serveurs à réhéberger", icon: categories/migration, x: 486, y: 40, w: 258}
    dms: {label: Database Migration Service, sub: "bases à migrer", icon: categories/migration, x: 486, y: 236, w: 258}
  flows:
    - {from: infra, to: client, text: "Le client de découverte (en continu) ou la CLI mcdc (en une passe) interroge vCenter et les serveurs : configuration, performances, dépendances réseau, logiciels installés"}
    - {from: client, to: mc, text: "Les données collectées sont envoyées dans Migration Center, dans la région choisie à son activation"}
    - {from: imp, to: mc, text: "Variante sans agent : export RVTools, tableaux remplis à la main ou scripts de collecte AWS et Azure, importés en fichiers"}
    - {from: mc, to: m2vm, control: true, text: "Les actifs sont regroupés, comparés dans un rapport TCO, puis répartis en vagues ; les serveurs à réhéberger partent vers Migrate to Virtual Machines"}
    - {from: mc, to: dms, control: true, text: "Les bases de la vague sont migrées par Database Migration Service vers Cloud SQL ou AlloyDB"}
docs:
  Page Migration: https://cloud.google.com/products/cloud-migration
  Documentation: https://docs.cloud.google.com/migration-center/docs
  Présentation: https://docs.cloud.google.com/migration-center/docs/migration-center-overview
  Découverte et évaluation: https://docs.cloud.google.com/migration-center/docs/discovery-and-assessment-overview
  Méthodes de collecte: https://docs.cloud.google.com/migration-center/docs/start-asset-discovery
  Client de découverte: https://docs.cloud.google.com/migration-center/docs/discovery-client-overview
  Rapports TCO: https://docs.cloud.google.com/migration-center/docs/generate-tco-report
  Planification des vagues: https://docs.cloud.google.com/migration-center/docs/migration-planning-overview
  Outils de migration: https://docs.cloud.google.com/migration-center/docs/migration-modernization-tools
  API REST: https://docs.cloud.google.com/migration-center/docs/reference/rest/v1
  Client Python: https://docs.cloud.google.com/python/docs/reference/migrationcenter/latest
  Quotas et limites: https://docs.cloud.google.com/migration-center/docs/quotas
  Notes de version: https://docs.cloud.google.com/migration-center/docs/release-notes
---

## Ce que c'est

Console d'évaluation et de planification d'une migration vers Google Cloud. Migration Center ne déplace aucune charge : il inventorie le parc existant, chiffre son coût cible et organise le travail, puis renvoie vers les outils d'exécution.

- **Découverte des actifs** : serveurs physiques, VM (vSphere, autres hyperviseurs, AWS EC2, Azure), bases SQL Server, MySQL et PostgreSQL. Trois modes de collecte :
  - le **client de découverte**, installé sur une machine Windows, qui scanne le parc à intervalles réguliers pendant plusieurs jours — il ne collecte pas les bases ;
  - la **CLI mcdc** (*Migration Center discovery client CLI*), sans installation, sous Linux ou Windows, pour une photo ponctuelle ; elle peut aussi produire une **évaluation hors ligne**, sans rien envoyer à Google Cloud ;
  - l'**import manuel** : export RVTools d'un vCenter, tableaux modèles remplis à la main, sorties des scripts de collecte AWS et Azure.
- **Données collectées** : caractéristiques des machines, configuration, taux d'utilisation, dépendances réseau, logiciels installés. Pas de contenu applicatif ni de fichiers ; la seule donnée personnelle est l'adresse IP.
- **Évaluation** : les actifs sont rangés en **groupes** (par application ou objectif), auxquels on applique des **préférences de migration** (région, cible Compute Engine ou VMware Engine, séries de machines, licences d'OS, formule de prix, stratégie de dimensionnement). Le **rapport TCO** compare jusqu'à quatre jeux de préférences sur cinq groupes au plus, et recommande une cible par actif (une VM Compute Engine pour un serveur, une instance Cloud SQL pour une base). Export vers Google Slides, Google Sheets, CSV ou Excel.
- **Estimation rapide** : un chiffrage du coût Google Cloud à partir de la taille du parc, sans activer le service ni collecter de données détaillées.
- **Planification** : découpage en **vagues** et en **groupes de déplacement** (*move groups*), dépendances à migrer ensemble, et le catalogue des outils d'exécution par stratégie (réhéberger, replateformer, refactoriser).
- **App Modernization Assessment** (`codmod`) : une CLI qui fait analyser le code source d'une application par Gemini et produit un rapport de modernisation ; le code est envoyé à l'API Gemini Enterprise Agent Platform, facturée aux jetons.
- **Région** : les données d'évaluation sont stockées dans une région choisie à l'activation, qu'on ne peut plus changer ensuite. Limite de 100 000 actifs par projet.
- **Facturation** : l'estimation et l'évaluation sont gratuites ; seul `codmod` coûte, au volume de code analysé.

## À quoi ça sert

- Dresser l'inventaire d'un centre de données avant une migration, quand la CMDB est incomplète ou périmée.
- Chiffrer le coût cible d'un parc et comparer plusieurs scénarios (dimensionnement à l'identique ou d'après l'utilisation réelle, engagements d'utilisation).
- Repérer les dépendances réseau entre serveurs pour composer des vagues cohérentes.
- Partager un rapport chiffré avec la direction ou un partenaire d'intégration.

**À éviter** pour exécuter la migration : Migration Center ne réplique rien. Le déplacement des VM passe par [Migrate to Virtual Machines](#migrate-to-virtual-machines), celui des bases par [Database Migration Service](#database-migration-service). Pour une poignée de serveurs bien connus, un chiffrage dans le simulateur de prix suffit.

> [!TIP]
> Le dimensionnement sans données de performance recopie la taille des VM sources, souvent surdimensionnées. Laisser tourner le client de découverte quelques semaines donne des taux d'utilisation réels et des recommandations plus justes.

## Alternatives en logiciel libre

Pas d'équivalent intégré : on assemble l'inventaire, la mesure et le chiffrage soi-même.

- **GLPI** avec son agent d'inventaire : CMDB libre qui recense matériel, systèmes et logiciels installés.
- **Ralph** : gestion d'actifs et CMDB libre orientée centres de données.
- **Netdata**, **Prometheus** avec `node_exporter` : relevé de l'utilisation réelle des serveurs pour dimensionner la cible.
- Pour les dépendances réseau, les flux NetFlow collectés par **ntopng** (édition communautaire) ou **pmacct**.
