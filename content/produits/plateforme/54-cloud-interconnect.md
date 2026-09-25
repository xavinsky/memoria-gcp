---
title: Cloud Interconnect
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 340]
  zones:
    - {label: "Installation de colocation ou autre cloud", x: 10, y: 16, w: 250, h: 310}
    - {label: "Réseau Google", x: 296, y: 16, w: 190, h: 310}
    - {label: "Projet GCP — réseau VPC", x: 522, y: 16, w: 228, h: 310}
  nodes:
    onprem: {label: "Routeur sur site", sub: "circuits 10 à 400 G", external: true, x: 30, y: 70, w: 210}
    other: {label: "Autre cloud", sub: "AWS, Azure, OCI", external: true, x: 30, y: 190, w: 210}
    edge: {label: "Interconnexion", sub: "circuits, LACP", icon: categories/networking, focus: true, x: 316, y: 130, w: 160, h: 68}
    att: {label: "Rattachement VLAN", sub: "802.1Q, capacité", icon: categories/networking, x: 542, y: 44, w: 196}
    rtr: {label: "Cloud Router", sub: "session BGP", icon: categories/networking, x: 542, y: 130, w: 196}
    vms: {label: "VMs et services", sub: "adresses internes", icon: produits/compute-engine, x: 542, y: 216, w: 196}
  flows:
    - {from: onprem, to: edge, to_offset: -16, text: "Un ou plusieurs circuits Ethernet relient l'équipement du client à un routeur périphérique de Google, dans la même installation de colocation."}
    - {from: other, to: edge, to_offset: 16, text: "Avec Cross-Cloud Interconnect, c'est Google qui pose la liaison jusqu'au réseau de l'autre fournisseur de cloud."}
    - {from: edge, to: att, text: "Un rattachement VLAN découpe une part de la capacité de la connexion et la rattache à un réseau VPC donné."}
    - {from: att, to: rtr, text: "Le rattachement porte une session BGP entre le routeur du client et un Cloud Router régional, qui échangent leurs préfixes dans les deux sens."}
    - {from: rtr, to: vms, text: "Les préfixes appris deviennent des routes dynamiques : les ressources du VPC joignent le site par adresses internes, sans tunnel ni traduction d'adresses."}
docs:
  Page produit: https://cloud.google.com/hybrid-connectivity
  Documentation: https://docs.cloud.google.com/network-connectivity/docs/interconnect
  Vue d'ensemble: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/overview
  Dedicated Interconnect: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/dedicated-overview
  Partner Interconnect: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/partner-overview
  Cross-Cloud Interconnect: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/cci-overview
  Choisir un produit de connectivité: https://docs.cloud.google.com/network-connectivity/docs/how-to/choose-product
  Emplacements de colocation: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/choosing-colocation-facilities
  Résilience et SLA: https://docs.cloud.google.com/network-connectivity/docs/interconnect/tutorials/dedicated-creating-9999-availability
  MACsec: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/macsec-overview
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/interconnects
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/interconnects
  Quotas et limites: https://docs.cloud.google.com/network-connectivity/docs/interconnect/quotas
  Tarifs: https://cloud.google.com/network-connectivity/docs/interconnect/pricing
  Notes de version: https://docs.cloud.google.com/network-connectivity/docs/interconnect/release-notes
---

## Ce que c'est

Liaisons physiques privées entre le réseau de Google et un autre réseau : un centre de données d'entreprise, ou celui d'un autre fournisseur de cloud. Le trafic ne passe pas par l'Internet public, les adresses internes du VPC sont directement joignables, et le tarif de sortie est réduit par rapport à Internet.

- **Dedicated Interconnect.** Une connexion physique directe. L'équipement du client rencontre celui de Google dans une **installation de colocation**, en fibre monomode : circuits de 10 Gbit/s (10GBASE-LR), 100 Gbit/s (100GBASE-LR4) ou 400 Gbit/s (400GBASE-LR4), jusqu'à huit circuits par connexion — donc 80, 800 ou 3 200 Gbit/s. L'équipement doit gérer LACP, même sur un seul circuit, le VLAN 802.1Q, l'adressage IPv4 lien-local et eBGP multisaut. Le type de lien est figé à la commande.
- **Partner Interconnect.** Le raccordement passe par un **opérateur partenaire** déjà présent chez Google : pas de présence en colocation à monter, et des rattachements de **50 Mbit/s à 50 Gbit/s**, selon ce que le partenaire propose à l'emplacement choisi. C'est la porte d'entrée pour les sites qui n'ont ni le volume ni l'équipement d'une liaison dédiée.
- **Cross-Cloud Interconnect.** Google pose et exploite une liaison dédiée entre son réseau et celui d'un autre fournisseur de cloud, sans routeur à déployer en colocation ni contrat tiers à négocier. Il existe aussi une variante *partenaire* pour AWS et OCI, où la connexion est mutualisée via un opérateur. Google ne garantit rien au-delà du point où la liaison atteint le réseau de l'autre fournisseur.
- **Cross-Site Interconnect** relie entre eux deux sites du client à travers le réseau de Google, sans passer par un VPC ; le MTU y monte à 9 000 octets.
- **Rattachements VLAN.** Une connexion physique ne porte rien à elle seule : chaque **rattachement VLAN** découpe une capacité, la rattache à un réseau VPC et ouvre une session BGP avec un **Cloud Router** régional. Les préfixes du site deviennent des routes dynamiques du VPC, et le Cloud Router annonce en retour les plages des sous-réseaux selon le mode de routage dynamique du réseau, régional ou global.
- **Résilience.** La configuration se déclare avec un niveau de fiabilité visé : **production critique** (SLA de 99,99 %, deux connexions dans deux zones de périphérie distinctes, dans deux métropoles pour une résilience régionale), **production non critique** (99,9 %) ou **sans SLA**. Les MTU disponibles pour un rattachement sont 1 440, 1 460, 1 500 ou 8 896 octets, à aligner sur celui du réseau VPC.
- **Chiffrement.** Rien n'est chiffré par défaut. **MACsec** protège le segment entre le routeur du client et le routeur périphérique de Google ; **HA VPN sur Cloud Interconnect** ajoute des tunnels IPsec par-dessus les rattachements VLAN, de bout en bout.
- **Facturation.** Un tarif mensuel par port de connexion, un tarif horaire par rattachement VLAN selon sa capacité, et le trafic sortant à un tarif réduit. Dedicated Interconnect propose aussi une **tarification fixe au port** pour le trafic sortant, avec une facture mensuelle prévisible, distincte selon que le rattachement et la région de destination sont dans la même métropole ou non.

> [!WARNING]
> Le délai de mise en service n'est pas celui d'une ressource cloud : il faut commander la connexion, recevoir la lettre d'autorisation (LOA-CFA), la transmettre à l'opérateur, faire poser les liaisons, puis tester. Compter des semaines, et prévoir [Cloud VPN](#cloud-vpn) comme raccordement d'attente.

## À quoi ça sert

- Étendre le réseau d'entreprise vers Google Cloud avec une capacité et une latence stables, pour des applications sensibles au temps de réponse.
- Transférer de gros volumes de façon régulière — sauvegardes, entrepôt de données, flux vidéo — là où le tarif de sortie Internet deviendrait le premier poste de dépense.
- Répondre à une exigence de non-exposition : le trafic ne traverse aucun réseau public, et MACsec ou IPsec s'ajoutent si le chiffrement est exigé.
- Bâtir une architecture multicloud où la donnée vit d'un côté et les traitements de l'autre, par Cross-Cloud Interconnect.
- Utiliser le réseau de Google comme réseau étendu entre sites, avec Cross-Site Interconnect ou le transfert site à site de [Network Connectivity Center](#network-connectivity-center).

**À éviter** pour un besoin ponctuel, modeste ou urgent : [Cloud VPN](#cloud-vpn) se monte dans la journée, sans commande ni intervention physique, et suffit jusqu'à quelques gigabits par seconde. À éviter aussi de commander une liaison dédiée quand personne n'a de présence en colocation ni d'équipement conforme : Partner Interconnect existe pour cela. Et pour joindre seulement quelques services managés depuis un réseau distant, [Private Service Connect](#private-service-connect) suffit sans liaison privée.

## Alternatives en logiciel libre

Il n'y a pas d'équivalent libre à la pose d'une fibre : la partie matérielle et contractuelle de Cloud Interconnect ne se réplique pas. Le logiciel libre couvre en revanche tout ce qui se passe à l'extrémité de la liaison.

- **FRRouting** et **BIRD** : les piles BGP qui tiennent la session face au Cloud Router, annoncent les préfixes du site et filtrent ce qui est accepté.
- **Open vSwitch** : découpage en VLAN 802.1Q et agrégation LACP sur un routeur ou un commutateur logiciel, l'équivalent côté client d'un rattachement VLAN.
- **VyOS** : routeur logiciel complet — BGP, VLAN, LACP, MACsec, pare-feu — pour tenir l'extrémité d'une connexion sans assembler les briques.
- **wpa_supplicant** (`macsec`) et le sous-système MACsec du noyau Linux : chiffrement de niveau 2 sur le segment physique, en face de MACsec pour Cloud Interconnect.
- **strongSwan** : les tunnels IPsec quand la liaison doit être chiffrée de bout en bout plutôt que sur le seul segment physique.
