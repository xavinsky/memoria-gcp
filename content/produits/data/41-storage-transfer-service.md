---
title: Storage Transfer Service
subgroup: Stockage objet et transfert
icon: categories/storage
schema:
  size: [760, 360]
  zones:
    - {label: Sur site, x: 6, y: 170, w: 210, h: 180}
    - {label: Projet GCP, x: 256, y: 16, w: 490, h: 330}
  nodes:
    s3: {label: Amazon S3, sub: "Azure Blob, compatible S3", external: true, x: 20, y: 40, w: 180}
    nfs: {label: Système de fichiers, sub: "NFS, HDFS", external: true, x: 20, y: 192, w: 180}
    agent: {label: Agents, sub: "conteneurs Docker", external: true, x: 20, y: 282, w: 180}
    sts: {label: Storage Transfer, sub: "jobs de transfert", icon: categories/storage, focus: true, x: 300, y: 150, w: 200, h: 66}
    pubsub: {label: Pub/Sub, sub: "notifications d'objets", icon: categories/data-analytics, x: 300, y: 40, w: 200}
    gcs: {label: Cloud Storage, sub: "bucket de destination", icon: produits/cloud-storage, x: 550, y: 150, w: 190}
    bq: {label: BigQuery, sub: "analyse des données migrées", icon: produits/bigquery, x: 496, y: 270, w: 234}
  flows:
    - {from: s3, to: sts, to_offset: -16, text: "Transfert sans agent depuis Amazon S3, Azure Blob Storage ou un stockage compatible S3"}
    - {from: nfs, to: agent, text: "Les agents, lancés en conteneurs Docker sur des machines Linux, montent le système de fichiers"}
    - {from: agent, to: sts, to_offset: 16, text: "Le pool d'agents pousse les fichiers ; c'est lui qui consomme la bande passante du site"}
    - {from: pubsub, to: sts, text: "Transfert piloté par les événements : le service écoute les notifications et copie les objets nouveaux ou modifiés"}
    - {from: sts, to: gcs, text: "Écriture dans le bucket de destination, avec vérification d'intégrité et journal de transfert"}
    - {from: gcs, to: bq, text: "Les données migrées alimentent l'entrepôt et les traitements du projet"}
docs:
  Page produit: https://cloud.google.com/storage-transfer-service
  Documentation: https://docs.cloud.google.com/storage-transfer/docs/overview
  Transferts pilotés par événements: https://docs.cloud.google.com/storage-transfer/docs/event-driven-transfers
  Pools d'agents: https://docs.cloud.google.com/storage-transfer/docs/on-prem-agent-pools
  Fichier manifeste: https://docs.cloud.google.com/storage-transfer/docs/manifest
  API REST: https://docs.cloud.google.com/storage-transfer/docs/reference/rest
  Commandes gcloud transfer: https://docs.cloud.google.com/sdk/gcloud/reference/transfer
  Bibliothèques clientes: https://docs.cloud.google.com/storage-transfer/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/storagetransfer/latest
  Quotas et limites: https://docs.cloud.google.com/storage-transfer/quotas
  Tarifs: https://cloud.google.com/storage-transfer/pricing
  Notes de version: https://docs.cloud.google.com/storage-transfer/docs/release-notes
---

## Ce que c'est

Service géré de copie de fichiers et d'objets vers, depuis et à l'intérieur de Google Cloud. On décrit un **job de transfert** (source, destination, filtres, calendrier), le service l'exécute et le rejoue.

- **Deux modes.** *Sans agent*, Google mène le transfert de bout en bout : Amazon S3, Azure Blob Storage et Data Lake Storage Gen2, un stockage compatible S3, une liste d'URL publiques, ou un bucket [Cloud Storage](#cloud-storage) vers un autre. *Avec agents*, des conteneurs Docker installés sur des machines Linux du site source lisent un système de fichiers POSIX ou HDFS ; ils sont regroupés en **pools d'agents**, qui servent aussi à plafonner la bande passante consommée.
- **Déclenchement** : à la demande, sur un calendrier récurrent, ou **piloté par les événements** — abonnement Pub/Sub pour une source Cloud Storage, Amazon SQS pour S3, Azure Storage Queue pour Azure. Le mode événementiel évite de lister la source à chaque passage et réplique en quelques minutes ; il ne propage pas les suppressions.
- **Sélection des données** : préfixes, motifs *glob*, date de dernière modification, classe de stockage, ou **fichier manifeste** listant les objets à copier. Options d'écrasement et de suppression à la source après copie.
- **Fiabilité** : parallélisation, reprises automatiques, validation d'intégrité, journal de transfert détaillé, chiffrement TLS 1.3 en transit. Le service n'a **pas de SLA**, ni sur le débit ni sur la latence.
- **Facturation** : les transferts sans agent (entre buckets, depuis un autre cloud ou une liste d'URL) sont gratuits, hors frais de sortie du fournisseur d'origine. Les transferts avec agent vers ou depuis un système de fichiers sont facturés au volume transféré ; ceux depuis un stockage compatible S3 ou HDFS sont gratuits. Le transfert depuis S3 par le réseau privé géré est facturé à part.

## À quoi ça sert

- Migrer un lac de données depuis AWS ou Azure, en une passe massive puis en transferts incrémentaux jusqu'à la bascule.
- Rapatrier un NAS ou un cluster HDFS vers Cloud Storage avant de moderniser les traitements avec [Managed Service for Apache Spark](#managed-service-for-apache-spark) ou [BigQuery](#bigquery).
- Répliquer un bucket dans une autre région, un autre projet ou un autre continent, pour la sauvegarde ou la séparation des environnements.
- Changer l'emplacement ou la classe d'un jeu de données existant, en copiant vers un nouveau bucket.

**À éviter** pour quelques fichiers ou quelques gigaoctets : le service vise les transferts de plus d'un tébioctet, et `gcloud storage cp` ou `rsync` suffisent en dessous. À éviter aussi quand la liaison réseau mettrait plus d'une semaine à écouler le volume : préférer [Transfer Appliance](#transfer-appliance). Pour importer des données d'applications SaaS dans l'entrepôt, c'est BigQuery Data Transfer Service qu'il faut, pas celui-ci.

## Alternatives en logiciel libre

- **Rclone** : synchronisation entre plus de soixante stockages objet et systèmes de fichiers, avec filtres, reprise et vérification de somme de contrôle ; l'équivalent le plus direct.
- **rsync** : la référence pour les transferts incrémentaux entre systèmes de fichiers POSIX.
- **Apache DistCp** (Hadoop) : copie distribuée entre HDFS et stockage objet, pour les gros volumes d'un cluster.
- **Apache NiFi** : flux de fichiers pilotés par événements, avec routage et traçabilité, quand le transfert demande de la logique.
- **s5cmd** : client S3 parallélisé, pour les copies massives entre buckets compatibles S3.
