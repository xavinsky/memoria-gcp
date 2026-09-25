---
title: Local SSD
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 150, y: 16, w: 596, h: 310}
    - {label: Serveur hôte, x: 175, y: 48, w: 290, h: 252}
  nodes:
    maint: {label: Arrêt ou panne, sub: "événement hôte", external: true, x: 10, y: 150, w: 130}
    vm: {label: VM avec Local SSD, sub: "c4-standard-32-lssd", icon: produits/compute-engine, x: 200, y: 85, w: 240, h: 60}
    lssd: {label: Local SSD Titanium, sub: "4 x 375 Gio, NVMe", icon: categories/storage, focus: true, x: 200, y: 215, w: 240}
    hd: {label: Hyperdisk Balanced, sub: "données durables", icon: produits/hyperdisk, x: 520, y: 85, w: 215}
    gcs: {label: Cloud Storage, sub: "artefacts finaux", icon: produits/cloud-storage, x: 520, y: 215, w: 215}
  flows:
    - {from: hd, to: vm, from_side: left, to_side: right, from_offset: -12, to_offset: -12, text: "Le jeu de données de départ est lu depuis le volume durable attaché à la VM"}
    - {from: vm, to: lssd, text: "Les fichiers temporaires, caches et fichiers de tri sont écrits sur les disques physiquement attachés au serveur hôte"}
    - {from: vm, to: hd, from_side: right, to_side: left, from_offset: 12, to_offset: 12, text: "Tout ce qui doit survivre à la VM est recopié sur le disque durable"}
    - {from: vm, to: gcs, text: "Les artefacts finaux sont déposés dans un bucket avant l'arrêt de l'instance"}
    - {from: maint, to: lssd, control: true, text: "Un arrêt, une suspension ou une panne de l'hôte efface le contenu du Local SSD : rien n'y est sauvegardé"}
docs:
  Page produit: https://cloud.google.com/products/block-storage
  Documentation: https://docs.cloud.google.com/compute/docs/disks/local-ssd
  Choisir un type de disque: https://docs.cloud.google.com/compute/docs/disks
  Ajouter des disques Local SSD: https://docs.cloud.google.com/compute/docs/disks/add-local-ssd
  Optimiser les performances: https://docs.cloud.google.com/compute/docs/disks/optimizing-local-ssd-performance
  Mesurer les performances: https://docs.cloud.google.com/compute/docs/disks/benchmarking-local-ssd-performance
  API REST instances: https://docs.cloud.google.com/compute/docs/reference/rest/v1/instances
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances
  Client Python: https://docs.cloud.google.com/python/docs/reference/compute/latest
  Quotas et limites: https://docs.cloud.google.com/compute/resource-usage
  Tarifs: https://cloud.google.com/compute/disks-image-pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Stockage bloc **éphémère** : des SSD physiquement attachés au serveur qui héberge l'instance. Pas de réseau entre la VM et le disque, donc la latence la plus basse et les IOPS les plus élevées de toute l'offre [Compute Engine](#compute-engine) — au prix d'une donnée qui ne survit pas à l'instance.

- **Deux générations.** *Titanium SSD* utilise le déport d'entrées-sorties Titanium et équipe les séries récentes : C4, C4A, C4D, C4N, Z3, Z4D, H4D, A4X, A4X Max, G4. *Local SSD*, la génération précédente, fournit des partitions de 375 Gio montées en NVMe ou en SCSI sur les séries plus anciennes.
- **Attaché à la création seulement.** Le nombre de disques est déterminé par le type de machine — souvent un suffixe `-lssd` dans son nom. On ne peut ni en ajouter ni en retirer après la création de l'instance.
- **Performances cumulatives.** Le débit et les IOPS montent avec le nombre de disques attachés : sur une `c4-standard-192-lssd`, 32 disques Titanium totalisent 12 000 Gio et dépassent 4,8 millions d'IOPS en lecture.
- **Persistance des données.** Le contenu est conservé lors d'un redémarrage du système invité, lors d'une migration à chaud pour maintenance de l'hôte, et lorsqu'on choisit explicitement de le préserver à l'arrêt ou à la suspension. Il est perdu à la suppression de l'instance, et il peut l'être après une erreur d'hôte, selon le délai de récupération configuré et le redémarrage automatique.
- **Sans sauvegarde possible.** Ni instantané, ni clone, ni image machine : le Local SSD est invisible pour tous les mécanismes de sauvegarde de Compute Engine.
- **Chiffrement** systématique au repos, avec les clés de Google exclusivement — ni CMEK, ni CSEK.
- **Limites.** Indisponible sur les types de machines à cœur partagé, et impossible comme volume de démarrage.
- **Facturation** à la capacité attachée, pour toute la durée de vie de l'instance.

> [!WARNING]
> Le Local SSD n'est pas répliqué. Toute donnée qu'on n'accepte pas de perdre doit être écrite en parallèle sur [Hyperdisk](#hyperdisk), [Persistent Disk](#persistent-disk) ou [Cloud Storage](#cloud-storage), au fil de l'eau et non en fin de traitement.

## À quoi ça sert

- Espace de travail des traitements par lots : tris externes, jointures qui débordent de la mémoire, décompression de gros jeux de données.
- Caches et bases de données optimisées pour le flash, où le moteur reconstruit son état à partir d'une source durable.
- `tempdb` de SQL Server, tables temporaires et fichiers de *spill* des moteurs analytiques.
- Cache de blocs partagé sur les nœuds d'un cluster de calcul ou d'entraînement, devant un système de fichiers parallèle.
- Stockage de travail des nœuds [GKE](#gke) éphémères, monté en volume local.

**À éviter** pour toute donnée de référence, tout état applicatif et toute sauvegarde : la disparition n'est pas un incident, c'est le comportement normal. Pour un volume durable attaché à une VM, [Hyperdisk](#hyperdisk) ; pour un partage entre machines, [Filestore](#filestore) ou [Managed Lustre](#managed-lustre) ; pour des fichiers à conserver, [Cloud Storage](#cloud-storage).

## Alternatives en logiciel libre

- **tmpfs** et **RAM disk** : espace de travail en mémoire, plus rapide encore mais limité par la taille de la RAM ; Compute Engine le permet aussi dans la VM.
- **bcache**, **dm-cache**, **LVM cache** : un SSD local placé en cache devant un volume durable — exactement l'usage « cache devant le stockage réseau ».
- **OpenCAS** (Open Cache Acceleration Software) : cache de blocs sur NVMe local, orienté charges d'entreprise.
- **mdadm** : agrégation en RAID 0 de plusieurs disques locaux pour cumuler leur débit, ce que font les images qui exposent plusieurs partitions de 375 Gio.
- **ZFS** avec un *special vdev* ou un L2ARC sur NVMe local, pour accélérer un pool dont les données vivent ailleurs.
