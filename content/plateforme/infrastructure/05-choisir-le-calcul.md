---
title: "Choisir le calcul : VMs, GKE, Cloud Run"
subgroup: Calcul et réseau
---

Google classe ses plateformes d'exécution de la plus gérée à la moins gérée : [Cloud Run](#cloud-run) (services, jobs, worker pools, fonctions), puis [GKE](#gke) en mode Autopilot, puis GKE Standard et [Compute Engine](#compute-engine), où le projet administre des machines. Sa recommandation est de **partir du serverless** : à moins d'avoir réellement besoin de Kubernetes, vérifier d'abord que la charge tient dans Cloud Run, et sinon prendre Autopilot, qui est le mode par défaut de GKE (guide *Select a managed container runtime environment* de l'Architecture Center). On ne descend d'un cran que pour une raison précise : un accès aux nœuds, un OS complet, du matériel particulier.

![Arbre de décision : de la forme de la charge à la plateforme de calcul](../../svg/choix-calcul.svg)

La première question porte sur la **forme de la charge** : un service qui répond à des requêtes ou à des événements, un consommateur continu sans requête entrante, une tâche qui se termine, ou un logiciel qui exige une machine entière. [Batch](#batch) crée les VM d'un job et les rend à la fin ; il se distingue d'un job Cloud Run par le matériel (séries de VM, MPI multi-nœuds, GPU lourds) et par la durée.

## Ce que chaque plateforme permet

| Plateforme | Contrôle | État local | GPU | Durée maximale |
|---|---|---|---|---|
| **Compute Engine** (VM, [MIG](#lexterm-groupe-d-instances-gere-mig)) | Total : OS, noyau, type de machine, *bare metal* | Disques persistants ; MIG avec état | Toutes les séries A et G (voir [Cloud GPUs](#cloud-gpus)), TPU à part | Aucune ; [Spot VMs](#spot-vms) reprises à tout moment |
| **GKE Standard** | Nœuds et pools : image, DaemonSets, Pods privilégiés, Arm, Windows | Volumes persistants, StatefulSets | GPU et TPU par pool | Aucune ; Pods réordonnancés aux mises à niveau |
| **GKE Autopilot** | API Kubernetes complète, pas d'accès aux nœuds | Volumes persistants, StatefulSets | GPU et TPU demandés par le Pod | Pods protégés de l'éviction jusqu'à 7 jours |
| **Cloud Run service** | Conteneur, CPU, mémoire, concurrence ; x86 seulement | Aucun : système de fichiers en mémoire ; montages Cloud Storage ou NFS | L4 ou RTX PRO 6000, un par instance | 60 minutes par requête |
| **Cloud Run functions** | Code source et déclencheur ; mêmes réglages qu'un service | Aucun | Oui | 60 minutes en HTTP, 9 minutes en événementiel créé par l'API Cloud Functions v2 |
| **Cloud Run job** | Tâches indexées en parallèle, relances | Aucun | Oui | 168 heures par tâche, 1 heure avec GPU |
| **Cloud Run worker pool** | Consommateur sans URL ni requête entrante | Aucun | Oui | Aucune |
| **Batch** | Job de VM : séries, Spot, réservations, MPI | Disques, Filestore, Cloud Storage FUSE | Séries A et G | 14 jours en exécution, 7 jours en Flex-start |

Limites d'une instance Cloud Run : 8 vCPU, 32 Gio de mémoire, 4 minutes pour démarrer, 1 000 requêtes simultanées. Ce sont les seuils qui envoient une charge vers GKE ; la page *Is my app a good fit for a Cloud Run service?* y ajoute l'absence de système de fichiers local persistant et la capacité à tourner en plusieurs instances simultanées.

## Ce que chaque plateforme coûte

| Plateforme | Mise à zéro | Démarrage à froid | Facturation | Portabilité | Exploitation |
|---|---|---|---|---|---|
| **Compute Engine** | MIG à zéro sur calendrier ou métrique Monitoring externe, jamais sur CPU ni capacité du load balancer | Démarrage d'une VM, puis de l'application | VM à la seconde (1 minute minimum), remises d'usage soutenu et engagements, Spot jusqu'à −91 % | Images importables et exportables | Lourde : OS, correctifs, images, groupes |
| **GKE Standard** | Un pool peut descendre à zéro nœud ; le cluster reste facturé | Pod en secondes sur un nœud libre, minutes s'il faut un nœud | Nœuds au tarif Compute Engine, plus 0,10 $ par cluster et par heure | Manifestes Kubernetes | Pools, versions, capacité, sécurité des nœuds |
| **GKE Autopilot** | Sans Pod, seuls les frais de cluster restent | Minutes si un nœud doit être créé ; capacité de réserve possible | Ressources demandées par Pod ; au nœud pour du matériel imposé | Manifestes Kubernetes | Faible : manifestes et fenêtres de maintenance |
| **Cloud Run service et fonctions** | Par défaut | Secondes ; atténué par les instances minimales et le *startup CPU boost* | vCPU-seconde et Gio-seconde, par tranche de 100 ms, à la requête ou à l'instance | Image standard ; API v1 au format Knative ; Functions Framework pour les fonctions | Minimale |
| **Cloud Run job** | N'existe que pendant l'exécution | Secondes par tâche | Durée d'exécution des tâches | Image standard | Minimale |
| **Cloud Run worker pool** | Nombre d'instances fixé à la main ou par un système externe | Sans objet | À l'instance, qu'elle travaille ou non | Image standard | Faible : dimensionnement à piloter |
| **Batch** | Les VM n'existent que pendant le job | Création des VM à chaque job | VM, disques et réseau seulement ; le service est gratuit | Scripts et conteneurs ; définition de job propre à Batch | Faible |

[App Engine](#app-engine) n'apparaît pas dans ces tableaux : Google recommande Cloud Run pour tout nouveau projet, et les notions d'App Engine (service, version, répartition du trafic) s'y transposent presque terme à terme.

## Questions qui départagent

- **Cloud Run ou GKE Autopilot ?** Cloud Run tant que la charge respecte le contrat de conteneur : HTTP, gRPC ou WebSockets, pas d'état local, 8 vCPU et 32 Gio au plus, x86. Autopilot dès qu'il faut des volumes persistants, des processus de plus de 60 minutes par requête, de l'Arm, des TPU, des opérateurs ou des outils qui parlent à l'API Kubernetes (Helm, CRD), ou un contrôle fin du trafic entre services (NetworkPolicy, Gateway API).
- **Autopilot ou Standard ?** Standard seulement si l'on doit agir sur les nœuds : DaemonSets privilégiés, image de nœud ou noyau particuliers, nœuds Windows, logiciels du Marketplace qui l'exigent. Des demandes de ressources surdimensionnées se paient en nœuds vides en Standard, et en Pods trop chers en Autopilot : dans les deux cas, dimensionner au plus juste.
- **Cloud Run ou VM pour une charge constante ?** Un service qui ne descend jamais à zéro et occupe plusieurs vCPU en permanence revient moins cher en facturation à l'instance, avec un engagement d'utilisation flexible, ou sur un MIG. Cloud Run garde l'avantage de ne rien avoir à patcher.
- **Job Cloud Run ou Batch ?** Job Cloud Run pour des tâches en conteneur de moins de 7 jours, sans exigence de machine. Batch pour choisir la série de VM, consommer une réservation, lancer du MPI multi-nœuds ou dépasser les limites d'une instance Cloud Run. Pour un enchaînement d'étapes avec dépendances, ni l'un ni l'autre : un orchestrateur (voir [Orchestration](#orchestration)).
- **Worker pool ou service à abonnement *push* ?** Un abonnement *push* Pub/Sub vers un service Cloud Run descend à zéro et se facture à la requête. Le worker pool convient aux clients *pull* qui gardent une connexion ouverte : Kafka, RabbitMQ, lecture Pub/Sub à fort débit.
- **Où servir un modèle ?** Voir [Entraîner et servir](#entrainer-et-servir) : Cloud Run sur GPU pour une inférence qui descend à zéro, GKE pour des pools de GPU ou de TPU dimensionnés, Compute Engine pour de très grosses machines.

## Pièges

- **Choisir GKE pour une poignée de services HTTP.** Le frais de cluster, les montées de version et la sécurité des nœuds se paient même quand le cluster est presque vide ; Cloud Run couvre ce besoin sans cluster.
- **Écrire sur le disque d'une instance Cloud Run.** Le système de fichiers est en mémoire : ce qui y est écrit consomme la mémoire de l'instance et disparaît avec elle.
- **Du travail en arrière-plan après la réponse, en facturation à la requête.** Le CPU n'est alloué que pendant le traitement des requêtes : un traitement lancé après la réponse n'avance pas. Le passer en facturation à l'instance, dans un job ou dans un worker pool.
- **Compter sur la mise à zéro d'un MIG piloté par le CPU.** L'autoscaler ne descend pas à zéro sur l'utilisation CPU ni sur la capacité du load balancer ; il faut un calendrier ou une métrique extérieure aux instances, comme la longueur d'une file.
- **Des Spot VMs pour un service joignable.** Préavis nul par défaut, 30 secondes au mieux pour s'arrêter : les réserver aux charges qui reprennent d'un point de sauvegarde (voir [Spot VMs](#spot-vms)).
- **Une image multi-architecture sans `linux/amd64`.** Cloud Run exige cette entrée dans le manifeste ; une image construite seulement pour Arm sur un poste de développement ne se déploie pas.
- **Laisser le délai de requête à 5 minutes.** C'est la valeur par défaut d'un service Cloud Run ; un export ou un appel à un modèle plus long est coupé sans erreur applicative. Le relever, ou passer en job.

## Alternatives en logiciel libre

- **Kubernetes** (Apache 2.0) : la même API que GKE, avec le plan de contrôle et les nœuds à exploiter soi-même ; c'est le socle commun qui rend une charge portable entre GKE et un autre environnement.
- **Knative** (Apache 2.0) : services, révisions, répartition du trafic et mise à zéro au-dessus de Kubernetes, le modèle que reprend Cloud Run.
- **KEDA** (Apache 2.0) : mise à l'échelle de charges Kubernetes sur la longueur d'une file ou d'un sujet, jusqu'à zéro ; l'équivalent de l'autoscaling des worker pools et des MIG sur file.
- **Fission** (Apache 2.0) : fonctions déployées depuis le code source sur Kubernetes, pour la part *Cloud Run functions*.
- **OpenStack** (Apache 2.0) : Nova pour les VM, avec images, groupes et autoscaling par Heat ; l'équivalent le plus complet de Compute Engine, lourd à exploiter.
- **Apache CloudStack** (Apache 2.0) : gestion de parcs de VM avec API cloud, plus simple à installer qu'OpenStack.
- **Slurm** (GPL v2) : files de jobs, tableaux de tâches et MPI sur un parc de machines, le terrain de Batch.
