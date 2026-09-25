---
title: Cloud VPN
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 320]
  zones:
    - {label: "Projet GCP — réseau VPC", x: 14, y: 16, w: 456, h: 290}
    - {label: "Réseau sur site ou autre cloud", x: 522, y: 16, w: 228, h: 290}
  nodes:
    rtr: {label: "Cloud Router", sub: "sessions BGP des tunnels", icon: categories/networking, x: 36, y: 50, w: 214}
    vms: {label: "VMs et services", sub: "adresses IP internes", icon: produits/compute-engine, x: 36, y: 200, w: 214}
    gw: {label: "Passerelle HA VPN", sub: "2 interfaces, 2 IP", icon: categories/networking, focus: true, x: 274, y: 120, w: 182, h: 68}
    peer1: {label: "Passerelle pair 1", sub: "site principal", external: true, x: 544, y: 50, w: 184}
    peer2: {label: "Passerelle pair 2", sub: "second équipement", external: true, x: 544, y: 200, w: 184}
  flows:
    - {from: vms, to: gw, text: "Le trafic destiné aux plages du réseau distant est remis au tunnel par les routes dynamiques installées dans le VPC."}
    - {from: gw, to: peer1, from_offset: -16, text: "Le premier tunnel IPsec part de l'interface 0 vers la passerelle du site principal ; seuls ESP et UDP 500 et 4500 circulent entre les deux adresses externes."}
    - {from: gw, to: peer2, from_offset: 16, text: "Le second tunnel part de l'interface 1 vers un autre équipement : c'est cette redondance qui donne les 99,99 % de disponibilité."}
    - {from: peer1, to: rtr, from_offset: 14, to_offset: 14, text: "Le routeur distant annonce en BGP les préfixes de son réseau à travers le tunnel."}
    - {from: rtr, to: gw, from_offset: -14, control: true, text: "Cloud Router installe ces préfixes comme routes dynamiques, avec le tunnel pour saut suivant, et annonce en retour les plages des sous-réseaux."}
docs:
  Page produit: https://cloud.google.com/hybrid-connectivity
  Documentation: https://docs.cloud.google.com/network-connectivity/docs/vpn
  Vue d'ensemble: https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/overview
  Topologies HA VPN: https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/topologies
  Bonnes pratiques: https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/best-practices
  Chiffrements pris en charge: https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/supported-ike-ciphers
  Passerelles pairs validées: https://docs.cloud.google.com/network-connectivity/docs/vpn/how-to/interop-guides
  HA VPN sur Cloud Interconnect: https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/ha-vpn-interconnect
  Passer de Classic VPN à HA VPN: https://docs.cloud.google.com/network-connectivity/docs/vpn/how-to/moving-to-ha-vpn
  Dépréciations: https://docs.cloud.google.com/network-connectivity/docs/vpn/deprecations
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/vpnGateways
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/vpn-gateways
  Quotas et limites: https://docs.cloud.google.com/network-connectivity/docs/vpn/quotas
  Tarifs: https://cloud.google.com/vpn/pricing
  Notes de version: https://docs.cloud.google.com/network-connectivity/docs/vpn/release-notes
---

## Ce que c'est

Tunnels IPsec entre un réseau VPC et un réseau distant — site d'entreprise, autre fournisseur de cloud, ou un second réseau VPC. Le trafic chiffré emprunte l'Internet public ; une passerelle chiffre, l'autre déchiffre. Cloud VPN ne fait que du site à site : aucun client logiciel ne s'y connecte, et il ne sert pas à sortir vers Internet.

- **HA VPN.** La forme à retenir. Google attribue à la passerelle **deux adresses IP externes**, une par interface, prises dans deux pools distincts. Deux tunnels montés depuis les deux interfaces vers deux équipements distants — ou vers deux interfaces du même équipement — donnent un SLA de **99,99 %** ; une seule interface active ramène à **99,9 %** et, en dessous, à aucun engagement. Le routage est exclusivement **dynamique**, en BGP par un [Cloud Router](https://docs.cloud.google.com/network-connectivity/docs/router/concepts/overview). L'équipement distant est décrit par une ressource *passerelle VPN externe*. HA VPN accepte IPv4, IPv6 et la double pile.
- [!DECONSEILLE] **Classic VPN.** Une seule interface, une seule adresse externe, **routage statique uniquement** (basé sur des règles ou sur des routes), SLA de 99,9 %, pas d'IPv6. Le routage dynamique y est déprécié : aucun tunnel BGP ne s'y crée, quelle que soit la passerelle en face, et les tunnels BGP existants fonctionnent sans engagement de disponibilité. Rien de neuf ne se construit dessus : HA VPN est la passerelle à choisir. Dans l'API et la CLI, une passerelle Classic VPN reste une `target-vpn-gateway`, là où HA VPN est une `vpn-gateway`.
- **Migration.** On ne convertit pas un tunnel : il faut créer la passerelle HA VPN, ses tunnels et son Cloud Router, vérifier, puis supprimer les anciens tunnels, les routes statiques résiduelles et l'ancienne passerelle. Les adresses externes ne sont pas conservées, et l'équipement distant doit savoir parler BGP.
- **Débit.** Chaque tunnel accepte jusqu'à **250 000 paquets par seconde**, entrée et sortie confondues, soit de 1 à 3 Gbit/s selon la taille moyenne des paquets. Au-delà, il faut ajouter des tunnels. Le débit réel dépend aussi du temps d'aller-retour, du taux de perte et de l'équipement distant.
- **Prérequis côté distant.** Adresse externe statique, prise en charge d'IKEv1 ou IKEv2, préfragmentation des paquets avant encapsulation, ouverture d'ESP et d'UDP 500 et 4500. Les plages d'adresses des deux réseaux ne doivent pas se recouvrir. La détection de rejeu, sur une fenêtre de 4 096 paquets, n'est pas désactivable.
- **HA VPN sur Cloud Interconnect.** Les tunnels HA VPN peuvent emprunter des rattachements VLAN [Cloud Interconnect](#cloud-interconnect) au lieu d'Internet : on ajoute le chiffrement IPsec à une liaison privée, ce qu'exige parfois la conformité, notamment avec Partner Interconnect.
- **Facturation.** Un tarif horaire par tunnel rattaché à la passerelle, variable selon la région. Le trafic suit le tarif de transfert entre VMs quand le tunnel aboutit à une autre passerelle Cloud VPN, et le tarif de sortie Internet sinon. Une adresse externe affectée à une passerelle mais qu'aucun tunnel n'utilise est facturée à part.

> [!WARNING]
> Un seul tunnel monté depuis une passerelle HA VPN ne donne aucun SLA. La configuration à deux tunnels n'est pas un raffinement : c'est ce qui fait la différence entre 99,99 % et rien du tout.

## À quoi ça sert

- Prolonger un réseau d'entreprise vers Google Cloud en quelques heures, sans commande de circuit ni intervention en salle machine.
- Relier Google Cloud à un autre fournisseur de cloud, ou deux réseaux VPC entre eux quand l'appairage ne convient pas — plages recouvrantes, besoin de chiffrement, ou routage dynamique voulu.
- Doubler une liaison Cloud Interconnect par un chemin de secours indépendant, avec des priorités BGP distinctes.
- Chiffrer une liaison Cloud Interconnect qui doit l'être pour des raisons réglementaires, par HA VPN sur Cloud Interconnect.
- Servir de raccordement d'appoint pendant une migration, le temps que l'interconnexion définitive soit livrée.

**À éviter** dès que le volume ou la régularité comptent : un tunnel plafonne autour de 3 Gbit/s et traverse l'Internet public, avec la latence et la gigue qui vont avec ; [Cloud Interconnect](#cloud-interconnect) apporte la capacité, la latence stable et des tarifs de sortie réduits. À éviter aussi pour donner un accès distant à des postes de travail : ce n'est pas un VPN client, et l'accès aux applications internes passe plutôt par Identity-Aware Proxy. Enfin, ne pas bâtir un nouveau raccordement sur Classic VPN : sans BGP, il faut entretenir les routes statiques à la main, et le SLA est inférieur d'un ordre de grandeur.

## Alternatives en logiciel libre

- **strongSwan** : la pile IPsec et IKEv2 de référence sous Linux ; c'est souvent elle qu'on met en face d'une passerelle HA VPN côté site distant.
- **Libreswan** : l'autre implémentation IPsec majeure, issue d'Openswan, avec un suivi long des distributions d'entreprise.
- **WireGuard** : tunnel chiffré bien plus simple à exploiter et plus rapide, mais hors du protocole IPsec — donc inutilisable face à Cloud VPN, seulement entre machines que l'on gère des deux côtés.
- **FRRouting** ou **BIRD** : le BGP côté site distant, qui répond à celui du Cloud Router et annonce les préfixes internes.
- **VyOS** et **OPNsense** : routeurs logiciels complets qui intègrent IPsec, BGP et le pare-feu, pour tenir l'extrémité du tunnel sans assembler les briques une à une.
- **OpenVPN** : accès distant par client logiciel, le besoin que Cloud VPN ne couvre pas.
