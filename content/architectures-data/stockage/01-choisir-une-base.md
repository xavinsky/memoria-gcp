---
title: Choisir une base de données
---

Le choix se fait d'abord sur l'**usage** : analyse sur de gros volumes, transactions d'une application, accès clé-valeur à très faible latence, ou cache. Le modèle de données, l'échelle et la portée géographique départagent ensuite les candidats.

![Arbre de décision : du besoin au service de stockage](../../svg/choix-base-de-donnees.svg)

## Matrice de choix

| Service | Modèle | Échelle | Cohérence | Cas typiques |
|---|---|---|---|---|
| **[BigQuery](#bigquery)** | Entrepôt analytique, colonnes | Pétaoctets, serverless | Forte | Analyse, reporting, BI, ML en SQL |
| **[Cloud SQL](#cloud-sql)** | Relationnel (MySQL, PostgreSQL, SQL Server) | Verticale, réplicas en lecture | Forte, ACID | Application transactionnelle régionale, migration « lift and shift » |
| **[AlloyDB](#alloydb)** | Relationnel compatible PostgreSQL | Verticale, pools de lecture | Forte, ACID | PostgreSQL à forte charge, requêtes analytiques sur données transactionnelles |
| **[Spanner](#spanner)** | Relationnel distribué | Horizontale, multirégionale | Forte, externe | Transactions à l'échelle mondiale, très haute disponibilité |
| **[Bigtable](#bigtable)** | NoSQL colonnes larges, clé-valeur | Horizontale, pétaoctets | Forte au sein d'un cluster | Séries temporelles, IoT, finance, très haut débit à faible latence |
| **[Firestore](#firestore)** | NoSQL documents | Serverless | Forte | Applications web et mobiles, synchronisation temps réel |
| **[Memorystore](#memorystore)** | Clé-valeur en mémoire (Valkey, Redis ; Memcached [!DECONSEILLE], obsolète, à remplacer par Valkey) | Mémoire d'une instance ou d'un cluster | Selon le moteur | Cache, sessions, classements |

## Questions qui départagent

- **Relationnel, mais régional ou mondial ?** Cloud SQL et AlloyDB montent en puissance sur une machine ; Spanner répartit les données sur plusieurs nœuds et régions sans sacrifier la cohérence.
- **Transactions ou analyse ?** Une base transactionnelle sert des lectures et écritures unitaires ; BigQuery sert des balayages de gros volumes. Les deux se combinent : requête fédérée de BigQuery vers Cloud SQL, ou réplication par Datastream.
- **Bigtable ou BigQuery pour des séries temporelles ?** Bigtable pour des lectures et écritures à la milliseconde par clé ; BigQuery pour des agrégations sur l'historique.

> [!WARNING]
> Bigtable accepte GoogleSQL en lecture, mais pas les transactions multi-lignes : la conception de la **clé de ligne** détermine les performances. Une clé qui commence par un horodatage concentre les écritures sur un seul nœud.

## Alternatives en logiciel libre

- **PostgreSQL** (licence PostgreSQL), **MySQL** et **MariaDB** (GPL v2) : les moteurs de Cloud SQL et le socle d'AlloyDB, à exploiter soi-même (haute disponibilité, sauvegardes, mises à jour).
- **YugabyteDB** (Apache 2.0 pour le moteur) et **TiDB** (Apache 2.0) : SQL distribué avec transactions et réplication par consensus, compatible PostgreSQL pour le premier, MySQL pour le second ; l'alternative à Spanner, sans ses horloges atomiques ni sa cohérence externe.
- **ClickHouse** (Apache 2.0) : base analytique en colonnes, très rapide sur les agrégats ; elle occupe la place de BigQuery, avec des nœuds à dimensionner au lieu d'un service sans serveur.
- **Apache HBase** et **Apache Cassandra** (Apache 2.0) : colonnes larges et accès par clé à faible latence ; HBase suit le modèle de Bigtable, qui en propose l'API, Cassandra réplique sans maître entre centres de données.
- **FerretDB** (Apache 2.0) et **Apache CouchDB** (Apache 2.0) : le modèle document ; FerretDB rejoue le protocole MongoDB sur PostgreSQL, CouchDB synchronise des clients hors ligne, sans l'intégration mobile de Firestore.
- **Valkey** (BSD 3-Clause) : cache et structures en mémoire, le moteur que Memorystore exécute.
