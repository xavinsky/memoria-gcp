---
title: Spot VMs
subgroup: Calcul
icon: categories/compute
aka: VM préemptibles
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    ps: {label: Pub/Sub, sub: file de tâches, icon: categories/data-analytics, x: 190, y: 40, w: 170}
    mig: {label: Groupe d'instances géré, sub: recrée les VM, icon: produits/compute-engine, x: 190, y: 210, w: 230}
    meta: {label: Serveur de métadonnées, sub: préavis de préemption, icon: categories/management-tools, x: 430, y: 36, w: 225}
    spot: {label: Spot VMs, sub: capacité excédentaire, icon: categories/compute, focus: true, x: 430, y: 120, w: 200, h: 60}
    gcs: {label: Cloud Storage, sub: points de reprise, icon: produits/cloud-storage, x: 430, y: 216, w: 190}
  flows:
    - {from: ps, to: spot, text: "Chaque instance tire ses unités de travail d'un abonnement Pub/Sub, de sorte qu'une tâche interrompue soit redistribuée"}
    - {from: spot, to: gcs, from_offset: -50, to_offset: -50, text: "Les résultats et les points de reprise sont écrits au fil de l'eau dans un bucket"}
    - {from: meta, to: spot, control: true, text: "La clé de métadonnées preempted passe à TRUE, puis Compute Engine envoie le signal ACPI G2 Soft Off"}
    - {from: spot, to: gcs, from_offset: 50, to_offset: 50, text: "Le script d'arrêt sauvegarde l'état courant pendant la période d'extinction, au mieux 30 secondes"}
    - {from: mig, to: spot, control: true, text: "Le groupe d'instances géré recrée les VM préemptées dès que de la capacité redevient disponible dans la zone"}
docs:
  Page solution: https://cloud.google.com/solutions/spot-vms
  Documentation: https://docs.cloud.google.com/compute/docs/instances/spot
  Modèles de provisionnement: https://docs.cloud.google.com/compute/docs/instances/provisioning-models
  Créer des Spot VM: https://docs.cloud.google.com/compute/docs/instances/create-use-spot
  Groupe d'instances en Spot VM: https://docs.cloud.google.com/compute/docs/instance-groups/create-mig-with-spot-vms
  Voir le prix de préemption: https://docs.cloud.google.com/compute/docs/instances/view-spot-preemption-price
  Arrêt progressif: https://docs.cloud.google.com/compute/docs/instances/graceful-shutdown-overview
  Cycle de vie d'une instance: https://docs.cloud.google.com/compute/docs/instances/instance-lifecycle
  VM Flex-start: https://docs.cloud.google.com/compute/docs/instances/about-flex-start-vms
  VM préemptibles: https://docs.cloud.google.com/compute/docs/instances/preemptible
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances
  Quotas et limites: https://docs.cloud.google.com/compute/resource-usage
  Tarifs: https://cloud.google.com/products/compute/pricing
  Notes de version: https://docs.cloud.google.com/compute/docs/release-notes
---

## Ce que c'est

Un **modèle de provisionnement** de [Compute Engine](#compute-engine), pas un produit séparé : une instance créée avec le modèle `SPOT` occupe de la capacité excédentaire de Compute Engine, à prix fortement réduit, et peut être reprise à tout moment.

- **Remise.** Jusqu'à 91 % du tarif à la demande selon le type de machine, appliquée aussi aux GPU, aux TPU et aux Local SSD attachés. Le prix Spot d'un type de machine ne change pas plus d'une fois par jour et se consulte avant la création, en même temps que le taux de préemption observé dans la zone.
- **Préemption.** Compute Engine reprend la capacité quand il en a besoin. Il écrit d'abord `preempted=TRUE` dans les métadonnées de l'instance, puis envoie un signal *ACPI G2 Soft Off* qui déclenche le script d'arrêt. Le délai entre les deux, le *préavis de préemption*, vaut 0 seconde par défaut. La période d'extinction qui suit est au mieux de 30 secondes, plus courte que pour une instance standard. Passé ce délai, le signal *ACPI G3 Mechanical Off* coupe la machine.
- **Action de fin.** `STOP` (défaut) laisse l'instance en état `TERMINATED`, disques conservés et facturés, redémarrable telle quelle ; `DELETE` la supprime.
- **Sans garantie.** Pas de SLA, pas de durée minimale ni maximale d'exécution, pas de migration à chaud, pas de redémarrage automatique sur incident hôte. La disponibilité dépend de la zone et du moment. Une instance préemptée dans la minute qui suit son démarrage n'est pas facturée, hors licences d'OS premium.
- **Limites.** Incompatible avec la série A4X et avec les instances *bare metal*. Les crédits de l'offre gratuite ne s'y appliquent pas. Des quotas d'allocation `preemptible` distincts peuvent être demandés, notamment pour les GPU.
- **Modèle `PREEMPTIBLE`.** Toujours disponible et facturé aux mêmes prix Spot, mais plafonné à 24 heures d'exécution d'affilée et privé des options récentes ; Google recommande `SPOT` pour les nouvelles charges.
- **Flex-start.** Pour une charge qui ne tolère pas l'interruption mais accepte d'attendre la capacité, le modèle `FLEX_START` réserve un créneau de 10 minutes à 7 jours sans risque de préemption pendant l'exécution.

> [!WARNING]
> Le préavis par défaut étant nul, un script d'arrêt qui met plus de 30 secondes à écrire son état ne finira pas. Sauvegarder en continu — points de reprise réguliers, accusés de réception côté file d'attente — plutôt que tout à l'extinction.

## À quoi ça sert

- Traitements par lots tolérants aux pannes : encodage média, rendu, simulations, tests, calcul scientifique, en particulier au travers de [Batch](#batch), qui accepte le modèle Spot par simple option d'allocation.
- Nœuds de travail d'un cluster qui redistribue lui-même les tâches perdues : files Pub/Sub, ordonnanceurs de jobs, pools de *runners* de CI.
- Entraînement de modèles avec points de reprise fréquents, où la perte de quelques minutes de calcul coûte moins que le plein tarif GPU (voir [Cloud GPUs](#cloud-gpus)).
- Environnements de développement et de recette que l'on peut perdre sans conséquence.
- Absorber un pic de capacité en complément d'un socle d'instances standard, dans un groupe d'instances géré qui mélange les deux.

**À éviter** pour tout ce qui doit rester joignable : serveurs d'état, bases de données, frontaux de production, nœuds de quorum. À éviter aussi pour une charge qui ne tolère pas l'interruption mais que l'on peut décaler dans le temps : le modèle *Flex-start* donne la capacité sans le risque de préemption. Enfin, à éviter pour un besoin de capacité garantie à date : c'est le rôle des réservations et des réservations futures de [Compute Engine](#compute-engine).

## Alternatives en logiciel libre

Le modèle commercial lui-même n'a pas d'équivalent : sur une infrastructure que l'on possède, il n'y a pas de capacité excédentaire à revendre. Ce qui se transpose, c'est la tolérance à l'interruption.

- **Slurm** : préemption de jobs par priorité (`PreemptMode=REQUEUE`), remise en file automatique et *checkpoint/restart* ; c'est la façon classique d'exploiter une capacité reprise à tout moment.
- **Kubernetes** : *PriorityClass* et préemption des pods, `PodDisruptionBudget` et arrêts progressifs, avec un autoscaler de cluster qui recrée les nœuds perdus, exactement comme un groupe d'instances géré.
- **HTCondor** : ordonnanceur conçu dès l'origine pour des machines qui peuvent disparaître (*opportunistic computing*), avec reprise des tâches.
- **Volcano** et **Kueue** : files de travail par lots sur Kubernetes, avec quotas et réadmission des jobs évincés.
- **CRIU** et **DMTCP** : gel et reprise de processus en cours d'exécution, pour sauvegarder un calcul avant l'extinction.
