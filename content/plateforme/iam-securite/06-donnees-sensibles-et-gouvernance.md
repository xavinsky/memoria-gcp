---
title: Données sensibles et gouvernance
subgroup: Protection des données
---

Protéger une donnée sensible se fait en trois temps : **savoir où elle se trouve**, **décider qui la lit en clair**, **pouvoir le prouver**. Le pilier sécurité du Well-Architected Framework suit le même ordre dans son principe [conformité et confidentialité](https://docs.cloud.google.com/architecture/framework/security/meet-regulatory-compliance-and-privacy-needs) : maîtriser la résidence, classer les données confidentielles, puis verrouiller leur accès. Pour la deuxième étape, deux familles de contrôles s'opposent. **Transformer** la donnée : elle n'existe plus en clair chez le consommateur. **Filtrer la lecture** : elle reste en clair dans la table, et BigQuery décide à chaque requête ce que voit l'appelant.

![Arbre de décision : du besoin de lecture au contrôle](../../svg/choix-controle-donnees.svg)

## Matrice risque → contrôle

| Risque | Contrôle | Où il s'applique |
|---|---|---|
| Ignorer où sont les données personnelles | Découverte [Sensitive Data Protection](#sensitive-data-protection), profils publiés dans [Security Command Center](#security-command-center) et [Knowledge Catalog](#knowledge-catalog) | Organisation, dossier ou projet |
| Un analyste lit un identifiant dont il n'a pas besoin | *Policy tag* (accès refusé) ou masquage dynamique | Colonne BigQuery |
| Une équipe voit les lignes d'une autre entité | Politique d'accès aux lignes | Table BigQuery |
| Partager un résultat sans donner la table | Vue, dataset ou routine autorisés | Dataset BigQuery |
| Données de production copiées en recette, envoyées à un tiers ou à un modèle | Dé-identification : tokenisation, généralisation | Pipeline d'ingestion, copie de fichiers |
| Copie vers un projet extérieur par un compte légitime | Périmètre [VPC Service Controls](#perimetres-vpc-sc) | Projets du périmètre |
| Lecture directe des fichiers d'un *lakehouse* | Accès au bucket réservé au compte de la connexion BigQuery (voir [Lakehouse](#lakehouse-architecture)) | Bucket Cloud Storage |
| Données créées hors de la zone autorisée | Contrainte `gcp.resourceLocations`, [Assured Workloads](#assured-workloads) | Organisation, dossier |
| Garder trop longtemps, ou effacer trop tôt | Expiration de tables et de partitions, rétention verrouillée | Dataset, bucket, bucket de journaux |
| Accès par le personnel du fournisseur | Access Transparency, Access Approval (voir [Détection et conformité](#detection-et-conformite)) | Organisation |

## Découvrir et classer

[Sensitive Data Protection](#sensitive-data-protection) reconnaît les données par [infoTypes](#lexterm-infotype) prédéfinis (IBAN, numéro de sécurité sociale français, adresse e-mail) et par détecteurs personnalisés (dictionnaire, expression régulière). Son API garde le nom **Cloud Data Loss Prevention** (`dlp.googleapis.com`).

- **Découverte.** Une configuration de scan, posée sur l'organisation, un dossier ou un projet, **profile** en continu les tables [BigQuery](#bigquery) et BigLake, les instances [Cloud SQL](#cloud-sql), les buckets [Cloud Storage](#cloud-storage), les données d'entraînement Vertex AI, Amazon S3 et Azure Blob Storage. Chaque profil donne les infoTypes trouvés, un **niveau de sensibilité** et un **risque de données**, sans copier les données.
- **Actions de fin.** Publication dans Security Command Center, dans Google Security Operations, dans Knowledge Catalog (sous forme d'aspects) et vers Pub/Sub ; historique des profils dans BigQuery ; **pose d'un tag de sensibilité** sur la ressource, qu'une [condition IAM](#lexterm-condition-iam) exploite pour accorder ou refuser l'accès selon le niveau calculé.
- **Inspection.** Un job ciblé qui rend la position exacte de chaque occurrence, à réserver aux ressources que la découverte a signalées.

[Knowledge Catalog](#knowledge-catalog) (API, CLI et rôles préfixés `dataplex`) porte ensuite le sens de ces données : glossaire, aspects, [lignage](#lexterm-lignage-data-lineage) jusqu'à la colonne, scans de qualité et produits de données. Le lignage répond à la question que pose tout incident de confidentialité : dans quelles tables en aval une colonne sensible a-t-elle été recopiée ? L'organisation en domaines et produits de données est décrite dans [Lakehouse](#lakehouse-architecture). Knowledge Catalog décrit, il n'autorise rien : les droits restent portés par IAM et BigQuery.

## Transformer la donnée

La dé-identification s'impose quand le consommateur n'a pas besoin de la valeur : environnement de recette, partenaire, jeu d'entraînement, invite envoyée à un modèle.

| Transformation (objet de l'API) | Réversible | Jointures possibles | Usage |
|---|---|---|---|
| Chiffrement déterministe (`CryptoDeterministicConfig`, AES-SIV) | Oui, avec la clé | Oui | **Tokenisation par défaut** : identifiant client, numéro de contrat |
| [!DECONSEILLE] Chiffrement préservant le format (`CryptoReplaceFfxFpeConfig`, FPE-FFX) | Oui | Oui | Seulement si un système aval valide la longueur et l'alphabet ; lent, entrées courtes et de longueur uniforme ; sinon chiffrement déterministe |
| Hachage cryptographique (`CryptoHashConfig`) | Non | Oui | Pseudonyme stable, sans retour possible |
| Masquage par caractère, remplacement, suppression | Non | Non | Affichage, journaux, texte libre |
| Regroupement en intervalles (*bucketing*) | Non | Non | Âge, revenu, code postal : garder une valeur analysable |
| Décalage de dates | Non | Non | Dates décalées d'un écart aléatoire, identique pour une même entité : les durées restent justes |

La documentation déconseille FPE sauf contrainte de format : le chiffrement déterministe n'a pas de limite d'entrée et va beaucoup plus vite. Les clés de chiffrement sont des clés enveloppées par [Cloud KMS](#cloud-kms) (voir [Chiffrement](#chiffrement)) : qui peut utiliser la clé KMS peut ré-identifier.

Où placer la transformation :

- **À l'ingestion**, dans un pipeline [Dataflow](#dataflow) qui appelle `content.deidentify` avec un modèle de dé-identification. Le modèle Google *Data Masking/Tokenization from Cloud Storage to BigQuery* [!PREVERSION] couvre le cas de fichiers CSV chargés dans BigQuery.
- **Sur des fichiers**, par un job qui écrit des copies dé-identifiées de Cloud Storage dans un autre bucket, arborescence conservée.
- **Dans BigQuery**, par les fonctions `DLP_DETERMINISTIC_ENCRYPT` et `DLP_DETERMINISTIC_DECRYPT`, compatibles avec le chiffrement déterministe de Sensitive Data Protection : une colonne tokenisée à l'ingestion se ré-identifie en SQL, pour ceux qui ont accès à la clé.
- **Dans une application**, par un appel synchrone à `content.deidentify` avant d'écrire un journal ou d'envoyer un texte à un modèle.

## Filtrer la lecture dans BigQuery

Les mécanismes (*policy tags*, masquage, lignes, vues autorisées) et les types de tables qui les acceptent sont détaillés dans [Lakehouse](#lakehouse-architecture). Ce qui compte à la conception :

- **Colonne refusée ou masquée.** Un *policy tag* réserve la colonne aux titulaires de *Fine-Grained Reader* (`roles/datacatalog.categoryFineGrainedReader`) ; une politique de masquage lui ajoute un public qui lit une valeur masquée, avec *Masked Reader* (`roles/bigquerydatapolicy.maskedReader`), à accorder sur la politique plutôt que sur le projet. Les requêtes existantes n'ont pas à changer, alors qu'une colonne refusée fait échouer tout `SELECT *`.
- **Règle de masquage.** `SHA256` est déterministe et sans clé, donc attaquable par force brute sur un petit domaine de valeurs ; `RANDOM_HASH` sale chaque requête et ne permet de joindre qu'à l'intérieur d'une même requête ; il n'existe que pour les politiques posées directement sur une colonne. Les autres règles : `ALWAYS_NULL`, `DEFAULT_MASKING_VALUE`, `EMAIL_MASK`, `FIRST_FOUR_CHARACTERS`, `LAST_FOUR_CHARACTERS`, `DATE_YEAR_MASK`, ou une routine personnalisée.
- **Taxonomie ou politique sur la colonne.** Les *policy tags* passent par une taxonomie régionale, dans la même région que les tables. Une politique de données peut aussi se poser directement sur une colonne, sans taxonomie, jusqu'à huit par colonne ; une colonne porte l'un ou l'autre, jamais les deux.
- **Lignes.** Une politique d'accès aux lignes filtre par groupe ; un utilisateur absent de toutes les politiques ne voit **aucune** ligne. Une sous-requête sur une table d'habilitations remplace des dizaines de politiques, mais une politique à sous-requête est incompatible avec l'API Storage Read et fait facturer la lecture de la table de référence.
- **Vue, dataset, routine autorisés.** Pour partager un sous-ensemble ou un agrégat avec une autre équipe, sans droit sur la table source. Le dataset autorisé évite de déclarer chaque vue ; une procédure stockée autorisée hérite du DML et du DDL de ses tables, à accorder avec prudence.

```sql
-- Lignes : chaque commercial voit ses régions, lues dans une table d'habilitations
CREATE ROW ACCESS POLICY regions_commerciaux
ON DATASET.ventes
GRANT TO ('group:commerciaux@example.com')
FILTER USING (region IN (
  SELECT region FROM DATASET.habilitations WHERE email = SESSION_USER()));

-- L'équipe data garde tout : sans cette politique, elle ne verrait plus rien
CREATE ROW ACCESS POLICY tout_voir
ON DATASET.ventes
GRANT TO ('group:equipe-data@example.com')
FILTER USING (TRUE);

-- Colonne : masque d'e-mail posé sans taxonomie (instructions en préversion)
CREATE DATA_POLICY `PROJECT_ID.region-REGION.email_masque`
OPTIONS (data_policy_type = 'DATA_MASKING_POLICY', masking_expression = 'EMAIL_MASK');

GRANT FINE_GRAINED_READ ON DATA_POLICY `PROJECT_ID.region-REGION.email_masque`
TO "principalSet://goog/group/analystes@example.com";

ALTER TABLE DATASET.clients
ALTER COLUMN email SET OPTIONS (
  data_policies = ["{'name':'PROJECT_ID.region-REGION.email_masque'}"]);
```

## Résidence et rétention

- **Résidence.** La contrainte `gcp.resourceLocations`, posée sur l'organisation ou un dossier (voir [Hiérarchie des ressources](#hierarchie-des-ressources)), refuse la création de ressources hors des emplacements permis ; les groupes de valeurs `in:eu-locations` (Union européenne) et `in:europe-locations` (Europe au sens large) évitent de lister les régions. Elle ne vaut que pour les nouvelles ressources, ne couvre pas les ressources globales et ne constitue pas un engagement contractuel de stockage. Quand la réglementation exige cet engagement, avec le contrôle de l'accès du personnel Google, c'est un dossier [Assured Workloads](#assured-workloads) qu'il faut.
- **Rétention minimale.** Politique de conservation Cloud Storage verrouillée (*Bucket Lock*) ou *Object Retention Lock*, bucket de journaux verrouillé : irréversibles, ils empêchent toute suppression avant l'échéance, y compris par un administrateur.
- **Rétention maximale.** Expiration par défaut d'un dataset, expiration de partition, règles de cycle de vie Cloud Storage (voir [Classes de stockage](#cloud-storage-classes)). Une donnée supprimée de BigQuery reste récupérable pendant la fenêtre de *time travel* (2 à 7 jours, 7 par défaut) puis sept jours de *fail-safe* ; un objet Cloud Storage supprimé reste 7 jours en suppression réversible par défaut, jusqu'à 90 jours selon le réglage.

## Pièges

- **Taxonomie non appliquée.** Des *policy tags* posés sur une taxonomie dont le contrôle d'accès n'est pas activé (*enforce*) ne protègent rien.
- **Édition Standard.** L'édition Standard de BigQuery n'inclut aucun contrôle fin : ni *policy tags*, ni politiques de lignes, ni masquage. Un projet qui interroge des tables protégées doit exécuter ses requêtes en édition Enterprise, Enterprise Plus ou à la demande.
- **Politiques de lignes effacées.** `CREATE OR REPLACE TABLE`, un chargement ou une requête en `WRITE_TRUNCATE` et une copie qui écrase la table suppriment les politiques d'accès aux lignes sans avertissement. Un pipeline qui reconstruit sa table chaque nuit doit les recréer, idéalement dans le même code.
- **Masquage vu comme de l'anonymisation.** Une valeur masquée à la lecture reste en clair dans la table, dans ses exports et pour tout détenteur de *Fine-Grained Reader*. Pour sortir des données de l'entrepôt, dé-identifier.
- **Découvrir sans agir.** Des profils que personne ne lit ne protègent rien : brancher les profils à haut risque sur Pub/Sub, ou sur des tags de sensibilité avec conditions IAM.
- **Suppression sur demande.** Un effacement exigé par la réglementation n'est complet qu'après le *time travel*, le *fail-safe*, la suppression réversible des objets et l'expiration des sauvegardes : documenter ce délai.

## Alternatives en logiciel libre

- **Microsoft Presidio** (MIT) : détection et anonymisation de données personnelles dans le texte, les images et les données structurées, par règles et par modèles ; le pendant de l'inspection et de la dé-identification, sans découverte continue à l'échelle d'une organisation.
- **ARX** (Apache 2.0) : anonymisation de tables avec k-anonymat, l-diversité et t-proximité, et arbitrage entre risque de ré-identification et utilité des données.
- **Apache Ranger** (Apache 2.0) : politiques centralisées d'accès, de filtrage des lignes et de masquage des colonnes, appliquées par des greffons dans Hive, Spark ou Trino ; l'équivalent des *policy tags* et des politiques de lignes, moteur par moteur.
- **OpenMetadata** (Apache 2.0) : catalogue, glossaire, classification des colonnes, lignage et tests de qualité, dans le rôle de Knowledge Catalog.
- **DataHub** (Apache 2.0) : catalogue, classification et lignage au niveau colonne, avec un modèle de métadonnées extensible.
- **Great Expectations** (Apache 2.0) : règles de qualité des données exécutées dans les pipelines, l'équivalent des scans de qualité.
