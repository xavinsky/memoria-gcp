---
title: Transfer Appliance
subgroup: Stockage objet et transfert
icon: categories/storage
schema:
  size: [760, 340]
  zones:
    - {label: Centre de données du client, x: 6, y: 20, w: 236, h: 300}
    - {label: Projet GCP, x: 436, y: 20, w: 310, h: 300}
  nodes:
    src: {label: Stockage existant, sub: "NAS, SAN, archives", external: true, x: 18, y: 44, w: 206}
    ta: {label: Transfer Appliance, sub: "TA40 ou TA300, SSD", icon: categories/storage, focus: true, x: 18, y: 170, w: 206, h: 66}
    fac: {label: Site Google, sub: "téléversement", external: true, x: 266, y: 175, w: 140}
    bq: {label: BigQuery, sub: "analyse", icon: produits/bigquery, x: 452, y: 44, w: 180}
    gcs: {label: Cloud Storage, sub: "bucket de destination", icon: produits/cloud-storage, x: 452, y: 170, w: 230, h: 66}
    kms: {label: Cloud KMS, sub: "clé CMEK", icon: categories/security-identity, x: 452, y: 250, w: 180}
  flows:
    - {from: src, to: ta, text: "Les serveurs montent le partage NFS ou SMB de l'appliance et y copient les données"}
    - {from: kms, to: ta, control: true, from_side: left, to_side: bottom, text: "Les données sont chiffrées en AES-256 avec une clé que le client gère dans Cloud KMS"}
    - {from: ta, to: fac, text: "L'appliance scellée est expédiée à un site Google : environ trois semaines pour le cycle complet"}
    - {from: fac, to: gcs, text: "Google téléverse les données dans le bucket, puis efface l'appliance selon la norme NIST 800-88"}
    - {from: gcs, to: bq, text: "Les fichiers sont ensuite chargés dans l'entrepôt ou exploités sur place"}
docs:
  Documentation: https://docs.cloud.google.com/transfer-appliance/docs/4.0/overview
  Spécifications: https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications
  Sécurité et chiffrement: https://docs.cloud.google.com/transfer-appliance/docs/4.0/security-and-encryption
  Commander une appliance: https://docs.cloud.google.com/transfer-appliance/docs/4.0/order-appliance
  Déroulé de la procédure: https://docs.cloud.google.com/transfer-appliance/docs/4.0/procedure-guide
  Transfert en ligne: https://docs.cloud.google.com/transfer-appliance/docs/4.0/online-transfer
  Ressources: https://docs.cloud.google.com/transfer-appliance/docs/4.0/resources
  Assistance: https://docs.cloud.google.com/transfer-appliance/docs/4.0/support
  Tarifs: https://cloud.google.com/transfer-appliance/pricing
  Notes de version: https://docs.cloud.google.com/transfer-appliance/docs/release-notes
---

## Ce que c'est

Baie de stockage que Google expédie chez le client, qui la remplit et la renvoie ; Google verse ensuite les données dans un bucket [Cloud Storage](#cloud-storage). C'est un transfert **hors réseau**, pour les volumes qu'une liaison Internet mettrait des mois à écouler.

- **Modèles** : TA40 et TA300, en version rackable ou autonome, sur disques SSD. Capacité utile maximale de 40 à 300 To de données chiffrées selon le modèle ; on commande plusieurs appliances pour aller plus vite ou plus loin.
- **Raccordement** : port RJ45 à 10 Gbit/s, et QSFP28 à 100 Gbit/s sur les modèles V2. Les données sont copiées par un partage NFS ou SMB, ou par SSH et SCP — un seul de ces protocoles est actif à la fois sur une appliance.
- **Sécurité** : boîtier résistant à l'ouverture et étiquettes inviolables, puce TPM vérifiée par attestation à distance avant tout raccordement, chiffrement AES-256 avec une **clé gérée par le client** dans Cloud KMS. Après téléversement, Google efface l'appliance conformément à la norme NIST 800-88 et fournit un certificat d'effacement sur demande.
- **Mode en ligne** : l'appliance peut aussi diffuser les données directement vers le bucket au fur et à mesure de la copie, sans attendre l'expédition ; le mode se bascule en ligne ou hors ligne par une commande.
- **Délais** : environ trois semaines pour un cycle complet. L'ordre de grandeur donné par la documentation : 300 To capturés en moins de 25 jours, puis disponibles dans Cloud Storage une dizaine de jours ouvrés plus tard, sans consommer de bande passante sortante.
- **Disponibilité** : États-Unis, États membres de l'Union européenne, Royaume-Uni, Singapour, Japon, Canada et Inde. Pour l'Union européenne, les appliances partent de Belgique et y reviennent.

## À quoi ça sert

- Migrer un centre de données ou un lac de données volumineux : archives, images médicales, rushes vidéo, sauvegardes historiques.
- Collecter des données produites hors ligne, sur des sites mal connectés — navires, chantiers, campagnes de mesure, laboratoires partenaires.
- Amorcer une architecture hybride : une copie du patrimoine dans le cloud, exploitée ensuite par [BigQuery](#bigquery) ou [Managed Service for Apache Spark](#managed-service-for-apache-spark), pendant que l'existant continue de tourner sur site.

**À éviter** dès que le réseau peut écouler le volume en moins d'une semaine, ou qu'il faut des transferts répétés et incrémentaux : [Storage Transfer Service](#storage-transfer-service) fait le travail sans logistique. À éviter aussi pour des données qu'il faut garder synchronisées : l'appliance fige un instantané, elle ne réplique rien.

> [!WARNING]
> Beaucoup de très petits fichiers allongent nettement la reconstitution des données après téléversement. Regrouper les arborescences fines en archives avant la copie.

## Alternatives en logiciel libre

Il n'existe pas d'équivalent libre : le service est d'abord du matériel et de la logistique. Côté logiciel, la copie hors ligne se monte avec des outils classiques :

- **rsync** ou **Rclone** vers un tableau de disques ou une baie NAS que l'on transporte, puis **Rclone** ou **s5cmd** pour verser le contenu dans le stockage objet d'arrivée.
- **tar** avec **GNU Parallel** pour regrouper les arborescences de petits fichiers avant la copie.
- **LUKS** (dm-crypt) pour chiffrer les disques transportés, l'équivalent du chiffrement matériel de l'appliance.
- **par2** pour ajouter des données de redondance et détecter la corruption au retour.
