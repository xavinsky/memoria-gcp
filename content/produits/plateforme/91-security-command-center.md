---
title: Security Command Center
subgroup: IAM et sécurité
icon: produits/security-command-center
schema:
  size: [760, 320]
  zones:
    - {label: Organisation, x: 190, y: 16, w: 558, h: 290}
  nodes:
    sha: {label: Security Health Analytics, sub: "configuration", icon: categories/security-identity, x: 205, y: 30, w: 250}
    etd: {label: Event Threat Detection, sub: "journaux, menaces", icon: categories/security-identity, x: 205, y: 120, w: 250}
    sdp: {label: Sensitive Data Protection, sub: "données sensibles", icon: categories/security-identity, x: 205, y: 210, w: 250}
    bq: {label: BigQuery, sub: "export continu", icon: produits/bigquery, x: 490, y: 30, w: 250}
    scc: {label: Security Command Center, sub: "résultats, posture", icon: produits/security-command-center, focus: true, x: 490, y: 110, w: 250, h: 64}
    ps: {label: Pub/Sub, sub: "notifications", icon: categories/data-analytics, x: 490, y: 220, w: 250}
  flows:
    - {from: sha, to: scc, to_offset: -16, text: "Security Health Analytics analyse la configuration des ressources et ouvre un résultat par écart : bucket public, clé sans rotation, règle de pare-feu trop large."}
    - {from: etd, to: scc, text: "Event Threat Detection lit les journaux d'audit, DNS et réseau pour repérer des comportements : minage de cryptomonnaie, ajout d'un propriétaire hors du domaine, exfiltration."}
    - {from: sdp, to: scc, text: "La découverte de Sensitive Data Protection indique quelles ressources contiennent des données personnelles ; l'exposition aux attaques s'en sert pour pondérer les chemins."}
    - {from: scc, to: bq, text: "Un export continu déverse les résultats dans BigQuery, pour les croiser avec l'inventaire des ressources et alimenter des tableaux de bord."}
    - {from: scc, to: ps, text: "Une notification Pub/Sub déclenche un traitement automatique — fermeture d'un accès, ouverture d'un ticket — à chaque nouveau résultat."}
docs:
  Page produit: https://cloud.google.com/security/products/security-command-center
  Documentation: https://docs.cloud.google.com/security-command-center/docs
  Vue d'ensemble: https://docs.cloud.google.com/security-command-center/docs/security-command-center-overview
  Niveaux de service: https://docs.cloud.google.com/security-command-center/docs/service-tiers
  Sources de résultats: https://docs.cloud.google.com/security-command-center/docs/concepts-security-sources
  Event Threat Detection: https://docs.cloud.google.com/security-command-center/docs/concepts-event-threat-detection-overview
  Résultats de vulnérabilité: https://docs.cloud.google.com/security-command-center/docs/concepts-vulnerabilities-findings
  Exposition aux attaques: https://docs.cloud.google.com/security-command-center/docs/attack-exposure-learn
  Posture de sécurité: https://docs.cloud.google.com/security-command-center/docs/security-posture-overview
  Configurer les services: https://docs.cloud.google.com/security-command-center/docs/how-to-configure-security-command-center
  Utiliser la console: https://docs.cloud.google.com/security-command-center/docs/how-to-use-security-command-center
  API REST: https://docs.cloud.google.com/security-command-center/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/scc
  Quotas et limites: https://docs.cloud.google.com/security-command-center/quotas
  Tarifs: https://cloud.google.com/security-command-center/pricing
  Notes de version: https://docs.cloud.google.com/security-command-center/docs/release-notes
---

## Ce que c'est

Le poste central de gestion des risques d'un environnement Google Cloud : il rassemble en un seul flux de **résultats** ce que découvrent des détecteurs de configuration, des détecteurs de menaces et des services partenaires, puis les classe par gravité et par exposition.

- **Quatre domaines.** La **détection de vulnérabilités** — configurations fautives, ressources exposées, identifiants qui fuient, conformité aux référentiels NIST, PCI DSS, HIPAA, CIS. La **détection de menaces** — logiciels malveillants, minage de cryptomonnaie, attaques sur les conteneurs en exécution, dénis de service. La **posture** — un état de sécurité attendu, déployé sur la hiérarchie des ressources, dont on surveille la dérive. Les **cadres de conformité et de sécurité des données**, déployés et audités de la même façon.
- **Résultat.** L'unité de travail : l'enregistrement d'un problème constaté sur une ressource, avec sa gravité, sa catégorie, la ressource concernée, la recommandation de correction et son état (actif, inactif, muet).
- **Trois origines.** Les services **intégrés au produit** (Security Health Analytics, Event Threat Detection, Web Security Scanner, Container Threat Detection, Virtual Machine Threat Detection, Vulnerability Assessment) ; les services **Google Cloud partenaires** qui y déversent leurs constats — [Cloud Armor](#cloud-armor), [Sensitive Data Protection](#sensitive-data-protection), [Artifact Analysis](#artifact-analysis) ; et les **éditeurs tiers** enregistrés sur Cloud Marketplace, comme Snyk ou CrowdStrike.
- **Exposition aux attaques.** Un graphe qui simule les chemins qu'un attaquant pourrait suivre entre les ressources et attribue à chaque résultat un score d'exposition : c'est ce qui permet de traiter d'abord les dix résultats qui comptent au lieu des mille qui existent.
- **Niveaux de service.** **Standard** (et *Standard-legacy*), gratuit, pour la posture et la conformité de base sur Google Cloud. **Premium**, qui ajoute la détection de menaces, les chemins d'attaque, la surveillance de conformité et la posture avancée, activable au projet ou à l'organisation, facturé à l'usage ou par abonnement. Le niveau **Enterprise** [!DECONSEILLE] étend la couverture à AWS et Azure avec les fonctions Google SecOps, mais n'est pas à retenir : les nouveaux déploiements passent par Premium et par [Google Security Operations](#google-security-operations).
- **Activation.** Au niveau d'un projet ou de l'organisation entière ; certains services intégrés n'existent qu'en activation au niveau de l'organisation.
- **Sorties.** Export continu vers [BigQuery](#bigquery) pour l'analyse et la conservation, notifications Pub/Sub pour l'automatisation, API REST et `gcloud scc` pour tout le reste.

> [!TIP]
> Le niveau Standard suffit à repérer les erreurs de configuration les plus coûteuses — bucket public, clé de compte de service ancienne, pare-feu ouvert — et ne coûte rien. C'est le premier réglage à faire sur une organisation qui n'a encore rien.

## À quoi ça sert

- Obtenir en une vue l'état de sécurité de tous les projets d'une organisation, y compris ceux que personne ne regarde plus.
- Hiérarchiser le travail de correction par l'exposition réelle plutôt que par la seule gravité théorique d'une vulnérabilité.
- Surveiller la conformité à un référentiel et produire la preuve attendue par un auditeur, sans campagne manuelle.
- Détecter une compromission en cours : minage sur une VM, conteneur qui lance un shell inattendu, ajout d'un compte à un rôle d'administration.
- Déclencher une remédiation automatique par Pub/Sub — retirer un accès public, isoler une instance, ouvrir un ticket.
- Figer une posture de référence sur un dossier et être averti dès qu'une contrainte y est désactivée.

**À éviter** comme SIEM d'entreprise : Security Command Center regarde Google Cloud, il n'ingère ni les journaux des postes de travail, ni ceux du réseau interne, ni ceux des applications SaaS — c'est le rôle de [Google Security Operations](#google-security-operations), vers lequel les résultats remontent. À éviter aussi comme outil de correction : il constate et recommande, mais n'applique rien — la remédiation se construit avec l'automatisation, les contraintes d'organisation et l'infrastructure déclarative. Enfin, il ne remplace pas l'analyse des images dans la chaîne de livraison, qui se fait plus tôt avec [Artifact Analysis](#artifact-analysis) et [Binary Authorization](#binary-authorization).

## Alternatives en logiciel libre

- **Prowler** : centaines de contrôles de configuration sur Google Cloud, AWS, Azure et Kubernetes, avec correspondance vers CIS, PCI DSS et les autres référentiels — l'équivalent libre le plus direct de Security Health Analytics.
- **Scout Suite** : audit multicloud qui produit un rapport de posture navigable à partir des APIs du fournisseur.
- **Falco** : détection de comportements suspects à l'exécution dans les conteneurs et sur l'hôte, à partir des appels système — le pendant de Container Threat Detection.
- **Trivy** : analyse de vulnérabilités et d'erreurs de configuration sur les images, les dépôts et les manifestes d'infrastructure.
- **Wazuh** : plateforme de surveillance de sécurité avec agents, contrôles de conformité et corrélation d'événements, pour la partie détection continue.
- **Cloud Custodian** : moteur de règles qui, au-delà du constat, applique la correction (fermer un bucket, étiqueter, arrêter une instance).
