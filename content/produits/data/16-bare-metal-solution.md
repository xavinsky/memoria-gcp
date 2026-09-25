---
title: Bare Metal Solution
subgroup: Bases de données
icon: categories/databases
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 16, y: 16, w: 316, h: 308}
    - {label: Extension régionale, x: 366, y: 16, w: 380, h: 308}
  nodes:
    app: {label: Compute Engine, sub: applications, icon: produits/compute-engine, x: 36, y: 44, w: 276}
    mon: {label: Cloud Monitoring, sub: métriques et agent Ops, icon: categories/observability, x: 36, y: 112, w: 276}
    jump: {label: Serveur relais, sub: accès SSH aux serveurs, icon: produits/compute-engine, x: 36, y: 188, w: 276}
    gcs: {label: Cloud Storage, sub: sauvegardes exportées, icon: produits/cloud-storage, x: 36, y: 260, w: 276}
    bms: {label: Bare Metal Solution, sub: serveurs Oracle Database, icon: categories/databases, focus: true, x: 390, y: 96, w: 336, h: 70}
    san: {label: Stockage SAN, sub: "LUN Fibre Channel, instantanés", icon: categories/storage, x: 390, y: 210, w: 336}
  flows:
    - {from: app, to: bms, to_offset: -20, text: "Les applications du VPC joignent les serveurs par une paire de rattachements VLAN Partner Interconnect et un Cloud Router"}
    - {from: jump, to: bms, from_side: top, to_side: bottom, to_offset: -120, control: true, text: "Un serveur relais du VPC ouvre les sessions SSH d'administration : les serveurs n'ont pas d'accès direct depuis Internet"}
    - {from: bms, to: san, text: "Les bases écrivent sur des volumes Fibre Channel, présentés en LUN et partageables entre serveurs pour Oracle RAC"}
    - {from: san, to: gcs, text: "Les sauvegardes RMAN, prises sur un volume NFS ou SAN, sont recopiées vers Cloud Storage"}
    - {from: bms, to: mon, from_offset: 20, text: "Les métriques d'infrastructure des serveurs et l'agent Ops remontent dans Cloud Monitoring"}
deprecie: "Accès restreint à une liste d'autorisation : pour la plupart des déploiements Oracle, Google recommande Oracle Database@Google Cloud."
docs:
  Page produit: https://cloud.google.com/bare-metal
  Documentation: https://docs.cloud.google.com/bare-metal/docs
  Vue d'ensemble: https://docs.cloud.google.com/bare-metal/docs/bms-overview
  Dimensionner son environnement: https://docs.cloud.google.com/bare-metal/docs/bms-planning
  Sécurité: https://docs.cloud.google.com/bare-metal/docs/bms-security
  Bonnes pratiques Oracle: https://docs.cloud.google.com/bare-metal/docs/solutions/oracle/bms-oracle-best-practices
  Offres du partenariat Oracle: https://docs.cloud.google.com/bare-metal/docs/explore-oracle-partnership-offerings
  Oracle Database@Google Cloud: https://docs.cloud.google.com/oracle/database/docs
  API REST: https://docs.cloud.google.com/bare-metal/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/bms
  Oracle sur Google Cloud: https://cloud.google.com/solutions/oracle
  Notes de version: https://docs.cloud.google.com/bare-metal/docs/release-notes
---

## Ce que c'est

Des **serveurs physiques dédiés**, commandés par configuration et par durée, installés dans une *extension régionale* : une salle voisine d'une région Google Cloud, reliée à elle par un réseau géré à faible latence. C'est la réponse aux logiciels qui refusent la virtualisation ou dont les licences se comptent en cœurs physiques — au premier rang desquels Oracle Database.

> [!WARNING]
> Bare Metal Solution est proposé sur liste d'autorisation. Pour la plupart des déploiements Oracle, la documentation renvoie vers **Oracle Database@Google Cloud**, qui exécute Oracle Exadata Database Service et Autonomous Database dans Google Cloud, avec une facturation unique.

- **Partage des rôles.** Google fournit et entretient le matériel, la salle, l'alimentation, le réseau et la supervision matérielle, et installe le système au départ. Tout le reste est au client : système d'exploitation, correctifs, hyperviseur, clusters, bases, sauvegardes, chiffrement, supervision applicative, licences. Le modèle est *bring your own license*.
- **Serveurs** : des configurations fixes de la série `o2`, de 16 vCPU et 192 Go de mémoire à 896 vCPU et 24 To ; processeurs Intel Xeon, quatre à huit ports réseau à 25 Gbit/s, et 200 Go de stockage réseau pour le disque de démarrage. L'hyperthreading est désactivé par défaut, ce qui compte pour le décompte des licences.
- **Stockage** : blocs Fibre Channel présentés en LUN — dédiés à un serveur, ou multipath partagés entre serveurs pour Oracle RAC — et volumes NFS. Par tranches de 1 Tio, jusqu'à 16 Tio en SSD ou HDD, 8 Tio en SSD performance ; 200 LUN au plus par serveur. Les IOPS suivent la taille : environ 7 200 IOPS par Tio en SSD standard. Un volume provisionné n'est ni extensible ni convertible : il faut en commander un autre et migrer.
- **Réseau** : une paire de rattachements VLAN Partner Interconnect relie le VPC au réseau client de l'extension, à travers un Cloud Router. Les serveurs ne sont pas joignables depuis Internet ; l'administration passe par un serveur relais du VPC, ou par la console série interactive.
- **Régions** : une douzaine, dont `europe-west2`, `europe-west3`, `europe-west4`, `us-central1` et `us-east4`.
- **Instantanés** de volumes de stockage, à demander à la commande du volume.

## À quoi ça sert

- Faire tourner Oracle Database, seul ou en RAC, sur du matériel certifié et sans changement de version, à côté des services Google Cloud.
- Reprendre à l'identique un socle qui exige un accès bas niveau au serveur : hyperviseur tiers, logiciel lié au matériel, contrainte de certification de l'éditeur.
- Étape intermédiaire d'une migration : sortir du centre de données propre sans réécrire l'application, puis moderniser ensuite.

**À éviter** dès qu'une autre voie existe, car tout l'entretien logiciel reste à la charge du client, le matériel se commande et se livre, et l'accès au service est restreint à une liste d'autorisation. Pour Oracle, la documentation oriente vers Oracle Database@Google Cloud. Pour une application qui peut changer de moteur, une base gérée demande beaucoup moins d'exploitation : [Cloud SQL](#cloud-sql) ou [AlloyDB](#alloydb) pour le relationnel, [Spanner](#spanner) quand il faut l'échelle. Pour un simple besoin de machine physique dédiée, les instances *bare metal* de Compute Engine suffisent souvent.

## Alternatives en logiciel libre

Le service vend du matériel, pas un logiciel : l'alternative libre porte sur ce qu'on y exécute.

- **PostgreSQL**, avec **Patroni** ou **CloudNativePG** pour la haute disponibilité : la cible la plus courante pour quitter Oracle.
- **orafce**, **pg_dbms_job** et **ora2pg** : les extensions et l'outil de conversion qui rapprochent PostgreSQL du dialecte Oracle et automatisent une partie de la migration.
- **Babelfish for PostgreSQL** : compatibilité du protocole et du dialecte SQL Server au-dessus de PostgreSQL, pour le même genre de sortie.
- **KVM** et **oVirt**, **Proxmox VE** : la virtualisation libre, quand c'est l'hyperviseur tiers qui motivait le serveur physique.
- **MAAS** et **Tinkerbell** : provisionner et gérer son propre parc de serveurs physiques.
