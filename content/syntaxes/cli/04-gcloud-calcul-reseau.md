---
title: "gcloud : calcul et réseau"
subgroup: gcloud
type: syntax
---

Les ressources zonales demandent `--zone`, les régionales `--region` ; `gcloud config set compute/zone ZONE` et `compute/region REGION` évitent de les répéter.

### VM Compute Engine

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer une VM | `gcloud compute instances create VM --zone=ZONE --machine-type=e2-standard-4 --image-family=debian-12 --image-project=debian-cloud --subnet=SUBNET --no-address` | VM sans IP publique, sortie Internet par [Cloud NAT](#cloud-nat) ; `--boot-disk-size=50GB` pour agrandir le disque |
| VM avec son propre compte de service | `... --service-account=SA@PROJECT_ID.iam.gserviceaccount.com --scopes=cloud-platform` | Droits fixés par les rôles IAM du compte ; *scope* `cloud-platform` pour ne pas limiter en plus par les *scopes* |
| VM Spot | `... --provisioning-model=SPOT --instance-termination-action=STOP` | Prix réduit, arrêt possible à tout moment ; `DELETE` pour supprimer au lieu d'arrêter |
| VM à durée limitée | `... --max-run-duration=4h --instance-termination-action=DELETE` | Arrêt ou suppression automatique après la durée, comptée depuis le dernier démarrage |
| Script de démarrage | `... --metadata-from-file=startup-script=init.sh` | Exécuté en root à chaque démarrage |
| Étiquettes réseau et labels | `... --tags=web,ssh-iap --labels=env=dev,equipe=data` | *Tags* : cibles des règles de pare-feu ; labels : tri et facturation |
| VM sécurisée au démarrage | `... --shielded-secure-boot` | Démarrage sécurisé activé ; vTPM et contrôle d'intégrité le sont par défaut sur les images compatibles |
| Arrêter, démarrer | `gcloud compute instances stop VM --zone=ZONE` / `start` | VM arrêtée : plus de facturation du calcul, les disques restent facturés |
| Supprimer | `gcloud compute instances delete VM --zone=ZONE --keep-disks=boot` | Par défaut le disque de démarrage est supprimé avec la VM |
| Changer de type de machine | `gcloud compute instances set-machine-type VM --zone=ZONE --machine-type=e2-standard-8` | VM arrêtée au préalable |
| Changer le compte de service | `gcloud compute instances set-service-account VM --zone=ZONE --service-account=SA@PROJECT_ID.iam.gserviceaccount.com --scopes=cloud-platform` | VM arrêtée au préalable |
| IP interne d'une VM | `gcloud compute instances describe VM --zone=ZONE --format="value(networkInterfaces[0].networkIP)"` | Adresse seule, pour un script |
| VM en cours d'exécution d'une région | `gcloud compute instances list --filter="status=RUNNING AND zone~europe-west1"` | Nom, zone, type, IP |
| SSH par IAP, sans IP publique | `gcloud compute ssh VM --zone=ZONE --tunnel-through-iap` | Tunnel par [Identity-Aware Proxy](#identity-aware-proxy) ; exige `roles/iap.tunnelResourceAccessor` et une règle de pare-feu depuis `35.235.240.0/20` sur `tcp:22` |
| Commande à distance | `gcloud compute ssh VM --zone=ZONE --tunnel-through-iap --command="sudo journalctl -u app -n 50"` | Sortie de la commande, sans session interactive |
| Copier des fichiers | `gcloud compute scp fichier.txt VM:~/ --zone=ZONE --tunnel-through-iap` | `--recurse` pour un dossier |
| Ouvrir un port distant en local | `gcloud compute start-iap-tunnel VM 5432 --local-host-port=localhost:5432 --zone=ZONE` | Base de données ou console web de la VM accessibles sur le poste |

### Modèles d'instance et groupes gérés (MIG)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un modèle d'instance | `gcloud compute instance-templates create TPL-v1 --machine-type=e2-standard-2 --image-family=debian-12 --image-project=debian-cloud --region=REGION --subnet=SUBNET --no-address --metadata-from-file=startup-script=init.sh` | Mêmes options que `instances create` ; un modèle ne se modifie pas, on en crée un nouveau |
| Modèle régional | `... --instance-template-region=REGION` | Modèle rattaché à une région plutôt que global |
| Créer un MIG régional | `gcloud compute instance-groups managed create MIG --template=TPL-v1 --size=3 --region=REGION` | VM réparties sur plusieurs zones de la région |
| Réparation automatique | `... --health-check=HC --initial-delay=300` | VM recréée si le contrôle d'état échoue, après le délai de démarrage |
| Mise à l'échelle automatique | `gcloud compute instance-groups managed set-autoscaling MIG --region=REGION --min-num-replicas=2 --max-num-replicas=10 --target-cpu-utilization=0.6` | Ajoute ou retire des VM pour tenir 60 % de CPU en moyenne |
| Port nommé pour un load balancer | `gcloud compute instance-groups managed set-named-ports MIG --region=REGION --named-ports=http:8080` | Le service de backend vise le nom `http` |
| Mise à jour progressive | `gcloud compute instance-groups managed rolling-action start-update MIG --region=REGION --version=template=TPL-v2 --max-surge=3 --max-unavailable=0` | VM remplacées par lots, sans perte de capacité |
| Canary | `... --version=template=TPL-v1 --canary-version=template=TPL-v2,target-size=10%` | 10 % des VM sur le nouveau modèle |
| Recréer toutes les VM | `gcloud compute instance-groups managed rolling-action replace MIG --region=REGION` | Même modèle, VM neuves |
| Redimensionner | `gcloud compute instance-groups managed resize MIG --region=REGION --size=5` | Sans *autoscaler* actif |
| État des VM du groupe | `gcloud compute instance-groups managed list-instances MIG --region=REGION` | Statut, action en cours, version du modèle |

### Disques et instantanés

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un disque | `gcloud compute disks create DISK --zone=ZONE --size=200GB --type=pd-balanced` | `hyperdisk-balanced`, `pd-ssd`... selon le type de machine |
| Disque régional | `gcloud compute disks create DISK --region=REGION --replica-zones=ZONE_A,ZONE_B --size=200GB --type=pd-balanced` | Réplication synchrone entre deux zones |
| Attacher un disque | `gcloud compute instances attach-disk VM --disk=DISK --zone=ZONE` | Disque visible dans la VM, à formater et monter |
| Agrandir un disque | `gcloud compute disks resize DISK --zone=ZONE --size=500GB` | À chaud ; étendre ensuite le système de fichiers ; réduire est impossible |
| Instantané ponctuel | `gcloud compute snapshots create SNAP --source-disk=DISK --source-disk-zone=ZONE` | Instantané incrémental, stocké en multirégion par défaut ; `--storage-location=REGION` pour le fixer |
| Planifier des instantanés | `gcloud compute resource-policies create snapshot-schedule SCHED --region=REGION --daily-schedule --start-time=02:00 --max-retention-days=14` puis `gcloud compute disks add-resource-policies DISK --zone=ZONE --resource-policies=SCHED` | Instantané quotidien, conservé 14 jours ; heure en UTC |
| Restaurer un disque | `gcloud compute disks create DISK-2 --zone=ZONE --source-snapshot=SNAP` | Nouveau disque, dans n'importe quelle zone |
| Instantanés d'un disque | `gcloud compute snapshots list --filter="sourceDisk~DISK" --sort-by="~creationTimestamp"` | Du plus récent au plus ancien |

### Cloud Run

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Déployer une image | `gcloud run deploy SERVICE --image=REGION-docker.pkg.dev/PROJECT_ID/REPO/IMAGE:TAG --region=REGION --no-allow-unauthenticated --service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Nouvelle révision servie à 100 %, appel authentifié par IAM uniquement |
| Déployer depuis le code source | `gcloud run deploy SERVICE --source=. --region=REGION` | Construit par Cloud Build (Dockerfile ou *buildpacks*), image poussée dans Artifact Registry ; respecte `.gcloudignore` |
| Ressources et mise à l'échelle | `... --cpu=2 --memory=1Gi --concurrency=80 --min-instances=1 --max-instances=20` | `--min-instances=1` évite le démarrage à froid, mais l'instance gardée prête est facturée même inactive |
| Variables et secrets | `... --set-env-vars=ENV=prod --set-secrets=DB_PASSWORD=db-password:latest` | Secret Manager lu au démarrage de l'instance ; `--update-env-vars` pour modifier sans tout remplacer |
| Accès au VPC | `... --network=NETWORK --subnet=SUBNET --vpc-egress=private-ranges-only` | Sortie VPC directe vers les IP privées ; `all-traffic` pour tout faire passer par le VPC |
| Limiter l'entrée | `... --ingress=internal-and-cloud-load-balancing` | Refuse les appels directs depuis Internet ; `internal` pour le VPC seulement |
| Déployer sans basculer le trafic | `... --no-traffic --tag=canary` | Révision testable sur l'URL `https://canary---...run.app`, sans trafic de production |
| Répartir le trafic | `gcloud run services update-traffic SERVICE --region=REGION --to-revisions=SERVICE-00012-abc=90,SERVICE-00013-def=10` | Canary en pourcentages ; `--to-latest` pour tout rendre à la dernière révision |
| Donner le droit d'appeler | `gcloud run services add-iam-policy-binding SERVICE --region=REGION --member=serviceAccount:APPELANT@PROJECT_ID.iam.gserviceaccount.com --role=roles/run.invoker` | L'appelant présente un jeton d'identité dont l'audience est l'URL du service |
| Appeler un service privé depuis le poste | `gcloud run services proxy SERVICE --region=REGION --port=8080` | `http://localhost:8080` relaie avec les identifiants de l'utilisateur |
| URL et configuration | `gcloud run services describe SERVICE --region=REGION --format="value(status.url)"` | URL seule ; sans `--format`, révision active, image, compte de service |
| Révisions d'un service | `gcloud run revisions list --service=SERVICE --region=REGION` | Révisions, part de trafic, date |
| Lire les journaux | `gcloud run services logs read SERVICE --region=REGION --limit=50` | Dernières entrées des 24 dernières heures par défaut (`--freshness`) |
| Créer un job | `gcloud run jobs create JOB --image=IMAGE --region=REGION --tasks=10 --parallelism=5 --max-retries=3 --task-timeout=30m --service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Tâches indexées par `CLOUD_RUN_TASK_INDEX` ; `jobs deploy` crée ou met à jour |
| Exécuter un job | `gcloud run jobs execute JOB --region=REGION --wait` | Attend la fin ; `--update-env-vars` ou `--args` pour surcharger cette exécution |

### GKE

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un cluster Autopilot | `gcloud container clusters create-auto CLUSTER --region=REGION --network=NETWORK --subnetwork=SUBNET --cluster-secondary-range-name=pods --services-secondary-range-name=services --enable-private-nodes` | Nœuds gérés par Google, sans IP publique, plages secondaires du sous-réseau pour les pods et les services |
| Créer un cluster Standard | `gcloud container clusters create CLUSTER --region=REGION --num-nodes=1 --machine-type=e2-standard-4 --enable-autoscaling --min-nodes=1 --max-nodes=5 --workload-pool=PROJECT_ID.svc.id.goog` | En régional, `--num-nodes` s'entend **par zone** ; Workload Identity Federation for GKE activée |
| Ajouter un pool de nœuds Spot | `gcloud container node-pools create POOL --cluster=CLUSTER --region=REGION --spot --machine-type=e2-standard-4` | Nœuds à prix réduit pour les charges tolérantes aux interruptions |
| Configurer `kubectl` | `gcloud container clusters get-credentials CLUSTER --region=REGION` | Contexte ajouté à `~/.kube/config` ; exige le composant `gke-gcloud-auth-plugin` |
| Lister les clusters | `gcloud container clusters list` | Nom, emplacement, version, nombre de nœuds |

### Réseau VPC

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un réseau en mode personnalisé | `gcloud compute networks create NETWORK --subnet-mode=custom` | Aucun sous-réseau créé d'office ; sans l'option, mode automatique avec un sous-réseau par région |
| Créer un sous-réseau | `gcloud compute networks subnets create SUBNET --network=NETWORK --region=REGION --range=10.10.0.0/20 --enable-private-ip-google-access` | Les VM sans IP publique atteignent les API Google |
| Sous-réseau avec plages secondaires | `... --secondary-range=pods=10.20.0.0/16,services=10.30.0.0/20` | Plages d'alias pour les pods et services GKE |
| Journaux de flux | `... --enable-flow-logs` | Échantillon des connexions dans Cloud Logging |
| Agrandir un sous-réseau | `gcloud compute networks subnets expand-ip-range SUBNET --region=REGION --prefix-length=19` | Extension sans coupure ; réduire est impossible |
| Sous-réseau proxy uniquement | `gcloud compute networks subnets create PROXY_SUBNET --network=NETWORK --region=REGION --range=10.129.0.0/23 --purpose=REGIONAL_MANAGED_PROXY --role=ACTIVE` | Requis par les load balancers Envoy régionaux |
| Réserver une IP externe statique | `gcloud compute addresses create IP_NAME --region=REGION` | `--global` pour un load balancer global |
| Réserver une IP interne | `gcloud compute addresses create IP_NAME --region=REGION --subnet=SUBNET --addresses=10.10.0.10` | Adresse fixe dans le sous-réseau |
| Plage pour l'accès aux services privés | `gcloud compute addresses create RANGE --global --purpose=VPC_PEERING --prefix-length=16 --network=NETWORK` | Plage réservée aux services gérés (Cloud SQL en IP privée…) |
| Lire une IP réservée | `gcloud compute addresses describe IP_NAME --region=REGION --format="value(address)"` | Adresse seule |

### Pare-feu et Cloud NAT

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Autoriser SSH par IAP | `gcloud compute firewall-rules create allow-iap-ssh --network=NETWORK --direction=INGRESS --allow=tcp:22 --source-ranges=35.235.240.0/20 --target-tags=ssh-iap` | Seules les VM portant l'étiquette `ssh-iap` sont concernées |
| Autoriser les contrôles d'état | `gcloud compute firewall-rules create allow-hc --network=NETWORK --allow=tcp:8080 --source-ranges=35.191.0.0/16 --target-service-accounts=SA@PROJECT_ID.iam.gserviceaccount.com` | Cible par compte de service, plus sûre qu'une étiquette que tout éditeur de VM peut poser |
| Lister les règles d'un réseau | `gcloud compute firewall-rules list --filter="network~NETWORK" --sort-by=priority` | Priorité, direction, sources, cibles |
| Journaliser une règle | `gcloud compute firewall-rules update RULE --enable-logging` | Connexions autorisées ou refusées par la règle dans Cloud Logging |
| Créer une politique de pare-feu réseau | `gcloud compute network-firewall-policies create POLICY --global` | Ensemble de règles réutilisable, préféré aux règles VPC isolées |
| Ajouter une règle à la politique | `gcloud compute network-firewall-policies rules create 1000 --firewall-policy=POLICY --global-firewall-policy --direction=INGRESS --action=allow --layer4-configs=tcp:443 --src-ip-ranges=0.0.0.0/0` | Le premier argument est la priorité |
| Associer la politique au réseau | `gcloud compute network-firewall-policies associations create --firewall-policy=POLICY --network=NETWORK --global-firewall-policy` | Règles appliquées à tout le réseau |
| Créer un Cloud Router | `gcloud compute routers create ROUTER --network=NETWORK --region=REGION` | Support de Cloud NAT ; plan de contrôle BGP pour VPN et Interconnect |
| Créer Cloud NAT | `gcloud compute routers nats create NAT --router=ROUTER --region=REGION --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges` | Sortie Internet pour toutes les VM et pods de la région sans IP publique |
| NAT avec IP fixes | `... --nat-external-ip-pool=IP_1,IP_2` | Adresses de sortie connues, à déclarer chez un partenaire |
| Diagnostiquer le NAT | `gcloud compute routers nats describe NAT --router=ROUTER --region=REGION` | Configuration, ports par VM, journalisation |

Contexte : [concevoir le réseau](#concevoir-le-reseau), [choisir le calcul](#choisir-le-calcul), [Compute Engine](#compute-engine), [Cloud Run](#cloud-run), [GKE](#gke), [VPC](#vpc), [filtres et formats](#gcloud-filtres-formats).
