---
title: "GoogleSQL : requêtes"
subgroup: Requêtes
type: syntax
---

GoogleSQL est le dialecte SQL de BigQuery. Les noms de table s'écrivent `` `PROJECT_ID.DATASET.TABLE` `` entre accents graves.

### Sélection

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Toutes les colonnes sauf certaines | `SELECT * EXCEPT (col_a, col_b) FROM DATASET.TABLE` | Évite de lister cinquante colonnes pour en retirer deux |
| Toutes les colonnes, une transformée | `SELECT * REPLACE (UPPER(pays) AS pays) FROM DATASET.TABLE` | Même ordre de colonnes, `pays` en majuscules |
| Filtrer sur une fonction de fenêtre | `SELECT ... FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY maj DESC) = 1` | Filtre appliqué après le calcul des fenêtres, sans sous-requête ; cf. [fonctions de fenêtre](#googlesql-fenetres) |
| Découper une requête en étapes | `WITH a AS (SELECT ...), b AS (SELECT ... FROM a) SELECT * FROM b` | CTE (*common table expression*) : sous-requête nommée, visible dans la suite de la requête |
| Parcourir une hiérarchie | `WITH RECURSIVE h AS (SELECT id, parent, 0 AS niv FROM t WHERE parent IS NULL UNION ALL SELECT t.id, t.parent, h.niv + 1 FROM t JOIN h ON t.parent = h.id) SELECT * FROM h` | Terme de base, puis terme récursif en `UNION ALL` ; échec au-delà de 500 itérations |
| Échantillonner une grosse table | `SELECT * FROM DATASET.TABLE TABLESAMPLE SYSTEM (1 PERCENT)` | Environ 1 % des blocs de données lus et facturés ; une table de moins d'environ 1 Go tient souvent en un bloc et est lue entière ; résultat différent à chaque exécution, jamais mis en cache |

### Agrégation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Grouper sans répéter les colonnes | `SELECT pays, ville, SUM(ca) FROM t GROUP BY ALL` | Clés de groupement déduites des colonnes non agrégées du `SELECT` |
| Sous-totaux hiérarchiques | `SELECT pays, ville, SUM(ca) FROM t GROUP BY ROLLUP (pays, ville)` | Lignes (pays, ville), (pays) et total général ; `NULL` dans les colonnes agrégées |
| Combinaisons choisies de regroupements | `GROUP BY GROUPING SETS ((pays, canal), (pays), ())` | Une série de lignes par ensemble ; `()` donne le total ; `CUBE (a, b)` produit toutes les combinaisons |
| Distinguer un `NULL` de sous-total | `SELECT GROUPING(ville) AS est_sous_total, ...` | `1` si la ligne agrège toutes les villes, `0` sinon |
| Compter sous condition | `COUNTIF(statut = 'KO')` | Nombre de lignes où la condition est vraie |
| Somme conditionnelle | `SUM(IF(canal = 'web', ca, 0))` | Plusieurs indicateurs filtrés en un seul passage |
| Tous / au moins un | `LOGICAL_AND(paye)`, `LOGICAL_OR(en_retard)` | Booléen par groupe |
| Valeur associée au max | `MAX_BY(produit, ca)` | Produit du meilleur chiffre d'affaires ; `MIN_BY` pour le min |
| N'importe quelle valeur du groupe | `ANY_VALUE(libelle)` | Évite de grouper sur une colonne fonctionnellement dépendante |
| Distincts approchés | `APPROX_COUNT_DISTINCT(user_id)` | Estimation HyperLogLog++, bien moins coûteuse que `COUNT(DISTINCT ...)` sur des milliards de lignes |
| Quantiles approchés | `APPROX_QUANTILES(latence, 100)[OFFSET(95)]` | 95e centile approché |
| Valeurs les plus fréquentes | `APPROX_TOP_COUNT(page, 10)` | Tableau de STRUCT `{value, count}` |
| Lignes en colonnes | `SELECT * FROM t PIVOT (SUM(ca) FOR trimestre IN ('T1', 'T2', 'T3', 'T4'))` | Une colonne par valeur listée ; les colonnes non citées servent de clés |
| Colonnes en lignes | `SELECT * FROM t UNPIVOT (ca FOR trimestre IN (T1, T2, T3, T4))` | Une ligne par (clé, trimestre) ; lignes `NULL` écartées sauf `INCLUDE NULLS` |

### Jointures

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Jointure sur colonnes homonymes | `FROM commandes JOIN clients USING (client_id)` | Une seule colonne `client_id` en sortie |
| Garder les lignes sans correspondance | `FROM a LEFT JOIN b ON a.id = b.id` | Colonnes de `b` à `NULL` quand rien ne correspond |
| Semi-jointure | `SELECT * FROM a WHERE EXISTS (SELECT 1 FROM b WHERE b.id = a.id)` | Lignes de `a` ayant au moins un `b`, sans doublon |
| Anti-jointure | `SELECT * FROM a WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.id = a.id)` | Lignes de `a` sans `b` ; plus sûr que `NOT IN` quand `b.id` contient des `NULL` |

### NULL et erreurs

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Première valeur non nulle | `COALESCE(tel_mobile, tel_fixe, 'inconnu')` | Évaluée de gauche à droite |
| Remplacer un `NULL` | `IFNULL(remise, 0)` | Équivaut à `COALESCE(remise, 0)` |
| Transformer une valeur en `NULL` | `NULLIF(quantite, 0)` | `NULL` si `quantite = 0` : évite la division par zéro |
| Diviser sans erreur | `SAFE_DIVIDE(ca, nb)` | `NULL` si `nb = 0` |
| Convertir sans erreur | `SAFE_CAST(code AS INT64)` | `NULL` au lieu d'une erreur si la chaîne n'est pas un entier |
| Rendre une fonction tolérante | `SAFE.PARSE_DATE('%d/%m/%Y', d)` | Préfixe `SAFE.` : `NULL` au lieu d'une erreur due à la valeur des arguments |

### Dates et heures

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Tronquer au mois | `DATE_TRUNC(d, MONTH)` | Premier jour du mois ; `WEEK(MONDAY)`, `QUARTER`, `YEAR` aussi |
| Écart entre deux dates | `DATE_DIFF(fin, debut, DAY)` | Nombre de frontières d'unité franchies (`fin - debut`) |
| Ajouter une durée | `DATE_ADD(d, INTERVAL 7 DAY)`, `TIMESTAMP_SUB(ts, INTERVAL 1 HOUR)` | Date ou horodatage décalé |
| Extraire un élément | `EXTRACT(DAYOFWEEK FROM d)` | 1 = dimanche … 7 = samedi |
| Lire une date texte | `PARSE_DATE('%d/%m/%Y', '31/12/2025')` | `DATE '2025-12-31'` ; `PARSE_TIMESTAMP` pour un horodatage |
| Formater un horodatage | `FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', ts, 'Europe/Paris')` | Texte à l'heure de Paris ; sans fuseau, UTC |
| Heure locale d'un horodatage | `DATETIME(ts, 'Europe/Paris')` | `DATETIME` sans fuseau, à l'heure locale |
| Horodatage depuis une heure locale | `TIMESTAMP(dt, 'Europe/Paris')` | Instant absolu, stocké en UTC |
| Jour civil local | `DATE(ts, 'Europe/Paris')` | Date du jour à Paris, qui peut différer de la date UTC |
| Tronquer dans un fuseau | `TIMESTAMP_TRUNC(ts, DAY, 'Europe/Paris')` | Minuit heure de Paris |
| Calendrier continu | `SELECT jour FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2025-12-31', INTERVAL 1 DAY)) AS jour` | Une ligne par jour, bornes incluses ; à joindre en `LEFT JOIN` pour faire apparaître les jours sans données |

> [!WARNING]
> `TIMESTAMP` est un instant absolu (stocké en UTC), `DATETIME` une heure murale sans fuseau. Regrouper des `TIMESTAMP` par jour sans préciser `'Europe/Paris'` coupe les journées à minuit UTC.

### Chaînes

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Tester une expression régulière | `REGEXP_CONTAINS(email, r'@exemple\.fr$')` | Booléen ; préfixe `r` pour une chaîne brute |
| Extraire un groupe | `REGEXP_EXTRACT(url, r'utm_source=([^&]+)')` | Premier groupe capturant, `NULL` si absent ; `REGEXP_EXTRACT_ALL` rend un tableau |
| Remplacer par motif | `REGEXP_REPLACE(tel, r'[^0-9]', '')` | Chiffres seuls ; `\\1` dans le remplacement pour un groupe |
| Découper | `SPLIT(tags, ',')` | `ARRAY<STRING>` ; `SPLIT(...)[SAFE_OFFSET(1)]` pour un élément |
| Concaténer un groupe | `STRING_AGG(nom, ', ' ORDER BY nom)` | Une chaîne par groupe, dans l'ordre donné |
| Recherche insensible à la casse | `CONTAINS_SUBSTR(description, 'bigquery')` | Recherche normalisée, sans regex |

### Tables génériques et paramètres

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Interroger une famille de tables | ``SELECT * FROM `PROJECT_ID.DATASET.events_*` WHERE _TABLE_SUFFIX BETWEEN '20250101' AND '20250131'`` | Seules les tables dont le suffixe correspond sont lues ; filtre constant obligatoire pour limiter le coût |
| Paramètre nommé | `WHERE pays = @pays AND jour >= @debut` | Valeurs passées par le client, la console ou `bq query --parameter=pays::FR --parameter=debut:DATE:2025-01-01` |
| Paramètre tableau | `WHERE id IN UNNEST(@ids)` | Liste de valeurs en un seul paramètre (pas depuis la console, qui n'accepte que les types simples) |

> [!WARNING]
> Un paramètre remplace une valeur, jamais un identifiant : pas de nom de table ou de colonne en `@param`. Une requête utilise soit des paramètres nommés `@x`, soit des paramètres positionnels `?`, pas les deux.

### Syntaxe pipe

Une requête peut commencer par `FROM` et enchaîner des opérateurs `|>`, chacun appliqué au résultat du précédent. Elle se mélange librement avec la syntaxe classique (vues, sous-requêtes, fonctions de table).

```sql
FROM `PROJECT_ID.DATASET.ventes`
|> WHERE jour >= '2025-01-01'
|> EXTEND prix * quantite AS ca
|> AGGREGATE SUM(ca) AS ca_total, COUNT(*) AS nb
   GROUP BY pays
|> ORDER BY ca_total DESC
|> LIMIT 10
```

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Ajouter une colonne calculée | `\|> EXTEND prix * quantite AS ca` | Colonnes existantes plus `ca` |
| Agréger | `\|> AGGREGATE SUM(ca) AS total GROUP BY pays` | Clés puis agrégats ; pas de `GROUP BY` isolé |
| Agréger et trier d'un coup | `\|> AGGREGATE SUM(ca) AS total GROUP AND ORDER BY pays` | Résultat trié par `pays` |
| Modifier, retirer, renommer | `\|> SET ca = ROUND(ca, 2)`, `\|> DROP col_tmp`, `\|> RENAME ca AS chiffre` | Les autres colonnes sont conservées |
| Filtrer après agrégation | `\|> AGGREGATE ... GROUP BY pays \|> WHERE total > 1000` | Remplace `HAVING` |
| Joindre | `\|> JOIN DATASET.clients USING (client_id)` | Jointure de la table courante avec une autre |

### Maîtriser le coût

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lire moins d'octets | `SELECT col_a, col_b FROM ...` plutôt que `SELECT *` | Stockage en colonnes : seules les colonnes citées sont facturées ; `LIMIT` ne réduit pas les octets lus |
| Élaguer les partitions | `WHERE jour BETWEEN '2025-01-01' AND '2025-01-31'` sur la colonne de partitionnement | Seules les partitions concernées sont lues ; le filtre doit porter directement sur la colonne, avec des constantes |
| Filtrer sur l'ingestion | `WHERE _PARTITIONTIME >= TIMESTAMP('2025-01-01')` | Table partitionnée par date d'ingestion |
| Estimer avant d'exécuter | `bq query --dry_run --use_legacy_sql=false 'SELECT ...'` | Octets qui seraient lus, sans rien facturer |

> [!TIP]
> Le validateur de l'éditeur BigQuery Studio affiche aussi le volume estimé avant exécution. Un filtre sur une colonne de *clustering* réduit les octets lus, mais l'estimation préalable n'en tient pas compte.

Contexte : [BigQuery](#bigquery), [Organiser BigQuery](#organiser-bigquery), [bq : requêtes et jobs](#bq-requetes-jobs), [fonctions de fenêtre](#googlesql-fenetres), [ARRAY, STRUCT et JSON](#googlesql-tableaux-struct-json).
