---
title: Migrate to Containers
subgroup: Migration et hybride
icon: categories/migration
aka: Migrate for Anthos and GKE
deprecie: "Outil en maintenance : CLI seule, correctifs de sécurité uniquement, systèmes testés anciens. Pour un nouveau projet, écrire le Dockerfile et déployer sur [Cloud Run](#cloud-run) ou [GKE](#gke), ou migrer la VM telle quelle avec [Migrate to Virtual Machines](#migrate-to-virtual-machines)."
schema:
  size: [760, 330]
  zones:
    - {label: Sur site ou Compute Engine, x: 6, y: 16, w: 212, h: 120}
    - {label: Poste de migration, x: 6, y: 170, w: 212, h: 144}
    - {label: Projet GCP, x: 236, y: 16, w: 518, h: 298}
  nodes:
    vm: {label: VM source, sub: "Linux, Tomcat, IIS…", external: true, x: 16, y: 48, w: 192}
    m2c: {label: CLI m2c, sub: "plan, Dockerfile, YAML", icon: categories/migration, focus: true, x: 16, y: 226, w: 192, h: 70}
    ar: {label: Artifact Registry, sub: "image du conteneur", icon: categories/devops, x: 276, y: 128, w: 200}
    gke: {label: GKE, sub: "Standard ou Autopilot", icon: produits/gke, x: 538, y: 236, w: 200}
    run: {label: Cloud Run, sub: "charge sans état", icon: produits/cloud-run, x: 538, y: 40, w: 200}
  flows:
    - {from: vm, to: m2c, text: "m2c copy : copie du système de fichiers de la VM par SSH (ou gcloud pour Compute Engine) sur le poste local"}
    - {from: m2c, to: ar, from_side: right, to_side: left, from_offset: -18, text: "m2c analyze puis m2c generate produisent un plan de migration modifiable, puis un Dockerfile, des manifestes Kubernetes et une configuration Skaffold ; l'image construite est poussée dans le registre"}
    - {from: ar, to: gke, to_offset: -14, text: "Skaffold déploie les manifestes sur un cluster GKE, qui tire l'image du registre"}
    - {from: ar, to: run, text: "Variante pour une application sans état : déploiement du même conteneur sur Cloud Run"}
    - {from: m2c, to: gke, from_side: right, to_side: left, from_offset: 18, to_offset: 18, text: "m2c migrate-data copie les fichiers de données de la source dans des volumes persistants du cluster"}
docs:
  Page produit: https://cloud.google.com/products/cloud-migration/containers
  Documentation: https://docs.cloud.google.com/migrate/containers/docs
  Architecture de la CLI: https://docs.cloud.google.com/migrate/containers/docs/m2c-cli/architecture
  Charges et systèmes pris en charge: https://docs.cloud.google.com/migrate/containers/docs/m2c-cli/compatible-components
  Démarrage rapide: https://docs.cloud.google.com/migrate/containers/docs/migrate-vm
  Conteneurs système Linux: https://docs.cloud.google.com/migrate/containers/docs/about-linux-system-containers
  Déploiement sur Cloud Run: https://docs.cloud.google.com/migrate/containers/docs/deploy-run
  Référence CLI (Linux): https://docs.cloud.google.com/migrate/containers/docs/m2c-cli-reference-linux
  Référence CLI (Windows): https://docs.cloud.google.com/migrate/containers/docs/m2c-cli-reference-windows
  Quotas et limites: https://docs.cloud.google.com/migrate/containers/docs/quotas
  Tarifs: https://cloud.google.com/migrate/containers/pricing
  Notes de version de la CLI: https://docs.cloud.google.com/migrate/containers/docs/m2c-cli-relnotes
---

## Ce que c'est

Outil de conteneurisation d'applications qui tournent sur des VM : il extrait l'application et son environnement du système source et produit de quoi la faire tourner en conteneur, sans accès au code source ni réécriture. Il se présente comme une CLI, `m2c`, exécutée sur un poste de travail ; il n'a pas d'interface dans la console.

- **Étapes** : `m2c copy` copie le système de fichiers de la machine source (SSH direct, ou `gcloud` pour une VM Compute Engine) ; `m2c analyze` en tire un **plan de migration** (`config.yaml`) qu'on édite ; `m2c generate` produit les artefacts ; `m2c migrate-data`, facultatif, recopie les données dans des volumes persistants.
- **Artefacts** : un ou plusieurs Dockerfile, des manifestes de déploiement Kubernetes et une configuration Skaffold, à intégrer ensuite dans une chaîne CI/CD pour maintenir l'image.
- **Plugins** par type de charge : **conteneur système Linux** (tout l'espace utilisateur de la VM, relancé par un gestionnaire de services qui démarre les services d'origine), Apache Tomcat, Apache HTTP Server, JBoss et WildFly, IBM WebSphere (traditionnel et Liberty), WordPress, applications Windows IIS. Les plugins Java demandent Java SE 8 ou plus.
- **Cibles** : GKE (Standard, Autopilot, GKE Enterprise) ; Cloud Run pour une charge sans état.
- **Poste de migration** : Linux 64 bits pour les charges Linux, Windows Server 2019 pour IIS, avec l'espace disque nécessaire pour la copie. Par défaut, l'analyse refuse une image dont les couches dépassent 15 Go.
- **Évaluation** : l'aptitude d'une VM à la conteneurisation se mesure avec la CLI mcdc de [Migration Center](#migration-center).
- **Facturation** : l'outil est gratuit ; on paie le cluster GKE ou le service Cloud Run cible.
- **État du produit** : les versions récentes des plugins ne contiennent que des correctifs de vulnérabilités, et la liste des systèmes sources testés s'arrête à RHEL 8, Debian 10, Ubuntu 19.04 et SUSE 15.

## À quoi ça sert

- Sortir d'une VM une application d'un type couvert par un plugin (Tomcat, WebSphere, JBoss, IIS) quand l'équipe d'origine n'est plus là pour la reconstruire.
- Réduire un parc de VM à entretenir en regroupant des applications sur un cluster, avec des images reconstruites par la CI plutôt que des serveurs patchés un à un.

**À éviter** pour une application dont on maîtrise le code : un Dockerfile écrit à la main, construit par [Cloud Build](#cloud-build), donne une image plus petite et plus propre qu'une copie de système de fichiers. Pour une charge qu'on ne veut pas toucher, [Migrate to Virtual Machines](#migrate-to-virtual-machines) la reprend telle quelle sur Compute Engine.

> [!WARNING]
> Un conteneur système Linux embarque tout le système de fichiers de la VM, bibliothèques obsolètes comprises : les failles de l'OS source suivent l'application dans l'image. Faire analyser l'image par [Artifact Analysis](#artifact-analysis) avant la mise en production.

## Alternatives en logiciel libre

- **Konveyor** (projet CNCF) : analyse d'applications Java et .NET en vue de leur modernisation, et **Move2Kube**, qui génère Dockerfile et manifestes Kubernetes à partir d'une application existante.
- **Buildpacks** (Cloud Native Buildpacks, Paketo) : construction d'une image à partir du code source, sans Dockerfile.
- **KubeVirt** : garder la VM telle quelle, mais la faire tourner sur Kubernetes à côté des conteneurs.
- **Skaffold** : l'outil de construction et de déploiement que les artefacts générés utilisent déjà.
