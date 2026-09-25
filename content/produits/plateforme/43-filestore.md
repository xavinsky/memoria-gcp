---
title: Filestore
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 360]
  zones:
    - {label: Projet GCP, x: 14, y: 16, w: 732, h: 330}
  nodes:
    vms: {label: VMs applicatives, sub: "montage NFS", icon: produits/compute-engine, x: 40, y: 100, w: 210}
    gke: {label: Cluster GKE, sub: "PVC ReadWriteMany", icon: produits/gke, x: 40, y: 220, w: 210}
    fs: {label: Filestore, sub: "niveau Regional", icon: categories/storage, focus: true, x: 310, y: 150, w: 200, h: 70}
    snap: {label: Instantanés, sub: "dossier .snapshot", icon: categories/storage, x: 310, y: 280, w: 200}
    rep: {label: Réplique, sub: "autre zone, async", icon: categories/storage, x: 560, y: 40, w: 180}
    bkp: {label: Sauvegardes, sub: "autre région", icon: categories/storage, x: 560, y: 150, w: 180}
  flows:
    - {from: vms, to: fs, to_offset: -12, text: "Les VM montent le partage en NFSv3 ou NFSv4.1 depuis le VPC et écrivent toutes en même temps dans la même arborescence"}
    - {from: gke, to: fs, to_offset: 12, text: "Un volume persistant ReadWriteMany donne le même partage à tous les pods, sur tous les nœuds du cluster"}
    - {from: fs, to: snap, text: "Un instantané fige l'état du partage ; les fichiers restent lisibles dans le dossier caché .snapshot de chaque répertoire"}
    - {from: fs, to: rep, from_offset: -15, text: "La réplication asynchrone entretient une instance de secours dans l'emplacement choisi"}
    - {from: fs, to: bkp, from_offset: 15, text: "Une sauvegarde différentielle part vers une autre région et sert à recréer une instance n'importe où"}
docs:
  Page produit: https://cloud.google.com/filestore
  Documentation: https://docs.cloud.google.com/filestore/docs
  Vue d'ensemble: https://docs.cloud.google.com/filestore/docs/overview
  Niveaux de service: https://docs.cloud.google.com/filestore/docs/service-tiers
  Protocoles pris en charge: https://docs.cloud.google.com/filestore/docs/about-supported-protocols
  Performances personnalisées: https://docs.cloud.google.com/filestore/docs/custom-performance
  Instantanés: https://docs.cloud.google.com/filestore/docs/snapshots
  Sauvegardes: https://docs.cloud.google.com/filestore/docs/backups
  Réplication d'instance: https://docs.cloud.google.com/filestore/docs/instance-replication
  Pilote CSI pour GKE: https://docs.cloud.google.com/filestore/docs/csi-driver
  API REST: https://docs.cloud.google.com/filestore/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/filestore
  Bibliothèques clientes: https://docs.cloud.google.com/filestore/docs/reference/libraries
  Quotas et limites: https://docs.cloud.google.com/filestore/docs/limits
  Tarifs: https://cloud.google.com/filestore/pricing
  Notes de version: https://docs.cloud.google.com/filestore/docs/release-notes
---

## Ce que c'est

Serveur de fichiers NFS géré. Une instance Filestore expose un ou plusieurs partages sur un réseau VPC ; VMs [Compute Engine](#compute-engine), clusters [GKE](#gke), services Cloud Run, banques de données VMware Engine et machines sur site montent le même système de fichiers POSIX, en lecture-écriture concurrente.

- **Niveaux de service principaux :**
  - **Zonal** — calcul à haute performance, rendu, traitements par lots localisés. De 1 Tio à 9,75 Tio par pas de 256 Gio, ou de 10 Tio à 100 Tio par pas de 2,5 Tio.
  - **Regional** — disponibilité à l'échelle de la région, résistance à la perte d'une zone. De 100 Gio à 9,75 Tio, puis de 10 Tio à 100 Tio ; les instances de moins de 1 Tio ne sont proposées que dans certaines régions et imposent des performances personnalisées.
  - **Multishares for GKE (Enterprise)** — plusieurs partages découpés dans une même instance régionale, pour éviter une instance par volume persistant. De 1 Tio à 10 Tio.
  - [!DECONSEILLE] **Basic HDD** et **Basic SSD** — niveaux hérités, capacité extensible seulement à la hausse par pas de 1 Gio, jusqu'à 63,9 Tio, performances fixes ; Zonal ou Regional pour une nouvelle instance.
- **Protocoles.** NFSv3 sur tous les niveaux ; NFSv4.1 sur Zonal, Regional et Enterprise, avec authentification Kerberos et chiffrement en transit (`krb5p`). Le raccordement passe par l'appairage de VPC, l'accès aux services privés ou Private Service Connect.
- **Performances personnalisées.** Sur les niveaux Zonal et Regional, les IOPS se fixent indépendamment de la capacité, soit en valeur absolue, soit en IOPS par Tio ; un cluster GKE peut les ajuster sans interruption.
- **Instantanés.** Copie logique interne à l'instance, prise en deux minutes sans recopier les données et sans effet sur les performances. Chaque répertoire du partage contient un dossier caché `.snapshot` d'où l'on relit un fichier à l'état voulu. Jusqu'à 240 instantanés par instance ; ils ne consomment de la place qu'à mesure que les données changent. Réservés aux niveaux Zonal, Regional et Enterprise.
- **Sauvegardes.** Copie différentielle externe à l'instance, ressource régionale que l'on peut créer dans une autre région et à partir de laquelle on restaure une nouvelle instance n'importe où. Les sauvegardes *standard* sont gérées par Filestore ; les sauvegardes *améliorées* sont déléguées à [Backup and DR](#backup-and-dr).
- **Réplication d'instance.** Réplication asynchrone continue vers une instance de secours dans l'emplacement choisi, proposée sur les niveaux Zonal, Regional et Enterprise.
- **Contrôle d'accès** par adresse IP du client, et chiffrement au repos par défaut, avec CMEK possible sur les niveaux non hérités.
- **Facturation** à la capacité provisionnée selon le niveau et l'emplacement, à laquelle s'ajoutent les IOPS provisionnées en performances personnalisées et le stockage des sauvegardes.

> [!TIP]
> Le redimensionnement se fait sans interruption, mais les niveaux hérités Basic ne savent qu'augmenter. Si la capacité doit pouvoir redescendre, choisir Zonal ou Regional dès la création.

## À quoi ça sert

- Répertoires partagés d'applications d'entreprise : dépôts de documents, espaces de travail, données de configuration lues par plusieurs serveurs.
- Volumes `ReadWriteMany` pour [GKE](#gke), via le pilote CSI : un même partage monté par tous les pods d'un déploiement.
- Fermes de rendu et traitements par lots dont les nœuds lisent et écrivent le même jeu de fichiers.
- Migration d'applications sur site qui attendent un montage NFS, des liens durs et des verrous de fichiers — ce que ne donne pas un bucket monté en FUSE.
- Banques de données pour Google Cloud VMware Engine.

**À éviter** pour du calcul massivement parallèle qui réclame des dizaines de Gio/s agrégés : c'est le terrain de [Managed Lustre](#managed-lustre). À éviter aussi quand il faut du SMB, des quotas par utilisateur ou de la hiérarchisation automatique vers un palier froid, où [NetApp Volumes](#netapp-volumes) est mieux armé. Et pour des fichiers simplement déposés et relus par des services managés, [Cloud Storage](#cloud-storage) coûte bien moins cher.

## Alternatives en logiciel libre

- **NFS-Ganesha** : serveur NFSv3 et NFSv4.x en espace utilisateur, l'équivalent direct, posé sur un système de fichiers local ou sur Ceph.
- **Le serveur NFS du noyau Linux** (`nfs-kernel-server`) : la solution la plus simple pour exposer un partage depuis une VM, sans gestion de la haute disponibilité.
- **CephFS** : système de fichiers POSIX distribué, avec instantanés et quotas, exporté en NFS par Ganesha si besoin.
- **GlusterFS** : agrégation de volumes répartis sur plusieurs serveurs, avec réplication synchrone ou géo-réplication asynchrone.
- **MooseFS** et **JuiceFS** : systèmes de fichiers distribués avec instantanés, montés par FUSE, pour des grappes de taille moyenne.
- **ZFS** avec envoi incrémental (`zfs send`) : instantanés et réplication asynchrone vers un second serveur, comme les instantanés et la réplication d'instance.
