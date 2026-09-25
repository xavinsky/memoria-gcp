---
title: Google Security Operations
subgroup: IAM et sécurité
icon: produits/security-operations
aka: Chronicle
schema:
  size: [760, 320]
  zones:
    - {label: Google SecOps, x: 230, y: 16, w: 518, h: 290}
  nodes:
    src: {label: Sources de journaux, sub: "EDR, pare-feu, cloud", external: true, x: 8, y: 40, w: 200}
    fwd: {label: Forwarder ou agent, sub: "syslog, BindPlane", external: true, x: 8, y: 150, w: 200}
    udm: {label: Modèle de données unifié, sub: "événements normalisés", icon: produits/security-operations, x: 250, y: 40, w: 250}
    secops: {label: Google SecOps, sub: "détection, corrélation", icon: produits/security-operations, focus: true, x: 250, y: 130, w: 250, h: 64}
    search: {label: Recherche UDM, sub: "investigation, graphe", icon: produits/security-operations, x: 250, y: 226, w: 250}
    ti: {label: Threat Intelligence, sub: "Mandiant, IoC", icon: produits/threat-intelligence, x: 520, y: 40, w: 228}
    cases: {label: Cas et playbooks, sub: "réponse automatisée", icon: produits/security-operations, x: 520, y: 160, w: 228}
  flows:
    - {from: src, to: fwd, control: true, text: "Les journaux des équipements, des applications et des autres clouds sont collectés par un forwarder, un agent BindPlane, un connecteur d'API ou un webhook."}
    - {from: fwd, to: udm, text: "L'ingestion normalise chaque enregistrement dans le modèle de données unifié : un analyseur par produit, puis l'enrichissement par le contexte des entités."}
    - {from: udm, to: secops, text: "Les événements normalisés sont indexés et conservés un an par défaut ; le moteur de détection y exécute en continu les règles YARA-L."}
    - {from: ti, to: secops, text: "Les détections gérées par Google et les indicateurs de Mandiant Threat Intelligence sont appliqués rétroactivement à l'historique, pas seulement au flux courant."}
    - {from: secops, to: search, text: "L'analyste part d'une alerte, pivote sur un actif, une adresse IP, un domaine ou une empreinte, et reconstitue la chronologie dans le graphe d'investigation."}
    - {from: secops, to: cases, text: "Les alertes corrélées deviennent des cas ; un playbook enchaîne enrichissement, confinement et notification, avec étape d'approbation quand elle est nécessaire."}
captures:
  - image: https://docs.cloud.google.com/static/chronicle/images/investigation/events-table-and-eventviewer-eventfields.png
    page: https://docs.cloud.google.com/chronicle/docs/investigation/udm-search
    legende: "Résultat d'une recherche UDM : table des événements à gauche, champs de l'événement sélectionné dans la visionneuse à droite"
docs:
  Page produit: https://cloud.google.com/security/products/security-operations
  Documentation: https://docs.cloud.google.com/chronicle/docs
  Vue d'ensemble: https://docs.cloud.google.com/chronicle/docs/secops/secops-overview
  Architecture: https://docs.cloud.google.com/chronicle/docs/secops/secops-architecture
  Offres et modules: https://docs.cloud.google.com/chronicle/docs/secops/secops-packages
  Ingestion: https://docs.cloud.google.com/chronicle/docs/secops/secops-ingestion
  Méthodes d'ingestion: https://docs.cloud.google.com/chronicle/docs/ingestion/ingestion-overview
  Modèle de données unifié: https://docs.cloud.google.com/chronicle/docs/unified-data-model/udm-usage
  Recherche UDM: https://docs.cloud.google.com/chronicle/docs/investigation/udm-search
  Détection: https://docs.cloud.google.com/chronicle/docs/detection
  Langage YARA-L: https://docs.cloud.google.com/chronicle/docs/yara-l/getting-started
  Détections gérées par Google: https://docs.cloud.google.com/chronicle/docs/detection/curated-detections
  Cas et réponse: https://docs.cloud.google.com/chronicle/docs/secops/respond-cases
  Playbooks: https://docs.cloud.google.com/chronicle/docs/soar/respond/working-with-playbooks/case-playbooks
  Google Unified Security: https://docs.cloud.google.com/chronicle/docs/secops/google-unified-security
  Conservation des données: https://docs.cloud.google.com/chronicle/docs/about/data-retention
  API REST: https://docs.cloud.google.com/chronicle/docs/reference/rest
  Notes de version: https://docs.cloud.google.com/chronicle/docs/secops/release-notes
---

## Ce que c'est

La plateforme de centre opérationnel de sécurité de Google : un **SIEM** — collecte, normalisation, détection, recherche sur un historique long — et un **SOAR** — gestion de cas et réponse automatisée par playbooks — dans une même interface. Elle est bâtie sur l'infrastructure de stockage et d'indexation de Google, ce qui explique son modèle : on ingère tout, on garde longtemps, on cherche sans réhydrater.

- **Collecte.** Un **forwarder** léger déployé dans le réseau (syslog, capture de paquets, dépôts de journaux existants), un **collecteur** ou agent BindPlane, un collecteur OpenTelemetry, des **APIs d'ingestion** directes, des connecteurs vers les APIs de services tiers (Microsoft 365, Entra ID, AWS) et des webhooks.
- **Normalisation.** Chaque enregistrement est converti au **modèle de données unifié** (UDM) par un analyseur — plusieurs centaines d'analyseurs standard sont fournis, et on peut en écrire. Les événements sont ensuite enrichis par des données de **contexte d'entité** : qui est cet utilisateur, à quel projet appartient cette VM, quel est le niveau de risque de cet actif.
- **Conservation.** Un an d'historique par défaut, indexé et consultable en ligne : l'enquête sur une compromission ancienne ne demande aucune restauration d'archive, et un nouvel indicateur s'applique rétroactivement à tout l'historique.
- **Détection.** Le moteur exécute en continu des règles **YARA-L** : celles de l'équipe, et les **détections gérées par Google**, maintenues par catégories (menaces cloud, Linux, macOS, Chrome Enterprise, mouvement latéral, UEBA). Les **détections composites** enchaînent plusieurs signaux pour réduire le bruit. L'analyse de risque calcule un score par entité à partir des détections accumulées.
- **Investigation.** La **recherche UDM** interroge les événements et les alertes ; le **balayage de journaux bruts** et les expressions régulières couvrent ce que les analyseurs n'ont pas structuré. Les vues par actif, adresse IP, domaine, empreinte et utilisateur servent de points de pivot, et le graphe d'investigation reconstitue le qui, quoi et quand.
- **Renseignement.** Le produit intègre **Google Threat Intelligence** et les travaux de **Mandiant** : indicateurs priorisés, flux de fusion, catégories de détection dédiées, et une couche de questions en langage naturel avec Gemini.
- **Réponse.** Les alertes deviennent des **cas** : file d'attente, tri, attribution, collaboration, audit. Le **concepteur de playbooks** enchaîne des actions prédéfinies sans code — enrichissement, confinement, notification, approbation — et un environnement de développement intégré permet d'écrire ses propres actions et intégrations.
- **Contrôle d'accès.** Rôles prédéfinis et rôles personnalisés, appliqués par [IAM](#cloud-iam), avec un **RBAC sur les données** qui restreint les classes d'événements visibles par un analyste.
- **Offres.** Le produit se décline en modules (SIEM seul, SIEM et SOAR, renseignement, protection des données) et fait partie de l'offre **Google Unified Security**, qui le regroupe avec [Security Command Center](#security-command-center) et la sécurité navigateur. La facturation dépend du module et se fonde sur le volume ingéré ou sur le nombre d'utilisateurs, selon l'offre.

> [!TIP]
> Le niveau de service Enterprise [!DECONSEILLE] de [Security Command Center](#security-command-center), qui inclut une partie de ces fonctions, n'est pas à retenir : pour un nouveau déploiement, c'est bien Google SecOps qu'on active, et Security Command Center Premium y déverse ses résultats.

## À quoi ça sert

- Centraliser les journaux de sécurité d'un parc hétérogène — postes, pare-feux, identité, SaaS, plusieurs clouds — dans un référentiel unique et normalisé.
- Chercher un indicateur sur un an d'historique en quelques secondes, pour répondre à la question « avons-nous été touchés ? » quand une vulnérabilité est publiée.
- Détecter les attaques connues sans écrire de règles, en activant les détections gérées par Google, puis ajouter les règles propres à l'entreprise.
- Faire remonter les résultats de Security Command Center dans le même flux que le reste, pour que le cloud ne soit pas un silo d'alertes à part.
- Automatiser le tri de premier niveau : enrichir une alerte, interroger l'EDR, vérifier l'utilisateur, fermer les faux positifs évidents et ne présenter à l'analyste que ce qui mérite son temps.
- Mesurer l'activité du centre opérationnel — délai de prise en charge, délai de résolution, couverture MITRE ATT&CK — avec des tableaux de bord intégrés.

**À éviter** pour la supervision applicative et l'exploitation courante : ce n'est pas un outil d'observabilité, les journaux d'application et les métriques de performance n'y ont pas leur place. À éviter aussi comme seul outil de posture cloud : la détection d'une configuration fautive relève de [Security Command Center](#security-command-center), qui alimente ensuite SecOps. Enfin, la plateforme suppose une équipe qui l'exploite : sans personne pour traiter les cas et entretenir les règles, l'investissement ne produit rien.

## Alternatives en logiciel libre

- **Wazuh** : la plateforme libre la plus complète pour la partie SIEM — agents, collecte, règles de corrélation, contrôles de conformité, réponse active.
- **OpenSearch** avec le module **Security Analytics** : ingestion, détection à partir de règles Sigma et tableaux de bord, sur un moteur d'indexation à l'échelle.
- **Sigma** : le format ouvert de règles de détection, traduisible vers plusieurs moteurs — l'équivalent communautaire des détections gérées, bien qu'il ne couvre pas les corrélations les plus fines de YARA-L.
- **Zeek** et **Suricata** : production des journaux réseau et des alertes qui alimentent la chaîne, là où SecOps s'attend à recevoir de la télémétrie déjà normalisée.
- **Velociraptor** : collecte et interrogation d'artefacts sur les postes et les serveurs, pour la partie investigation et réponse sur les terminaux.
- **Shuffle** et **IRIS** : orchestration de playbooks et gestion de cas d'incident, le pendant du volet SOAR.
