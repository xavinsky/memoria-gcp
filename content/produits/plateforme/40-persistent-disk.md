---
title: Persistent Disk
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 380]
  zones:
    - {label: Projet GCP, x: 14, y: 16, w: 732, h: 350}
  nodes:
    sched: {label: Calendrier, sub: "instantané nocturne", icon: categories/storage, x: 40, y: 40, w: 180}
    vm: {label: Compute Engine, sub: "VM applicative", icon: produits/compute-engine, x: 40, y: 160, w: 180, h: 60}
    boot: {label: Disque de démarrage, sub: "pd-balanced 50 Gio", icon: categories/storage, x: 280, y: 40, w: 210}
    data: {label: Disque de données, sub: "pd-ssd 500 Gio", icon: categories/storage, focus: true, x: 280, y: 160, w: 210, h: 60}
    repd: {label: Réplica zone B, sub: "disque régional", icon: categories/storage, x: 280, y: 290, w: 210}
    snap: {label: Instantanés, sub: "stockage régional", icon: categories/storage, x: 540, y: 160, w: 200}
    newd: {label: Nouveau disque, sub: "restauration", icon: categories/storage, x: 540, y: 290, w: 200}
  flows:
    - {from: vm, to: boot, from_side: right, to_side: left, text: "La VM démarre sur son disque de démarrage, attaché comme un périphérique bloc réseau"}
    - {from: vm, to: data, from_side: right, to_side: left, text: "Le disque de données est monté par la VM ; son débit et ses IOPS montent avec sa taille et avec le nombre de vCPU"}
    - {from: sched, to: data, control: true, text: "Un calendrier d'instantanés déclenche chaque nuit une capture, sans arrêter la VM"}
    - {from: data, to: repd, text: "Un disque régional réplique chaque écriture de façon synchrone dans une seconde zone de la région"}
    - {from: data, to: snap, text: "L'instantané ne copie que les blocs modifiés depuis le précédent et il est conservé hors de la zone du disque"}
    - {from: snap, to: newd, text: "Un instantané sert de source à un nouveau disque, dans n'importe quelle zone ou région"}
captures:
  - image: https://docs.cloud.google.com/static/compute/images/disk_clone.png
    page: https://docs.cloud.google.com/compute/docs/disks/clone-duplicate-disks
    legende: "Liste des disques dans la console : type, taille, zone, calendrier d'instantanés et menu d'actions"
deprecie: "Ne subsiste que sur les séries de machines qui ne prennent pas [Hyperdisk](#hyperdisk), seul choix sur les séries récentes."
docs:
  Page produit: https://cloud.google.com/persistent-disk
  Documentation: https://docs.cloud.google.com/compute/docs/disks/persistent-disks
  Choisir un type de disque: https://docs.cloud.google.com/compute/docs/disks
  Performances: https://docs.cloud.google.com/compute/docs/disks/performance
  Disque régional: https://docs.cloud.google.com/compute/docs/disks/high-availability-regional-persistent-disk
  Instantanés: https://docs.cloud.google.com/compute/docs/disks/snapshots
  Instantanés instantanés: https://docs.cloud.google.com/compute/docs/disks/instant-snapshots
  Calendriers d'instantanés: https://docs.cloud.google.com/compute/docs/disks/scheduled-snapshots
  Redimensionner un disque: https://docs.cloud.google.com/compute/docs/disks/resize-persistent-disk
  Changer de type de disque: https://docs.cloud.google.com/compute/docs/disks/migrate-to-hyperdisk
  Partager un disque entre VMs: https://docs.cloud.google.com/compute/docs/disks/sharing-disks-between-vms
  API REST disks: https://docs.cloud.google.com/compute/docs/reference/rest/v1/disks
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/disks
  Client Python: https://docs.cloud.google.com/python/docs/reference/compute/latest
  Quotas et limites: https://docs.cloud.google.com/compute/resource-usage
  Tarifs: https://cloud.google.com/compute/disks-image-pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Stockage bloc durable pour les instances [Compute Engine](#compute-engine). Le disque se présente à la VM comme un périphérique bloc ordinaire, mais il vit sur le réseau : les données sont réparties sur plusieurs disques physiques gérés par Google, et le volume survit à la suppression de l'instance.

- **Types de disque.** `pd-balanced` (SSD, équilibre prix-performance), `pd-ssd` (SSD, plus d'IOPS et moins de latence), `pd-standard` (disques durs, bon marché pour les accès séquentiels) et `pd-extreme` (SSD, IOPS provisionnées, réservé à quelques types de machines). Dans la console, le type par défaut est `pd-balanced` ; par `gcloud` et par l'API, c'est `pd-standard`.
- **Performances liées à la capacité.** Le débit et les IOPS d'un volume croissent linéairement avec sa taille, jusqu'aux plafonds imposés par le nombre de vCPU de la VM. Augmenter les performances revient donc à agrandir le disque — sauf sur `pd-extreme`, seul type qui laisse fixer les IOPS séparément. Un disque neuf atteint immédiatement son maximum, sans préchauffage.
- **Zonal ou régional.** Un disque zonal vit dans une seule zone. Un **disque régional** entretient deux fois plus de réplicas, répartis sur deux zones de la même région, en écriture synchrone ; si la zone principale tombe, le volume est rattaché à une VM de la seconde zone. Sa durabilité annoncée par conception va de 99,999 % (standard) à mieux que 99,9999 % (balanced, SSD).
- **Capacités.** Jusqu'à 64 Tio par volume, 127 disques non amorçables zonaux par VM, et 257 Tio cumulés sur une même instance.
- **Instantanés.** Trois formes : *standard* (incrémental, stocké hors de la zone du disque, survit à la suppression du disque), *instantané instantané* (copie locale à la zone, restauration la plus rapide, détruite avec le disque source) et *archive* (le stockage le moins cher, la restauration la plus lente). Un calendrier d'instantanés automatise la capture et l'expiration.
- **Redimensionnement.** La taille d'un disque s'augmente à chaud, disque attaché ou non ; elle ne se réduit jamais. Le système de fichiers invité doit ensuite être étendu, sauf sur les images publiques où le disque de démarrage est redimensionné automatiquement. Changer le type, la zone, le projet ou le mode de chiffrement impose de passer par un instantané et un nouveau disque.
- **Chiffrement** au repos par défaut, avec clés gérées par Google, clés gérées par le client (CMEK) ou clés fournies par le client (CSEK).
- **Facturation** à la capacité provisionnée, du jour de la création à celui de la suppression, que le disque soit attaché ou non et que la VM tourne ou non ; `pd-extreme` facture en plus les IOPS provisionnées.

> [!WARNING]
> Persistent Disk n'est pas proposé sur les séries de machines les plus récentes (C4, C4A, C4D, N4, M4, A4, G4, X4...). Sur ces familles, le stockage bloc durable passe obligatoirement par [Hyperdisk](#hyperdisk).

## À quoi ça sert

- Disques de démarrage et de données des VM des séries qui ne prennent pas encore Hyperdisk : E2, N1, N2, N2D, C2, C2D, M1, M2, T2A, T2D.
- Haute disponibilité à peu de frais pour une charge à état : un disque régional plus un basculement de la VM dans la seconde zone.
- Sauvegardes par instantanés planifiés, et clonage d'un environnement de production vers un bac à sable.
- Partage en lecture seule d'un même volume entre plusieurs VMs (jeux de données de référence, images), ou en multi-écrivain pour les rares applications qui gèrent elles-mêmes le verrouillage.

**À éviter** pour tout nouveau déploiement sur une série de machines récente : [Hyperdisk](#hyperdisk) y est le seul choix, et il découple performances et capacité. À éviter aussi comme espace de travail temporaire à très faible latence — c'est le rôle du [Local SSD](#local-ssd) —, comme système de fichiers partagé en lecture-écriture par plusieurs machines, où il faut [Filestore](#filestore) ou [NetApp Volumes](#netapp-volumes), et pour des fichiers volumineux lus par des services managés, qui appellent [Cloud Storage](#cloud-storage).

> [!TIP]
> Un disque détaché continue d'être facturé au tarif plein. Après une migration, vérifier la liste des disques sans VM (`gcloud compute disks list --filter="-users:*"`) avant de clore le chantier.

## Alternatives en logiciel libre

- **LVM** et **mdadm** : gestion de volumes logiques et agrégats RAID à l'intérieur d'un serveur, avec instantanés à copie sur écriture ; c'est l'équivalent local du redimensionnement et des instantanés.
- **Ceph RBD** : périphériques blocs répartis sur un cluster, attachés à des machines par le réseau, avec instantanés, clones et réplication — le modèle le plus proche de Persistent Disk.
- **DRBD** : réplication bloc synchrone entre deux nœuds, ce que fait un disque régional entre deux zones.
- **Longhorn** et **OpenEBS** : stockage bloc répliqué pour Kubernetes, exposé par CSI comme des volumes persistants.
- **LIO** (`targetcli`) : cible iSCSI du noyau Linux, pour servir un volume bloc à des machines distantes.
