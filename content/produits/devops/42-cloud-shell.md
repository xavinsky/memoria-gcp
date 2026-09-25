---
title: Cloud Shell
subgroup: Poste de développement
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: "Environnement Cloud Shell (géré par Google)", x: 185, y: 16, w: 300, h: 268}
    - {label: Projet GCP, x: 520, y: 16, w: 226, h: 268}
  nodes:
    user: {label: Navigateur, sub: "console Google Cloud", external: true, x: 10, y: 118, w: 165}
    editor: {label: Éditeur Cloud Shell, sub: "Code OSS, Cloud Code", icon: categories/developer-tools, x: 205, y: 40, w: 215}
    shell: {label: Cloud Shell, sub: "VM Debian éphémère", icon: categories/developer-tools, focus: true, x: 205, y: 120, w: 215, h: 60}
    home: {label: Disque persistant, sub: "$HOME, 5 Gio", icon: categories/storage, x: 205, y: 216, w: 215}
    api: {label: APIs Google Cloud, sub: "gcloud, bq, kubectl", icon: categories/management-tools, x: 535, y: 60, w: 195}
    run: {label: Cloud Run, sub: "service déployé", icon: produits/cloud-run, x: 535, y: 180, w: 195}
  flows:
    - {from: user, to: shell, text: "Le développeur ouvre Cloud Shell depuis la console : une VM Debian lui est attribuée pour la durée de la session, hors de ses projets."}
    - {from: user, to: editor, from_offset: -18, text: "Le même onglet bascule vers l'éditeur Cloud Shell, un Code OSS dans le navigateur avec l'extension Cloud Code préinstallée."}
    - {from: shell, to: home, text: "Seul le répertoire personnel est persistant : 5 Gio conservés d'une session à l'autre et partagés par le terminal et l'éditeur."}
    - {from: shell, to: api, control: true, text: "gcloud est déjà authentifié avec le compte connecté à la console et pointé sur le projet actif : aucune clé à installer."}
    - {from: api, to: run, text: "Les commandes créent et pilotent les ressources du projet, ici le déploiement d'un service."}
    - {from: shell, to: user, from_offset: 18, to_offset: 18, text: "L'aperçu web publie un port de la VM (2000 à 65000) derrière un proxy HTTPS réservé au seul utilisateur de la session."}
captures:
  - image: https://docs.cloud.google.com/static/shell/docs/images/cloudshelltutorial.png
    page: https://docs.cloud.google.com/shell/docs/cloud-shell-tutorials/tutorials
    legende: "Cloud Shell en pleine page : l'éditeur, le terminal et un tutoriel interactif dans le panneau de droite"
  - image: https://docs.cloud.google.com/static/shell/docs/images/launch-within-docs.png
    page: https://docs.cloud.google.com/shell/docs/launching-cloud-shell
    legende: "Le terminal Cloud Shell ouvert dans le bas d'une page de documentation, avec la commande d'exemple déjà recopiée"
docs:
  Documentation: https://docs.cloud.google.com/shell/docs
  Démarrage rapide: https://docs.cloud.google.com/shell/docs/quickstart
  Fonctionnement: https://docs.cloud.google.com/shell/docs/how-cloud-shell-works
  Lancer Cloud Shell: https://docs.cloud.google.com/shell/docs/launching-cloud-shell
  Éditeur Cloud Shell: https://docs.cloud.google.com/shell/docs/editor-overview
  Personnaliser l'environnement: https://docs.cloud.google.com/shell/docs/configuring-cloud-shell
  Aperçu web: https://docs.cloud.google.com/shell/docs/using-web-preview
  Réinitialiser la VM: https://docs.cloud.google.com/shell/docs/resetting-cloud-shell
  API REST: https://docs.cloud.google.com/shell/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/cloud-shell
  Quotas et limites: https://docs.cloud.google.com/shell/docs/quotas-limits
  Tarifs: https://cloud.google.com/shell/pricing
  Notes de version: https://docs.cloud.google.com/shell/docs/release-notes
---

## Ce que c'est

Terminal Linux et éditeur de code accessibles depuis la console Google Cloud, sans rien installer. La session tourne sur une VM Compute Engine Debian provisionnée par utilisateur et par session, que Google possède et administre : elle n'apparaît dans aucun projet.

- **VM éphémère.** L'environnement de travail est un conteneur Docker sur cette VM. Après une heure d'inactivité, la session se termine et la VM est détruite ; tout ce qui a été installé hors du répertoire personnel disparaît. L'utilisateur dispose des droits `sudo` et peut donc tout installer — le temps de la session.
- **Répertoire personnel persistant.** 5 Gio de disque persistant montés sur `$HOME`, gratuits, attachés à l'utilisateur et non au projet, conservés entre les sessions et privés. Un mode éphémère, sans disque, démarre plus vite mais ne garde rien. Le volume ne peut pas être agrandi.
- **Outillage préinstallé** : la gcloud CLI et ses outils (`gcloud`, `bq`, `gsutil`), Docker, Git, Mercurial, kubectl, les éditeurs Vim, Emacs et Nano, les outils de construction (Maven, Gradle, Bazel, Make, npm, pip, uv, Helm, Composer), et les langages Java 17, Go, Python 3.12, Node.js LTS, Ruby 3.2, PHP 8.3 et .NET Core. L'image du conteneur est mise à jour chaque semaine.
- **Personnalisation** : un script `.customize_environment` rejoue les installations à chaque démarrage de la VM ; les fichiers de configuration placés dans `$HOME` (`.bashrc`, `.vimrc`) sont conservés. Un mode sans échec permet de réparer un `.bashrc` qui ferme la session à l'ouverture.
- **Éditeur Cloud Shell** : un Code OSS dans le navigateur, avec [Cloud Code](#cloud-code) préinstallé, ouvert sur les mêmes fichiers que le terminal.
- **Authentification** : au premier appel d'API, la session demande l'autorisation d'utiliser les identifiants du compte connecté à la console. Le projet actif de la console est propagé à la configuration `gcloud` et à la variable `GOOGLE_CLOUD_PROJECT`.
- **Aperçu web** : un port entre 2000 et 65000 est exposé en HTTPS par un proxy qui n'accepte que le compte de la session ; l'adresse est celle de l'hôte `PORT-$WEB_HOST` en HTTPS.
- **Limites** : 50 heures d'usage par semaine, sessions plafonnées à 12 heures, sessions non interactives coupées au bout de 40 minutes, région imposée par la proximité. Le service est gratuit.

> [!WARNING]
> Le répertoire personnel est supprimé après 120 jours sans session — un courriel prévient avant. Ce n'est pas un espace de stockage : le code va dans un dépôt Git, les données dans [Cloud Storage](#cloud-storage).

## À quoi ça sert

- Administrer un projet depuis n'importe quel navigateur, avec une gcloud CLI à jour et déjà authentifiée : c'est l'accès d'urgence quand le poste habituel n'est pas là.
- Rejouer les commandes de la documentation et des tutoriels : les blocs de code des pages Google Cloud s'ouvrent directement dans un terminal Cloud Shell.
- Faire découvrir la plateforme, en formation ou en démonstration, sans demander d'installation préalable.
- Prototyper une petite application et la montrer par l'aperçu web, ou la déployer sur Cloud Run en quelques commandes.
- Manipuler un cluster GKE : `gcloud container clusters get-credentials` puis `kubectl`, sans configurer de contexte local.

**À éviter** comme poste de travail quotidien : quota hebdomadaire, session coupée au bout de 12 heures, disque non extensible, aucune machine dimensionnable et aucun accès au VPC d'un projet. Dès que l'usage devient régulier ou qu'il faut atteindre des ressources privées, passer à [Cloud Workstations](#cloud-workstations). À éviter aussi pour l'automatisation : un travail non interactif est arrêté au bout de 40 minutes et relève d'une chaîne d'intégration continue ; les traitements longs et scriptés veulent la [gcloud CLI](#cloud-sdk) installée sur une machine dédiée.

## Alternatives en logiciel libre

- **code-server** : Code OSS servi dans le navigateur depuis une machine que l'on administre ; l'équivalent direct de l'éditeur Cloud Shell.
- **Eclipse Theia** : socle d'IDE web extensible, avec les extensions d'Open VSX — la même famille d'outils que l'éditeur de Google.
- **ttyd** et **Wetty** : un terminal exposé en HTTP ou en WebSocket, pour la seule partie *shell* ; à placer derrière une authentification.
- **Eclipse Che** : espaces de travail conteneurisés sur Kubernetes, terminal et éditeur compris, avec cycle de vie et quotas gérés.
- **JupyterLab** : terminal, éditeur et notebooks dans le navigateur, servis par un serveur que l'on héberge ; **JupyterHub** pour le multi-utilisateur.
- **tmux** sur un petit serveur SSH : la version minimale de la session persistante, sans interface web.
