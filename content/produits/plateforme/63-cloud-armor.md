---
title: Cloud Armor
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 16, w: 566, h: 268}
  nodes:
    net: {label: Trafic internet, sub: "légitime et hostile", external: true, x: 8, y: 126, w: 160}
    ap: {label: Adaptive Protection, sub: "modèles de trafic", icon: categories/security-identity, x: 196, y: 36, w: 210}
    armor: {label: Cloud Armor, sub: "règles WAF, limitation", icon: categories/security-identity, focus: true, x: 196, y: 114, w: 210, h: 64}
    scc: {label: Security Command Center, sub: "alertes d'attaque", icon: produits/security-command-center, x: 448, y: 36, w: 282}
    lb: {label: Load balancer, sub: "service de backend", icon: categories/networking, x: 448, y: 118, w: 170}
    gke: {label: GKE, sub: "pods applicatifs", icon: produits/gke, x: 448, y: 214, w: 170}
  flows:
    - {from: net, to: armor, text: "Chaque requête est évaluée au point de présence Google, règle après règle, par ordre de priorité croissant, avant d'entrer dans le VPC."}
    - {from: armor, to: lb, text: "Les requêtes autorisées poursuivent vers le service de backend auquel la politique est rattachée."}
    - {from: lb, to: gke, text: "Le load balancer répartit le trafic restant sur les pods du cluster."}
    - {from: armor, to: ap, from_offset: -40, to_offset: -40, text: "Adaptive Protection apprend le profil de trafic normal de chaque service de backend et signale les écarts."}
    - {from: ap, to: scc, text: "Une attaque suspectée produit un événement dans Cloud Logging et un résultat dans Security Command Center, avec niveau de confiance."}
    - {from: ap, to: armor, from_offset: 40, to_offset: 40, control: true, text: "La règle de blocage proposée est déployée automatiquement ou après validation, puis affinée à la main."}
docs:
  Page produit: https://cloud.google.com/security/products/armor
  Documentation: https://docs.cloud.google.com/armor/docs
  Vue d'ensemble: https://docs.cloud.google.com/armor/docs/cloud-armor-overview
  Règles de sécurité: https://docs.cloud.google.com/armor/docs/security-policy-overview
  Langage des règles: https://docs.cloud.google.com/armor/docs/rules-language-reference
  Règles WAF préconfigurées: https://docs.cloud.google.com/armor/docs/waf-rules
  Règles gérées: https://docs.cloud.google.com/armor/docs/managed-rules-overview
  Adaptive Protection: https://docs.cloud.google.com/armor/docs/adaptive-protection-overview
  Cloud Armor Enterprise: https://docs.cloud.google.com/armor/docs/armor-enterprise-overview
  Protection DDoS réseau avancée: https://docs.cloud.google.com/armor/docs/advanced-network-ddos
  Politiques hiérarchiques: https://docs.cloud.google.com/armor/docs/hierarchical-policies-overview
  Limitation de débit: https://docs.cloud.google.com/armor/docs/configure-rate-limiting
  Gestion des bots: https://docs.cloud.google.com/armor/docs/bot-management
  Renseignement sur les menaces: https://docs.cloud.google.com/armor/docs/threat-intelligence
  API REST: https://docs.cloud.google.com/compute/docs/reference/rest/v1/securityPolicies
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/security-policies
  Tarifs: https://cloud.google.com/armor/pricing
  Notes de version: https://docs.cloud.google.com/armor/docs/release-notes
---

## Ce que c'est

Pare-feu applicatif et protection contre le déni de service, appliqués **en périphérie du réseau Google**, avant que le trafic n'atteigne le VPC. La protection contre les attaques volumétriques de couches 3 et 4 est permanente et automatique ; la protection applicative, elle, repose sur des règles que le projet écrit.

- **Politiques et règles.** Une *politique de sécurité* est une liste ordonnée de règles, chacune faite d'une **condition** et d'une **action** (autoriser, refuser avec un code 403, 404 ou 502, rediriger, limiter le débit, insérer un en-tête). Les priorités vont du plus petit nombre au plus grand ; la première règle qui correspond l'emporte. Une règle par défaut de priorité maximale termine toujours la liste.
- **Où elles s'attachent.** Aux services de backend de tous les Application Load Balancers externes, de l'Application Load Balancer interne régional, des proxy Network Load Balancers externes globaux et classiques, du passthrough Network Load Balancer externe régional, au transfert de protocole, et aux VM porteuses d'une adresse IP externe. Une politique *backend* filtre le trafic du service ; une politique *de périphérie* filtre en amont du cache, pour [Cloud CDN](#cloud-cdn) et [Media CDN](#media-cdn) ; les deux peuvent coexister sur un même service.
- **Conditions.** Listes d'adresses et de plages, code de pays, expressions du **langage de règles** portant sur l'URL, la méthode, les en-têtes, les cookies, les paramètres, la région ou le numéro de système autonome, et **groupes d'adresses** réutilisables entre politiques.
- **Règles WAF préconfigurées.** Des jeux de signatures dérivés de l'*OWASP ModSecurity Core Rule Set* — injection SQL, script intersites, inclusion de fichiers, exécution à distance, fuite de données. Les versions 4.22, 3.3 et 3.0 du CRS sont prises en charge, la 4.22 étant recommandée. Chaque jeu se règle par niveau de sensibilité et se corrige signature par signature, en désactivant celles qui produisent des faux positifs.
- **Règles gérées** (option payante) : signatures de menaces mises à jour par Google au fil des CVE et des vulnérabilités du jour, sans intervention du projet.
- **Limitation de débit.** Deux actions : `throttle` rejette au-delà d'un seuil, `rate_based_ban` bannit pour une durée l'auteur qui dépasse le seuil. La clé de comptage est l'adresse IP, un en-tête, un cookie, la région, ou une combinaison.
- **Mode aperçu.** Une règle en `preview` journalise ce qu'elle aurait fait sans l'appliquer : c'est le passage obligé avant d'activer un jeu WAF sur du trafic réel.
- **Adaptive Protection.** Modèle d'apprentissage du profil de trafic de chaque service de backend, qui détecte les attaques DDoS de couche 7 (déluges HTTP), les signale dans Cloud Logging et Security Command Center avec un niveau de confiance, et propose une règle de blocage — déployable automatiquement. Les *modèles granulaires* affinent l'analyse par hôte ou par préfixe de chemin.
- **Protection DDoS réseau avancée** pour les points de terminaison non proxy : passthrough Network Load Balancer externe régional, transfert de protocole, VM à adresse publique. Surveillance permanente, atténuations ciblées et télémétrie.
- **Renseignement sur les menaces.** L'expression `evaluateThreatIntelligence()` confronte l'adresse source à des listes tenues à jour — nœuds de sortie Tor, fournisseurs de VPN, adresses malveillantes connues, moteurs de recherche.
- **Politiques hiérarchiques**, attachées à l'organisation, à un dossier ou à un projet, pour imposer un socle de règles que les équipes ne peuvent pas contourner.
- **Deux niveaux de service.** **Standard**, à l'usage : protection L3/L4 permanente, règles WAF préconfigurées, facturation à la politique, à la règle et à la requête. **Cloud Armor Enterprise**, par abonnement annuel ou à l'usage : usage WAF inclus, listes d'adresses de tiers, renseignement sur les menaces, Adaptive Protection, protection DDoS réseau avancée, visibilité sur les attaques et politiques hiérarchiques ; l'abonnement annuel ouvre en plus la protection de facture et l'accès à l'équipe de réponse DDoS.

> [!TIP]
> Activer un jeu de règles WAF directement en mode bloquant casse presque toujours quelque chose. Le déroulé sûr : règle en `preview`, lecture des journaux pendant quelques jours, désactivation des signatures bruyantes, puis bascule en `deny`.

## À quoi ça sert

- Protéger un site ou une API publics des attaques applicatives courantes — injection, script intersites, exploration de chemins — sans modifier l'application.
- Filtrer géographiquement : n'ouvrir un service qu'aux pays où il est censé être utilisé, et bloquer les plages d'adresses connues pour leur activité malveillante.
- Limiter le débit d'une API par clé, par adresse ou par utilisateur, et bannir temporairement ceux qui insistent.
- Absorber une attaque DDoS de couche 7 avec des règles proposées par Adaptive Protection, sans attendre qu'une équipe écrive les conditions pendant l'incident.
- Imposer depuis l'organisation un socle de blocage commun à tous les projets, que les équipes complètent sans pouvoir l'affaiblir.
- Protéger une infrastructure hébergée ailleurs, en la plaçant derrière un Application Load Balancer externe dont les backends sont des NEG internet ou hybrides.

**À éviter** comme filtrage entre machines d'un même VPC : Cloud Armor ne voit que ce qui passe par un point d'entrée externe, le trafic est-ouest relève de [Cloud NGFW](#cloud-ngfw). À éviter aussi comme mécanisme d'authentification — bloquer sur l'adresse IP ne remplace pas une identité vérifiée ; Identity-Aware Proxy ou une authentification applicative sont à leur place ici. Enfin, une politique posée sur un backend que l'on peut joindre directement, sans passer par l'équilibreur, ne protège rien : il faut fermer les adresses publiques des instances en parallèle.

## Alternatives en logiciel libre

- **Coraza** : moteur WAF compatible avec le langage de règles ModSecurity et le *Core Rule Set*, en Go, greffable dans Envoy, Caddy ou Traefik. **ModSecurity**, le moteur d'origine, est maintenu par l'OWASP.
- **OWASP CRS** : le jeu de règles dont dérivent les règles préconfigurées de Cloud Armor, utilisable tel quel avec Coraza ou un autre moteur.
- **CrowdSec** : détection comportementale sur les journaux et blocage par listes partagées entre participants, proche dans l'esprit d'Adaptive Protection et du renseignement sur les menaces.
- **Fail2ban** : bannissement d'adresses sur motif dans les journaux, l'équivalent modeste du `rate_based_ban`.
- **NAXSI** : pare-feu applicatif pour NGINX fondé sur une liste blanche apprise plutôt que sur des signatures.
- **BunkerWeb** : distribution NGINX préconfigurée qui réunit WAF, limitation de débit, filtrage géographique et anti-bot en un seul produit.
