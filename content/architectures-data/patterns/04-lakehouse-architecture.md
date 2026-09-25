---
title: "Lakehouse : tables ouvertes et gouvernance"
id: lakehouse-architecture
---

Un *lakehouse* garde une seule copie des données, en fichiers ouverts dans un stockage objet, et leur ajoute ce qu'offre un entrepôt : tables transactionnelles, schéma, sécurité fine, performances. Quatre briques le composent : le **stockage objet**, un **format de table ouvert** ([Iceberg](#lexterm-iceberg-apache-iceberg)), un **catalogue partagé** qui tient les métadonnées, et **plusieurs moteurs** qui lisent et écrivent les mêmes tables. La gouvernance — recherche, lignage, qualité, droits — s'applique au-dessus, quel que soit le moteur.

![Architecture d'un lakehouse : moteurs, catalogue, stockage en couches et gouvernance](../../svg/lakehouse-architecture.svg)

## Les briques sur Google Cloud

| Brique | Service | Rôle |
|---|---|---|
| Stockage | [Cloud Storage](#cloud-storage) | Fichiers Parquet et métadonnées Iceberg, dans des buckets du client |
| Format | Apache Iceberg (V2 ; V3 [!PREVERSION], V1 non pris en charge) | Instantanés, évolution du schéma et du partitionnement, *time travel* |
| Catalogue | Catalogue d'exécution de [Lakehouse](#lakehouse) (BigLake metastore) | Source de vérité des tables ; point de terminaison **Iceberg REST**, point **Hive** [!PREVERSION], catalogue Iceberg adossé à BigQuery |
| Moteurs | [BigQuery](#bigquery), [Managed Service for Apache Spark](#managed-service-for-apache-spark), Flink, Trino | Calcul séparé du stockage, facturé par le moteur qui exécute |
| Gouvernance | [Knowledge Catalog](#knowledge-catalog) | Catalogage automatique des tables, découverte, lignage, qualité, profil, glossaire |
| Sécurité | IAM, *policy tags*, sécurité des lignes, masquage | Droits portés par BigQuery et le catalogue, jamais par l'accès direct au bucket |

Depuis BigQuery, une table du catalogue se nomme `PROJECT_ID.CATALOG.NAMESPACE.TABLE` ; depuis Spark ou Trino, l'entrepôt (*warehouse*) se désigne par `bl://projects/PROJECT_ID/catalogs/CATALOG_ID`. Le produit s'appelle Lakehouse, mais l'API, `gcloud` et les rôles IAM gardent le préfixe `biglake`.

## Choisir le type de table

La question qui tranche est celle du moteur qui écrit : c'est lui qui gère les fichiers, les autres ne font que lire.

![Arbre de décision : du moteur qui écrit au type de table](../../svg/choix-table-lakehouse.svg)

| Type de table | Stockage | Qui écrit | Autres moteurs | Sécurité fine | Maintenance des fichiers |
|---|---|---|---|---|---|
| **Table native BigQuery** | Stockage BigQuery | BigQuery | Lecture par l'API Storage Read (connecteurs Spark, Trino) | Colonnes, lignes, masquage, vues autorisées | Aucune |
| **Table Iceberg gérée** par BigQuery | Vos buckets, Iceberg + Parquet | BigQuery seul (DML, API Storage Write) | Lecture de l'instantané de métadonnées exporté | Colonnes et masquage ; ni sécurité des lignes, ni vues autorisées, ni vues matérialisées | Automatique : compactage, *clustering*, ramasse-miettes, facturés en DCU |
| **Table Iceberg du catalogue** (REST) | Vos buckets, Iceberg | Moteurs open source ; BigQuery en DML [!PREVERSION] | Lecture et écriture par tout client Iceberg REST | IAM au niveau catalogue, espace de noms ou table | Par vous, ou par Google [!PREVERSION] |
| [!PREVERSION] **Table Hive du catalogue** | Vos buckets, Parquet, ORC, Avro | Spark, Hive | BigQuery en lecture | IAM au niveau table | Par vous |
| **Table BigLake** (externe avec connexion) | Cloud Storage, S3 ou Azure (BigQuery Omni) | Le producteur des fichiers ; BigQuery lit seulement | Connecteurs BigQuery, avec les mêmes contrôles | Colonnes, lignes ; masquage sur Cloud Storage | Par le producteur des fichiers |
| [!PREVERSION] **Accès multicloud** | S3 ou Cloud Storage, catalogue AWS Glue, Databricks Unity, Snowflake Horizon | Le propriétaire du catalogue distant | Lecture par Iceberg REST | IAM au niveau table | Hors Google Cloud |

La documentation Lakehouse recommande par défaut les **tables Iceberg du catalogue, servies par le point Iceberg REST** : c'est la configuration la plus interopérable entre les moteurs open source et BigQuery. Quand BigQuery est le seul à écrire, la table Iceberg gérée offre la même expérience qu'une table native, avec les fichiers dans vos buckets.

> [!WARNING]
> Les **tables externes Iceberg** [!DECONSEILLE] de BigQuery (métadonnées gérées hors de Google Cloud, lecture seule) sont déconseillées par la documentation, qui oriente vers le catalogue d'exécution et son accès multicloud.

Créer une table Iceberg gérée par BigQuery, dans un bucket accessible au compte de service de la connexion :

```sql
CREATE TABLE DATASET.ventes (
  id INT64,
  montant NUMERIC,
  jour DATE
)
CLUSTER BY id
WITH CONNECTION `PROJECT_ID.REGION.CONNECTION`
OPTIONS (
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://BUCKET/ventes');

-- Publier un instantané de métadonnées Iceberg pour les autres moteurs
EXPORT TABLE METADATA FROM DATASET.ventes;
```

## Lakehouse ou BigQuery seul ?

- **Un seul moteur, BigQuery ?** Les tables natives sont plus simples, plus rapides et portent toute la sécurité fine. Le lakehouse ne se justifie pas (voir [Choisir une base de données](#choisir-une-base)).
- **Des équipes Spark, Flink ou Trino écrivent aussi ?** Le catalogue partagé évite deux copies et leur synchronisation : c'est le cas d'école.
- **Les données doivent-elles rester dans un format ouvert ?** Réversibilité, obligation de garder les fichiers dans ses propres buckets, lecture par un outil tiers : tables Iceberg, gérées par BigQuery si lui seul écrit.
- **Un metastore Hive existe déjà ?** Le point Hive du catalogue le remplace sans réécrire les jobs.
- **Les données restent chez un autre fournisseur ?** L'accès multicloud interroge un catalogue Glue ou Unity sans migration, ou une table BigLake lit S3 ou Azure par BigQuery Omni.
- **Faut-il de la sécurité au niveau ligne ?** Elle est disponible sur les tables natives et les tables BigLake, pas sur les tables Iceberg gérées ni sur les tables du catalogue REST : servir la couche exposée en tables natives, ou filtrer par des vues.

## Organiser en couches (médaillon)

L'architecture **médaillon** range les données par niveau de qualité :

| Couche | Contenu | Stockage typique | Écrit par |
|---|---|---|---|
| **Bronze** (brut) | Données telles qu'ingérées, historisées | Tables Iceberg du catalogue, ou tables BigLake sur les fichiers déposés | Spark, [Dataflow](#dataflow), [Datastream](#datastream) |
| **Argent** (nettoyé) | Données dédoublonnées, typées, conformes | Tables Iceberg (catalogue ou gérées par BigQuery) | Spark, BigQuery avec [Dataform](#dataform) |
| **Or** (exposé) | Agrégats et tables métier, prêts pour la BI | Tables natives BigQuery ou Iceberg gérées | BigQuery |

La couche or est en général servie par BigQuery, pour les performances et la sécurité fine. Les traitements entre couches relèvent de [Batch ETL / ELT](#batch-etl-elt) et de [Choisir un moteur de traitement](#choisir-un-moteur), et leur enchaînement de l'[orchestration](#orchestration). Le découpage en datasets et projets est détaillé dans [Organiser BigQuery](#organiser-bigquery).

## Gouvernance avec Knowledge Catalog

- **Catalogage** : les tables enregistrées dans le catalogue d'exécution sont inscrites automatiquement dans Knowledge Catalog, comme les datasets et tables BigQuery.
- **Découverte** : une analyse de découverte parcourt un bucket et crée des tables BigLake ou externes pour les données structurées, des **tables d'objets** pour les fichiers non structurés (réglages ci-dessous).
- **Lignage** : suivi jusqu'à la colonne, alimenté par BigQuery, Spark, Datastream et Cloud Data Fusion ; il sert l'analyse d'impact avant un changement de schéma.
- **Qualité et profil** : analyses planifiées sur les tables BigQuery et les tables du catalogue Iceberg REST, résultats publiés dans le catalogue.
- **Sens métier** : glossaires, descriptions de colonnes, aspects.

Pour un *data mesh*, où chaque domaine métier produit et publie ses données :

- [!PREVERSION] les **domaines de données** regroupent les ressources par domaine, indépendamment des dossiers et projets, avec un propriétaire par domaine ;
- les **produits de données** empaquettent des assets BigQuery avec leur documentation, leur contrat et des groupes d'accès que le consommateur demande en libre-service ;
- les *lakes*, *zones* et *assets* regroupent logiquement des buckets et des datasets (détail ci-dessous).

Côté ressources, un projet par domaine producteur garde la facturation et les droits séparés (voir [Organiser BigQuery](#organiser-bigquery)) ; le partage BigQuery (*BigQuery sharing*) publie des datasets vers d'autres projets ou organisations sans copie.

### Lacs, zones et assets

| Objet | Ce qu'il regroupe | Contraintes |
|---|---|---|
| **Lac** (*lake*) | Les données d'un domaine, réparties sur plusieurs projets et services de stockage | Une région ; un service Dataproc Metastore rattaché en option, qui ne sert qu'un lac |
| **Zone brute** (*raw*) | Données à traiter avant de les consommer, dans n'importe quel format, souvent venues de sources externes | Type de zone immuable ; les assets sont tous régionaux ou tous multirégionaux |
| **Zone organisée** (*curated*) | Données prêtes pour l'analyse et une large consommation | Fichiers Cloud Storage en Parquet, Avro ou ORC, rangés en arborescence compatible Hive |
| **Asset** | Un bucket Cloud Storage ou un dataset BigQuery rattaché à une zone | Pour un bucket : lecture directe par l'API de stockage, ou gérée par les API BigQuery (mode `MANAGED`) |

- Le démarrage rapide *Build a data mesh* fait du lac le **domaine**, et des zones les équipes ou les contrats de données à l'intérieur du domaine, avec au moins une zone brute et une zone organisée par domaine. La zone brute recouvre la couche bronze, la zone organisée les couches argent et or.
- L'identifiant d'une zone devient le nom d'un dataset BigQuery : il doit être unique dans le projet, même entre deux lacs.
- La découverte se règle sur la zone (motifs d'inclusion et d'exclusion, options CSV et JSON, planning cron, toutes les 60 minutes par défaut et jamais plus souvent) ; un asset hérite de ce réglage sauf s'il porte le sien.
- La documentation actuelle ne traite des lacs et des zones que dans ce démarrage rapide et dans la référence de l'API (`lakes`, `zones`, `assets`). Ses pages de concepts organisent le *data mesh* par **domaines de données**, indépendants des projets et des dossiers, qui accueillent projets, datasets, tables et produits de données, et par **produits de données** ; la découverte s'y fait par des analyses autonomes. Un nouveau lac se construit donc sur domaines, produits de données et analyses de découverte ; lacs et zones se rencontrent dans des environnements existants.

### Régler la découverte

Une analyse de découverte (*DataScan* de type `data-discovery`, appelée aussi découverte autonome) vise un bucket et publie ses tables dans un dataset BigQuery qui porte le nom du bucket, dans le projet du bucket ou un autre.

| Réglage | Options |
|---|---|
| **Périmètre** | Motifs *glob* d'inclusion et d'exclusion sur le nom des objets, l'exclusion appliquée d'abord : `*` ne traverse pas les `/`, `**` les traverse, plus `?`, `[a-z]`, `{a,b}` |
| **Formats structurés** | Parquet, Avro, ORC, JSON délimité par des sauts de ligne, CSV sans ligne de commentaire ; compression interne (Snappy, gzip…) ou gzip et bzip2 pour CSV et JSON. Ni Iceberg ni Delta Lake |
| **Non structurés** | Images, documents, audio, vidéo : une table d'objets par dossier de même format |
| **Type de table** | BigLake si une connexion BigQuery est fournie, table externe sinon |
| **Déclenchement** | Planning cron, à la demande, ou exécution unique supprimée après un TTL (24 heures par défaut) |
| **CSV et JSON** | Délimiteur, lignes d'en-tête, encodage, inférence de types désactivable |

```bash
gcloud dataplex datascans create data-discovery ventes-lac \
  --project=PROJECT_ID --location=REGION \
  --data-source-resource=//storage.googleapis.com/projects/PROJECT_ID/buckets/BUCKET \
  --storage-include-patterns="ventes/**" --storage-exclude-patterns="**/_tmp/**" \
  --bigquery-publishing-table-type=BIGLAKE \
  --bigquery-publishing-connection=projects/PROJECT_ID/locations/REGION/connections/CONNECTION \
  --schedule="0 * * * *"

gcloud dataplex datascans run ventes-lac --location=REGION   # relancer sans attendre le planning
```

Un dossier donne une table : la découverte ne regroupe que des fichiers de même format, de schémas compatibles, sous des clés de partition cohérentes (`year=YYYY/month=MM/`). **Un fichier ou une table n'apparaît pas ?** Vérifier dans cet ordre :

1. **Le scan a-t-il tourné** depuis le dépôt du fichier ? Historique dans la page *Cloud Storage discovery*, ou lancement à la demande.
2. **Le chemin passe-t-il les motifs ?** Un `*` qui aurait dû être `**`, une exclusion trop large, des guillemets saisis dans la console autour d'un motif.
3. **Le format est-il pris en charge ?** CSV avec commentaires, JSON non délimité, tables Iceberg ou Delta ne sont pas découverts.
4. **Le dossier est-il homogène ?** Les journaux du job dans Cloud Logging signalent `INVALID_DATA_FORMAT` (formats mélangés), `INCOMPATIBLE_DATA_SCHEMA` (types divergents, champ ajouté sans valeur par défaut dans Avro ou Parquet, fichier corrompu) et `INVALID_PARTITION_DEFINITION` (clés de partition différentes d'un chemin à l'autre). Ranger chaque schéma sous son propre préfixe.
5. **La publication a-t-elle échoué ?** `FAILED_BIGQUERY_TABLE_PUBLISH` : rôles manquants pour l'agent de service Knowledge Catalog (`service-PROJECT_NUMBER@gcp-sa-dataplex.iam.gserviceaccount.com`) ou pour le compte de service de la connexion, qui doit lire le bucket ; connexion et dataset dans deux régions différentes ; très gros buckets ou gros fichiers Avro, où la publication expire et où il faut restreindre le périmètre.
6. **Le schéma ne suit pas les fichiers ?** La table porte l'étiquette `metadata-managed-mode` à la valeur `user_managed`, dont la découverte ne touche alors pas le schéma.

## Sécurité fine

| Mécanisme | Granularité | S'applique à | Principe |
|---|---|---|---|
| **IAM** | Projet, dataset, table ; catalogue, espace de noms, table | Tous les types | Rôles BigQuery et `biglake` |
| ***Policy tags*** | Colonne | Natives, BigLake, Iceberg gérées | Taxonomie de tags posée sur les colonnes ; lecture réservée aux titulaires de *Fine-Grained Reader* sur le tag |
| **Masquage dynamique** | Colonne | Natives, BigLake sur Cloud Storage, Iceberg gérées | Valeur remplacée à la lecture par `NULL`, une valeur par défaut ou un hachage, selon l'utilisateur |
| **Politique d'accès aux lignes** | Ligne | Natives, BigLake | Filtre évalué à chaque requête, par groupe |
| **Vue autorisée** | Sous-ensemble de lignes et colonnes | Natives, BigLake | La vue lit la table ; le lecteur n'a de droit que sur la vue |
| **Dataset autorisé** | Toutes les vues d'un dataset | Idem | Autorise en bloc les vues d'un dataset sur un autre, sans les déclarer une à une |
| **Credential vending** | Chemin de fichiers | Tables du catalogue Iceberg REST | Le catalogue délivre au moteur un jeton court, limité aux fichiers de la requête |

```sql
CREATE ROW ACCESS POLICY filtre_emea
ON DATASET.ventes
GRANT TO ('group:ventes-emea@example.com')
FILTER USING (region = 'EMEA');
```

> [!WARNING]
> Un droit de lecture direct sur le bucket contourne tous ces contrôles : n'importe quel moteur lit alors les fichiers Parquet en clair. Le schéma recommandé ne donne l'accès aux fichiers qu'au compte de service de la **connexion** BigQuery, et fait passer les moteurs externes par l'API BigQuery Storage, qui applique *policy tags* et masquage.

Le détail des droits (rôles, comptes de service, périmètres VPC Service Controls) relève de l'onglet Plateforme ; la détection des données sensibles, de [Sensitive Data Protection](#sensitive-data-protection).

## Alternatives en logiciel libre

- **Apache Iceberg** (Apache 2.0) : le format de table lui-même ; les tables du catalogue d'exécution sont des tables Iceberg standard, lisibles par tout moteur qui parle Iceberg REST.
- **Apache Polaris** et **Project Nessie** (Apache 2.0) : catalogues Iceberg REST autogérés, à la place du catalogue d'exécution ; Polaris délivre aussi des identifiants temporaires limités à une table, Nessie ajoute des branches et des *commits* multi-tables.
- **Unity Catalog** (Apache 2.0, version open source) : catalogue de tables et de fichiers compatible avec l'API Iceberg REST et le metastore Hive, qui gère aussi les tables Delta Lake.
- **Trino** et **Apache Spark** (Apache 2.0) : les moteurs qui lisent et écrivent les mêmes tables ; ce sont eux, et non un service géré, qui assurent le compactage et l'expiration des instantanés.
- **Delta Lake** et **Apache Hudi** (Apache 2.0) : formats de table concurrents d'Iceberg, avec transactions et *time travel* ; Hudi vise surtout les mises à jour fréquentes issues du CDC.
- **DataHub** et **OpenMetadata** (Apache 2.0) : catalogue, lignage au niveau colonne, glossaire et contrôles de qualité, le rôle de Knowledge Catalog ; les domaines et produits de données y existent aussi.
- **Apache Ranger** (Apache 2.0) : politiques d'accès centralisées avec filtrage des lignes et masquage de colonnes, appliquées par des greffons dans Hive, Spark ou Trino ; l'équivalent des *policy tags* et des politiques d'accès aux lignes, moteur par moteur.
