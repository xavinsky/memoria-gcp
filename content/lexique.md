## ADC (Application Default Credentials)

Mécanisme par lequel les bibliothèques clientes Google trouvent seules leurs identifiants : variable `GOOGLE_APPLICATION_CREDENTIALS`, identifiants de `gcloud auth application-default login`, puis compte de service attaché à la ressource. Voir [Authentifier un appel à une API](#authentifier-un-appel).

## AlloyDB

Base relationnelle gérée compatible PostgreSQL, conçue pour les fortes charges transactionnelles et les requêtes analytiques sur les mêmes données. Voir [AlloyDB](#alloydb).

## Bigtable

Base NoSQL à colonnes larges pour de très gros volumes à faible latence : séries temporelles, IoT, finance. Voir [Bigtable](#bigtable).

## Clé de ligne (row key)

Identifiant unique d'une ligne Bigtable, qui détermine le tri des données et leur répartition entre les nœuds. Voir [Choisir une base de données](#choisir-une-base).

## Spanner

Base relationnelle distribuée à cohérence forte, qui monte en charge horizontalement jusqu'à l'échelle mondiale. Voir [Spanner](#spanner).

## Agent Runtime

Runtime géré de Gemini Enterprise Agent Platform qui exécute un agent déployé, avec ses sessions et sa mémoire. Voir [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform).

## Agent Search

Moteur de recherche et de RAG d'entreprise, anciennement Vertex AI Search ; son API reste Discovery Engine. Voir [Agent Search](#agent-search).

## BigLake

Ancien nom de Lakehouse, la couche de tables ouvertes (Iceberg) partagée entre BigQuery et les moteurs externes. Les API et la CLI gardent le préfixe `biglake`. Voir [Lakehouse](#lakehouse).

## CDC (Change Data Capture)

Capture des changements d'une base à partir de son journal de transactions, pour les rejouer ailleurs sans requête lourde sur la source. Voir [Datastream](#datastream).

## Cloud Composer

Ancien nom de Managed Service for Apache Airflow. La documentation et la CLI `gcloud composer` gardent l'ancien nom. Voir [Managed Service for Apache Airflow](#managed-service-for-apache-airflow).

## Dataplex

Ancien nom de Knowledge Catalog, le catalogue et la gouvernance des données. Les API, la CLI et les rôles IAM gardent le préfixe `dataplex`. Voir [Knowledge Catalog](#knowledge-catalog).

## Dataproc

Ancien nom de Managed Service for Apache Spark. Les URL de documentation et la CLI `gcloud dataproc` gardent l'ancien nom. Voir [Managed Service for Apache Spark](#managed-service-for-apache-spark).

## Dialogflow CX

Ancien nom de Customer Experience Agent Studio, l'atelier de construction d'agents conversationnels. Voir [Customer Experience Agent Studio](#customer-experience-agent-studio).

## Looker Studio

Ancien nom de Data Studio, l'outil de tableaux de bord en libre-service, à distinguer de Looker et de son modèle LookML. Voir [Data Studio](#data-studio).

## Slot

Unité de calcul d'une requête BigQuery. Le mode à la demande en alloue automatiquement ; les éditions en réservent un nombre donné. Voir [BigQuery](#bigquery).

## Vertex AI

Ancien nom de Gemini Enterprise Agent Platform, la plateforme de modèles et d'agents. Voir [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform).

## AI Applications

Nom de la page de la console où se configurent Agent Search et ses applications de recherche. Voir [Agent Search](#agent-search).

## Anthos Service Mesh

Ancien nom d'une des deux composantes de Cloud Service Mesh, le maillage de services géré. Voir [Cloud Service Mesh](#cloud-service-mesh).

## Apigee Edge

Ancien nom de la plateforme de gestion d'APIs Apigee. Voir [Apigee](#apigee).

## Chronicle

Ancien nom de Google Security Operations, le SIEM et SOAR de Google. Les URL de documentation gardent le préfixe `chronicle`. Voir [Google Security Operations](#google-security-operations).

## Cloud Datastore

Ancien nom de Firestore en mode Datastore, la couche de compatibilité de Firestore pour les applications App Engine existantes. Voir [Firestore](#firestore).

## Cloud DLP (Data Loss Prevention)

Ancien nom de Sensitive Data Protection. L'API sous-jacente s'appelle toujours Cloud Data Loss Prevention. Voir [Sensitive Data Protection](#sensitive-data-protection).

## Cloud Firewall

Ancien nom de Cloud NGFW, le pare-feu distribué appliqué à chaque interface de VM. Voir [Cloud NGFW](#cloud-ngfw).

## Cloud Functions

Ancien nom des Cloud Run functions : une fonction est un service Cloud Run déployé depuis le code source, avec un déclencheur HTTP ou CloudEvents. La 1re génération, pilotée par l'API Cloud Functions v1, reste à part. Voir [Cloud Run](#cloud-run).

## Cloud SDK

Ensemble des outils de développement Google Cloud : la CLI, les bibliothèques clientes et les extensions d'IDE. Le paquet installable qui contient les commandes est la gcloud CLI. Voir [gcloud CLI](#cloud-sdk).

## Container Analysis

Ancien nom d'Artifact Analysis, l'analyse de vulnérabilités et le stockage de métadonnées des artefacts. Voir [Artifact Analysis](#artifact-analysis).

## Container Registry

Registre d'images remplacé par Artifact Registry, qui sert les adresses `gcr.io`. Voir [Artifact Registry](#artifact-registry).

## Duet AI for Developers

Ancien nom de Gemini Code Assist, l'assistance au code dans l'IDE. Voir [Gemini Code Assist](#gemini-code-assist).

## Google Agentspace

Ancien nom de Gemini Enterprise app, l'application de recherche et d'agents destinée aux salariés. Voir [Gemini Enterprise app](#gemini-enterprise-app).

## Serverless for Apache Spark

Forme serverless de Managed Service for Apache Spark : des charges Spark lancées sans cluster à gérer. Voir [Managed Service for Apache Spark](#managed-service-for-apache-spark).

## Stackdriver

Ancien nom de la suite d'observabilité de Google Cloud : Monitoring, Logging, Trace, Profiler et Error Reporting, réunis sous le nom Google Cloud Observability. Voir [Cloud Monitoring](#cloud-monitoring).

## Traffic Director

Ancien nom du plan de contrôle de maillage de services, fondu dans Cloud Service Mesh. Voir [Cloud Service Mesh](#cloud-service-mesh).

## Vertex AI Search

Ancien nom d'Agent Search. Voir [Agent Search](#agent-search).

## VM préemptibles

Ancienne forme des Spot VMs : des instances Compute Engine à prix réduit, que Google peut reprendre à tout moment. Voir [Spot VMs](#spot-vms).

## ACID

Propriétés d'une transaction fiable : atomicité, cohérence, isolation, durabilité. Une transaction ACID s'applique entièrement ou pas du tout, même en cas de panne. Voir [Cloud SQL](#cloud-sql).

## Restauration à un instant donné (PITR, point-in-time recovery)

Restauration d'une base dans l'état exact où elle était à une date et une heure choisies, en rejouant le journal de transactions après la dernière sauvegarde. Voir [Cloud SQL](#cloud-sql).

## HTAP (Hybrid Transactional/Analytical Processing)

Transactions et requêtes analytiques exécutées sur les mêmes données vivantes, dans la même base, sans copie vers un entrepôt. AlloyDB y répond par son moteur en colonnes tenu en mémoire. Voir [AlloyDB for PostgreSQL](#alloydb).

## Recherche vectorielle

Recherche des éléments dont l'embedding est le plus proche de celui d'une requête, ce qui retrouve des contenus proches par le sens plutôt que par les mots. Un index de voisins approximatifs la rend rapide sur de gros volumes. Voir [AlloyDB for PostgreSQL](#alloydb).

## Split

Plage contiguë de lignes d'une table Spanner, unité de répartition et de réplication entre serveurs. Une clé primaire croissante concentre les écritures sur un seul split. Voir [Spanner](#spanner).

## Cohérence externe

Garantie de Spanner : une transaction validée après une autre est vue comme postérieure par tous les lecteurs, dans toutes les régions. Elle repose sur les horodatages de TrueTime, l'horloge distribuée de Google. Voir [Spanner](#spanner).

## Unité de traitement (processing unit)

Mesure de la capacité de calcul d'une instance Spanner : 1 000 unités de traitement valent un nœud. Voir [Spanner](#spanner).

## Table entrelacée (interleaved table)

Table Spanner dont les lignes filles sont rangées physiquement à côté de leur ligne parente (`INTERLEAVE IN PARENT`), ce qui évite une jointure distribuée. Voir [Spanner](#spanner).

## Flux de modifications (change stream)

Publication continue des insertions, modifications et suppressions d'une base Spanner, consommable par Dataflow ou Kafka. Voir [Spanner](#spanner).

## Requête fédérée

Requête BigQuery qui lit directement une base Cloud SQL, AlloyDB ou Spanner, sans copier les données dans l'entrepôt. Voir [BigQuery](#bigquery).

## Famille de colonnes (column family)

Groupe de colonnes d'une table Bigtable. Chaque cellule ligne–colonne contient des valeurs horodatées, donc plusieurs versions. Voir [Bigtable](#bigtable).

## Édition BigQuery

Formule de calcul en capacité de BigQuery (Standard, Enterprise, Enterprise Plus), facturée en slots plutôt qu'au volume lu par requête. Chaque édition ouvre un ensemble de fonctionnalités. Voir [BigQuery](#bigquery).

## Réservation (BigQuery)

Ensemble de slots, dédiés ou en autoscaling, rattaché à une édition BigQuery. Les projets affectés à une réservation y puisent leur calcul. Voir [BigQuery](#bigquery).

## Table externe

Table BigQuery dont les données restent dans des fichiers hors de l'entrepôt (Parquet, ORC, Avro, Iceberg sur Cloud Storage) et sont lues sur place à chaque requête. Voir [BigQuery](#bigquery).

## Table partitionnée

Table BigQuery découpée en partitions selon une colonne de date, l'heure d'ingestion ou une plage d'entiers. Une requête filtrée sur cette colonne ne lit que les partitions utiles ; le *clustering* trie en plus les blocs selon d'autres colonnes. Voir [BigQuery](#bigquery).

## Runner (Apache Beam)

Moteur qui exécute un pipeline Apache Beam. Le même pipeline tourne sur le runner Dataflow, Flink, Spark ou le runner direct, sans changer de code. Voir [Dataflow](#dataflow).

## Fenêtrage (windowing)

Découpage d'un flux sans fin en fenêtres finies selon l'horodatage des éléments, pour pouvoir y calculer des agrégats. Les fenêtres sont fixes, glissantes ou par session. Voir [Dataflow](#dataflow).

## Filigrane (watermark)

Seuil qui indique jusqu'à quelle date un pipeline de flux estime avoir reçu toutes les données d'une fenêtre. Un élément qui arrive après ce seuil est une donnée en retard. Voir [Dataflow](#dataflow).

## Exactement une fois (exactly-once)

Garantie qu'un message est traité une seule fois, sans perte ni doublon. Le mode *au moins une fois* (*at-least-once*), moins coûteux, peut produire des doublons que le consommateur doit tolérer. Voir [Dataflow](#dataflow).

## Lakehouse (architecture)

Architecture qui garde les données dans des fichiers ouverts sur un stockage objet, comme un lac de données, tout en les servant en tables SQL, comme un entrepôt. Plusieurs moteurs partagent une seule copie. Voir [Lakehouse](#lakehouse).

## Iceberg (Apache Iceberg)

Format de table ouvert : des fichiers de données et des métadonnées qui décrivent schéma, partitionnement et instantanés. Plusieurs moteurs (BigQuery, Spark, Flink, Trino) lisent et écrivent la même table. Voir [Lakehouse](#lakehouse).

## Sujet (topic)

Canal nommé de Pub/Sub dans lequel les producteurs publient leurs messages. Chaque abonnement rattaché au sujet en reçoit une copie. Voir [Pub/Sub](#pubsub).

## Abonnement (subscription)

Point de consommation d'un sujet Pub/Sub. En *pull*, le consommateur vient chercher les messages ; en *push*, Pub/Sub les envoie à un point de terminaison HTTPS ; l'abonnement peut aussi écrire directement dans BigQuery ou Cloud Storage. Voir [Pub/Sub](#pubsub).

## Acquittement (acknowledgement)

Confirmation par le consommateur qu'un message est traité. Un message non acquitté avant l'échéance est relivré. Voir [Pub/Sub](#pubsub).

## Sujet de lettres mortes (dead-letter topic)

Sujet où Pub/Sub envoie un message après un nombre donné d'échecs de livraison, pour l'isoler au lieu de le relivrer sans fin. Voir [Pub/Sub](#pubsub).

## Partition (Kafka)

Découpage d'un topic Kafka en journaux ordonnés répartis entre les brokers. L'ordre des messages n'est garanti qu'à l'intérieur d'une partition, et leur nombre fixe le parallélisme des consommateurs. Voir [Managed Service for Apache Kafka](#managed-service-for-apache-kafka).

## DCU (Data Compute Unit)

Unité de facturation qui agrège le vCPU, la mémoire et parfois le stockage consommés par un service. Sa composition varie selon le produit (Airflow, Kafka, Knowledge Catalog). Voir [Managed Service for Apache Airflow](#managed-service-for-apache-airflow).

## DAG (Directed Acyclic Graph)

Graphe orienté sans cycle de tâches et de dépendances, qui fixe l'ordre d'exécution d'un workflow. Dans Airflow, un DAG est un fichier Python. Voir [Managed Service for Apache Airflow](#managed-service-for-apache-airflow).

## Backfill

Traitement de l'historique avant ou en dehors du flux courant. Dans Airflow, rattrapage des exécutions manquées d'un DAG ; dans Datastream, lecture initiale des tables entières avant la capture des changements. Voir [Datastream](#datastream).

## ETL (Extract, Transform, Load)

Chaîne qui extrait les données d'une source, les transforme hors de la destination, puis les charge dans l'entrepôt. Voir [Cloud Data Fusion](#cloud-data-fusion).

## ELT (Extract, Load, Transform)

Variante de l'ETL où les données brutes sont chargées d'abord, puis transformées dans l'entrepôt lui-même, en SQL. Voir [Dataform](#dataform).

## SQLX

Format de fichier de Dataform : un bloc `config` suivi d'une requête `SELECT`, dont Dataform déduit la table ou la vue à créer. `ref()` y déclare les dépendances entre tables. Voir [Dataform](#dataform).

## Lignage (data lineage)

Trace des transformations qui relient une donnée à ses sources, jusqu'au niveau de la colonne. Il sert à l'analyse d'impact avant un changement de schéma. Voir [Knowledge Catalog](#knowledge-catalog).

## Requête vérifiée (verified query)

Requête SQL exacte attachée à un agent de données, qui fixe la logique métier d'une question type. C'est le levier le plus efficace sur la justesse des réponses. Voir [Agents de données BigQuery](#data-analytics-agents).

## Modèle sémantique

Couche qui définit une fois pour toutes les dimensions, les mesures et les jointures d'un patrimoine de données, pour que tous les rapports calculent les indicateurs de la même façon. Voir [Looker](#looker).

## Classe de stockage

Niveau de prix d'un objet Cloud Storage : Standard, Nearline, Coldline, Archive. Les classes froides coûtent moins en stockage, mais facturent la récupération et une durée minimale. Voir [Cloud Storage](#cloud-storage).

## Règle de cycle de vie (lifecycle rule)

Règle attachée à un bucket qui supprime un objet ou change sa classe de stockage selon des conditions (âge, date, nombre de versions, préfixe). Voir [Cloud Storage](#cloud-storage).

## LookML (Looker Modeling Language)

Langage déclaratif, versionné en Git, qui décrit le modèle sémantique de Looker : *views* (dimensions et mesures d'une table), *models* (connexion et jointures), *explores*. Voir [Looker](#looker).

## Explore (Looker)

Point d'entrée d'exploration défini en LookML : l'utilisateur y choisit dimensions, mesures et filtres, et Looker génère la requête SQL. Voir [Looker](#looker).

## Identifiants du propriétaire (owner's credentials)

Mode d'une source Data Studio où les lecteurs voient les données avec les droits du propriétaire du rapport, sans droits propres. Les requêtes BigQuery sont alors facturées au projet du propriétaire. Voir [Data Studio](#data-studio).

## RAG (Retrieval-Augmented Generation)

Génération augmentée par récupération : on cherche d'abord les passages pertinents dans ses propres documents, puis on les donne au modèle pour qu'il rédige une réponse fondée sur eux. Voir [Agent Search](#agent-search).

## Embedding

Vecteur numérique qui représente le sens d'un texte, d'une image ou d'un document : deux contenus proches ont des vecteurs proches. C'est la base de la recherche sémantique. Voir [Agent Search](#agent-search).

## Ancrage (grounding)

Rattachement de la réponse d'un modèle à des sources vérifiables — documents de l'entreprise, définitions du catalogue — avec citations, pour limiter les réponses inventées. Voir [Agent Search](#agent-search).

## Modèle de fondation (foundation model)

Grand modèle préentraîné sur un corpus très large, utilisable tel quel pour de nombreuses tâches ou affinable sur ses propres données. Voir [Model Garden](#model-garden).

## Jeton (token)

Fragment de texte (mot ou morceau de mot) sur lequel un modèle de langue travaille. Les limites d'entrée et la facturation des modèles appelés à l'API se comptent en jetons. Voir [Model Garden](#model-garden).

## Réglage fin (fine-tuning)

Entraînement complémentaire d'un modèle préentraîné sur ses propres données, pour l'adapter à une tâche ou à un domaine. Voir [Model Garden](#model-garden).

## Endpoint (point de terminaison d'inférence)

Ressource sur laquelle un modèle est déployé pour répondre à des requêtes en ligne, sur des machines réservées. Il est facturé tant qu'il existe, même sans trafic. Voir [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform).

## ADK (Agent Development Kit)

Cadre de développement d'agents de Google, modulaire et indépendant du modèle. Un agent écrit avec l'ADK se déploie sur Agent Runtime. Voir [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform).

## MCP (Model Context Protocol)

Protocole ouvert par lequel une application d'IA découvre et appelle des outils et des sources de données exposés par des serveurs MCP. Voir [Gemini Code Assist](#gemini-code-assist).

## Système multi-agents

Application où un agent de pilotage reçoit l'utilisateur, comprend l'objectif et délègue à des sous-agents spécialisés, qui peuvent eux-mêmes en appeler d'autres. Voir [Customer Experience Agent Studio](#customer-experience-agent-studio).

## Opération longue (long-running operation)

Appel d'API asynchrone qui renvoie immédiatement un identifiant d'opération, que l'on interroge jusqu'à la fin du traitement. Les traitements par lots des API d'IA fonctionnent ainsi. Voir [Speech-to-Text](#speech-to-text).

## SSML (Speech Synthesis Markup Language)

Balisage XML qui règle la synthèse vocale : pauses, prononciation, emphase, épellation. Voir [Text-to-Speech](#text-to-speech).

## NMT (Neural Machine Translation)

Traduction automatique par réseau de neurones, le modèle générique de la Cloud Translation API. Voir [Translation AI](#translation-ai).

## OCR (Optical Character Recognition)

Reconnaissance optique de caractères : extraction du texte contenu dans une image ou un document numérisé. Voir [Document AI](#document-ai).

## Processeur (Document AI)

Ressource Document AI créée dans un projet et une région, spécialisée dans une tâche (OCR, analyse de formulaire, extraction, classification). Il renvoie un objet `Document` normalisé. Voir [Document AI](#document-ai).

## Déclencheur (trigger)

Règle qui lance un build Cloud Build sur un événement : poussée de branche ou de tag, *pull request*, message Pub/Sub, webhook ou appel manuel. Voir [Cloud Build](#cloud-build).

## Pool privé (private pool)

Pool de workers Cloud Build dédié, créé dans une région, qui peut atteindre un VPC et se passer d'adresses IP publiques. Voir [Cloud Build](#cloud-build).

## SLSA (Supply-chain Levels for Software Artifacts)

Cadre de niveaux de sécurité de la chaîne logicielle. Cloud Build atteint le niveau 3 et produit une *provenance* signée : la preuve de la source et de la chaîne qui ont construit un artefact. Voir [Cloud Build](#cloud-build).

## Buildpack

Outil qui détecte le langage d'un code source et en construit une image de conteneur sans Dockerfile. Voir [Cloud Code](#cloud-code).

## Digest

Empreinte `sha256` qui désigne une image de conteneur de façon immuable (`IMAGE@sha256:...`), à la différence d'un tag, qui peut être déplacé. Voir [Artifact Registry](#artifact-registry).

## SCA (Software Composition Analysis)

Analyse de composition logicielle : comparaison des paquets installés dans un artefact à des bases publiques de vulnérabilités. Elle ne dit rien du code maison. Voir [Artifact Analysis](#artifact-analysis).

## SBOM (Software Bill of Materials)

Nomenclature logicielle : la liste des composants et dépendances d'un artefact, avec leurs versions. Voir [Artifact Analysis](#artifact-analysis).

## VEX (Vulnerability Exploitability eXchange)

Déclaration qu'une vulnérabilité détectée n'est pas exploitable dans un contexte donné, pour ne pas traiter le même faux positif à chaque analyse. Voir [Artifact Analysis](#artifact-analysis).

## Attestation

Document signé qui certifie qu'une image a franchi une étape : build par une chaîne de confiance, tests, validation manuelle. Un *attestor* porte la clé publique qui la vérifie au déploiement. Voir [Binary Authorization](#binary-authorization).

## Release (Cloud Deploy)

État figé d'une application à livrer : manifestes rendus pour chaque cible du pipeline de livraison, images désignées par leur digest. Voir [Cloud Deploy](#cloud-deploy).

## Rollout (Cloud Deploy)

Déploiement d'une release sur une cible. Chaque promotion vers la cible suivante crée un nouveau rollout. Voir [Cloud Deploy](#cloud-deploy).

## Déploiement canary

Déploiement progressif d'une nouvelle version par paliers de trafic (25 %, 50 %…), pour détecter un problème avant qu'il touche tous les utilisateurs. Voir [Cloud Deploy](#cloud-deploy).

## GitOps

Pratique où un dépôt Git décrit l'état voulu de l'infrastructure ou des applications, et un opérateur le réconcilie en continu avec l'état réel. Voir [Config Connector](#config-connector).

## IaC (Infrastructure as Code)

Description de l'infrastructure dans des fichiers versionnés, appliqués par un outil (Terraform, Config Connector), plutôt que par des commandes ou des clics. Voir [Infrastructure Manager](#infrastructure-manager).

## État Terraform (state)

Fichier qui enregistre la correspondance entre une configuration Terraform et les ressources réellement créées. Infrastructure Manager le conserve dans un bucket géré et le verrouille pendant les opérations. Voir [Infrastructure Manager](#infrastructure-manager).

## CRD (Custom Resource Definition)

Extension de l'API Kubernetes qui ajoute un nouveau type d'objet. Config Connector en installe une par type de ressource Google Cloud. Voir [Config Connector](#config-connector).

## Réconciliation

Boucle d'un contrôleur qui compare en continu l'état déclaré (`spec`) à l'état réel et corrige l'écart, y compris une modification faite à la main. Voir [Config Connector](#config-connector).

## Niveau de publication (launch stage)

Maturité d'un produit ou d'une commande : GA (disponibilité générale, stable), *preview*, *beta*, *alpha*. Dans la gcloud CLI, les commandes non GA sont préfixées (`gcloud beta ...`). Voir [gcloud CLI](#cloud-sdk).

## IaaS (Infrastructure as a Service)

Modèle de service où le fournisseur loue des machines virtuelles, des disques et du réseau, et où le système d'exploitation et tout ce qui tourne dessus restent à la charge du client. Voir [Compute Engine](#compute-engine).

## Ressource zonale, régionale ou globale

Portée d'une ressource Google Cloud : une zone (un disque, une VM), une région et toutes ses zones (un sous-réseau, un groupe d'instances régional), ou le monde entier (un réseau VPC, ses routes et ses règles de pare-feu). Voir [Virtual Private Cloud](#vpc).

## Type de machine

Configuration de vCPU et de mémoire d'une VM Compute Engine. Une famille (usage général, calcul, mémoire, accélérateurs...) se décline en séries, et une série en types prédéfinis dont le suffixe (`standard`, `highmem`, `highcpu`...) donne le rapport mémoire/vCPU ; certaines séries acceptent un type personnalisé. Voir [Compute Engine](#compute-engine).

## Groupe d'instances géré (MIG)

Groupe de VM identiques, créées à partir d'un modèle d'instance, que Compute Engine maintient au nombre voulu : il recrée les VM défaillantes, se redimensionne par autoscaling et se met à jour par déploiement progressif. Il peut être zonal ou régional, et sert de backend aux load balancers. Voir [Compute Engine](#compute-engine).

## Modèle de provisionnement

Mode d'obtention d'une VM, choisi à sa création : standard, Spot (capacité excédentaire à prix réduit, reprise à tout moment), Flex-start (attente d'une fenêtre de capacité, puis exécution sans préemption) ou lié à une réservation. Voir [Compute Engine](#compute-engine).

## Préemption

Reprise par Compute Engine d'une VM Spot dont il a besoin de la capacité : le script d'arrêt reçoit un signal, puis la machine est coupée au bout d'une trentaine de secondes au mieux. Voir [Spot VMs](#spot-vms).

## Réservation (Compute Engine)

Capacité bloquée dans une zone pour des VM d'une configuration précise, facturée au tarif à la demande qu'elle soit consommée ou non. Elle se consomme automatiquement par toute VM compatible, ou seulement par les VM qui la ciblent. Voir [Compute Engine](#compute-engine).

## Remise sur engagement d'usage (CUD)

Remise accordée contre un engagement d'un ou trois ans, soit sur des ressources précises (vCPU, mémoire, GPU...), soit sur un montant de dépense horaire valable sur plusieurs produits. Voir [Compute Engine](#compute-engine).

## Remise à l'usage soutenu (SUD)

Remise appliquée automatiquement, sans engagement, aux VM de certaines séries anciennes qui tournent une part importante du mois. Les séries récentes n'y sont pas éligibles. Voir [Compute Engine](#compute-engine).

## XLA

Compilateur open source qui transforme les graphes de calcul de JAX, PyTorch ou TensorFlow en code pour CPU, GPU ou TPU. Tout code exécuté sur un TPU passe par lui. Voir [Cloud TPU](#cloud-tpu).

## Compte de service

Identité destinée à une application plutôt qu'à une personne, identifiée par une adresse e-mail. Attaché à une ressource (VM, service Cloud Run, pod GKE), il fournit au code des jetons courts sans qu'aucun secret ne circule. Voir [IAM](#cloud-iam).

## Agent de service

Compte de service créé et géré par Google, qui agit pour le compte d'un produit sur les ressources du projet — par exemple pour utiliser une clé CMEK ou lire un bucket. Voir [IAM](#cloud-iam).

## Principal

Toute identité à qui IAM peut accorder un rôle : compte Google, groupe, compte de service, identité fédérée d'un pool de personnel ou de charges de travail. Voir [IAM](#cloud-iam).

## Permission IAM

Droit élémentaire de la forme `service.ressource.verbe` (`storage.objects.get`), correspondant le plus souvent à une méthode d'API. Elle ne s'accorde jamais seule, toujours au travers d'un rôle. Voir [IAM](#cloud-iam).

## Rôle prédéfini

Rôle IAM maintenu par Google, qui regroupe les permissions d'un métier sur un service (`roles/run.invoker`, `roles/secretmanager.secretAccessor`). Voir [IAM](#cloud-iam).

## Rôle personnalisé

Rôle IAM dont on choisit chaque permission, pour coller au besoin exact ; plus précis qu'un rôle prédéfini, mais à entretenir soi-même et limité en nombre. Voir [IAM](#cloud-iam).

## Stratégie d'autorisation (allow policy)

Objet attaché à une ressource, composé de liaisons qui associent un rôle à une liste de principaux, éventuellement sous condition. C'est ce que lit IAM pour accepter ou refuser un appel. Voir [IAM](#cloud-iam).

## Hiérarchie des ressources

Arborescence organisation → dossiers → projets → ressources. Une stratégie posée sur un niveau s'hérite vers le bas, si bien que l'accès effectif est l'union des stratégies de la ressource et de ses ancêtres. Voir [IAM](#cloud-iam).

## Condition IAM

Expression CEL attachée à une liaison de rôle, qui ne l'active que si elle est vraie : date d'expiration, préfixe de nom de ressource, tag, adresse IP. Voir [IAM](#cloud-iam).

## Stratégie de refus (deny policy)

Stratégie IAM qui retire des permissions même à qui détient un rôle qui les contient ; elle prime sur les autorisations. Voir [IAM](#cloud-iam).

## Emprunt d'identité (impersonation)

Mécanisme par lequel un principal autorisé agit comme un compte de service le temps d'un jeton court, sans en détenir la clé. Voir [IAM](#cloud-iam).

## CEL (Common Expression Language)

Langage d'expressions court et sans effet de bord, utilisé dans les conditions IAM, les mappages et conditions d'attribut de la fédération d'identité, ou les filtres d'Eventarc Advanced. Voir [IAM](#cloud-iam).

## Pool d'identités de charge de travail

Conteneur d'identités externes (AWS, GitHub, GitLab, Kubernetes, fournisseur OIDC ou SAML) qui peuvent échanger leur jeton contre un jeton Google Cloud court, sans clé de compte de service. On en crée un par environnement. Voir [Workload Identity Federation](#workload-identity-federation).

## Fédération d'identité de personnel (workforce identity federation)

Accès des employés à la console et aux APIs Google Cloud à partir d'un fournisseur d'identité externe, par un *workforce identity pool*, sans créer de compte Google pour chacun. Voir [Workload Identity Federation](#workload-identity-federation).

## JWT (JSON Web Token)

Jeton signé au format JSON qui transporte des revendications sur son porteur et se vérifie avec la clé publique de l'émetteur, sans appel au service qui l'a produit. Voir [Identity Platform](#identity-platform).

## OAuth 2.0

Protocole de délégation d'autorisation par jetons d'accès. Les APIs Google Cloud attendent un jeton OAuth 2.0 dans l'en-tête `Authorization: Bearer`. Voir [Authentifier un appel à une API](#authentifier-un-appel).

## OIDC (OpenID Connect)

Couche d'identité au-dessus d'OAuth 2.0 : le fournisseur émet un jeton d'identité JWT qui dit qui est l'appelant. Cloud Tasks et Cloud Scheduler en joignent un pour appeler un service privé. Voir [Workload Identity Federation](#workload-identity-federation).

## SAML 2.0

Standard XML d'authentification unique (SSO) : le fournisseur d'identité de l'entreprise remet à l'application une assertion signée, si bien que celle-ci ne détient aucun mot de passe. Voir [Cloud Identity](#cloud-identity).

## Niveau d'accès

Condition de contexte définie dans Access Context Manager — plage d'adresses IP, région, appareil géré, identité — utilisée par Identity-Aware Proxy et VPC Service Controls pour l'accès contextuel. Voir [VPC Service Controls](#vpc-service-controls).

## Trousseau de clés (key ring)

Regroupement de clés Cloud KMS dans un emplacement donné. Chaque clé a des versions, dont une primaire ; trousseaux et clés ne se suppriment pas, seules les versions se détruisent. Voir [Cloud KMS](#cloud-kms).

## CMEK (Customer-Managed Encryption Keys)

Clés Cloud KMS contrôlées par le client, qui protègent les données d'un service à la place des clés internes de Google. Le client en maîtrise la rotation, la révocation et la destruction, ce qui rend les données illisibles si la clé disparaît. Voir [Cloud KMS](#cloud-kms).

## HSM (Hardware Security Module)

Module matériel qui génère et utilise des clés cryptographiques sans jamais les laisser sortir. Cloud HSM en fournit un cluster certifié FIPS 140-2 niveau 3. Voir [Cloud KMS](#cloud-kms).

## EKM (External Key Manager)

Niveau de protection de Cloud KMS où la clé reste chez un gestionnaire externe partenaire ; Google ne fait que relayer chaque opération. Voir [Cloud KMS](#cloud-kms).

## mTLS (TLS mutuel)

TLS où le client présente lui aussi un certificat, si bien que chacun des deux côtés authentifie l'autre. C'est la base de l'authentification entre services d'un maillage. Voir [Cloud Service Mesh](#cloud-service-mesh).

## infoType

Type de donnée sensible reconnu par Sensitive Data Protection — numéro de carte bancaire, IBAN, adresse e-mail, numéro de sécurité sociale — détecté par un détecteur prédéfini ou personnalisé. Voir [Sensitive Data Protection](#sensitive-data-protection).

## Périmètre de service

Frontière VPC Service Controls autour d'un ensemble de projets et de services Google : les appels circulent librement à l'intérieur, et tout échange qui traverse la frontière est refusé sauf règle d'entrée ou de sortie. Un mode simulation (*dry run*) journalise les refus sans bloquer. Voir [VPC Service Controls](#vpc-service-controls).

## Résultat (finding)

Enregistrement d'un problème constaté sur une ressource par Security Command Center ou un détecteur partenaire, avec gravité, catégorie, recommandation de correction et état. Voir [Security Command Center](#security-command-center).

## Règle d'administration (organization policy)

Contrainte posée sur l'organisation, un dossier ou un projet pour interdire une configuration — régions autorisées, création du réseau par défaut, clés CMEK obligatoires — quels que soient les droits IAM. Voir [Assured Workloads](#assured-workloads).

## SIEM (Security Information and Event Management)

Système qui collecte, normalise et conserve les journaux de sécurité, y applique des règles de détection et permet d'y rechercher sur un long historique. Voir [Google Security Operations](#google-security-operations).

## SOAR (Security Orchestration, Automation and Response)

Outil de gestion des cas de sécurité et de réponse automatisée, qui enchaîne des actions (enrichissement, confinement, notification) dans des playbooks. Voir [Google Security Operations](#google-security-operations).

## UDM (Unified Data Model)

Schéma commun de Google Security Operations dans lequel chaque journal ingéré est converti par un analyseur, pour que toutes les sources s'interrogent de la même façon. Voir [Google Security Operations](#google-security-operations).

## WAF (Web Application Firewall)

Pare-feu applicatif qui inspecte les requêtes HTTP pour bloquer les attaques connues : injection SQL, script intersites, inclusion de fichiers. Voir [Cloud Armor](#cloud-armor).

## DDoS (déni de service distribué)

Attaque qui sature un service par un volume de trafic venu de nombreuses sources, au niveau réseau (couches 3 et 4) ou applicatif (déluge de requêtes HTTP). Voir [Cloud Armor](#cloud-armor).

## Sous-réseau

Plage d'adresses IP d'un réseau VPC, définie dans une région ; une VM se rattache à un sous-réseau de la région de sa zone. Un sous-réseau peut porter des plages secondaires pour les alias IP. Voir [Virtual Private Cloud](#vpc).

## Plage d'alias IP

Plage d'adresses secondaire d'un sous-réseau, attribuée à une VM en plus de son adresse principale. GKE y prend les adresses des pods et des services, ce qui les rend routables dans le VPC (cluster « VPC natif »). Voir [Virtual Private Cloud](#vpc).

## Cloud Router

Routeur BGP managé et régional qui apprend les routes d'un réseau distant (VPN, Interconnect) et annonce celles du VPC. Le mode de routage dynamique du réseau dit si ces routes valent pour sa seule région ou pour toutes. Voir [Virtual Private Cloud](#vpc).

## BGP (Border Gateway Protocol)

Protocole d'échange de routes entre réseaux autonomes. Sur Google Cloud, il relie un VPC à un réseau distant par Cloud Router et décide de l'annonce des adresses externes sur Internet. Voir [Cloud VPN](#cloud-vpn).

## Règle de pare-feu VPC

Règle attachée à un réseau VPC qui autorise ou refuse un trafic selon sa direction, ses adresses, ses ports et une cible (étiquette réseau, compte de service). Tout réseau porte deux règles implicites : entrée refusée, sortie autorisée. Voir [Virtual Private Cloud](#vpc).

## Politique de pare-feu hiérarchique

Ensemble de règles de pare-feu attaché à l'organisation ou à un dossier, évalué avant les règles des projets et imposé à tous les réseaux qu'ils contiennent. Voir [Cloud NGFW](#cloud-ngfw).

## Tag

Paire clé-valeur définie dans une organisation ou un projet, avec ses propres contrôles IAM, attachée aux ressources. Les tags servent de cible aux règles de pare-feu (tags sécurisés), de condition IAM et d'axe d'analyse des coûts. Voir [Cloud NGFW](#cloud-ngfw).

## Shared VPC

Organisation où un projet hôte porte le réseau VPC et où des projets de service y créent leurs ressources : le réseau est administré de façon centrale, chaque équipe garde son projet et son budget. Voir [Virtual Private Cloud](#vpc).

## Appairage de réseaux VPC (VPC peering)

Liaison entre deux réseaux VPC qui échangent leurs routes de sous-réseau et communiquent en adresses internes. Elle n'est pas transitive et ne partage ni règles de pare-feu ni noms DNS. Voir [Virtual Private Cloud](#vpc).

## Accès privé à Google

Option d'un sous-réseau qui permet à des VM sans adresse IP externe de joindre les APIs Google, sans passer par Cloud NAT. Voir [Cloud NAT](#cloud-nat).

## Endpoint Private Service Connect

Règle de transfert qui pose une adresse IP interne dans un sous-réseau du consommateur et la fait pointer vers un service publié ou vers les APIs Google, sans exposer le reste du réseau producteur. Voir [Private Service Connect](#private-service-connect).

## IPsec

Suite de protocoles qui chiffre et authentifie les paquets IP entre deux passerelles ; les tunnels Cloud VPN la négocient par IKEv1 ou IKEv2. Voir [Cloud VPN](#cloud-vpn).

## Hub et spoke

Topologie de Network Connectivity Center : un hub global auquel se rattachent des spokes (réseaux VPC, tunnels VPN, rattachements Interconnect) entre lesquels il échange les routes, avec une transitivité que l'appairage de VPC n'offre pas. Voir [Network Connectivity Center](#network-connectivity-center).

## Anycast

Annonce d'une même adresse IP depuis de nombreux points du réseau, si bien que chaque client joint le point le plus proche. Les load balancers globaux et les serveurs de Cloud DNS l'utilisent. Voir [Cloud Load Balancing](#cloud-load-balancing).

## Load balancer proxy ou passthrough

Un load balancer proxy termine la connexion du client et en ouvre une nouvelle vers le backend, qui voit l'adresse du proxy ; un load balancer passthrough transmet les paquets tels quels, adresse source du client comprise, et les réponses repartent directement. Voir [Cloud Load Balancing](#cloud-load-balancing).

## Règle de transfert (forwarding rule)

Ressource qui associe une adresse IP, un protocole et un port à la cible d'un load balancer (proxy cible ou service de backend) ou à un endpoint Private Service Connect. Voir [Cloud Load Balancing](#cloud-load-balancing).

## Service de backend

Ressource d'un load balancer qui regroupe les backends (groupes d'instances, NEG) et porte le protocole, le mode d'équilibrage, l'affinité de session et le contrôle d'état ; c'est là que s'attachent Cloud CDN, Cloud Armor et IAP. Voir [Cloud Load Balancing](#cloud-load-balancing).

## NEG (groupe de points de terminaison du réseau)

Backend de load balancer qui désigne des points de terminaison plutôt que des VM : adresses de pods GKE, service Cloud Run (NEG sans serveur), origine hors de Google Cloud (NEG internet), site sur site (NEG hybride) ou service Private Service Connect. Voir [Cloud Load Balancing](#cloud-load-balancing).

## Contrôle d'état (health check)

Sonde qui interroge régulièrement chaque backend (TCP, HTTP, gRPC...) ; un backend défaillant sort de la rotation du load balancer, ou est recréé par son groupe d'instances géré. Voir [Cloud Load Balancing](#cloud-load-balancing).

## Niveau de service réseau (Premium ou Standard)

Attribut d'une adresse IP externe qui fixe le chemin du trafic Internet : en Premium, il entre dans le réseau de Google au point de présence le plus proche du client ; en Standard, il traverse l'Internet public jusqu'à la région, pour un tarif de sortie plus bas. Voir [Network Service Tiers](#network-service-tiers).

## Révision (Cloud Run)

Version immuable d'un service Cloud Run, créée à chaque déploiement ou changement de configuration. Le trafic se répartit entre révisions par pourcentages, pour un déploiement progressif ou un retour arrière. Voir [Cloud Run](#cloud-run).

## Concurrence (Cloud Run)

Nombre maximal de requêtes qu'une instance Cloud Run traite en même temps. C'est le premier levier de coût : plus elle est haute, moins il faut d'instances. Voir [Cloud Run](#cloud-run).

## Sortie VPC directe

Mode par lequel un service ou un job Cloud Run envoie son trafic sortant dans un sous-réseau VPC, sans connecteur à maintenir, pour joindre des adresses privées. Voir [Cloud Run](#cloud-run).

## Autopilot

Mode de GKE où Google gère les nœuds, leur dimensionnement et leur sécurité : on déclare des pods et on paie les ressources qu'ils demandent. À l'inverse, le mode Standard laisse administrer les pools de nœuds. Voir [Google Kubernetes Engine](#gke).

## Pool de nœuds

Groupe de nœuds d'un cluster GKE de configuration identique (type de machine, image, VM Spot...), que l'on crée, met à niveau ou supprime sans toucher au reste du cluster. Voir [Google Kubernetes Engine](#gke).

## RPO (Recovery Point Objective)

Quantité maximale de données, exprimée en durée, que l'on accepte de perdre lors d'un incident. Une réplication synchrone vise un RPO nul. Voir [Hyperdisk](#hyperdisk).

## RTO (Recovery Time Objective)

Durée maximale acceptable avant que le service soit rétabli après un incident. Voir [Backup and DR Service](#backup-and-dr).

## CloudEvents

Spécification ouverte de la CNCF qui décrit une enveloppe commune d'événement (source, type, identifiant, données), utilisée par Eventarc. Voir [Eventarc](#eventarc).

## Livraison au moins une fois (at-least-once)

Garantie qu'un message ou une tâche sera remis, au prix de doublons possibles ; le récepteur doit donc être idempotent. Voir [Cloud Tasks](#cloud-tasks).

## File de lettres mortes (dead-letter queue)

File qui recueille les messages qu'aucune livraison n'a réussi à faire acquitter, pour les examiner à part au lieu de les perdre. Voir [Eventarc](#eventarc).

## Proxy d'API

Façade placée entre les clients et un backend, qui applique sécurité, quotas et transformations sans toucher au code du backend. Voir [Apigee](#apigee).

## Clé d'API

Chaîne qui identifie le projet appelant d'une API et sert de base aux quotas ; elle n'authentifie pas un utilisateur. Voir [API Gateway](#api-gateway).

## Google Cloud Observability

Nom d'ensemble de Cloud Monitoring, Cloud Logging, Cloud Trace, Error Reporting, Cloud Profiler et Managed Service for Prometheus. Voir [Cloud Monitoring](#cloud-monitoring).

## Type de métrique et ressource surveillée

Une série temporelle de Cloud Monitoring est identifiée par un type de métrique (`compute.googleapis.com/instance/cpu/utilization`), une ressource surveillée (`gce_instance`, `cloud_run_revision`) et des étiquettes. Voir [Cloud Monitoring](#cloud-monitoring).

## PromQL

Langage de requête de Prometheus, recommandé par Cloud Monitoring pour interroger toutes les métriques, y compris celles de Google Cloud. Voir [Managed Service for Prometheus](#managed-service-for-prometheus).

## Règle d'alerte

Règle Cloud Monitoring qui associe une condition (seuil, absence de métrique, requête PromQL, correspondance de journal) à des canaux de notification, et ouvre un incident quand elle est franchie. Voir [Cloud Monitoring](#cloud-monitoring).

## SLI (Service Level Indicator)

Mesure de la qualité d'un service vue par ses utilisateurs, typiquement la part de requêtes réussies ou servies sous un seuil de latence. Voir [Cloud Monitoring](#cloud-monitoring).

## SLO (Service Level Objective)

Objectif chiffré sur un SLI pour une période donnée, par exemple 99,9 % de requêtes réussies sur 30 jours glissants. Voir [Cloud Monitoring](#cloud-monitoring).

## Budget d'erreur

Marge d'échec qu'autorise un SLO (0,1 % des requêtes pour un SLO de 99,9 %). On alerte sur sa vitesse de consommation plutôt que sur chaque erreur. Voir [Cloud Monitoring](#cloud-monitoring).

## SLA (Service Level Agreement)

Engagement contractuel de disponibilité d'un fournisseur, assorti de compensations s'il n'est pas tenu. Sur Google Cloud, il dépend souvent de la configuration retenue. Voir [Cloud VPN](#cloud-vpn).

## Puits de journaux (sink)

Règle du routeur de Cloud Logging qui envoie les entrées correspondant à un filtre vers une destination : bucket de journaux, BigQuery, Cloud Storage, Pub/Sub ou autre projet. Des filtres d'exclusion écartent ce qu'on ne veut pas ingérer. Voir [Cloud Logging](#cloud-logging).

## Bucket de journaux

Conteneur de stockage de Cloud Logging, avec sa rétention et sa région. Chaque projet a `_Required` (journaux d'audit obligatoires, 400 jours) et `_Default` (le reste, 30 jours par défaut). Voir [Cloud Logging](#cloud-logging).

## Journaux d'audit (Cloud Audit Logs)

Journaux qui répondent à « qui a fait quoi, quand, sur quelle ressource » : activité d'administration (toujours active), accès aux données (à activer, facturés), événements système et refus de règle. Voir [Cloud Logging](#cloud-logging).

## OpenTelemetry

Standard ouvert d'instrumentation (SDK, collecteur, protocole OTLP) pour produire traces, métriques et journaux sans dépendre d'un fournisseur. Voir [Cloud Trace](#cloud-trace).

## Span

Unité d'une trace distribuée : une opération nommée, avec son début, sa fin, son parent et ses attributs. Les spans d'une même requête forment un arbre, la trace. Voir [Cloud Trace](#cloud-trace).

## Quota

Borne imposée par projet, dossier ou organisation, globale, régionale ou zonale : quota d'allocation (nombre de vCPU, d'adresses IP), de débit (appels par minute) ou de simultanéité. Il se relève par une préférence de quota, à la différence d'une limite du système. Voir [Cloud Quotas](#cloud-quotas).

## Compte de facturation

Objet Cloud Billing qui porte le moyen de paiement et la devise, auquel chaque projet est rattaché ; budgets, rapports et exports s'y définissent. Voir [Cost Management](#cost-management).

## Budget

Montant de dépense attendu sur une portée (compte, projets, services, étiquettes), avec des seuils qui déclenchent des alertes, éventuellement publiées sur Pub/Sub. Un budget d'alerte n'arrête aucune ressource ; un budget à plafond de dépense (*spend cap*, en préversion) met en pause un service éligible d'un projet. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Adaptation de l'OS

Retouches qu'applique Migrate to Virtual Machines au système d'une VM répliquée pour qu'elle démarre sur Compute Engine : configuration réseau, agent invité, console série. Voir [Migrate to Virtual Machines](#migrate-to-virtual-machines).

## Bascule (cut-over)

Dernière étape d'une migration de VM : arrêt de la source, ultime réplication, puis création de la VM de production sur Google Cloud. Voir [Migrate to Virtual Machines](#migrate-to-virtual-machines).

## Clone de test

VM Compute Engine créée à partir des dernières données répliquées d'une VM en cours de migration, pour vérifier son fonctionnement pendant que la source reste en service. Voir [Migrate to Virtual Machines](#migrate-to-virtual-machines).

## Client de découverte (discovery client)

Application Windows de Migration Center qui scanne le parc existant pendant plusieurs jours et remonte configuration, utilisation, dépendances réseau et logiciels installés ; la CLI `mcdc` fait la même collecte en une passe. Voir [Migration Center](#migration-center).

## Conteneur système Linux

Image produite par Migrate to Containers qui embarque tout l'espace utilisateur d'une VM Linux, relancé par un gestionnaire de services qui démarre les services d'origine. Voir [Migrate to Containers](#migrate-to-containers).

## Espace de conversion (conversion workspace)

Espace de Database Migration Service où le schéma et le code d'une base Oracle ou SQL Server sont traduits en PostgreSQL, relus et corrigés avant d'être appliqués à la destination. Voir [Database Migration Service](#database-migration-service).

## Groupe de déplacement (move group)

Ensemble de serveurs et d'applications interdépendants qui doivent migrer ensemble, au sein d'une vague de migration. Voir [Migration Center](#migration-center).

## Migrate Connector

Appliance OVA installée sur un vCenter, qui inventorie les VM, lit leurs disques et les réplique vers Google Cloud pour Migrate to Virtual Machines. Voir [Migrate to Virtual Machines](#migrate-to-virtual-machines).

## Migration homogène et hétérogène

Une migration homogène garde le même moteur de base de données (MySQL vers Cloud SQL for MySQL) ; une migration hétérogène en change (Oracle vers PostgreSQL) et demande de convertir schéma et code. Voir [Database Migration Service](#database-migration-service).

## Plan de migration (Migrate to Containers)

Fichier `config.yaml` produit par `m2c analyze` à partir du système de fichiers copié, qu'on édite pour choisir ce qui entre dans l'image avant `m2c generate`. Voir [Migrate to Containers](#migrate-to-containers).

## Promotion (Database Migration Service)

Opération qui détache la destination d'une migration continue de sa source et en fait une instance principale, prête à recevoir les écritures. Voir [Database Migration Service](#database-migration-service).

## Rapport TCO

Rapport de Migration Center qui compare le coût d'exploitation d'un groupe d'actifs sur Google Cloud selon plusieurs jeux de préférences de migration, avec une cible recommandée par actif. Voir [Migration Center](#migration-center).

## Vague de migration (wave)

Lot d'applications migrées ensemble parce qu'elles partagent des caractéristiques ou des dépendances ; les applications isolées forment en général la première vague. Voir [Migration Center](#migration-center).

## Air-gapped

Déploiement de Google Distributed Cloud entièrement déconnecté d'internet et de Google Cloud, avec sa propre console, sa CLI `gdcloud` et ses propres API. Voir [Google Distributed Cloud](#google-distributed-cloud).

## Anthos clusters on bare metal, Anthos clusters on VMware

Anciens noms de Google Distributed Cloud (logiciel seul), la distribution de GKE installée sur les serveurs ou l'infrastructure vSphere du client. Voir [Google Distributed Cloud](#google-distributed-cloud).

## Cloud privé (VMware Engine)

Pile VMware isolée (ESXi, vCenter, vSAN, NSX, HCX) sur des nœuds *bare metal* dédiés d'une même région, avec son propre vCenter ; au moins trois nœuds hors essai. Voir [VMware Engine](#vmware-engine).

## Cloud privé étendu (stretched private cloud)

Cloud privé VMware Engine réparti à parts égales sur deux zones d'une région, avec un nœud témoin dans une troisième, pour survivre à la perte d'une zone. Voir [VMware Engine](#vmware-engine).

## Data Analytics Migration Services

Nom commercial de l'offre de Google Cloud pour migrer entrepôts et lacs de données, dont l'outillage est BigQuery Migration Service. Voir [BigQuery Migration Service](#bigquery-migration-service).

## Distributed Cloud connected

Déploiement de Google Distributed Cloud sur du matériel certifié installé chez le client et géré à distance par Google ; il tolère jusqu'à 7 jours de coupure avec Google Cloud. Voir [Google Distributed Cloud](#google-distributed-cloud).

## dwh-migration-dumper

Outil en ligne de commande open source qui extrait les métadonnées et les journaux de requêtes d'un entrepôt de données, pour l'évaluation et la traduction SQL de BigQuery Migration Service. Voir [BigQuery Migration Service](#bigquery-migration-service).

## Évaluation de migration (migration assessment)

Analyse des métadonnées et des journaux de requêtes d'un entrepôt existant, restituée dans un rapport Data Studio : coût dans BigQuery, optimisations, taux de traduction automatique, plan de migration. Voir [BigQuery Migration Service](#bigquery-migration-service).

## GDC Edge, GDC Hosted, GDC Virtual

Anciens noms des déploiements de Google Distributed Cloud : *connected*, *air-gapped* et logiciel seul. Voir [Google Distributed Cloud](#google-distributed-cloud).

## HCX

Outil VMware de migration et de mobilité des VM entre sites vSphere (migration à chaud par vMotion, réplication), inclus dans chaque cloud privé VMware Engine. Voir [VMware Engine](#vmware-engine).

## Mode de survie (survivability mode)

État d'un cluster Distributed Cloud connected qui a perdu sa liaison avec Google Cloud : les charges continuent de tourner, jusqu'à 7 jours. Voir [Google Distributed Cloud](#google-distributed-cloud).

## Nœud de stockage seul (storage-only node)

Nœud VMware Engine sans cœur utilisable par les VM, ajouté à un cluster pour augmenter la capacité vSAN. Voir [VMware Engine](#vmware-engine).

## Réseau VMware Engine (VMware Engine network)

Réseau global qui relie les clouds privés VMware Engine entre eux, aux réseaux VPC par appairage et au site du client par VPN ou Interconnect. Voir [VMware Engine](#vmware-engine).

## Traducteur SQL par lots (batch SQL translator)

Service qui traduit en GoogleSQL des dossiers de scripts SQL déposés dans Cloud Storage et renvoie les fichiers traduits avec un rapport d'erreurs. Voir [BigQuery Migration Service](#bigquery-migration-service).

## VMware Cloud Foundation (VCF)

Suite logicielle VMware (vSphere, vSAN, NSX, HCX) dont la souscription, achetée chez Broadcom, doit être apportée pour utiliser des nœuds VMware Engine. Voir [VMware Engine](#vmware-engine).

## vSAN

Stockage logiciel VMware qui agrège les disques locaux des nœuds d'un cluster en un datastore partagé et redondant. Voir [VMware Engine](#vmware-engine).

## Migrate for Compute Engine

Ancien nom de Migrate to Virtual Machines, le service de migration de VM vers Compute Engine. Voir [Migrate to Virtual Machines](#migrate-to-virtual-machines).

## Migrate for Anthos and GKE

Ancien nom de Migrate to Containers, l'outil qui convertit une VM en conteneur. Voir [Migrate to Containers](#migrate-to-containers).

## Birégion (dual-region)

Emplacement Cloud Storage formé d'une paire de régions précise : les données sont répliquées de façon asynchrone entre les deux, avec bascule automatique en cas de panne d'une région. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Réplication turbo (turbo replication)

Option des buckets birégionaux qui réplique 100 % des nouveaux objets dans les deux régions en 15 minutes au plus, quelle que soit leur taille (`--rpo=ASYNC_TURBO`). Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Durée minimale de stockage

Durée facturée au minimum pour un objet Nearline (30 jours), Coldline (90 jours) ou Archive (365 jours), même s'il est supprimé ou remplacé avant. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Frais de récupération (retrieval fees)

Frais au gibioctet lu, copié ou réécrit depuis une classe de stockage froide de Cloud Storage, en plus des opérations et du réseau. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Politique de conservation (Bucket Lock)

Durée minimale pendant laquelle aucun objet d'un bucket ne peut être supprimé ni remplacé, jusqu'à 100 ans. Une fois verrouillée, elle ne peut plus être réduite ni retirée. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Object Retention Lock

Conservation définie objet par objet dans Cloud Storage, avec une date de fin propre à chacun et un mode modifiable (`Unlocked`) ou définitif (`Locked`). Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Élagage de partitions (partition pruning)

Mécanisme par lequel BigQuery ne lit que les partitions retenues par un filtre constant sur la colonne de partition ; le clustering fait de même au niveau des blocs (*block pruning*). Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Filtre de partition obligatoire (require_partition_filter)

Option d'une table partitionnée BigQuery qui fait échouer toute requête sans filtre sur la colonne de partition. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Expiration de partition

Délai après lequel BigQuery supprime chaque partition d'une table partitionnée par date, calculé depuis la borne de la partition (`partition_expiration_days`). Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Stockage à long terme (BigQuery)

Tarif réduit d'environ moitié appliqué à une table ou une partition BigQuery non modifiée depuis 90 jours, sans différence de performances. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Table BigLake

Table BigQuery sur des fichiers externes (Cloud Storage, S3, Azure) dont l'accès passe par une connexion : l'utilisateur reçoit un droit sur la table, pas sur le bucket. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Délégation d'accès (access delegation)

Principe des tables BigLake et des tables d'objets : une connexion associée à un compte de service lit la source, et les utilisateurs n'ont besoin que d'un droit sur la table. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Vue matérialisée

Résultat précalculé d'une requête BigQuery, tenu à jour en arrière-plan ; les requêtes compatibles sont réacheminées vers elle automatiquement (*smart tuning*). Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Table Iceberg gérée (Apache Iceberg managed table)

Table BigQuery dont les données sont stockées en Parquet au format Iceberg dans un bucket du client, modifiable en DML et lisible par d'autres moteurs. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Requête continue (continuous query)

Requête SQL BigQuery qui tourne en permanence sur les lignes arrivant dans une table et écrit ses résultats dans une table, Pub/Sub, Bigtable ou Spanner ; elle demande une réservation Enterprise ou Enterprise Plus. Voir [Choisir le moteur de traitement](#choisir-un-moteur).

## Préparation de données BigQuery (BigQuery data preparation)

Éditeur visuel de BigQuery Studio qui propose, avec Gemini, des étapes de nettoyage et de transformation, planifiées ensuite par Dataform. Voir [Choisir le moteur de traitement](#choisir-un-moteur).

## Dataprep

Service de préparation visuelle de données édité par Alteryx (*Dataprep by Trifacta*), offre parallèle d'Alteryx Designer Cloud pour Google Cloud, hors du catalogue de Google. Voir [Choisir le moteur de traitement](#choisir-un-moteur).

## Cluster éphémère

Cluster Spark créé pour un job ou un workflow puis supprimé, les données restant dans Cloud Storage ou BigQuery. Voir [Choisir le moteur de traitement](#choisir-un-moteur).

## Déclencheur (Apache Beam)

Règle qui décide quand une fenêtre émet un résultat : au passage du filigrane, après un délai de traitement, ou après un nombre d'éléments. Plusieurs émissions successives sont possibles pour une même fenêtre. Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Retard autorisé (allowed lateness)

Durée pendant laquelle une fenêtre reste ouverte après le passage du filigrane, pour intégrer des données en retard. Elle vaut zéro par défaut : un élément en retard est alors ignoré. Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Mode d'accumulation

Choix, dans Apache Beam, de ce qu'émet une fenêtre à chaque déclenchement : le total depuis son ouverture (*accumulating*) ou seulement ce qui est arrivé depuis l'émission précédente (*discarding*). Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Heure de l'événement (event time)

Horodatage auquel un événement s'est produit à la source, par opposition à l'heure à laquelle le pipeline le traite (*processing time*). Les fenêtres de Beam se calculent sur l'heure de l'événement. Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Clé chaude (hot key)

Clé surreprésentée dans les données, que Dataflow traite en série sur un seul worker et qui ralentit tout le pipeline. On la redistribue ou on répartit l'agrégat (*fanout*). Voir [Dataflow](#dataflow).

## Retard du système (system lag)

Métrique Dataflow : temps maximal pendant lequel un élément attend ou est en cours de traitement, pour tout le pipeline ou par étape. Voir [Dataflow](#dataflow).

## Storage Write API

API d'écriture de BigQuery en gRPC, pour le flux comme pour le batch : flux par défaut (au moins une fois), flux *committed* avec *offsets* (exactement une fois), flux *pending* validés d'un bloc. Voir [BigQuery](#bigquery).

## Job de chargement (load job)

Job BigQuery qui lit des fichiers (Cloud Storage, fichier local) et les écrit dans une table, en tout ou rien. Gratuit sur le pool de slots partagé, limité à 1 500 par table et par jour. Voir [Batch : ETL ou ELT](#batch-etl-elt).

## Décorateur de partition

Suffixe `$` ajouté au nom d'une table BigQuery pour viser une partition, par exemple `ventes$20260923`. Avec `--replace`, un chargement n'écrase que cette partition. Voir [Batch : ETL ou ELT](#batch-etl-elt).

## Architecture médaillon

Organisation d'un lakehouse en trois couches de qualité croissante : bronze (brut), argent (nettoyé), or (exposé, prêt pour la BI). Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Binlog (journal binaire MySQL)

Journal des modifications d'une base MySQL, lu par les outils de CDC ; il doit être au format `ROW` et conservé assez longtemps pour couvrir un arrêt du flux. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Data mesh

Organisation où chaque domaine métier possède ses données et les publie comme des produits, avec un propriétaire et un contrat. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Dataset autorisé (authorized dataset)

Dataset BigQuery dont toutes les vues sont autorisées en bloc à lire un autre dataset, sans les déclarer une à une. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Domaine de données (data domain)

Regroupement logique des ressources d'un domaine métier dans Knowledge Catalog, indépendant des dossiers et projets, avec un propriétaire. Voir [Knowledge Catalog](#knowledge-catalog).

## GTID (Global Transaction Identifier)

Identifiant unique d'une transaction MySQL dans toute une topologie de réplication ; il permet à un flux CDC de survivre à la bascule vers une réplique. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Masquage dynamique des données

Remplacement à la lecture de la valeur d'une colonne BigQuery par `NULL`, une valeur par défaut ou un hachage, selon l'utilisateur qui interroge. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## max_staleness

Option de table BigQuery qui fixe l'obsolescence tolérée d'une table alimentée en CDC : elle arbitre entre fraîcheur des résultats et coût des fusions. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Mode ajout seul (Datastream)

Écriture où chaque changement de la source devient une nouvelle ligne BigQuery, avec son type d'opération, ce qui conserve tout l'historique. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Policy tag

Étiquette d'une taxonomie posée sur une colonne BigQuery ; seuls les titulaires du rôle *Fine-Grained Reader* sur le tag lisent la colonne en clair. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Politique d'accès aux lignes (row access policy)

Filtre attaché à une table BigQuery, qui restreint les lignes visibles par un groupe d'utilisateurs à chaque requête. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Slot de réplication (PostgreSQL)

Curseur de réplication logique qui retient le WAL tant que le consommateur ne l'a pas confirmé ; abandonné, il fait grossir le WAL sans limite. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Type unifié (Datastream)

Représentation commune et sans perte des types de données de toutes les sources Datastream, fondée sur les types Avro. Voir [Datastream](#datastream).

## Vue autorisée (authorized view)

Vue BigQuery autorisée à lire une table source : ses lecteurs n'ont de droit que sur la vue, pas sur la table. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## WAL (Write-Ahead Log)

Journal où une base écrit chaque opération avant de l'appliquer ; PostgreSQL le décode pour la réplication logique et le CDC. Voir [CDC : répliquer une base vers l'analytique](#cdc).

## Envoi composite parallèle (parallel composite upload)

Envoi d'un gros fichier vers Cloud Storage découpé en au plus 32 morceaux envoyés en parallèle, puis recomposés en un seul objet. L'objet obtenu n'a pas de somme MD5, seulement un CRC32C. Voir [Migrer et transférer des données](#migrations-transferts).

## Transfert hors ligne

Transfert de données par un support physique expédié plutôt que par le réseau, quand la liaison mettrait trop longtemps à écouler le volume. Voir [Transfer Appliance](#transfer-appliance).

## Pool d'agents (agent pool)

Groupe d'agents Storage Transfer Service, des conteneurs installés près d'un système de fichiers source, qui se partagent un transfert et un plafond de bande passante. Voir [Storage Transfer Service](#storage-transfer-service).

## Requête planifiée (scheduled query)

Requête GoogleSQL exécutée par BigQuery à intervalle régulier, au plus toutes les cinq minutes, avec les paramètres `@run_time` et `@run_date`. Elle repose sur le BigQuery Data Transfer Service. Voir [Orchestrer les pipelines](#orchestration).

## Date logique (logical date)

Date à laquelle une exécution d'un DAG Airflow se rattache, distincte de l'heure réelle d'exécution ; les tâches la reçoivent par les gabarits `{{ ds }}`, ce qui rend les relances et les rattrapages reproductibles. Voir [Orchestrer les pipelines](#orchestration).

## Catchup (Airflow)

Réglage d'un DAG Airflow qui lance, à sa mise en service, une exécution pour chaque intervalle écoulé depuis sa `start_date`. Activé par défaut en Airflow 2, désactivé en Airflow 3. Voir [Orchestrer les pipelines](#orchestration).

## Capteur (sensor, Airflow)

Tâche Airflow qui attend une condition — fichier présent, partition disponible, fin d'un autre DAG — avant de laisser partir la suite. Voir [Orchestrer les pipelines](#orchestration).

## Opérateur différable (deferrable operator)

Opérateur Airflow qui, pendant une attente, rend son *worker* et confie la surveillance au *triggerer*, au lieu d'occuper un emplacement d'exécution. Voir [Orchestrer les pipelines](#orchestration).

## Connecteur (Workflows)

Étape Workflows qui encapsule l'appel à une API Google Cloud : construction de la requête, authentification, et attente de la fin d'une opération longue. Voir [Workflows](#workflows).

## Instantané d'environnement (Airflow)

Sauvegarde d'un environnement Managed Airflow — dossiers du bucket, configuration, paquets PyPI, base Airflow — qui permet de le restaurer ou d'en recréer un identique. Voir [Orchestrer les pipelines](#orchestration).

## AutoML

Service d'Agent Platform qui entraîne un modèle sans code d'entraînement : il choisit l'architecture, les variables et les hyperparamètres à partir d'un dataset étiqueté. Il couvre les images (classification, détection d'objets) et les données tabulaires (classification, régression, prévision). Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Réglage supervisé (supervised tuning)

Réglage fin d'un modèle Gemini sur des exemples étiquetés entrée → sortie, pour fixer un comportement, un format ou un style que le prompt ne tient pas. La documentation recommande une centaine d'exemples ou plus. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## TabFM

Modèle de fondation pour données tabulaires, appelé dans BigQuery par `AI.PREDICT` : il reçoit une table d'exemples et une table à prédire, et fait de la régression ou de la classification sans entraînement préalable. Voir [BigQuery ML](#bigquery-ml).

## TimesFM

Modèle de fondation préentraîné pour les séries temporelles, appelé dans BigQuery par `AI.FORECAST` : il prévoit une série sans `CREATE MODEL`. Voir [BigQuery ML](#bigquery-ml).

## ARIMA_PLUS

Type de modèle BigQuery ML pour la prévision de séries temporelles, qui gère la tendance, la saisonnalité, les jours fériés et les anomalies, et entraîne des milliers de séries en une requête. `ARIMA_PLUS_XREG` y ajoute des covariables. Voir [BigQuery ML](#bigquery-ml).

## Clause TRANSFORM (BigQuery ML)

Partie d'un `CREATE MODEL` qui déclare le prétraitement des variables (mise à l'échelle, découpage en quantiles, encodage). Elle est enregistrée avec le modèle et réappliquée à l'identique à l'évaluation et à la prédiction. Voir [BigQuery ML](#bigquery-ml).

## Factorisation de matrices (matrix factorization)

Technique de recommandation qui décompose la matrice utilisateurs × articles en facteurs latents, à partir de notes explicites ou de retours implicites (clics, achats). Voir [BigQuery ML](#bigquery-ml).

## Fonction IA gérée (BigQuery)

Fonction SQL de BigQuery (`AI.IF`, `AI.CLASSIFY`, `AI.SCORE`, `AI.AGG`) qui applique Gemini à chaque ligne avec une syntaxe réduite : BigQuery choisit le modèle et construit le prompt. Voir [BigQuery ML](#bigquery-ml).

## Index vectoriel

Index BigQuery (IVF ou ScaNN) créé par `CREATE VECTOR INDEX`, qui fait passer `VECTOR_SEARCH` d'une comparaison exhaustive à une recherche approchée, plus rapide au prix d'un rappel un peu moindre. Voir [BigQuery ML](#bigquery-ml).

## Job d'entraînement serverless (CustomJob)

Job de Managed Training qui crée les machines demandées, exécute un conteneur d'entraînement puis les supprime ; facturé à la durée du job. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Ressource persistante (persistent resource)

Pool de machines d'entraînement gardé allumé entre les jobs pour garantir la capacité et supprimer le temps de provisionnement ; facturé tant qu'il tourne. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Réglage d'hyperparamètres (hyperparameter tuning)

Exécution répétée d'un entraînement avec des valeurs d'hyperparamètres différentes (trials), pour trouver celles qui optimisent une métrique. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Flex-start (Dynamic Workload Scheduler)

Stratégie d'ordonnancement où le job attend que tous ses GPU soient disponibles ensemble, puis s'exécute sans préemption. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Point de contrôle (checkpoint)

Sauvegarde périodique de l'état d'un modèle en cours d'entraînement, qui permet de reprendre après une interruption. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Alias de version (Model Registry)

Nom mobile (`default`, `prod`, `candidat`) qui désigne une version d'un modèle dans Model Registry, comme une étiquette Docker ou une branche Git. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Inférence par lots (batch inference)

Job asynchrone qui applique un modèle non déployé à un volume de données dans Cloud Storage ou BigQuery ; rien n'est facturé entre deux jobs. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Mise à zéro (scale to zero)

Capacité d'un service à descendre à zéro instance sans trafic, au prix d'un délai au premier appel. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Conteneur prédéfini (prebuilt container)

Image fournie par Google pour entraîner ou servir un modèle d'un cadre donné (TensorFlow, PyTorch, scikit-learn, XGBoost), avec une date de fin de disponibilité. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## KFP (Kubeflow Pipelines)

SDK Python qui décrit un pipeline ML comme un graphe de composants conteneurisés, compilé en YAML et exécuté par Agent Platform Pipelines. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Entraînement continu (continuous training)

Réentraînement automatique d'un modèle par un pipeline, déclenché par une planification, l'arrivée de données ou une alerte de surveillance. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Biais entraînement-service (training-serving skew)

Écart entre la distribution des caractéristiques vues à l'entraînement et celles reçues en production. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Dérive (drift)

Évolution dans le temps de la distribution des entrées ou des sorties d'un modèle en production. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Feature store

Dépôt centralisé des caractéristiques d'un modèle, qui sert les mêmes valeurs à l'entraînement et à l'inférence en ligne. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Vérité terrain (ground truth)

Étiquettes correctes, établies par des humains, auxquelles on compare les prédictions d'un modèle pour l'évaluer. Voir [MLOps : pipelines, suivi, surveillance](#mlops).

## Endpoint global

Point d'accès aux modèles de Gemini Enterprise Agent Platform sans région (`location="global"`) : la requête est servie par la région la plus disponible, ce qui réduit les erreurs 429, mais sans aucune garantie sur le lieu du traitement. Les endpoints multirégionaux `us` et `eu` gardent le traitement dans une juridiction. Voir [Choisir un modèle génératif](#choisir-un-modele).

## Disponibilité courte (modèle)

Régime de cycle de vie des modèles Gemini les plus récents : le modèle reste actif jusqu'à l'annonce d'une date de retrait, avec au moins 45 jours de préavis, au lieu d'une disponibilité garantie de douze mois. Voir [Choisir un modèle génératif](#choisir-un-modele).

## Réglage par préférence (preference tuning)

Réglage d'un modèle à partir de paires de réponses dont l'une est jugée meilleure que l'autre, quand la qualité se juge par comparaison plutôt que par une sortie exacte. Voir [Choisir un modèle génératif](#choisir-un-modele).

## Niveau de réflexion (thinking level)

Paramètre des modèles Gemini 3 (`MINIMAL`, `LOW`, `MEDIUM`, `HIGH`) qui règle la quantité de raisonnement interne produite avant la réponse ; ces jetons sont facturés en sortie et allongent la latence. Voir [Appeler Gemini depuis du code](#appeler-gemini).

## Signature de réflexion (thought signature)

Donnée opaque que Gemini joint à son tour de conversation quand il réfléchit ; elle doit être renvoyée telle quelle au tour suivant, notamment avec le résultat d'un appel de fonction, sous peine d'erreur 400. Voir [Appeler Gemini depuis du code](#appeler-gemini).

## Cache de contexte (context caching)

Réutilisation d'un préfixe de prompt déjà traité (document, instructions) : implicite et automatique, ou explicite avec une durée de vie ; les jetons servis depuis le cache coûtent 90 % de moins. Voir [Appeler Gemini depuis du code](#appeler-gemini).

## Standard PayGo

Mode de consommation par défaut des modèles Gemini : paiement au jeton sur une capacité partagée, avec un débit de référence par palier fixé selon les dépenses de l'organisation sur 30 jours. Priority PayGo et Flex PayGo en sont les variantes prioritaire et à prix réduit. Voir [Appeler Gemini depuis du code](#appeler-gemini).

## Provisioned Throughput

Débit réservé pour un modèle génératif, acheté en unités (GSU) sur un engagement d'une semaine à un an ; le trafic qui dépasse la réservation est servi et facturé en PayGo. Voir [Appeler Gemini depuis du code](#appeler-gemini).

## Rubrique adaptative (adaptive rubric)

Méthode d'évaluation où un modèle juge génère, pour chaque prompt, une liste de tests réussi ou échoué, puis vérifie la réponse contre chacun ; le score est le taux de réussite. Voir [Évaluer et sécuriser une application générative](#evaluer-et-securiser).

## Modèle juge (autorater)

Modèle de langue qui note ou compare les réponses d'un autre modèle selon des critères donnés ; ses biais (position, auto-préférence) se contrôlent par inversion des réponses et comparaison à des notes humaines. Voir [Évaluer et sécuriser une application générative](#evaluer-et-securiser).

## Injection de prompt (prompt injection)

Attaque qui glisse des instructions dans l'entrée d'un modèle — message de l'utilisateur ou document récupéré — pour lui faire ignorer ses consignes, divulguer des données ou déclencher des actions. Voir [Évaluer et sécuriser une application générative](#evaluer-et-securiser).

## Model Armor

Service Google Cloud qui inspecte prompts et réponses d'une application générative selon des modèles de filtres (injection de prompt, contenus nuisibles, données sensibles, URL malveillantes), en inspection seule ou avec blocage. Voir [Évaluer et sécuriser une application générative](#evaluer-et-securiser).

## Paramètres plancher (floor settings, Model Armor)

Configuration Model Armor minimale appliquée à tout un projet, un dossier ou une organisation, par exemple à chaque appel `generateContent` d'Agent Platform, sans modification du code. Voir [Évaluer et sécuriser une application générative](#evaluer-et-securiser).

## Reclassement (reranking)

Deuxième passe d'une récupération : un modèle note chaque fragment ramené contre la question et n'en garde que les plus pertinents, plus finement que la seule similarité d'embeddings. Sur Google Cloud, c'est le rôle de la ranking API. Voir [RAG : ancrer les réponses dans ses données](#rag).

## Recherche hybride (hybrid search)

Combinaison d'une recherche sémantique par embeddings et d'une recherche par mots-clés, fusionnées par rang, pour retrouver aussi les identifiants, codes et noms propres que les embeddings ratent. Voir [RAG : ancrer les réponses dans ses données](#rag).

## ANN (Approximate Nearest Neighbor)

Recherche des plus proches voisins approchée : un index (ScaNN, HNSW, IVF) évite de comparer la requête à tous les vecteurs, au prix d'une petite perte de rappel par rapport à la recherche exacte (KNN). Voir [RAG : ancrer les réponses dans ses données](#rag).

## ScaNN (Scalable Nearest Neighbors)

Algorithme de recherche de voisins approchée de Google Research, utilisé par Vector Search, l'index `scann` d'AlloyDB, les index vectoriels de Cloud SQL pour MySQL et l'index `TREE_AH` de BigQuery. Voir [RAG : ancrer les réponses dans ses données](#rag).

## RAG Engine

Service géré de Gemini Enterprise Agent Platform qui assemble une chaîne RAG réglable : corpus, import, découpage, embeddings, base vectorielle au choix et outil de récupération pour Gemini. Voir [RAG : ancrer les réponses dans ses données](#rag).

## Agent Retrieval

Moteur de récupération géré de Gemini Enterprise Agent Platform, anciennement Vector Search 2.0 : collections d'objets JSON, embeddings calculés par le service, recherches vectorielle, plein texte et sémantique combinées. Voir [RAG : ancrer les réponses dans ses données](#rag).

## Vector Search

Index de voisins approchés de Gemini Enterprise Agent Platform, anciennement Vertex AI Vector Search, servi sur un endpoint ; les documents sont stockés ailleurs. Voir [RAG : ancrer les réponses dans ses données](#rag).

## Type de tâche (task type)

Paramètre d'un modèle d'embeddings qui optimise le vecteur pour un usage : `RETRIEVAL_DOCUMENT` pour les fragments, `RETRIEVAL_QUERY` pour les questions, `CLASSIFICATION`, `CLUSTERING`… Voir [RAG : ancrer les réponses dans ses données](#rag).

## Injection de prompt indirecte

Attaque où des instructions cachées dans un document récupéré, une page web ou une réponse d'outil détournent le modèle qui les lit comme contexte. Voir [RAG : ancrer les réponses dans ses données](#rag).

## A2A (Agent2Agent)

Protocole ouvert par lequel un agent confie une tâche à un autre agent, traité comme un pair opaque : découverte par carte d'agent, tâches à états, messages et artefacts, sur JSON-RPC, gRPC ou HTTP/REST. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Carte d'agent (Agent Card)

Document JSON publié par un serveur A2A, en général à `/.well-known/agent-card.json` : identité, adresse, capacités, compétences et schémas d'authentification de l'agent. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Serveur MCP distant (Google Cloud)

Point de terminaison MCP géré par Google pour un produit, de la forme `https://SERVICE.googleapis.com/mcp`, contrôlé par IAM et utilisable dès que l'API du produit est activée. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## MCP Toolbox for Databases

Serveur MCP open source qui expose des requêtes SQL paramétrées, déclarées dans un fichier `tools.yaml`, sur les bases Google Cloud et d'autres moteurs. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Streamable HTTP

Transport MCP pour les serveurs distants : chaque message est un POST vers un point de terminaison unique, la réponse arrive en JSON ou en flux SSE propre à la requête. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Empoisonnement d'outils (tool poisoning)

Attaque où un serveur MCP glisse des consignes malveillantes dans la description d'un outil, que le modèle lit comme du contexte. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Agent comme outil (AgentTool)

Mécanisme d'ADK par lequel un agent en appelle un autre comme une fonction et garde la main sur la conversation, à la différence d'un sous-agent. Voir [Construire un agent avec ADK](#construire-un-agent).

## Workflow (ADK)

Graphe de nœuds (agents, fonctions, outils) dont le routage est codé, pour imposer l'ordre des étapes tout en laissant le modèle trancher à certains embranchements. Voir [Construire un agent avec ADK](#construire-un-agent).

## Memory Bank

Service d'Agent Platform qui extrait, par un modèle, les faits utiles des conversations d'un utilisateur et les restitue d'une session à l'autre. Voir [Construire un agent avec ADK](#construire-un-agent).

## Identité d'agent (Agent Identity)

Principal IAM propre à un agent déployé, fondé sur SPIFFE et lié à l'ID de sa ressource, avec un certificat X.509 auquel ses jetons sont liés. Voir [Déployer un agent](#deployer-un-agent).

## Agent Gateway

Point d'entrée et de sortie du trafic des agents dans Agent Platform : il n'autorise que les destinations inscrites dans Agent Registry et accordées par IAM, et applique Model Armor. Voir [Déployer un agent](#deployer-un-agent).

## Agent Registry

Catalogue d'Agent Platform des agents, serveurs MCP, outils et points de terminaison autorisés dans une organisation. Voir [MCP et A2A : outils et agents interopérables](#protocoles-mcp-a2a).

## Agent Engine

Nom que gardent la CLI ADK (`adk deploy agent_engine`), le fichier `.agent_engine_config.json` et l'API (`reasoningEngines`) pour Agent Runtime. Voir [Déployer un agent](#deployer-un-agent).

## Cible (Cloud Deploy target)

Environnement d'exécution vers lequel Cloud Deploy déploie : service Cloud Run, cluster GKE, cluster rattaché ou cible personnalisée, avec son exigence d'approbation et son environnement d'exécution. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Phase (Cloud Deploy)

Étape d'un rollout : une seule, `stable`, en déploiement standard, une par palier (`canary-25`, `canary-50`, puis `stable`) en canary. Chaque phase regroupe des jobs de déploiement, de vérification et d'analyse. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Multicible (multi-target)

Cible Cloud Deploy qui regroupe plusieurs cibles enfants et y déploie en parallèle, par exemple plusieurs régions de production. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Automatisation (Cloud Deploy)

Ressource attachée à un pipeline de livraison qui promeut une release, fait avancer les phases d'un canary ou répare un rollout en échec, selon des règles prédéfinies. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Politique de déploiement (deploy policy)

Ressource Cloud Deploy qui interdit les rollouts sur des fenêtres de temps choisies, pour geler les mises en production ; une exception demande un rôle dédié et reste tracée. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Déploiement bleu-vert (blue-green)

Stratégie qui déploie la nouvelle version à côté de l'ancienne, sans trafic, puis bascule tout le trafic d'un coup, avec retour immédiat possible. Voir [Cloud Deploy : livrer et promouvoir](#cloud-deploy-livrer).

## Contrôle par commentaire (comment control)

Réglage d'un déclencheur Cloud Build sur les pull requests GitHub : le build n'est lancé qu'après un commentaire `/gcbrun` d'un propriétaire ou d'un collaborateur du dépôt. Voir [Cloud Build : builds, déclencheurs, pools privés](#cloud-build-builds).

## Cache de couches (layer cache)

Réutilisation des couches d'une image déjà construite pour ne reconstruire que celles qui ont changé ; dans Cloud Build, par `--cache-from` sur l'image précédente. Voir [Cloud Build : builds, déclencheurs, pools privés](#cloud-build-builds).

## Construire une fois, déployer partout (build once, deploy many)

Principe de livraison selon lequel un même artefact, désigné par son digest, est promu d'environnement en environnement ; seule la configuration change. Voir [La chaîne CI/CD sur Google Cloud](#chaine-cicd).

## Provenance de build

Métadonnées signées qui décrivent comment un artefact a été construit : digest produit, dépôt et commit source, déclencheur, étapes, dépendances résolues. Cloud Build la produit au format in-toto, au niveau 3 de SLSA. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Attestor

Ressource Binary Authorization qui porte la clé publique servant à vérifier une attestation au déploiement. Cloud Build crée dans chaque projet l'attestor `built-by-cloud-build`. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Validation continue (Binary Authorization)

Surveillance des pods GKE déjà lancés, réexaminés au moins toutes les 24 heures selon une règle de plateforme (provenance SLSA, signature, vulnérabilités, fraîcheur) ; les écarts sont journalisés, aucun pod n'est arrêté. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Confusion de dépendances (dependency confusion)

Attaque qui publie sur un registre public un paquet portant le nom d'un paquet interne, pour qu'il soit installé à sa place. Un dépôt virtuel Artifact Registry qui donne priorité au dépôt privé la neutralise. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Assured OSS (Assured Open Source Software)

Paquets open source Java, Go, Python et JavaScript construits et analysés par Google, au niveau 3 de SLSA, avec provenance, SBOM et VEX, servis depuis un dépôt Artifact Registry géré par Google. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Analyse à la demande (On-Demand Scanning)

Analyse de vulnérabilités d'une image locale ou distante lancée par `gcloud artifacts docker images scan`, sans poussée dans un dépôt ; les résultats restent 48 heures. Sert à bloquer un build avant publication. Voir [Sécuriser la chaîne logicielle](#securiser-la-chaine).

## Dépôts Cloud Build (2e génération)

Connexions de Cloud Build aux forges GitHub, GitLab et Bitbucket, gérables par API, `gcloud` et Terraform, qui ajoutent aux déclencheurs de dépôt les déclencheurs manuels, Pub/Sub et webhook. Voir [Connecter un dépôt de code](#connecter-un-depot).

## Proxy Git (Developer Connect)

Serveur géré par Google par lequel passent les requêtes Git vers un dépôt connecté : l'appelant s'authentifie par IAM, sans jeton, et un dépôt sur réseau privé devient joignable. Lecture seule. Voir [Connecter un dépôt de code](#connecter-un-depot).

## Cloud Source Repositories

Hébergement Git de Google Cloud fermé aux nouveaux clients : une organisation qui ne l'a jamais utilisé ne peut pas en activer l'API. Secure Source Manager est l'hébergement proposé à la place. Voir [Connecter un dépôt de code](#connecter-un-depot).

## Mappage d'attributs

Expressions CEL qui tirent des claims du jeton externe les attributs du jeton Google (`google.subject`, `attribute.NOM`), sur lesquels portent ensuite la condition d'attribut et les liaisons IAM. Voir [Déployer sans clé](#deployer-sans-cle).

## Principal fédéré (principal, principalSet)

Identité externe admise dans un pool d'identités de charge de travail, désignée dans IAM par `principal://…/subject/SUJET` pour une seule, ou `principalSet://…/attribute.NOM/VALEUR` pour un ensemble. Voir [Déployer sans clé](#deployer-sans-cle).

## Security Token Service (STS)

Service Google qui échange un jeton externe (OIDC, SAML, AWS) contre un jeton fédéré de courte durée, après vérification de la signature et de la condition d'attribut. Voir [Déployer sans clé](#deployer-sans-cle).

## Canal de notification

Destination d'une règle d'alerte de Cloud Monitoring, réutilisée par Error Reporting : e-mail, SMS, application mobile, Slack, PagerDuty, webhook, Pub/Sub ou Google Chat. Voir [Notifications et tickets : Slack, Jira et les autres](#notifications-tickets).

## Notifier (Cloud Build)

Image fournie par Cloud Build, déployée sur Cloud Run et abonnée au sujet des builds, qui filtre les événements en CEL et les transmet à Slack, un serveur SMTP, un point HTTP, BigQuery, Google Chat ou GitHub Issues. Voir [Notifications et tickets : Slack, Jira et les autres](#notifications-tickets).

## Incoming webhook (Slack)

URL propre à un canal Slack, qui publie un message reçu en POST JSON ; elle contient son propre secret. Voir [Notifications et tickets : Slack, Jira et les autres](#notifications-tickets).

## Data source syncer

Job de Managed Service for Prometheus qui génère un jeton d'accès Google toutes les 10 minutes et le réécrit dans une source Prometheus de Grafana par l'API de Grafana. Voir [Brancher Grafana sur Google Cloud](#grafana).

## Source de données (Grafana)

Connexion de Grafana à un système interrogeable (Cloud Monitoring, Prometheus, Cloud Logging, BigQuery), avec son type, son authentification et ses réglages ; elle se provisionne en YAML. Voir [Brancher Grafana sur Google Cloud](#grafana).

## MQL (Monitoring Query Language)

Langage de requête de Cloud Monitoring à opérations chaînées, hors support Google et absent de la console ; les requêtes existantes tournent encore par l'API. PromQL le remplace. Voir [Brancher Grafana sur Google Cloud](#grafana).

## OpenTofu

Fork libre de Terraform, sous licence MPL-2.0 et hébergé par la Linux Foundation : il lit la même configuration HCL, utilise les mêmes fournisseurs, et peut chiffrer lui-même l'état. Voir [Choisir un outil d'Infrastructure as Code](#choisir-un-outil-iac).

## Pulumi

Outil d'Infrastructure as Code qui décrit les ressources en Python, TypeScript, Go, C#, Java ou YAML ; son fournisseur `gcp` est construit à partir du fournisseur Terraform `google-beta`. Voir [Choisir un outil d'Infrastructure as Code](#choisir-un-outil-iac).

## Config Controller

Plan de contrôle hébergé par Google qui embarque Config Connector, Config Sync et Policy Controller, pour gérer des ressources Google Cloud en GitOps sans installer de cluster soi-même. Voir [Choisir un outil d'Infrastructure as Code](#choisir-un-outil-iac).

## Backend Terraform

Emplacement où Terraform stocke et verrouille son état ; sur Google Cloud, le backend `gcs` le range dans un bucket Cloud Storage, un préfixe par état. Voir [Terraform sur Google Cloud](#terraform-sur-gcp).

## Bloc import (Terraform)

Bloc de configuration (Terraform 1.5 et plus) qui fait entrer une ressource existante dans l'état : l'import se prévisualise au `plan` et s'exécute à l'`apply`. Voir [Terraform sur Google Cloud](#terraform-sur-gcp).

## Argument write-only

Argument d'une ressource Terraform, suffixé `_wo`, dont la valeur est transmise à l'API sans jamais être écrite dans le plan ni dans l'état ; il demande Terraform 1.11 ou plus. Voir [Terraform sur Google Cloud](#terraform-sur-gcp).

## Project factory

Module Terraform qui crée des projets Google Cloud normalisés (dossier, facturation, API activées, IAM, budgets) à partir d'une description courte, un appel par projet. Voir [Terraform sur Google Cloud](#terraform-sur-gcp).

## Cloud Foundation Toolkit

Ensemble de modules Terraform et de *blueprints* maintenus par Google, publiés sous l'organisation GitHub `terraform-google-modules`. Voir [Terraform sur Google Cloud](#terraform-sur-gcp).

## Configuration de release (Dataform)

Modèle de compilation d'un dépôt Dataform : branche, tag ou commit à compiler, *overrides* (projet, suffixe de schéma, préfixe de table, variables) et fréquence de compilation. Une par environnement ; elle alimente les configurations de workflow. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Configuration de workflow (Dataform)

Planification Dataform qui exécute, à l'horaire choisi et avec un compte de service donné, les actions sélectionnées du dernier résultat de compilation d'une configuration de release. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Compilation override (Dataform)

Réglage qui modifie la sortie d'une compilation Dataform sans toucher au code : projet cible, suffixe de schéma, préfixe de table, valeur de variable. Sert à isoler dev, staging et prod. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Espace de développement (Dataform)

Copie de travail d'un dépôt Dataform, propre à un développeur et reliée à une branche Git, dans laquelle on édite, compile et exécute à la main avant de pousser. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Test unitaire (Dataform)

Fichier SQLX de type `test` qui remplace les dépendances d'une action par des lignes simulées et compare le résultat à une sortie attendue ; lancé par `dataform test`. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Modèle Flex (Flex Template)

Modèle Dataflow composé d'une image de conteneur qui contient le pipeline et d'un fichier de spécification JSON dans Cloud Storage ; construit par `gcloud dataflow flex-template build`, lancé par `flex-template run`. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Job de remplacement (Dataflow)

Nouveau job de flux lancé avec `--update` sous le même nom et dans la même région qu'un job en cours, qui reprend son état après un contrôle de compatibilité ; `graph_validate_only` fait ce contrôle sans rien remplacer. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Composer Local Development CLI

Outil `composer-dev` qui lance en local, dans Docker ou Podman, l'image Airflow d'une version de Managed Service for Apache Airflow pour tester des DAG. Voir [CI/CD pour la data et l'IA](#cicd-data-ia).

## Émulateur local (gcloud)

Version en mémoire d'un service — Pub/Sub, Firestore, Datastore, Spanner, Bigtable — lancée par `gcloud emulators` ou `gcloud beta emulators` ; les bibliothèques clientes s'y connectent quand la variable `*_EMULATOR_HOST` est définie. Voir [Le poste de développement](#poste-de-developpement).

## Functions Framework

Bibliothèque libre qui sert une fonction Cloud Run en HTTP sur le poste, sans conteneur (`functions-framework --target=NOM`). Voir [Le poste de développement](#poste-de-developpement).

## Zone d'atterrissage (landing zone)

Socle posé avant la première application : organisation, dossiers, projets partagés, règles d'administration de base, groupes IAM, réseau partagé et journaux centralisés. Tout ce qui s'y trouve s'hérite vers les projets des équipes. Voir [Organiser l'environnement : organisation, dossiers, projets](#hierarchie-des-ressources).

## Super administrateur (Cloud Identity)

Compte d'administration de Cloud Identity ou Google Workspace qui contourne l'authentification unique pour pouvoir réparer une fédération en panne. Il se réserve aux urgences, avec une clé de sécurité physique, et ne sert pas à administrer Google Cloud au quotidien. Voir [Organiser l'environnement : organisation, dossiers, projets](#hierarchie-des-ressources).

## Contacts essentiels (Essential Contacts)

Destinataires, définis sur l'organisation, un dossier ou un projet, des notifications importantes de Google : suspension de compte, évolution des conditions, avis de sécurité, facturation. Voir [Organiser l'environnement : organisation, dossiers, projets](#hierarchie-des-ressources).

## Puits agrégé (aggregated sink)

Puits de journaux posé sur une organisation ou un dossier avec l'option `--include-children`, qui recopie les journaux de tous les projets descendants vers une destination unique. Un puits interceptant empêche en plus les projets de les router eux-mêmes. Voir [Organiser l'environnement : organisation, dossiers, projets](#hierarchie-des-ressources).

## Mode simulation (règle d'administration)

Règle d'administration appliquée en *dry-run* : chaque configuration qu'elle interdirait est inscrite dans les journaux d'audit, sans être refusée. Sert à mesurer l'effet d'une règle avant de l'imposer. Voir [Organiser l'environnement : organisation, dossiers, projets](#hierarchie-des-ressources).

## Projet d'amorçage (seed project)

Projet créé à la main, une fois, dans le dossier d'amorçage : il porte le bucket d'état de l'IaC, la clé de chiffrement des secrets et les comptes de service des pipelines qui construisent le reste de la fondation. Voir [Construire les fondations en code (Pulumi)](#fondations-en-code).

## Stack (Pulumi)

Instance d'un projet Pulumi avec sa propre configuration et son propre état, en général une par environnement (`dev`, `prod`). Une stack lit les sorties d'une autre par `StackReference`. Voir [Construire les fondations en code (Pulumi)](#fondations-en-code).

## Fournisseur de secrets (Pulumi)

Mécanisme qui chiffre les valeurs secrètes de la configuration et de l'état d'une stack Pulumi : phrase de passe, Pulumi Cloud, ou clé de service de chiffrement comme Cloud KMS (`gcpkms://`). Voir [Construire les fondations en code (Pulumi)](#fondations-en-code).

## Policy pack (Pulumi Policies)

Ensemble versionné de règles, écrites en Python, TypeScript ou Rego, que Pulumi évalue sur chaque ressource pendant `preview` et `up` ; une règle obligatoire en échec bloque le déploiement. Voir [Construire les fondations en code (Pulumi)](#fondations-en-code).

## Plafond de dépense (spend cap)

Type de budget Cloud Billing, en aperçu, limité à un projet et à un service éligible (Gemini API, Gemini Enterprise Agent Platform, Cloud Run, Cloud Run functions) : au-delà du montant mensuel, tout nouvel usage du service est mis en pause jusqu'à levée manuelle, sans suppression de ressources. Le déclenchement repose sur des coûts bruts estimés et n'est pas instantané. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Notification programmatique de budget

Message publié par Cloud Billing sur un sujet Pub/Sub plusieurs fois par jour, avec l'état courant du budget (`costAmount`, `budgetAmount`, seuils dépassés). Il sert à déclencher une réaction automatique : message Slack, arrêt de ressources, coupure de la facturation. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Profil de paiement Google (payments profile)

Objet de niveau Google, partagé avec les autres services Google, qui porte l'identité fiscale, l'adresse et les moyens de paiement auxquels un compte de facturation Cloud Billing est rattaché. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Export de facturation vers BigQuery

Alimentation automatique, au fil de la journée, de tables BigQuery avec les coûts du compte de facturation : usage standard, usage détaillé par ressource, tarifs, format FOCUS. L'historique n'est repris que sur un dataset multirégional, et seulement pour le mois en cours et le précédent. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Quota personnalisé de requêtes (BigQuery)

Plafond du volume de données lu par jour en tarification à la demande, par projet (`QueryUsagePerDay`) ou par utilisateur (`QueryUsagePerUserPerDay`) ; au-delà, les requêtes sont refusées. Voir [Facturation, budgets et plafonds de coût](#facturation-et-budgets).

## Engagement flexible (compute flexible CUD)

Remise sur engagement fondée sur un montant horaire de dépense, valable sur Compute Engine, GKE et Cloud Run quels que soient projet, région et série de machines ; le montant est dû chaque heure, consommé ou non. Voir [Optimiser les coûts](#optimiser-les-couts).

## Requête batch (BigQuery)

Requête de priorité basse, mise en file quand le projet ou la réservation n'a plus de capacité, puis exécutée comme une requête interactive ; son prix est le même. Voir [Optimiser les coûts](#optimiser-les-couts).

## Slots inactifs (idle slots)

Slots d'engagement non affectés, ou slots de base d'une réservation qui ne sont pas utilisés ; BigQuery les prête aux autres réservations de la même édition et du même projet d'administration. Voir [Optimiser les coûts](#optimiser-les-couts).

## FinOps hub

Tableau de bord d'optimisation du compte de facturation : économies réalisées, score, utilisation des engagements et recommandations de coût issues de Recommender. Voir [Optimiser les coûts](#optimiser-les-couts).

## Well-Architected Framework

Référentiel de conception de Google Cloud : cinq principes fondamentaux, six piliers (excellence opérationnelle, sécurité, fiabilité, coûts, performances, durabilité) et des perspectives transverses (IA et ML, services financiers). Voir [Le Well-Architected Framework de Google](#well-architected).

## Responsabilité partagée et destin partagé (shared fate)

Répartition de la sécurité entre fournisseur et client selon le type de service (IaaS, PaaS, SaaS) ; le destin partagé y ajoute l'engagement de Google à fournir des configurations sûres par défaut, des blueprints et des outils de gouvernance. Voir [Le Well-Architected Framework de Google](#well-architected).

## ADR (Architecture Decision Record)

Court document, rangé près du code, qui consigne une décision d'architecture : le contexte, les options envisagées, les exigences qui ont tranché. Voir [Le Well-Architected Framework de Google](#well-architected).

## Domaine de défaillance (failure domain)

Ressource ou groupe de ressources qui peut tomber en panne indépendamment des autres : une VM, une zone, une région. Répartir une application sur plusieurs domaines relève sa disponibilité. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Archétype de déploiement (deployment archetype)

Modèle abstrait qui fixe les domaines de défaillance sur lesquels tourne une application : zonal, régional, multirégional, global, hybride ou multicloud. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Multirégion (multi-region)

Emplacement couvrant une grande zone géographique (`US`, `EU`) : Cloud Storage et Spanner y répliquent entre plusieurs régions, BigQuery y range les données dans une seule région. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Disponibilité composée

Disponibilité d'une pile d'étages interdépendants, produit des disponibilités de chaque étage : elle est toujours inférieure à celle de l'étage le plus faible. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Reprise froide, tiède ou chaude (cold, warm, hot)

Modèles de reprise d'activité selon ce qui tourne dans le site de secours : rien que des sauvegardes (froid), des données répliquées et un calcul réduit (tiède), une pile complète prête à prendre le trafic (chaud). Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Actif-actif

Architecture où plusieurs régions servent le trafic en même temps, sur des données répliquées ; la perte d'une région ne demande aucune bascule. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Basculement et retour (failover, failback)

Passage du service sur la ressource de secours quand la principale tombe, puis retour sur la principale une fois rétablie ; l'un ou l'autre peut être automatique ou manuel selon le produit. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Switchover (Cloud SQL)

Inversion planifiée des rôles entre une instance Cloud SQL Enterprise Plus et sa réplique de reprise désignée, sans perte de données ; elle sert aussi aux exercices de reprise. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Retard de réplication (replication lag)

Écart entre la validation d'une transaction sur le primaire et son application sur une réplique asynchrone ; il borne le RPO d'une bascule vers cette réplique. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Double primaire (split brain)

Situation où deux copies d'une base acceptent chacune des écritures après une bascule, et divergent ; la réconciliation est manuelle. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Réplication asynchrone de disque (Asynchronous Replication)

Copie continue d'un volume Persistent Disk ou Hyperdisk vers une autre région, avec un RPO visé d'une minute et une bascule manuelle. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Reprise après sinistre gérée (BigQuery)

Bascule d'une réservation Enterprise Plus et de ses datasets répliqués vers une région secondaire, en mode *soft* (sans perte, les deux régions disponibles) ou *hard* (immédiat, perte possible). Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Fault Injection Testing

Service Google Cloud, en Preview sur demande, qui injecte des pannes dans des ressources pour éprouver la résilience d'une application. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Démarrage à froid (cold start)

Délai supplémentaire d'une requête qui doit attendre le démarrage d'une nouvelle instance, parce qu'aucune n'est disponible ou que le service est descendu à zéro. Sur Cloud Run, les instances minimales et le *startup CPU boost* le réduisent. Voir [Choisir le calcul : VMs, GKE, Cloud Run](#choisir-le-calcul).

## Contrat de conteneur (Cloud Run)

Conditions qu'une image doit remplir pour tourner sur Cloud Run : écouter sur le port fourni par la variable `PORT` pour un service, s'exécuter en `linux/amd64`, ne pas compter sur un système de fichiers local persistant, démarrer en moins de 4 minutes. Voir [Choisir le calcul : VMs, GKE, Cloud Run](#choisir-le-calcul).

## ComputeClass (GKE)

Ressource Kubernetes de GKE qui décrit le matériel qu'une charge exige (série de machines, Spot, GPU, Arm) et l'ordre des solutions de repli en cas de pénurie ; elle vaut en mode Standard comme en Autopilot. Voir [Choisir le calcul : VMs, GKE, Cloud Run](#choisir-le-calcul).

## RFC 1918

Norme qui réserve trois blocs d'adresses IPv4 privées : `10.0.0.0/8`, `172.16.0.0/12` et `192.168.0.0/16`. Un réseau VPC accepte aussi d'autres plages non publiques, comme `100.64.0.0/10` (RFC 6598) ou `240.0.0.0/4` (classe E). Voir [Concevoir le réseau VPC](#concevoir-le-reseau).

## Mode de routage dynamique

Réglage d'un réseau VPC qui décide où s'appliquent les routes apprises en BGP par un Cloud Router : dans sa seule région (*régional*) ou dans toutes (*global*). Il décide aussi quels sous-réseaux le Cloud Router annonce au réseau distant. Voir [Concevoir le réseau VPC](#concevoir-le-reseau).

## Zone d'appairage (DNS)

Zone privée Cloud DNS qui délègue la résolution d'un domaine à l'ordre de résolution d'un autre réseau VPC ; c'est ainsi que plusieurs réseaux s'appuient sur un même hub DNS. Voir [Concevoir le réseau VPC](#concevoir-le-reseau).

## Règle de serveur DNS (server policy)

Réglage Cloud DNS attaché à un réseau VPC. Une règle **entrante** attribue au résolveur du réseau des adresses que le réseau du site peut interroger ; une règle **sortante** envoie toutes les requêtes du réseau vers des serveurs de substitution. Voir [Concevoir le réseau VPC](#concevoir-le-reseau).

## Sous-réseau proxy uniquement (proxy-only subnet)

Sous-réseau réservé aux proxys Envoy que Google exploite pour les load balancers régionaux, internes et interrégionaux, avec l'objectif `REGIONAL_MANAGED_PROXY` ou `GLOBAL_MANAGED_PROXY`. Un seul actif par réseau, par région et par objectif, d'au moins `/26`. Voir [Choisir un load balancer](#choisir-un-load-balancer).

## Accès global (load balancer interne)

Option de la règle de transfert d'un load balancer interne régional qui le rend joignable depuis des clients de toutes les régions, et non de sa seule région. Voir [Choisir un load balancer](#choisir-un-load-balancer).

## NEG sans serveur (serverless NEG)

Groupe de points de terminaison qui désigne un service Cloud Run, une fonction ou une application App Engine d'une région, pour en faire le backend d'un Application Load Balancer. Il n'a ni adresse ni port, et pas de contrôle d'état. Voir [Choisir un load balancer](#choisir-un-load-balancer).

## Retour direct du serveur (direct server return)

Mode des load balancers passthrough : le backend reçoit les paquets avec l'adresse du client et lui répond directement, sans repasser par le load balancer. Voir [Choisir un load balancer](#choisir-un-load-balancer).

## Détection d'anomalies (outlier detection)

Analyse, par le load balancer, des réponses de chaque backend : ceux qui renvoient trop d'erreurs sont écartés temporairement de la répartition. Sur un NEG sans serveur, elle tient lieu de contrôle d'état. Voir [Choisir un load balancer](#choisir-un-load-balancer).

## Clé d'autorisation (authorization key)

Clé API liée à un compte de service : l'appel est traité comme s'il venait de ce compte, à la manière d'un jeton d'accès longue durée. Réservée à l'exploration (mode express de Vertex AI, API Gemini) et limitée par une contrainte d'organisation active par défaut. Voir [Authentifier un appel à une API](#authentifier-un-appel).

## Serveur de métadonnées

Point de terminaison interne présent sur les VM, les services Cloud Run et les pods GKE, qui fournit au code des jetons courts du compte de service attaché ; c'est la dernière source consultée par ADC. Voir [Authentifier un appel à une API](#authentifier-un-appel).

## Projet de quota (quota project)

Projet facturé et décompté pour un appel d'API fait avec des identifiants d'utilisateur, désigné par l'en-tête `x-goog-user-project` ou la configuration d'ADC. Voir [Authentifier un appel à une API](#authentifier-un-appel).

## Compte de service par défaut

Compte de service créé automatiquement par certains services (Compute Engine, App Engine), qui reçoit le rôle Editor sur le projet sauf si une contrainte d'organisation l'interdit ; à remplacer par un compte dédié en production. Voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques).

## Privileged Access Manager (PAM)

Service d'accès juste-à-temps de Google Cloud : un droit (*entitlement*) définit qui peut demander quels rôles, pour quelle durée maximale et avec quelle approbation ; les rôles sont retirés automatiquement à l'expiration. Voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques).

## Version d'application (Principal Access Boundary)

Numéro qui fixe la liste des permissions qu'une stratégie Principal Access Boundary sait bloquer ; les permissions absentes de cette version restent utilisables partout. Voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques).

## Policy Intelligence

Ensemble d'outils d'analyse des accès : Policy Analyzer (qui a accès à quoi), Policy Troubleshooter (pourquoi un accès est accordé ou refusé), Policy Simulator (effet d'une modification avant de l'appliquer) et recommandations de rôles. Voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques).

## Google Cloud Directory Sync (GCDS)

Outil gratuit de Google qui synchronise à sens unique les utilisateurs et les groupes d'Active Directory ou d'un annuaire LDAP vers Cloud Identity ou Google Workspace, sans les mots de passe. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Validation en deux étapes (2SV)

Second facteur exigé à la connexion d'un compte Google (clé de sécurité, passkey, invite Google, code), imposé progressivement pour accéder à la console Google Cloud. Avec le SSO, le second facteur de l'IdP en tient lieu. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Super-administrateur

Rôle d'administration le plus élevé d'un compte Cloud Identity ou Workspace, qui s'étend à l'organisation Google Cloud associée ; il n'est pas redirigé vers l'IdP en SSO et se protège par des comptes dédiés et une clé de sécurité. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Console (fédérée)

Version de la console Google Cloud destinée aux utilisateurs d'un pool de fédération d'identité de personnel, qui n'ont pas de compte Google ; certains produits n'y sont pas disponibles. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Groupe de sécurité

Groupe Google étiqueté pour le contrôle d'accès, distinct d'une liste de diffusion ; l'étiquette ne peut pas être retirée. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Chrome Enterprise Premium

Offre *zero trust* de Google : accès contextuel selon l'identité, l'appareil et le lieu, protection contre la fuite de données et l'hameçonnage dans Chrome ; sa licence est requise pour les niveaux d'accès fondés sur l'état de l'appareil dans IAP. Voir [Identités des utilisateurs](#identites-des-utilisateurs).

## Autokey

Fonction de Cloud KMS qui crée à la demande le trousseau, la clé CMEK protégée par HSM et le rôle de l'agent de service au moment où une ressource est créée, sans droit élevé pour le développeur ni pour le pipeline IaC. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Cloud HSM mono-locataire (Single-tenant Cloud HSM)

Instance de partitions HSM dédiée à un seul client, administrée par un quorum d'administrateurs qui détiennent des clés de contrôle hors de Google, et qui doit être rafraîchie au moins tous les 730 jours. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Destruction cryptographique (crypto-shredding)

Effacement de données par la destruction de la clé qui les chiffre : toutes les copies, sauvegardes comprises, deviennent illisibles d'un coup. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Confidential Computing

Chiffrement des données en cours d'utilisation, en mémoire, par un environnement d'exécution de confiance (TEE) matériel avec attestation à distance : Confidential VM, Confidential GKE Nodes, Confidential Space. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Confidential Space

Environnement de confiance où une charge conteneurisée, sur une image durcie en Confidential VM, ne reçoit les données ou secrets de plusieurs parties qu'après attestation ; l'opérateur lui-même n'y a pas accès. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Key Access Justifications

Service qui joint à chaque opération sur une clé Cloud KMS un code de justification, que le gestionnaire de clés externe peut utiliser pour refuser l'opération. Voir [Chiffrement : Cloud KMS, HSM, EKM](#chiffrement).

## Exfiltration de données

Sortie non autorisée de données hors de l'organisation, par un identifiant volé, un initié ou du code compromis, par exemple une copie de table vers un projet extérieur. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Règle d'entrée (ingress rule)

Règle VPC Service Controls qui autorise un client situé hors d'un périmètre, désigné par son identité et son origine, à appeler des méthodes précises sur des ressources du périmètre. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Règle de sortie (egress rule)

Règle VPC Service Controls qui autorise un appel mettant en jeu, depuis le périmètre, une ressource située hors de celui-ci, quel que soit le sens de la donnée. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Pont de périmètre (perimeter bridge)

Liaison bidirectionnelle entre projets de deux périmètres VPC Service Controls d'une même organisation ; les règles d'entrée et de sortie, plus fines, sont recommandées à sa place. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Stratégie d'accès (access policy)

Conteneur Access Context Manager des périmètres de service et des niveaux d'accès : une seule pour l'organisation, plus des stratégies à portée réduite sur des dossiers ou projets pour déléguer l'administration. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Services accessibles depuis le VPC (VPC accessible services)

Liste des API Google que les réseaux VPC d'un périmètre ont le droit d'appeler ; la valeur `RESTRICTED-SERVICES` reprend les services protégés par le périmètre. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## VIP restreinte (restricted.googleapis.com)

Plage d'adresses 199.36.153.4/30, non annoncée sur internet, qui ne sert que les API compatibles avec VPC Service Controls ; on y dirige le DNS des API Google pour empêcher l'accès aux services non couverts. Voir [Périmètres : VPC Service Controls](#perimetres-vpc-sc).

## Tokenisation

Remplacement d'une valeur sensible par un jeton chiffré. Avec le chiffrement déterministe de Sensitive Data Protection (AES-SIV), la même valeur donne toujours le même jeton, ce qui garde les jointures possibles, et le détenteur de la clé Cloud KMS peut revenir à la valeur. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Chiffrement préservant le format (FPE)

Tokenisation qui produit un jeton de même longueur et du même alphabet que la valeur d'origine (mode FFX), pour les systèmes qui valident le format. Plus lente et plus contrainte que le chiffrement déterministe, à réserver à ce cas. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Décalage de dates (date shifting)

Transformation de Sensitive Data Protection qui décale chaque date d'un nombre de jours aléatoire, identique pour toutes les dates d'une même entité : les durées entre événements restent justes, les dates réelles disparaissent. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Profil de données (Sensitive Data Protection)

Résultat de la découverte de Sensitive Data Protection pour une table, un bucket ou une base : infoTypes trouvés, niveau de sensibilité et risque de données, calculés sans copier les données. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Politique de données (data policy)

Ressource BigQuery qui associe une règle de masquage (ou l'accès brut) à des principaux, posée sur un *policy tag* ou directement sur une colonne. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Fail-safe (BigQuery)

Période de sept jours, non configurable, qui suit la fenêtre de *time travel* et pendant laquelle BigQuery conserve encore les données supprimées pour une récupération d'urgence. Voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance).

## Access Approval

Contrôle qui exige une approbation explicite du client, signée, avant tout accès du personnel de Google aux données ; les demandes arrivent par e-mail ou Pub/Sub. Voir [Détection et conformité](#detection-et-conformite).

## Event Threat Detection

Service de Security Command Center Premium qui analyse en continu le flux Cloud Logging (journaux d'audit, réseau, DNS) pour détecter menaces et compromissions, et écrit des résultats. Voir [Détection et conformité](#detection-et-conformite).

## Règle de mise en sourdine (mute rule)

Règle de Security Command Center qui met en sourdine les résultats correspondant à un filtre, pour documenter un risque accepté sans le supprimer. Voir [Détection et conformité](#detection-et-conformite).

## Compliance Manager

Fonction de Security Command Center qui déploie des cadres de conformité (CIS, NIST, PCI DSS...) sous forme de contrôles cloud, détecte les écarts et, en Premium, collecte les preuves d'audit. Voir [Détection et conformité](#detection-et-conformite).

## Signaux dorés (golden signals)

Les quatre mesures que le livre SRE de Google retient pour un service exposé aux utilisateurs : latence, trafic, erreurs et saturation. Voir [Observer : métriques, journaux, traces, SLO](#observabilite).

## Observability Analytics

Interrogation en SQL des buckets de journaux et des spans dans la console Google Cloud, après activation de l'analyse sur le bucket ; la page de tarifs l'appelle Log Analytics. Voir [Observer : métriques, journaux, traces, SLO](#observabilite).

## Filtre d'exclusion (Cloud Logging)

Filtre posé sur un puits de journaux qui écarte les entrées correspondantes de sa destination, et donc de la facture d'ingestion de ce bucket ; la fonction `sample()` en exclut une fraction. Voir [Observer : métriques, journaux, traces, SLO](#observabilite).

## Taux de consommation (burn rate)

Rapport entre le taux d'erreur observé et celui qui épuiserait exactement le budget d'erreur en fin de période : 1 tient l'objectif, 14,4 épuise un budget de 30 jours en deux jours. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Alerte multi-fenêtres

Alerte sur le taux de consommation qui exige le dépassement du seuil sur une fenêtre longue et sur une fenêtre courte à la fois, pour éviter les faux positifs et retomber vite après le problème. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Fenêtre de réévaluation (retest window)

Durée pendant laquelle une condition d'alerte Cloud Monitoring doit rester vraie avant d'ouvrir une alerte ; champ `duration` de l'API. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Mise en sourdine (snooze)

Suspension temporaire d'une règle d'alerte Cloud Monitoring, par exemple pendant une maintenance ; elle ferme les alertes ouvertes de la règle. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Fatigue d'alerte

Perte de vigilance d'une astreinte exposée à trop d'alertes sans action utile ; on la combat en n'alertant que sur des symptômes. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Runbook

Procédure écrite d'intervention sur une alerte : tri, investigation, communication, escalade, contacts. Dans Cloud Monitoring, on la place dans la documentation de la règle. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Postmortem

Compte rendu écrit d'un incident, sans recherche de coupable : impact, faits, causes, actions correctives. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Personalized Service Health

Service qui signale les incidents Google Cloud touchant les produits et régions d'un projet ou d'une organisation, par tableau de bord, API et journaux. Voir [Alerter et gérer les incidents](#alertes-et-incidents).

## Traînard (straggler)

Dans un job Dataflow, *work item* nettement plus lent que les autres de la même étape : il retient la fin de l'étape en lots, le filigrane en flux. Les détails d'exécution le signalent avec sa cause probable (clé chaude, worker lent). Voir [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).

## Fusion (Dataflow)

Optimisation par laquelle Dataflow regroupe plusieurs transformations consécutives en une seule étape, sans matérialiser les données entre elles. Elle peut limiter le parallélisme après une source peu parallèle ; un `Reshuffle` (ou `Redistribute`) l'interrompt. Voir [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).

## Détecteur de goulots (bottleneck detector)

Fonction de Dataflow qui signale, dans un job en flux, le composant en retard de plus de cinq minutes et le classe : bloqué, en retard croissant, en retard stable ou en rattrapage. Voir [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).

## Backlog (Dataflow)

Volume de données non encore traité par une étape d'un pipeline, en octets, en éléments ou, avec Streaming Engine, en secondes estimées de résorption. Il sert, avec la fraîcheur des données, à décider l'autoscaling. Voir [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).

## Portable Runner (Dataflow)

Architecture d'exécution de Dataflow où le code utilisateur tourne dans des conteneurs SDK séparés du *runner harness* ; requise pour Python et les pipelines multilangages. Une partie de la documentation la nomme Runner v2. Voir [Diagnostiquer un pipeline Dataflow](#diagnostiquer-dataflow).

## Préférence de quota (quota preference)

Ressource de Cloud Quotas qui déclare la valeur souhaitée d'un quota pour une combinaison de dimensions (région, famille de GPU...) ; elle sert à demander une hausse ou une baisse, par la console, l'API, `gcloud` ou l'IaC. Voir [Quotas et limites](#quotas-et-limites).

## Ajusteur de quota (quota adjuster)

Option de Cloud Quotas qui relève d'elle-même de 10 à 20 % un quota compatible dont la consommation de pointe approche la valeur ; elle ne baisse jamais un quota. Voir [Quotas et limites](#quotas-et-limites).

## Quota de débit (rate quota)

Quota qui borne une cadence sur une période (requêtes par minute, octets par jour) ; il se libère à la fin de la fenêtre, glissante d'une minute ou à minuit heure du Pacifique. À distinguer du quota d'allocation, qui borne un stock. Voir [Quotas et limites](#quotas-et-limites).

## Gigue (jitter)

Part aléatoire ajoutée au délai d'attente entre deux relances, pour que des clients refusés au même instant ne relancent pas tous ensemble. Elle accompagne le délai exponentiel. Voir [Quotas et limites](#quotas-et-limites).

## Configuration nommée (gcloud)

Jeu de propriétés `gcloud` (compte, projet, région, zone...) enregistré sous un nom et activé d'un coup, pour passer d'un contexte de travail à un autre. Voir [gcloud : filtres, formats et scripts](#gcloud-filtres-formats).

## Projection (gcloud)

Liste de clés d'une ressource, avec leurs transformations et attributs, qui choisit les valeurs affichées par `--format`, par exemple `table(name, zone.basename())`. Voir [gcloud : filtres, formats et scripts](#gcloud-filtres-formats).

## Portée d'accès d'une VM (access scope)

Limite OAuth posée sur les jetons que le compte de service attaché à une VM obtient du serveur de métadonnées ; elle s'ajoute aux rôles IAM du compte. Le niveau `cloud-platform` laisse les rôles IAM seuls décider. Voir [gcloud : calcul et réseau](#gcloud-calcul-reseau).

## Politique de pare-feu réseau (network firewall policy)

Ensemble de règles de pare-feu, global ou régional, associé à un ou plusieurs réseaux VPC et géré comme une seule ressource, plutôt qu'une série de règles VPC indépendantes. Voir [gcloud : calcul et réseau](#gcloud-calcul-reseau).

## Mise à jour progressive (rolling update)

Remplacement par lots des VM d'un groupe géré par des VM créées depuis un nouveau modèle d'instance, dans les limites fixées par `max-surge` et `max-unavailable`. Voir [gcloud : calcul et réseau](#gcloud-calcul-reseau).

## Job (BigQuery)

Unité de travail exécutée par BigQuery : requête, chargement, export ou copie. Chaque job a un ID, une région, un état (`PENDING`, `RUNNING`, `DONE`) et des statistiques (octets facturés, temps de slot), consultables par `bq show -j` ou `INFORMATION_SCHEMA.JOBS`. Voir [bq : requêtes et jobs](#bq-requetes-jobs).

## Simulation de requête (dry run)

Validation d'une requête sans l'exécuter : BigQuery renvoie le volume qu'elle lirait, sans consommer de slot ni rien facturer. Sert à estimer le coût d'une requête à la demande. Voir [bq : requêtes et jobs](#bq-requetes-jobs).

## Requête paramétrée (parameterized query)

Requête dont les valeurs sont passées à part (`@nom` ou `?`) plutôt que concaténées dans le texte SQL, ce qui écarte l'injection SQL. Voir [bq : requêtes et jobs](#bq-requetes-jobs).

## Clone de table (table clone)

Copie inscriptible d'une table BigQuery, qui partage le stockage de sa table de base et ne facture que les données modifiées ou ajoutées depuis sa création. Voir [bq : datasets, tables et chargement](#bq-tables-chargement).

## Partitionnement Hive (hive partitioning)

Rangement de fichiers dans des dossiers nommés `clé=valeur` (`jour=2026-01-31/pays=FR/`). BigQuery en déduit des colonnes de partition, au chargement comme pour une table externe. Voir [bq : datasets, tables et chargement](#bq-tables-chargement).

## Accès uniforme au niveau du bucket (uniform bucket-level access)

Réglage d'un bucket Cloud Storage qui désactive les ACL par objet : l'accès ne dépend plus que d'IAM, au niveau du bucket ou au-dessus. Voir [gcloud storage : buckets et objets](#gcloud-storage).

## Prévention de l'accès public (public access prevention)

Réglage d'un bucket, ou règle d'administration, qui refuse tout accès accordé à `allUsers` ou `allAuthenticatedUsers`, même si une stratégie IAM le prévoit. Voir [gcloud storage : buckets et objets](#gcloud-storage).

## Génération (Cloud Storage)

Numéro qui identifie une version d'un objet Cloud Storage, changé à chaque réécriture. Il désigne une version précise (`gs://BUCKET/OBJET#GENERATION`) et sert de précondition d'écriture (`--if-generation-match`). Voir [gcloud storage : buckets et objets](#gcloud-storage).

## Retenue d'objet (object hold)

Blocage posé sur un objet Cloud Storage qui empêche sa suppression tant qu'il n'est pas levé. La retenue temporaire est indépendante de la politique de conservation ; la retenue sur événement fait repartir la durée de conservation à sa levée. Voir [gcloud storage : buckets et objets](#gcloud-storage).

## CTE (Common Table Expression)

Sous-requête nommée dans une clause `WITH`, réutilisable dans la suite de la requête ; la forme `WITH RECURSIVE` parcourt une hiérarchie. Voir [GoogleSQL : requêtes](#googlesql-requetes).

## Fonction de fenêtre (window function)

Fonction SQL qui calcule une valeur par ligne à partir d'un ensemble de lignes voisines défini par `OVER (PARTITION BY … ORDER BY …)`, sans regrouper le résultat : rang, cumul, moyenne mobile, valeur précédente. Voir [GoogleSQL : fonctions de fenêtre](#googlesql-fenetres).

## Champ imbriqué et répété (nested and repeated field)

Colonne BigQuery de type `ARRAY<STRUCT<…>>` (`RECORD` en mode `REPEATED`) qui stocke les lignes filles dans la ligne parente, à la place d'une table séparée et d'une jointure. Voir [GoogleSQL : ARRAY, STRUCT et JSON](#googlesql-tableaux-struct-json).

## Syntaxe pipe (pipe syntax)

Écriture GoogleSQL où la requête commence par `FROM` et enchaîne des opérateurs `|>` (`WHERE`, `EXTEND`, `AGGREGATE`…), chacun appliqué au résultat du précédent. Voir [GoogleSQL : requêtes](#googlesql-requetes).

## Table générique (wildcard table)

Requête BigQuery sur toutes les tables d'un préfixe commun (`events_*`), filtrée par la pseudo-colonne `_TABLE_SUFFIX`. Voir [GoogleSQL : requêtes](#googlesql-requetes).

## Upsert

Écriture qui met à jour une ligne si sa clé existe déjà et l'insère sinon. Dans BigQuery, c'est un `MERGE` avec une clause `WHEN MATCHED` et une clause `WHEN NOT MATCHED`. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## DML modifiante (mutating DML)

Instruction `UPDATE`, `DELETE` ou `MERGE`, par opposition à `INSERT`. BigQuery en exécute au plus deux à la fois par table et met les suivantes en file ; elles réécrivent les partitions qu'elles touchent. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## Requête multi-instructions (multi-statement query)

Script GoogleSQL qui enchaîne plusieurs instructions dans un même job : variables (`DECLARE`, `SET`), conditions, boucles, SQL dynamique, gestion d'erreurs. Chaque instruction s'exécute comme un job enfant. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## Transaction multi-instructions (multi-statement transaction)

Suite d'instructions encadrée par `BEGIN TRANSACTION` et `COMMIT TRANSACTION`, appliquée en tout ou rien sur une ou plusieurs tables, avec isolation par instantané. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## Table temporaire (BigQuery)

Table créée par `CREATE TEMP TABLE` dans une requête multi-instructions ou une session, rangée dans un dataset caché et supprimée au plus tard 24 heures après la fin du script. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## Instantané de table (table snapshot)

Copie en lecture seule d'une table BigQuery à un instant donné de sa fenêtre de *time travel*, facturée sur les seules données qui diffèrent de la table de base ; on restaure en la clonant. Voir [BigQuery : DDL](#bigquery-ddl).

## UDF (User-Defined Function)

Fonction écrite par l'utilisateur et appelée dans une requête comme une fonction native : en SQL, en JavaScript ou en Python dans BigQuery, temporaire (le temps d'une requête) ou persistante dans un dataset. Voir [BigQuery : DDL](#bigquery-ddl).

## Fonction de table (TVF, table-valued function)

Fonction qui renvoie une table et s'utilise dans une clause `FROM`, à la manière d'une vue qui accepte des paramètres. Voir [BigQuery : DDL](#bigquery-ddl).

## Fonction distante (remote function)

UDF BigQuery dont le code s'exécute dans un service Cloud Run, appelé par lots de lignes à travers une connexion. Elle ouvre le SQL à du code arbitraire ou à des API externes. Voir [BigQuery : DDL](#bigquery-ddl).

## Prédicat constant faux (constant false predicate)

Condition `ON FALSE` dans un `MERGE` : aucune ligne ne correspond, ce qui permet de supprimer puis réinsérer atomiquement une partie de la table sans jointure. Voir [GoogleSQL : DML et transactions](#googlesql-dml).

## Génération autonome d'embeddings (autonomous embedding generation)

Colonne BigQuery définie par `GENERATED ALWAYS AS (AI.EMBED(...))`, que BigQuery tient à jour quand la colonne source change ; `AI.SEARCH` l'interroge directement. Voir [BigQuery ML : syntaxe](#sql-bigquery-ml).

## PCollection (Apache Beam)

Collection d'éléments qui circule entre les étapes d'un pipeline Beam, bornée (lot) ou non bornée (flux). Chaque élément porte un horodatage et une fenêtre. Voir [Apache Beam en Python](#beam-python).

## DoFn et ParDo (Apache Beam)

`ParDo` applique à chaque élément d'une `PCollection` une fonction écrite comme classe `DoFn`, dont la méthode `process` émet zéro, un ou plusieurs éléments. `setup` et `teardown` préparent et libèrent une ressource par instance, pas par élément. Voir [Apache Beam en Python](#beam-python).

## Entrée annexe (side input)

Donnée supplémentaire passée à une étape Beam, lue en entier par chaque worker : table de correspondance, taux, paramètres. Elle doit tenir en mémoire. Voir [Apache Beam en Python](#beam-python).

## Sortie secondaire (tagged output)

Seconde `PCollection` produite par une même étape Beam, en marquant certains éléments d'une étiquette ; sert en général à écarter les éléments en erreur vers une destination à part. Voir [Apache Beam en Python](#beam-python).

## Prism (runner Beam)

Runner local d'Apache Beam, écrit en Go, auquel le *DirectRunner* Python confie les pipelines qu'il prend en charge. Il sert aux tests sur le poste, pas à la production. Voir [Apache Beam en Python](#beam-python).

## Output (Pulumi)

Valeur d'une ressource Pulumi qui n'est connue qu'après sa création, comme une URL ou un ID. On la transforme par `apply`, `Output.all`, `concat` ou `format`, jamais comme une chaîne ordinaire. Voir [Pulumi GCP en Python](#pulumi-gcp-python).

## StackReference (Pulumi)

Lecture, depuis une stack Pulumi, des sorties publiées par une autre stack : c'est le lien entre les couches d'une fondation (organisation, réseau, projets). Voir [Construire les fondations en code](#fondations-en-code).

## Composant (Pulumi)

Classe Python dérivée de `pulumi.ComponentResource` qui regroupe plusieurs ressources sous un même parent, pour les réutiliser comme un seul bloc. Voir [Pulumi GCP en Python](#pulumi-gcp-python).

## Endpoint dédié (Agent Platform)

Endpoint d'inférence public doté de son propre nom DNS, isolé du trafic des autres clients. Il n'est pas compatible avec VPC Service Controls. Voir [Entraîner et servir un modèle](#entrainer-et-servir).

## Cloud Client Libraries

Bibliothèques clientes recommandées pour les API Google Cloud, un paquet `google-cloud-*` par service en Python, avec transport gRPC ou REST. Voir [Bibliothèques clientes Python](#bibliotheques-clientes).

## GAPIC

Générateur qui produit la plupart des Cloud Client Libraries à partir des définitions protobuf de l'API : même structure de client, pagers et opérations longues d'un service à l'autre. Voir [Bibliothèques clientes Python](#bibliotheques-clientes).

## Pager

Objet renvoyé par une méthode `list_*` d'une bibliothèque cliente : l'itérer parcourt tous les éléments et appelle les pages suivantes au fil de l'eau. Voir [Bibliothèques clientes Python](#bibliotheques-clientes).

## Document de découverte (discovery document)

Description JSON d'une API REST Google (`https://SERVICE.googleapis.com/$discovery/rest?version=v1`) : méthodes, chemins, paramètres, schémas et points de terminaison régionaux ; base du client `google-api-python-client`. Voir [Appeler une API REST sans bibliothèque](#api-rest-directe).

## Masque de champs (field mask)

Liste de champs qui limite une mise à jour (`update_mask`, `updateMask`) ou une réponse (`fields`, `X-Goog-FieldMask`) aux seuls champs nommés. Voir [Appeler une API REST sans bibliothèque](#api-rest-directe).

## Point de terminaison régional (regional endpoint)

Hôte d'API propre à une région (`SERVICE.REGION.rep.googleapis.com`) qui garantit que la requête est traitée dans cette région. Voir [Bibliothèques clientes Python](#bibliotheques-clientes).

## gRPC

Protocole d'appel de procédure à distance sur HTTP/2 avec des messages protobuf ; transport par défaut des bibliothèques clientes générées, plus efficace que REST et seul à porter les flux bidirectionnels. Voir [Bibliothèques clientes Python](#bibliotheques-clientes).

## Jeton d'accès (access token)

Jeton OAuth 2.0 court, valable une heure par défaut, qui autorise un principal à appeler les API Google (`*.googleapis.com`) dans la limite de ses scopes et de ses rôles IAM. Les bibliothèques clientes l'obtiennent par ADC et le renouvellent seules. Voir [Authentification côté code](#authentification-code).

## Jeton d'identité (ID token)

Jeton OIDC signé par Google, valable une heure, qui atteste l'identité de l'appelant auprès d'un destinataire précis, désigné par son audience. C'est lui qu'attendent Cloud Run, les fonctions Cloud Run et IAP, et que reçoivent les *push* Pub/Sub ou les tâches Cloud Tasks authentifiés. Voir [Authentification côté code](#authentification-code).

## Audience (jeton d'identité)

Champ `aud` d'un jeton d'identité : le destinataire pour lequel il a été émis, par exemple l'URL d'un service Cloud Run ou l'ID client OAuth d'IAP. Le destinataire refuse un jeton émis pour une autre audience. Voir [Authentification côté code](#authentification-code).

## ErrorInfo

Détail structuré joint aux erreurs des API Google : une raison (`RATE_LIMIT_EXCEEDED`, `SERVICE_DISABLED`, `IAM_PERMISSION_DENIED`...), un domaine et des métadonnées (service, projet consommateur, métrique de quota). Il permet de distinguer par code un quota, un débit et un droit manquant. Voir [Erreurs, quotas et relances](#erreurs-quotas-relances).

## Disjoncteur (circuit breaker)

Mécanisme qui cesse d'appeler un service en échec répété pendant un temps et renvoie un repli, au lieu d'ajouter de la charge par des relances. Voir [Erreurs, quotas et relances](#erreurs-quotas-relances).

## Contrôle de flux (flow control, Pub/Sub)

Réglage des bibliothèques clientes Pub/Sub qui borne le nombre de messages et d'octets en attente : côté abonné, les messages non acquittés gardés en mémoire ; côté éditeur, les messages pas encore envoyés. Voir [Pub/Sub, Firestore, Secret Manager et Cloud Tasks en Python](#pubsub-firestore-secrets-code).

## CRC32C

Somme de contrôle de 32 bits calculée par Cloud Storage et Secret Manager sur chaque objet ou version de secret ; le client la recalcule pour détecter une donnée corrompue en transit. Voir [Cloud Storage et BigQuery en Python](#storage-bigquery-code).

## Création de job facultative (optional job creation, BigQuery)

Mode de requête dans lequel BigQuery n'enregistre pas de job pour une requête courte, ce qui réduit sa latence ; la bibliothèque Python l'active avec `default_job_creation_mode="JOB_CREATION_OPTIONAL"`. Voir [Cloud Storage et BigQuery en Python](#storage-bigquery-code).

## Concurrence pessimiste ou optimiste (Firestore)

Mode de contrôle des transactions Firestore : en pessimiste, la transaction verrouille les documents qu'elle lit ; en optimiste, elle vérifie à la validation qu'ils n'ont pas changé et échoue sinon. Voir [Pub/Sub, Firestore, Secret Manager et Cloud Tasks en Python](#pubsub-firestore-secrets-code).

## Recognizer (Speech-to-Text)

Ressource de l'API Speech-to-Text v2 qui fixe une configuration de reconnaissance réutilisable : modèle, langues, options. L'identifiant `_` désigne le recognizer implicite, dont la configuration voyage dans chaque requête. Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## Chirp 3

Famille de modèles génératifs de Google pour la parole : `chirp_3` pour la transcription dans Speech-to-Text v2, et les voix *Chirp 3: HD* pour la synthèse dans Text-to-Speech. Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## Gemini-TTS

Modèles de synthèse vocale Gemini appelés par l'API Text-to-Speech, pilotés par une consigne en langage naturel (style, débit, émotion) et capables de faire dialoguer plusieurs voix. Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## Résultat intermédiaire (interim result)

Transcription provisoire renvoyée pendant une reconnaissance en flux, avant que le service ne fixe le segment (`is_final`). Sert à afficher le texte au fil de la parole. Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## Dynamic batch (Speech-to-Text)

Mode de transcription par lots traité avec une priorité moindre, facturé nettement moins cher à la minute en échange d'un délai plus long (`processing_strategy=DYNAMIC_BATCHING`). Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## PhraseSet

Liste d'expressions (noms propres, vocabulaire métier) passée à Speech-to-Text pour favoriser leur reconnaissance, avec un poids facultatif. Voir [Speech-to-Text et Text-to-Speech en Python](#speech-to-text-tts).

## SafeSearch

Fonction de Vision API qui évalue la vraisemblance de contenu sensible dans une image en cinq catégories (adulte, parodie, médical, violence, suggestif), sur une échelle de `VERY_UNLIKELY` à `VERY_LIKELY`. Voir [Vision et Video Intelligence en Python](#vision-video).

## Glossaire (Translation)

Ressource de Cloud Translation qui impose la traduction de termes précis (noms de produits, vocabulaire maison), créée à partir d'un fichier CSV, TSV ou TMX dans Cloud Storage. Elle vit dans `us-central1` et ne s'utilise que depuis cette région. Voir [Natural Language et Translation en Python](#natural-language-translation).

## Translation LLM

Modèle de traduction de Cloud Translation bâti sur Gemini et spécialisé pour la traduction (`general/translation-llm`), plus fluide que le modèle NMT sur un contexte de plusieurs phrases ; il sert aussi de base à la traduction adaptative. Voir [Natural Language et Translation en Python](#natural-language-translation).

## Traduction adaptative (adaptive translation)

Traduction par le Translation LLM guidée par quelques paires d'exemples source/cible, passées dans la requête (cinq au plus) ou tirées d'un jeu de données, sans entraînement. Voir [Natural Language et Translation en Python](#natural-language-translation).

## Type d'encodage (encoding type)

Paramètre de Natural Language qui fixe l'unité des positions renvoyées (`begin_offset`) : UTF-8, UTF-16 ou UTF-32. Sans lui, les positions valent −1 ; en Python, UTF-32 donne des positions en points de code. Voir [Natural Language et Translation en Python](#natural-language-translation).

## Ancre de texte (text anchor)

Dans l'objet `Document` de Document AI, référence d'un élément (champ, cellule, entité) vers ses segments dans le texte intégral du document, par positions de début et de fin. Voir [Document AI en Python](#document-ai-code).

## Shard (Document AI)

Fichier JSON partiel d'un résultat de traitement par lots : un gros document est écrit en plusieurs shards, chacun avec son propre texte et sa position dans l'ensemble (`shard_info`). Document AI Toolbox les regroupe. Voir [Document AI en Python](#document-ai-code).

## Version de processeur (processor version)

Modèle précis servi par un processeur Document AI (par exemple `pretrained-ocr-v2.1-2024-08-07`). Le processeur a une version par défaut ; la viser explicitement fige les résultats en production. Voir [Document AI en Python](#document-ai-code).

## Document AI Toolbox

Bibliothèque Python (`google-cloud-documentai-toolbox`) qui charge les résultats de Document AI, regroupe les shards d'un lot, convertit les tableaux en DataFrame pandas et charge entités et champs dans BigQuery. Voir [Document AI en Python](#document-ai-code).

## Dimension à évolution lente (slowly changing dimension, SCD)

Table de dimension dont les attributs changent rarement mais changent. Le type 1 écrase l'ancienne valeur ; le type 2 ferme la ligne courante et insère une nouvelle version avec ses dates de validité, pour lire chaque fait avec la valeur en vigueur à sa date. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## BI Engine

Cache en mémoire de BigQuery, avec un moteur vectorisé, qui accélère les requêtes courtes des tableaux de bord sans les modifier. Il se réserve en Gio de mémoire par projet et par région, et peut se limiter à une liste de tables préférées. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## Schéma en étoile (star schema)

Modèle d'entrepôt où une table de faits centrale (mesures et clés) est jointe à des tables de dimensions (client, produit, date). Le schéma en flocon normalise en plus les dimensions. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## Dénormalisation

Regroupement dans une même table de données qu'un modèle normalisé répartit entre plusieurs, pour supprimer des jointures à la lecture. Dans BigQuery, elle passe de préférence par des champs imbriqués et répétés plutôt que par un aplatissement complet. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## Jointure par diffusion (broadcast join)

Plan de jointure où la plus petite table, tenue en mémoire, est envoyée à chaque slot qui lit la grande ; il évite de redistribuer les deux côtés comme le fait une jointure par hachage. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## Table préférée (BI Engine preferred table)

Table inscrite dans la réservation BI Engine d'un projet : seules ces tables sont accélérées, les autres requêtes utilisent les slots habituels. Voir [Modéliser l'entrepôt BigQuery](#modeliser-entrepot).

## Graphe d'exécution (BigQuery)

Plan d'une requête BigQuery vu comme un graphe d'étapes reliées par le brassage, avec pour chaque étape ses opérations, ses lignes lues et écrites et ses temps d'attente, de lecture, de calcul et d'écriture. Voir [Diagnostiquer une requête BigQuery](#diagnostiquer-bigquery).

## Insight de performance (BigQuery)

Diagnostic que BigQuery attache à une étape du graphe d'exécution : contention de slots, quota de brassage insuffisant, jointure à forte cardinalité, déséquilibre de partition, hausse du volume lu. Voir [Diagnostiquer une requête BigQuery](#diagnostiquer-bigquery).

## Contention de slots

Situation où une requête a des tâches prêtes à s'exécuter mais pas de slots libres pour les prendre, parce que la réservation ou le projet à la demande est saturé. Voir [Diagnostiquer une requête BigQuery](#diagnostiquer-bigquery).

## Déséquilibre de partition (partition skew)

Répartition inégale des données entre les partitions d'une étape de jointure ou d'agrégation, due à une valeur de clé très fréquente : un seul slot traite la partition surdimensionnée, et ajouter des slots n'y change rien. Voir [Diagnostiquer une requête BigQuery](#diagnostiquer-bigquery).

## Jointure à forte cardinalité

Jointure sur des clés non uniques des deux côtés, qui produit beaucoup plus de lignes qu'elle n'en reçoit. Voir [Diagnostiquer une requête BigQuery](#diagnostiquer-bigquery).

## Réservation à autoscaling

Réservation BigQuery définie par un maximum de slots, avec une base éventuellement nulle : BigQuery ajoute des slots par multiples de 50 selon la demande et les facture tant qu'ils sont alloués, sans engagement. Voir [Optimiser les coûts](#optimiser-les-couts).

## Engagement de capacité (BigQuery)

Achat de slots pour un ou trois ans, en édition Enterprise ou Enterprise Plus, avec une remise de 20 % ou 40 % ; régional, payé chaque heure qu'il serve ou non, il couvre le socle permanent d'une charge. Voir [Optimiser les coûts](#optimiser-les-couts).

## Facturation fluide (fluid scaling)

Option d'une réservation BigQuery qui facture les slots d'autoscaling à la seconde, sans la minute minimale par défaut. Voir [Optimiser les coûts](#optimiser-les-couts).

## Partage BigQuery (BigQuery sharing)

Publication de datasets BigQuery et de sujets Pub/Sub vers d'autres projets ou organisations, sans copie : l'éditeur range des fiches dans un échange privé ou public, l'abonné obtient un dataset lié en lecture seule. L'API et les rôles gardent le nom `analyticshub`. Voir [Partager des données](#partager-des-donnees).

## Analytics Hub

Ancien nom du partage BigQuery. L'API `analyticshub.googleapis.com`, les rôles `roles/analyticshub.*` et la page Sharing (Analytics Hub) de la console gardent l'ancien nom. Voir [Partager des données](#partager-des-donnees).

## Dataset lié (linked dataset)

Dataset en lecture seule créé dans le projet d'un abonné au partage BigQuery ; il pointe vers le dataset de l'éditeur, sans copie, et l'abonné ne paie que ses requêtes. Voir [Partager des données](#partager-des-donnees).

## Salle blanche (data clean room)

Échange de partage BigQuery réservé aux données sensibles : plusieurs parties y croisent leurs données sous des règles d'analyse, sans voir les lignes des autres ni pouvoir les exporter. Voir [Partager des données](#partager-des-donnees).

## Règle d'analyse (analysis rule)

Politique posée sur une vue BigQuery qui restreint les requêtes permises : seuil d'agrégation, confidentialité différentielle ou recouvrement de listes, avec une restriction de jointure en option. Voir [Partager des données](#partager-des-donnees).

## Connected Sheets

Connexion de Google Sheets à BigQuery : tableaux croisés, formules et graphiques portent sur toute une table, chaque calcul étant une requête BigQuery facturée au projet choisi. Voir [Data Studio](#data-studio).

## Data Catalog

Service de catalogue de métadonnées de Google Cloud, fermé : Knowledge Catalog tient son rôle, ses tags et modèles de tags y correspondant aux aspects et types d'aspects. Seul Policy Tag Manager (taxonomies et *policy tags* de BigQuery) reste servi par l'API `datacatalog.googleapis.com`, qui doit rester activée, d'où le préfixe `datacatalog` des rôles de lecture fine. Voir [Knowledge Catalog](#knowledge-catalog).

## Aspect (Knowledge Catalog)

Bloc de métadonnées typé, attaché à une entrée du catalogue ; son type d'aspect en fixe la structure, et on peut définir les siens. Un aspect décrit la donnée sans en restreindre l'accès : la sécurité au niveau colonne reste l'affaire des *policy tags* de BigQuery, un mécanisme distinct. Voir [Knowledge Catalog](#knowledge-catalog).

## ACL (Cloud Storage)

Liste de contrôle d'accès posée sur un bucket ou un objet, système hérité conçu pour l'interopérabilité avec Amazon S3. Elle agit en parallèle d'IAM : il suffit que l'un des deux accorde l'accès. Voir [Cloud Storage](#cloud-storage).

## Dossier géré (managed folder)

Dossier Cloud Storage sur lequel on pose une stratégie IAM, appliquée à tous les objets dont le nom commence par son chemin. Exige l'accès uniforme au niveau du bucket. Voir [Cloud Storage](#cloud-storage).

## Rapport d'inventaire (inventory report)

Liste planifiée des objets d'un bucket Cloud Storage et de leurs métadonnées, écrite en CSV ou en Parquet dans un bucket de destination. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Storage Intelligence

Abonnement Cloud Storage qui donne une vue d'ensemble d'un parc de buckets : recommandations, jeux de données Storage Insights interrogés dans BigQuery, rapports d'inventaire, opérations par lots. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Jeu de données Storage Insights (Storage Insights dataset)

Index des métadonnées et de l'activité des buckets et objets d'un bucket, d'un projet, d'un dossier ou d'une organisation, lu en SQL dans un dataset BigQuery lié. Voir [Cloud Storage : classes et cycle de vie](#cloud-storage-classes).

## Projet de calcul (BigQuery)

Projet dans lequel s'exécutent les jobs BigQuery d'une équipe, distinct du projet qui stocke les données : il porte la facture des requêtes à la demande et les quotas de calcul. Voir [BigQuery : organiser les tables](#organiser-bigquery).

## Lac (Knowledge Catalog)

Regroupement logique des données d'un domaine, réparties sur plusieurs projets, organisé en zones brutes et organisées auxquelles on rattache buckets et datasets. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Zone brute, zone organisée (raw zone, curated zone)

Zones d'un lac Knowledge Catalog : la zone brute accepte tout format pour des données encore à traiter, la zone organisée des fichiers Parquet, Avro ou ORC en arborescence Hive, prêts pour l'analyse. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Analyse de découverte (discovery scan)

Analyse Knowledge Catalog qui parcourt un bucket, regroupe les fichiers par dossier et publie des tables BigLake, externes ou d'objets dans BigQuery. Voir [Lakehouse : tables ouvertes et gouvernance](#lakehouse-architecture).

## Placement régional (Dataflow)

Répartition des workers d'un job Dataflow sur toutes les zones de sa région, qui permet de les recréer ailleurs si une zone tombe. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Environnement hautement résilient (Airflow)

Environnement Managed Service for Apache Airflow réparti sur au moins deux zones, avec sa base Cloud SQL en haute disponibilité. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Mode haute disponibilité (Spark)

Cluster Managed Service for Apache Spark à trois maîtres, choisi à la création, dont HDFS et YARN traversent la panne d'un nœud ; tous les nœuds restent dans une zone. Voir [Régions, zones et reprise d'activité](#regions-zones-resilience).

## Croisement de caractéristiques (feature cross)

Caractéristique synthétique qui combine deux caractéristiques catégorielles ou découpées en intervalles, pour qu'un modèle linéaire apprenne leur interaction ; `ML.FEATURE_CROSS` en BigQuery ML. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Découpage en intervalles (bucketing)

Remplacement d'une valeur continue par la plage à laquelle elle appartient, quand sa relation avec l'étiquette n'est pas linéaire ; `ML.BUCKETIZE` et `ML.QUANTILE_BUCKETIZE` en BigQuery ML. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Surapprentissage (overfitting)

Modèle qui colle si bien aux données d'entraînement qu'il prédit mal sur des données nouvelles : la perte de validation remonte pendant que celle d'entraînement baisse. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Sous-apprentissage (underfitting)

Modèle qui prédit mal même sur ses données d'entraînement, faute de caractéristiques utiles, d'itérations ou de capacité, ou sous une régularisation trop forte. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Régularisation (L1, L2)

Pénalité sur la taille des poids ajoutée à la perte pour limiter le surapprentissage. L2 rapproche les poids de zéro ; L1 annule ceux des caractéristiques peu utiles. Options `L1_REG` et `L2_REG` en BigQuery ML. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Arrêt anticipé (early stopping)

Arrêt de l'entraînement quand la perte de validation cesse de s'améliorer, avant que le modèle ne surapprenne ; option `EARLY_STOP`, active par défaut, en BigQuery ML. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Epoch

Passage complet sur le jeu d'entraînement, chaque exemple étant traité une fois ; `MAX_ITERATIONS` en compte le nombre maximal en BigQuery ML. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Taux d'apprentissage (learning rate)

Hyperparamètre qui règle l'ampleur de chaque correction des poids : trop bas, l'entraînement traîne ; trop haut, il ne converge pas. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Fuite d'étiquette (label leakage)

Caractéristique qui n'est connue qu'après le résultat à prédire, ou qui en est un substitut : les métriques de validation sont excellentes, le modèle échoue en production. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Biais d'échantillonnage (sampling bias)

Données d'entraînement qui ne sont pas tirées au hasard dans la population sur laquelle le modèle prédira ; le jeu de validation, découpé dans les mêmes données, ne le révèle pas. Voir [Choisir une approche ML](#choisir-une-approche-ml).

## Instantané Dataflow (Dataflow snapshot)

Sauvegarde de l'état d'un job Dataflow en continu, avec en option un instantané Pub/Sub de sa source, à partir de laquelle un nouveau job reprend sans perdre ses fenêtres ni ses agrégats. Voir [Dataflow](#dataflow).

## Drainage (drain)

Arrêt d'un job Dataflow en continu qui cesse de lire la source mais termine les éléments en mémoire ; les fenêtres ouvertes se ferment aussitôt avec des résultats partiels. Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Seek (Pub/Sub)

Opération qui modifie en bloc l'état d'acquittement d'un abonnement Pub/Sub, vers une date ou un instantané, pour rejouer des messages déjà acquittés ou purger un arriéré. Voir [Streaming : Pub/Sub, Dataflow, BigQuery](#streaming).

## Autoscaling vertical (Dataflow)

Fonction de Dataflow Prime qui remplace les workers à court ou en excès de mémoire par des workers dont seule la mémoire change. Voir [Dataflow](#dataflow).

## Décommissionnement progressif (graceful decommissioning)

Retrait d'un nœud d'un cluster Spark après la fin des applications YARN en cours, dans la limite d'un délai au-delà duquel le nœud est arrêté de force. Voir [Managed Service for Apache Spark](#managed-service-for-apache-spark).

## Réglage par renforcement (reinforcement learning fine-tuning)

Réglage d'un modèle où celui-ci génère plusieurs réponses par prompt, chacune notée par une fonction de récompense, et apprend à rendre probables les réponses les mieux notées. Adapté aux tâches dont le résultat se vérifie par programme. Voir [Régler un modèle Gemini](#regler-gemini).

## Fonction de récompense (reward function)

Fonction qui attribue une note numérique à une réponse du modèle pendant un réglage par renforcement : comparaison avec une valeur attendue, avis d'un modèle juge, code exécuté ou service externe. Voir [Régler un modèle Gemini](#regler-gemini).

## Adaptateur (adapter, LoRA)

Petit ensemble de paramètres entraînés à côté des poids figés d'un grand modèle, qui en modifie le comportement à moindre coût ; LoRA en est la forme la plus courante, QLoRA la variante sur un modèle quantifié. Voir [Régler un modèle Gemini](#regler-gemini).

## Réglage continu (continuous tuning)

Nouveau réglage qui part d'un modèle déjà réglé ou de l'un de ses points de contrôle, pour ajouter des exemples ou des epochs sans repartir du modèle de base. Voir [Régler un modèle Gemini](#regler-gemini).

## Distillation

Réglage d'un petit modèle, dit élève, sur les réponses produites par un grand modèle, dit enseignant, pour lui transmettre une capacité à moindre coût d'inférence. Voir [Régler un modèle Gemini](#regler-gemini).

## Nœud-heure (node hour)

Unité de facturation d'AutoML et des endpoints d'Agent Platform : une heure de calcul d'un nœud, décomptée par fractions. Le budget d'entraînement d'AutoML s'exprime en nœuds-heures (en milli-nœuds-heures dans l'API) et plafonne le coût, pas la durée. Voir [AutoML : entraîner sans code](#automl).

## Modèle Edge (AutoML)

Modèle d'image AutoML entraîné pour s'exécuter hors de Google Cloud : exporté en TF Lite, Core ML, TensorFlow.js ou conteneur, il ne se sert pas sur Agent Platform. Voir [AutoML : entraîner sans code](#automl).

## Tabular Workflows

Pipelines gérés d'Agent Platform qui exécutent AutoML tabulaire étape par étape (découpage, ingénierie des variables, recherche d'architecture, ensemble, distillation), chaque étape étant réglable. Voir [AutoML : entraîner sans code](#automl).

## Matrice de confusion (confusion matrix)

Tableau qui croise les classes réelles et les classes prédites d'un modèle de classification : la diagonale compte les bonnes réponses, le reste montre quelles classes le modèle confond. Voir [AutoML : entraîner sans code](#automl).

## IoU (Intersection over Union)

Rapport entre l'aire commune d'une boîte prédite et d'une boîte réelle et l'aire de leur union ; un seuil d'IoU décide si une détection d'objet compte comme juste. Voir [AutoML : entraîner sans code](#automl).

## Importance des variables (feature importance)

Part de chaque colonne dans les prédictions d'un modèle, en pourcentage sur le modèle entier ; une variable qui domine sans raison métier signale souvent une fuite d'étiquette. Voir [AutoML : entraîner sans code](#automl).

## Horizon de prévision (forecast horizon)

Nombre de pas de temps futurs qu'un modèle de prévision prédit pour chaque série, exprimé dans la granularité des données. Voir [AutoML : entraîner sans code](#automl).
