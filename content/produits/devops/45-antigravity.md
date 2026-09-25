---
title: Antigravity
subgroup: Poste de développement
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: Poste du développeur, x: 10, y: 16, w: 400, h: 268}
    - {label: Projet GCP, x: 440, y: 16, w: 306, h: 268}
  nodes:
    agy: {label: Antigravity, sub: "2.0, CLI, IDE", icon: categories/developer-tools, focus: true, x: 230, y: 110, w: 154, h: 60}
    repo: {label: Dépôt Git local, sub: "code, tests", icon: categories/devops, x: 26, y: 50, w: 180}
    chrome: {label: Chrome piloté, sub: "profil isolé", icon: categories/web-mobile, x: 26, y: 190, w: 180}
    cb: {label: Cloud Build, sub: "intégration continue", icon: categories/devops, x: 458, y: 50, w: 270}
    run: {label: Cloud Run, sub: "service déployé", icon: produits/cloud-run, x: 458, y: 130, w: 270}
    gep: {label: Agent Platform, sub: "modèles Gemini", icon: produits/vertex-ai, x: 458, y: 212, w: 270}
  flows:
    - {from: agy, to: gep, text: "Chaque tour d'agent part vers les modèles Gemini : sur un compte Google personnel, ou sur le projet et la licence Gemini Enterprise déclarés à la connexion."}
    - {from: agy, to: repo, from_offset: -10, text: "L'agent lit et écrit les fichiers du projet, lance les tests dans le bac à sable du terminal et rend un plan, des différentiels et un récapitulatif sous forme d'artefacts."}
    - {from: agy, to: chrome, from_offset: 10, control: true, text: "Le sous-agent navigateur ouvre l'application dans un profil Chrome séparé, clique, lit la page et rapporte captures et enregistrements, dans les limites de la liste d'URL autorisées."}
    - {from: repo, to: cb, text: "Une fois les modifications validées et poussées, le déclencheur Cloud Build reconstruit et teste le dépôt : la chaîne d'intégration reste le juge, pas le poste."}
    - {from: cb, to: run, text: "Cloud Build publie l'image et déploie le service ; l'agent n'a aucun rôle dans cette étape."}
docs:
  Site produit: https://antigravity.google
  Documentation: https://antigravity.google/docs/home
  Antigravity 2.0: https://antigravity.google/docs/overview
  Antigravity CLI: https://antigravity.google/docs/cli/overview
  Installation de la CLI: https://antigravity.google/docs/cli/install
  Référence de la CLI: https://antigravity.google/docs/cli/reference
  Antigravity IDE: https://antigravity.google/docs/ide/overview
  Extensions d'IDE: https://antigravity.google/docs/ide/extensions
  Artefacts: https://antigravity.google/docs/artifacts
  Navigateur: https://antigravity.google/docs/ide/browser
  Permissions de l'agent: https://antigravity.google/docs/permissions
  Bac à sable du terminal: https://antigravity.google/docs/sandbox
  Modèles: https://antigravity.google/docs/models
  Offres et quotas: https://antigravity.google/docs/plans
  SDK: https://antigravity.google/docs/sdk/overview
  Déploiement en entreprise: https://antigravity.google/docs/enterprise
  Outils de développement IA (Gemini Enterprise): https://docs.cloud.google.com/gemini/enterprise/docs/ai-developer-tools-overview
  Réglages administrateur: https://docs.cloud.google.com/gemini/enterprise/docs/ai-developer-tools-settings
  Tarifs: https://antigravity.google/pricing
  Notes de version: https://antigravity.google/changelog
---

## Ce que c'est

Plateforme de développement agentique de Google : plusieurs surfaces — application de bureau, terminal, extensions d'IDE, SDK — qui partagent le même moteur d'agent, le même compte et les mêmes réglages.

- **Antigravity 2.0.** Application de bureau autonome pour macOS, Linux et Windows, indépendante de tout IDE : elle sert de poste de commandement pour lancer, suivre et orchestrer des agents. Les conversations sont groupées en **projets**, qui couvrent au besoin plusieurs dossiers et plusieurs *worktrees* Git, avec réglages et permissions propres à chacun. S'y ajoutent un terminal intégré, un panneau Git (différentiels du dépôt et des éditions de l'agent, indexation, *commit*, *push*), des tâches planifiées déclenchées par horaire, la dictée vocale et *Remote Control*, qui permet de suivre et d'approuver depuis un navigateur une session qui tourne sur le poste.
- **Antigravity CLI.** Interface en mode texte dans le terminal ; le binaire `agy` s'installe par script dans `~/.local/bin` sur macOS et Linux, dans le profil utilisateur sur Windows. Même moteur d'agent et mêmes permissions qu'Antigravity 2.0, avec synchronisation des réglages entre les deux et export d'une conversation de l'un vers l'autre. Connexion par le trousseau du système, boucle OAuth par copier-coller de code en session SSH, identifiants par défaut de l'application (`AGY_ADC_AUTH=true`) ou clé API Gemini quand aucun navigateur n'est disponible. Un mode sans interface sert les exécutions automatisées.
- **Antigravity IDE et extensions d'IDE.** Antigravity IDE est un éditeur complet publié par Google : panneau d'agent, revue des artefacts dans l'éditeur, complétion *Tab* avec suggestions à l'échelle du fichier, saut au point d'édition suivant et ajout automatique des imports. La documentation indique qu'il n'est pas pris en charge pour les déploiements d'entreprise. Pour rester dans son éditeur habituel, des extensions apportent l'agent dans VS Code, Visual Studio, les IDE JetBrains, Zed et Xcode ; sur les trois derniers, la prise en charge entreprise [!PREVERSION] reste limitée.
- **Antigravity SDK.** Cadre Python pour construire ses propres agents sur le même *harness* : outils et *skills* déclarés, sous-agents, politiques de sécurité, points d'entrée de cycle de vie, sortie structurée.
- **Ce que fait l'agent.** Exécution de commandes système, lecture et écriture de fichiers, recherche sur le web, pilotage de Chrome, délégation à des sous-agents qui travaillent en parallèle. Il s'étend par serveurs **MCP**, *skills* décrites dans un fichier `SKILL.md`, règles, greffons, sous-agents personnalisés et *hooks* JSON qui exécutent un script local avant un appel d'outil ou à la fin d'un tour.
- **Artefacts.** L'agent rend son travail sous forme de livrables : plan d'implémentation en Markdown, différentiels de code, diagrammes, images, captures et enregistrements du navigateur, récapitulatif de fin de tâche. Chaque artefact se commente ligne à ligne, et l'agent s'arrête aux jalons pour demander une revue avant de modifier les fichiers — sauf si la politique de revue est réglée sur « toujours continuer ».
- **Navigateur piloté.** Un sous-agent navigateur ouvre les pages dans un **profil Chrome séparé** du profil personnel, agit dessus, capture des images et enregistre des vidéos `webm` versées aux artefacts. Une liste d'URL autorisées et une liste d'interdiction encadrent ce qu'il peut atteindre ; l'outil s'intègre au serveur MCP Chrome DevTools et se coupe entièrement dans les réglages.
- **Permissions et bac à sable.** Chaque opération sensible s'écrit `action(cible)` — `read_file`, `write_file`, `command`… — et passe par trois listes évaluées dans l'ordre **Deny > Ask > Allow**. Trois préréglages : *Default* (commandes autorisées dans le bac à sable, demande au-delà), *Request Review* (demande systématique, accès limité à l'espace de travail) et *Turbo* (aucune demande, système de fichiers entier). Le bac à sable du terminal repose sur les primitives du système — espaces de noms du noyau sous Linux, `sandbox-exec` sous macOS — sans machine virtuelle ni conteneur : il masque ce qui n'est pas monté, bloque `~/.ssh` et les fichiers `.env`, et coupe le réseau hors des domaines approuvés. Sous Windows, ce moteur de permissions ne s'applique pas, et le bac à sable du terminal [!PREVERSION] y est disponible.
- **Modèles.** Le modèle de raisonnement se choisit dans la conversation, où il reste en place d'un message à l'autre ; changé en cours d'exécution, il ne prend effet qu'au tour suivant. Gemini 3.8, 3.7 et 3.6 Flash et Gemini 3.1 Pro sur toutes les offres ; Claude Sonnet 4.6, Claude Opus 4.6 et GPT-OSS-120b sur les offres individuelles seulement, pas en entreprise. La génération d'images passe par Nano Banana 2 et n'est pas paramétrable.
- **Offres et facturation.** Deux voies distinctes. Pour un compte personnel, l'accès est gratuit avec des quotas de base, et les offres Google AI Pro et Ultra élèvent les limites ; les dépassements se paient en **crédits IA** achetés d'avance, consommés au tarif de Gemini Enterprise Agent Platform, avec un réglage « jamais » ou « toujours » pour décider si l'agent bascule dessus. Pour une organisation, l'accès passe par Google Cloud : connexion directe à l'API [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) facturée à la consommation, ou licence Gemini Enterprise (éditions Standard, Plus ou paiement à l'usage) avec quotas inclus, gestion des dépassements et contrôles d'administration. Cette seconde voie exige un compte de facturation Cloud sur facture et l'API `aiplatform.googleapis.com` activée avant l'achat des licences.
- **En entreprise.** Connexion unique avec le compte professionnel, sélecteur de licence, une licence par projet et par emplacement, identité externe possible par fédération d'identité de personnel — *Workforce Identity Federation*, avec Okta par exemple. Trois emplacements — `global`, `us`, `eu` — dont seul `global` fait de la génération d'images. La télémétrie et les échanges avec le modèle sont journalisés dans le projet porteur de la licence ; le code, les prompts et les transcriptions ne servent pas à l'entraînement. VPC Service Controls s'applique à l'API Agent Platform, et la journalisation requête/réponse fournit la trace d'audit. Le rôle `roles/discoveryengine.agentspaceUser` est requis pour accéder aux outils, y compris pour un administrateur.
- **Limites d'usage.** Les quotas ne se comptent pas en nombre de prompts mais en quantité de travail fourni par l'agent : une tâche courte en consomme peu, une tâche longue beaucoup. Les offres Pro et Ultra rechargent leur quota toutes les cinq heures dans la limite d'un plafond hebdomadaire ; les autres comptes sont rechargés à la semaine. Les complétions *Tab* sont illimitées. La documentation annonce que ces limites peuvent être ajustées selon la capacité disponible, et qu'aucune clé ni point de terminaison apportés par l'utilisateur ne permettent de les relever.
- **Place parmi les outils Google.** Les offres individuelles — compte Google personnel, Google AI Pro, Google AI Ultra — passent par Antigravity et Antigravity CLI. Les extensions [Gemini Code Assist](#gemini-code-assist) et Gemini CLI servent les abonnements Standard et Enterprise, qui gardent la personnalisation sur dépôts privés, les citations de sources et l'assistance hors de l'IDE. [Cloud Code](#cloud-code) reste l'extension du cycle conteneur — manifestes Kubernetes, émulateur Cloud Run, skaffold, débogage local — et ne fait pas d'assistance par modèle. Côté Google Cloud, seule l'intégration à Gemini Enterprise est documentée ; le reste du produit est documenté sur `antigravity.google`.

> [!WARNING]
> Le préréglage **Turbo** supprime à la fois le bac à sable et les demandes d'autorisation : l'agent exécute n'importe quelle commande et accède à tout le système de fichiers. À réserver à un dépôt dont on contrôle le contenu, et à régler par projet plutôt que globalement.

## À quoi ça sert

- Confier une tâche à plusieurs étapes sur un dépôt — implémenter une fonctionnalité, migrer un appel d'API, écrire une série de tests — en gardant la main aux jalons grâce au plan d'implémentation et aux différentiels commentables.
- Travailler sur plusieurs chantiers en parallèle : un projet par dépôt ou par *worktree*, des sous-agents qui traitent en arrière-plan les parties indépendantes d'un même problème.
- Itérer sur une interface avec vérification réelle : l'agent recharge la page, clique, capture l'écran et joint l'enregistrement, au lieu d'affirmer que le correctif fonctionne.
- Travailler depuis le terminal, une session SSH ou une machine sans interface graphique avec `agy`, en réutilisant les réglages et permissions du poste.
- Automatiser des vérifications récurrentes par tâches planifiées, ou intégrer l'agent à une chaîne existante par le mode sans interface et les *hooks* JSON.
- Encadrer l'usage à l'échelle d'une organisation : licence Gemini Enterprise, résidence des données en `us` ou `eu`, VPC Service Controls, journalisation dans le projet, rôles IAM.

**À éviter** quand l'organisation a déjà des licences Gemini Code Assist Standard ou Enterprise et compte sur ce qu'elles seules apportent : suggestions alignées sur les dépôts privés, citations de sources, indemnisation contractuelle, assistance dans BigQuery, Cloud Run ou la console. Dans ce cas, rester sur [Gemini Code Assist](#gemini-code-assist) dans son IDE. À éviter aussi pour le cycle conteneur — écrire des manifestes, déboguer un service sur minikube ou sur l'émulateur Cloud Run — qui relève de [Cloud Code](#cloud-code), et pour déployer : un agent sur un poste ne remplace pas [Cloud Build](#cloud-build) et une chaîne d'intégration tracée. Enfin, ce n'est pas un poste de travail infogéré : pour imposer une image, des dépendances et un périmètre réseau identiques à toute l'équipe, c'est [Cloud Workstations](#cloud-workstations) qu'il faut, quitte à y installer la CLI. Deux restrictions à vérifier avant de s'engager : Antigravity IDE n'est pas pris en charge en entreprise, et l'accès est limité à une liste de pays et aux utilisateurs majeurs.

> [!TIP]
> Brancher un agent de codage tiers sur ses identifiants Antigravity est interdit par les conditions d'utilisation et expose à la suspension du compte. Pour piloter Gemini depuis un autre outil, la voie prévue est une clé d'API Gemini ou l'API Agent Platform.

## Alternatives en logiciel libre

- **OpenHands** (MIT) : l'équivalent le plus complet — agents qui lisent et écrivent le dépôt, exécutent des commandes dans un conteneur isolé et pilotent un navigateur, avec un modèle au choix.
- **Aider** (Apache 2.0) : assistant en ligne de commande qui édite le dépôt et valide dans Git, proche de l'esprit de la CLI.
- **OpenCode** (MIT) : agent de codage en interface texte dans le terminal, l'équivalent direct d'`agy` pour les postes sans interface graphique et les sessions SSH.
- **Cline** (Apache 2.0) : agent en extension VS Code, avec séparation du plan et de l'exécution, autorisation par outil et serveurs MCP.
- **Continue** (Apache 2.0) : extension VS Code et JetBrains qui branche complétion, chat et agent sur le modèle de son choix, local ou distant.
- **Goose** (Apache 2.0) : agent de bureau et en ligne de commande, extensible par MCP, pour les tâches qui dépassent l'édition de code.
- **Chrome DevTools MCP** (Apache 2.0, publié par l'équipe Chrome) et **Playwright MCP** (Apache 2.0) : la brique « navigateur piloté » seule, branchable sur n'importe quel agent qui parle MCP.
- **Ollama**, **llama.cpp** et **vLLM** : service local ou interne des modèles ouverts que ces clients appellent, pour une chaîne complète sans envoi de code à l'extérieur.
