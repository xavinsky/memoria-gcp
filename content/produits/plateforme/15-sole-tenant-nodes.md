---
title: Sole-tenant nodes
subgroup: Calcul
icon: categories/compute
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    tmpl: {label: Modèle de nœud, sub: type n2-node-80-640, icon: categories/compute, x: 190, y: 36, w: 200}
    grp: {label: Groupe de nœuds, sub: "zonal, redimensionnable", icon: categories/compute, x: 190, y: 126, w: 215}
    vms: {label: Instances de VM, sub: affinité de nœud, icon: produits/compute-engine, x: 190, y: 216, w: 190}
    maint: {label: Règle de maintenance, sub: migration ou redémarrage, icon: categories/management-tools, x: 440, y: 36, w: 215}
    node: {label: Nœud à locataire unique, sub: serveur physique dédié, icon: categories/compute, focus: true, x: 440, y: 118, w: 230, h: 60}
    log: {label: Cloud Logging, sub: ID du serveur physique, icon: categories/observability, x: 440, y: 216, w: 205}
  flows:
    - {from: tmpl, to: grp, text: "Le modèle de nœud fixe le type de nœud et les libellés d'affinité ; ces propriétés sont copiées telles quelles dans chaque nœud créé"}
    - {from: grp, to: node, from_offset: -18, to_offset: -18, text: "Le groupe alloue un serveur physique entier par nœud, en correspondance stricte de un pour un"}
    - {from: vms, to: node, text: "Les VM qui portent le libellé d'affinité correspondant sont placées sur les nœuds du groupe, jusqu'à épuisement des vCPU ou de la mémoire"}
    - {from: node, to: log, text: "Compute Engine journalise l'identifiant du serveur physique où chaque VM est planifiée, de quoi justifier des licences facturées au cœur"}
    - {from: maint, to: node, control: true, text: "La règle de maintenance de l'hôte décide si les VM migrent vers un autre nœud du groupe ou redémarrent sur le même serveur"}
    - {from: grp, to: node, from_offset: 18, to_offset: 18, control: true, text: "L'autoscaler du groupe ajoute ou retire des nœuds selon les VM restant à placer"}
docs:
  Documentation: https://docs.cloud.google.com/compute/docs/nodes/sole-tenant-nodes
  Modèles de nœuds: https://docs.cloud.google.com/compute/docs/nodes/sole-tenancy-node-templates
  Groupes de nœuds: https://docs.cloud.google.com/compute/docs/nodes/sole-tenancy-node-groups
  Provisionner des VM dédiées: https://docs.cloud.google.com/compute/docs/nodes/provisioning-sole-tenant-vms
  Autoscaling des groupes de nœuds: https://docs.cloud.google.com/compute/docs/nodes/autoscaling-node-groups
  Partager un groupe de nœuds: https://docs.cloud.google.com/compute/docs/nodes/share-node-groups
  Licences BYOL: https://docs.cloud.google.com/compute/docs/nodes/bringing-your-own-licenses
  Suivi du serveur physique: https://docs.cloud.google.com/compute/docs/nodes/determining-server-usage
  Surengagement de CPU: https://docs.cloud.google.com/compute/docs/nodes/overcommitting-cpus-sole-tenant-vms
  Contrôle avancé de la maintenance: https://docs.cloud.google.com/compute/docs/nodes/sole-tenancy-advanced-maintenance-control
  Modifier la tenancy d'une VM: https://docs.cloud.google.com/compute/docs/nodes/updating-vm-tenancy
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/sole-tenancy
  API REST (nodeTemplates): https://docs.cloud.google.com/compute/docs/reference/rest/v1/nodeTemplates
  Tarifs: https://cloud.google.com/compute/sole-tenant-pricing
---

## Ce que c'est

Une option de placement de [Compute Engine](#compute-engine) : un **nœud à locataire unique** est un serveur physique dédié à un seul projet, qui n'héberge aucune VM d'un autre client. Chaque nœud correspond à une machine physique, un pour un.

- **Modèle de nœud.** Ressource régionale qui décrit les nœuds à créer : un **type de nœud**, qui fixe le nombre total de vCPU et la mémoire du serveur (`n2-node-80-640` : 80 vCPU, 640 Go), et facultativement des **libellés d'affinité**. Les propriétés du modèle sont copiées de façon immuable dans chaque nœud du groupe.
- **Groupe de nœuds.** Ressource zonale créée à partir d'un modèle, redimensionnable à la main ou par un autoscaler. Il peut rester privé au projet ou être **partagé** avec d'autres projets, voire avec toute l'organisation.
- **Placement des VM.** Une VM ne va sur un nœud dédié que si son type de machine correspond à la série du type de nœud — un nœud `n2` n'accepte que des machines `n2` — et si son **affinité de nœud** désigne le groupe ou un libellé. On remplit ensuite le nœud avec autant de VM, de tailles différentes, que ses vCPU et sa mémoire le permettent. Le **surengagement de CPU** autorise à dépasser le nombre de vCPU physiques sur certaines séries. La tenancy d'une VM existante peut être modifiée après coup.
- **Licences apportées.** La visibilité sur le matériel est le principal intérêt du modèle : Compute Engine journalise dans Cloud Logging l'identifiant du serveur physique où chaque VM s'exécute, ce qui permet de suivre l'usage des cœurs et des processeurs qu'exigent les licences facturées au socket ou au cœur.
- **Maintenance.** Une règle de maintenance de l'hôte, configurable, dit quand la maintenance a lieu et ce que deviennent les VM : migration à chaud vers un autre nœud du même groupe, ou redémarrage sur place pour conserver l'affinité avec un serveur précis. Une migration à chaud peut aussi être déclenchée manuellement.
- **Facturation.** On paie le **nœud entier**, pas les VM qui tournent dessus : la totalité des vCPU et de la mémoire du type de nœud, plus un **supplément de locataire unique de 10 %**. Facturation dès la création, une minute minimum puis à la seconde. Les remises à l'usage soutenu et les engagements flexibles sur la dépense font baisser ce supplément ; les engagements sur ressources ne s'y appliquent pas, seulement aux vCPU et à la mémoire.

> [!WARNING]
> Un nœud est facturé dès sa création, même vide, et les VM qu'il héberge ne le sont pas séparément. Un groupe surdimensionné coûte donc plein tarif pour rien : l'autoscaler du groupe de nœuds est là pour ça.

## À quoi ça sert

- Satisfaire une exigence d'isolation physique : conformité réglementaire, santé, finance, séparation contractuelle des charges.
- Amener ses propres licences (*BYOL*) quand l'éditeur facture au cœur ou au processeur physique et exige un matériel traçable, cas fréquent des environnements Windows Server, SQL Server et Oracle.
- Regrouper volontairement des VM sur le même serveur, pour réduire la latence entre elles ou garantir qu'elles partagent le même sort en cas de panne.
- Charges sensibles au voisinage : jeux, traitements temps réel, tout ce qui souffre du partage de cache et de bande passante mémoire.

**À éviter** quand l'isolation logique suffit : une VM ordinaire est déjà séparée des autres clients par l'hyperviseur, et les nœuds dédiés reviennent nettement plus cher à ressource égale. Pour le seul besoin de chiffrer la mémoire d'une VM en cours d'exécution, les instances *Confidential VM* répondent sans immobiliser un serveur entier. Pour du matériel sans hyperviseur du tout, ce sont les instances *bare metal* de [Compute Engine](#compute-engine), et pour du matériel spécialisé destiné à Oracle, [Bare Metal Solution](#bare-metal-solution).

## Alternatives en logiciel libre

Sur une infrastructure que l'on possède, la question ne se pose pas dans les mêmes termes : les serveurs sont déjà dédiés. Ce qui se transpose, c'est le placement contraint des machines virtuelles sur des hôtes nommés.

- **OpenStack Nova** : agrégats d'hôtes et filtres de planification (`AggregateInstanceExtraSpecsFilter`, `ServerGroupAntiAffinityFilter`) — l'équivalent direct des groupes de nœuds et des libellés d'affinité, avec la même logique de licences suivies par hôte.
- **Proxmox VE** : règles d'affinité et d'anti-affinité entre machines virtuelles et nœuds du cluster, migration à chaud incluse.
- **oVirt** : politiques de placement par cluster et épinglage d'une VM sur un hôte donné, conçues pour les licences facturées au socket.
- **libvirt** et **KVM** : épinglage des vCPU sur des cœurs physiques (`vcpupin`), topologie NUMA exposée à l'invité, pour le contrôle fin du matériel sous une VM.
- **Kubernetes** : `nodeSelector`, taints et tolérances reproduisent le placement sur un parc de nœuds réservé, sans la garantie d'isolation physique.
