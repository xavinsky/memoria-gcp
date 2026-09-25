---
title: "Cloud Storage : classes et cycle de vie"
---

Trois décisions fixent le coût et la résilience d'un bucket [Cloud Storage](#cloud-storage) : l'**emplacement** (fixé à la création), la **classe de stockage** de chaque objet (modifiable ensuite), et la **protection** contre l'effacement. Les classes ne changent ni la durabilité ni la latence de lecture : elles échangent un stockage moins cher contre une durée minimale de facturation et des frais de lecture.

## Classes de stockage

| Classe | Nom API | Durée minimale | Frais de récupération | Disponibilité typique (région / bi- ou multirégion) | Rythme d'accès visé |
|---|---|---|---|---|---|
| **Standard** | `STANDARD` | Aucune | Aucun | 99,99 % / > 99,99 % | Données chaudes, ou conservées peu de temps |
| **Nearline** | `NEARLINE` | 30 jours | 0,01 $/Gio | 99,9 % / 99,95 % | Au plus une fois par mois |
| **Coldline** | `COLDLINE` | 90 jours | 0,02 $/Gio | 99,9 % / 99,95 % | Au plus une fois par trimestre |
| **Archive** | `ARCHIVE` | 365 jours | 0,05 $/Gio | 99,9 % / 99,95 % | Moins d'une fois par an : archives légales, reprise après sinistre |

- **Durée minimale** : un objet supprimé, remplacé ou déplacé avant ce délai est facturé comme s'il était resté jusqu'au bout (frais de *suppression anticipée*). Réécrire un objet pour changer sa classe compte comme un remplacement ; un changement de classe par une règle de cycle de vie, non.
- **Frais de récupération** : dus à chaque lecture, copie ou réécriture d'un objet d'une classe froide, en plus des opérations et du réseau, au volume réellement lu. Ils ne s'appliquent ni dans un bucket Autoclass, ni à la restauration d'un objet supprimé de façon réversible.
- Les *SLA* de disponibilité sont un cran en dessous des valeurs typiques : 99,95 % (bi- et multirégion) ou 99,9 % (région) en Standard, 99,9 % ou 99,0 % pour les trois classes froides.
- **Rapid** est une cinquième classe, réservée aux buckets zonaux (*Rapid Bucket*) : stockage au plus près du calcul pour l'IA et l'analytique intensive, sans redondance entre zones.

> [!TIP]
> Archive se lit en millisecondes, comme Standard : il n'y a pas de délai de restauration. Le vrai critère est la fréquence de lecture : les frais de récupération y sont cinq fois ceux de Nearline.

## Types d'emplacement

| | Région | Birégion (*dual-region*) | Multirégion |
|---|---|---|---|
| Redondance | Entre zones d'une région, synchrone | Entre deux régions choisies, asynchrone | Entre au moins deux régions d'une zone géographique (US, EU, ASIA), asynchrone |
| Panne d'une région | Données indisponibles | Bascule automatique, RTO nul, chemins inchangés | Bascule automatique, RTO nul, chemins inchangés |
| Réplication | — | Par défaut : 99,9 % des nouveaux objets en une heure, 100 % en 12 heures ; **réplication turbo** en option : 100 % en 15 minutes | Par défaut uniquement |
| Prix du stockage | Le plus bas | Le plus haut | Entre les deux |
| Coûts annexes | Pas de transfert sortant pour une lecture dans la région | Réplication facturée à l'écriture, lecture gratuite depuis les deux régions | Réplication facturée à l'écriture, transfert sortant facturé à la lecture |
| Usage type | Analytique et calcul colocalisés, données éphémères | Continuité d'activité avec un RPO court, analytique dans deux régions | Contenu servi à des utilisateurs répartis |

- Des données de courte durée (fichiers intermédiaires d'un pipeline) vont dans une **région**, celle du calcul : pas de frais de réplication, pas de transfert.
- Un **RPO** court et garanti ne s'obtient qu'en **birégion avec réplication turbo**. La multirégion ne propose que la réplication par défaut.
- Quand les deux copies doivent être indépendantes (propriétaire, chiffrement ou classe différents, bucket d'un partenaire), la **réplication inter-buckets** copie les objets de façon asynchrone d'un bucket vers un autre.

## Changer de classe : Autoclass ou règles de cycle de vie

| | Autoclass | Règles de cycle de vie |
|---|---|---|
| Critère | Accès réels à chaque objet | Âge, date, nombre de versions, préfixe ou suffixe, classe actuelle |
| Sens des transitions | Vers le froid sans accès, retour en Standard à la lecture | Vers le froid uniquement (Standard → Nearline → Coldline → Archive) |
| Rythme | Standard → Nearline après 30 jours sans accès ; si la classe terminale est Archive : Coldline à 90 jours, Archive à 365 jours | Défini par la règle |
| Coûts | Frais de gestion, frais d'activation ; ni frais de récupération ni suppression anticipée | Aucun frais propre ; frais de récupération et durées minimales normaux |
| Petits objets | Moins de 128 Kio : restent en Standard | Pas de seuil |
| Autres actions | — | `Delete`, `AbortIncompleteMultipartUpload` |

- **Autoclass** convient quand les accès sont variés ou inconnus. La classe terminale est Nearline par défaut, Archive sur option. Il est à écarter quand on sait déjà quels objets sont chauds et lesquels ne seront jamais relus, ou quand un service relit tout le bucket régulièrement (un scan de Sensitive Data Protection ramène chaque objet en Standard).
- **Les deux se combinent partiellement** : un bucket Autoclass accepte des règles `Delete`, mais refuse toute règle `SetStorageClass` ou toute condition `matchesStorageClass`.
- **Précédence** : si plusieurs règles s'appliquent au même objet, `Delete` l'emporte, puis la classe la moins chère. Une modification de configuration met jusqu'à 24 heures à prendre effet, et l'ancienne configuration peut encore agir pendant ce délai.

Exemple de fichier `lifecycle.json` pour des journaux : Nearline à 30 jours, Archive à un an, suppression à sept ans, trois versions *noncurrent* au plus, gardées 30 jours, et nettoyage des envois multiparties abandonnés.

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
        "condition": {"age": 365, "matchesStorageClass": ["NEARLINE"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 2555}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"isLive": false, "numNewerVersions": 3}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"isLive": false, "daysSinceNoncurrentTime": 30}
      },
      {
        "action": {"type": "AbortIncompleteMultipartUpload"},
        "condition": {"age": 7}
      }
    ]
  }
}
```

> [!WARNING]
> Une règle vers Coldline sur des objets supprimés au bout d'une semaine fait payer 90 jours par objet. Comparer la durée de vie réelle des données aux durées minimales avant d'écrire la règle.

## Protéger contre l'effacement

| Mécanisme | Portée | Ce qu'il empêche | Réversible |
|---|---|---|---|
| **Suppression réversible** (*soft delete*) | Bucket, actif par défaut | Perte d'un objet ou d'un bucket supprimé : restauration pendant 7 jours par défaut, de 7 à 90 jours sur réglage | Oui (durée 0 = désactivé) |
| **Versionnement d'objets** | Bucket | Perte d'une version remplacée : chaque remplacement garde l'ancienne version, identifiée par sa génération | Oui |
| **Politique de conservation** (*Bucket Lock*) | Bucket | Suppression ou remplacement d'un objet avant la fin de la durée, jusqu'à 100 ans | Oui tant qu'elle n'est pas verrouillée |
| **Verrouillage de la politique** | Bucket | Réduction ou retrait de la politique ; le bucket ne se supprime qu'une fois tous ses objets expirés | **Non** : la durée peut seulement augmenter |
| **Object Retention Lock** | Objet | Suppression avant une date propre à chaque objet ; mode `Unlocked` modifiable, mode `Locked` définitif | Fonction non désactivable une fois activée sur le bucket |
| **Conservation temporaire ou sur événement** (*hold*) | Objet | Suppression tant que la retenue est posée | Oui |

- Suppression réversible et versionnement ne font pas double emploi : le premier rattrape une suppression, y compris celle du bucket ; le second garde l'historique des remplacements. Les objets supprimés de façon réversible restent facturés au stockage pendant leur rétention.
- Le versionnement sans règle de cycle de vie fait croître le bucket sans limite : l'associer à `numNewerVersions` ou `daysSinceNoncurrentTime`, comme dans l'exemple ci-dessus.
- Les obligations réglementaires (conservation de pièces pendant N années) relèvent d'une politique de conservation **verrouillée**, ou d'Object Retention Lock quand la durée varie d'un objet à l'autre.

## Surveiller un bucket de lac de données

| Outil | Ce qu'il donne | Portée et fraîcheur |
|---|---|---|
| **Métriques Cloud Storage** dans [Cloud Monitoring](#cloud-monitoring) | `storage/v2/total_bytes` et `storage/object_count` par classe ; la v2 sépare objets actifs, versions *noncurrent*, objets supprimés de façon réversible et envois multiparties. `storage/v2/deleted_bytes`, `api/request_count` par méthode et code de réponse | Par bucket ; volumes mesurés une fois par jour, requêtes échantillonnées chaque minute. Onglet *Observabilité* du bucket, page *Monitoring* de Cloud Storage pour le projet |
| **Rapports d'inventaire** | Liste des objets d'un bucket avec les métadonnées choisies (classe, taille, ETag, type de contenu), en CSV ou Parquet, écrite selon un planning dans un bucket de destination du même emplacement | Un bucket par configuration ; livraison ni garantie quotidienne ni garantie complète. Facturés selon l'emplacement |
| **Jeux de données Storage Insights** | Index des métadonnées et de l'activité (mutations, erreurs, activité par bucket et par projet, trafic par région), lu en SQL dans un dataset BigQuery lié | Bucket, dossier, projet ou organisation ; métadonnées rafraîchies chaque jour, activité toutes les 4 à 6 heures. Réservés à l'abonnement **Storage Intelligence** |
| **Export de facturation détaillé** vers BigQuery | Coût par bucket (colonne `resource.global_name`), avec les étiquettes du bucket dans `labels` | Tous les buckets du compte de facturation ; voir [Facturation et budgets](#facturation-et-budgets) |

- **Volume et croissance** : les métriques suffisent, et une alerte sur `storage/v2/total_bytes` détecte une rétention oubliée ; la répartition par type montre ce que coûtent les versions et la suppression réversible.
- **Contenu du lac** (buckets inactifs, fichiers temporaires ou en double, objets publics, données hors de la région attendue) : jeux de données Storage Insights à l'échelle d'une organisation, rapport d'inventaire pour un bucket isolé ou pour valider un transfert.
- **Coût par équipe ou par zone du lac** : poser des étiquettes (`equipe`, `couche`) sur chaque bucket dès sa création ; elles portent sur le bucket, jamais sur les objets, d'où un bucket par couche ou par domaine quand la dépense doit être ventilée ainsi.
- **Qui lit quoi** : journaux d'audit d'accès aux données (voir [Détection et conformité](#detection-et-conformite)). La **qualité** des données relève des analyses de [Knowledge Catalog](#knowledge-catalog).

## Commandes `gcloud storage`

```bash
# Bucket régional, Standard, accès uniforme
gcloud storage buckets create gs://BUCKET --project=PROJECT_ID \
  --location=REGION --default-storage-class=STANDARD --uniform-bucket-level-access

# Birégion configurable, puis réplication turbo
gcloud storage buckets create gs://BUCKET --location=EU \
  --placement=EUROPE-WEST1,EUROPE-WEST4
gcloud storage buckets update gs://BUCKET --rpo=ASYNC_TURBO

# Autoclass avec Archive comme classe terminale
gcloud storage buckets update gs://BUCKET --enable-autoclass \
  --autoclass-terminal-storage-class=ARCHIVE

# Règles de cycle de vie
gcloud storage buckets update gs://BUCKET --lifecycle-file=lifecycle.json

# Versionnement, suppression réversible portée à 30 jours
gcloud storage buckets update gs://BUCKET --versioning
gcloud storage buckets update gs://BUCKET --soft-delete-duration=30d

# Politique de conservation, puis verrouillage (irréversible)
gcloud storage buckets update gs://BUCKET --retention-period=365d
gcloud storage buckets update gs://BUCKET --lock-retention-period

# Vérifier la configuration
gcloud storage buckets describe gs://BUCKET \
  --format="default(autoclass,lifecycle_config,soft_delete_policy,retention_policy,rpo)"
```

## Questions qui départagent

- **Sait-on à l'avance quand les données refroidissent ?** Oui : règles de cycle de vie, sans frais de gestion. Non : Autoclass.
- **Les données seront-elles relues en masse ?** Un lac de données interrogé chaque jour par [BigQuery](#bigquery) ou Spark reste en Standard, dans la région du calcul. Les classes froides visent les sauvegardes et les archives.
- **Faut-il survivre à la perte d'une région ?** Birégion, avec réplication turbo si le RPO doit être garanti ; une région seule, sinon, plus une copie de sauvegarde ailleurs.
- **L'effacement doit-il être impossible, même pour un administrateur ?** Politique de conservation verrouillée. Pour une simple erreur de manipulation, la suppression réversible et le versionnement suffisent.
- **Pour déplacer de gros volumes vers ou entre buckets**, voir [Migrations et transferts](#migrations-transferts) ; pour organiser un lac de données au-dessus des buckets, [Lakehouse](#lakehouse-architecture).

## Alternatives en logiciel libre

- **Ceph** avec **RADOS Gateway** (LGPL 2.1 ou LGPL 3) : stockage objet compatible S3 avec classes de stockage associées à des pools, règles de cycle de vie qui déplacent ou expirent les objets, versionnement, Object Lock et réplication entre sites ; l'ensemble le plus complet, mais lourd à exploiter.
- **OpenStack Swift** (Apache 2.0) : politiques de stockage par conteneur (réplication ou codes d'effacement), expiration programmée des objets et versionnement ; la répartition multirégion est native.
- **SeaweedFS** (Apache 2.0) : stockage objet et fichier compatible S3, avec déplacement des volumes peu lus vers un niveau moins cher, y compris un stockage objet distant ; l'équivalent le plus proche d'une hiérarchie de classes.
- **Garage** (AGPL v3) : stockage objet compatible S3 réparti sur plusieurs sites, pensé pour des machines modestes ; il couvre la redondance géographique, sans classes de stockage ni versionnement.
- **Rclone** (MIT) : copie planifiée d'un bucket vers un autre stockage, pour une seconde copie indépendante comme la réplication inter-buckets.
