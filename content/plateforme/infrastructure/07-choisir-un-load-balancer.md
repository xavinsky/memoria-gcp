---
title: Choisir un load balancer
subgroup: Calcul et réseau
---

[Cloud Load Balancing](#cloud-load-balancing) regroupe une douzaine de variantes, qui se départagent par trois questions posées dans l'ordre de la page *Choose a load balancer* de la documentation : le **type de trafic** (HTTP ou non), la **provenance des clients** (Internet ou réseau privé), la **portée des backends** (plusieurs régions ou une seule). Une quatrième découle des précédentes : **proxy ou passthrough**, c'est-à-dire terminer la connexion du client ou transmettre ses paquets tels quels.

![Arbre de décision : protocole, provenance des clients, puis portée du load balancer](../../svg/choix-load-balancer.svg)

- **Protocole.** HTTP, HTTPS, HTTP/2, gRPC, WebSockets : **Application Load Balancer**, qui route sur l'hôte, le chemin, les en-têtes. TCP, avec déchargement TLS en option : **Network Load Balancer proxy**. UDP, ESP, GRE, ICMP, ou besoin que le backend voie l'adresse IP du client : **Network Load Balancer passthrough**, où les réponses repartent directement vers le client.
- **Clients.** Internet : variante *externe*. Réseau VPC, réseau appairé, VPN ou Interconnect : variante *interne*.
- **Portée.** Un load balancer **global** externe présente une adresse *anycast* unique et répartit vers plusieurs régions ; son équivalent interne est **interrégional**, joignable depuis toutes les régions par une adresse interne régionale. Un load balancer **régional** termine les connexions et le TLS dans une seule région : c'est le choix imposé par une exigence de juridiction.

## Matrice de choix

| Load balancer | Trafic | Portée | Implémentation | Niveau réseau | À retenir |
|---|---|---|---|---|---|
| **Application LB externe global** | HTTP(S) | Plusieurs régions, adresse anycast, IPv6 | GFE fondé sur Envoy | Premium | Le point d'entrée web par défaut : Cloud CDN, Cloud Armor, IAP, NEG sans serveur multirégion |
| [!DECONSEILLE] **Application LB classique** | HTTP(S) | Global en Premium, régional en Standard | GFE | Premium ou Standard | Variante héritée ; Google recommande de migrer vers le global |
| **Application LB externe régional** | HTTP(S) | Une région | Envoy, sous-réseau proxy uniquement | Premium ou Standard | TLS terminé dans la région ; pas de Cloud CDN |
| **Application LB interne régional** | HTTP(S) | Une région ; accès global en option | Envoy, sous-réseau proxy uniquement | Premium | Point d'entrée privé entre services, trafic avancé |
| **Application LB interne interrégional** | HTTP(S) | Plusieurs régions, bascule entre elles | Envoy, sous-réseau proxy uniquement | Premium | Service interne résilient à la perte d'une région |
| **Network LB proxy externe global** | TCP, TLS en option | Plusieurs régions | GFE fondé sur Envoy | Premium | Protocole TCP non HTTP exposé mondialement |
| **Network LB proxy externe régional** | TCP | Une région | Envoy | Premium ou Standard | TCP avec contrainte de juridiction |
| **Network LB proxy interne** (régional, interrégional) | TCP sans déchargement TLS | Une ou plusieurs régions | Envoy | Premium | Service TCP interne derrière une adresse stable |
| **Network LB passthrough externe** | TCP, UDP, ESP, GRE, ICMP | Régional ; global [!PREVERSION] | Maglev | Premium ou Standard (régional) | Adresse du client conservée, protocoles non TCP |
| **Network LB passthrough interne** | TCP, UDP, ICMP, SCTP, ESP, AH, GRE | Régional ; accès global en option | Andromeda | Premium | Appliances réseau, saut suivant de routes, bases en haute disponibilité |

Les load balancers globaux externes n'existent qu'en niveau Premium ; tous les load balancers internes utilisent le réseau de Google. Pour un service Cloud Run, les **NEG sans serveur** ne se branchent que sur les Application Load Balancers — jamais sur un Network LB.

## Autour du load balancer

| Service | Rôle | Où il s'attache |
|---|---|---|
| **[Cloud CDN](#cloud-cdn)** | Cache dans les points de présence de Google | Option du service ou du bucket de backend d'un Application LB externe global ou classique |
| **[Media CDN](#media-cdn)** | Diffusion vidéo et gros téléchargements, caches chez les opérateurs | Service autonome, sans load balancer ; accès par l'équipe commerciale |
| **[Cloud Armor](#cloud-armor)** | WAF (règles OWASP CRS), limitation de débit, DDoS | Services de backend des Application LB externes et de l'Application LB interne régional, Network LB proxy externe global et classique, passthrough externe régional |
| **[Certificate Manager](#certificate-manager)** | Certificats gérés ou importés, mappage de certificats par nom d'hôte, TLS mutuel | Proxys cibles HTTPS et SSL des Application LB et des Network LB proxy |
| **[Cloud DNS](#cloud-dns)** | Enregistrement A ou AAAA vers l'adresse du load balancer ; autorisation DNS des certificats | Zone publique ou privée |
| **[Identity-Aware Proxy](#identity-aware-proxy)** | N'admet que des utilisateurs authentifiés, par IAM | Service de backend d'un Application LB ; incompatible avec Cloud CDN sur un même service de backend à NEG sans serveur |

Un Application LB interne interrégional n'a pas d'adresse anycast : on lui donne une règle de transfert, donc une adresse interne, dans chaque région où se trouvent des clients, et une politique de routage DNS géographique de Cloud DNS envoie chaque client vers l'adresse de sa région.

## Exemple Pulumi : Cloud Run derrière un Application LB externe global

Le service n'accepte que le trafic interne et celui des load balancers, et son URL `run.app` est désactivée : le seul chemin passe par le load balancer, donc par Cloud Armor et le certificat du domaine.

```python
import pulumi
import pulumi_gcp as gcp

REGION = "europe-west1"

service = gcp.cloudrunv2.Service(
    "app",
    location=REGION,
    ingress="INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
    default_uri_disabled=True,      # pas d'URL run.app qui contourne le load balancer
    invoker_iam_disabled=True,      # service public : le filtrage se fait au load balancer
    template={"containers": [{"image": "REGION-docker.pkg.dev/PROJECT_ID/REPO/app:TAG"}]},
)

neg = gcp.compute.RegionNetworkEndpointGroup(
    "app-neg",
    region=REGION,
    network_endpoint_type="SERVERLESS",
    cloud_run={"service": service.name},
)

backend = gcp.compute.BackendService(
    "app-backend",
    load_balancing_scheme="EXTERNAL_MANAGED",     # global externe ; EXTERNAL = classique
    backends=[{"group": neg.id}],
    # security_policy=politique_armor.id, enable_cdn=True
)

url_map = gcp.compute.URLMap("app-urlmap", default_service=backend.id)
cert = gcp.compute.ManagedSslCertificate("app-cert", managed={"domains": ["app.example.com"]})
proxy = gcp.compute.TargetHttpsProxy("app-proxy", url_map=url_map.id, ssl_certificates=[cert.id])
ip = gcp.compute.GlobalAddress("app-ip")

gcp.compute.GlobalForwardingRule(
    "app-https",
    load_balancing_scheme="EXTERNAL_MANAGED",
    ip_address=ip.address,
    port_range="443",
    target=proxy.id,
)
pulumi.export("ip", ip.address)   # enregistrement A de app.example.com
```

Le certificat géré par le load balancer n'est émis qu'une fois l'enregistrement DNS pointé sur l'adresse. Pour une bascule sans coupure, ou pour de nombreux domaines, passer par Certificate Manager avec autorisation DNS (`gcp.certificatemanager.Certificate`, `CertificateMap`, `CertificateMapEntry`) et le paramètre `certificate_map` du proxy cible. Pour servir le même service depuis plusieurs régions, ajouter un NEG sans serveur par région au même service de backend.

## Pièges

- **L'URL par défaut du service reste ouverte.** Sans restriction d'entrée à « interne et Cloud Load Balancing » et sans désactivation de l'URL `run.app`, n'importe qui contourne Cloud Armor, IAP et le certificat.
- **L'adresse du client disparaît derrière un proxy.** Les backends voient l'adresse du GFE ou d'Envoy ; l'adresse réelle est dans `X-Forwarded-For`. Une application qui authentifie par adresse source demande un passthrough, ou mieux, IAP.
- **Oublier le sous-réseau proxy uniquement.** Les load balancers fondés sur Envoy (régionaux, internes, interrégionaux) en exigent un par région et par réseau, d'au moins `/26` ; Google conseille de commencer en `/23`. Le pare-feu des backends doit autoriser cette plage.
- **Des contrôles d'état bloqués.** Pour des backends VM ou GKE, autoriser en entrée les sondes (`35.191.0.0/16` pour les load balancers à GFE) ; sinon la règle implicite les refuse et tous les backends paraissent défaillants. Les NEG sans serveur n'ont pas de contrôle d'état : la détection d'anomalies (*outlier detection*) en tient lieu sur le load balancer global.
- **Un load balancer interne régional appelé depuis une autre région.** Refusé tant que l'accès global n'est pas activé sur la règle de transfert.
- **Affinité de session sur un NEG sans serveur.** Elle ne s'applique pas ; utiliser l'affinité de session de Cloud Run.
- **Le port 80 oublié.** Une règle de transfert HTTPS ne répond que sur 443 ; ajouter une seconde règle sur 80, avec un mappage d'URL qui redirige vers HTTPS.
- **Activer un jeu WAF directement en blocage.** Passer d'abord la règle Cloud Armor en `preview`, lire les journaux, puis bloquer.
- **Les NEG sans serveur en régional.** Le trafic vers les NEG sans serveur des load balancers régionaux, externes et internes, est plafonné à 5 000 requêtes par seconde par projet, tous load balancers confondus.

## Alternatives en logiciel libre

- **Envoy** (Apache 2.0) : le proxy qui implémente les Application LB régionaux et internes et Cloud Service Mesh ; routage de couche 7, nouvelles tentatives, détection d'anomalies.
- **HAProxy** (GPL v2) : load balancer TCP et HTTP très répandu, avec contrôles d'état, affinité et terminaison TLS ; l'équivalent d'un load balancer proxy régional.
- **NGINX** (BSD 2) et **Traefik** (MIT) : proxys inverses HTTP ; Traefik se configure seul à partir de Kubernetes ou de Docker et obtient ses certificats par ACME.
- **Katran** (GPL v2) : répartiteur de couche 4 en XDP publié par Meta, de la même famille que Maglev, pour le terrain du passthrough.
- **MetalLB** (Apache 2.0) et **Keepalived** (GPL v2) : adresses de service annoncées en BGP ou en ARP, et bascule d'adresse virtuelle, pour exposer des services sans load balancer géré.
- **Apache Traffic Server** (Apache 2.0) : cache HTTP de périphérie, dans le rôle de Cloud CDN.
- **Coraza** (Apache 2.0) : WAF compatible avec les règles OWASP CRS, intégrable à Envoy ou Caddy, dans le rôle des règles préconfigurées de Cloud Armor.
