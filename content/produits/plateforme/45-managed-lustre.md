---
title: Managed Lustre
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 14, y: 16, w: 732, h: 290}
  nodes:
    gcs: {label: Cloud Storage, sub: "jeu de données brut", icon: produits/cloud-storage, x: 40, y: 130, w: 200}
    lustre: {label: Managed Lustre, sub: "POSIX, 1 000 Mo/s par Tio", icon: categories/storage, focus: true, x: 300, y: 130, w: 210, h: 70}
    gke: {label: Cluster GKE, sub: "pilote CSI", icon: produits/gke, x: 570, y: 40, w: 170}
    vms: {label: VMs A4, sub: "clients Lustre", icon: produits/compute-engine, x: 570, y: 150, w: 170}
  flows:
    - {from: gcs, to: lustre, from_side: right, to_side: left, from_offset: -14, to_offset: -14, text: "Le jeu d'entraînement est importé depuis le bucket ; les transferts sont incrémentaux et ne recopient que ce qui a changé"}
    - {from: lustre, to: gke, from_side: right, to_side: left, from_offset: -14, text: "Le pilote CSI monte le système de fichiers dans les pods, en ReadWriteMany, sans installer de module dans les nœuds"}
    - {from: lustre, to: vms, from_side: right, to_side: left, from_offset: 14, text: "Les VM accélérées montent le même point de montage avec le client Lustre et lisent en parallèle depuis tous les serveurs d'objets"}
    - {from: gke, to: lustre, from_side: bottom, to_side: top, text: "Les points de contrôle de l'entraînement sont écrits sur le système de fichiers, à plein débit"}
    - {from: lustre, to: gcs, from_side: left, to_side: right, from_offset: 14, to_offset: 14, text: "En fin de travail, les résultats sont exportés vers Cloud Storage, où ils coûtent moins cher à conserver"}
docs:
  Page produit: https://cloud.google.com/products/managed-lustre
  Documentation: https://docs.cloud.google.com/managed-lustre/docs/overview
  Paliers de performance: https://docs.cloud.google.com/managed-lustre/docs/performance-tiers
  Créer une instance: https://docs.cloud.google.com/managed-lustre/docs/create-instance
  Monter depuis Compute Engine: https://docs.cloud.google.com/managed-lustre/docs/connect-from-compute-engine
  Pilote CSI pour GKE: https://docs.cloud.google.com/managed-lustre/docs/lustre-csi-driver-overview
  Transferts avec Cloud Storage: https://docs.cloud.google.com/managed-lustre/docs/transfer-data
  Conformité POSIX: https://docs.cloud.google.com/managed-lustre/docs/posix-compliance
  Sauvegarder les données: https://docs.cloud.google.com/managed-lustre/docs/back-up-instance-data
  API REST: https://docs.cloud.google.com/managed-lustre/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/lustre
  APIs et bibliothèques: https://docs.cloud.google.com/managed-lustre/docs/apis
  Quotas et limites: https://docs.cloud.google.com/managed-lustre/docs/quotas
  Tarifs: https://cloud.google.com/products/managed-lustre/pricing
  Notes de version: https://docs.cloud.google.com/managed-lustre/docs/release-notes
---

## Ce que c'est

Système de fichiers parallèle géré, fondé sur Lustre et développé avec DDN, son principal mainteneur. Les données d'un fichier sont réparties sur de nombreux serveurs d'objets que les clients interrogent simultanément : le débit agrégé croît avec le nombre de nœuds de calcul, là où un serveur NFS plafonne sur un point d'entrée unique.

- **Capacité et débit.** De 9 000 Gio à 84 016 000 Gio (80,1 Pio) par instance, jusqu'à 10 To/s de débit agrégé, jusqu'à 5 800 IOPS en lecture et 5 600 en écriture par Tio, et 0,5 Pio pour un seul fichier.
- **Paliers de performance.** Quatre paliers numérotés, où le débit est proportionnel à la capacité provisionnée — 1 000, 500, 250 et 125 Mo/s par Tio —, avec une capacité minimale d'autant plus grande que le palier est modeste (9 000 Gio à 1 000 Mo/s par Tio, 72 000 Gio à 125). Le palier **Dynamic** (25 Mo/s par Tio, à partir de 472 000 Gio) garde un espace de noms unique à l'échelle du pétaoctet et déplace automatiquement les données actives vers un cache rapide.
- **Conformité POSIX.** Droits, liens durs, verrous, horodatages : les outils et les bibliothèques existants fonctionnent sans adaptation, contrairement à un bucket monté en FUSE.
- **Métadonnées.** Pour 72 Go/s de débit, jusqu'à 410 000 `stat`, 115 000 créations et 95 000 suppressions par seconde, et jusqu'à 22 fois ces valeurs sur les grandes instances — le point qui distingue un système de fichiers parallèle sur des jeux de millions de petits fichiers.
- **Clients.** VM [Compute Engine](#compute-engine) avec le client Lustre et le module noyau fourni (DKMS), ou pods [GKE](#gke) par le pilote CSI, qui gère les volumes persistants provisionnés dynamiquement ou rattachés à une instance existante, en `ReadWriteMany`, `ReadOnlyMany` et `ReadWriteOnce`.
- **Échanges avec Cloud Storage.** Import et export incrémentaux, jusqu'à 100 Go/s pour les fichiers de plus de 32 Mio, dans la limite du débit de l'instance. Un bucket à espace de noms hiérarchique accélère nettement ces transferts. L'agent de service Managed Lustre doit avoir un rôle de lecture ou d'écriture sur le bucket.
- **Réseau et sécurité.** L'instance vit dans un VPC, avec contrôle d'accès par adresse IP, chiffrement au repos avec CMEK possible, journalisation d'audit et compatibilité VPC Service Controls. Le protocole Lustre ne chiffre pas lui-même les échanges, mais tout le trafic interne à Google Cloud l'est.
- **Maintenance.** Une stratégie de maintenance permet de choisir les fenêtres pendant lesquelles l'instance peut être mise à jour.

> [!WARNING]
> Une instance Managed Lustre n'est pas un espace de conservation : il n'existe ni instantané ni sauvegarde intégrée. La sauvegarde consiste à exporter vers un bucket [Cloud Storage](#cloud-storage), qui reste la source de vérité des données.

## À quoi ça sert

- Entraînement de modèles sur des flottes de machines accélérées, où des centaines de nœuds lisent le même corpus et écrivent leurs points de contrôle en même temps.
- Calcul à haute performance : simulation, modélisation, dynamique des fluides, séquençage, où les nœuds partagent un espace de travail commun.
- Prétraitement de gros jeux de données avant l'entraînement, quand le coût en temps vient des métadonnées et des petits fichiers.
- Portage sur Google Cloud d'une chaîne HPC existante déjà écrite pour Lustre, sans changer les scripts ni les points de montage.

**À éviter** pour un partage de fichiers d'entreprise : ni SMB, ni jonction à un domaine, ni instantanés, et un plancher de capacité qui se chiffre en dizaines de Tio. [Filestore](#filestore) ou [NetApp Volumes](#netapp-volumes) conviennent mieux. À éviter aussi comme stockage durable de référence, rôle qui revient à [Cloud Storage](#cloud-storage), et pour un espace de travail purement local à une machine, où le [Local SSD](#local-ssd) coûte bien moins cher.

## Alternatives en logiciel libre

- **Lustre** lui-même (licence GPL) : c'est exactement le même logiciel, à installer et administrer soi-même sur des serveurs de métadonnées et d'objets.
- **CephFS** : espace de noms POSIX distribué, plus polyvalent mais moins taillé pour le débit séquentiel massif.
- **OrangeFS** : descendant de PVFS, orienté entrées-sorties parallèles MPI.
- **DAOS** : pile de stockage pour mémoire persistante et NVMe, pensée pour les charges HPC et IA à très faible latence.
- **GekkoFS** : système de fichiers éphémère monté sur les nœuds de calcul le temps d'un travail, pour absorber les accès aux petits fichiers.
