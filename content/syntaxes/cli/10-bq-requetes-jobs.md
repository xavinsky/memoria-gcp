---
title: "bq : requêtes et jobs"
subgroup: bq
type: syntax
---

`bq` est la CLI de BigQuery, livrée avec le SDK Google Cloud. Les options globales (`--location`, `--format`, `--project_id`) se placent avant ou après la commande ; `bq help COMMANDE` liste les options d'une commande.

### Lancer une requête

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Requête en GoogleSQL | `bq query --use_legacy_sql=false 'SELECT ... FROM DATASET.TABLE'` | Sans `--use_legacy_sql=false` (ni `.bigqueryrc`, ni réglage de projet), `bq` interprète la requête en SQL historique (*legacy SQL*) |
| Requête lue dans un fichier | `bq query --use_legacy_sql=false < requete.sql` | Texte lu sur l'entrée standard : pas de problème de guillemets dans le shell |
| Estimer le volume lu sans exécuter | `bq query --use_legacy_sql=false --dry_run 'SELECT ...'` | « *running this query will process N bytes of data* » : gratuit, sans slot, base de l'estimation du coût à la demande. Renvoie 0 octet sur une table externe ou protégée par sécurité au niveau des lignes |
| Plafonner la facture d'une requête | `bq query --use_legacy_sql=false --maximum_bytes_billed=10000000000 'SELECT ...'` | Échec sans frais si la requête facturerait plus de 10 Go |
| Choisir la région d'exécution | `bq --location=REGION query --use_legacy_sql=false 'SELECT ...'` | Le job tourne là où sont les données ; une jointure entre régions échoue |
| Limiter les lignes affichées | `bq query --use_legacy_sql=false -n 1000 'SELECT ...'` | 100 lignes par défaut ; ne change rien au volume lu ni facturé |
| Sortie exploitable par un script | `bq query --use_legacy_sql=false --format=csv 'SELECT ...'` | Aussi `json`, `prettyjson`, `sparse`, `pretty` (tableau, par défaut) |
| Ignorer le cache de résultats | `bq query --use_legacy_sql=false --use_cache=false 'SELECT ...'` | Force l'exécution, pour mesurer une durée ou un coût réels |
| Priorité batch | `bq query --use_legacy_sql=false --batch 'SELECT ...'` | Job mis en file jusqu'à ce que des slots se libèrent ; ne réduit pas le prix à la demande |
| Étiqueter le job | `bq query --use_legacy_sql=false --label=equipe:finance 'SELECT ...'` | Libellé visible dans `INFORMATION_SCHEMA.JOBS` et l'export de facturation |
| Limiter la durée | `bq query --use_legacy_sql=false --job_timeout_ms=600000 'SELECT ...'` | BigQuery tente d'arrêter le job au bout de 10 minutes |

### Paramètres et destination

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Paramètre nommé | `bq query --use_legacy_sql=false --parameter=pays::FR --parameter=seuil:INT64:250 'SELECT ... WHERE pays = @pays AND n > @seuil'` | Forme `NOM:TYPE:VALEUR`, type `STRING` si omis ; valeur injectée sans concaténation de texte |
| Paramètre positionnel | `bq query --use_legacy_sql=false --parameter=::FR 'SELECT ... WHERE pays = ?'` | Nom vide : paramètres dans l'ordre des `?` |
| Paramètre tableau | `bq query --use_legacy_sql=false --parameter='etats:ARRAY<STRING>:["WA", "WI"]' 'SELECT ... WHERE etat IN UNNEST(@etats)'` | Tableau passé en JSON |
| Écrire le résultat dans une table | `bq query --use_legacy_sql=false --destination_table=DATASET.TABLE 'SELECT ...'` | Échec si la table existe déjà et n'est pas vide |
| Remplacer la table | `bq query --use_legacy_sql=false --destination_table=DATASET.TABLE --replace 'SELECT ...'` | Données et schéma écrasés ; `--replace_data` garde le schéma |
| Ajouter à la table | `bq query --use_legacy_sql=false --destination_table=DATASET.TABLE --append_table 'SELECT ...'` | Lignes ajoutées ; `--schema_update_option=ALLOW_FIELD_ADDITION` accepte de nouvelles colonnes |
| Réécrire une seule partition | `bq query --use_legacy_sql=false --destination_table='DATASET.TABLE$20260131' --replace 'SELECT ... WHERE jour = "2026-01-31"'` | Seule la partition du 31 janvier est remplacée ; apostrophes obligatoires à cause du `$` |
| Créer une table partitionnée et clusterisée | `bq query --use_legacy_sql=false --destination_table=DATASET.TABLE --time_partitioning_field=jour --clustering_fields=client_id 'SELECT ...'` | Équivalent de `CREATE TABLE ... PARTITION BY ... CLUSTER BY ... AS SELECT` |

> [!TIP]
> Un fichier `~/.bigqueryrc` fixe les options par défaut : les options globales en tête, sans en-tête, puis une section par commande. `--nouse_legacy_sql` n'y est pas accepté, il faut la forme `--use_legacy_sql=false`.
>
> ```
> --location=EU
> [query]
> --use_legacy_sql=false
> --maximum_bytes_billed=10000000000
> [mk]
> --use_legacy_sql=false
> ```

### Suivre les jobs

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lancer sans attendre | `bq --nosync query --use_legacy_sql=false 'SELECT ...'` | Rend la main aussitôt et affiche l'ID du job |
| Imposer l'ID du job | `bq --job_id=JOB_ID query --use_legacy_sql=false 'SELECT ...'` | ID réutilisable dans un script ; relancer avec le même ID échoue, ce qui évite un doublon |
| Lister mes jobs récents | `bq ls -j -n 20` | ID, type, état, date et durée |
| Jobs de tous les utilisateurs | `bq ls -j --all --filter='states:RUNNING,PENDING' PROJECT_ID` | Jobs en cours du projet ; demande la permission `bigquery.jobs.listAll` |
| Jobs d'une période | `bq ls -j --all --min_creation_time=1767225600000 PROJECT_ID` | Bornes en millisecondes depuis l'époque Unix : `date -d '2026-01-01' +%s000` |
| Détail d'un job | `bq show --format=prettyjson -j PROJECT_ID:REGION.JOB_ID` | Configuration, octets traités et facturés, `totalSlotMs`, erreurs |
| Lire le résultat d'un job terminé | `bq head -j JOB_ID -n 50` | Lignes de la table temporaire du job, conservée environ 24 heures |
| Attendre la fin d'un job | `bq wait --fail_on_error JOB_ID 600` | Rend la main au plus tard après 600 s ; code de sortie non nul si le job échoue |
| Annuler un job | `bq --location=REGION cancel JOB_ID` | Demande l'arrêt puis attend ; `bq --nosync cancel` rend la main aussitôt |

### Inspecter tables et coûts

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Aperçu d'une table sans la facturer | `bq head -n 20 DATASET.TABLE` | Lecture directe, gratuite, contrairement à `SELECT * ... LIMIT 20` |
| Métadonnées complètes d'une table | `bq show --format=prettyjson DATASET.TABLE` | `numRows`, `numBytes`, `timePartitioning`, `clustering`, `expirationTime`, libellés |
| Octets facturés par utilisateur | ``bq query --use_legacy_sql=false 'SELECT user_email, SUM(total_bytes_billed) / POW(1024, 4) AS tio FROM `region-REGION`.INFORMATION_SCHEMA.JOBS WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY) AND job_type = "QUERY" AND statement_type != "SCRIPT" GROUP BY user_email ORDER BY tio DESC'`` | Tio facturés sur 30 jours ; le filtre sur `creation_time` limite la lecture de la vue |
| Mes requêtes les plus lourdes | ``bq query --use_legacy_sql=false 'SELECT job_id, total_bytes_billed, total_slot_ms, query FROM `region-REGION`.INFORMATION_SCHEMA.JOBS_BY_USER WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) ORDER BY total_bytes_billed DESC LIMIT 10'`` | `JOBS_BY_USER` ne montre que ses propres jobs : la permission `bigquery.jobs.list` suffit, là où `JOBS` demande `bigquery.jobs.listAll` |
| Slots consommés en moyenne | ``bq query --use_legacy_sql=false 'SELECT SUM(total_slot_ms) / (1000 * 60 * 60 * 24 * 7) AS slots_moyens FROM `region-REGION`.INFORMATION_SCHEMA.JOBS WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) AND job_type = "QUERY" AND statement_type != "SCRIPT"'`` | Base pour dimensionner une réservation ; `SCRIPT` exclu pour ne pas compter deux fois ses requêtes filles |
| Volume stocké par table | ``bq query --use_legacy_sql=false 'SELECT table_schema, table_name, total_logical_bytes, long_term_logical_bytes, total_physical_bytes FROM `region-REGION`.INFORMATION_SCHEMA.TABLE_STORAGE ORDER BY total_logical_bytes DESC LIMIT 20'`` | Octets logiques et physiques, part en stockage à long terme |

### Requêtes planifiées

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Planifier une requête | `bq query --use_legacy_sql=false --destination_table=DATASET.TABLE --display_name='NOM' --schedule='every 24 hours' --replace=true 'SELECT ...'` | Configuration de transfert de type `scheduled_query` ; horaires en UTC, par exemple `every day 03:00` |
| Même chose via le service de transfert | `bq mk --transfer_config --data_source=scheduled_query --target_dataset=DATASET --display_name='NOM' --schedule='every 24 hours' --params='{"query":"SELECT ...","destination_table_name_template":"TABLE_{run_date}","write_disposition":"WRITE_TRUNCATE"}'` | Table de destination nommée par date d'exécution ; `--service_account_name=SA_EMAIL` pour ne pas dépendre d'un compte utilisateur |
| Lister les requêtes planifiées | `bq ls --transfer_config --transfer_location=REGION --filter='dataSourceIds:scheduled_query'` | Nom complet `projects/.../transferConfigs/CONFIG_ID` de chaque configuration |
| Rattraper une période | `bq mk --transfer_run --start_time=2026-01-01T00:00:00Z --end_time=2026-01-08T00:00:00Z projects/PROJECT_ID/locations/REGION/transferConfigs/CONFIG_ID` | Une exécution par date planifiée de l'intervalle (*backfill*) |
| Historique des exécutions | `bq ls --transfer_run --filter='states:FAILED' projects/PROJECT_ID/locations/REGION/transferConfigs/CONFIG_ID` | Exécutions en échec ; `bq ls --transfer_log RUN_NAME` pour leurs messages |
| Supprimer une requête planifiée | `bq rm --transfer_config projects/PROJECT_ID/locations/REGION/transferConfigs/CONFIG_ID` | Configuration et planification supprimées, tables conservées |

### Réservations de slots

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer une réservation | `bq mk --project_id=ADMIN_PROJECT_ID --location=REGION --reservation --edition=ENTERPRISE --slots=0 --autoscale_max_slots=200 RESERVATION` | Aucun slot de base, jusqu'à 200 slots en autoscaling facturés à l'usage |
| Affecter un projet | `bq mk --project_id=ADMIN_PROJECT_ID --location=REGION --reservation_assignment --reservation_id=ADMIN_PROJECT_ID:REGION.RESERVATION --job_type=QUERY --assignee_type=PROJECT --assignee_id=PROJECT_ID` | Les requêtes de `PROJECT_ID` passent en facturation à la capacité ; `FOLDER` ou `ORGANIZATION` pour un ensemble de projets |
| Redimensionner | `bq update --project_id=ADMIN_PROJECT_ID --location=REGION --slots=100 --autoscale_max_slots=300 --reservation RESERVATION` | Nouvelle base et nouveau plafond d'autoscaling |
| Lister réservations et affectations | `bq ls --reservation --project_id=ADMIN_PROJECT_ID --location=REGION` puis `bq ls --reservation_assignment --project_id=ADMIN_PROJECT_ID --location=REGION` | Slots de base, autoscaling, édition ; projets affectés |

> [!WARNING]
> Une réservation ne sert qu'aux projets qui lui sont affectés, et seulement dans sa région. Un projet sans affectation reste facturé à la demande, au volume lu.

Contexte : [BigQuery](#bigquery), [organiser les tables](#organiser-bigquery), [datasets, tables et chargement](#bq-tables-chargement), [requêtes GoogleSQL](#googlesql-requetes), [quotas et limites](#quotas-et-limites).
