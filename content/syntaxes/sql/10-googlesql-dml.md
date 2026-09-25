---
title: "GoogleSQL : DML et transactions"
subgroup: DML et DDL
type: syntax
---

Écrire dans une table [BigQuery](#bigquery) en SQL : insertion, mise à jour, fusion, puis les requêtes multi-instructions (*scripting*) et les transactions.

### Insérer, modifier, supprimer

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Insérer des lignes littérales | `INSERT INTO DATASET.TABLE (col1, col2) VALUES ('a', 1), ('b', 2)` | Lignes ajoutées ; les colonnes omises prennent leur valeur par défaut ou `NULL` |
| Insérer le résultat d'une requête | `INSERT INTO DATASET.TABLE (col1, col2) SELECT a, b FROM DATASET.SOURCE WHERE ...` | Chargement ensembliste, la forme la plus courante en ELT |
| Utiliser la valeur par défaut d'une colonne | `INSERT INTO DATASET.TABLE (id, statut) VALUES (1, DEFAULT)` | Valeur définie par `DEFAULT` dans le schéma, ou identifiant généré pour une colonne d'identité |
| Insérer dans une partition d'ingestion précise | `INSERT INTO DATASET.TABLE (_PARTITIONTIME, col1) SELECT TIMESTAMP('2026-05-01'), 1` | Ligne rangée dans la partition du 1er mai ; la liste des colonnes est obligatoire et l'horodatage doit tomber pile sur une borne |
| Mettre à jour des lignes | `UPDATE DATASET.TABLE SET qte = qte - 10, maj = CURRENT_TIMESTAMP() WHERE produit LIKE '%lait%'` | `WHERE` est obligatoire |
| Mettre à jour toute la table | `UPDATE DATASET.TABLE SET actif = FALSE WHERE TRUE` | Réécrit toute la table : facturé sur sa taille entière |
| Mettre à jour par jointure | `UPDATE DATASET.CIBLE c SET prix = s.prix FROM DATASET.SOURCE s WHERE c.id = s.id` | Le prédicat de jointure avec la cible va dans `WHERE` ; chaque ligne cible doit joindre **au plus une** ligne source, sinon erreur *UPDATE/MERGE must match at most one source row* |
| Modifier un champ de `STRUCT` | `UPDATE DATASET.TABLE SET adresse.ville = 'Lyon' WHERE id = 42` | Notation pointée sur le champ imbriqué |
| Supprimer des lignes | `DELETE FROM DATASET.TABLE WHERE statut = 'annule'` | `WHERE` est obligatoire ; `WHERE TRUE` vide la table mais relit tout |
| Supprimer selon une autre table | `DELETE FROM DATASET.TABLE t WHERE NOT EXISTS (SELECT 1 FROM DATASET.REF r WHERE r.id = t.id)` | Anti-jointure par sous-requête corrélée |
| Vider une table | `TRUNCATE TABLE DATASET.TABLE` | Opération de métadonnées, non facturée ; schéma, description et libellés conservés |
| Compter les lignes touchées (script) | `SELECT @@row_count` juste après l'instruction | Lignes insérées, modifiées ou supprimées par la dernière DML ; somme des trois pour un `MERGE` |

### MERGE : fusionner une source dans une cible

| Objectif | Syntaxe | Résultat |
|---|---|---|
| *Upsert* : mettre à jour ou insérer | `MERGE DATASET.CIBLE c USING DATASET.SOURCE s ON c.id = s.id WHEN MATCHED THEN UPDATE SET val = s.val WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val)` | Mise à jour et insertion appliquées atomiquement |
| Insérer toutes les colonnes de la source | `... WHEN NOT MATCHED THEN INSERT ROW` | Colonnes de la source dans leur ordre, sans ses pseudo-colonnes (`_PARTITIONTIME`) |
| Supprimer les lignes absentes de la source | `... WHEN NOT MATCHED BY SOURCE THEN DELETE` | Synchronisation complète : la cible reflète la source |
| Appliquer une suppression logique venue d'une CDC | `... WHEN MATCHED AND s.op = 'D' THEN DELETE WHEN MATCHED THEN UPDATE SET ...` | Seule la **première** clause `WHEN` vraie s'applique à une ligne : mettre les plus précises en tête |
| Dédoublonner la source avant fusion | `USING (SELECT * EXCEPT(rn) FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY maj DESC) rn FROM DATASET.SOURCE) WHERE rn = 1) s` | Évite l'erreur « au plus une ligne source par ligne cible » |
| Joindre sur des colonnes qui peuvent être nulles | `ON c.k = s.k OR (c.k IS NULL AND s.k IS NULL)` | `NULL = NULL` ne vaut pas vrai : sans cela, doublons à l'insertion |
| Remplacer tout le contenu d'une partition | `MERGE DATASET.CIBLE c USING DATASET.SOURCE s ON FALSE WHEN NOT MATCHED AND s.jour = 'AAAA-MM-JJ' THEN INSERT ROW WHEN NOT MATCHED BY SOURCE AND c.jour = 'AAAA-MM-JJ' THEN DELETE` | Prédicat constant faux : suppression et insertion atomiques, limitées à la partition filtrée |
| Dimension historisée de type 2 (SCD) : fermer la version courante et insérer la nouvelle | `MERGE DATASET.DIM d USING (SELECT s.id AS cle, s.* FROM DATASET.MAJ s UNION ALL SELECT NULL, s.* FROM DATASET.MAJ s JOIN DATASET.DIM d ON d.id = s.id AND d.is_current WHERE s.attr_hash != d.attr_hash) m ON d.id = m.cle AND d.is_current WHEN MATCHED AND d.attr_hash != m.attr_hash THEN UPDATE SET is_current = FALSE, valid_to = CURRENT_TIMESTAMP() WHEN NOT MATCHED THEN INSERT (id, attr, attr_hash, valid_from, valid_to, is_current) VALUES (m.id, m.attr, m.attr_hash, CURRENT_TIMESTAMP(), NULL, TRUE)` | Chaque ligne modifiée de `MAJ` passe deux fois : avec sa clé, elle ferme la version courante ; avec une clé `NULL`, qui ne correspond à rien, elle est insérée comme nouvelle version. Une clé absente de la dimension est insérée directement. `MAJ` doit être dédoublonnée par `id` |
| Détecter un changement sur plusieurs colonnes | `attr_hash = FARM_FINGERPRINT(TO_JSON_STRING(STRUCT(nom, adresse, categorie)))` | Empreinte `INT64` à comparer au lieu de chaque colonne ; `!=` sur une empreinte évite le piège des `NULL` colonne par colonne |
| Dimension de type 1 : écraser sans historique | `MERGE DATASET.DIM d USING DATASET.MAJ m ON d.id = m.id WHEN MATCHED AND d.attr_hash != m.attr_hash THEN UPDATE SET attr = m.attr, attr_hash = m.attr_hash WHEN NOT MATCHED THEN INSERT ROW` | *Upsert* limité aux lignes réellement modifiées ; choix entre types 1 et 2 : [Modéliser l'entrepôt BigQuery](#modeliser-entrepot) |

### Partitions et coût

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Supprimer des partitions entières sans rien lire | `DELETE FROM DATASET.TABLE WHERE _PARTITIONDATE IN ('2026-01-01', '2026-01-02')` | Partitions retirées sans octet traité ni slot ; le vérifier par un *dry run* à 0 octet |
| Supprimer dans une table partitionnée par colonne | `DELETE FROM DATASET.TABLE WHERE DATE(ts) = '2026-06-01' AND client_id = 21` | Le filtre sur la colonne de partition limite la lecture à la partition visée |
| Élaguer la cible d'un `MERGE` | Filtre sur la colonne de partition dans la sous-requête `USING`, dans chaque condition `WHEN ... AND` ou dans `ON` | Une clause `WHEN NOT MATCHED BY SOURCE` sans filtre force la lecture de toute la cible |
| Déplacer des lignes d'une partition à l'autre | `UPDATE DATASET.TABLE SET ts = '2026-06-01' WHERE DATE(ts) = '2026-05-01' AND id = 21` | Les lignes changent de partition avec leur valeur de partitionnement |
| Estimer le volume d'une DML | `bq query --use_legacy_sql=false --dry_run 'UPDATE ...'` | Octets estimés, sans exécution |
| Calcul du volume facturé (à la demande) | `INSERT` : octets lus par la requête ; `UPDATE`, `DELETE`, `MERGE` avec mise à jour ou suppression : octets lus **plus** taille des tables ou partitions modifiées | Une mise à jour d'une seule ligne réécrit toute sa partition : partitionner réduit la facture |

> [!WARNING]
> Au plus **2** DML modifiantes (`UPDATE`, `DELETE`, `MERGE`) s'exécutent en même temps sur une table ; **20** autres attendent en file, au-delà elles échouent. Deux instructions qui modifient la même partition entrent en conflit, et BigQuery réessaie jusqu'à trois fois. Les `INSERT` ne sont pas en conflit, mais au-delà de 1 500 par table et par jour leur concurrence tombe à 10, avec 100 en file. Plafond commun : 25 DML toutes les 10 secondes par table. Pour de nombreuses petites écritures, la *Storage Write API* (voir [Streaming](#streaming)) convient mieux que des `INSERT` répétés.

### Requêtes multi-instructions

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Déclarer une variable | `DECLARE jour DATE DEFAULT CURRENT_DATE();` | Sans `DEFAULT`, la variable vaut `NULL` ; toutes les `DECLARE` en tête du script ou d'un bloc `BEGIN` |
| Déclarer depuis une requête | `DECLARE nb INT64 DEFAULT (SELECT COUNT(*) FROM DATASET.TABLE);` | Initialisation par une sous-requête scalaire ; sans type explicite, celui de l'expression est retenu |
| Affecter une ou plusieurs variables | `SET x = 5;` ou `SET (a, b) = (SELECT AS STRUCT MIN(d), MAX(d) FROM DATASET.TABLE);` | Affectation multiple depuis une ligne |
| Condition | `IF nb = 0 THEN RETURN; ELSEIF nb > 1000 THEN ... ELSE ... END IF;` | `RETURN` arrête le script |
| Boucle simple | `LOOP SET i = i + 1; IF i >= 10 THEN LEAVE; END IF; END LOOP;` | `LEAVE` (ou `BREAK`) sort, `CONTINUE` (ou `ITERATE`) passe au tour suivant ; aussi `WHILE ... DO ... END WHILE` et `REPEAT ... UNTIL ... END REPEAT` |
| Boucler sur les lignes d'une requête | `FOR t IN (SELECT table_name FROM DATASET.INFORMATION_SCHEMA.TABLES) DO ... t.table_name ... END FOR;` | La requête est évaluée une fois ; chaque ligne est un `STRUCT` |
| SQL dynamique paramétré | `EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM DATASET.TABLE WHERE jour = @j' INTO nb USING jour AS j;` | Paramètres `?` positionnels ou `@nom` nommés ; `INTO` récupère le résultat |
| Nom de table dynamique | `EXECUTE IMMEDIATE FORMAT('TRUNCATE TABLE DATASET.%s', nom_table);` | Les identifiants ne se passent pas en paramètre : construire la chaîne, avec une valeur maîtrisée |
| Intercepter une erreur | `BEGIN ... EXCEPTION WHEN ERROR THEN SELECT @@error.message, @@error.statement_text; END;` | Le script continue après le bloc |
| Lever une erreur | `RAISE USING MESSAGE = FORMAT('Aucune ligne pour %t', jour);` | Échec du job avec ce message |
| Créer une table temporaire | `CREATE TEMP TABLE staging AS SELECT ... ;` | Visible dans le script seulement, sans dataset ni projet dans le nom ; conservée 24 h au plus, stockage facturé |
| Appeler une procédure stockée | `CALL DATASET.PROCEDURE(arg1, var_out);` | Une variable passée en argument `OUT` ou `INOUT` reçoit la valeur |
| Rafraîchir une vue matérialisée | `CALL BQ.REFRESH_MATERIALIZED_VIEW('PROJECT_ID.DATASET.VUE_MAT');` | Rafraîchissement immédiat, hors planification |
| Suivre le coût d'un script | `SELECT @@script.bytes_processed, @@script.num_child_jobs;` | Chaque instruction est un job enfant ; le volume n'est connu qu'à l'exécution |

### Transactions

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Transaction multi-instructions | `BEGIN TRANSACTION; DELETE ...; INSERT ...; COMMIT TRANSACTION;` | Tout ou rien, sur une ou plusieurs tables, même dans des datasets ou projets différents |
| Annuler | `ROLLBACK TRANSACTION;` | Changements abandonnés ; un script qui se termine sans `COMMIT` est annulé automatiquement |
| Annuler sur erreur | `BEGIN BEGIN TRANSACTION; ...; COMMIT TRANSACTION; EXCEPTION WHEN ERROR THEN ROLLBACK TRANSACTION; RAISE; END;` | Libère les verrous tout de suite et remonte l'erreur |
| Retrouver les transactions validées | `` SELECT transaction_id, parent_job_id, query FROM `region-REGION`.INFORMATION_SCHEMA.JOBS_BY_PROJECT WHERE statement_type = 'COMMIT_TRANSACTION' `` | Chaque instruction d'une transaction porte le même `transaction_id` |

```sql
-- Remplacer la partition du jour depuis une table de préparation, atomiquement
DECLARE v_jour DATE DEFAULT (SELECT MAX(jour) FROM DATASET.ventes_staging);

BEGIN
  BEGIN TRANSACTION;
  DELETE FROM DATASET.ventes WHERE jour = v_jour;   -- partition entière : 0 octet lu
  INSERT INTO DATASET.ventes
    SELECT * FROM DATASET.ventes_staging WHERE jour = v_jour;
  COMMIT TRANSACTION;
EXCEPTION WHEN ERROR THEN
  ROLLBACK TRANSACTION;
  RAISE;   -- relance l'erreur d'origine
END;
```

> [!TIP]
> Préfixer les variables (`v_jour`) : quand une variable et une colonne portent le même nom, la colonne l'emporte, et `WHERE jour = jour` est toujours vrai.

- Une transaction accepte `SELECT`, les DML et `TRUNCATE`, et les DDL sur des objets temporaires (`CREATE TEMP TABLE`, `CREATE TEMP FUNCTION`) ; pas de `CREATE` ni de `DROP` sur une table permanente.
- Isolation par instantané : les lectures voient l'état du début de la transaction, et `CURRENT_TIMESTAMP()` renvoie l'heure de ce début.
- Limites : 100 tables modifiées et 100 000 modifications de partitions par transaction ; 6 h par instruction et 24 h au total pour un script ; 1 000 scripts simultanés par projet.
- Une transaction qui modifie ou supprime des lignes bloque les autres DML modifiantes sur la même table (mises en file) et fait annuler les transactions concurrentes ; lectures, `INSERT`, chargements en ajout et streaming continuent.

Contexte : [BigQuery : organiser les tables](#organiser-bigquery), [Modéliser l'entrepôt BigQuery](#modeliser-entrepot), [BigQuery : DDL](#bigquery-ddl), [Batch : ETL ou ELT](#batch-etl-elt), [CDC](#cdc), [BigQuery](#bigquery).
