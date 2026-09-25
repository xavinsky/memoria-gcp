---
title: NetApp Volumes
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 386]
  zones:
    - {label: Projet GCP, x: 14, y: 16, w: 732, h: 356}
  nodes:
    win: {label: VMs Windows, sub: "partage SMB", icon: produits/compute-engine, x: 40, y: 70, w: 210}
    lin: {label: VMs Linux, sub: "montage NFSv4.1", icon: produits/compute-engine, x: 40, y: 200, w: 210}
    pool: {label: Pool de stockage, sub: "niveau Premium", icon: categories/storage, x: 290, y: 40, w: 200}
    vol: {label: Volume, sub: "NFS et SMB", icon: categories/storage, focus: true, x: 290, y: 170, w: 200, h: 64}
    snap: {label: Instantanés, sub: "restauration fichier", icon: categories/storage, x: 290, y: 300, w: 200}
    ad: {label: Active Directory, sub: "domaine Windows", icon: categories/security-identity, x: 540, y: 40, w: 200}
    rep: {label: Réplication, sub: "autre région", icon: categories/storage, x: 540, y: 170, w: 200}
  flows:
    - {from: ad, to: pool, control: true, text: "Une stratégie Active Directory rattache le pool au domaine ; c'est elle qui rend le partage SMB possible"}
    - {from: pool, to: vol, text: "Le volume est taillé dans le pool, qui impose l'emplacement, le niveau de service, le réseau VPC et la clé de chiffrement"}
    - {from: win, to: vol, from_side: right, to_side: left, to_offset: -14, text: "Les postes Windows montent le partage en SMB, avec les droits hérités du domaine"}
    - {from: lin, to: vol, from_side: right, to_side: left, to_offset: 14, text: "Les VM Linux montent le même volume en NFSv3 ou NFSv4.1, avec un modèle de droits UNIX"}
    - {from: vol, to: snap, text: "Les instantanés automatiques permettent de rendre un fichier à son état antérieur, ou de ramener tout le volume en arrière"}
    - {from: vol, to: rep, text: "La réplication asynchrone entretient une copie du volume dans une autre région, prête à prendre le relais"}
docs:
  Page produit: https://cloud.google.com/netapp-volumes
  Documentation: https://docs.cloud.google.com/netapp/volumes/docs
  Vue d'ensemble: https://docs.cloud.google.com/netapp/volumes/docs/discover/overview
  Niveaux de service: https://docs.cloud.google.com/netapp/volumes/docs/discover/service-levels
  Pools de stockage: https://docs.cloud.google.com/netapp/volumes/docs/configure-and-use/storage-pools/overview
  Volumes: https://docs.cloud.google.com/netapp/volumes/docs/configure-and-use/volumes/overview
  Instantanés: https://docs.cloud.google.com/netapp/volumes/docs/configure-and-use/volume-snapshots/overview
  Réplication de volume: https://docs.cloud.google.com/netapp/volumes/docs/protect-data/about-volume-replication
  Hiérarchisation automatique: https://docs.cloud.google.com/netapp/volumes/docs/configure-and-use/volumes/manage-auto-tiering
  Active Directory: https://docs.cloud.google.com/netapp/volumes/docs/configure-and-use/active-directory/about-ad
  Connecter des clients NFS: https://docs.cloud.google.com/netapp/volumes/docs/connect-clients/connect-nfs-clients
  API REST: https://docs.cloud.google.com/netapp/volumes/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/netapp
  Client Python: https://docs.cloud.google.com/python/docs/reference/netapp/latest
  Quotas et limites: https://docs.cloud.google.com/netapp/volumes/docs/quotas
  Tarifs: https://cloud.google.com/netapp/volumes/pricing
  Notes de version: https://docs.cloud.google.com/netapp/volumes/docs/release-notes
---

## Ce que c'est

Service de stockage de fichiers géré, bâti sur la technologie ONTAP de NetApp et exploité dans les centres de données Google. Il apporte au cloud les fonctions attendues d'une baie NAS d'entreprise : multiprotocole, instantanés, clonage instantané, hiérarchisation automatique, réplication.

- **Deux niveaux d'objets.** Un **pool de stockage** fixe l'emplacement, le niveau de service, le réseau VPC, la stratégie Active Directory, les réglages LDAP et la clé CMEK ; les **volumes** sont taillés dedans, de 1 Gio à 3 Pio, créés en quelques secondes. La facturation porte sur la capacité allouée au pool, pas sur l'occupation des volumes.
- **Niveaux de service :**
  - **Flex Unified** — usage général, capacité et performances provisionnées indépendamment : de 64 Mio/s à 5 Gio/s par pas de 1 Mio/s, chaque Mio/s ouvrant droit à 16 IOPS, avec jusqu'à 160 000 IOPS supplémentaires. Les pools de grande capacité montent à 22 Gio/s et 750 000 IOPS. Deux modes d'exploitation : *Default-mode*, entièrement géré, et *ONTAP-mode*, qui expose les commandes ONTAP à ceux qui savent s'en servir.
  - **Standard** — 16 Kio/s par Gio de volume, jusqu'à 1,6 Gio/s : partages de fichiers courants, fichiers partagés SAP, banques VMware Engine.
  - **Premium** — 64 Kio/s par Gio, jusqu'à 4,5 Gio/s (30 Gio/s en volume de grande capacité) : bases auto-gérées, NFS d'entreprise, postes virtuels.
  - **Extreme** — 128 Kio/s par Gio, mêmes plafonds que Premium : charges les plus exigeantes en débit. Un volume passe de Premium à Extreme et inversement sans recopie.
  - **Flex File** — usage général ; plus aucun nouveau pool ne pourra être créé à compter du 15 septembre 2026, les pools existants restant pris en charge, avec une migration prévue vers Flex Unified.
- **Protocoles.** NFSv3, NFSv4.1 et NFSv4.2, SMB 2.1, 3.0 et 3.1.1, iSCSI et NVMe/TCP ; le mode ONTAP ajoute le multiprotocole S3. Un même volume peut servir simultanément des clients UNIX et Windows.
- **Active Directory.** C'est le seul annuaire pris en charge, et il est obligatoire pour SMB. La stratégie AD est attachée au pool — un pool, une stratégie — avec un test de connectivité intégré.
- **Instantanés et clones.** Instantanés automatiques ou manuels, restauration d'un fichier isolé ou retour complet du volume, création d'un nouveau volume à partir d'un instantané, clonage rapide pour les environnements de test.
- **Hiérarchisation automatique.** Les données peu lues descendent de façon transparente vers un palier froid moins cher. Elle s'active à la création du pool pour Flex, sur un pool existant pour Premium et Extreme, et le choix est définitif.
- **Disponibilité et réplication.** Un pool régional Flex maintient deux répliques synchrones dans deux zones, l'une active et l'autre en attente, avec bascule manuelle ou automatique. La réplication de volume, asynchrone, entretient une copie dans une autre région ; **FlexCache** met en cache un volume ONTAP distant.

> [!WARNING]
> Un pool régional Flex sert ses volumes depuis sa seule zone active. Placer les VM clientes dans cette zone, sinon chaque entrée-sortie traverse la région et la latence s'en ressent.

## À quoi ça sert

- Reprise de partages de fichiers d'entreprise existants, avec les mêmes protocoles, les mêmes droits et le même annuaire qu'une baie sur site.
- Environnements mixtes Windows et Linux qui doivent voir la même arborescence en SMB et en NFS.
- Bases de données auto-gérées, SAP, postes de travail virtuels et banques de données VMware Engine réclamant une latence basse et un débit garanti.
- Clonage instantané de jeux de données de production pour le développement, les tests et l'analyse, sans recopier les octets.
- Volumes de grande capacité à conserver longtemps, avec descente automatique des données dormantes vers un palier froid.

**À éviter** quand un simple partage NFS suffit : [Filestore](#filestore) est plus simple à exploiter et moins cher. À éviter aussi pour du calcul parallèle à très haut débit agrégé, qui relève de [Managed Lustre](#managed-lustre), et pour des fichiers déposés puis relus par des services managés, où [Cloud Storage](#cloud-storage) reste le bon choix.

## Alternatives en logiciel libre

- **Samba** : serveur SMB et contrôleur de domaine compatible Active Directory — l'équivalent de la partie SMB, jonction au domaine comprise.
- **NFS-Ganesha** ou le serveur NFS du noyau Linux : pour la partie NFS, exportant le même arbre que Samba afin d'obtenir un accès multiprotocole.
- **ZFS** : instantanés, clones instantanés, compression, déduplication et envoi incrémental vers un second site — le plus proche du modèle de données d'ONTAP.
- **CephFS** avec sa passerelle NFS et Samba : espace de noms distribué, instantanés et quotas sur une grappe.
- **OpenEBS** ou **LIO** (`targetcli`) pour la partie bloc, si l'on cherche l'équivalent des volumes iSCSI.
- **MooseFS** (GPL v2) : système de fichiers réparti avec paliers de stockage par classes, proche de la hiérarchisation automatique.
- [!SOMMEIL] **LizardFS** (GPL v3) : dérivé de MooseFS, avec les mêmes classes de stockage.
