---
title: Bigtable
subgroup: Bases de données
icon: categories/databases
aka: Cloud Bigtable
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 150, y: 16, w: 596, h: 288}
  nodes:
    src: {label: Capteurs, sub: "IoT, journaux", external: true, x: 8, y: 60, w: 124}
    ps: {label: Pub/Sub, sub: événements, icon: categories/data-analytics, x: 172, y: 40, w: 150}
    df: {label: Dataflow, sub: écriture continue, icon: categories/data-analytics, x: 172, y: 140, w: 170}
    bt: {label: Bigtable, sub: cluster us-central1, icon: categories/databases, focus: true, x: 380, y: 96, w: 190, h: 70}
    bt2: {label: Bigtable, sub: cluster europe-west1, icon: categories/databases, x: 380, y: 228, w: 190, h: 56}
    run: {label: Cloud Run, sub: lecture par clé, icon: produits/cloud-run, x: 172, y: 236, w: 160}
    bq: {label: BigQuery, sub: via Data Boost, icon: produits/bigquery, x: 604, y: 96, w: 140}
  flows:
    - {from: src, to: ps, text: "Les capteurs publient leurs relevés dans un sujet Pub/Sub"}
    - {from: ps, to: df, text: "Dataflow consomme le flux et compose la clé de ligne : identifiant de l'appareil, puis horodatage"}
    - {from: df, to: bt, text: "Écriture des cellules horodatées dans la famille de colonnes de la table"}
    - {from: bt, to: bt2, text: "Réplication automatique vers le second cluster de l'instance ; un profil d'application décide du routage"}
    - {from: run, to: bt, to_offset: -60, text: "Le service lit une plage de lignes par préfixe de clé, en quelques millisecondes"}
    - {from: bt, to: bq, text: "Data Boost exécute les gros balayages sur un calcul serverless, sans consommer les nœuds du cluster"}
captures:
  - image: https://docs.cloud.google.com/static/bigtable/img/example_tourist_poi_query.png
    page: https://docs.cloud.google.com/bigtable/docs/work-with-geo-data
    legende: "Bigtable Studio : une requête GoogleSQL sur une table et ses résultats, dans la console"
  - image: https://docs.cloud.google.com/static/bigtable/img/keyvis-scan-example.png
    page: https://docs.cloud.google.com/bigtable/docs/keyvis-getting-started
    legende: "Key Visualizer : carte de chaleur des accès, les clés de ligne en ordonnée et le temps en abscisse"
docs:
  Page produit: https://cloud.google.com/bigtable
  Documentation: https://docs.cloud.google.com/bigtable/docs
  Conception de la clé de ligne: https://docs.cloud.google.com/bigtable/docs/schema-design
  GoogleSQL pour Bigtable: https://docs.cloud.google.com/bigtable/docs/googlesql-overview
  Interface HBase: https://docs.cloud.google.com/bigtable/docs/hbase-bigtable
  API de données (gRPC): https://docs.cloud.google.com/bigtable/docs/reference/data/rpc
  API d'administration (REST): https://docs.cloud.google.com/bigtable/docs/reference/admin/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/bigtable
  Référence cbt: https://docs.cloud.google.com/bigtable/docs/cbt-reference
  Bibliothèques clientes: https://docs.cloud.google.com/bigtable/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/bigtable/latest
  Quotas et limites: https://docs.cloud.google.com/bigtable/quotas
  Tarifs: https://cloud.google.com/bigtable/pricing
  Notes de version: https://docs.cloud.google.com/bigtable/docs/release-notes
---

## Ce que c'est

Base NoSQL à **colonnes larges**, conçue pour un très haut débit de lectures et d'écritures par clé, à quelques millisecondes. C'est le système décrit par l'article Bigtable de Google, offert en service géré.

- **Modèle de données** : une table est une carte triée par **clé de ligne**. Les colonnes sont regroupées en *familles de colonnes* ; chaque intersection ligne–colonne contient des cellules horodatées, donc plusieurs versions. Les colonnes non utilisées ne consomment rien : la table est creuse.
- **Architecture** : une *instance* contient un ou plusieurs *clusters* (un par zone), chacun composé de *nœuds*. La table est découpée en *tablets* de lignes contiguës, stockés sur Colossus au format SSTable. Les nœuds ne contiennent pas les données, seulement des pointeurs : rééquilibrer ou remplacer un nœud est rapide et ne perd rien.
- **Réplication** : ajouter un cluster suffit, la réplication démarre seule. Les *profils d'application* décident du routage : un seul cluster (cohérence forte) ou le cluster disponible le plus proche (cohérence à terme, ou lecture de ses propres écritures selon la configuration).
- **Disponibilité** : 99,9 % pour une instance à un seul cluster ou en routage mono-cluster, 99,99 % avec routage multi-cluster, 99,999 % à partir de trois régions.
- **Performance** : un nœud SSD sert jusqu'à 17 000 lectures et 14 000 écritures par seconde, à moins de 5 ms.
- **Accès** : bibliothèques clientes, extension de la bibliothèque **Apache HBase** pour Java, CLI `cbt`, et requêtes **GoogleSQL** depuis Bigtable Studio.
- **Calcul séparé** : *Data Boost* exécute les gros travaux de lecture sur un calcul serverless, sans toucher aux nœuds qui servent l'application.
- **Deux éditions** : *Enterprise* pour l'usage courant, *Enterprise Plus* pour la lecture ponctuelle sous la milliseconde (niveau en mémoire), une densité de stockage par nœud plus élevée et le SQL sur Data Boost.
- **Facturation** : nœuds provisionnés (ou autoscaling), stockage SSD ou HDD, sauvegardes et sortie réseau.

> [!WARNING]
> Tout se joue sur la **clé de ligne**. Une clé qui commence par un horodatage ou un compteur envoie toutes les écritures du moment sur le même *tablet*, donc sur un seul nœud : le cluster entier attend ce nœud. Faire précéder l'horodatage d'un identifiant bien réparti, et vérifier le résultat dans Key Visualizer.

## À quoi ça sert

- Séries temporelles à gros volume : supervision, compteurs, relevés IoT, cours financiers.
- Historiques par entité lus par plage de clés : parcours d'un utilisateur, transactions d'un compte, événements d'un appareil.
- Moteur de stockage de traitements par lots ou en flux (Dataflow, Spark) et de charges d'apprentissage.
- Migration depuis Apache HBase ou Cassandra, quand on veut garder le modèle sans exploiter le cluster.

**À éviter** quand il faut des transactions sur plusieurs lignes, des jointures ou des index secondaires généraux : préférer [Spanner](#spanner) ou [Cloud SQL](#cloud-sql). À éviter aussi pour l'analyse ad hoc sur l'historique complet, qui revient moins cher dans [BigQuery](#bigquery), et pour des valeurs de plus de quelques mégaoctets, qui ont leur place dans Cloud Storage. Voir [Choisir une base de données](#choisir-une-base).

## Alternatives en logiciel libre

- **Apache HBase** : la mise en œuvre libre du même modèle, sur HDFS ; Bigtable en propose d'ailleurs l'API.
- **Apache Cassandra** : colonnes larges également, avec une réplication multi-nœuds sans maître.
- **Apache Accumulo** : proche de HBase, avec en plus une sécurité au niveau de la cellule.
- **Apache Phoenix** : couche SQL au-dessus de HBase, comme GoogleSQL au-dessus de Bigtable.
- **Apache HBase + OpenTSDB** : la variante spécialisée séries temporelles.
