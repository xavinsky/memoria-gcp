---
title: "Régions, zones et reprise d'activité"
subgroup: Résilience
---

La résilience d'une application se décide sur deux questions : **quelle panne doit-elle traverser** (une machine, une zone, une région entière) et **qu'accepte-t-on de perdre** quand elle survient (des minutes de service, des minutes de données). La première fixe l'emplacement des ressources, la seconde le modèle de reprise. Cette page suit le guide [*Disaster recovery planning*](https://docs.cloud.google.com/architecture/dr-scenarios-planning-guide), le guide des [archétypes de déploiement](https://docs.cloud.google.com/architecture/deployment-archetypes) et le principe « tester la reprise » du pilier fiabilité du [Well-Architected Framework](#well-architected).

## Emplacements et domaines de défaillance

Une **région** est une zone géographique indépendante, composée d'au moins trois **zones** logées dans au moins trois centres de données ; Stockholm, Mexico, Osaka et Montréal logent encore leurs trois zones dans un ou deux centres. Une zone est un **domaine de défaillance** (*failure domain*) : une panne y reste en général confinée, sans toucher les autres zones de la région. Chaque ressource a une **portée** (*location scope*), fixée par le produit ou choisie à la création (voir [Ressource zonale, régionale ou globale](#lexterm-ressource-zonale-regionale-ou-globale)).

| Portée | Exemples | Survit à | Objectif d'infrastructure |
|---|---|---|---|
| **Zonale** | VM, MIG zonal, disque Hyperdisk ou Persistent Disk, cluster GKE zonal, instance Cloud SQL sans HA, ressources d'arrière-plan d'un job Dataflow (ses workers sont répartis entre les zones par défaut) | Panne d'un composant | 99,9 % (43 min par mois) |
| **Régionale** | MIG régional, cluster GKE régional, service Cloud Run, bucket régional, instance Spanner régionale, Hyperdisk Balanced High Availability, sous-réseau | Panne d'une zone | 99,99 % (4,3 min par mois) |
| **Birégionale, multirégionale** | Bucket birégion ou multirégion, instance Spanner birégion ou multirégion, instance Bigtable multi-régions, trousseau Cloud KMS multirégional | Panne d'une région | 99,999 % (26 s par mois) |
| **Globale** | Projet, réseau VPC et règles de pare-feu, zone Cloud DNS, load balancer applicatif externe global, sujet Pub/Sub, secret Secret Manager | Panne d'une région | 99,999 % |

Ces pourcentages sont les objectifs de conception de l'infrastructure, publiés dans le [guide de fiabilité de l'infrastructure](https://docs.cloud.google.com/architecture/infra-reliability-guide/building-blocks), non des engagements : le **SLA** de chaque produit dépend de sa configuration et figure sur sa page [SLA](https://cloud.google.com/terms/sla).

## Archétypes de déploiement

Un archétype dit **sur quels domaines de défaillance l'application tourne**. Le choisir d'abord simplifie le reste : un archétype régional impose un cluster GKE régional, un MIG régional, une base en haute disponibilité.

| Archétype | Principe | Disponibilité visée | Usages | Coût, exploitation |
|---|---|---|---|---|
| **Zonal** | Une seule zone, éventuellement une copie passive dans une autre | 99,9 % | Développement, recette, logiciel sous licence liée à une machine, applications sans exigence de disponibilité | Le plus simple ; RTO de plusieurs heures en cas de panne de zone |
| **Régional** | Plusieurs zones d'une région, chacune autonome | 99,99 % | Application interne ou utilisateurs d'une même zone géographique ; résidence des données | Coût moyen ; indisponible si la région tombe |
| **Multirégional** | Une pile par région, routage DNS vers des load balancers régionaux | 99,999 % | Utilisateurs dispersés, latence, résidence par routage géographique | Le plus cher : réplication et transfert inter-régions, exploitation de plusieurs piles |
| **Global** | Pile répartie ou piles régionales derrière un load balancer *anycast* et une base mondiale | 99,999 % | Service mondial | Coût moyen : ressources globales au lieu de N copies régionales ; Premium Tier obligatoire |
| **Hybride**, **multicloud** | Un des archétypes ci-dessus, combiné à un site sur site ou à un autre cloud | Selon le maillon le plus faible | Site de secours d'un existant, migration progressive | Réseau hybride et double outillage |

## Options par service

| Service | Panne de zone | Panne de région | Point d'attention |
|---|---|---|---|
| [Compute Engine](#compute-engine) | MIG régional, autoréparation par contrôle d'état | Un MIG régional par région derrière un load balancer global ou inter-régions | Un MIG à état ne s'étend pas horizontalement : prévoir la capacité |
| Disques ([Persistent Disk](#persistent-disk), [Hyperdisk](#hyperdisk)) | Disque régional ou Hyperdisk Balanced High Availability : écriture synchrone sur deux zones, rattachement forcé à une VM de l'autre zone | Réplication asynchrone de disque, RPO visé d'une minute, bascule manuelle | Le disque régional double le stockage facturé |
| [GKE](#gke) | Cluster régional : trois plans de contrôle et des nœuds sur trois zones | Un cluster régional par région, Multi Cluster Ingress ou Gateway multicluster | Un cluster zonal perd son plan de contrôle avec la zone |
| [Cloud Run](#cloud-run) | Natif : instances réparties sur les zones par le service | Service multirégion (`gcloud run deploy --regions`), load balancer global, *service health* pour la bascule automatique | Le service ne réplique rien et ne route jamais vers une autre région de lui-même |
| [Cloud SQL](#cloud-sql) | Haute disponibilité : secours dans une autre zone sur disque régional, bascule automatique | Réplique inter-régions asynchrone, promotion manuelle ; en Enterprise Plus, réplique de reprise désignée, *switchover* sans perte et point d'écriture qui suit le primaire | Une instance sans HA est zonale |
| [AlloyDB](#alloydb) | HA par défaut : deux nœuds dans deux zones, stockage régional | Cluster secondaire inter-régions asynchrone, promu en primaire autonome | Le RPO dépend du retard de réplication : mesurer le débit sûr |
| [Spanner](#spanner) | Configuration régionale : trois zones, quorum de deux | Birégion ou multirégion (Enterprise Plus) : écriture validée dans deux régions, RPO nul ; en birégion, bascule du quorum manuelle (une minute environ) ou automatique (jusqu'à 45 min) | Latence d'écriture plus haute ; birégion proposée dans quelques pays seulement |
| [Bigtable](#bigtable) | Deux clusters dans la région, routage multi-cluster | Clusters dans plusieurs régions, routage multi-cluster | Réplication asynchrone à cohérence à terme : les écritures récentes peuvent manquer |
| [Cloud Storage](#cloud-storage) | Bucket régional : aucune écriture perdue | Birégion ou multirégion, RTO nul ; 99,9 % des nouveaux objets répliqués en une heure, 100 % en 12 h ; [réplication turbo](#lexterm-replication-turbo-turbo-replication) en birégion : 100 % en 15 min | Réplication entre buckets pour deux buckets indépendants, sans RPO garanti |
| [BigQuery](#bigquery) | Natif : écriture synchrone sur deux zones | Réplication de dataset inter-régions (asynchrone) ; reprise gérée en Enterprise Plus, bascule *soft* sans perte ou *hard* immédiate | Une **multirégion** (`US`, `EU`) ne réplique pas entre régions |
| [Pub/Sub](#pubsub) | Natif : message écrit sur au moins deux zones | Sujet global : les éditeurs et abonnés des autres régions continuent | Les messages stockés dans la région en panne sont inaccessibles jusqu'à son retour |
| [Dataflow](#dataflow) | Placement régional par défaut : les workers sont créés dans toutes les zones de la région et recréés ailleurs si une zone tombe, le travail d'un worker perdu étant retraité ; exige Streaming Engine ou Dataflow Shuffle, sinon le job tourne dans une seule zone | Le job appartient à sa région : relancer le pipeline dans une autre région, avec des sources et des destinations accessibles de là | Des ressources internes du job restent zonales (champ *Service zones*) et peuvent le faire échouer. L'instantané d'un job en continu (état, plus en option un instantané de l'abonnement Pub/Sub) ne se restaure que dans sa région |
| [Managed Service for Apache Spark](#managed-service-for-apache-spark) | Aucune : tous les nœuds d'un cluster, même en haute disponibilité, sont dans la même zone ; recréer le cluster dans une autre zone | Recréer le cluster dans une autre région, avec les données et les scripts dans Cloud Storage | Mode haute disponibilité (trois maîtres, choisi à la création) : HDFS et YARN traversent la panne d'un nœud, mais pas le *driver* d'un job soumis par l'API Jobs |
| [Managed Service for Apache Airflow](#managed-service-for-apache-airflow) | Environnement hautement résilient, recommandé en production : composants sur au moins deux zones, base Cloud SQL en haute disponibilité ; les tâches de la zone en panne échouent, puis Airflow les replanifie | [Instantanés d'environnement](#lexterm-instantane-d-environnement-airflow) planifiés dans un bucket d'une autre région ou multirégional, chargés dans un environnement de secours, créé à l'avance (tiède) ou après l'incident (froid) | L'environnement de secours doit avoir la même version et le même build d'Airflow ; son interface et son bucket changent d'adresse. Instantanés limités à une base Airflow de moins de 20 Go |
| [Filestore](#filestore) | Niveau Regional ou Enterprise : écriture confirmée sur deux zones | Réplication d'instance asynchrone, sauvegardes restaurées dans une autre région | Basic et Zonal sont zonaux |
| [Cloud Load Balancing](#cloud-load-balancing) | Load balancer régional | Load balancer global, ou inter-régions avec bascule vers des backends de secours | La résilience réelle dépend autant des backends que du load balancer |

## RPO, RTO et SLA

- **[RPO](#lexterm-rpo-recovery-point-objective)** (*recovery point objective*) : durée maximale de données qu'on accepte de perdre. Il se fixe **par type de données** : un catalogue qui se recharge depuis une source tolère des heures, des commandes aucune perte.
- **[RTO](#lexterm-rto-recovery-time-objective)** (*recovery time objective*) : durée maximale d'indisponibilité. Il inclut les gestes humains : décider de basculer, promouvoir une base, changer un DNS.
- RPO et RTO sont des SLO parmi d'autres. Ils se déduisent d'une analyse d'impact métier, et **leur coût croît vite quand ils tendent vers zéro**.

Le guide [*Architecting disaster recovery for cloud infrastructure outages*](https://docs.cloud.google.com/architecture/disaster-recovery) donne les repères : un **RPO nul** impose une réplication synchrone, donc des produits régionaux (résistants à la perte d'une zone) ou Spanner birégion ou multirégion pour la perte d'une région. Un **RTO de quelques minutes** impose une bascule automatique, sans décision humaine. La plupart des applications visent **entre une heure et un jour**, ce qui permet une veille tiède ; au-delà d'un jour, une restauration depuis les sauvegardes suffit. Réserver le RPO et le RTO nuls à la partie des données et des services qui les exige.

**Composer les disponibilités.** Des étages qui dépendent l'un de l'autre se multiplient : un load balancer à 99,99 %, un service Cloud Run à 99,95 % et une instance Cloud SQL Enterprise en HA à 99,95 % donnent 0,9999 × 0,9995 × 0,9995 ≈ **99,89 %**, soit environ 48 minutes par mois. Chaque étage ajouté fait baisser le total. À l'inverse, deux copies redondantes d'une ressource à 99,9 % dans deux domaines de défaillance tombent ensemble avec une probabilité de 0,001², mais le résultat reste plafonné par l'objectif de l'emplacement : 99,99 % sur plusieurs zones, 99,999 % sur plusieurs régions.

## Modèles de reprise

![Modèles de reprise d'activité entre une région principale et une région de secours](../../svg/modeles-reprise-activite.svg)

| Modèle | Région de secours avant l'incident | RPO | RTO | Coût | Briques Google Cloud |
|---|---|---|---|---|---|
| **Sauvegarde et restauration** | Sauvegardes et code IaC, rien ne tourne | Intervalle entre sauvegardes | Heures à jours : tout recréer | Stockage des sauvegardes | Sauvegardes Cloud SQL, instantanés de disque multirégionaux, [Backup and DR](#backup-and-dr), bucket birégion |
| **Veille tiède** | Données répliquées, calcul éteint ou réduit | Minutes | Une heure à un jour : monter le calcul, promouvoir, rediriger | Base de secours et réplication | Réplique Cloud SQL ou AlloyDB inter-régions, MIG à zéro instance, IaC prête |
| **Veille chaude** | Pile complète, sans trafic | Secondes à minutes | Minutes, bascule automatisée | Près du double | Réplique DR Cloud SQL Enterprise Plus, load balancer global avec backends de secours, *service health* Cloud Run |
| **Actif-actif** | Pile complète qui sert une part du trafic | Nul avec une base synchrone | Quasi nul | Double, plus la réplication et l'exploitation de plusieurs piles | Spanner birégion ou multirégion, load balancer global, GKE ou Cloud Run dans chaque région |

Les ordres de grandeur de RPO et de RTO sont indicatifs : chacun se mesure sur la charge réelle, pendant un exercice. Le guide Google classe ces modèles en **froid** (pas de roue de secours), **tiède** (roue de secours, arrêt pour la changer) et **chaud** (pneus qui roulent crevés). Un même système les combine souvent : la base en veille chaude, les frontaux en veille tiède, l'archive réglementaire en sauvegarde froide.

```python
import pulumi_gcp as gcp

reglages = {
    "tier": "db-perf-optimized-N-4",
    "edition": "ENTERPRISE_PLUS",
    "availability_type": "REGIONAL",  # secours dans une autre zone, bascule automatique
}

primaire = gcp.sql.DatabaseInstance(
    "primaire",
    region="europe-west1",
    database_version="POSTGRES_17",
    deletion_protection=True,
    settings={**reglages, "backup_configuration": {
        "enabled": True,
        "point_in_time_recovery_enabled": True,
        "location": "europe-west4",  # sauvegardes rangées dans la région de secours
    }},
)

# Réplique asynchrone dans la région de secours, promue en cas de panne régionale
secours = gcp.sql.DatabaseInstance(
    "secours",
    region="europe-west4",
    database_version="POSTGRES_17",
    master_instance_name=primaire.name,
    deletion_protection=True,
    settings=reglages,
)
```

Pour une bascule sans perte et un retour automatisé, désigner ensuite `secours` comme réplique de reprise du primaire (`settings.replication_cluster.failover_dr_replica_name`, format `PROJECT_ID:secours`), ce qui ouvre le *switchover*.

## Tester la reprise

Un plan de reprise non testé ne vaut rien : le pilier fiabilité en fait un principe à part, [*Perform testing for recovery from failures*](https://docs.cloud.google.com/architecture/framework/reliability/perform-testing-for-recovery-from-failures), complété par la reprise après perte de données.

- **Fixer l'objectif du test** : valider le RPO et le RTO, vérifier la bascule automatique, restaurer une sauvegarde. Délimiter le périmètre, y compris les dépendances externes.
- **Simuler la panne** en recette, ou en production avec un retour arrière prêt : arrêter un nœud d'un cluster GKE, couper une instance Cloud SQL, isoler une région par des règles de pare-feu. **Fault Injection Testing** [!PREVERSION] injecte, sur demande, des pannes dans les ressources Google Cloud.
- **Exercer la vraie procédure** : un *switchover* Cloud SQL Enterprise Plus, une bascule *soft* BigQuery, une restauration de sauvegarde dans l'autre région, un changement de DNS. Chaque étape du plan est une commande précise, pas « lancer le script de restauration ».
- **Observer** la bascule dans [Cloud Monitoring](#cloud-monitoring) : latence, erreurs, retard de réplication, alertes déclenchées (voir [Alertes et incidents](#alertes-et-incidents)).
- **Vérifier l'environnement de secours** : les mêmes droits IAM, les mêmes règles réseau, un accès des équipes testé, un chemin d'accès à Google Cloud de rechange si l'habituel est coupé.
- **Rédiger un postmortem** et corriger le plan après chaque exercice.

## Backup and DR

[Backup and DR](#backup-and-dr) centralise les sauvegardes de VM, de disques, de Filestore, de Cloud SQL, d'AlloyDB et de bases auto-gérées (Oracle, SQL Server, SAP HANA), dans des **coffres** immuables situés hors du projet protégé. Il sert le modèle « sauvegarde et restauration » quand la politique doit être unique pour tout un parc, ou quand la rétention doit résister à un administrateur compromis. Pour quelques disques ou une seule base, les instantanés planifiés et les sauvegardes natives du service suffisent. Il clone aussi une production vers un autre projet ou une autre région, ce qui sert de répétition de reprise.

## Pièges

- **Résidence des données.** Une multirégion reste dans sa géographie (`EU`, `US`), mais la région de secours doit, elle aussi, respecter les contraintes réglementaires. La contrainte de règle d'administration `gcp.resourceLocations` limite les emplacements autorisés (voir [Hiérarchie des ressources](#hierarchie-des-ressources)).
- **Coût du transfert inter-régions.** Réplication de base, de disques et de buckets, trafic entre piles : tout octet qui change de région est facturé. Le load balancer global exige le niveau réseau Premium.
- **Quotas et capacité dans la région de secours.** Les quotas sont régionaux : une région de secours sous-dimensionnée refuse la montée en charge le jour de la bascule. Relever les quotas à l'avance, réserver la capacité rare (GPU, grands types de machine) par des réservations Compute Engine (voir [Quotas et limites](#quotas-et-limites)).
- **TTL DNS.** Une bascule par DNS attend l'expiration du TTL dans les caches des clients et des résolveurs. Un load balancer global garde la même adresse *anycast* et bascule sans toucher au DNS.
- **Dépendances oubliées.** Clés [Cloud KMS](#cloud-kms) régionales, images dans un Artifact Registry régional, chaîne de déploiement, secrets, identités : si elles ne vivent que dans la région en panne, la restauration échoue ailleurs.
- **Double primaire** (*split brain*). Promouvoir une réplique en retard alors que le primaire revient produit deux bases divergentes. La promotion Cloud SQL est manuelle pour cette raison ; la bascule *hard* de BigQuery peut aussi perdre les droits d'accès pas encore répliqués.

## Alternatives en logiciel libre

- **Velero** (Apache 2.0) : sauvegarde et restauration des objets Kubernetes et de leurs volumes vers un stockage objet, restauration dans un autre cluster ou une autre région ; le modèle « sauvegarde et restauration » pour GKE.
- **CloudNativePG** (Apache 2.0) : opérateur PostgreSQL pour Kubernetes, avec haute disponibilité dans un cluster et *replica clusters* dans une autre région, promus à la main ; l'équivalent d'une réplique inter-régions Cloud SQL.
- **Patroni** (MIT) : haute disponibilité PostgreSQL par consensus (etcd, Consul, ZooKeeper), avec un *standby cluster* dans un autre centre de données.
- **Ceph** (LGPL 2.1 ou 3) : stockage objet et bloc distribué, avec réplication *multisite* de la passerelle objet et miroir de volumes RBD entre sites ; ce que font les buckets birégions et la réplication asynchrone de disque.
- **restic** (BSD 2 clauses) : sauvegarde incrémentale, dédupliquée et chiffrée vers un bucket compatible S3 ou Cloud Storage ; la brique la plus simple d'un plan froid.
- **Chaos Mesh** et **LitmusChaos** (Apache 2.0) : injection de pannes dans Kubernetes (pods, réseau, zones simulées), pour exercer la reprise comme Fault Injection Testing.
