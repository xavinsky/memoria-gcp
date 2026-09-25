---
title: Cloud DNS
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 320]
  zones:
    - {label: "Projet GCP — réseau VPC", x: 14, y: 16, w: 430, h: 290}
  nodes:
    vm: {label: "VMs et pods", sub: "résolveur 169.254.169.254", icon: produits/compute-engine, x: 36, y: 56, w: 250}
    dns: {label: "Cloud DNS", sub: "zones autorisées sur le VPC", icon: categories/networking, focus: true, x: 36, y: 200, w: 290, h: 68}
    onprem: {label: "DNS sur site", sub: "BIND, Active Directory", external: true, x: 520, y: 56, w: 210}
    pub: {label: "Résolveurs publics", sub: "zone publique, DNSSEC", external: true, x: 520, y: 200, w: 210}
  flows:
    - {from: vm, to: dns, from_offset: -30, to_offset: -30, text: "La VM interroge le serveur de métadonnées, qui soumet la requête à Cloud DNS selon l'ordre de résolution de noms du réseau."}
    - {from: dns, to: vm, from_offset: 30, to_offset: 30, text: "Une zone privée autorisée sur ce réseau répond avec l'adresse interne du service demandé, sans aucun trafic sortant."}
    - {from: dns, to: onprem, from_offset: -16, text: "Une zone de transfert dirige les requêtes d'un domaine donné vers les serveurs de noms du site distant, par le tunnel VPN ou l'interconnexion."}
    - {from: onprem, to: dns, to_offset: 16, text: "Une règle de serveur entrante ouvre le chemin inverse : les postes du site résolvent les noms privés du VPC en interrogeant les adresses d'entrée que la règle réserve dans les sous-réseaux."}
    - {from: pub, to: dns, text: "Les résolveurs d'Internet interrogent les serveurs de noms anycast de Cloud DNS pour les enregistrements des zones publiques, signés par DNSSEC."}
docs:
  Page produit: https://cloud.google.com/dns
  Documentation: https://docs.cloud.google.com/dns/docs
  Vue d'ensemble: https://docs.cloud.google.com/dns/docs/overview
  Types de zones: https://docs.cloud.google.com/dns/docs/zones/zones-overview
  Zones privées: https://docs.cloud.google.com/dns/docs/zones
  Enregistrements: https://docs.cloud.google.com/dns/docs/records-overview
  Règles DNS: https://docs.cloud.google.com/dns/docs/policies-overview
  Règles de routage et contrôles d'état: https://docs.cloud.google.com/dns/docs/configure-routing-policies
  DNSSEC: https://docs.cloud.google.com/dns/docs/dnssec
  Journalisation: https://docs.cloud.google.com/dns/docs/monitoring
  Bonnes pratiques pour les zones privées: https://docs.cloud.google.com/dns/docs/best-practices
  API REST: https://docs.cloud.google.com/dns/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/dns
  Client Python: https://docs.cloud.google.com/python/docs/reference/dns/latest
  Quotas et limites: https://docs.cloud.google.com/dns/quotas
  Tarifs: https://cloud.google.com/dns/pricing
  Notes de version: https://docs.cloud.google.com/dns/docs/release-notes
---

## Ce que c'est

Service DNS géré, à la fois **autoritaire** pour les zones qu'on lui confie et **résolveur** pour les réseaux VPC. Les zones publiques sont servies depuis des serveurs de noms **anycast** répartis dans le monde ; les zones privées ne sont visibles que des réseaux explicitement autorisés.

- **Zones publiques.** Cloud DNS publie les enregistrements d'un domaine sur l'Internet. Il est nécessairement autoritaire : une zone publique ne transfère jamais une requête à un autre serveur.
- **Zones privées.** Une zone gérée privée n'est résolue que par les réseaux VPC inscrits dans sa liste de réseaux autorisés. C'est ainsi qu'un nom interne pointe sur une adresse privée sans jamais paraître sur Internet. Avec Shared VPC, la zone se crée dans le projet hôte, ou dans un projet de service par *liaison entre projets*.
- **Zones de transfert et règles de serveur.** Une **zone de transfert** est une zone privée sans enregistrement : elle désigne des serveurs de noms cibles — une VM du réseau, un load balancer interne, un serveur sur site joint par [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect), ou un nom pleinement qualifié. Une **règle de serveur sortante** envoie au contraire *toutes* les requêtes du réseau vers un serveur de substitution, au prix de la résolution des zones privées. Une **règle de serveur entrante** ouvre le chemin inverse : elle réserve des adresses d'entrée dans les sous-réseaux du VPC, que les clients du réseau distant interrogent. Les requêtes que Cloud DNS transfère vers des serveurs sur site partent, elles, de la plage `35.199.192.0/19`, à autoriser dans le pare-feu du site. Les deux sens peuvent être actifs en même temps.
- **Zones d'appairage.** Une zone d'appairage délègue la résolution d'un domaine à l'ordre de résolution d'un autre réseau VPC — le moyen de partager des noms entre réseaux, que l'appairage de VPC ne fait pas de lui-même.
- **Règles de réponse.** Elles remplacent les réponses pour certains noms, avant toute recherche dans les zones, à la façon des *response policy zones* de BIND : bloquer un domaine, rediriger un nom public vers une adresse interne, sans toucher aux zones elles-mêmes.
- **Règles de routage.** Un jeu d'enregistrements peut répondre différemment selon la requête : **répartition pondérée** entre plusieurs cibles, **géolocalisation** selon la région d'origine, ou **bascule** sur une cible de secours pilotée par des contrôles d'état. De quoi faire du routage de trafic sans load balancer devant.
- **DNSSEC.** Signature gérée des zones publiques, avec rotation des clés : un résolveur validant peut vérifier l'origine des réponses. C'est une authentification, pas un chiffrement.
- **DNS64.** Pour des VMs en IPv6 seul, Cloud DNS synthétise un enregistrement `AAAA` à partir d'un `A`, en préfixant l'adresse IPv4 par `64:ff9b::/96` ; combiné à NAT64 dans [Cloud NAT](#cloud-nat), il donne accès à des destinations IPv4.
- **Propagation.** Un changement atteint d'abord les serveurs autoritaires, puis les résolveurs au rythme du **TTL** des enregistrements. Beaucoup de résolveurs gardent aussi les réponses négatives jusqu'à quinze minutes : avant une bascule, abaisser le TTL, puis le remonter une fois la migration faite.
- **Facturation** à la zone gérée, tous types confondus, et au million de requêtes — plus cher pour une requête servie par une règle de routage. Les contrôles d'état se facturent à part, le trafic sortant n'est pas facturé, et il n'y a pas de palier gratuit.

> [!TIP]
> La résolution d'une VM suit un ordre fixe : règles de réponse, puis zones privées autorisées, zones de transfert et zones d'appairage, puis le DNS interne de Compute Engine, puis l'Internet public. Un nom qui se résout mal vient presque toujours d'un chevauchement entre deux de ces étages.

## À quoi ça sert

- Héberger les domaines publics d'une organisation, avec DNSSEC et une administration par IAM au projet ou à la zone.
- Nommer les ressources internes — bases, files, services — par des noms stables en zone privée, indépendants des adresses IP.
- Faire coexister le DNS d'entreprise et celui du cloud : transfert sortant vers les serveurs du site pour les domaines internes, règle entrante pour que le site résolve les noms du VPC.
- Répartir le trafic géographiquement ou par poids, et basculer sur un site de secours sur échec d'un contrôle d'état, sans load balancer global.
- Créer automatiquement les noms des endpoints [Private Service Connect](#private-service-connect), à partir du domaine déclaré par le producteur du service.

**À éviter** comme couche de répartition de charge fine : le DNS est mis en cache par des résolveurs qui ignorent parfois le TTL, ce qui rend les bascules lentes et imprévisibles ; pour répartir des requêtes HTTP, un load balancer décide à chaque requête. À éviter aussi de basculer un réseau entier sur une règle de serveur sortante sans mesurer ce qu'on perd : les zones privées, les zones de transfert, les zones d'appairage et le DNS interne de Compute Engine cessent alors d'être résolus.

## Alternatives en logiciel libre

- **BIND 9** : le serveur DNS de référence, autoritaire et récursif, avec DNSSEC, transferts de zone et *response policy zones* — le pendant direct des règles de réponse.
- **PowerDNS** : serveur autoritaire adossé à une base de données, avec une API REST pour piloter les zones, plus **PowerDNS Recursor** pour la partie résolveur ; le plus proche d'un service DNS géré par API.
- **Knot DNS** et **NSD** : serveurs autoritaires taillés pour le débit, utilisés sur des domaines de premier niveau.
- **Unbound** : résolveur validant, l'équivalent de la résolution récursive rendue aux VMs.
- **CoreDNS** : résolveur modulaire, celui de Kubernetes ; ses greffons font l'équivalent des zones de transfert et des règles de réponse.
- **dnsdist** : répartiteur de requêtes DNS avec règles par origine, pour reproduire un routage par géolocalisation ou par poids.
