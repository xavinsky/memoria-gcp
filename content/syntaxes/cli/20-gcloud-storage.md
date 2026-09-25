---
title: "gcloud storage : buckets et objets"
subgroup: gcloud storage
type: syntax
---

`gcloud storage` est la CLI de Cloud Storage. `gsutil` [!DECONSEILLE] est un outil hérité, à ne pas utiliser : `gcloud storage` couvre les mêmes commandes et parallélise seul les transferts. Joker `*` : un niveau de dossier ; `**` : tous les niveaux.

### Buckets

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un bucket privé | `gcloud storage buckets create gs://BUCKET --project=PROJECT_ID --location=REGION --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention` | Accès par IAM seulement, jamais public ; nom unique au monde, emplacement définitif (`US` si `--location` est omis) |
| Bucket de travail sans suppression réversible | `gcloud storage buckets create gs://BUCKET --location=REGION --soft-delete-duration=0` | Objets supprimés aussitôt effacés ; 7 jours de rétention par défaut sinon |
| Lister les buckets | `gcloud storage buckets list --format="table(name,location,default_storage_class)"` | Buckets du projet courant ; `gcloud storage ls` pour les seules URL |
| Lire la configuration | `gcloud storage buckets describe gs://BUCKET --format="default(location,soft_delete_policy,versioning_enabled,uniform_bucket_level_access,public_access_prevention)"` | Seuls les champs demandés ; sans `--format`, toute la ressource |
| Taille d'un bucket | `gcloud storage du -s --readable-sizes gs://BUCKET` | Total lisible ; `-a` compte aussi les versions non courantes |
| Ajouter des libellés | `gcloud storage buckets update gs://BUCKET --update-labels=equipe=data,env=prod` | `--remove-labels=env` en retire |
| Changer la classe par défaut | `gcloud storage buckets update gs://BUCKET --default-storage-class=NEARLINE` | Vaut pour les objets écrits ensuite ; les objets existants gardent leur classe |
| Supprimer un bucket et tout son contenu | `gcloud storage rm --recursive gs://BUCKET` | Objets, versions, puis bucket ; `gcloud storage buckets delete` ne supprime qu'un bucket vide |

### Copier, déplacer, synchroniser

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Envoyer un fichier | `gcloud storage cp ./f.csv gs://BUCKET/rep/` | Objet `rep/f.csv` ; somme de contrôle vérifiée |
| Envoyer un dossier | `gcloud storage cp --recursive ./dossier gs://BUCKET/rep/` | Arborescence recopiée sous `rep/dossier/` |
| Télécharger par motif | `gcloud storage cp 'gs://BUCKET/rep/*.csv' ./local/` | Apostrophes pour que le shell ne développe pas le joker |
| Ne pas écraser | `gcloud storage cp -n ./f.csv gs://BUCKET/rep/` | Objets déjà présents ignorés et signalés |
| Fixer classe et métadonnées à l'envoi | `gcloud storage cp --storage-class=NEARLINE --content-type=application/json --cache-control="no-cache" ./f.json gs://BUCKET/rep/` | Évite une réécriture après coup |
| Écrire depuis un flux | `mysqldump BASE \| gzip \| gcloud storage cp - gs://BUCKET/dumps/base.sql.gz` | `-` lit l'entrée standard, sans fichier local intermédiaire |
| Copier entre buckets | `gcloud storage cp --recursive gs://SRC/rep gs://DEST/` | Copie côté serveur, sans passer par la machine locale |
| Renommer un préfixe | `gcloud storage mv gs://BUCKET/ancien gs://BUCKET/nouveau` | Copie puis suppression de chaque objet, facturées comme telles : pas de renommage atomique |
| Synchroniser, à blanc | `gcloud storage rsync --recursive --dry-run ./site gs://BUCKET/site` | Liste des copies qui seraient faites, sans rien écrire |
| Synchroniser en miroir | `gcloud storage rsync --recursive --delete-unmatched-destination-objects ./site gs://BUCKET/site` | Destination identique à la source : les objets absents de la source sont **supprimés** |
| Exclure des fichiers | `gcloud storage rsync --recursive --exclude='.*\.tmp$' ./data gs://BUCKET/data` | Expression régulière Python, relative à la racine synchronisée |
| Accélérer les gros envois | `gcloud config set storage/parallel_composite_upload_enabled True` | Fichiers de plus de 150 Mio découpés, envoyés en parallèle puis recomposés ; objet sans MD5, contrôlé par CRC32C |
| Lire un objet | `gcloud storage cat gs://BUCKET/rep/f.csv \| head` | Contenu sur la sortie standard ; `-r 0-999` pour une plage d'octets |
| Supprimer par motif | `gcloud storage rm 'gs://BUCKET/rep/**'` | Tous les objets sous `rep/`, à tous les niveaux |

> [!WARNING]
> Un envoi composite parallèle laisse des objets temporaires qu'un bucket soumis à une politique de conservation ou à une retenue par défaut ne peut pas effacer. La vérification de compatibilité, active par défaut, l'évite en ne l'appliquant qu'aux objets `STANDARD`.

### Objets et métadonnées

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lister avec tailles et dates | `gcloud storage ls -l gs://BUCKET/rep/` | Taille, date de création, URL ; `--recursive` pour descendre dans les sous-dossiers |
| Lister toutes les versions | `gcloud storage ls -a gs://BUCKET/rep/f.csv` | URL suffixées de leur génération : `gs://BUCKET/rep/f.csv#1767225600123456` |
| Détail d'un objet | `gcloud storage objects describe gs://BUCKET/rep/f.csv --format="default(size,storage_class,content_type,update_time,custom_fields)"` | Taille, classe, type, date, métadonnées personnalisées |
| Ajouter des métadonnées | `gcloud storage objects update gs://BUCKET/rep/f.csv --update-custom-metadata=source=crm` | `--custom-metadata=...` remplace l'ensemble ; `--remove-custom-metadata=source` retire une clé |
| Changer la classe d'objets existants | `gcloud storage objects update 'gs://BUCKET/**/*.jpg' --storage-class=COLDLINE` | Réécriture des objets ; une règle de cycle de vie fait la même chose en continu |
| Restaurer un objet supprimé | `gcloud storage ls --soft-deleted gs://BUCKET/rep/` puis `gcloud storage restore gs://BUCKET/rep/f.csv` | Dernière version supprimée de façon réversible remise en ligne ; `#GENERATION` pour une version précise |
| Restaurer en masse | `gcloud storage restore 'gs://BUCKET/**' --async --deleted-after-time="2026-01-31T00:00:00Z"` | Opération longue qui restaure tout ce qui a été supprimé depuis cette date |

### Accès

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Donner la lecture à un compte de service | `gcloud storage buckets add-iam-policy-binding gs://BUCKET --member=serviceAccount:SA@PROJECT_ID.iam.gserviceaccount.com --role=roles/storage.objectViewer` | Lecture de tous les objets du bucket ; `roles/storage.objectCreator` pour l'écriture seule, `roles/storage.objectUser` pour lire, écrire et supprimer |
| Retirer un rôle | `gcloud storage buckets remove-iam-policy-binding gs://BUCKET --member=user:EMAIL --role=roles/storage.objectViewer` | Liaison supprimée |
| Voir la stratégie IAM | `gcloud storage buckets get-iam-policy gs://BUCKET` | Liaisons rôle → membres du bucket |
| URL signée de téléchargement | `gcloud storage sign-url gs://BUCKET/rep/f.pdf --duration=10m --impersonate-service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Lien valable 10 minutes, sans compte Google ; 7 jours au plus. Demande `roles/iam.serviceAccountTokenCreator` sur le compte de service, pas de clé |
| URL signée d'envoi | `gcloud storage sign-url gs://BUCKET/depot/f.csv --http-verb=PUT --duration=1h --headers=content-type=text/csv --impersonate-service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Le client envoie par `PUT` avec exactement cet en-tête `Content-Type` |
| Rendre un bucket public en lecture | `gcloud storage buckets add-iam-policy-binding gs://BUCKET --member=allUsers --role=roles/storage.objectViewer` | Refusé tant que la prévention de l'accès public est active ; à réserver à un site statique ou à des données ouvertes |

### Protection et cycle de vie

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Activer le versionnement | `gcloud storage buckets update gs://BUCKET --versioning` | Chaque remplacement ou suppression garde l'ancienne version ; `--no-versioning` pour arrêter |
| Régler la suppression réversible | `gcloud storage buckets update gs://BUCKET --soft-delete-duration=30d` | Rétention de 7 à 90 jours ; `0` la désactive |
| Appliquer des règles de cycle de vie | `gcloud storage buckets update gs://BUCKET --lifecycle-file=cycle.json` | Règles du fichier (voir ci-dessous) ; `--clear-lifecycle` les retire |
| Relire les règles | `gcloud storage buckets describe gs://BUCKET --format="default(lifecycle_config)"` | Règles actives |
| Politique de conservation | `gcloud storage buckets update gs://BUCKET --retention-period=365d` | Aucun objet supprimable ni remplaçable avant un an ; `--clear-retention-period` tant qu'elle n'est pas verrouillée |
| Verrouiller la politique | `gcloud storage buckets update gs://BUCKET --lock-retention-period` | **Irréversible** : la durée ne peut plus qu'augmenter, le bucket ne se supprime qu'une fois tous ses objets arrivés au terme de leur conservation |
| Retenue temporaire sur un objet | `gcloud storage objects update gs://BUCKET/rep/f.pdf --temporary-hold` | Objet non supprimable jusqu'à `--no-temporary-hold` |
| Retenue sur événement | `gcloud storage objects update gs://BUCKET/rep/f.pdf --event-based-hold` | À la levée (`--no-event-based-hold`), la durée de conservation du bucket repart de zéro |
| Conservation propre à un objet | `gcloud storage objects update gs://BUCKET/rep/f.pdf --retain-until=2031-01-01T00:00:00Z --retention-mode=Unlocked` | Demande un bucket créé avec `--enable-per-object-retention` ; `Locked` rend la date impossible à avancer |

Fichier `cycle.json` : passage en Coldline à 90 jours, suppression à 3 ans, deux versions non courantes au plus.

```json
{
  "rule": [
    {"action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
     "condition": {"age": 90, "matchesStorageClass": ["STANDARD"]}},
    {"action": {"type": "Delete"}, "condition": {"age": 1095}},
    {"action": {"type": "Delete"}, "condition": {"numNewerVersions": 2, "isLive": false}}
  ]
}
```

### Notifications Pub/Sub

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Notifier les nouveaux objets | `gcloud storage buckets notifications create gs://BUCKET --topic=TOPIC --event-types=OBJECT_FINALIZE --object-prefix=entrant/` | Un message par objet écrit sous `entrant/` ; sujet créé et droit de publication donné à l'agent de service si besoin |
| Sujet déjà configuré | `gcloud storage buckets notifications create gs://BUCKET --topic=projects/PROJECT_ID/topics/TOPIC --skip-topic-setup` | Ni création de sujet ni modification IAM : l'agent de service doit déjà avoir `roles/pubsub.publisher` |
| Lister les notifications | `gcloud storage buckets notifications list gs://BUCKET` | ID, sujet, filtres de chaque configuration |
| Supprimer une notification | `gcloud storage buckets notifications delete projects/_/buckets/BUCKET/notificationConfigs/NOTIFICATION_ID` | Configuration supprimée, sujet conservé |

Contexte : [Cloud Storage](#cloud-storage), [classes et cycle de vie](#cloud-storage-classes), [Pub/Sub](#pubsub), [datasets, tables et chargement](#bq-tables-chargement), [configuration de gcloud](#gcloud-config).
