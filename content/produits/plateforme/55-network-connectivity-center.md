---
title: Network Connectivity Center
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 330]
  zones:
    - {label: "Organisation Google Cloud", x: 14, y: 16, w: 732, h: 300}
  nodes:
    spoke1: {label: "VPC production", sub: "spoke VPC", icon: categories/networking, x: 40, y: 50, w: 190}
    spoke2: {label: "VPC hors production", sub: "spoke VPC", icon: categories/networking, x: 40, y: 230, w: 212}
    hub: {label: "Hub NCC", sub: "ressource globale", icon: categories/networking, focus: true, x: 300, y: 140, w: 180, h: 68}
    spoke3: {label: "Tunnels HA VPN", sub: "spoke hybride", icon: categories/networking, x: 540, y: 50, w: 190}
    spoke4: {label: "Rattachements VLAN", sub: "spoke hybride", icon: categories/networking, x: 520, y: 230, w: 210}
  flows:
    - {from: spoke1, to: hub, text: "Un réseau VPC rattaché comme spoke exporte au hub les plages de ses sous-réseaux, IPv4 comme IPv6 selon le filtre d'export."}
    - {from: hub, to: spoke2, text: "Le hub réinjecte ces plages dans les autres spokes VPC : la maille complète remplace les appairages deux à deux, sans limite de transitivité."}
    - {from: spoke3, to: hub, text: "Un spoke hybride regroupe des tunnels HA VPN d'un même réseau et publie au hub les routes dynamiques apprises en BGP."}
    - {from: spoke4, to: hub, from_offset: -14, to_offset: -14, text: "Un autre spoke hybride fait de même avec des rattachements VLAN Cloud Interconnect."}
    - {from: hub, to: spoke4, from_offset: 14, to_offset: 14, text: "Le transfert de données site à site réannonce les routes d'un spoke hybride vers les autres : deux sites distants se joignent à travers le réseau de Google."}
docs:
  Page produit: https://cloud.google.com/network-connectivity-center
  Documentation: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center
  Vue d'ensemble: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview
  Spokes VPC: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview
  Topologies prédéfinies: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/connectivity-topologies
  Connectivité site vers cloud: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/site-to-cloud
  Transfert de données site à site: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/data-transfer
  Filtres de spokes: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/spoke-filters-overview
  Router appliance: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/ra-overview
  API REST: https://docs.cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/network-connectivity/hubs
  Quotas et limites: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/quotas
  Tarifs: https://cloud.google.com/network-connectivity/pricing
  Notes de version: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/release-notes
---

## Ce que c'est

Un plan de connectivité en étoile : un **hub**, ressource globale, auquel se rattachent des **spokes** qui représentent des réseaux ou des liaisons. Le hub échange les routes entre eux, ce qui remplace la maille d'appairages de VPC et les topologies de transit montées à la main.

- **Spokes VPC.** Un réseau VPC rattaché au hub exporte ses routes de sous-réseau et importe celles des autres, y compris entre projets et entre organisations. C'est la différence de fond avec l'appairage de VPC : le hub apporte la **transitivité**, et un seul rattachement par réseau remplace *n(n-1)/2* connexions.
- **Spokes hybrides.** Un spoke hybride regroupe des ressources d'un même type : tunnels **HA VPN**, rattachements VLAN **Cloud Interconnect** (Dedicated, Partner, Cross-Cloud) ou VMs **Router appliance**. Un spoke ne mélange pas les types, et doit vivre dans le même projet que le hub. Les routes dynamiques apprises remontent au hub et redescendent vers les autres spokes.
- **Spokes VPC producteur.** Quand un spoke VPC consomme un service publié par un réseau producteur à travers un appairage, un spoke *producteur* rend ce service joignable depuis les autres spokes du hub.
- **Spokes NCC Gateway.** Un type de spoke régional qui insère une inspection de sécurité tierce (*Security Service Edge*) dans le trafic du réseau intercloud.
- **Topologies prédéfinies.** Une topologie en **maille** fait communiquer tous les spokes VPC entre eux ; une topologie en **étoile** sépare un groupe central d'un groupe périphérique, dont les membres ne se joignent qu'en passant par le centre — le modèle d'un réseau de transit avec inspection centralisée.
- **Filtres.** Les **filtres d'export** limitent ce qu'un spoke publie au hub, les **filtres d'import** ce qu'un spoke hybride en reprend ; un spoke hybride peut réannoncer les routes de sous-réseau importées vers le réseau distant.
- **Transfert de données site à site.** Les routes dynamiques apprises par un spoke hybride sont réannoncées aux autres spokes hybrides : deux centres de données éloignés communiquent par le réseau de Google, qui joue le rôle de réseau étendu. Cette fonction exige que tous les spokes hybrides concernés s'appuient sur des ressources d'un même réseau VPC, et n'est proposée qu'à certains emplacements.
- **Administration.** Un spoke créé dans un autre projet que le hub donne lieu à une **proposition**, qu'un administrateur du hub accepte ou refuse. VPC Service Controls s'applique aux spokes entre projets et organisations.
- **Facturation.** Le hub ne coûte rien. Chaque spoke est facturé à l'heure d'activité, plus cher pour un spoke VPC que pour un spoke hybride ; les trois premiers spokes Cloud VPN et les trois premiers spokes Cloud Interconnect sont exonérés. S'y ajoute un tarif au Gio pour tout le trafic qui traverse le hub, imputé au projet d'où il part. Les tunnels, rattachements VLAN et VMs sous-jacents restent facturés par leurs propres produits.

> [!WARNING]
> Un appairage de VPC et un rattachement au même hub ne cohabitent pas entre deux mêmes réseaux : il faut supprimer l'appairage avant de créer les spokes, sauf pour les deux cas prévus — un spoke VPC producteur, et deux spokes du groupe périphérique d'une topologie en étoile.

## À quoi ça sert

- Remplacer une maille d'appairages de VPC devenue ingérable par un hub unique, en gardant la séparation des projets et des équipes.
- Donner à plusieurs réseaux VPC un accès partagé au réseau d'entreprise, sans dupliquer les tunnels ni les rattachements VLAN dans chaque projet.
- Monter un réseau de transit où tout le trafic entre environnements traverse un groupe central, pour l'inspecter ou le filtrer.
- Faire communiquer deux sites distants, ou deux autres clouds, à travers le dorsal de Google plutôt que par l'Internet public.
- Insérer une appliance réseau tierce — pare-feu, SD-WAN — entre des réseaux VPC, par un spoke Router appliance.

**À éviter** quand deux réseaux seulement doivent communiquer : un appairage de VPC ne coûte rien et se règle en deux commandes. À éviter aussi pour donner accès à un service précis publié par une autre équipe — le hub ouvre des réseaux entiers, là où [Private Service Connect](#private-service-connect) n'expose qu'un point d'entrée avec une liste d'autorisation.

## Alternatives en logiciel libre

- **FRRouting** : un réflecteur de routes BGP joue exactement le rôle du hub — recevoir les annonces de chaque site et les redistribuer aux autres, sans maille de sessions.
- **BIRD** : l'autre pile de routage courante pour tenir un point de concentration ou un réflecteur de routes.
- **Open vSwitch** et **OVN** : réseaux logiques et routeurs distribués, pour bâtir soi-même le plan de données d'un réseau de transit.
- **WireGuard** et **strongSwan** : les tunnels que les spokes hybrides représentent, montés et entretenus à la main.
- **Netmaker** et **Nebula** : réseaux superposés en étoile ou en maille, avec un plan de contrôle central qui distribue les routes et les clés.
