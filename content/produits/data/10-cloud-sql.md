---
title: Cloud SQL
subgroup: Bases de données
icon: produits/cloud-sql
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 156, y: 16, w: 590, h: 268}
  nodes:
    users: {label: Utilisateurs, sub: "web, mobile", external: true, x: 8, y: 120, w: 124}
    run: {label: Cloud Run, sub: service HTTPS, icon: produits/cloud-run, x: 180, y: 120, w: 160}
    sql: {label: Cloud SQL, sub: instance primaire, icon: produits/cloud-sql, focus: true, x: 380, y: 110, w: 180, h: 70}
    replica: {label: Réplica lecture, sub: autre zone, icon: produits/cloud-sql, x: 380, y: 222, w: 180, h: 50}
    backup: {label: Sauvegardes, sub: journaux PITR, icon: categories/storage, x: 600, y: 36, w: 142}
    ds: {label: Datastream, sub: changements, icon: categories/data-analytics, x: 600, y: 120, w: 142}
    bq: {label: BigQuery, sub: analyse, icon: produits/bigquery, x: 600, y: 222, w: 142}
  flows:
    - {from: users, to: run, text: "Les utilisateurs appellent le service applicatif, qui seul connaît la base"}
    - {from: run, to: sql, text: "Le connecteur de langage (ou le Cloud SQL Auth Proxy) ouvre une connexion chiffrée, autorisée par IAM, sans exposer d'adresse IP publique"}
    - {from: sql, to: replica, text: "Réplication vers un réplica de lecture qui absorbe les requêtes en lecture seule"}
    - {from: sql, to: backup, from_offset: -20, text: "Sauvegardes automatiques et journaux de transactions, qui permettent la restauration à un instant donné"}
    - {from: sql, to: ds, from_offset: 10, text: "Datastream lit le journal de réplication de l'instance : la capture des changements ne passe pas par des requêtes"}
    - {from: ds, to: bq, text: "Les changements sont répliqués en continu dans des tables BigQuery, pour l'analyse"}
captures:
  - image: https://docs.cloud.google.com/static/sql/images/pg-si-dashboard-1.png
    page: https://docs.cloud.google.com/sql/docs/postgres/use-system-insights
    legende: "Page d'une instance PostgreSQL : menu de l'instance (Cloud SQL Studio, sauvegardes, réplicas...), frise des événements et jauges de System insights"
  - image: https://docs.cloud.google.com/static/sql/images/insights-dashboard-postgres-edition-ep.png
    page: https://docs.cloud.google.com/sql/docs/postgres/using-query-insights
    legende: "Query insights : charge de la base par temps d'exécution, puis les requêtes qui y contribuent le plus, avec leur latence moyenne et leur nombre d'appels"
docs:
  Page produit: https://cloud.google.com/sql
  Documentation: https://docs.cloud.google.com/sql/docs
  Éditions: https://docs.cloud.google.com/sql/docs/mysql/editions-intro
  API REST (Admin API): https://docs.cloud.google.com/sql/docs/mysql/admin-api/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/sql
  Connecteurs de langage: https://docs.cloud.google.com/sql/docs/mysql/language-connectors
  Cloud SQL Auth Proxy: https://docs.cloud.google.com/sql/docs/mysql/sql-proxy
  Quotas et limites: https://docs.cloud.google.com/sql/docs/mysql/quotas
  Tarifs: https://cloud.google.com/sql/pricing
  Notes de version: https://docs.cloud.google.com/sql/docs/mysql/release-notes
---

## Ce que c'est

Service de bases de données relationnelles géré, pour trois moteurs du marché : **MySQL**, **PostgreSQL** et **SQL Server**. Google administre la machine, le système, les correctifs et les sauvegardes ; le moteur reste celui d'origine, avec ses outils et ses clients habituels.

- **Une instance, une machine.** Chaque instance est une VM avec un disque persistant et une adresse IP statique. On choisit son nombre de vCPU et sa mémoire ; le stockage s'étend automatiquement, jusqu'à 64 To.
- **Versions** : MySQL 5.6 à 9.7, PostgreSQL 12 à 18, SQL Server 2017 à 2025. À partir de MySQL 8.4 et de PostgreSQL 16, l'édition Enterprise Plus est celle retenue par défaut.
- **Deux éditions.** *Enterprise* couvre les besoins courants ; *Enterprise Plus* ajoute le cache de données sur SSD local, les pools de lecture gérés, le *Managed Connection Pooling*, la reprise après sinistre inter-régions, une maintenance sans coupure perceptible et une rétention des journaux jusqu'à 35 jours (7 jours en Enterprise).
- **Disponibilité** : en configuration haute disponibilité, une VM de secours dans une autre zone bascule automatiquement. SLA de 99,95 % en Enterprise (hors maintenance) et 99,99 % en Enterprise Plus (maintenance comprise).
- **Réplication** : réplicas de lecture dans la même région ou ailleurs, réplication depuis ou vers un serveur externe.
- **Reprise** : sauvegardes automatiques, restauration à un instant donné à partir des journaux de transactions, clonage d'instance.
- **Connexion** : adresse IP privée dans un VPC (ou Private Service Connect), Cloud SQL Auth Proxy et connecteurs de langage, authentification des utilisateurs de base par IAM.
- **Facturation** : vCPU, mémoire, stockage provisionné, adresses IP et sortie réseau, à la seconde.

> [!WARNING]
> Une instance avec adresse IP publique et réseaux autorisés est exposée à Internet. Préférer l'IP privée, le Cloud SQL Auth Proxy ou un connecteur de langage : la connexion est chiffrée et l'autorisation passe par IAM, sans mot de passe dans le code.

## À quoi ça sert

- Base transactionnelle d'une application régionale : commandes, comptes, catalogue, tout ce qui demande des transactions ACID et du SQL standard.
- Reprise d'une base MySQL, PostgreSQL ou SQL Server existante sans réécriture, souvent via Database Migration Service.
- Stockage derrière des services Cloud Run, GKE ou Compute Engine, avec un connecteur par langage.
- Source de capture des changements pour Datastream, vers [BigQuery](#bigquery).

**À éviter** quand les écritures dépassent ce qu'une seule machine encaisse, ou quand l'application doit être répartie sur plusieurs régions en écriture : préférer [Spanner](#spanner). Pour un PostgreSQL très sollicité, ou pour croiser transactions et requêtes analytiques dans la même base, préférer [AlloyDB](#alloydb). Pour l'analyse sur de gros volumes, préférer BigQuery (voir [Choisir une base de données](#choisir-une-base)).

## Alternatives en logiciel libre

- **PostgreSQL**, **MySQL**, **MariaDB** : les moteurs eux-mêmes, autohébergés ; c'est la même base, sans l'exploitation.
- **CloudNativePG** : opérateur Kubernetes pour PostgreSQL (bascule, sauvegardes, réplicas), l'équivalent le plus direct d'une instance gérée.
- **Percona Operator for MySQL** et **Percona XtraDB Cluster** : haute disponibilité MySQL sur Kubernetes ou sur machines.
- **Patroni** : bascule automatique d'un groupe PostgreSQL, appuyée sur etcd ou Consul.
- **PgBouncer** : mutualisation des connexions PostgreSQL, ce que fait le *Managed Connection Pooling*.
- **pgBackRest**, **Percona XtraBackup** : sauvegardes et restauration à un instant donné.
