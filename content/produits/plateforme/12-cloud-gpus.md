---
title: Cloud GPUs
subgroup: Calcul
icon: categories/compute
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    gcs: {label: Cloud Storage, sub: jeu de données, icon: produits/cloud-storage, x: 190, y: 36, w: 180}
    drv: {label: Pilote NVIDIA et CUDA, sub: image Deep Learning VM, icon: categories/developer-tools, x: 190, y: 122, w: 225}
    quota: {label: Quotas du projet, sub: GPUS_ALL_REGIONS, icon: categories/management-tools, x: 190, y: 210, w: 200}
    gpu: {label: GPU NVIDIA H100, sub: 8 cartes en pass-through, icon: categories/compute, focus: true, x: 440, y: 36, w: 215}
    vm: {label: Instance a3-highgpu, sub: VM d'entraînement, icon: produits/compute-engine, x: 440, y: 118, w: 220, h: 60}
    mon: {label: Cloud Monitoring, sub: utilisation des GPU, icon: categories/observability, x: 440, y: 216, w: 200}
  flows:
    - {from: quota, to: vm, from_side: right, to_side: left, to_offset: 18, control: true, text: "La création échoue tant que le quota d'allocation de GPU du projet n'a pas été relevé dans la région visée"}
    - {from: drv, to: vm, text: "Le pilote NVIDIA et la boîte à outils CUDA sont installés au démarrage, ou déjà présents dans une image Deep Learning VM"}
    - {from: vm, to: gpu, text: "Les cartes sont attachées en pass-through : le système invité pilote directement le GPU et sa mémoire"}
    - {from: gcs, to: vm, to_offset: -18, text: "Le jeu de données d'entraînement est lu depuis un bucket Cloud Storage"}
    - {from: vm, to: mon, text: "L'agent d'observabilité remonte l'utilisation et la mémoire de chaque carte à Cloud Monitoring"}
docs:
  Page produit: https://cloud.google.com/gpu
  Documentation: https://docs.cloud.google.com/compute/docs/gpus/overview
  Types de machines GPU: https://docs.cloud.google.com/compute/docs/gpus
  Instances à GPU: https://docs.cloud.google.com/compute/docs/gpus/about-gpus
  Famille optimisée pour les accélérateurs: https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines
  Créer une VM avec GPU: https://docs.cloud.google.com/compute/docs/gpus/create-vm-with-gpus
  Installer les pilotes: https://docs.cloud.google.com/compute/docs/gpus/install-drivers-gpu
  Pilotes NVIDIA RTX vWS: https://docs.cloud.google.com/compute/docs/gpus/grid-drivers-table
  Régions et zones: https://docs.cloud.google.com/compute/docs/regions-zones/gpu-regions-zones
  Surveiller les GPU: https://docs.cloud.google.com/compute/docs/gpus/monitor-gpus
  GPUDirect et RDMA: https://docs.cloud.google.com/compute/docs/gpus/gpudirect
  Maintenance des hôtes GPU: https://docs.cloud.google.com/compute/docs/gpus/gpu-host-maintenance
  Quotas et limites: https://docs.cloud.google.com/compute/resource-usage
  Tarifs: https://cloud.google.com/products/compute/pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Des accélérateurs NVIDIA attachés à des instances [Compute Engine](#compute-engine). Il n'y a pas de service « GPU » séparé : le GPU est une propriété de l'instance, facturée en plus du type de machine.

- **Deux façons d'obtenir un GPU.** Sur la famille **optimisée pour les accélérateurs**, le modèle et le nombre de cartes sont fixés par le type de machine : séries A4X Max (GB300), A4X (GB200), A4 (B200), A3 Ultra (H200), A3 Mega, A3 High et A3 Edge (H100), A2 Ultra et A2 Standard (A100), G4 (RTX PRO 6000) et G2 (L4). Sur les machines **N1 d'usage général** — hors `f1-micro` et `g1-small` — on attache en revanche soi-même un nombre choisi de T4, P4 ou V100.
- **Mode d'attachement.** Le GPU est présenté en *pass-through* : l'instance contrôle directement la carte et sa mémoire. Les séries G4, G2 et N1 proposent en plus les **NVIDIA RTX Virtual Workstations** (vWS), qui ajoutent une licence de station de travail ; sur G4, les types de machines fractionnaires partagent une carte physique entre plusieurs vGPU.
- **Pilotes.** Rien n'est préinstallé sur une image publique ordinaire : il faut installer le pilote NVIDIA, puis la boîte à outils CUDA si le code en a besoin, chacun dans une version compatible avec le modèle de carte — les générations récentes demandent CUDA 13 ou plus, tandis que CUDA 12 est le dernier à couvrir l'architecture Pascal. Trois chemins : les **images Deep Learning VM**, qui arrivent avec pilote et CUDA ; le script d'installation fourni par Google, appelable depuis un script de démarrage ; l'installation manuelle de la boîte à outils CUDA.
- **Quotas.** Les GPU consomment un quota d'allocation propre, régional et par modèle, plus un quota global `GPUS_ALL_REGIONS`. Un quota `preemptible` distinct existe pour les cartes attachées à des [Spot VMs](#spot-vms). Un projet neuf a un quota nul sur la plupart des modèles : la demande d'augmentation précède la première instance.
- **Disponibilité et maintenance.** Chaque modèle n'existe que dans certaines zones. Les instances à GPU ne migrent pas à chaud comme les autres : lors d'un événement de maintenance, elles sont arrêtées puis redémarrées selon la règle configurée, avec un préavis d'une heure pour les instances standard.
- **Réseau.** Les séries A3 Ultra, A4 et A4X exposent **GPUDirect** et le RDMA sur réseau dédié, pour que les cartes de plusieurs machines communiquent sans passer par la pile réseau de l'hôte — condition d'un entraînement distribué efficace.
- **Facturation.** À la seconde, par carte attachée, en plus du type de machine et des disques. Les remises à l'usage soutenu ne couvrent que les GPU attachés à des N1 ; les autres passent par un engagement ou par le modèle Spot.

> [!WARNING]
> Les modèles T4 et P4 approchent de leur fin de support. Un nouveau projet qui vise l'inférence à petite échelle ou le transcodage a intérêt à partir sur L4 (G2) ou RTX PRO 6000 (G4).

## À quoi ça sert

- Entraîner et affiner des modèles d'apprentissage automatique, seul sur une machine ou en cluster sur plusieurs nœuds A3 ou A4.
- Servir de l'inférence, notamment de grands modèles de langage, sur des cartes à forte mémoire ; L4 et RTX PRO 6000 visent l'inférence à hôte unique.
- Calcul haute performance : simulation, dynamique moléculaire, analyse sismique, finance quantitative.
- Charges graphiques : rendu, transcodage vidéo, stations de travail virtuelles à distance avec les licences vWS.

**À éviter** pour un entraînement à grande échelle sur des centaines d'accélérateurs, où la densité et la fiabilité du cluster comptent plus que la machine : passer par [AI Hypercomputer](#ai-hypercomputer), qui provisionne des blocs de nœuds interconnectés. À éviter aussi pour des charges massivement matricielles qui tiennent dans XLA : [Cloud TPU](#cloud-tpu) y est généralement plus économique. Enfin, pour entraîner un modèle sans gérer d'infrastructure, les jobs d'entraînement de [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) allouent les accélérateurs à la demande.

## Alternatives en logiciel libre

Le matériel n'a évidemment pas d'équivalent libre ; ce qui se remplace, c'est la couche qui expose et partage les cartes.

- **KVM** avec **VFIO** : attachement d'un GPU physique à une machine virtuelle en *pass-through*, exactement le mécanisme utilisé ici.
- **Pilotes noyau GPU ouverts de NVIDIA** (double licence MIT/GPLv2) et **ROCm** pour les cartes AMD : la pile d'exécution sans composant propriétaire côté noyau.
- **NVIDIA GPU Operator** et le **device plugin** Kubernetes : installation des pilotes, découverte et allocation des cartes aux pods, y compris en *time slicing* ou en MIG.
- **Slurm** avec les ressources génériques (`gres/gpu`) : allocation des cartes aux jobs sur un cluster classique.
- **Ray** : répartition de charges Python sur un parc de GPU, pour l'entraînement comme pour l'inférence.
- **DCGM** (NVIDIA Data Center GPU Manager, Apache 2.0) et son exportateur Prometheus : l'équivalent des métriques GPU remontées à Cloud Monitoring.
