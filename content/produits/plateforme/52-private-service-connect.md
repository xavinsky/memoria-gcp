---
title: Private Service Connect
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 340]
  zones:
    - {label: "VPC consommateur", x: 14, y: 16, w: 340, h: 312}
    - {label: "VPC producteur — éditeur, autre équipe ou Google", x: 420, y: 16, w: 326, h: 312}
  nodes:
    cli: {label: "Clients", sub: "VMs, GKE, Cloud Run", icon: produits/compute-engine, x: 36, y: 60, w: 210}
    ep: {label: "Endpoint", sub: "IP interne 10.0.0.5", icon: categories/networking, focus: true, x: 36, y: 152, w: 210}
    bck: {label: "Backend", sub: "NEG et load balancer", icon: categories/networking, x: 36, y: 244, w: 210}
    sa: {label: "Rattachement de service", sub: "liste d'autorisation", icon: categories/networking, x: 440, y: 60, w: 290}
    svc: {label: "Service publié", sub: "load balancer interne", icon: categories/networking, x: 440, y: 152, w: 290}
    api: {label: "API Google", sub: "Cloud Storage, BigQuery", icon: categories/networking, x: 440, y: 244, w: 290}
  flows:
    - {from: cli, to: ep, text: "Le client ouvre une connexion vers une adresse IP interne de son propre sous-réseau, sans résoudre ni joindre le moindre nom public."}
    - {from: ep, to: sa, from_offset: -14, text: "La règle de transfert porte le trafic jusqu'au rattachement de service du producteur, qui n'accepte que les projets inscrits sur sa liste d'autorisation."}
    - {from: sa, to: svc, text: "Le rattachement remet le trafic au load balancer interne du producteur, après traduction depuis son sous-réseau NAT : aucune plage d'adresses n'est partagée entre les deux réseaux."}
    - {from: ep, to: api, from_offset: 14, text: "Un autre endpoint vise un paquet d'API Google et remplace leurs noms publics par une adresse interne choisie par le projet."}
    - {from: bck, to: svc, text: "Un backend place un load balancer du consommateur devant le service : domaine et certificat propres, règles de sécurité, bascule entre régions."}
docs:
  Documentation: https://docs.cloud.google.com/vpc/docs/private-service-connect
  Endpoints vers un service publié: https://docs.cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints
  Endpoints vers les API Google: https://docs.cloud.google.com/vpc/docs/about-accessing-google-apis-endpoints
  Backends: https://docs.cloud.google.com/vpc/docs/private-service-connect-backends
  Publier un service: https://docs.cloud.google.com/vpc/docs/about-vpc-hosted-services
  Interfaces: https://docs.cloud.google.com/vpc/docs/about-private-service-connect-interfaces
  Compatibilité des produits: https://docs.cloud.google.com/vpc/docs/private-service-connect-compatibility
  Architecture et performances: https://docs.cloud.google.com/vpc/docs/private-service-connect-architecture
  Options d'accès privé aux services: https://docs.cloud.google.com/vpc/docs/private-access-options
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/service-attachments
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/serviceAttachments
  Quotas et limites: https://docs.cloud.google.com/vpc/docs/quota
  Tarifs: https://cloud.google.com/vpc/pricing
---

## Ce que c'est

Le mécanisme d'accès privé aux services managés : un **consommateur** joint un service par une adresse IP interne de son propre réseau VPC, un **producteur** publie ce service depuis son réseau à lui. Le trafic ne quitte jamais le réseau de Google et ne traverse aucune adresse publique. Quand on accède à [Cloud SQL](#cloud-sql) ou à [BigQuery](#bigquery) de cette façon, le producteur, c'est Google.

- **Endpoints.** Côté consommateur, un *endpoint* est une **règle de transfert** qui pose une adresse IP interne dans un sous-réseau et la fait pointer vers un **rattachement de service** du producteur, ou vers un paquet d'API Google — global, régional ou multirégional. Les clients du réseau l'atteignent comme n'importe quelle machine voisine. C'est la connectivité de niveau 4, sans fonction de load balancing.
- **Backends.** Pour un service publié ou une API Google, un **groupe de points de terminaison réseau** Private Service Connect sert de *backend* à un load balancer du consommateur. On gagne ce qu'un load balancer apporte : domaine et certificat propres devant un service managé, règles de sécurité et journalisation centralisées, bascule choisie par le consommateur entre deux régions du service.
- **Services publiés.** Côté producteur, un **rattachement de service** désigne un load balancer interne, une **liste d'autorisation** des projets consommateurs, le **sous-réseau NAT** d'où part le trafic traduit, et éventuellement un domaine DNS dont les enregistrements sont créés automatiquement dans une zone privée du consommateur. Plusieurs endpoints et plusieurs organisations peuvent se connecter au même rattachement.
- **Interfaces.** Une **interface** Private Service Connect est une interface réseau du producteur rattachée à un *network attachment* du consommateur : elle inverse le sens, et permet au service managé d'ouvrir des connexions vers le réseau du consommateur. Contrairement à un endpoint, elle est **transitive** : les charges du réseau producteur peuvent joindre ce qui est connecté au réseau consommateur.
- **Ce que le modèle garantit.** Le service est exposé par une adresse unique, pas par tout un réseau : le consommateur n'accède à rien d'autre. Rien n'est partagé entre les deux réseaux — la traduction d'adresses fait que les plages peuvent se recouvrir sans conséquence. Et le trafic va directement de la machine physique du client à celle du load balancer producteur, la traduction étant faite par ces machines : le débit n'est limité que par elles.
- **Facturation.** Côté consommateur, un tarif horaire par endpoint, plus les données traitées — sauf pour les endpoints vers les API Google, dont les données ne sont pas facturées. Un backend suit la tarification du load balancer qui le porte, à laquelle s'ajoute le trafic entre le groupe de points de terminaison et le service. Le transfert entre zones n'est jamais facturé sur un endpoint ; celui entre régions l'est dès que l'accès global est activé.

> [!TIP]
> Private Service Connect remplace, pour les services qui le proposent, l'accès aux services privés fondé sur l'appairage de VPC : plus de plage d'adresses à réserver pour le producteur, plus de recouvrement possible, et aucune transitivité involontaire entre réseaux.

## À quoi ça sert

- Joindre les API Google depuis un réseau sans sortie Internet, avec des adresses internes choisies par le projet et non celles des domaines publics.
- Diriger le trafic d'API venu du réseau d'entreprise vers une région précise, en annonçant l'adresse de l'endpoint par [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect).
- Consommer en privé un service SaaS tiers hébergé sur Google Cloud, sans appairer son réseau à celui de l'éditeur.
- Publier un service interne entre équipes : une équipe expose une API derrière un load balancer interne, les autres s'y connectent depuis leurs propres réseaux.
- Placer son propre domaine, son certificat et ses règles de sécurité devant un service managé, grâce à un backend.

**À éviter** quand deux réseaux doivent communiquer largement, dans les deux sens et sur de nombreux ports : c'est un rôle d'appairage de VPC ou de [Network Connectivity Center](#network-connectivity-center), pas d'un accès orienté service. À éviter aussi pour le seul accès aux API Google depuis des VMs sans adresse externe, quand les noms publics conviennent : l'accès privé à Google y suffit et ne coûte rien.

## Alternatives en logiciel libre

- **HAProxy** et **Envoy** : mandataires de niveau 4 et 7 tenus par le consommateur, qui exposent une adresse locale et relaient vers le service distant — l'idée d'un endpoint, avec la machine à exploiter en plus.
- **Nginx** en mode `stream` : le même relais TCP, pour des besoins plus simples.
- **WireGuard** : tunnel point à point entre deux réseaux quand le service distant n'expose pas d'adresse joignable ; moins ciblé, puisqu'il relie des réseaux et non des services.
- **Cloud Native Computing Foundation Gateway API** : publication et découverte de services entre domaines administratifs, avec autorisation explicite côté producteur.
- **Skupper** : maillage de services entre réseaux séparés, où chaque côté n'expose que les services qu'il déclare — le plus proche du modèle producteur/consommateur.
