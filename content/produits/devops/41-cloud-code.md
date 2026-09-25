---
title: Cloud Code
subgroup: Poste de développement
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: Poste du développeur, x: 10, y: 16, w: 230, h: 268}
    - {label: Projet GCP, x: 270, y: 16, w: 476, h: 268}
  nodes:
    ide: {label: Cloud Code, sub: "VS Code, JetBrains", icon: categories/developer-tools, focus: true, x: 28, y: 60, w: 195, h: 60}
    local: {label: Exécution locale, sub: "minikube, émulateur", icon: categories/containers, x: 28, y: 190, w: 195}
    ar: {label: Artifact Registry, sub: "images de conteneur", icon: categories/devops, x: 290, y: 120, w: 195}
    run: {label: Cloud Run, sub: "service déployé", icon: produits/cloud-run, x: 540, y: 40, w: 195}
    gke: {label: GKE, sub: "cluster Kubernetes", icon: produits/gke, x: 540, y: 210, w: 195}
    logs: {label: Cloud Logging, sub: "journaux du service", icon: categories/observability, x: 290, y: 220, w: 195}
  flows:
    - {from: ide, to: local, control: true, text: "L'extension lance d'abord l'application sur minikube ou sur l'émulateur Cloud Run, avec reconstruction continue et débogage pas à pas."}
    - {from: ide, to: ar, text: "Au déploiement, skaffold ou les buildpacks construisent l'image depuis l'IDE et la poussent dans Artifact Registry."}
    - {from: ar, to: run, from_offset: -12, text: "Cloud Code crée ou met à jour le service Cloud Run à partir de l'image publiée, puis affiche son URL."}
    - {from: ar, to: gke, from_offset: 12, text: "La même image part sur un cluster GKE, décrite par les manifestes et le skaffold.yaml du dépôt."}
    - {from: run, to: logs, from_side: left, to_side: right, to_offset: -12, text: "L'explorateur de services rapatrie dans l'IDE les journaux du service déployé."}
    - {from: gke, to: logs, to_offset: 12, text: "Le panneau Kubernetes fait de même pour les pods du contexte kubectl actif, avec accès à un terminal dans le conteneur."}
captures:
  - image: https://docs.cloud.google.com/static/code/docs/vscode/images/vscode-describe-resource.png
    page: https://docs.cloud.google.com/code/docs/vscode/k8s-overview
    legende: "L'explorateur Kubernetes de Cloud Code dans VS Code : ressources du cluster actif et description d'un service dans le terminal"
  - image: https://docs.cloud.google.com/static/code/docs/vscode/images/quickstart-debug-breakpoints.png
    page: https://docs.cloud.google.com/code/docs/vscode/deploy-kubernetes-app
    legende: "Débogage d'une application déployée sur Kubernetes : point d'arrêt, variables et pile d'appels dans VS Code"
docs:
  Page produit: https://cloud.google.com/code
  Documentation: https://docs.cloud.google.com/code/docs
  Cloud Code pour VS Code: https://docs.cloud.google.com/code/docs/vscode/overview
  Cloud Code pour IntelliJ: https://docs.cloud.google.com/code/docs/intellij/overview
  Installation (VS Code): https://docs.cloud.google.com/code/docs/vscode/install
  Installation (JetBrains): https://docs.cloud.google.com/code/docs/intellij/install
  Développer sur Kubernetes: https://docs.cloud.google.com/code/docs/vscode/k8s-overview
  Développer sur Cloud Run: https://docs.cloud.google.com/code/docs/vscode/cloud-run-overview
  Paramètres de l'extension: https://docs.cloud.google.com/code/docs/vscode/configuring-settings
  Référence: https://docs.cloud.google.com/code/docs/vscode/reference
  Cloud Code dans Cloud Shell: https://docs.cloud.google.com/code/docs/shell
  Gouvernance des données: https://docs.cloud.google.com/code/docs/cloud-code-gemini-code-assist-data-governance
  Ressources et notes de version: https://docs.cloud.google.com/code/docs/vscode/resources
---

## Ce que c'est

Extension d'IDE qui amène le cycle complet d'une application conteneurisée — création, exécution locale, débogage, déploiement, journaux — dans l'éditeur, sans passer par la console.

- **IDE pris en charge** : VS Code, IntelliJ IDEA et les autres IDE JetBrains (support limité pour Android Studio). L'extension est préinstallée dans l'éditeur Cloud Shell et dans les images de base de [Cloud Workstations](#cloud-workstations).
- **Langages** : Go, Java, Node.js, Python et .NET Core, avec des applications d'exemple prêtes à exécuter.
- **Kubernetes** : modèles d'application, édition assistée des YAML (complétion et validation des schémas), exploration des clusters et des ressources, ouverture d'un terminal dans un pod, lecture des journaux. Le cycle build-déploiement s'appuie sur **skaffold**, **kubectl** et **minikube** ; les modules skaffold permettent de ne reconstruire qu'une partie de l'application.
- **Cloud Run** : création d'un service à partir d'un modèle, exécution et débogage en local sur un **émulateur Cloud Run**, déploiement, explorateur de services et journaux.
- **Images de conteneur** : construction sans Dockerfile grâce aux *buildpacks* Google Cloud ; cibles Arm, x86 ou mixtes.
- **Services connectés** : Secret Manager (créer, lire, référencer un secret sans le mettre dans le dépôt), navigateur des APIs Google Cloud et des bibliothèques clientes, gestion des VM Compute Engine, intégration Migrate to Containers pour conteneuriser une application Linux existante.
- **Authentification** : l'extension réutilise les identifiants de la [gcloud CLI](#cloud-sdk) ; le projet actif est affiché dans la barre d'état.
- **Assistance IA** : [Gemini Code Assist](#gemini-code-assist) est un greffon distinct, à installer et à activer séparément.
- **Facturation** : l'extension est gratuite ; seules les ressources déployées sont facturées.

> [!TIP]
> Le développement local (minikube ou émulateur Cloud Run) donne la boucle de retour la plus courte et ne consomme rien dans le projet : garder le déploiement distant pour la vérification, pas pour l'itération.

## À quoi ça sert

- Itérer sur une application GKE ou Cloud Run sans sortir de l'IDE : modifier, reconstruire, redéployer et lire les journaux dans la même fenêtre.
- Déboguer pas à pas un conteneur, local ou distant, avec les points d'arrêt et l'inspection de variables de l'IDE.
- Écrire des manifestes Kubernetes et des `skaffold.yaml` avec complétion et validation, au lieu de les corriger après un `kubectl apply` raté.
- Démarrer un projet depuis un modèle déjà gréé (Dockerfile ou buildpacks, manifestes, configuration skaffold).
- Donner à toute l'équipe la même chaîne de développement, en préinstallant l'extension dans une image [Cloud Workstations](#cloud-workstations).

**À éviter** comme outil de déploiement en production : un déploiement depuis un poste n'est ni tracé ni reproductible, il revient à une chaîne d'intégration continue. À éviter aussi pour piloter l'infrastructure — réseaux, bases, IAM : cela relève de la [gcloud CLI](#cloud-sdk) ou d'un outil d'infrastructure as code. Pour une intervention ponctuelle depuis n'importe quel navigateur, [Cloud Shell](#cloud-shell) embarque déjà le même éditeur.

## Alternatives en logiciel libre

- **skaffold** (Apache 2.0, développé par Google) : le moteur de build et de déploiement continu que Cloud Code pilote ; utilisable seul en ligne de commande.
- **Tilt** et **DevSpace** : boucles de développement sur Kubernetes avec synchronisation de fichiers et redéploiement à chaud, l'équivalent du mode « développement continu ».
- **Okteto CLI** : exécution d'un service directement dans le cluster, avec synchronisation du code depuis le poste.
- **vscode-kubernetes-tools** et **kubectl** : exploration des clusters et édition des manifestes dans VS Code, sans la partie Cloud Run.
- **minikube** et **kind** : clusters Kubernetes locaux — minikube est déjà ce que Cloud Code utilise.
- **Knative** : le projet dont Cloud Run reprend le modèle ; permet de rejouer localement, sur un cluster, une application écrite pour Cloud Run.
