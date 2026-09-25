---
title: Backup and DR Service
subgroup: Stockage bloc et fichiers
icon: categories/storage
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 14, y: 16, w: 732, h: 310}
  nodes:
    plan: {label: Plan de sauvegarde, sub: "règles horaires à annuelles", icon: categories/storage, x: 40, y: 40, w: 220}
    work: {label: Charges de travail, sub: "VMs, disques, bases, NFS", icon: produits/compute-engine, x: 40, y: 160, w: 220, h: 60}
    mon: {label: Journaux et alertes, sub: "Cloud Monitoring", icon: categories/observability, x: 320, y: 40, w: 200}
    job: {label: Job de sauvegarde, sub: "incrémental", icon: categories/storage, x: 320, y: 160, w: 180, h: 60}
    vault: {label: Coffre, sub: "immuable, WORM", icon: categories/storage, focus: true, x: 550, y: 160, w: 190, h: 64}
    restore: {label: Restauration, sub: "fichier ou VM", icon: categories/storage, x: 320, y: 250, w: 180}
  flows:
    - {from: plan, to: work, control: true, text: "Le plan associe ses règles — fréquence, fenêtre de lancement, durée de rétention — aux ressources à protéger, découvertes automatiquement"}
    - {from: work, to: job, text: "À l'heure dite, un job capture les blocs modifiés depuis la sauvegarde précédente, sans interrompre la charge"}
    - {from: job, to: vault, text: "La sauvegarde est écrite dans le coffre, verrouillée pour la durée de rétention imposée, hors d'atteinte des administrateurs du projet"}
    - {from: job, to: mon, control: true, text: "Chaque exécution remonte son état dans Cloud Logging et Cloud Monitoring, avec trois nouvelles tentatives en cas d'échec"}
    - {from: vault, to: restore, from_side: bottom, to_side: right, text: "Une restauration remonte un volume, recrée l'instance ou extrait quelques fichiers depuis un point de reprise"}
    - {from: restore, to: work, text: "La cible peut être la ressource d'origine, un clone de recette ou un autre projet, voire une autre région"}
captures:
  - image: https://docs.cloud.google.com/static/bare-metal/docs/solutions/oracle/images/backup-and-dr-timeline-ramp-view.png
    page: https://docs.cloud.google.com/bare-metal/docs/solutions/oracle/bms-oracle-backup-and-dr
    legende: "Backup and DR : choix d'une image à restaurer sur la frise des snapshots et des copies OnVault d'une base Oracle, dans la console de gestion"
  - image: https://docs.cloud.google.com/static/bare-metal/docs/solutions/oracle/images/backup-and-dr-apply-backup-plan.png
    page: https://docs.cloud.google.com/bare-metal/docs/solutions/oracle/bms-oracle-backup-and-dr
    legende: "Backup and DR : application d'un modèle et d'un profil de plan de sauvegarde à une base Oracle, avec ses règles snapshot et OnVault, dans la console de gestion"
docs:
  Page produit: https://cloud.google.com/backup-disaster-recovery
  Documentation: https://docs.cloud.google.com/backup-disaster-recovery/docs
  Vue d'ensemble: https://docs.cloud.google.com/backup-disaster-recovery/docs/concepts/backup-dr
  Plans de sauvegarde: https://docs.cloud.google.com/backup-disaster-recovery/docs/concepts/backup-plan
  Coffres de sauvegarde: https://docs.cloud.google.com/backup-disaster-recovery/docs/concepts/backup-vault
  Matrice de compatibilité: https://docs.cloud.google.com/backup-disaster-recovery/docs/supportmatrix-backupdr
  Créer un coffre: https://docs.cloud.google.com/backup-disaster-recovery/docs/cloud-console/backup-vault-create
  Protéger des instances Compute Engine: https://docs.cloud.google.com/backup-disaster-recovery/docs/quickstarts/gce-instances-backup-vault
  Suivi des jobs: https://docs.cloud.google.com/backup-disaster-recovery/docs/monitor-reports/monitor-jobs
  Contrôle d'accès: https://docs.cloud.google.com/backup-disaster-recovery/docs/access-control
  API REST: https://docs.cloud.google.com/backup-disaster-recovery/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/backup-dr
  Bibliothèques clientes: https://docs.cloud.google.com/backup-disaster-recovery/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/backupdr/latest
  Tarifs: https://cloud.google.com/backup-disaster-recovery/pricing
  Notes de version: https://docs.cloud.google.com/backup-disaster-recovery/docs/release-notes
---

## Ce que c'est

Service de sauvegarde et de reprise centralisé pour les charges de travail d'entreprise, sur Google Cloud comme en environnement hybride. Il applique des règles depuis une console unique, capture des sauvegardes cohérentes avec l'application et les range dans un stockage que personne ne peut modifier.

- **Hiérarchie des objets.** Un **coffre de sauvegarde** (*backup vault*) est un espace de stockage isolé, géré par Google, hors du projet des ressources sauvegardées ; il impose une durée de rétention minimale, jusqu'à 99 ans, et rend les sauvegardes immuables et indestructibles. Un **plan de sauvegarde** désigne un coffre et regroupe des **règles** ; une **association** relie le plan aux ressources protégées.
- **Règles de sauvegarde.** Chacune fixe une récurrence (horaire, quotidienne, hebdomadaire, mensuelle, annuelle), une fenêtre de lancement d'au moins six heures et une durée de rétention. Deux règles d'un même plan ne peuvent pas avoir la même périodicité. Une rétention maximale distincte encadre les sauvegardes lancées à la main.
- **Charges de travail prises en charge.** Instances [Compute Engine](#compute-engine) et leurs disques, instances [Filestore](#filestore), VM Google Cloud VMware Engine, [Cloud SQL](#cloud-sql) (MySQL, PostgreSQL, SQL Server) et [AlloyDB](#alloydb) en mode cohérent avec l'application ; Oracle Database, SQL Server, SAP HANA, MySQL et PostgreSQL auto-gérés sur VM ou sur [Bare Metal Solution](#bare-metal-solution).
- **Journaux de transactions.** Pour les bases, la sauvegarde des journaux entre deux captures complètes ouvre la restauration à un instant précis (*point-in-time recovery*).
- **Capture incrémentale permanente.** Seuls les blocs modifiés sont transférés ; le montage instantané d'un volume écourte le temps de reprise, sans attendre la recopie complète des données.
- **Deux cibles de stockage.** Le coffre, recommandé, qui apporte immutabilité et rétention imposée. Ou un **stockage auto-géré** — instantanés de disques et buckets [Cloud Storage](#cloud-storage) du projet — administré depuis la console d'appliance, sans garantie d'immutabilité.
- **Restauration.** Récupération de fichiers isolés, remontage d'un volume, recréation complète d'une charge, clonage entre projets et entre régions pour les répétitions de reprise après sinistre.
- **Sécurité.** Chiffrement CMEK (Compute Engine, Persistent Disk, Cloud SQL), rôles IAM dédiés, périmètres VPC Service Controls, intégration à Cloud Logging et Cloud Monitoring. Un plan pointant vers un coffre sans CMEK ne peut pas protéger une ressource chiffrée par CMEK.
- **Facturation** aux frais de gestion par ressource protégée et au stockage occupé dans le coffre. Un essai de 30 jours suspend les deux sur un projet éligible.

> [!WARNING]
> La rétention imposée d'un coffre prime sur celle du plan : une sauvegarde ne peut pas être supprimée avant son terme, même par un administrateur de l'organisation. C'est la protection contre le rançongiciel, et c'est aussi une facture qu'on ne peut pas arrêter en cours de route.

## À quoi ça sert

- Sauvegarde centralisée d'un parc de VM et de bases, avec une politique unique et un inventaire des ressources non protégées.
- Protection contre le rançongiciel et la suppression malveillante, grâce à un stockage inaltérable situé hors du projet compromis.
- Conformité réglementaire imposant une durée de conservation opposable et une piste d'audit.
- Sauvegarde de bases auto-gérées et d'applications d'entreprise (Oracle, SAP HANA, SQL Server) avec cohérence applicative, y compris sur Bare Metal Solution.
- Répétitions de reprise après sinistre : cloner la production dans une autre région ou un autre projet sans y toucher.

**À éviter** quand un calendrier d'instantanés [Persistent Disk](#persistent-disk) ou [Hyperdisk](#hyperdisk) suffit : pour quelques disques sans exigence d'immutabilité, il est plus simple et bien moins cher. À éviter aussi pour les sauvegardes propres à un service managé lorsqu'elles couvrent déjà le besoin — sauvegardes automatiques de Cloud SQL, instantanés [Filestore](#filestore) — et pour l'archivage de fichiers, où une règle de cycle de vie sur [Cloud Storage](#cloud-storage) fait le travail.

## Alternatives en logiciel libre

- **Bacula** et **Bareos** : ordonnanceurs de sauvegarde d'entreprise avec catalogue, politiques de rétention, agents par système et lecteurs de bandes — le modèle « plan, règles, jobs » le plus proche.
- **Restic** et **BorgBackup** : sauvegarde incrémentale déduplicée et chiffrée vers un dépôt distant ; Restic sait viser un bucket compatible S3 et verrouiller un dépôt en ajout seul.
- **Velero** : sauvegarde et restauration des ressources Kubernetes et de leurs volumes persistants, avec planification et restauration sélective.
- [!SOMMEIL] **Amanda** : sauvegarde réseau centralisée, répandue dans les parcs UNIX.
- **urBackup** : sauvegarde d'images et de fichiers de postes et serveurs, avec agents Windows et Linux.
- **ZFS** ou **Btrfs** avec envoi incrémental : instantanés et réplication vers un dépôt distant, avec des instantanés en lecture seule pour l'immutabilité.
