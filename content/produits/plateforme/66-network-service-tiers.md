---
title: Network Service Tiers
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 404, y: 16, w: 342, h: 268}
  nodes:
    users: {label: Clients internet, sub: "partout dans le monde", external: true, x: 8, y: 126, w: 150}
    pop: {label: Point de présence, sub: "proche du client", external: true, x: 190, y: 36, w: 190}
    isp: {label: Réseau de transit, sub: "internet public", external: true, x: 190, y: 214, w: 190}
    glb: {label: Load balancer global, sub: "adresse IP anycast", icon: categories/networking, focus: true, x: 416, y: 36, w: 218}
    gce: {label: Compute Engine, sub: "instances de backend", icon: produits/compute-engine, x: 416, y: 122, w: 218}
    rlb: {label: Load balancer régional, sub: "adresse IP régionale", icon: categories/networking, x: 416, y: 214, w: 218}
  flows:
    - {from: users, to: pop, from_side: right, to_side: left, text: "En niveau Premium, l'adresse est annoncée depuis tous les points de présence : le trafic entre dans le réseau Google au plus près du client."}
    - {from: pop, to: glb, text: "Il parcourt ensuite le réseau mondial privé de Google jusqu'au load balancer, dont les backends peuvent être répartis sur plusieurs régions."}
    - {from: glb, to: gce, text: "Le trafic est remis aux instances les plus proches qui disposent encore de capacité."}
    - {from: users, to: isp, from_side: right, to_side: left, text: "En niveau Standard, seuls les points d'appairage proches de la région portent l'annonce : le trafic reste sur les réseaux de transit jusque-là."}
    - {from: isp, to: rlb, text: "Il n'entre dans le réseau Google qu'à cet appairage, sur une adresse IP externe régionale."}
    - {from: rlb, to: gce, text: "Le load balancer régional, comme Cloud NAT et les adresses externes de VM, accepte les deux niveaux."}
docs:
  Documentation: https://docs.cloud.google.com/network-tiers/docs
  Vue d'ensemble: https://docs.cloud.google.com/network-tiers/docs/overview
  Choisir et appliquer un niveau: https://docs.cloud.google.com/network-tiers/docs/set-network-tier
  Choisir un load balancer: https://docs.cloud.google.com/load-balancing/docs/choosing-load-balancer
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/projects
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/addresses/create
  APIs et bibliothèques: https://docs.cloud.google.com/network-tiers/docs/apis
  Tarifs: https://cloud.google.com/network-tiers/pricing
  Notes de version: https://docs.cloud.google.com/network-tiers/docs/release-notes
---

## Ce que c'est

Choix du chemin que le trafic internet emprunte pour atteindre une ressource Google Cloud et pour en repartir. Le niveau n'est pas une option de projet mais un attribut de **ressource** — concrètement, de l'adresse IP externe : un même projet mélange les deux.

- **Premium.** L'adresse est annoncée en BGP avec des métriques équivalentes depuis l'ensemble des points de présence de Google. Les réseaux d'appairage et de transit livrent donc le trafic au point de présence le plus proche du client, et le reste du trajet se fait sur le réseau privé de Google. Le retour suit le meilleur chemin BGP, en minimisant la distance parcourue hors du réseau Google. C'est le niveau par défaut.
- **Standard.** L'adresse n'est annoncée que depuis les points d'appairage proches de la région où elle est déployée. Le trafic circule donc sur l'internet public jusqu'à cette région, et n'entre dans le réseau Google qu'à la fin. Les points d'appairage retenus minimisent la distance parcourue sur le réseau de Google, pas la latence perçue par l'utilisateur, et ne sont pas nécessairement dans le même pays que la région.
- **Types d'adresses.** Les adresses externes **globales** (IPv4 et IPv6, anycast) n'existent qu'en Premium. Les adresses externes **régionales IPv4** acceptent les deux niveaux ; les adresses externes **régionales IPv6** sont réservées au Premium.
- **Ressources compatibles Standard** : Application Load Balancer externe régional, proxy Network Load Balancer externe régional, passthrough Network Load Balancer externe régional, instances de VM (y compris les nœuds [GKE](#gke)), passerelles Cloud NAT. L'Application Load Balancer externe global et le proxy Network Load Balancer externe global exigent le Premium ; l'Application Load Balancer classique et le proxy Network Load Balancer classique sont globaux en Premium et régionaux en Standard ; les passerelles Cloud VPN exigent le Premium.
- **Cas particuliers.** L'accès à un bucket [Cloud Storage](#cloud-storage) est réputé Premium ; le Standard n'est possible que pour un bucket servi comme backend d'un Application Load Balancer externe à adresse régionale. [Cloud CDN](#cloud-cdn) est toujours en Premium.
- **Trafic interne.** Quel que soit le niveau, le trafic entre instances de Google Cloud — même région ou non, adresses publiques ou privées, équilibreur sur le chemin ou non — reste sur le réseau de Google. Les équilibreurs internes sont toujours en Premium, sans que les frais de sortie associés s'appliquent.
- **Engagement de service.** 99,99 % de disponibilité en Premium, 99,9 % en Standard.
- **Tarifs.** Le transfert sortant est facturé moins cher en Standard, à un barème par région ; le Premium est facturé au barème mondial, au niveau des autres grands fournisseurs. Le niveau se fixe à la création de l'adresse ou de la règle de transfert, ou par un paramètre de niveau par défaut du projet.

> [!WARNING]
> Le niveau d'une adresse externe ne se change pas après coup : il faut créer une nouvelle adresse au bon niveau, refaire la règle de transfert et basculer le DNS. Le choix se fait donc au moment de réserver l'adresse.

## À quoi ça sert

- Servir une audience mondiale avec le temps de réponse le plus court possible : le Premium fait entrer le trafic dans le réseau de Google près de l'utilisateur, ce qui évite les aléas des réseaux de transit.
- Réduire la facture de sortie d'une charge dont les clients sont concentrés dans la même zone géographique que la région : un back-office interne, un service national, une API consommée depuis une seule région.
- Dégrader volontairement le niveau des flux non critiques — sauvegardes sortantes, exports par lots, mise à jour de miroirs — tout en gardant le trafic client en Premium, puisque le niveau se choisit adresse par adresse.
- Accéder à toutes les fonctions réseau qui n'existent qu'en Premium : adresse anycast globale, backends multirégionaux, IPv6 régional, Cloud VPN, Cloud CDN.
- Comparer à coût réel deux architectures d'exposition avant de figer le choix, en déployant les deux niveaux côte à côte dans le même projet.

**À éviter** : le niveau Standard dès que la latence compte pour des utilisateurs éloignés de la région, ou dès qu'une fonction globale est nécessaire — adresse anycast, backends répartis sur plusieurs continents, [Cloud CDN](#cloud-cdn). À éviter aussi de le retenir pour un service critique sans avoir regardé l'écart d'engagement de disponibilité, et de croire qu'il réduit le trafic entre régions : ce trafic-là reste sur le réseau de Google et se facture à son propre barème. Enfin, ce n'est pas un levier d'économie sur les charges dont la sortie internet est marginale — l'essentiel de la facture se joue alors ailleurs.

## Alternatives en logiciel libre

Le choix d'un niveau de service réseau n'a pas d'équivalent logiciel : il porte sur le transport, propriété de l'opérateur. Les briques ci-dessous servent à reproduire soi-même les deux comportements chez un hébergeur ou dans un réseau d'entreprise.

- **BIRD** et **FRRouting** : démons de routage BGP libres, avec lesquels on annonce un préfixe depuis un seul point d'échange (l'équivalent du Standard) ou depuis plusieurs en anycast (l'équivalent du Premium).
- **ExaBGP** : annonce et retrait de routes pilotés par script, pour automatiser la bascule d'un préfixe entre points de présence.
- **WireGuard** et **strongSwan** : transport chiffré entre sites lorsque l'on veut sortir au plus tôt du réseau public, plutôt que de compter sur un chemin privé fourni.
- **Anycast avec Keepalived** ou **ExaBGP** devant une flotte de proxys : la même adresse annoncée depuis plusieurs emplacements, l'équivalent artisanal de l'adresse IP anycast globale.
