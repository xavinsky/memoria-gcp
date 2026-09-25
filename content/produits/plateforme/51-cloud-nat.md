---
title: Cloud NAT
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 340]
  zones:
    - {label: "Projet GCP — réseau VPC", x: 14, y: 16, w: 520, h: 304}
  nodes:
    vm: {label: "VMs sans IP externe", sub: "sous-réseau privé", icon: produits/compute-engine, x: 36, y: 56, w: 220}
    gke: {label: "Nœuds GKE privés", sub: "pods et services", icon: produits/gke, x: 36, y: 136, w: 220}
    run: {label: "Cloud Run", sub: "sortie VPC directe", icon: produits/cloud-run, x: 36, y: 216, w: 220}
    rtr: {label: "Cloud Router", sub: "plan de contrôle", icon: categories/networking, x: 310, y: 40, w: 200}
    nat: {label: "Cloud NAT", sub: "passerelle régionale", icon: categories/networking, focus: true, x: 310, y: 130, w: 200, h: 68}
    net: {label: "Internet", sub: "dépôts, API tierces", external: true, x: 590, y: 130, w: 160}
  flows:
    - {from: vm, to: nat, text: "Les VMs dépourvues d'adresse externe envoient leur trafic sortant avec leur seule adresse interne ; la passerelle sert tous les sous-réseaux déclarés dans sa configuration."}
    - {from: gke, to: nat, text: "Les nœuds d'un cluster privé passent par la même passerelle ; le couple adresse et ports est alloué au nœud et partagé par tous ses pods."}
    - {from: run, to: nat, text: "Les services Cloud Run atteignent la passerelle par la sortie VPC directe, et les instances App Engine standard par un connecteur d'accès VPC sans serveur."}
    - {from: rtr, to: nat, control: true, text: "La passerelle se déclare sur un Cloud Router, qui n'en porte que la configuration : aucun paquet ne le traverse."}
    - {from: nat, to: net, from_offset: -14, to_offset: -14, text: "Andromeda remplace l'adresse et le port source par un couple pris dans les adresses externes régionales de la passerelle."}
    - {from: net, to: nat, from_offset: 14, to_offset: 14, text: "Les réponses des connexions établies reviennent par le même couple ; aucune connexion entrante non sollicitée n'est acceptée."}
docs:
  Page produit: https://cloud.google.com/nat
  Documentation: https://docs.cloud.google.com/nat/docs
  Vue d'ensemble: https://docs.cloud.google.com/nat/docs/overview
  Adresses IP et ports: https://docs.cloud.google.com/nat/docs/ports-and-addresses
  Public NAT: https://docs.cloud.google.com/nat/docs/public-nat
  Private NAT: https://docs.cloud.google.com/nat/docs/private-nat
  Règles NAT: https://docs.cloud.google.com/nat/docs/nat-rules-overview
  Interactions avec les autres produits: https://docs.cloud.google.com/nat/docs/nat-product-interactions
  Journalisation: https://docs.cloud.google.com/nat/docs/monitoring
  Configurer une passerelle: https://docs.cloud.google.com/nat/docs/set-up-manage-network-address-translation
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/routers
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/routers/nats
  Quotas et limites: https://docs.cloud.google.com/nat/quota
  Tarifs: https://cloud.google.com/nat/pricing
  Notes de version: https://docs.cloud.google.com/nat/docs/release-notes
---

## Ce que c'est

Traduction d'adresses réseau (*NAT*) pour le trafic sortant d'un réseau VPC, rendue par le logiciel Andromeda lui-même : ni VM relais, ni appliance, ni goulet d'étranglement. Une passerelle est une ressource **régionale**, déclarée sur un **Cloud Router** qui ne sert que de porteur de configuration — les paquets ne passent pas par lui.

- **Deux types de passerelles.** **Public NAT** donne accès à des destinations Internet en IPv4 à des ressources sans adresse IP externe. **Private NAT** traduit une adresse privée en une autre adresse privée, vers un autre réseau VPC rattaché au même hub Network Connectivity Center, ou vers un réseau sur site ou d'un autre cloud joint par [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect) — c'est la réponse au recouvrement de plages d'adresses entre deux réseaux. Une passerelle rend l'un ou l'autre service, jamais les deux ; il en faut donc deux pour couvrir les deux besoins sur le même sous-réseau.
- **Ressources servies.** VMs [Compute Engine](#compute-engine), nœuds [GKE](#gke), instances [Cloud Run](#cloud-run) (services, jobs et fonctions) par la sortie VPC directe, instances App Engine standard par un connecteur d'accès VPC sans serveur, et groupes de points de terminaison réseau Internet régionaux pour Public NAT. La traduction s'applique d'elle-même dès qu'une ressource tourne dans un sous-réseau servi par la passerelle.
- **Sens unique.** La passerelle traduit les réponses des connexions sortantes établies, et rien d'autre : elle n'ouvre aucun accès entrant. Exposer un service demande un load balancer ou une adresse IP externe.
- **Adresses.** En **allocation automatique**, la passerelle réserve et libère elle-même des adresses externes régionales selon le nombre de ressources servies, dans le niveau réseau choisi ; on ne peut alors pas prévoir quelles adresses seront prises. En **affectation manuelle**, on rattache des adresses statiques réservées, ce qui permet de les communiquer à un partenaire pour une liste d'autorisation, et de **vidanger** une adresse retirée pour laisser les connexions en cours se terminer. Si une passerelle manque d'adresses, elle rejette les paquets.
- **Ports.** Chaque ressource reçoit un lot de couples adresse et port. En **allocation statique**, le lot est fixe : 64 ports par défaut, arrondis à une puissance de deux, 1 024 au minimum dès qu'une plage d'alias couvre plus d'une adresse. En **allocation dynamique**, la passerelle part de 32 ports et monte jusqu'au maximum configuré selon la demande, puis rend les ports inutilisés. Le nombre de ports limite les connexions simultanées vers une même destination — même adresse, même port, même protocole.
- **Règles NAT.** Une règle associe une condition sur la destination à un jeu d'adresses de traduction : on présente une adresse différente selon le partenaire joint, sans multiplier les passerelles.
- **Journalisation et métriques.** Les journaux tracent les connexions créées et les paquets rejetés, séparément ; les métriques d'allocation de ports et d'utilisation partent dans Cloud Monitoring, et Network Analyzer publie des recommandations sur la configuration.
- **Facturation.** Un tarif horaire par passerelle proportionnel au nombre de VMs servies, plafonné à 32 VMs — au-delà, le tarif ne monte plus — un tarif au Gio traité, identique dans toutes les régions, et pour Public NAT un tarif horaire par adresse externe utilisée. Le trafic sortant vers Internet reste facturé par ailleurs.

> [!TIP]
> Le trafic vers les API Google passe par l'accès privé à Google, pas par la passerelle, même quand la VM utilise Public NAT : ce n'est pas Cloud NAT qu'il faut ouvrir pour joindre Cloud Storage ou BigQuery depuis une VM privée.

## À quoi ça sert

- Laisser des VMs sans adresse externe télécharger des paquets, des images ou des mises à jour, et appeler des API tierces.
- Donner un accès sortant aux nœuds d'un cluster GKE privé, qui n'ont par construction aucune adresse publique.
- Présenter à un partenaire un jeu d'adresses source stable et restreint, pour figurer sur sa liste d'autorisation.
- Faire communiquer deux réseaux dont les plages d'adresses se recouvrent, par Private NAT, sans replanifier l'adressage d'un des deux.
- Joindre des destinations IPv4 depuis des VMs en IPv6 seul, en combinant NAT64 et la synthèse d'adresses DNS64 de [Cloud DNS](#cloud-dns).

**À éviter** pour exposer un service au monde : la passerelle n'accepte aucune connexion entrante. À éviter aussi comme point de contrôle du trafic sortant — elle ne filtre rien : les destinations autorisées se décident dans les règles de sortie du pare-feu, éventuellement par nom de domaine avec Cloud NGFW. Enfin, inutile de la mettre en place pour atteindre les API Google ou un service managé : l'accès privé à Google et [Private Service Connect](#private-service-connect) y mènent sans passer par Internet.

## Alternatives en logiciel libre

- **nftables** (ou **iptables** avec `MASQUERADE`) sur un routeur Linux : la traduction d'adresses source telle qu'on la fait à la main ; c'est ce que remplace une passerelle Cloud NAT, sans la VM à maintenir ni le point de défaillance unique.
- **FRRouting** : pour annoncer la route par défaut vers ce routeur depuis le reste du réseau, comme le ferait un Cloud Router.
- **VyOS** et **OPNsense** : distributions de routeur et de pare-feu clés en main, avec NAT source, règles de sortie et journalisation.
- **conntrackd** : synchronisation des tables de suivi de connexions entre deux routeurs, pour obtenir la continuité que la passerelle managée offre nativement.
- **Squid** : mandataire sortant, quand le besoin réel est de filtrer et de tracer les destinations plutôt que de traduire des adresses.
