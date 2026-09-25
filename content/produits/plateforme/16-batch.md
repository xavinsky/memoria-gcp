---
title: Batch
subgroup: Calcul
icon: categories/compute
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 16, w: 566, h: 268}
  nodes:
    user: {label: Soumission, sub: gcloud batch jobs submit, external: true, x: 10, y: 120, w: 170}
    batch: {label: Batch, sub: "file, planification", icon: categories/compute, focus: true, x: 200, y: 118, w: 170, h: 60}
    log: {label: Cloud Logging, sub: journaux des tâches, icon: categories/observability, x: 200, y: 216, w: 200}
    ar: {label: Artifact Registry, sub: image du conteneur, icon: categories/devops, x: 430, y: 36, w: 200}
    mig: {label: Groupe d'instances géré, sub: VM créées puis détruites, icon: produits/compute-engine, x: 430, y: 118, w: 235, h: 60}
    gcs: {label: Cloud Storage, sub: entrées et sorties, icon: produits/cloud-storage, x: 430, y: 216, w: 190}
  flows:
    - {from: user, to: batch, text: "Le job est soumis en JSON : un groupe de tâches, une suite de runnables et une règle d'allocation des ressources"}
    - {from: batch, to: mig, control: true, text: "Batch crée un groupe d'instances géré régional dimensionné pour les tâches, puis le supprime une fois le job terminé"}
    - {from: ar, to: mig, text: "Chaque tâche exécute un conteneur tiré d'Artifact Registry, ou un script sur l'image d'OS déclarée"}
    - {from: gcs, to: mig, from_offset: -45, to_offset: -45, text: "Les volumes déclarés dans le job sont montés par Cloud Storage FUSE : les tâches lisent leurs entrées comme des fichiers locaux"}
    - {from: mig, to: gcs, from_offset: 45, to_offset: 45, text: "Les sorties de chaque tâche sont réécrites dans le bucket"}
    - {from: mig, to: log, text: "Les journaux des tâches partent vers Cloud Logging, filtrables par identifiant de tâche"}
docs:
  Page produit: https://cloud.google.com/batch
  Documentation: https://docs.cloud.google.com/batch/docs
  Démarrer avec Batch: https://docs.cloud.google.com/batch/docs/get-started
  Créer et exécuter un job: https://docs.cloud.google.com/batch/docs/create-run-job
  Job de base: https://docs.cloud.google.com/batch/docs/create-run-basic-job
  Monter un volume de stockage: https://docs.cloud.google.com/batch/docs/create-run-job-storage
  Job avec GPU: https://docs.cloud.google.com/batch/docs/create-run-job-gpus
  Consommer une réservation: https://docs.cloud.google.com/batch/docs/create-run-job-reservation
  Améliorer l'obtention des ressources: https://docs.cloud.google.com/batch/docs/improve-obtainability-overview
  Réseau: https://docs.cloud.google.com/batch/docs/networking-overview
  Analyser les journaux: https://docs.cloud.google.com/batch/docs/analyze-job-using-logs
  API REST: https://docs.cloud.google.com/batch/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/batch
  APIs et bibliothèques clientes: https://docs.cloud.google.com/batch/docs/apis
  Client Python: https://docs.cloud.google.com/python/docs/reference/batch/latest
  Quotas et limites: https://docs.cloud.google.com/batch/quotas
  Tarifs: https://cloud.google.com/batch/pricing
  Notes de version: https://docs.cloud.google.com/batch/docs/release-notes
---

## Ce que c'est

Service managé de mise en file et d'exécution de traitements par lots sur des ressources Google Cloud. On décrit un travail et les ressources dont il a besoin ; Batch obtient la capacité, met le travail en file, l'exécute, puis rend les machines.

- **Job.** Un programme planifié qui s'exécute jusqu'au bout sans interaction. Un job contient un **groupe de tâches** — un seul par job, nommé `group0` — et l'environnement dans lequel les exécuter.
- **Tâche.** Une exécution de la suite de *runnables* du job. Les tâches d'un même groupe se distinguent par leur index, exposé en variable d'environnement, et s'exécutent en parallèle ou en séquence selon la configuration.
- **Runnable.** Un script ou un conteneur. Un runnable peut être déclaré non critique — un code de retour non nul n'échoue pas la tâche — ou d'arrière-plan, auquel cas la tâche n'attend pas sa fin.
- **Ressources.** Au minimum, les cœurs et la mémoire par tâche, plus éventuellement du disque de démarrage. Chaque job s'exécute en réalité sur un **groupe d'instances géré régional** que Batch crée et supprime lui-même, réparti sur les zones autorisées. Les GPU, les volumes de stockage externes, les Spot VMs et les réservations se déclarent dans la règle d'allocation.
- **Séries de machines acceptées** : usage général C4, C4A, C4D, C3, C3D, E2, N4, N4A, N2D, N2, N1 et T2D ; calcul C2, C2D et H3 ; mémoire M3, M2 et M1 ; accélérateurs A4, A3 Ultra, A3 Mega, A3 High, A2, G4 et G2.
- **Stockage.** Un job peut monter un bucket [Cloud Storage](#cloud-storage) par Cloud Storage FUSE, un partage Filestore ou un disque persistant : les tâches voient des chemins de fichiers, pas une API.
- **Intégrations.** Journaux dans Cloud Logging, métriques de ressources dans Cloud Monitoring, notifications d'état par Pub/Sub, exécution possible depuis Workflows ou Cloud Scheduler. Les outils de bio-informatique `dsub` et Nextflow savent soumettre à Batch.
- **Identités.** Les jobs s'exécutent sous un compte de service — par défaut celui de Compute Engine — qui doit porter au moins le rôle `roles/batch.agentReporter`, et `roles/logging.logWriter` pour journaliser. Un agent de service `gcp-sa-cloudbatch` est créé automatiquement dans le projet.
- **Facturation.** Le service ne coûte rien : on paie uniquement les ressources sous-jacentes, c'est-à-dire les instances, les disques et le réseau consommés pendant l'exécution.

> [!TIP]
> Comme chaque job crée ses propres VM, le mode d'obtention change tout sur le coût : une règle d'allocation en [Spot VMs](#spot-vms), combinée à la flexibilité d'instances qui laisse Batch choisir parmi plusieurs types de machines, réduit à la fois la facture et le risque de manquer de capacité.

## À quoi ça sert

- Traitements par lots classiques : conversion de fichiers, encodage média, rendu, extraction de données, calculs de fin de journée.
- Calcul haute performance : simulations paramétriques, jobs MPI multi-nœuds, analyses génomiques.
- Charges d'apprentissage automatique qui n'ont pas besoin d'une plateforme complète : préparation de données, inférence hors ligne, entraînements courts sur GPU.
- Exécution en parallèle d'un même programme sur des milliers d'index d'entrée, sans écrire la logique de découpage ni de reprise.

**À éviter** pour un enchaînement de tâches hétérogènes avec dépendances, conditions et reprises : c'est le rôle d'un orchestrateur comme [Managed Service for Apache Airflow](#managed-service-for-apache-airflow) ou Workflows, qui peut d'ailleurs déclencher des jobs Batch. À éviter pour du traitement de données distribué qui a son propre moteur : [Dataflow](#dataflow) et [Managed Service for Apache Spark](#managed-service-for-apache-spark) gèrent eux-mêmes le partitionnement et la tolérance aux pannes. À éviter enfin pour une tâche courte déclenchée par un événement, qu'un job [Cloud Run](#cloud-run) traitera sans provisionner de VM.

## Alternatives en logiciel libre

- **Slurm** : l'ordonnanceur de référence en calcul scientifique, avec files, priorités, quotas, tableaux de jobs et dépendances ; l'équivalent le plus complet, mais à administrer.
- **HTCondor** : ordonnancement de très nombreuses tâches indépendantes sur un parc hétérogène, y compris des machines qui peuvent disparaître.
- **OpenPBS** : gestionnaire de files de travail pour clusters HPC, dans la lignée de PBS.
- **Kubernetes** avec **Kueue** ou **Volcano** : objets `Job` et `Indexed Job` pour les tâches parallèles, files d'attente avec quotas et ordonnancement en bande, l'équivalent direct du groupe de tâches de Batch.
- **Argo Workflows** : enchaînements de tâches en conteneurs sur Kubernetes, quand il faut un graphe de dépendances plutôt qu'un simple tableau de tâches.
- **Nextflow** et **Snakemake** : chaînes de traitement scientifiques reproductibles, capables de cibler indifféremment un cluster local ou un service cloud.
- **Dask** et **Ray** : répartition de calculs Python sur un parc de machines, pour les charges que l'on écrit soi-même.
