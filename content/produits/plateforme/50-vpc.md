---
title: Virtual Private Cloud
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 340]
  zones:
    - {label: "Réseau VPC — ressource globale du projet", x: 14, y: 16, w: 500, h: 312}
  nodes:
    sub1: {label: "Sous-réseau us-west1", sub: "10.10.0.0/24", icon: categories/networking, x: 36, y: 56, w: 212}
    vm1: {label: "VMs Compute Engine", sub: "IP internes de la plage", icon: produits/compute-engine, x: 290, y: 56, w: 200}
    sub2: {label: "Sous-réseau europe-west1", sub: "10.20.0.0/24", icon: categories/networking, x: 36, y: 146, w: 236}
    gke: {label: "Cluster GKE", sub: "plages secondaires", icon: produits/gke, x: 290, y: 146, w: 200}
    fw: {label: "Politique de pare-feu", sub: "règles entrée/sortie", icon: categories/networking, x: 36, y: 236, w: 236}
    rtr: {label: "Cloud Router", sub: "routes BGP annoncées", icon: categories/networking, x: 290, y: 236, w: 200}
    peervpc: {label: "VPC appairé", sub: "autre projet", external: true, x: 560, y: 56, w: 180}
    onprem: {label: "Réseau sur site", sub: "routeur BGP", external: true, x: 560, y: 236, w: 180}
  flows:
    - {from: sub1, to: vm1, text: "Chaque interface de VM reçoit son adresse IP principale dans la plage du sous-réseau de sa région."}
    - {from: sub2, to: gke, text: "Le cluster puise les adresses de ses pods et de ses services dans les plages secondaires du sous-réseau."}
    - {from: vm1, to: gke, from_offset: -30, text: "Les routes de sous-réseau, créées automatiquement, font communiquer toutes les régions du réseau par adresses internes."}
    - {from: fw, to: vm1, to_offset: 30, control: true, text: "Les règles de pare-feu sont appliquées sur l'interface de chaque instance, avant l'entrée et après la sortie des paquets."}
    - {from: vm1, to: peervpc, text: "L'appairage de VPC échange les routes de sous-réseau avec un réseau d'un autre projet, sans transitivité ni partage des règles de pare-feu."}
    - {from: rtr, to: onprem, text: "Cloud Router annonce les plages du VPC en BGP au réseau distant et installe en retour les préfixes appris comme routes dynamiques."}
docs:
  Page produit: https://cloud.google.com/vpc
  Documentation: https://docs.cloud.google.com/vpc/docs
  Réseaux VPC: https://docs.cloud.google.com/vpc/docs/vpc
  Sous-réseaux: https://docs.cloud.google.com/vpc/docs/subnets
  Routes: https://docs.cloud.google.com/vpc/docs/routes
  Règles de pare-feu VPC: https://docs.cloud.google.com/firewall/docs/firewalls
  Politiques de pare-feu: https://docs.cloud.google.com/firewall/docs/firewall-policies-overview
  Shared VPC: https://docs.cloud.google.com/vpc/docs/shared-vpc
  Appairage de réseaux VPC: https://docs.cloud.google.com/vpc/docs/vpc-peering
  MTU: https://docs.cloud.google.com/vpc/docs/mtu
  Journaux de flux VPC: https://docs.cloud.google.com/vpc/docs/flow-logs
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/networks
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/networks
  Quotas et limites: https://docs.cloud.google.com/vpc/docs/quota
  Tarifs: https://cloud.google.com/vpc/network-pricing
  Notes de version: https://docs.cloud.google.com/vpc/docs/release-notes
---

## Ce que c'est

Le réseau virtuel dans lequel vivent toutes les ressources d'un projet : VMs [Compute Engine](#compute-engine), nœuds [GKE](#gke), services [Cloud Run](#cloud-run), instances [Cloud SQL](#cloud-sql). Il est implémenté par **Andromeda**, la pile de virtualisation réseau de Google : il n'y a ni équipement ni appliance à administrer.

- **Portée.** Un réseau VPC est une ressource **globale**, comme ses routes et ses règles de pare-feu. Les **sous-réseaux** sont **régionaux** : une instance peut se rattacher à n'importe quel sous-réseau d'une région qui contient sa zone. Un projet peut contenir plusieurs réseaux.
- **Mode de création des sous-réseaux.** Un réseau en **mode automatique** reçoit un sous-réseau par région, pris dans le bloc `10.128.0.0/9`, et un nouveau à chaque ouverture de région. Un réseau en **mode personnalisé** ne crée rien tout seul : les plages et les régions sont choisies une à une. La conversion de l'automatique vers le personnalisé est possible, l'inverse non.
- **Plages d'adresses.** Chaque sous-réseau porte une plage IPv4 principale, dont sortent les adresses des VMs, des load balancers internes et du transfert de protocole interne, et peut porter en plus des **plages secondaires**, réservées aux plages d'alias IP — c'est ainsi que GKE adresse ses pods et ses services. Quatre adresses de chaque plage principale sont inutilisables. Les plages IPv6, internes ou externes, ne sont proposées qu'en mode personnalisé, en *dual-stack* ou en IPv6 seul.
- **Routes.** Elles sont évaluées dans un ordre fixe : **routes basées sur des règles** d'abord (sélection par adresse source, destination et protocole, avec un load balancer réseau passthrough interne comme saut suivant), puis les **routes de sous-réseau** (locales, importées d'un appairage ou d'un hub Network Connectivity Center), puis les **routes personnalisées** — statiques créées à la main, ou dynamiques apprises en BGP par un **Cloud Router**. Le **mode de routage dynamique** du réseau décide si les routes apprises s'appliquent à la seule région du Cloud Router (*régional*) ou à toutes (*global*).
- **Pare-feu.** Deux formes coexistent : les **règles de pare-feu VPC**, attachées au réseau, et les **politiques de pare-feu** de Cloud NGFW, qui groupent des règles dans un objet réutilisable — hiérarchiques (organisation ou dossier), réseau globales, réseau régionales, et système régionales gérées par Google. Toutes s'appliquent aussi entre deux VMs du même réseau. Chaque réseau porte des **règles implicites** : tout le trafic entrant est refusé, tout le trafic sortant est autorisé. Les cibles et les sources se désignent par plage d'adresses, étiquette réseau, compte de service ou *Tag* sécurisé.
- **Shared VPC.** Un **projet hôte** porte le réseau ; des **projets de service** y sont rattachés et leurs ressources consomment ses sous-réseaux. L'administration du réseau (sous-réseaux, routes, pare-feu) reste centralisée pendant que chaque équipe crée ses instances dans son propre projet et sur son propre budget. Un projet est hôte ou de service, jamais les deux ; un projet de service n'est rattaché qu'à un seul hôte. L'API nomme la fonction `XPN`.
- **Appairage de réseaux VPC.** Deux réseaux échangent leurs routes de sous-réseau et communiquent en adresses internes, à la même latence et au même débit qu'à l'intérieur d'un réseau, y compris entre projets et organisations. L'appairage **n'est pas transitif**, n'échange ni règles de pare-feu ni noms DNS internes, et ne relie pas deux réseaux en mode automatique, dont les plages se recouvrent.
- **MTU.** 1 460 octets par défaut, réglable de 1 300 à 8 896 octets pour le réseau ; il faut régler l'interface de chaque instance sur la même valeur. Entre réseaux appairés, des MTU différents posent problème : Google Cloud ajuste le MSS des paquets SYN, mais rejette avec un message ICMP tout paquet de plus de 1 600 octets à destination de l'extérieur du réseau.
- **Facturation.** Le réseau, les sous-réseaux, les routes et les règles de pare-feu ne coûtent rien. Ce qui se facture, c'est le trafic : sortie vers Internet, trafic entre zones et entre régions, et les fonctions attachées (Cloud NAT, journaux de flux, load balancers).

> [!WARNING]
> Le réseau `default` créé avec chaque projet est en mode automatique et porte des règles de pare-feu préremplies, dont l'autorisation de SSH depuis n'importe quelle adresse. Pour une production, créer un réseau en mode personnalisé et interdire le réseau par défaut par la contrainte d'organisation `compute.skipDefaultNetworkCreation`.

## À quoi ça sert

- Isoler les environnements : un réseau par domaine de confiance, des sous-réseaux par région et par usage, un plan d'adressage qui ne recoupe pas celui du réseau d'entreprise.
- Donner un socle réseau commun à plusieurs équipes avec Shared VPC : les administrateurs réseau gardent les sous-réseaux et le pare-feu, les équipes applicatives gardent leurs projets et leurs quotas.
- Segmenter le trafic est-ouest par des règles de pare-feu entre étiquettes ou comptes de service, plutôt que par des sous-réseaux séparés.
- Étendre le réseau d'entreprise vers Google Cloud, par [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect), avec échange de routes par Cloud Router.
- Ouvrir un accès privé aux services managés, par [Private Service Connect](#private-service-connect) ou par accès privé à Google, sans adresse IP externe sur les instances.

**À éviter** : relier plus de deux ou trois réseaux par appairage. Comme l'appairage n'est pas transitif, une topologie en maille demande *n(n-1)/2* connexions et un plan d'adressage sans recouvrement ; [Network Connectivity Center](#network-connectivity-center) fait le même travail avec un hub et des spokes. À éviter aussi de donner une adresse IP externe à chaque VM pour qu'elle accède à Internet : [Cloud NAT](#cloud-nat) suffit et réduit la surface exposée. Enfin, l'appairage ne convient pas pour consommer un service managé publié par une autre équipe : il ouvre tout le réseau, là où Private Service Connect n'expose qu'un point d'entrée.

## Alternatives en logiciel libre

- **Open vSwitch** et **OVN** : commutateur virtuel distribué et plan de contrôle associé — réseaux logiques, routeurs, listes de contrôle d'accès ; ce qui se rapproche le plus d'un VPC logiciel.
- **OpenStack Neutron** : la couche réseau d'un cloud IaaS complet, avec réseaux, sous-réseaux, routeurs, groupes de sécurité et adresses flottantes.
- **Calico** et **Cilium** : réseau et filtrage pour Kubernetes, avec des règles par étiquette plutôt que par adresse — le pendant des règles de pare-feu ciblées par étiquette réseau.
- **FRRouting** : pile de routage (BGP, OSPF, IS-IS) pour un routeur logiciel ; l'équivalent de Cloud Router quand il faut échanger des routes avec un autre réseau.
- **nftables** : le filtrage de paquets du noyau Linux, à la maille de l'hôte, là où les règles de pare-feu VPC s'appliquent à l'interface de chaque instance.
- **netplan**, **systemd-networkd**, **cloud-init** : configuration des interfaces et du MTU côté système invité, à aligner sur le réseau.
