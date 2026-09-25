---
title: Migrate to Virtual Machines
subgroup: Migration et hybride
icon: categories/migration
aka: Migrate for Compute Engine
schema:
  size: [760, 340]
  zones:
    - {label: Sur site (vSphere), x: 6, y: 16, w: 200, h: 196}
    - {label: AWS ou Azure, x: 6, y: 228, w: 200, h: 96}
    - {label: Projet GCP, x: 226, y: 16, w: 528, h: 308}
  nodes:
    vs: {label: vCenter, sub: "VM VMware en service", external: true, x: 16, y: 44, w: 184}
    conn: {label: Migrate Connector, sub: "appliance OVA", icon: categories/migration, x: 16, y: 138, w: 184}
    cloud: {label: VM sources, sub: "EC2, VM Azure", external: true, x: 16, y: 254, w: 184}
    m2vm: {label: Migrate to Virtual Machines, sub: "réplication, clones, bascule", icon: categories/migration, focus: true, x: 250, y: 130, w: 256, h: 70}
    test: {label: Compute Engine, sub: "clone de test", icon: produits/compute-engine, x: 552, y: 44, w: 186}
    prod: {label: Compute Engine, sub: "VM de production", icon: produits/compute-engine, x: 552, y: 236, w: 186}
  flows:
    - {from: vs, to: conn, text: "Le Migrate Connector, déployé dans vSphere, lit les disques des VM par les API vSphere, sans arrêter la source"}
    - {from: conn, to: m2vm, text: "Première réplication complète, puis réplications incrémentales (toutes les deux heures par défaut) des seuls blocs modifiés, en HTTPS"}
    - {from: cloud, to: m2vm, from_side: right, to_side: bottom, text: "Pour AWS et Azure, pas de connecteur : le service prend des snapshots des disques par les API du fournisseur et lit leurs blocs"}
    - {from: m2vm, to: test, text: "Clone de test : une VM créée à partir des dernières données répliquées, dans un réseau isolé, pendant que la source continue de tourner"}
    - {from: m2vm, to: prod, text: "Bascule : arrêt de la source, dernière réplication, adaptation de l'OS et création de la VM de production"}
docs:
  Page produit: https://cloud.google.com/products/cloud-migration/virtual-machines
  Documentation: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0
  Architecture: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/discover/architecture
  Cycle de migration: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/discover/lifecycle
  Migrate Connector: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/migrate/migrate-connector
  Systèmes pris en charge: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/discover/supported-os-versions
  Adaptations de l'OS: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/resources/vm-adaptations
  Import d'images disque: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/migrate/image_import
  API REST: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/reference/rest/v1
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/migration/vms
  Client Python: https://docs.cloud.google.com/python/docs/reference/vmmigration/latest
  Quotas et limites: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/resources/quotas
  Tarifs: https://cloud.google.com/migrate/virtual-machines/pricing
  Notes de version: https://docs.cloud.google.com/migrate/virtual-machines/docs/5.0/resources/release-notes
---

## Ce que c'est

Service de migration de VM par réplication de disques, vers Compute Engine : il reprend une machine telle quelle (*lift and shift*), avec des retouches automatiques du système pour qu'elle démarre sur Google Cloud. Tout se pilote depuis la console, l'API VM Migration (`vmmigration.googleapis.com`) ou `gcloud migration vms`.

- **Sources** : centre de données vSphere, cloud privé Google Cloud VMware Engine, instances AWS EC2, VM Azure. Une **source** se déclare dans un **projet hôte**, qui pilote la migration ; les VM arrivent dans un ou plusieurs **projets cibles**. Au plus 15 sources AWS et Azure par projet hôte.
- **Migrate Connector** : pour vSphere et VMware Engine, une appliance OVA à installer sur chaque vCenter (4 vCPU, 16 Go de RAM, 30 Go de datastore). Elle inventorie les VM, lit leurs disques, arrête la source à la bascule, et sort en HTTPS (port 443) par internet, VPN, accès privé à Google ou Interconnect. Pour AWS et Azure, le service passe par les API du fournisseur, avec des identifiants délégués.
- **Réplication** : une première copie complète des disques, puis des réplications incrémentales à intervalle fixe (deux heures par défaut) qui ne transfèrent que les blocs modifiés (*Change Block Tracking* sur vSphere). La réplication se met en pause et reprend à la demande.
- **Cycle d'une VM** : embarquement, réplication, choix des **détails cibles** (projet, type de machine, disques, réseau, conversion BIOS vers UEFI), **clones de test** facultatifs, **bascule** (*cut-over*), finalisation. Une VM en cours de migration expire après 100 jours, prolongeables.
- **Adaptation de l'OS** : à chaque réplication, le service ajuste la configuration réseau, installe l'agent invité Compute Engine et active la console série. Linux (RHEL, CentOS, Rocky, Alma, Debian, Ubuntu, SUSE…) et Windows Server, en x86 et en Arm pour les sources cloud.
- **Groupes** : les mêmes étapes appliquées à un lot de VM, pour migrer par vagues.
- **Autres usages** : migrer seulement les disques d'une VM vers des volumes Persistent Disk, importer une image disque (VMDK, VHD, VHDX, QCOW2, VDI, RAW) comme image Compute Engine.
- **Facturation** : le service est gratuit pour une migration vers Google Cloud. On paie les VM de test et de production, les disques et le réseau, et côté AWS ou Azure les snapshots, volumes, instances temporaires et le trafic sortant.

## À quoi ça sert

- Sortir d'un centre de données VMware vers Compute Engine sans réinstaller les serveurs.
- Rapatrier des instances EC2 ou des VM Azure sur Google Cloud.
- Tester une VM migrée plusieurs fois avant la bascule, sur des données à jour, avec une coupure réduite à l'arrêt de la source et à la dernière synchronisation.
- Transformer une image disque existante (*golden image*) en image Compute Engine.

**À éviter** quand on veut garder vSphere, ses outils et ses licences : [VMware Engine](#vmware-engine) héberge les VM telles quelles, sans conversion. Pour une base de données, [Database Migration Service](#database-migration-service) réplique au niveau du moteur et bascule vers un service géré. Pour une application à conteneuriser, reconstruire l'image et la déployer sur [Cloud Run](#cloud-run) ou [GKE](#gke).

> [!WARNING]
> Un clone de test est une copie de la source encore en service, avec les mêmes noms et parfois les mêmes identifiants : le lancer dans un réseau VPC isolé, sans accès aux systèmes de production, pour éviter les doubles écritures et les conflits d'adresses.

## Alternatives en logiciel libre

- **virt-v2v** (projet libguestfs) : convertit une VM VMware, Xen ou Hyper-V vers KVM en adaptant pilotes et chargeur de démarrage, sans réplication à chaud.
- **qemu-img** : conversion de formats de disque (VMDK, VHD, QCOW2, RAW), avant un import d'image.
- **Coriolis** (Cloudbase Solutions, AGPL) : migration de VM entre VMware, OpenStack et clouds publics, avec réplication incrémentale.
- **Forklift** (Migration Toolkit for Virtualization) : migration de VM VMware ou oVirt vers KubeVirt, sur Kubernetes.
