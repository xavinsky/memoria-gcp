---
title: AI Hypercomputer
subgroup: Calcul
icon: produits/ai-hypercomputer
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    res: {label: Réservation future, sub: blocs de capacité, icon: categories/management-tools, x: 190, y: 36, w: 200}
    cd: {label: Cluster Director, sub: Slurm managé, icon: categories/compute, x: 190, y: 126, w: 190}
    gke: {label: GKE, sub: pods d'entraînement, icon: produits/gke, x: 190, y: 216, w: 190}
    gcs: {label: Cloud Storage, sub: jeux de données, icon: produits/cloud-storage, x: 430, y: 36, w: 185}
    cluster: {label: AI Hypercomputer, sub: "A4, TPU, réseau RDMA", icon: produits/ai-hypercomputer, focus: true, x: 430, y: 118, w: 215, h: 60}
    lustre: {label: Managed Lustre, sub: système de fichiers, icon: categories/storage, x: 430, y: 216, w: 195}
  flows:
    - {from: res, to: cluster, to_offset: -18, text: "La capacité est obtenue par réservation future ou par Dynamic Workload Scheduler, qui provisionne d'un seul tenant un bloc de nœuds interconnectés"}
    - {from: cd, to: cluster, control: true, text: "Cluster Director déploie le cluster, surveille la santé des nœuds et remplace automatiquement ceux qui tombent"}
    - {from: gke, to: cluster, to_offset: 18, text: "Pour une charge conteneurisée, GKE place les pods sur les nœuds accélérés en tenant compte de la topologie"}
    - {from: gcs, to: cluster, from_offset: -50, to_offset: -50, text: "Les jeux de données d'entraînement sont lus depuis Cloud Storage"}
    - {from: cluster, to: lustre, text: "Les nœuds montent Managed Lustre en POSIX pour absorber les écritures de points de reprise sans goulot d'entrée-sortie"}
    - {from: cluster, to: gcs, from_offset: 50, to_offset: 50, text: "Poids du modèle, journaux et mesures de goodput repartent dans Cloud Storage"}
docs:
  Page produit: https://cloud.google.com/ai-infrastructure
  Documentation: https://docs.cloud.google.com/ai-hypercomputer/docs
  Vue d'ensemble: https://docs.cloud.google.com/ai-hypercomputer/docs/overview
  Choisir son infrastructure: https://docs.cloud.google.com/ai-hypercomputer/docs/choose-infrastructure
  Choisir sa plateforme: https://docs.cloud.google.com/ai-hypercomputer/docs/choose-platform
  Modèles de consommation: https://docs.cloud.google.com/ai-hypercomputer/docs/consumption-models
  Capacités des clusters: https://docs.cloud.google.com/ai-hypercomputer/docs/cluster-capabilities
  Surveillance: https://docs.cloud.google.com/ai-hypercomputer/docs/monitor
  Cluster Director: https://docs.cloud.google.com/cluster-director/docs/overview
  Cluster Toolkit: https://docs.cloud.google.com/cluster-toolkit/docs
  Managed Lustre: https://docs.cloud.google.com/managed-lustre/docs/overview
  Réservations futures: https://docs.cloud.google.com/compute/docs/instances/future-reservations-overview
  Machines optimisées pour les accélérateurs: https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines
  Tarifs: https://cloud.google.com/products/compute/pricing
---

## Ce que c'est

Le portefeuille d'infrastructure d'IA de Google Cloud, présenté comme un système unique plutôt que comme une liste de produits : le matériel accéléré, le logiciel d'orchestration et les modes d'obtention de la capacité sont conçus ensemble, pour maximiser le *goodput* — la part du temps d'accélérateur effectivement consacrée au calcul utile.

- **Infrastructure optimisée.** Accélérateurs [Cloud GPUs](#cloud-gpus) et [Cloud TPU](#cloud-tpu), réseau à haut débit avec RDMA et GPUDirect, stockage à fort débit. Les GPU sont classés selon la façon dont leur cycle de vie est géré : **GPU généraux**, administrés comme des unités de calcul indépendantes avec maintenance asynchrone et réparation automatique des nœuds, et **GPU en cluster**, gérés comme un seul système fortement couplé, avec maintenance synchronisée, surveillance matérielle et remplacement proactif des nœuds défaillants.
- **Logiciel ouvert.** Versions optimisées de PyTorch, JAX et TensorFlow, et trois façons de déployer : [GKE](#gke) pour du conteneur à l'échelle, **Slurm** au travers de **Cluster Director**, et les plans de déploiement du **Cluster Toolkit**.
- **Cluster Director.** Plan de contrôle unifié, avec son API et son interface dans la console, qui déploie et redimensionne un cluster complet — calcul, réseau, stockage —, fournit un environnement Slurm managé, place les nœuds en tenant compte de la topologie pour réduire la latence, se répare tout seul et expose un tableau de bord de santé et de performance.
- **Modes d'obtention.** Selon la charge : **à la demande**, **Spot**, **Flex-start**, **réservations standard**, et pour les GPU en cluster les **réservations futures** — en blocs de capacité ou en *mode calendrier* — que le **Dynamic Workload Scheduler** provisionne de manière atomique : soit le bloc entier de nœuds interconnectés est obtenu, soit rien.
- **Stockage.** Les services à haut débit sont considérés comme partie du système : [Managed Lustre](#managed-lustre) pour un système de fichiers parallèle POSIX, et le mode rapide de [Cloud Storage](#cloud-storage) pour les jeux de données et les points de reprise.
- **Facturation.** Il n'y a pas de tarif « AI Hypercomputer » : on paie les ressources sous-jacentes — instances accélérées, réseau, stockage — selon le mode d'obtention retenu.

## À quoi ça sert

- Pré-entraîner un modèle de fondation sur des centaines ou des milliers d'accélérateurs, avec un réseau et un placement pensés pour le parallélisme.
- Affiner un grand modèle sur une capacité réservée à date, sans négocier zone par zone.
- Servir de l'inférence générative à grande échelle, avec mise à l'échelle automatique et remplacement des nœuds en panne.
- Calcul haute performance classique — simulation, découverte de médicaments, analyse de risque — sur un cluster Slurm que l'on n'administre pas.

**À éviter** pour quelques VM à GPU : monter un cluster n'a d'intérêt qu'à partir du moment où la topologie, la maintenance synchronisée et l'obtention de capacité deviennent des problèmes. Une instance [Compute Engine](#compute-engine) avec ses cartes attachées suffit pour un poste de recherche, un essai ou une inférence à hôte unique. À éviter aussi pour un simple traitement par lots parallèle sans couplage entre les tâches : [Batch](#batch) fait ce travail sans cluster persistant.

## Alternatives en logiciel libre

- **Slurm** : l'ordonnanceur que Cluster Director expose lui-même, en version managée ; sur un parc que l'on administre, il reste la référence pour les files, les réservations et le placement topologique.
- **Kubernetes** avec **Kueue**, **Volcano** et le *Training Operator* de Kubeflow : files de travail par lots, ordonnancement en bande (*gang scheduling*) et jobs d'entraînement distribués, l'équivalent du chemin GKE.
- **Ray** : cadre d'exécution distribué pour l'entraînement, l'ajustement d'hyperparamètres et l'inférence, avec sa propre gestion de parc d'accélérateurs.
- **OpenHPC** et **Warewulf** : distribution et provisionnement de nœuds pour un cluster de calcul, la partie que Cluster Toolkit automatise ici.
- **NCCL** et **RCCL** : bibliothèques de communication collective entre accélérateurs, socle de tout entraînement distribué, libres et utilisées telles quelles par Google Cloud.
- **Lustre** : le système de fichiers parallèle derrière Managed Lustre, déployable soi-même ; **Ceph** couvre le même besoin avec un modèle différent.
- **Determined** : plateforme d'entraînement distribué avec ordonnancement, suivi d'expériences et reprise sur incident.
