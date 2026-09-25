---
title: Hyperdisk
subgroup: Stockage bloc et fichiers
icon: produits/hyperdisk
schema:
  size: [760, 390]
  zones:
    - {label: Projet GCP, x: 150, y: 16, w: 596, h: 358}
  nodes:
    ops: {label: Exploitant, sub: "gcloud", external: true, x: 10, y: 45, w: 130}
    pool: {label: Storage Pool, sub: "capacité en gros", icon: produits/hyperdisk, x: 165, y: 45, w: 175}
    hdb: {label: Hyperdisk Balanced, sub: "IOPS au choix", icon: produits/hyperdisk, focus: true, x: 370, y: 45, w: 195, h: 60}
    db: {label: VM PostgreSQL, sub: "base applicative", icon: produits/compute-engine, x: 595, y: 45, w: 150}
    hdha: {label: Hyperdisk HA, sub: "réplica zone B", icon: produits/hyperdisk, x: 370, y: 155, w: 195}
    gcs: {label: Cloud Storage, sub: "jeu de données", icon: produits/cloud-storage, x: 165, y: 280, w: 175}
    hdml: {label: Hyperdisk ML, sub: "lecture seule", icon: produits/hyperdisk, x: 370, y: 280, w: 195}
    gpus: {label: VMs GPU, sub: "entraînement", icon: produits/compute-engine, x: 595, y: 280, w: 150}
  flows:
    - {from: ops, to: pool, control: true, text: "L'exploitant achète capacité et performances en gros dans un pool de stockage, au lieu de les provisionner volume par volume"}
    - {from: pool, to: hdb, text: "Les volumes sont taillés dans le pool et n'y consomment que ce qu'ils utilisent réellement"}
    - {from: db, to: hdb, from_side: left, to_side: right, text: "La base lit et écrit ses blocs ; les IOPS et le débit se règlent à chaud, sans toucher à la taille du volume"}
    - {from: hdb, to: hdha, text: "Un volume Balanced High Availability réplique chaque écriture de façon synchrone dans une seconde zone de la région"}
    - {from: gcs, to: hdml, text: "Le jeu d'entraînement est chargé depuis un bucket vers un volume Hyperdisk ML"}
    - {from: hdml, to: gpus, text: "Le même volume est attaché en lecture seule à toutes les instances d'entraînement, jusqu'à 2 500"}
docs:
  Page produit: https://cloud.google.com/products/block-storage
  Documentation: https://docs.cloud.google.com/compute/docs/disks/hyperdisks
  Choisir un type de disque: https://docs.cloud.google.com/compute/docs/disks
  Hyperdisk Balanced: https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-balanced
  Hyperdisk Balanced High Availability: https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-balanced-ha
  Hyperdisk Extreme: https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-extreme
  Hyperdisk Throughput: https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-throughput
  Hyperdisk ML: https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-ml
  Performances: https://docs.cloud.google.com/compute/docs/disks/hyperdisk-performance
  Limites de performances: https://docs.cloud.google.com/compute/docs/disks/hyperdisk-perf-limits
  Storage Pools: https://docs.cloud.google.com/compute/docs/disks/storage-pools
  Exapools: https://docs.cloud.google.com/compute/docs/disks/hyperdisk-exapools
  Ajouter un volume: https://docs.cloud.google.com/compute/docs/disks/add-hyperdisk
  Modifier taille et performances: https://docs.cloud.google.com/compute/docs/disks/modify-hyperdisks
  Réplication asynchrone: https://docs.cloud.google.com/compute/docs/disks/async-pd/about
  API REST disks: https://docs.cloud.google.com/compute/docs/reference/rest/v1/disks
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/disks
  Tarifs: https://cloud.google.com/compute/disks-image-pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Stockage bloc durable de [Compute Engine](#compute-engine), construit sur le déport d'entrées-sorties *Titanium*. Sa particularité : **les performances se provisionnent séparément de la capacité**. On fixe la taille d'un côté, les IOPS ou le débit de l'autre, et on les fait varier indépendamment sur un volume en service.

- **Cinq familles**, chacune taillée pour une forme de charge :
  - **Hyperdisk Balanced** — le choix par défaut : disques de démarrage, applications d'entreprise, PostgreSQL, MySQL, postes de travail virtuels. Jusqu'à 160 000 IOPS et 2 400 Mio/s par volume, 4 Gio à 64 Tio, accès en lecture-écriture simultané depuis 8 instances au plus.
  - **Hyperdisk Balanced High Availability** — mêmes usages avec un objectif de point de reprise nul : les écritures sont répliquées de façon synchrone dans deux zones de la même région. Jusqu'à 100 000 IOPS et 2 400 Mio/s.
  - **Hyperdisk Extreme** — les IOPS les plus élevées, pour SAP HANA, Oracle, SQL Server haut de gamme et bases en mémoire. Jusqu'à 350 000 IOPS, 64 Gio à 64 Tio ; le débit n'est pas réglable, il découle du niveau d'IOPS demandé.
  - **Hyperdisk Throughput** — beaucoup de bande passante et de capacité sans besoin d'IOPS : Hadoop, Spark, Kafka, disques froids. 2 Tio à 32 Tio, jusqu'à 2 400 Mio/s ; seul le débit se provisionne.
  - **Hyperdisk ML** — le débit en lecture le plus élevé, pour l'entraînement et l'inférence : un même volume s'attache en lecture seule à 2 500 instances au plus. Seul le débit se provisionne.
- **Pools de stockage.** Un *Hyperdisk Storage Pool* achète capacité et performances en gros dans un projet et une zone, puis les volumes y sont créés et ne consomment que ce qu'ils utilisent (provisionnement fin, réduction de données). Google le recommande à partir de 20 Tio provisionnés ; au-delà de 5 Pio ou 1 Tio/s dans une même zone, c'est un *Exapool*. Un pool saturé fait échouer les écritures de tous ses disques : la supervision de l'espace libre n'est pas optionnelle.
- **Haute disponibilité et reprise.** Balanced High Availability couvre la panne d'une zone. La **réplication asynchrone** entretient une copie dans une seconde région, avec basculement manuel ; elle s'applique aux volumes Balanced, Balanced High Availability et Extreme.
- **Protection contre les écritures déchirées.** Toutes les familles garantissent l'atomicité des écritures jusqu'à 128 Kio, tant qu'elles ne franchissent pas une frontière de 1 Mio : une coupure laisse soit l'écriture entière, soit les données d'origine.
- **Latence** de l'ordre du SSD d'entreprise pour Balanced, Balanced High Availability, Extreme et ML — sous la milliseconde pour Balanced et Extreme ; comparable à un disque dur pour Throughput.
- **Facturation** de la capacité provisionnée et des performances provisionnées, séparément. Un volume ML n'est facturé que sur son débit, un volume Balanced sur ses IOPS et son débit.

> [!TIP]
> Un volume n'atteint ses performances provisionnées que si le type de machine auquel il est attaché les supporte. Vérifier les limites de la série de machines avant de payer des IOPS que la VM ne pourra pas consommer.

## À quoi ça sert

- Disques de démarrage et de données de toutes les VM récentes : sur les séries C4, C4A, C4D, N4, M4, A4, G4 et X4, c'est le seul stockage bloc durable disponible.
- Bases de données dont la charge varie : on monte les IOPS avant une clôture comptable, on les redescend ensuite, sans toucher au volume.
- Bases critiques à basculement rapide, avec Balanced High Availability plutôt qu'un cluster à réplication applicative.
- Jeux d'entraînement partagés par une flotte de machines accélérées, avec un volume ML unique monté en lecture seule.
- Grandes flottes de disques dont on veut lisser le provisionnement, via un pool de stockage.

**À éviter** pour un espace de travail purement temporaire, où le [Local SSD](#local-ssd) offre une latence bien plus basse à moindre coût. À éviter aussi comme système de fichiers partagé en lecture-écriture par de nombreuses machines : au-delà de huit instances, il faut [Filestore](#filestore), [NetApp Volumes](#netapp-volumes) ou [Managed Lustre](#managed-lustre). Et pour des fichiers destinés à des services managés ou à un archivage long, [Cloud Storage](#cloud-storage) reste bien moins cher au Gio.

## Alternatives en logiciel libre

- **Ceph RBD** : volumes blocs répartis, avec provisionnement fin, instantanés et pools de capacité — l'équivalent le plus proche, pools de stockage compris.
- **LVM** avec *thin provisioning* : pools logiques sur un serveur, dans lesquels on taille des volumes qui ne consomment que leurs blocs écrits.
- **DRBD** : réplication bloc synchrone entre deux nœuds, comme Balanced High Availability entre deux zones.
- **Longhorn**, **OpenEBS Mayastor** : stockage bloc répliqué pour Kubernetes, avec instantanés et restauration par CSI.
- **SPDK** et **NVMe over Fabrics** : la brique bas niveau du déport d'entrées-sorties, pour exposer du NVMe distant à faible latence.
