---
title: Cloud NGFW
subgroup: Réseau
icon: categories/networking
aka: Cloud Firewall
schema:
  size: [760, 300]
  zones:
    - {label: Organisation, x: 170, y: 16, w: 576, h: 268}
    - {label: Réseau VPC, x: 186, y: 100, w: 548, h: 170}
  nodes:
    net: {label: Internet, sub: "trafic nord-sud", external: true, x: 8, y: 150, w: 150}
    hier: {label: Politique hiérarchique, sub: "organisation, dossiers", icon: categories/security-identity, x: 196, y: 32, w: 230}
    prof: {label: Profil de sécurité, sub: "menaces, filtrage d'URL", icon: categories/security-identity, x: 470, y: 32, w: 200}
    ngfw: {label: Cloud NGFW, sub: "politique de réseau VPC", icon: categories/networking, focus: true, x: 200, y: 150, w: 200, h: 70}
    vm: {label: Compute Engine, sub: "instances protégées", icon: produits/compute-engine, x: 450, y: 114, w: 170}
    db: {label: Cloud SQL, sub: "adresse IP privée", icon: produits/cloud-sql, x: 450, y: 194, w: 170}
  flows:
    - {from: hier, to: ngfw, control: true, text: "Les règles de la politique hiérarchique attachée à l'organisation ou au dossier sont évaluées avant celles du réseau, et peuvent déléguer la décision à l'échelon suivant."}
    - {from: prof, to: ngfw, control: true, text: "Le profil de sécurité fournit les signatures de menaces et les catégories d'URL que les règles d'inspection appliquent."}
    - {from: net, to: ngfw, text: "Le trafic entrant est confronté aux règles, dans l'ordre des priorités, jusqu'à la première correspondance."}
    - {from: ngfw, to: vm, text: "Le trafic autorisé, éventuellement inspecté en couche 7, atteint l'interface réseau de l'instance."}
    - {from: vm, to: db, text: "Le trafic est-ouest entre charges du même réseau est soumis aux mêmes politiques."}
    - {from: ngfw, to: db, control: true, text: "Une règle ciblée par tags sécurisés n'ouvre le port de la base qu'aux instances portant le tag applicatif : c'est la micro-segmentation."}
docs:
  Page produit: https://cloud.google.com/security/products/firewall
  Documentation: https://docs.cloud.google.com/firewall/docs
  Vue d'ensemble: https://docs.cloud.google.com/firewall/docs/about-firewalls
  Politiques de pare-feu: https://docs.cloud.google.com/firewall/docs/firewall-policies-overview
  Règles de politique: https://docs.cloud.google.com/firewall/docs/firewall-policies-rule-details
  Ordre d'évaluation: https://docs.cloud.google.com/firewall/docs/firewall-policies-rule-eval-order
  Politiques hiérarchiques: https://docs.cloud.google.com/firewall/docs/firewall-policies
  Politiques de réseau globales: https://docs.cloud.google.com/firewall/docs/network-firewall-policies
  Politiques de réseau régionales: https://docs.cloud.google.com/firewall/docs/regional-firewall-policies
  Tags sécurisés: https://docs.cloud.google.com/firewall/docs/tags-firewalls-overview
  Objets FQDN: https://docs.cloud.google.com/firewall/docs/fqdn-objects-overview
  Profils de sécurité: https://docs.cloud.google.com/firewall/docs/about-security-profiles
  Points de terminaison de pare-feu: https://docs.cloud.google.com/firewall/docs/about-firewall-endpoints
  Détection et prévention d'intrusion: https://docs.cloud.google.com/firewall/docs/about-intrusion-prevention
  Filtrage d'URL: https://docs.cloud.google.com/firewall/docs/about-url-filtering
  Niveaux de service: https://docs.cloud.google.com/firewall/docs/ngfw_tiers
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/networkFirewallPolicies
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/network-firewall-policies
  Quotas et limites: https://docs.cloud.google.com/firewall/docs/quotas
  Tarifs: https://cloud.google.com/firewall/pricing
  Notes de version: https://docs.cloud.google.com/firewall/docs/release-notes
---

## Ce que c'est

Pare-feu distribué, appliqué par la pile de virtualisation réseau Andromeda directement au niveau de chaque interface de VM : il n'y a pas d'appliance à traverser, donc pas de goulot d'étranglement ni de point de panne. Il filtre le trafic **nord-sud** (entrant ou sortant du [VPC](#vpc)) comme le trafic **est-ouest** (entre ressources d'un même réseau), avec inspection avec état et, au niveau le plus élevé, contrôle applicatif de couche 7.

- **Quatre sortes de politiques.** Les **politiques hiérarchiques** s'attachent à l'organisation ou à un dossier et s'imposent à tous les réseaux qu'ils contiennent. Les **politiques de réseau globales** couvrent toutes les régions d'un réseau VPC, les **régionales** une région donnée. Les **politiques système régionales** sont créées et tenues par Google quand un de ses services l'exige : on ne peut qu'y activer la journalisation, et leur évaluation n'est pas facturée. À part, les **règles de pare-feu VPC** (le modèle sans objet politique) restent utilisables sur les réseaux réguliers.
- **Ordre d'évaluation.** Politiques hiérarchiques, puis politiques système régionales, puis — selon le mode d'application choisi pour le réseau — les règles de pare-feu VPC avant ou après les politiques de réseau globales et régionales, et enfin les **actions implicites** : tout trafic entrant est refusé, tout trafic sortant est autorisé. Dans chaque politique, les règles sont classées par priorité croissante et la première correspondance tranche ; l'action `goto_next` renvoie la décision à l'échelon suivant.
- **Cibles et sources.** Les **tags sécurisés**, gérés au niveau de l'organisation avec leurs propres contrôles IAM, désignent les ressources auxquelles une règle s'applique — c'est la base de la micro-segmentation, indépendante du plan d'adressage. Les règles de pare-feu VPC ciblent par étiquettes réseau ou par compte de service. Sources et destinations se déclarent en plages d'adresses, en **groupes d'adresses** nommés, en **objets FQDN** (noms de domaine plutôt qu'adresses), en **objets de géolocalisation**, ou par listes de renseignement sur les menaces tenues par Google.
- **Inspection de couche 7.** Un **point de terminaison de pare-feu**, créé au niveau de l'organisation et déployé par zone, reçoit le trafic que les règles lui envoient. Un **profil de sécurité** — regroupé en *groupe de profils* référencé par la règle — décrit ce qu'il doit faire : détection et prévention d'intrusion par signatures, filtrage d'URL sur le chemin complet et pas seulement le domaine, bac à sable antimaliciel [!PREVERSION]. L'**inspection TLS** déchiffre le trafic pour permettre cette analyse.
- **Load balancers.** Les proxys Envoy gérés des Application Load Balancers internes et des proxy Network Load Balancers internes sont aussi des cibles de règles, en couches 3 et 4 ; l'inspection de couche 7 y est réservée à l'Application Load Balancer interne interrégional.
- **Trois niveaux de facturation**, non souscrits mais déduits des fonctions employées. **Essentials** : inspection avec état, tags sécurisés, groupes d'adresses, règles de pare-feu VPC — sans frais. **Standard** : objets FQDN, objets de géolocalisation, renseignement sur les menaces, facturés sur le trafic nord-sud évalué. **Enterprise** : inspection de couche 7, facturée à l'heure par point de terminaison déployé et au gigaoctet inspecté, sur le trafic nord-sud, est-ouest et à destination des équilibreurs internes pris en charge.
- **Journalisation** activable règle par règle, avec un format dédié et des métriques exploitables dans [Network Intelligence Center](#network-intelligence-center) pour repérer les règles inutilisées ou trop permissives.

> [!WARNING]
> Une règle de politique hiérarchique `deny` posée à l'échelle de l'organisation l'emporte sur toute règle `allow` d'un projet : c'est l'intérêt du mécanisme, mais c'est aussi la première cause de trafic bloqué sans explication visible dans le projet. L'analyseur de pare-feu et les tests de connectivité désignent la règle fautive, quel que soit l'échelon.

## À quoi ça sert

- Refermer un réseau par défaut : refuser tout le trafic entrant, puis n'ouvrir que les flux nommés, chacun ciblé par un tag sécurisé plutôt que par une plage d'adresses.
- Micro-segmenter une application : le niveau web ne parle qu'au niveau applicatif, qui seul atteint la base, sans dépendre du découpage en sous-réseaux.
- Imposer depuis l'organisation un socle non contournable — blocage du SSH depuis internet, interdiction des plages non allouées, refus des adresses signalées comme malveillantes.
- Restreindre la sortie vers une liste de domaines autorisés avec des objets FQDN, pour des charges qui ne doivent joindre que quelques services externes.
- Inspecter le trafic est-ouest à la recherche d'exploits et de maliciels, avec déchiffrement TLS, sans réacheminer le trafic vers une appliance tierce.
- Filtrer la navigation sortante de serveurs ou de postes gérés par catégorie et par URL.

**À éviter** comme pare-feu applicatif web devant un service public : le filtrage des requêtes HTTP, la limitation de débit et la protection DDoS relèvent de [Cloud Armor](#cloud-armor), appliqué en périphérie avant même que le trafic n'entre dans le réseau. À éviter aussi comme substitut à [Private Service Connect](#private-service-connect) ou à l'accès privé à Google : fermer l'accès à internet est plus sûr que de le filtrer. Enfin, l'inspection de couche 7 ne couvre pas le trafic sortant des charges sans serveur.

## Alternatives en logiciel libre

- **nftables** (et son prédécesseur **iptables**) : le filtrage avec état du noyau Linux, l'équivalent de ce que Cloud NGFW applique à chaque interface, mais à configurer machine par machine.
- **pfSense CE** et **OPNsense** : distributions de pare-feu complètes sur FreeBSD, avec interface web, règles par interface, VPN et journalisation — le modèle de l'appliance périmétrique.
- **Suricata** : moteur de détection et de prévention d'intrusion par signatures, avec les jeux de règles Emerging Threats ; l'équivalent direct du service IPS des profils de sécurité. **Zeek** le complète par l'analyse de protocoles.
- **Squid** avec un filtre de catégories : filtrage d'URL et inspection TLS de la navigation sortante.
- **Cilium** et ses politiques réseau eBPF : micro-segmentation par identité d'atelier plutôt que par adresse, l'esprit des tags sécurisés appliqué aux conteneurs.
- **firewalld** : couche de gestion par zones au-dessus de nftables, utile pour tenir un jeu de règles cohérent sur un parc de VM.
