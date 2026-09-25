---
title: VMware Engine
subgroup: Migration et hybride
icon: categories/hybrid-multicloud
deprecie: "Ne se justifie que par un parc VMware existant, avec une licence VMware Cloud Foundation à acheter chez Broadcom. Pour un projet neuf, [Compute Engine](#compute-engine) ou [GKE](#gke)."
schema:
  size: [760, 350]
  zones:
    - {label: Centre de données, x: 6, y: 80, w: 178, h: 160}
    - {label: Projet GCP, x: 204, y: 10, w: 542, h: 330}
    - {label: Réseau VMware Engine, x: 218, y: 70, w: 250, h: 190}
  nodes:
    onprem: {label: vSphere sur site, sub: "vCenter, HCX", external: true, x: 18, y: 128, w: 154, h: 64}
    ic: {label: Cloud Interconnect, sub: "ou Cloud VPN", icon: categories/networking, x: 500, y: 26, w: 230}
    gcve: {label: VMware Engine, sub: "cloud privé vSphere", icon: categories/hybrid-multicloud, focus: true, x: 240, y: 126, w: 206, h: 70}
    vpc: {label: VPC, sub: "appairage de réseaux", icon: categories/networking, x: 500, y: 132, w: 230}
    svc: {label: Compute Engine, sub: "services et VM Google", icon: produits/compute-engine, x: 500, y: 250, w: 230}
    bdr: {label: Backup and DR, sub: "sauvegarde des VM", icon: categories/storage, x: 240, y: 272, w: 206}
  flows:
    - {from: onprem, to: ic, from_side: top, to_side: left, from_offset: 58, text: "Le centre de données se raccorde au cloud par Cloud Interconnect ou Cloud VPN"}
    - {from: ic, to: gcve, control: true, from_side: bottom, to_side: top, text: "Le lien rejoint le réseau VMware Engine, qui route vers les clouds privés de la région"}
    - {from: onprem, to: gcve, text: "HCX déplace les VM à chaud (vMotion) ou par réplication, sans changer leur format ni leur adresse IP"}
    - {from: gcve, to: vpc, text: "Le réseau VMware Engine est appairé à un réseau VPC : les VM vSphere joignent les ressources du projet en adresses privées"}
    - {from: vpc, to: svc, text: "Les applications migrées appellent les services Google Cloud ou des VM Compute Engine"}
    - {from: gcve, to: bdr, text: "Backup and DR sauvegarde les VM du cloud privé, en complément d'un outil de sauvegarde tiers compatible vSphere"}
docs:
  Page produit: https://cloud.google.com/vmware-engine
  Documentation: https://docs.cloud.google.com/vmware-engine/docs
  Vue d'ensemble: https://docs.cloud.google.com/vmware-engine/docs/overview
  Clouds privés: https://docs.cloud.google.com/vmware-engine/docs/concepts-private-cloud
  Types de nœuds: https://docs.cloud.google.com/vmware-engine/docs/concepts-node-types
  Composants VMware: https://docs.cloud.google.com/vmware-engine/docs/concepts-vmware-components
  Réseaux VMware Engine: https://docs.cloud.google.com/vmware-engine/docs/networking/vmware-engine-network
  Clouds privés étendus: https://docs.cloud.google.com/vmware-engine/docs/concepts-stretched-private-cloud
  Options de migration: https://docs.cloud.google.com/vmware-engine/docs/concepts-migration-options
  API REST: https://docs.cloud.google.com/vmware-engine/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/vmware
  Client Python: https://docs.cloud.google.com/python/docs/reference/vmwareengine/latest
  Quotas et limites: https://docs.cloud.google.com/vmware-engine/quotas
  Tarifs: https://cloud.google.com/vmware-engine/pricing
  Notes de version: https://docs.cloud.google.com/vmware-engine/docs/release-notes
---

## Ce que c'est

**Google Cloud VMware Engine** fournit une pile **VMware Cloud Foundation** complète sur des serveurs *bare metal* dédiés, dans les régions Google Cloud. Google installe, met à jour et surveille l'infrastructure ; le client administre ses VM avec les outils VMware habituels.

- **Cloud privé** (*private cloud*) : une pile VMware isolée — hyperviseur ESXi, vCenter Server, stockage vSAN, réseau NSX, outil de migration HCX — avec son propre vCenter. Tous ses nœuds sont dans la même région. Le client s'y connecte avec le compte `CloudOwner@gve.local`, aux droits restreints ; des comptes de solution servent aux tâches qui en demandent plus (sources d'identité, gestion des utilisateurs).
- **Nœuds** : l'unité de consommation. Nœuds hyperconvergés `ve1-standard-72` (72 vCPU, 768 Gio, 19,2 To bruts) ou `ve2-*` (64 à 128 vCPU, 2 048 Gio, 12,8 à 51,2 To selon la taille *small*, *standard*, *large*, *mega*), et nœuds de **stockage seul** (`-so`) pour ajouter de la capacité vSAN sans calcul. Le nombre de cœurs actifs peut être réduit pour limiter le coût des licences logicielles facturées au cœur.
- **Limites** : 3 nœuds minimum par cluster (pour l'engagement de disponibilité), 32 nœuds par cluster, 128 nœuds et 32 clusters par cloud privé. Un cluster ne mélange pas deux types de nœuds hyperconvergés. vSAN doit garder 20 % d'espace libre. Un **cloud privé à un nœud**, sans engagement de disponibilité ni mises à jour, sert aux essais.
- **Cloud privé étendu** (*stretched*) : les clusters sont répartis à parts égales sur deux zones d'une région (6 à 32 nœuds), avec un nœud témoin dans une troisième zone ; il survit à la perte d'une zone. Ce choix se fait à la création et n'est pas réversible.
- **Réseau** : un **réseau VMware Engine** global relie les clouds privés entre eux, aux réseaux VPC par appairage et au site du client par Cloud VPN ou Cloud Interconnect. Des **règles réseau** ouvrent l'accès internet et les adresses IP publiques, des règles d'accès externe filtrent le trafic entrant. Chaque cloud privé a une zone Cloud DNS pour ses appliances de gestion.
- **Stockage externe** : en plus de vSAN, des datastores NFS sur [NetApp Volumes](#netapp-volumes) ou [Filestore](#filestore).
- **Facturation** : par nœud et à l'heure, à la demande ou avec un engagement d'un an (ou de trois ans selon le type de nœud). Le prix du nœud n'inclut pas le logiciel VMware : il faut apporter une souscription VMware Cloud Foundation achetée chez Broadcom (licence *portable*). La sauvegarde Backup and DR est une option facturée par nœud.

## À quoi ça sert

- Sortir d'un centre de données sans toucher aux applications : les VM passent de vSphere à vSphere avec HCX, sans conversion, avec les mêmes outils d'exploitation, de sauvegarde et de supervision.
- Absorber un pic de capacité ou un environnement temporaire pour un parc vSphere existant.
- Héberger un site de reprise d'activité ou des postes virtuels pour une infrastructure VMware sur site.
- Faire tourner des bases Oracle ou SQL Server déjà virtualisées sous vSphere, avec un contrôle du nombre de cœurs pour les licences.
- Servir d'étape intermédiaire : migrer vite sous vSphere, puis moderniser les applications une à une vers les services Google Cloud.

**À éviter** pour un projet neuf ou une application qu'on accepte de convertir : [Compute Engine](#compute-engine) facture à la seconde, sans minimum de trois serveurs dédiés ni licence VMware, et [Migrate to Virtual Machines](#migrate-to-virtual-machines) y transfère les VM vSphere existantes. Pour des applications en conteneurs, [GKE](#gke). VMware Engine se justifie quand la compatibilité vSphere elle-même est la contrainte : outillage, contrats, compétences ou calendrier qui interdisent la conversion.

> [!WARNING]
> Le minimum de trois nœuds dédiés fixe un plancher de coût élevé, facturé même à vide, auquel s'ajoute la souscription VMware Cloud Foundation. Chiffrer un projet VMware Engine sur la base d'un parc de VM, et non d'une VM isolée.

## Alternatives en logiciel libre

- **Proxmox VE** : virtualisation KVM et conteneurs LXC avec cluster, migration à chaud, stockage Ceph intégré et sauvegardes ; l'alternative la plus directe à vSphere pour un parc d'entreprise de taille moyenne.
- **OpenStack** : cloud IaaS complet (Nova, Cinder, Neutron), plus lourd à exploiter mais proche d'une offre de cloud privé.
- **oVirt** : gestionnaire de virtualisation KVM d'entreprise, conçu comme équivalent de vCenter.
- **KubeVirt** : VM exécutées dans Kubernetes, pour faire cohabiter les VM reprises et les conteneurs sur une même plateforme.
- **Ceph** : stockage distribué bloc, objet et fichier, l'équivalent libre de vSAN dans une architecture hyperconvergée.
