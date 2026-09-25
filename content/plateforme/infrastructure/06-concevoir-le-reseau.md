---
title: Concevoir le réseau VPC
subgroup: Calcul et réseau
---

Un réseau [VPC](#vpc) est **global**, ses sous-réseaux sont **régionaux** : un seul réseau couvre toutes les régions, sans passerelle à monter entre elles. La conception tient donc moins à la topologie physique qu'à quatre décisions : le **plan d'adressage**, le **découpage en réseaux** (combien, et qui les administre), la **connexion entre réseaux et avec le site**, et le **chemin vers Internet et vers les API Google**. Le guide *Best practices and reference architectures for VPC design* de l'Architecture Center et le chapitre réseau de l'*enterprise foundations blueprint* servent de trame à cette section.

![Réseau en étoile : VPC de connectivité, hub Network Connectivity Center et réseaux par environnement](../../svg/reseau-hub-spoke.svg)

Le blueprint propose deux topologies, toutes deux fondées sur [Shared VPC](#lexterm-shared-vpc) : un réseau partagé **par environnement** sans trafic direct entre eux, ou une **étoile** où un réseau central porte la connectivité hybride. Le schéma montre la seconde avec un hub [Network Connectivity Center](#network-connectivity-center), la méthode que le guide de conception recommande pour relier des réseaux VPC : les liaisons avec le site aboutissent dans un VPC de connectivité, le hub échange les routes entre ce réseau et les réseaux prod, hors prod et dev, et chaque réseau garde sa propre sortie Internet et ses accès privés aux API.

## Plan d'adressage

- **Mode personnalisé** toujours : le mode automatique prend des plages dans `10.128.0.0/9` et crée un sous-réseau par région, ce qui entre en collision avec les autres réseaux dès qu'on les relie. Interdire le réseau `default` par la contrainte `compute.skipDefaultNetworkCreation`.
- **Peu de sous-réseaux, larges** : un par région et par environnement suffit souvent. L'isolement se fait par le pare-feu, pas par le découpage ; l'accès privé à Google, les journaux de flux et les plages d'alias se règlent pourtant par sous-réseau, ce qui justifie d'en séparer certains.
- **Aucun recouvrement avec le site ni avec les autres clouds** : réserver dans le plan d'adressage de l'entreprise un bloc pour Google Cloud avant de créer le premier réseau. L'appairage, les VPN et l'Interconnect ne relient pas deux plages qui se recouvrent ; Private NAT et Private Service Connect sont les seules issues.
- **Plages secondaires pour GKE** : les Pods prennent leurs adresses dans une plage secondaire du sous-réseau, par défaut un `/24` par nœud (110 Pods). Un cluster de 1 000 nœuds consomme donc un `/14`. Les Services utilisent par défaut une plage gérée par GKE, `34.118.224.0/20`, sans plage à réserver.
- **Au-delà de la RFC 1918** : `100.64.0.0/10` (RFC 6598) et `240.0.0.0/4` (classe E) sont acceptés comme plages de sous-réseau, utiles pour les Pods quand l'espace privé manque. Vérifier que les systèmes d'exploitation et les équipements du site les acceptent, et éviter `172.17.0.0/16`, pris par Docker par défaut.
- **Sous-réseaux réservés** : un sous-réseau *proxy uniquement* par région pour les load balancers fondés sur Envoy (voir [Choisir un load balancer](#choisir-un-load-balancer)), et un sous-réseau NAT par service publié en Private Service Connect.

```python
import pulumi_gcp as gcp

REGION = "europe-west1"

vpc = gcp.compute.Network(
    "prod",
    auto_create_subnetworks=False,   # mode personnalisé
    routing_mode="GLOBAL",           # routes BGP apprises valables dans toutes les régions
)

subnet = gcp.compute.Subnetwork(
    "prod-ew1",
    network=vpc.id,
    region=REGION,
    ip_cidr_range="10.20.0.0/20",            # VM et nœuds GKE
    private_ip_google_access=True,           # API Google sans adresse externe
    secondary_ip_ranges=[{"range_name": "pods", "ip_cidr_range": "10.64.0.0/14"}],
    log_config={"aggregation_interval": "INTERVAL_5_SEC", "flow_sampling": 0.5},
)

router = gcp.compute.Router("prod-ew1-router", network=vpc.id, region=REGION)
gcp.compute.RouterNat(
    "prod-ew1-nat",
    router=router.name,
    region=REGION,
    nat_ip_allocate_option="AUTO_ONLY",
    source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
    enable_dynamic_port_allocation=True,
    log_config={"enable": True, "filter": "ERRORS_ONLY"},
)
```

## Relier des réseaux

| Mécanisme | Ce qui est partagé | Transitif | Recouvrement d'adresses | Quand le choisir |
|---|---|---|---|---|
| **Shared VPC** | Un seul réseau, dans un projet hôte ; les projets de service y créent leurs ressources | Sans objet | Impossible | Plusieurs équipes, une administration réseau centrale : le choix par défaut dans une organisation |
| **Hub [NCC](#network-connectivity-center)**, spokes VPC | Routes de sous-réseau entre jusqu'à 250 réseaux, entre projets et organisations | Oui | Non, sauf NAT entre VPC | Plus de deux ou trois réseaux ; la méthode que recommande le guide de conception |
| **Appairage de VPC** | Routes de sous-réseau entre deux réseaux ; ni pare-feu, ni DNS | Non | Non | Deux réseaux seulement, ou insertion d'appliances réseau tierces |
| **[Private Service Connect](#private-service-connect)** | Un seul service, derrière une adresse interne du consommateur | Non | Oui | Consommer ou publier un service entre équipes ou éditeurs sans ouvrir le réseau |
| **[HA VPN](#cloud-vpn)** entre VPC | Routes BGP à travers des tunnels | Oui | Non | Chiffrement exigé, ou points d'accès de services non propagés par NCC ; débit limité par tunnel |

Un projet est hôte ou de service, jamais les deux, et un projet de service n'a qu'un hôte. Un réseau par environnement, chacun dans son projet hôte, donne à chaque environnement ses quotas et ses rôles IAM (`compute.networkAdmin`, `compute.securityAdmin`, `compute.networkUser`) ; le guide recommande aussi d'isoler les données sensibles dans leur propre réseau.

> [!WARNING]
> Dans un réseau partagé, le réseau ne sépare pas les applications entre elles : un service ne doit jamais accepter un appelant sur la seule foi de son adresse IP. **Toujours exiger l'authentification IAM** : invocateur IAM sur [Cloud Run](#cloud-run), [Identity-Aware Proxy](#identity-aware-proxy) devant une application web, authentification IAM des bases [Cloud SQL](#cloud-sql) et [AlloyDB](#alloydb), de Memorystore for Valkey et for Redis Cluster. Un service qui n'accepte pas IAM (Memorystore for Redis en instance simple, qui n'a que la chaîne AUTH, ou un logiciel tiers) garde au minimum un secret propre à l'application, et, faute de mieux, un réseau ou un point d'accès [Private Service Connect](#private-service-connect) dédié.

## Sortie Internet et accès aux API Google

- **Pas d'adresse externe sur les VM** : la contrainte d'organisation `compute.vmExternalIpAccess` la refuse. La sortie passe par [Cloud NAT](#cloud-nat), une passerelle par réseau et par région, avec des adresses statiques quand un partenaire filtre par adresse source.
- **API Google** : l'**[accès privé à Google](#lexterm-acces-prive-a-google)**, activé par sous-réseau, suffit pour des VM sans adresse externe ; il ne passe pas par Cloud NAT. Pour des clients du site, ou pour ne laisser joindre que les API compatibles VPC Service Controls, on résout `*.googleapis.com` vers `private.googleapis.com` (`199.36.153.8/30`) ou `restricted.googleapis.com` (`199.36.153.4/30`).
- **Endpoint Private Service Connect pour les API** : une adresse interne choisie par le projet, liée au paquet `all-apis` ou `vpc-sc`. C'est la forme à retenir pour annoncer l'accès aux API vers le site par BGP, ou pour avoir des adresses différentes selon le réseau.
- **Services managés** (Cloud SQL, AlloyDB, Memorystore...) : Private Service Connect quand le service le propose ; l'accès aux services privés par appairage demande de réserver une plage par producteur et n'est pas transitif.

## Pare-feu

- **Politiques plutôt que règles isolées** : une [politique hiérarchique](#lexterm-politique-de-pare-feu-hierarchique) au niveau de l'organisation ou d'un dossier pose le socle que les projets ne peuvent pas contourner (pas de SSH depuis Internet, plages des sondes de contrôle d'état autorisées) ; une politique de réseau globale porte les règles de l'application. Voir [Cloud NGFW](#cloud-ngfw).
- **Tags sécurisés plutôt qu'étiquettes réseau** : un [tag](#lexterm-tag) sécurisé est une ressource IAM, qu'une équipe applicative ne peut pas poser sur sa VM pour s'ouvrir un flux ; une étiquette réseau, si. Les comptes de service jouent le même rôle dans les règles de pare-feu VPC.
- **Peu de règles, larges** : le guide recommande des ensembles de règles restreints plutôt qu'une règle par machine, et la surveillance automatique des tags utilisés comme cibles.
- **Le pare-feu ne suit pas les tunnels** : les tags et comptes de service source ne sont transmis ni par l'appairage, ni par NCC, ni par VPN. Entre réseaux, filtrer par plage d'adresses.

## Connectivité hybride

| Liaison | Débit | SLA | Mise en service | Chiffrement |
|---|---|---|---|---|
| **HA VPN** | Environ 250 000 paquets/s par tunnel, soit 1 à 3 Gbit/s ; plus de tunnels pour plus de débit | 99,99 % avec deux tunnels depuis les deux interfaces | Quelques heures | IPsec, sur Internet |
| **Partner Interconnect** | Rattachements de 50 Mbit/s à 50 Gbit/s | Google jusqu'au partenaire ; de bout en bout selon le partenaire | Selon l'opérateur | Aucun ; HA VPN par-dessus |
| **Dedicated Interconnect** | Circuits de 10, 100 ou 400 Gbit/s, jusqu'à 8 par connexion | 99,99 % (production critique) ou 99,9 % selon la topologie | Semaines : colocation, lettre d'autorisation, pose | MACsec ou HA VPN par-dessus |
| **Cross-Cloud Interconnect** | 10 ou 100 Gbit/s ; 400 Gbit/s vers AWS et OCI | 99,99 % avec deux connexions | 1 à 4 semaines | MACsec ou HA VPN par-dessus |

Toutes ces liaisons échangent leurs routes en BGP par un **[Cloud Router](#lexterm-cloud-router)**. Le **mode de routage dynamique global** du réseau rend les routes apprises dans une région valables dans toutes les autres, avec une pénalité pour préférer la liaison locale. Pour la haute disponibilité, deux liaisons dans deux zones de périphérie, et deux régions pour une résilience régionale ; [Cloud VPN](#cloud-vpn) sert de secours à un Interconnect ou de raccordement d'attente pendant sa livraison.

## DNS

Le blueprint recommande deux systèmes autoritaires : [Cloud DNS](#cloud-dns) pour les noms du cloud, le DNS du site pour les siens, reliés par transfert.

- **Zones privées** dans chaque réseau pour les noms internes ; avec Shared VPC, dans le projet hôte.
- **Hub DNS** : un seul réseau, en général le VPC de connectivité, porte les **zones de transfert** vers les serveurs du site et une **règle de serveur entrante** qui donne au site des adresses où interroger le résolveur du VPC. Les autres réseaux lui délèguent par des **zones d'appairage**.
- **Ouvrir le chemin retour** : les requêtes transférées vers le site partent de `35.199.192.0/19` ; cette plage doit être routée vers Google Cloud et autorisée par le pare-feu du site.

## Pièges

- **Concevoir l'adressage après le premier cluster.** Une plage de Pods trop petite limite le nombre de nœuds, et une plage qui recouvre le site interdit la connectivité hybride ; changer les plages d'un cluster en service est laborieux.
- **Une maille d'appairages.** L'appairage n'est pas transitif : relier *n* réseaux demande *n(n−1)/2* connexions, et les quotas (VM, règles de transfert internes) se comptent sur le groupe appairé tout entier. Passer à un hub NCC ; un appairage et un spoke NCC ne cohabitent pas entre deux mêmes réseaux.
- **Un seul tunnel HA VPN.** Sans le second tunnel depuis l'autre interface, aucun SLA.
- **Un routage dynamique régional avec des sous-réseaux dans plusieurs régions.** Le Cloud Router n'annonce alors au site que les sous-réseaux de sa région.
- **Oublier Cloud NAT dans une région.** Une passerelle ne sert que sa région : des nœuds GKE privés sans NAT dans leur région ne téléchargent pas leurs images hors d'Artifact Registry.
- **Une règle de serveur sortante sur tout le réseau.** Elle envoie toutes les requêtes vers le serveur de substitution et désactive la résolution des zones privées et du DNS interne de Compute Engine.
- **Le MTU.** 1 460 octets par défaut ; un tunnel VPN en retire pour l'encapsulation, et deux réseaux appairés doivent avoir le même.

## Alternatives en logiciel libre

- **Open vSwitch** et **OVN** (Apache 2.0) : commutation virtuelle et réseaux logiques distribués (routeurs, pare-feu, NAT), le rôle d'Andromeda sous OpenStack ou Kubernetes.
- **Cilium** (Apache 2.0) : réseau et politiques de sécurité par eBPF pour Kubernetes, la technologie de GKE Dataplane V2 ; il relie aussi plusieurs clusters (*Cluster Mesh*).
- **FRRouting** (GPL v2 et licences compatibles) : BGP, OSPF et routage statique sur un serveur Linux, l'équivalent d'un Cloud Router côté site ou dans une appliance.
- **strongSwan** (GPL v2) : IPsec avec IKEv1 et IKEv2, pour monter le côté distant d'un HA VPN.
- **VyOS** (GPL v2, LGPL pour ses bibliothèques) et **OPNsense** (BSD 2) : routeurs et pare-feu complets, utilisables comme appliance dans un hub ou comme extrémité de VPN sur site.
- **BIND 9** (MPL 2.0) et **CoreDNS** (Apache 2.0) : zones autoritaires, transfert conditionnel et vues, pour le DNS du site ou d'un cluster.
- **NetBox** (Apache 2.0) : gestion des plages d'adresses (IPAM) et de l'inventaire réseau, pour tenir le plan d'adressage partagé entre le site et les clouds.
