---
title: Cloud Storage
subgroup: Stockage objet et transfert
icon: produits/cloud-storage
schema:
  size: [760, 350]
  zones:
    - {label: Projet GCP, x: 168, y: 16, w: 578, h: 318}
  nodes:
    onprem: {label: Serveurs, sub: "fichiers, archives", external: true, x: 14, y: 34, w: 140}
    apps: {label: Applications, sub: "exports, logs", external: true, x: 14, y: 135, w: 130}
    sts: {label: Storage Transfer, sub: "copie planifiée", icon: categories/storage, x: 196, y: 34, w: 190}
    gcs: {label: Cloud Storage, sub: "bucket Standard", icon: produits/cloud-storage, focus: true, x: 196, y: 130, w: 190, h: 66}
    archive: {label: Classe Archive, sub: "objets rarement lus", icon: produits/cloud-storage, x: 196, y: 250, w: 190}
    bq: {label: BigQuery, sub: "tables, SQL", icon: produits/bigquery, x: 556, y: 100, w: 180}
    spark: {label: Managed Spark, sub: "lecture gs://", icon: categories/data-analytics, x: 556, y: 210, w: 180}
  flows:
    - {from: onprem, to: sts, text: "Un job de transfert récupère périodiquement les fichiers des serveurs existants"}
    - {from: sts, to: gcs, text: "Les fichiers arrivent dans le bucket, avec contrôle d'intégrité et journal de transfert"}
    - {from: apps, to: gcs, text: "Les applications déposent directement leurs objets (exports, sauvegardes, médias)"}
    - {from: gcs, to: bq, from_offset: -12, text: "Chargement par lots dans BigQuery, ou lecture sur place en table externe ou BigLake"}
    - {from: gcs, to: spark, from_offset: 12, text: "Les jobs Spark lisent et réécrivent les fichiers par le connecteur gs://"}
    - {from: gcs, to: archive, text: "Règle de cycle de vie : au bout de N jours l'objet passe en classe Archive, puis une autre règle le supprime"}
docs:
  Page produit: https://cloud.google.com/storage
  Documentation: https://docs.cloud.google.com/storage/docs
  Classes de stockage: https://docs.cloud.google.com/storage/docs/storage-classes
  Cycle de vie des objets: https://docs.cloud.google.com/storage/docs/lifecycle
  Versionnement: https://docs.cloud.google.com/storage/docs/object-versioning
  Cohérence: https://docs.cloud.google.com/storage/docs/consistency
  Contrôle d'accès: https://docs.cloud.google.com/storage/docs/access-control
  API JSON: https://docs.cloud.google.com/storage/docs/json_api
  API XML: https://docs.cloud.google.com/storage/docs/xml-api/overview
  Commandes gcloud storage: https://docs.cloud.google.com/sdk/gcloud/reference/storage
  Bibliothèques clientes: https://docs.cloud.google.com/storage/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/storage/latest
  Quotas et limites: https://docs.cloud.google.com/storage/quotas
  Tarifs: https://cloud.google.com/storage/pricing
  Notes de version: https://docs.cloud.google.com/storage/docs/release-notes
---

## Ce que c'est

Stockage d'objets géré : des fichiers de taille quelconque, identifiés par un nom, rangés dans des **buckets**. Durabilité annoncée de 99,999999999 % par an, aucune capacité à provisionner.

- **Structure.** Un bucket porte un nom unique au monde (3 à 63 caractères, minuscules, pas de préfixe `goog`), un emplacement et une classe par défaut. Les buckets ne s'imbriquent pas : l'arborescence apparente vient des `/` dans le nom des objets. L'option **espace de noms hiérarchique** (à l'activation du bucket, irréversible) crée de vrais dossiers, avec renommage atomique et un débit initial plus élevé.
- **Emplacement** : région, birégion ou multirégion. Il est fixé à la création et détermine la latence, la redondance et le prix.
- **Classes de stockage** : Standard (accès fréquent), Nearline (30 jours de durée minimale), Coldline (90 jours), Archive (365 jours), plus Rapid pour les buckets zonaux. Toutes ont la même durabilité et la même latence de lecture ; les classes froides échangent un stockage moins cher contre des frais de récupération et une durée minimale de facturation.
- **Cycle de vie.** Des règles attachées au bucket combinent une action (`Delete`, `SetStorageClass`, `AbortIncompleteMultipartUpload`) et des conditions (âge, date, nombre de versions, préfixe). `Delete` l'emporte sur `SetStorageClass`, et une modification de configuration met jusqu'à 24 heures à s'appliquer. **Autoclass** fait le même travail automatiquement, d'après les accès réels, contre des frais de gestion.
- **Versionnement.** Activé sur le bucket, il conserve chaque remplacement ou suppression comme version *noncurrent*, identifiée par son numéro de génération. En parallèle, la **suppression réversible** (*soft delete*) retient sept jours par défaut tout objet supprimé, y compris dans un bucket sans versionnement, et protège aussi contre la suppression du bucket.
- **Contrôle d'accès.** Deux systèmes coexistent : IAM, posé sur le projet, le bucket ou un **dossier géré** (IAM appliqué à tous les objets d'un préfixe), et les ACL [!DECONSEILLE], système hérité conçu pour l'interopérabilité avec Amazon S3, posées bucket par bucket ou objet par objet. Ils agissent en parallèle : **il suffit que l'un des deux accorde l'accès**, et aucun ne voit ce que l'autre accorde ; une ACL publique sur un objet l'expose, quelle que soit la stratégie IAM du bucket. Une **stratégie de refus** IAM, attachée au projet, au dossier ou à l'organisation (jamais au bucket), l'emporte sur les deux pour les permissions qu'elle vise. L'**accès uniforme au niveau du bucket**, recommandé par Google, désactive les ACL : seul IAM compte. Il devient définitif après 90 jours, et il est requis pour les dossiers gérés.
- **Cohérence forte** sur les opérations d'objets : lecture après écriture, après mise à jour de métadonnées, après suppression, et listage, y compris en birégion et en multirégion. Restent à cohérence à terme les changements de droits et la recréation d'un bucket après suppression ; un objet public mis en cache reste servi jusqu'à l'expiration de son `Cache-Control`.
- **Facturation** : stockage au Gio-mois selon la classe et l'emplacement, opérations (classes A et B), transfert sortant, plus les frais de récupération et de suppression anticipée des classes froides.

> [!WARNING]
> Le nom d'un bucket est public et réutilisable par n'importe qui après suppression. N'y mettre ni identifiant d'utilisateur, ni adresse e-mail, ni nom de projet.

## À quoi ça sert

- Zone d'atterrissage d'un lac de données : fichiers bruts lus ensuite par [BigQuery](#bigquery) ou [Managed Service for Apache Spark](#managed-service-for-apache-spark).
- Sauvegardes, archives légales et réglementaires, reprise après sinistre.
- Servir des contenus statiques (site, images, vidéos, artefacts de build).
- Stocker des jeux d'entraînement et des points de contrôle de modèles, montés en système de fichiers par Cloud Storage FUSE.

**À éviter** comme système de fichiers partagé pour des écritures concurrentes ou des modifications en place : un objet se remplace entièrement, il ne se modifie pas par morceaux. Préférer Filestore pour du NFS géré, un disque Persistent Disk ou Hyperdisk pour une VM, et une base de données pour des enregistrements mis à jour souvent (voir [Choisir une base de données](#choisir-une-base)).

> [!TIP]
> Un objet passé en Coldline puis supprimé au bout d'une semaine est facturé 90 jours. Vérifier les durées minimales avant d'écrire une règle de cycle de vie sur des données à rotation rapide.

## Alternatives en logiciel libre

- **Ceph** avec sa passerelle RADOS Gateway : stockage unifié objet, bloc et fichier, pour de grandes flottes.
- **OpenStack Swift** : stockage d'objets distribué, conçu pour des clusters multi-régions.
- **Apache Ozone** : espace de noms objet et fichier pour les traitements Hadoop et Spark.
- **SeaweedFS**, **Garage** : serveurs compatibles S3 de faible empreinte, pour des déploiements modestes ou répartis.
