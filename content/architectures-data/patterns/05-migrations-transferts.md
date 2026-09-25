---
title: Migrer et transférer des données
---

Le service se choisit d'abord sur la **nature des données** : fichiers et objets, entrepôt analytique, base transactionnelle, ou données d'une application SaaS. Pour les fichiers, la **bande passante** disponible et la **récurrence** du transfert départagent ensuite les candidats ; pour une base, c'est la **destination** — une autre base qu'on bascule, ou BigQuery qu'on alimente en continu.

![Arbre de décision : du type de données au service de migration ou de transfert](../../svg/choix-migration-transfert.svg)

## Matrice de choix

| Service | Source | Destination | Mode | Récurrence | Coût du service |
|---|---|---|---|---|---|
| **`gcloud storage`** | Disque local, VM, autre bucket | Cloud Storage | En ligne, lancé à la main | Ponctuelle ou script | Gratuit, seuls le stockage et les opérations sont facturés |
| **[Storage Transfer Service](#storage-transfer-service)** | S3, Azure, stockage compatible S3, URL, bucket, NFS ou HDFS par agents | Cloud Storage, système de fichiers | En ligne, géré | Ponctuelle, planifiée (toutes les heures au plus), événementielle | Gratuit sans agent ; au Gio avec agents vers ou depuis un système de fichiers |
| **[Transfer Appliance](#transfer-appliance)** | Centre de données, site mal connecté | Cloud Storage | Hors ligne, baie expédiée | Ponctuelle | Forfait par appliance (300 $ pour 40 To, 1 800 $ pour 300 To) avec 10 ou 25 jours inclus, puis un tarif journalier, plus l'expédition |
| **BigQuery Data Transfer Service** | SaaS (Salesforce, ServiceNow), régies publicitaires Google, S3, Azure, Cloud Storage, bases et entrepôts | BigQuery | En ligne, géré | Planifiée, événementielle pour Cloud Storage | En *slots*-heures ; gratuit pour les sources Google, le stockage objet et les connecteurs de migration |
| **[BigQuery Migration Service](#bigquery-migration-service)** | Teradata, Redshift, Snowflake, Netezza, Oracle, Hive | BigQuery | Évaluation, traduction SQL, puis transfert par le Data Transfer Service | Ponctuelle, incréments jusqu'à la bascule | Évaluation et traduction gratuites |
| **[Database Migration Service](#database-migration-service)** | MySQL, PostgreSQL, SQL Server, Oracle | Cloud SQL, AlloyDB | Vidage initial puis CDC, jusqu'à la promotion | Ponctuelle | Homogène gratuit ; hétérogène au volume traité |
| **[Datastream](#datastream)** | MySQL, PostgreSQL, Oracle, SQL Server, MongoDB, Spanner, Salesforce | BigQuery, Cloud Storage, tables Iceberg | *Backfill* puis CDC continu | Permanente | Au volume traité, rien à l'arrêt |

## Estimer la durée d'un transfert en ligne

La durée théorique vaut le volume divisé par le débit ; la documentation de Google y ajoute une marge de gestion et d'efficacité réseau, qui porte 100 To sur une liaison à 1 Gbit/s à **12 jours** au lieu de 9. D'où une règle de calcul mental :

**durée en jours ≈ 0,12 × volume en To ÷ débit en Gbit/s**

| Volume | 100 Mbit/s | 1 Gbit/s | 10 Gbit/s |
|---|---|---|---|
| 100 Go | 3 heures | 17 minutes | 2 minutes |
| 1 To | 1,2 jour | 3 heures | 17 minutes |
| 10 To | 12 jours | 1,2 jour | 3 heures |
| 100 To | 4 mois | 12 jours | 1,2 jour |
| 1 Po | 3 ans et demi | 4 mois | 12 jours |

Le débit à retenir est celui qu'on peut réellement **consacrer** au transfert, pas la capacité nominale du lien : une liaison partagée avec la production ne donne souvent qu'une fraction de sa capacité, et seulement la nuit.

Google recommande [Transfer Appliance](#transfer-appliance) dès que le transfert par le réseau prendrait **plus d'une semaine**. Pour comparer, un cycle complet d'appliance prend environ trois semaines : 300 To se copient sur l'appliance en moins de 25 jours, puis sont disponibles dans Cloud Storage une dizaine de jours ouvrés plus tard. Le même volume demande environ neuf mois sur une liaison à 100 Mbit/s. Entre une et trois semaines de transfert réseau, le choix dépend de l'échéance et de la logistique : réception de la baie, raccordement, expédition retour.

> [!TIP]
> Avant de commander une appliance, vérifier si le débit peut être augmenté pour la durée du projet : un [Cloud Interconnect](#cloud-interconnect) sert ensuite à l'architecture hybride, alors qu'une appliance ne sert qu'une fois. L'appliance reste la seule réponse pour un site sans connexion correcte.

## Fichiers et objets

- **`gcloud storage cp` et `rsync`** pour moins d'un tébioctet, ou pour quelques très gros fichiers. Au-delà de 150 Mio par fichier, la CLI découpe l'envoi en au plus 32 morceaux envoyés en parallèle puis recomposés (*parallel composite upload*), dès que la classe de destination est Standard et que le bucket n'a ni règle de conservation ni blocage par défaut.
- **[Storage Transfer Service](#storage-transfer-service)** au-delà d'un tébioctet, pour toute source dans un autre cloud, et pour tout transfert récurrent. Il apporte ce que la CLI n'a pas : reprise automatique, journal détaillé, plafond de bande passante sur les agents, planification, déclenchement par événement (Pub/Sub, SQS, Azure Storage Queue).
- **[Transfer Appliance](#transfer-appliance)** quand le réseau ne suffit pas, d'après le calcul ci-dessus. Le mode en ligne de l'appliance permet aussi de s'en servir comme passerelle sur un site bien connecté.

```bash
# Petit volume : copie puis synchronisation incrémentale
gcloud storage cp -r ./export gs://BUCKET/export/
gcloud storage rsync -r ./export gs://BUCKET/export

# Autre cloud : job quotidien depuis S3
gcloud transfer jobs create s3://SOURCE_BUCKET gs://BUCKET \
  --source-creds-file=creds.json --schedule-repeats-every=1d

# Système de fichiers sur site : agents dans un pool, puis job
gcloud transfer agents install --pool=POOL --count=3
gcloud transfer jobs create posix:///data/export gs://BUCKET \
  --source-agent-pool=POOL
```

Une migration de lac de données se fait rarement en une passe : une copie massive (appliance ou job initial), puis des transferts incrémentaux planifiés qui ne copient que les objets nouveaux ou modifiés, jusqu'à la bascule des traitements.

## Entrepôts de données

[BigQuery Migration Service](#bigquery-migration-service) organise la migration d'un entrepôt en trois temps. L'**évaluation** part des métadonnées et des journaux de requêtes extraits par `dwh-migration-dumper`, et chiffre le coût dans BigQuery, les tables inutilisées et le taux de traduction automatique. La **traduction SQL**, interactive ou par lots, convertit scripts, vues et procédures vers GoogleSQL. Le **transfert** des tables est délégué au BigQuery Data Transfer Service, avec des incréments jusqu'à la bascule. La modélisation cible est traitée dans [Organiser BigQuery](#organiser-bigquery).

Traduire le SQL ne suffit pas : un entrepôt migré garde les habitudes de la source (index, tables de travail, mises à jour ligne à ligne) que BigQuery rend coûteuses. La vague de migration est le bon moment pour partitionner, regrouper et réécrire les chaînes de transformation en [ELT](#batch-etl-elt).

## Bases transactionnelles

Deux services lisent le journal de transactions d'une base, pour deux usages différents :

- **[Database Migration Service](#database-migration-service)** **migre** une base vers Cloud SQL ou AlloyDB : vidage initial, réplication continue, puis **promotion** de la destination, qui la détache de la source. Le travail s'arrête là. Oracle et SQL Server vers PostgreSQL passent par un espace de conversion qui traduit schéma et code.
- **[Datastream](#datastream)** **réplique** en continu vers BigQuery, Cloud Storage ou des tables Iceberg, sans fin prévue. C'est le socle du [CDC](#cdc).

Pour une base qu'on ne change ni de moteur ni de modèle d'exploitation, [Migrate to Virtual Machines](#migrate-to-virtual-machines) déplace le serveur entier. Pour Spanner, les outils de migration propres à Spanner prennent le relais.

## Données SaaS et chargements récurrents vers BigQuery

Le **BigQuery Data Transfer Service** charge BigQuery à intervalle régulier, sans code : applications SaaS (Salesforce, Salesforce Marketing Cloud, ServiceNow), régies et outils Google (Google Ads, Google Analytics 4, YouTube), stockage objet (Cloud Storage, S3, Azure Blob) et bases ou entrepôts (MySQL, PostgreSQL, Oracle, Teradata, Redshift, Snowflake). Trois propriétés à connaître :

- l'intervalle minimal est de 15 minutes pour une source Cloud Storage, qui accepte aussi un déclenchement par un abonnement Pub/Sub ;
- un **backfill** relance le chargement d'une période passée après une panne ou pour amorcer l'historique ;
- il ne fait que charger : il ne sort aucune donnée de BigQuery.

Le même service porte deux fonctions internes à BigQuery : les **copies de datasets**, y compris d'une région à l'autre, et les **requêtes planifiées** (voir [Orchestrer les pipelines](#orchestration)).

## Pièges

- **Frais de sortie de la source** : Storage Transfer Service ne facture rien pour une source S3 ou Azure, mais le fournisseur d'origine facture la sortie des données. Sur un gros lac, c'est souvent le premier poste de coût.
- **Beaucoup de petits fichiers** : chaque objet coûte une opération et un aller-retour. Regrouper les arborescences fines en archives avant le transfert, que ce soit par le réseau ou par appliance.
- **Objets composites** : un objet issu d'un envoi composite parallèle n'a pas de somme MD5, seulement un CRC32C. Les outils qui contrôlent l'intégrité par MD5 échouent ; ne pas activer ce mode vers un bucket doté d'une règle de conservation, où les morceaux temporaires ne peuvent pas être supprimés.
- **Planifier la validation** : compter les objets et comparer les sommes de contrôle pour les fichiers, comparer nombres de lignes et agrégats pour un entrepôt (outil libre *Data Validation Tool*). Une migration sans validation n'est pas terminée.

> [!WARNING]
> Le mode événementiel de Storage Transfer Service ne propage pas les suppressions : un objet effacé à la source reste dans la destination. Pour une réplique fidèle, prévoir en complément un job planifié avec l'option `--delete-from=destination-if-unique`, qui supprime de la destination les objets absents de la source.

## Alternatives en logiciel libre

- **Rclone** (MIT) : copie et synchronisation entre plus de soixante stockages objet et systèmes de fichiers, avec reprise, filtres et vérification des sommes de contrôle ; l'équivalent le plus direct de Storage Transfer Service, sans planification ni agents gérés.
- **rsync** (GPL v3) : transferts incrémentaux entre systèmes de fichiers POSIX, pour alimenter une zone de dépôt avant l'envoi vers le stockage objet.
- **Apache Hadoop DistCp** (Apache 2.0) : copie distribuée entre HDFS et un stockage objet, pour migrer un lac de données depuis un cluster Hadoop.
- **SQLGlot** (MIT) : traduction SQL entre une trentaine de dialectes (Teradata, Snowflake, Redshift, BigQuery…), sans l'évaluation fondée sur les journaux de requêtes de BigQuery Migration Service.
- **Ora2Pg** (GPL v3) et **pgloader** (licence PostgreSQL) : conversion de schéma et de code Oracle vers PostgreSQL pour le premier, chargement de MySQL ou SQL Server vers PostgreSQL pour le second ; ils couvrent le vidage initial de Database Migration Service, pas sa réplication continue.
- **Debezium** (Apache 2.0) : la réplication continue jusqu'à la bascule, pour une migration sur mesure avec Kafka Connect.
- **Data Validation Tool** (Apache 2.0) : l'outil de validation cité plus haut, publié par Google ; il compare nombres de lignes, agrégats et sommes de contrôle entre la source et la cible, quel que soit l'outil de transfert.
