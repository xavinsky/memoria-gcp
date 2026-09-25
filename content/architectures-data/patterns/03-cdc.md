---
title: "CDC : répliquer une base vers l'analytique"
---

La capture de changements (*change data capture*, CDC) lit le **journal de transactions** d'une base — *binlog* MySQL, WAL PostgreSQL, *redo logs* Oracle — et rejoue chaque insertion, mise à jour ou suppression dans une destination. La base de production ne subit aucune requête lourde, et l'analytique suit la source à quelques minutes près. Sur Google Cloud, l'outil par défaut est [Datastream](#datastream) ; les autres options répondent à des cas plus étroits.

![Chemins d'une réplication CDC avec Datastream](../../svg/cdc-datastream.svg)

## Le déroulé d'un flux

1. **Connectivité** : Datastream joint la source par liste d'adresses IP, tunnel SSH ou connectivité privée (voir plus bas).
2. **Remplissage initial** (*backfill*) : lecture des tables entières pour constituer l'état de départ. Il tourne **en même temps** que la capture ; les métadonnées de chaque événement disent s'il vient du *backfill* ou du CDC.
3. **Capture continue** : chaque changement validé (*commit*) devient un événement, traduit dans un **type unifié** commun à toutes les sources.
4. **Écriture** : directement dans BigQuery, dans des tables Apache Iceberg, ou en fichiers Avro ou JSON dans Cloud Storage.

Sources : MySQL, PostgreSQL (dont AlloyDB), Oracle, SQL Server, où qu'elles soient hébergées (sur site, VM, Cloud SQL, Amazon RDS) ; Spanner, MongoDB ; Salesforce, Salesforce Marketing Cloud [!PREVERSION], ServiceNow [!PREVERSION], Microsoft Dataverse [!PREVERSION] et Workday [!PREVERSION].

## Matrice de choix

| Solution | Sources | Destination | Fraîcheur | Quand la choisir |
|---|---|---|---|---|
| **[Datastream](#datastream) → BigQuery** | Relationnel, Spanner, MongoDB, Salesforce | Tables BigQuery ou Iceberg | Minutes, réglable | Cas général : réplique analytique sans pipeline à écrire |
| **Datastream → Cloud Storage → [Dataflow](#dataflow)** | Idem | Fichiers, puis BigQuery, Spanner, Cloud SQL, AlloyDB | Minutes | Transformer au passage, alimenter une autre base, architecture événementielle |
| **Requête fédérée** (`EXTERNAL_QUERY`) | [Cloud SQL](#cloud-sql), [AlloyDB](#alloydb), [Spanner](#spanner) | Aucune copie | Temps réel | Jointure ponctuelle ou petit volume, sans réplication à maintenir |
| **Flux de modifications [Spanner](#spanner)** | Spanner | Dataflow, Kafka, Datastream | Secondes | Réagir aux changements Spanner dans un pipeline |
| **Flux de modifications [Bigtable](#bigtable)** | Bigtable | Dataflow (vers BigQuery, Pub/Sub) | Secondes | Historiser ou diffuser les écritures Bigtable |
| **[Database Migration Service](#database-migration-service)** | MySQL, PostgreSQL, SQL Server, Oracle | Cloud SQL, AlloyDB | Réplique jusqu'à la promotion | Migrer une base transactionnelle, pas alimenter l'analytique |
| **Debezium + [Kafka](#managed-service-for-apache-kafka)** | Toute base à connecteur | Sujets Kafka, puis tout consommateur | Secondes | Plateforme Kafka déjà en place, plusieurs consommateurs d'un même flux |

## Questions qui départagent

- **Copier ou interroger à distance ?** Une [requête fédérée](#lexterm-requete-federee) envoie une requête en lecture seule à Cloud SQL, AlloyDB ou Spanner, dans le dialecte de la base, et ramène le résultat dans une table temporaire. Rien à répliquer, mais chaque requête charge la base de production et reste plus lente qu'une lecture du stockage BigQuery. Au-delà d'un usage ponctuel, répliquer.
- **Migrer ou répliquer durablement ?** Database Migration Service fait aussi du CDC, mais pour tenir une **base transactionnelle** cible à jour jusqu'à la bascule, puis s'arrête à la promotion. Pour l'analytique, c'est Datastream (voir [Migrations et transferts](#migrations-transferts)).
- **BigQuery direct ou détour par Cloud Storage ?** La destination BigQuery est la plus simple : Datastream crée les tables et applique les changements. Le détour par Cloud Storage garde un journal d'événements brut et permet un pipeline Dataflow entre les deux, par exemple pour masquer ou enrichir des colonnes.
- **La source est Spanner ou Bigtable ?** Ces bases publient leurs propres **flux de modifications** (*change streams*). Spanner est aussi une source Datastream, avec une franchise mensuelle de 100 Gio vers BigQuery ; Bigtable passe par Dataflow.
- **Kafka est-il déjà le bus de l'entreprise ?** Si plusieurs équipes consomment les mêmes changements, un flux Debezium vers Kafka sert tout le monde. Sinon, Datastream évite d'exploiter des connecteurs.

## Datastream vers BigQuery : les réglages

### Mode d'écriture

| | Mode fusion (défaut) | Mode ajout seul |
|---|---|---|
| Contenu de la table | État courant de la source (`UPSERT`) | Une ligne par changement |
| Historique | Aucun : une ligne supprimée disparaît | Complet : `INSERT`, `UPDATE-INSERT`, `UPDATE-DELETE`, `DELETE` |
| Condition | Clé primaire sur la table source | Aucune |
| Coût BigQuery | Fusions en arrière-plan, facturées à part | Écriture simple, requêtes plus lourdes |
| Destination Iceberg | Non | Seul mode possible |

Une table sans clé primaire est toujours écrite en ajout seul, même dans un flux en mode fusion. Chaque table reçoit une colonne `datastream_metadata` : identifiant de l'événement (`UUID`), horodatage à la source (`SOURCE_TIMESTAMP`), et en ajout seul le type de changement (`CHANGE_TYPE`) et les clés de tri (`SORT_KEYS`).

Recalculer l'état courant depuis une table en ajout seul :

```sql
SELECT * EXCEPT (rang)
FROM (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY id
      ORDER BY datastream_metadata.source_timestamp DESC) AS rang
  FROM DATASET.commandes
)
WHERE rang = 1
  AND datastream_metadata.change_type NOT IN ('DELETE', 'UPDATE-DELETE');
```

Si deux changements d'une même ligne partagent le même horodatage, les départager par `SORT_KEYS`.

### Fraîcheur et coût : `max_staleness`

En mode fusion, BigQuery applique les changements en arrière-plan. L'option de table `max_staleness` fixe l'écart toléré : tant que la dernière fusion est plus récente que cet intervalle, une requête lit cette version sans attendre ; au-delà, BigQuery fusionne au moment de la requête, qui devient plus lente et plus chère. Datastream pose l'option à la création de chaque table, d'après la **limite d'obsolescence** du flux.

```sql
ALTER TABLE DATASET.commandes SET OPTIONS (max_staleness = INTERVAL 15 MINUTE);
```

La documentation recommande de retenir la plus grande de deux valeurs : l'obsolescence tolérable pour l'usage, et deux fois la durée des fusions en arrière-plan (95ᵉ centile, lu dans `INFORMATION_SCHEMA.JOBS` sur les jobs `cdc_background`), plus une marge. Un tableau de bord rafraîchi chaque heure n'a pas besoin de 5 minutes.

> [!TIP]
> Sans réservation affectée au type `BACKGROUND` (ou `BACKGROUND_CHANGE_DATA_CAPTURE`), les fusions sont facturées à la demande. Une réservation de slots dédiée rend ce coût prévisible et plafonné (voir [Organiser BigQuery](#organiser-bigquery)).

### Organisation des datasets

- **Un dataset par schéma** : Datastream crée dans BigQuery un dataset par schéma ou base source (`mydb.employees` → dataset `mydb`, table `employees`).
- **Un seul dataset** : toutes les tables dans un dataset choisi, nommées `schéma_table`.

Garder le flux et les datasets dans la même région limite le coût et la latence. La transformation vient ensuite, dans BigQuery : vues ou modèles [Dataform](#dataform) au-dessus des tables répliquées (voir [Batch ETL / ELT](#batch-etl-elt)).

## Le détour par Cloud Storage et Dataflow

Datastream dépose les événements en fichiers Avro ou JSON, un dossier par table, avec rotation à chaque changement de schéma. Une **notification Pub/Sub** sur le bucket déclenche un modèle Dataflow, qui charge la destination :

| Modèle Dataflow | Destination | Ce qu'il faut savoir |
|---|---|---|
| Datastream to BigQuery | BigQuery | Table de préparation partitionnée puis `MERGE` vers la réplique ; transformation par fonction JavaScript ou Python ; sources MySQL et Oracle seulement ; clé primaire exigée |
| Datastream to Spanner | Spanner | Conçu pour une migration : tables à créer d'avance, pas de propagation des changements de schéma, tables fantômes pour l'ordre des écritures |
| [!PREVERSION] Datastream to MySQL or PostgreSQL | Cloud SQL, AlloyDB, toute base MySQL ou PostgreSQL | Tables à créer d'avance, pas de DDL ; les versions de ligne arrivées en retard sont ignorées |

Ce chemin se justifie quand il faut transformer avant l'arrivée, alimenter une base transactionnelle, ou conserver le journal brut des changements pour d'autres consommateurs (voir [Streaming](#streaming) et [Choisir un moteur de traitement](#choisir-un-moteur)).

## Connectivité réseau

| Méthode | Principe | À savoir |
|---|---|---|
| **Liste d'adresses IP autorisées** | La source accepte les adresses publiques de Datastream pour la région | Source exposée sur une IP publique ; activer SSL sur la base, la connexion n'est pas chiffrée par défaut |
| **Tunnel SSH direct** (*forward SSH*) | Connexion chiffrée par un bastion | Bande passante limitée ; bastion à maintenir |
| **Appairage VPC** | Configuration de connectivité privée appairée à un VPC | Plage `/29` libre à fournir ; pas d'appairage transitif : un **proxy inverse** est nécessaire pour Cloud SQL ou une source hors du VPC appairé |
| **Interfaces [Private Service Connect](#private-service-connect)** | Configuration de connectivité privée par un rattachement réseau (*network attachment*) dans le VPC | Rattachement non modifiable après création ; une configuration par appairage ne se convertit pas |

Une source sur site passe par la connectivité privée, avec [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect) entre le centre de données et le VPC. La liste d'adresses IP est réservée aux essais ou aux sources déjà publiques.

## Pièges

- **Rétention du journal** : si le flux s'arrête plus longtemps que le journal n'est conservé, la reprise exige un nouveau *backfill*. MySQL : `binlog_format=ROW`, rétention recommandée de 7 jours (`binlog_expire_logs_seconds=604800`), et réplication par **GTID** dès qu'il existe des répliques ou une bascule, car le numérotage des fichiers *binlog* change de nœud en nœud. Oracle : mode `ARCHIVELOG`, journalisation supplémentaire (*supplemental logging*), journaux archivés conservés 4 jours au minimum, 7 recommandés.
- **Slot de réplication PostgreSQL** : il retient le WAL jusqu'à ce que Datastream le confirme. Un flux en échec, en pause ou supprimé sans supprimer le slot fait grossir le WAL **sans limite**, jusqu'à saturer le disque de la production. Surveiller l'espace disque du WAL, et éviter les transactions longues (`statement_timeout`, `idle_in_transaction_session_timeout`).
- **Clés primaires** : sans clé, pas de mode fusion. Côté PostgreSQL, `REPLICA IDENTITY FULL` sur une table de plus de 16 colonnes dépasse la limite de colonnes d'une clé de `MERGE` BigQuery et casse le flux ; préférer la clé primaire, ou un index `UNIQUE NOT NULL` avec `REPLICA IDENTITY USING INDEX`. Une clé de type `FLOAT` ou `REAL` empêche la réplication de la table, et on n'ajoute ni ne retire de clé à une table déjà répliquée.
- **Changements de schéma** : une colonne ajoutée est créée dans BigQuery, pour les nouvelles lignes seulement ; une colonne supprimée reste, remplie de `NULL` ; un renommage devient une suppression plus un ajout. Un changement de type, ou la suppression d'une colonne au milieu d'une table, peut corrompre les données. Les `TRUNCATE` et les suppressions en cascade sont ignorés.
- **Ordre et doublons** : la livraison est au moins une fois, sans ordre garanti. Les métadonnées d'événement servent à trier et à dédoublonner quand on lit les fichiers soi-même.
- **Tête de file PostgreSQL** : un flux PostgreSQL utilise un seul slot ; une table très active retarde toutes les autres. Isoler les tables à fort débit dans un flux à part.

> [!WARNING]
> Le volume facturé par Datastream est une représentation interne des données, souvent plusieurs fois plus volumineuse que la base : estimer le coût d'après la taille des tables le sous-évalue. Les fusions BigQuery s'y ajoutent.

## Alternatives au-delà de Datastream

- **Flux de modifications Spanner** : suivent des tables ou des colonnes, avec une rétention réglable de 1 à 30 jours (7 par défaut). Lecture par l'API Spanner, par Dataflow (connecteur SpannerIO et modèles vers BigQuery, Pub/Sub ou Cloud Storage), par un connecteur Kafka fondé sur Debezium, ou par Datastream.
- **Flux de modifications Bigtable** : activés par table, avec une rétention de 1 à 7 jours ; modèles Dataflow vers BigQuery et vers Pub/Sub.
- **Debezium et Kafka** : Managed Service for Apache Kafka propose des clusters Kafka Connect avec des connecteurs sources PostgreSQL (Cloud SQL ou générique) maintenus par Google. Les plugins personnalisés n'y sont pas acceptés : pour un autre connecteur Debezium (MySQL, Oracle, SQL Server), il faut héberger soi-même Kafka Connect, sur GKE par exemple.

## Alternatives en logiciel libre

- **Debezium** (Apache 2.0) : la référence du CDC, déjà décrite plus haut avec Kafka ; **Debezium Server** s'en passe et publie directement les changements dans Pub/Sub, Kinesis ou Pulsar.
- **Apache Flink CDC** (Apache 2.0) : les connecteurs Debezium intégrés à Flink, avec *backfill* initial et capture continue dans un même job ; il écrit vers Kafka, Iceberg, Doris ou StarRocks et propage les changements de schéma.
- **Maxwell** (Apache 2.0) : lit le *binlog* MySQL et émet chaque changement en JSON vers Kafka, Pub/Sub ou BigQuery ; plus simple que Debezium, limité à MySQL et MariaDB.
- **Apache SeaTunnel** (Apache 2.0) : moteur d'intégration avec des sources CDC (MySQL, PostgreSQL, Oracle, SQL Server) et des destinations comme BigQuery ou Iceberg ; un équivalent autogéré de Datastream, à déployer et superviser.
- **Réplication logique PostgreSQL** et **pglogical** (licence PostgreSQL) : réplication native entre bases PostgreSQL ; elle alimente une réplique transactionnelle, pas un entrepôt, et partage le piège du slot qui retient le WAL.
