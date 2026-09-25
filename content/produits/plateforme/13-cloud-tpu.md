---
title: Cloud TPU
subgroup: Calcul
icon: categories/compute
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    code: {label: Programme JAX, sub: ou PyTorch/XLA, external: true, x: 10, y: 126, w: 150}
    host: {label: VM hôte TPU, sub: compilateur XLA, icon: produits/compute-engine, x: 190, y: 126, w: 190}
    gke: {label: GKE, sub: planifie les pods TPU, icon: produits/gke, x: 430, y: 36, w: 190}
    tpu: {label: Tranche TPU v6e, sub: chips reliés par ICI, icon: categories/ai-machine-learning, focus: true, x: 430, y: 118, w: 200, h: 60}
    gcs: {label: Cloud Storage, sub: "données, points de reprise", icon: produits/cloud-storage, x: 430, y: 216, w: 216}
  flows:
    - {from: code, to: host, text: "Le programme s'exécute sur la VM hôte, qui pilote les chips TPU qui lui sont rattachés"}
    - {from: host, to: tpu, text: "XLA compile le graphe en code machine TPU, puis l'hôte pousse les données dans la file d'entrée des TensorCores"}
    - {from: gcs, to: host, text: "Les données d'entraînement sont lues depuis un bucket Cloud Storage"}
    - {from: tpu, to: gcs, text: "Les points de reprise et les poids du modèle repartent dans le bucket"}
    - {from: gke, to: tpu, control: true, text: "Sur GKE, une tranche devient un pool de nœuds : le planificateur place les pods d'entraînement sur les chips"}
docs:
  Page produit: https://cloud.google.com/tpu
  Documentation: https://docs.cloud.google.com/tpu/docs
  Introduction: https://docs.cloud.google.com/tpu/docs/intro-to-tpu
  Architecture: https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm
  TPU v6e (Trillium): https://docs.cloud.google.com/tpu/docs/v6e
  TPU7x (Ironwood): https://docs.cloud.google.com/tpu/docs/tpu7x
  Planifier ses ressources: https://docs.cloud.google.com/tpu/docs/plan-tpus
  Régions et zones: https://docs.cloud.google.com/tpu/docs/regions-zones
  Multislice: https://docs.cloud.google.com/tpu/docs/multislice-introduction
  Ressources en file d'attente: https://docs.cloud.google.com/tpu/docs/queued-resources
  Calcul avec JAX: https://docs.cloud.google.com/tpu/docs/run-calculation-jax
  Calcul avec PyTorch/XLA: https://docs.cloud.google.com/tpu/docs/run-calculation-pytorch
  TPU dans Compute Engine: https://docs.cloud.google.com/tpu/docs/tpus-in-compute-engine
  TPU dans GKE: https://docs.cloud.google.com/kubernetes-engine/docs/concepts/tpus
  API Cloud TPU (héritée): https://docs.cloud.google.com/tpu/docs/reference/rest
  Quotas et limites: https://docs.cloud.google.com/tpu/docs/quota
  Tarifs: https://cloud.google.com/tpu/pricing
  Notes de version: https://docs.cloud.google.com/tpu/docs/release-notes
---

## Ce que c'est

Les *Tensor Processing Units* sont des circuits intégrés spécialisés conçus par Google pour le calcul matriciel des réseaux de neurones. Un TPU ne remplace pas un processeur généraliste : il exécute uniquement des graphes compilés par **XLA**.

- **Architecture.** Un chip TPU contient un ou plusieurs *TensorCores*, chacun composé d'unités de multiplication matricielle (**MXU**), d'une unité vectorielle et d'une unité scalaire. Une MXU est un tableau systolique de 256 × 256 multiplieurs-accumulateurs sur TPU v6e et TPU7x, de 128 × 128 sur les versions antérieures ; les multiplications prennent des entrées `bfloat16` et accumulent en FP32. Chaque chip embarque sa mémoire à haute bande passante (**HBM**).
- **Tranches et pods.** Un **pod** est un ensemble contigu de TPU reliés par un réseau spécialisé. Une **tranche** (*slice*) est un sous-ensemble de chips d'un même pod reliés par des interconnexions inter-chips (**ICI**), décrite par une **topologie** à deux dimensions (`2x4`) ou trois dimensions (`4x4x8`). Au-delà d'un pod, **Multislice** fait coopérer plusieurs tranches sur le réseau du centre de données.
- **Générations.** **v5e** et **v5p**, puis **v6e** (nom commercial *Trillium*), puis **TPU7x**, première version de la génération *Ironwood*, à deux chiplets par chip — chacun avec son TensorCore, ses SparseCores et 96 Gio de HBM, soit 192 Go et environ 7,37 To/s par chip, exposés comme deux appareils distincts par JAX.
- **Cadre logiciel.** Le code passe obligatoirement par XLA, compilateur juste-à-temps embarqué dans l'image de la VM hôte. Les cadres pris en charge sont **JAX** et **PyTorch/XLA** ; le reste du programme s'exécute sur l'hôte. Les formes des tenseurs doivent être statiques, et les dimensions multiples de 128 (ou au moins de 8) pour éviter le remplissage par des zéros qui gaspille la MXU.
- **Où les consommer.** Par [Compute Engine](#compute-engine), par [GKE](#gke), ou par les jobs d'entraînement et les points de terminaison de [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform). Dans Compute Engine, une tranche à hôte unique *est* une instance de VM, et une tranche multi-hôtes un groupe d'instances géré dont la règle de charge porte la topologie d'accélérateur. L'API Cloud TPU d'origine n'évolue plus : elle ne reçoit que des correctifs, et les générations à partir de TPU7x ne sont accessibles que par Compute Engine ou GKE.
- **Obtention de la capacité.** Les tranches se demandent à la volée, par **ressource en file d'attente** (la demande attend que la capacité se libère), par réservation, en *Flex-start*, ou en Spot pour les charges interruptibles.
- **Facturation.** À la seconde, par chip, selon la génération, la région et le mode d'obtention.

> [!TIP]
> Un programme dominé par des opérations non matricielles — `reshape`, concaténations, branchements fréquents, arithmétique de haute précision — sous-utilisera la MXU. Dans ce cas, un GPU reste plus adapté.

## À quoi ça sert

- Pré-entraîner et affiner de grands modèles dont le calcul est dominé par des produits de matrices, sur des semaines ou des mois.
- Entraîner des modèles à très grands tableaux d'*embeddings*, typiques du classement et de la recommandation, où les SparseCores font la différence.
- Servir de l'inférence à grande échelle pour des modèles déjà compilés par XLA.
- Monter en taille de lot : la HBM embarquée autorise de plus gros lots effectifs que les accélérateurs généralistes.

**À éviter** quand le code contient des opérations personnalisées PyTorch ou JAX dans la boucle d'entraînement, des formes dynamiques ou beaucoup de branchements : [Cloud GPUs](#cloud-gpus) accepte ce code tel quel. À éviter aussi pour prototyper : un CPU suffit tant que le modèle est petit, et le temps de compilation XLA pèse lourd sur des essais courts. Pour un cluster d'accélérateurs à très grande échelle, avec ordonnanceur et surveillance intégrés, passer par [AI Hypercomputer](#ai-hypercomputer).

## Alternatives en logiciel libre

Le silicium n'a pas d'équivalent libre : les TPU n'existent que chez Google. Restent la pile logicielle et la voie matérielle de remplacement.

- **OpenXLA** et **XLA** : le compilateur lui-même est open source, et cible aussi bien CPU et GPU que TPU ; un modèle écrit pour XLA reste portable.
- **JAX** et **PyTorch/XLA** : les deux cadres pris en charge sont libres et s'exécutent sans modification sur GPU.
- **IREE** et **MLIR** : compilation de graphes d'apprentissage automatique vers des cibles matérielles variées, pour qui veut sortir de l'écosystème d'un fournisseur.
- Sur GPU, **DeepSpeed**, **Megatron-LM** et le *FSDP* de PyTorch couvrent le parallélisme de données, de tenseurs et de pipeline qu'une tranche TPU offre nativement.
- **Ray** et **Slurm** pour l'ordonnancement d'un entraînement distribué sur un parc que l'on administre.
