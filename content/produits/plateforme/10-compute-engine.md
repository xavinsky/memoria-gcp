---
title: Compute Engine
subgroup: Calcul
icon: produits/compute-engine
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    users: {label: Utilisateurs, sub: trafic web, external: true, x: 10, y: 126, w: 130}
    tmpl: {label: Modèle d'instance, sub: "image, type de machine", icon: categories/compute, x: 192, y: 36, w: 210}
    lb: {label: Cloud Load Balancing, sub: répartition du trafic, icon: categories/networking, x: 192, y: 120, w: 206}
    mon: {label: Cloud Monitoring, sub: métriques d'autoscaling, icon: categories/observability, x: 430, y: 36, w: 215}
    gce: {label: Compute Engine, sub: groupe d'instances géré, icon: produits/compute-engine, focus: true, x: 430, y: 118, w: 200, h: 60}
    disk: {label: Hyperdisk, sub: disques de données, icon: produits/hyperdisk, x: 430, y: 216, w: 190}
  flows:
    - {from: tmpl, to: gce, text: "Le modèle d'instance fige l'image de démarrage, le type de machine, les disques et le réseau ; le groupe crée toutes ses VM à l'identique"}
    - {from: users, to: lb, text: "Le trafic entrant arrive sur l'adresse du load balancer"}
    - {from: lb, to: gce, text: "Le load balancer répartit les requêtes sur les instances du groupe déclarées saines par le contrôle d'état"}
    - {from: gce, to: disk, text: "Chaque instance monte un volume Hyperdisk pour ses données durables, indépendant du cycle de vie de la VM"}
    - {from: gce, to: mon, from_offset: -40, to_offset: -40, text: "Les métriques d'utilisation remontent à Cloud Monitoring"}
    - {from: mon, to: gce, from_offset: 40, to_offset: 40, control: true, text: "L'autoscaler ajuste le nombre d'instances entre les bornes de la règle de mise à l'échelle"}
docs:
  Page produit: https://cloud.google.com/products/compute
  Documentation: https://docs.cloud.google.com/compute/docs
  Vue d'ensemble: https://docs.cloud.google.com/compute/docs/overview
  Familles de machines: https://docs.cloud.google.com/compute/docs/machine-resource
  Images d'OS: https://docs.cloud.google.com/compute/docs/images
  Stockage par blocs: https://docs.cloud.google.com/compute/docs/disks
  Groupes d'instances gérés: https://docs.cloud.google.com/compute/docs/instance-groups
  Autoscaling: https://docs.cloud.google.com/compute/docs/autoscaler
  Réservations: https://docs.cloud.google.com/compute/docs/instances/reservations-overview
  Remises à l'usage soutenu: https://docs.cloud.google.com/compute/docs/sustained-use-discounts
  Engagements d'utilisation: https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute
  Bibliothèques clientes: https://docs.cloud.google.com/compute/docs/api/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/compute/latest
  Quotas et limites: https://docs.cloud.google.com/compute/resource-usage
  Tarifs: https://cloud.google.com/products/compute/pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Service d'infrastructure (*IaaS*) : des instances de machine virtuelle sur hyperviseur KVM, et des instances *bare metal* sans couche d'hyperviseur. On choisit une zone, un type de machine, une image de démarrage, des disques et un réseau ; le reste du système est à la charge du projet.

- **Familles de machines.** Chaque famille vise un profil de charge : *usage général* (séries E, N, C4, C4A), *optimisée pour le calcul* (C2, C2D, H3, H4D), *optimisée pour le réseau* (C4N), *optimisée pour le stockage* (Z3, Z4D), *optimisée pour la mémoire* (M1 à M4, jusqu'à 12 To de RAM) et *optimisée pour les accélérateurs* (A2 à A4X, G2, G4 — voir [Cloud GPUs](#cloud-gpus)). Une famille se décline en séries (génération et processeur : Intel, AMD, Arm), une série en types de machines prédéfinis. Le suffixe donne le rapport mémoire/vCPU : `highcpu`, `standard`, `highmem`, `megamem`, `hypermem`, `ultramem`. Certaines séries acceptent un **type de machine personnalisé** (vCPU et mémoire choisis).
- **Disques.** Stockage par blocs *temporaire* avec les [Local SSD](#local-ssd) et Titanium SSD, attachés physiquement au serveur hôte, les plus rapides mais perdus dès que la VM s'arrête ; stockage *durable* avec [Hyperdisk](#hyperdisk), dont la capacité et les performances se règlent séparément, et [Persistent Disk](#persistent-disk) [!DECONSEILLE], dont le débit dépend de la taille provisionnée et qui ne couvre pas les séries récentes. Les volumes durables sont chiffrés au repos et en transit, détachables à chaud, et réplicables sur deux zones.
- **Images.** Images publiques Linux et Windows maintenues par Google, les communautés et des éditeurs ; certaines sont *premium* et facturées en plus. Les **familles d'images** (`--image-family`) pointent toujours sur la version la plus récente non dépréciée. Une **image personnalisée** se crée à partir d'un disque de démarrage ou s'importe depuis un disque virtuel existant.
- **Groupes d'instances gérés (MIG).** Un groupe maintient N instances conformes à un modèle d'instance. Il répare automatiquement les VM disparues ou déclarées défaillantes par un contrôle d'état applicatif, se déploie sur une zone ou sur plusieurs zones d'une région (jusqu'à 1 000 VM en zonal, 2 000 en régional par défaut), sert de *backend* aux load balancers, et met à jour son parc par déploiement progressif ou *canary*. Un MIG **avec état** préserve le nom, les disques et les métadonnées de chaque instance à travers les redémarrages et les recréations.
- **Autoscaling.** L'autoscaler d'un MIG ajoute ou retire des instances selon un ou plusieurs signaux : utilisation CPU moyenne, capacité de service du load balancer HTTP, métriques Cloud Monitoring, calendriers de capacité minimale, et pour un groupe zonal une file de travail Pub/Sub. Le *mode prédictif* anticipe les montées en charge quotidiennes ou hebdomadaires.
- **Modèles de provisionnement**, choisis à la création de l'instance : **standard**, **Spot** (voir [Spot VMs](#spot-vms)), **Flex-start** (attente d'une fenêtre de capacité, exécution de 10 minutes à 7 jours) et **reservation-bound** (lié à une réservation obtenue pour une période donnée).
- **Réservations.** Une réservation bloque de la capacité dans une zone pour des VM d'une configuration précise. Elle est consommée *automatiquement* par toute VM compatible ou *ciblée* nommément, limitée au projet ou partagée entre projets, éventuellement avec une règle de placement *compact*. La capacité réservée est facturée au tarif à la demande, consommée ou non.
- **Facturation.** À la seconde, avec une minute minimum. Les **remises à l'usage soutenu** (SUD) s'appliquent automatiquement aux séries N1, N2, N2D, C2, M1, M2 et aux nœuds à locataire unique dès 25 % du mois d'utilisation, jusqu'à 20 % ou 30 % de remise nette selon la série. Les **engagements** (CUD) d'un ou trois ans se déclinent en engagements *sur ressources* (vCPU, mémoire, GPU, Local SSD, nœuds dédiés, licences d'OS — jusqu'à 55 %, 70 % sur les séries optimisées pour la mémoire) et en engagements *flexibles sur la dépense*, valables sur Compute Engine, GKE et Cloud Run sans contrainte de région ni de configuration.

> [!TIP]
> Les remises à l'usage soutenu ne s'appliquent pas aux ressources déjà couvertes par un engagement, et les séries récentes (C4, N4, C3...) n'y sont pas éligibles du tout : sur ces machines, seul un engagement fait baisser la facture.

## À quoi ça sert

- Héberger des applications qui ont besoin d'un système d'exploitation complet : progiciels, serveurs d'applications, bases installées à la main, logiciels sous licence par cœur.
- Reprendre à l'identique un parc de machines existant lors d'une migration *lift and shift*, avec des images importées depuis l'infrastructure de départ.
- Servir une application web derrière un load balancer, avec un groupe régional qui se répare et se redimensionne tout seul.
- Fournir des nœuds de calcul à des charges qui pilotent elles-mêmes leur parc : clusters de calcul, rendus, simulations, entraînement de modèles.
- Obtenir du matériel qu'aucun service managé n'expose : très grosse mémoire, *bare metal*, virtualisation imbriquée, accélérateurs.

**À éviter** quand l'application tient dans un conteneur sans état : un service [Cloud Run](#cloud-run) ou un cluster [GKE](#gke) coûte moins cher en exploitation qu'un parc de VM à mettre à jour et à surveiller. À éviter aussi pour exécuter des traitements par lots que l'on orchestre soi-même à coups de scripts de démarrage : [Batch](#batch) crée et détruit les VM à la place du projet. Pour de la donnée analytique ou du traitement de flux, préférer les services dédiés ([BigQuery](#bigquery), [Dataflow](#dataflow), [Managed Service for Apache Spark](#managed-service-for-apache-spark)) plutôt qu'un cluster monté sur des instances.

## Alternatives en logiciel libre

- **KVM** + **libvirt** : l'hyperviseur qu'utilise Compute Engine lui-même ; la base de presque toutes les alternatives ci-dessous.
- **Proxmox VE** : plateforme de virtualisation clés en main (KVM et conteneurs LXC), avec interface web, cluster, migration à chaud et sauvegardes ; le plus direct pour un petit parc.
- **OpenStack** : l'équivalent le plus complet d'un cloud IaaS — Nova pour les instances, Glance pour les images, Cinder pour le stockage par blocs, Neutron pour le réseau, Heat pour les modèles. C'est aussi le plus lourd à exploiter.
- **Apache CloudStack** et **oVirt** : gestionnaires de virtualisation d'entreprise, orientés hyperviseurs et pools de stockage plutôt que API cloud.
- **Incus** (fork communautaire de LXD) : machines virtuelles et conteneurs système gérés par une même API, avec instantanés et migration.
- **diskimage-builder** et **cloud-init** : construction d'images de machines et personnalisation au premier démarrage, l'équivalent des images personnalisées et des scripts de démarrage.

