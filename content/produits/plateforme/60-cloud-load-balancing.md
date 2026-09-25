---
title: Cloud Load Balancing
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 584, h: 268}
  nodes:
    users: {label: Clients internet, sub: "navigateurs, API", external: true, x: 8, y: 126, w: 146}
    dns: {label: Cloud DNS, sub: "enregistrement A", icon: categories/networking, x: 174, y: 208, w: 172}
    armor: {label: Cloud Armor, sub: "filtrage en amont", icon: categories/security-identity, x: 174, y: 104, w: 172}
    lb: {label: Cloud Load Balancing, sub: "mappage d'URL", icon: categories/networking, focus: true, x: 368, y: 114, w: 200, h: 64}
    mig: {label: Compute Engine, sub: "groupe d'instances", icon: produits/compute-engine, x: 584, y: 36, w: 166}
    gcs: {label: Cloud Storage, sub: "bucket de backend", icon: produits/cloud-storage, x: 584, y: 122, w: 158}
    run: {label: Cloud Run, sub: "NEG sans serveur", icon: produits/cloud-run, x: 584, y: 208, w: 158}
  flows:
    - {from: dns, to: users, control: true, text: "Le nom de domaine du service est résolu par un enregistrement qui porte l'adresse IP de la règle de transfert."}
    - {from: users, to: armor, from_side: right, to_side: left, text: "La requête entre dans le réseau Google au point de présence le plus proche du client, où la règle Cloud Armor attachée au service de backend est évaluée."}
    - {from: armor, to: lb, text: "Le trafic accepté atteint le proxy, qui termine la connexion TLS puis choisit un service de backend d'après le mappage d'URL."}
    - {from: lb, to: mig, from_side: right, to_side: left, from_offset: -26, text: "Le chemin par défaut part vers le groupe d'instances géré, réparti selon le mode d'équilibrage et la capacité déclarée de chaque backend."}
    - {from: lb, to: gcs, from_side: right, to_side: left, text: "Les chemins de fichiers statiques sont servis par un bucket de backend, sans instance de calcul."}
    - {from: lb, to: run, from_side: right, to_side: left, from_offset: 26, text: "Les chemins d'API partent vers un groupe de points de terminaison réseau sans serveur qui désigne le service Cloud Run."}
docs:
  Page produit: https://cloud.google.com/load-balancing
  Documentation: https://docs.cloud.google.com/load-balancing/docs
  Vue d'ensemble: https://docs.cloud.google.com/load-balancing/docs/load-balancing-overview
  Choisir un load balancer: https://docs.cloud.google.com/load-balancing/docs/choosing-load-balancer
  Application Load Balancer: https://docs.cloud.google.com/load-balancing/docs/application-load-balancer
  Proxy Network Load Balancer: https://docs.cloud.google.com/load-balancing/docs/proxy-network-load-balancer
  Passthrough Network Load Balancer: https://docs.cloud.google.com/load-balancing/docs/passthrough-network-load-balancer
  Services de backend: https://docs.cloud.google.com/load-balancing/docs/backend-service
  Groupes de points de terminaison réseau: https://docs.cloud.google.com/load-balancing/docs/negs
  Contrôles d'état: https://docs.cloud.google.com/load-balancing/docs/health-check-concepts
  Gestion du trafic: https://docs.cloud.google.com/load-balancing/docs/https/traffic-management-global
  Certificats SSL: https://docs.cloud.google.com/load-balancing/docs/ssl-certificates
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/urlMaps
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/url-maps
  Quotas et limites: https://docs.cloud.google.com/load-balancing/docs/quotas
  Tarifs: https://cloud.google.com/vpc/network-pricing
  Notes de version: https://docs.cloud.google.com/load-balancing/docs/release-notes
---

## Ce que c'est

Service d'équilibrage de charge défini par logiciel, sans appliance ni instance à provisionner. Il s'appuie sur les mêmes briques que les services Google : les *Google Front Ends* (GFE) répartis dans plus de 80 points de présence, la pile de virtualisation réseau Andromeda, le répartiteur Maglev et le proxy libre Envoy.

- **Deux familles.** Les **Application Load Balancers** travaillent en couche 7 sur HTTP et HTTPS : ils lisent l'URL, les en-têtes et les cookies pour décider de la destination. Les **Network Load Balancers** travaillent en couche 4 ; ils se déclinent en variante **proxy** (TCP, avec déchargement TLS optionnel) et en variante **passthrough** (TCP, UDP, ESP, GRE, ICMP, ICMPv6).
- **Proxy ou passthrough.** Un proxy termine la connexion du client et en ouvre une nouvelle vers le backend : il voit le contenu applicatif, mais présente sa propre adresse IP source aux instances. Un *passthrough* ne termine rien : les paquets arrivent au backend avec leurs adresses et ports d'origine, et les réponses repartent directement vers le client sans repasser par le répartiteur (*direct server return*).
- **Externe ou interne.** Un load balancer externe reçoit le trafic d'internet ; un load balancer interne n'est joignable que depuis le même réseau VPC ou depuis un réseau qui lui est connecté (appairage, VPN, Interconnect).
- **Global, interrégional ou régional.** Un load balancer global présente une **adresse IP anycast** unique et répartit vers des backends de plusieurs régions, avec bascule automatique. L'équivalent interne s'appelle *interrégional* : il expose une adresse IP interne régionale mais reste joignable depuis toutes les régions. Un load balancer régional termine les connexions dans une seule région — le choix des déploiements soumis à une contrainte de juridiction, puisqu'il garantit où le TLS est terminé.
- **Anatomie d'une configuration.** Une **règle de transfert** associe une adresse IP et un port à un **proxy cible** ; celui-ci consulte un **mappage d'URL** (hôtes, chemins, réécritures, pondérations) qui désigne un **service de backend** ou un **bucket de backend** ; le service de backend porte le protocole, la politique de session, le mode d'équilibrage et le **contrôle d'état**. Les load balancers *passthrough* se passent de proxy cible et de mappage d'URL.
- **Backends.** Groupes d'instances gérés ou non, buckets Cloud Storage, et **groupes de points de terminaison réseau** (NEG) : *zonaux* (adresses IP de VM ou pods GKE), *sans serveur* (Cloud Run, App Engine), *internet* (origine hors de Google Cloud), *hybrides* (sur site ou autre cloud), *Private Service Connect* et *port mapping*.
- **Contrôles d'état.** Des sondes centralisées interrogent chaque point de terminaison en TCP, SSL, HTTP, HTTPS, HTTP/2 ou gRPC. Un backend déclaré défaillant sort de la rotation sans que les connexions des autres soient touchées.
- **Gestion du trafic** sur les Application Load Balancers : routage par en-tête, par paramètre de requête ou par expression régulière, répartition pondérée entre services (déploiements *canary*), miroir de trafic, réécriture d'URL, redirections, nouvelles tentatives, délais d'expiration, injection de fautes et *outlier detection*.
- **Terminaison TLS.** Certificats gérés par Google (validation par équilibreur ou par DNS), certificats auto-gérés, ou certificats distribués par Certificate Manager pour les parcs de domaines. Les politiques SSL fixent la version minimale de TLS et la suite de chiffrement.
- **Facturation.** Une règle de transfert est facturée à l'heure, à quoi s'ajoutent les données traitées par le proxy et le transfert sortant, dont le tarif dépend du niveau de service réseau retenu (voir [Network Service Tiers](#network-service-tiers)).

### Choisir

1. **Quel protocole ?** HTTP ou HTTPS → Application Load Balancer. TCP avec déchargement TLS → proxy Network Load Balancer. UDP, ESP, GRE, ICMP, ou besoin de conserver l'adresse IP source du client → passthrough Network Load Balancer.
2. **Quels clients ?** Internet → variante externe. Clients du VPC, d'un réseau appairé, d'un tunnel VPN ou d'un Interconnect → variante interne.
3. **Quels backends ?** Plusieurs régions → global (externe) ou interrégional (interne). Une seule région, ou obligation de terminer le TLS dans une juridiction donnée → régional.
4. **Quel niveau réseau ?** Les variantes globales externes n'existent qu'en niveau Premium ; les variantes régionales externes acceptent aussi le niveau Standard.

> [!TIP]
> L'authentification par adresse IP source ne survit pas à un proxy : les connexions vers les backends portent l'adresse du GFE ou d'Envoy, et l'adresse réelle du client n'est lisible que dans l'en-tête `X-Forwarded-For`. Si l'application en dépend vraiment, il faut un load balancer *passthrough* ; sinon, authentifier avec Identity-Aware Proxy.

## À quoi ça sert

- Publier un site ou une API sur un domaine unique avec certificat géré, en répartissant sur des backends de plusieurs continents derrière une seule adresse IP.
- Placer un point d'entrée commun devant des backends hétérogènes : VM pour le cœur applicatif, [Cloud Run](#cloud-run) pour les API, bucket [Cloud Storage](#cloud-storage) pour les fichiers statiques, le tout routé par chemin d'URL.
- Servir de socle aux Ingress et Gateway de [GKE](#gke), qui créent et pilotent les mêmes ressources à partir de manifestes Kubernetes.
- Exposer un service interne entre équipes ou entre environnements, sans adresse publique et sans sortir du VPC.
- Absorber les pointes de trafic : la capacité se règle à la hausse sans préchauffage, et un pic peut être dérouté vers les régions qui ont de la place.
- Répartir des protocoles que les proxys ne savent pas traiter — DNS en UDP, IPsec, tunnels GRE — en conservant les adresses source.

**À éviter** pour le trafic entre microservices d'un même maillage : [Cloud Service Mesh](#cloud-service-mesh) gère le routage, les nouvelles tentatives et le chiffrement mutuel au niveau du client, sans faire transiter chaque appel par un répartiteur. À éviter aussi comme unique mécanisme de répartition géographique quand il s'agit surtout de rapprocher des fichiers des utilisateurs : un cache de périphérie ([Cloud CDN](#cloud-cdn)) coûte moins cher que d'acheminer chaque octet depuis l'origine. Enfin, un service [Cloud Run](#cloud-run) joignable sur son URL `run.app` n'a pas besoin de load balancer : on n'en ajoute un que pour un domaine propre, un cache, des règles Cloud Armor ou un routage entre plusieurs services.

## Alternatives en logiciel libre

- **Envoy** : le proxy qui implémente la plupart des modes de Cloud Load Balancing ; même modèle de *listeners*, de clusters et de contrôles d'état, piloté par une API de configuration dynamique.
- **HAProxy** : répartiteur TCP et HTTP réputé pour sa robustesse et sa finesse de réglage, l'équivalent direct des proxys de couche 4 et 7.
- **NGINX** : serveur web et proxy inverse, souvent choisi quand la terminaison TLS et le service de fichiers statiques comptent autant que la répartition.
- **Traefik** : proxy qui découvre ses backends dans l'orchestrateur (Kubernetes, Docker, Consul) et obtient ses certificats par ACME, proche de l'expérience Ingress.
- **IPVS** et **Keepalived** : répartition en couche 4 dans le noyau Linux avec retour direct au client, l'équivalent des load balancers *passthrough* ; Keepalived y ajoute la bascule d'adresse virtuelle par VRRP.
- **Katran** : répartiteur de couche 4 en eBPF/XDP publié par Meta, bâti comme Maglev sur le hachage cohérent et le *direct server return*.
