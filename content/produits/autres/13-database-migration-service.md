---
title: Database Migration Service
subgroup: Migration et hybride
icon: categories/migration
schema:
  size: [760, 330]
  zones:
    - {label: Sur site ou autre cloud, x: 6, y: 16, w: 192, h: 298}
    - {label: Projet GCP, x: 212, y: 16, w: 542, h: 298}
  nodes:
    src: {label: Base source, sub: "MySQL, PostgreSQL, Oracle", external: true, x: 14, y: 50, w: 176}
    mss: {label: SQL Server, sub: "sauvegardes, journaux", external: true, x: 14, y: 226, w: 176}
    dms: {label: Database Migration Service, sub: "job de migration", icon: categories/migration, focus: true, x: 228, y: 42, w: 254, h: 70}
    gcs: {label: Cloud Storage, sub: "fichiers .bak et .trn", icon: produits/cloud-storage, x: 228, y: 222, w: 254}
    csql: {label: Cloud SQL, sub: "MySQL, PostgreSQL, SQL Server", icon: produits/cloud-sql, x: 504, y: 222, w: 238}
    alloy: {label: AlloyDB, sub: "PostgreSQL", icon: produits/alloydb, x: 504, y: 42, w: 238}
  flows:
    - {from: src, to: dms, text: "Connexion par liste d'adresses IP, tunnel SSH inversé, appairage VPC ou connectivité privée ; vidage initial puis capture continue des changements"}
    - {from: mss, to: gcs, text: "SQL Server : la sauvegarde complète puis les sauvegardes du journal de transactions sont déposées dans un bucket"}
    - {from: gcs, to: csql, text: "Le service surveille le bucket et restaure chaque fichier dans l'instance Cloud SQL for SQL Server"}
    - {from: dms, to: csql, from_side: bottom, to_side: top, from_offset: 90, text: "Migration homogène : l'instance de destination est une réplique de la source jusqu'à la promotion, qui en fait une instance principale"}
    - {from: dms, to: alloy, text: "Migration hétérogène (Oracle, SQL Server vers PostgreSQL) : le schéma converti dans un espace de conversion est appliqué, puis les données suivent"}
captures:
  - image: https://docs.cloud.google.com/static/database-migration/docs/images/htm/conversion_workspace_overview.png
    page: https://docs.cloud.google.com/database-migration/docs/oracle-to-postgresql/about-conversion-workspaces
    legende: "Espace de conversion Oracle vers PostgreSQL : taux de conversion du code, objets sans problème, à revoir ou à corriger, répartition par type d'objet"
  - image: https://docs.cloud.google.com/static/database-migration/docs/images/htm/htm_migration_job_metrics.png
    page: https://docs.cloud.google.com/database-migration/docs/oracle-to-postgresql/scenario-overview
    legende: "Onglet Monitoring d'un job de migration : volume du vidage initial, débit, délai de réplication et stockage consommé"
docs:
  Page produit: https://cloud.google.com/database-migration
  Documentation: https://docs.cloud.google.com/database-migration/docs
  Présentation: https://docs.cloud.google.com/database-migration/docs/overview
  Bases prises en charge: https://docs.cloud.google.com/database-migration/docs/supported-databases
  Migrations homogènes: https://docs.cloud.google.com/database-migration/docs/homogeneous-migrations
  Migrations hétérogènes: https://docs.cloud.google.com/database-migration/docs/heterogeneous-migrations
  Méthodes de connectivité: https://docs.cloud.google.com/database-migration/docs/mysql/networking-methods
  Espaces de conversion: https://docs.cloud.google.com/database-migration/docs/oracle-to-postgresql/about-conversion-workspaces
  API REST: https://docs.cloud.google.com/database-migration/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/database-migration
  Client Python: https://docs.cloud.google.com/python/docs/reference/datamigration/latest
  Quotas et limites: https://docs.cloud.google.com/database-migration/docs/quotas
  Tarifs: https://cloud.google.com/database-migration/pricing
  Notes de version: https://docs.cloud.google.com/database-migration/docs/release-notes
---

## Ce que c'est

Service serverless de migration de bases de données vers **Cloud SQL** et **AlloyDB for PostgreSQL**. Il prend en charge la connectivité, la copie initiale, la réplication continue et la bascule, et suit l'état de la migration.

- **Objets** : un **profil de connexion** par extrémité (hôte, identifiants, certificats), un **job de migration** qui relie la source à la destination, et pour les migrations hétérogènes un **espace de conversion**. Au plus 2 000 profils et 1 000 jobs par projet, jobs terminés compris.
- **Migrations homogènes**, même moteur des deux côtés :
  - MySQL (sur site, VM, Amazon RDS et Aurora, Azure, Cloud SQL) vers Cloud SQL for MySQL ;
  - PostgreSQL (mêmes sources) vers Cloud SQL for PostgreSQL ou AlloyDB, par réplication logique `pglogical` ;
  - SQL Server (autogéré, Amazon RDS, Cloud SQL) vers Cloud SQL for SQL Server, par restauration de fichiers de sauvegarde déposés dans Cloud Storage.
- **Migrations hétérogènes**, changement de moteur : Oracle (11g à 21c, dont RAC et Exadata, hors Autonomous Database) et SQL Server vers Cloud SQL for PostgreSQL ou AlloyDB. L'espace de conversion traduit schéma, procédures stockées, fonctions et vues ; un éditeur SQL permet de corriger ce qui ne passe pas, et Gemini propose des conversions pour le code que les règles déterministes ne traitent pas.
- **Types de migration** : **ponctuelle** (vidage et chargement, avec arrêt des écritures sur la source) ou **continue** (vidage initial puis capture des changements, CDC). En migration continue, la destination reste une réplique jusqu'à la **promotion**, qui la détache de la source ; la coupure se limite au temps de rediriger les applications.
- **Connectivité** : liste d'adresses IP autorisées (sur l'internet public), tunnel SSH inversé par une VM bastion dont le script est généré, appairage VPC ou connectivité privée (souvent sur un VPN ou un Interconnect).
- **Suivi** : onglet de métriques par job (volume du vidage, débit, délai de réplication), journaux dans Cloud Logging.
- **Facturation** : les migrations homogènes vers Cloud SQL et AlloyDB sont gratuites. Les migrations hétérogènes sont facturées au volume traité : le CDC par paliers dégressifs, le *backfill* à un tarif fixe au-delà de 500 Gio gratuits par mois. S'y ajoutent l'instance de destination et, le cas échéant, la VM du tunnel SSH.

## À quoi ça sert

- Déplacer une base MySQL, PostgreSQL ou SQL Server d'un centre de données ou d'un autre cloud vers un service géré, avec une coupure limitée au temps de la bascule.
- Passer d'une instance Cloud SQL à une autre (changement de région, de version majeure) ou de Cloud SQL for PostgreSQL à AlloyDB.
- Sortir d'Oracle ou de SQL Server vers PostgreSQL, en industrialisant la conversion du schéma et du code.

**À éviter** pour une réplication durable vers l'analytique : DMS migre puis s'arrête, [Datastream](#datastream) alimente BigQuery en continu. Pour une destination [Spanner](#spanner), passer par les outils de migration propres à Spanner. Pour une base qu'on garde telle quelle sur une VM, [Migrate to Virtual Machines](#migrate-to-virtual-machines) déplace le serveur entier.

> [!WARNING]
> Pour MySQL et PostgreSQL, les utilisateurs et leurs rôles ne sont pas migrés (la base système `mysql` n'est pas copiée) : les recréer sur la destination avant la promotion. En migration hétérogène, le taux de conversion affiché compte les instructions SQL, pas le travail restant : les objets « à revoir » demandent souvent plus de temps que les autres.

## Alternatives en logiciel libre

- **Ora2Pg** : l'outil de référence pour convertir un schéma et le code PL/SQL d'Oracle vers PostgreSQL, et exporter les données.
- **pgloader** : chargement de MySQL, SQL Server ou SQLite vers PostgreSQL, avec conversion de types, en une passe.
- **pglogical** et la réplication logique native de PostgreSQL : migration entre serveurs PostgreSQL avec une coupure minimale.
- **Debezium** : capture des changements pour une migration continue sur mesure, avec Kafka Connect.
- **mydumper** et **myloader** : vidage et chargement parallèles de MySQL.
