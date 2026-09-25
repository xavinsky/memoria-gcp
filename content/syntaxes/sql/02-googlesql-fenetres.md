---
title: "GoogleSQL : fonctions de fenêtre"
subgroup: Requêtes
type: syntax
---

Une fonction de fenêtre calcule une valeur par ligne à partir d'un ensemble de lignes voisines, sans regrouper le résultat. Forme générale : `FONCTION(...) OVER (PARTITION BY ... ORDER BY ... cadre)`.

### Numérotation et rang

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Numéroter les lignes d'un groupe | `ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date_cmd)` | 1, 2, 3… sans ex æquo ; ordre arbitraire entre lignes égales |
| Rang avec trous | `RANK() OVER (ORDER BY score DESC)` | 1, 2, 2, 4 |
| Rang sans trous | `DENSE_RANK() OVER (ORDER BY score DESC)` | 1, 2, 2, 3 |
| Répartir en quantiles | `NTILE(4) OVER (ORDER BY ca)` | Quartile 1 à 4 de chaque ligne |
| Rang relatif | `PERCENT_RANK() OVER (ORDER BY ca)`, `CUME_DIST() OVER (ORDER BY ca)` | Valeur entre 0 et 1 |
| Top N par groupe | `SELECT * FROM t QUALIFY RANK() OVER (PARTITION BY categorie ORDER BY ventes DESC) <= 3` | Trois meilleurs par catégorie, ex æquo compris |

### Navigation

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Valeur de la ligne précédente | `LAG(ca) OVER (PARTITION BY magasin ORDER BY mois)` | `NULL` sur la première ligne du groupe |
| Décalage et valeur par défaut | `LAG(ca, 12, 0) OVER (PARTITION BY magasin ORDER BY mois)` | Valeur douze lignes plus tôt, `0` s'il n'y en a pas |
| Valeur de la ligne suivante | `LEAD(ts) OVER (PARTITION BY user_id ORDER BY ts)` | Horodatage de l'événement suivant |
| Évolution d'une période à l'autre | `ca - LAG(ca) OVER (PARTITION BY magasin ORDER BY mois)` | Variation mensuelle |
| Première valeur du groupe | `FIRST_VALUE(page) OVER (PARTITION BY session_id ORDER BY ts)` | Page d'entrée de la session |
| Dernière valeur du groupe | `LAST_VALUE(page) OVER (PARTITION BY session_id ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` | Page de sortie ; le cadre explicite est indispensable |
| N-ième valeur | `NTH_VALUE(produit, 2) OVER (PARTITION BY client_id ORDER BY date_cmd ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` | Deuxième produit acheté |
| Ignorer les `NULL` | `LAST_VALUE(prix IGNORE NULLS) OVER (ORDER BY jour)` | Dernier prix connu, propagé sur les jours sans prix |
| Médiane par groupe | `PERCENTILE_CONT(duree, 0.5) OVER (PARTITION BY service)` | Médiane interpolée, répétée sur chaque ligne ; `PERCENTILE_DISC` rend une valeur existante |
| Médiane seule | `SELECT DISTINCT service, PERCENTILE_CONT(duree, 0.5) OVER (PARTITION BY service) FROM t` | Une ligne par service ; `APPROX_QUANTILES(duree, 2)[OFFSET(1)]` en agrégat approché |

> [!WARNING]
> Avec un `ORDER BY` et sans cadre, le cadre par défaut va du début du groupe à la ligne courante (`RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`). `LAST_VALUE` rend alors la valeur de la ligne courante, pas celle de la fin du groupe.

### Cadres et agrégats glissants

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Total du groupe sur chaque ligne | `SUM(ca) OVER (PARTITION BY pays)` | Même total répété ; `ca / SUM(ca) OVER (...)` donne la part de chaque ligne |
| Cumul | `SUM(ca) OVER (PARTITION BY pays ORDER BY jour)` | Total depuis le début jusqu'à la ligne courante, lignes de même `jour` comprises |
| Cumul ligne à ligne | `SUM(ca) OVER (ORDER BY jour ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` | Cumul strict, même en cas d'égalité sur `jour` |
| Moyenne mobile sur 7 lignes | `AVG(ca) OVER (ORDER BY jour ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | Suppose une ligne par jour, sans trou |
| Moyenne mobile sur 7 jours calendaires | `AVG(ca) OVER (ORDER BY UNIX_DATE(jour) RANGE BETWEEN 6 PRECEDING AND CURRENT ROW)` | Cadre sur la valeur de la clé : juste même avec des jours manquants |
| Fenêtre centrée | `AVG(x) OVER (ORDER BY t ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING)` | Lissage sur cinq lignes |
| Compter dans une plage de valeurs | `COUNT(*) OVER (ORDER BY UNIX_SECONDS(ts) RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW)` | Événements de la dernière heure à chaque instant |
| Tableau glissant | `ARRAY_AGG(produit) OVER (PARTITION BY client_id ORDER BY ts ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING)` | Trois derniers produits avant la ligne courante |
| Fenêtre nommée | `SELECT SUM(ca) OVER w, AVG(ca) OVER w FROM t WINDOW w AS (PARTITION BY pays ORDER BY jour)` | Définition écrite une fois ; `OVER (w ROWS BETWEEN ...)` la complète |

> [!TIP]
> `RANGE` exige un seul `ORDER BY` numérique : passer une date par `UNIX_DATE()`, un horodatage par `UNIX_SECONDS()`, `UNIX_MILLIS()` ou `UNIX_MICROS()`. Les bornes numériques sont des constantes entières positives ou nulles, ou des paramètres. `RANK`, `ROW_NUMBER` et les autres fonctions de numérotation n'acceptent pas de cadre.

### Motifs courants

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Dédoublonner (dernière version) | `SELECT * FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY maj DESC) = 1` | Une ligne par `id`, la plus récente |
| Dédoublonner par agrégat | `SELECT ARRAY_AGG(t ORDER BY maj DESC LIMIT 1)[OFFSET(0)].* FROM DATASET.TABLE AS t GROUP BY id` | Même résultat par agrégation, sans fonction de fenêtre |
| Premier et dernier d'un groupe | `MIN_BY(statut, ts)`, `MAX_BY(statut, ts)` avec `GROUP BY id` | Statut initial et final sans fenêtre |
| Écart entre événements | `TIMESTAMP_DIFF(ts, LAG(ts) OVER (PARTITION BY user_id ORDER BY ts), MINUTE)` | Minutes depuis l'événement précédent |

**Sessionisation** : une nouvelle session commence après 30 minutes d'inactivité.

```sql
WITH marques AS (
  SELECT user_id, ts,
    IF(COALESCE(TIMESTAMP_DIFF(ts, LAG(ts) OVER (PARTITION BY user_id ORDER BY ts), MINUTE) > 30, TRUE),
       1, 0) AS debut
  FROM `PROJECT_ID.DATASET.evenements`
)
SELECT user_id, ts,
  SUM(debut) OVER (PARTITION BY user_id ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_num
FROM marques
```

**Îlots et trous** (*gaps and islands*) : regrouper les jours consécutifs d'activité. Sur une suite continue, `jour - rang` est constant ; il change à chaque trou.

```sql
SELECT user_id, MIN(jour) AS debut, MAX(jour) AS fin, COUNT(*) AS nb_jours
FROM (
  SELECT user_id, jour,
    DATE_SUB(jour, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY jour) DAY) AS ilot
  FROM (SELECT DISTINCT user_id, jour FROM `PROJECT_ID.DATASET.activite`)
)
GROUP BY user_id, ilot
```

Contexte : [requêtes GoogleSQL](#googlesql-requetes), [ARRAY, STRUCT et JSON](#googlesql-tableaux-struct-json), [BigQuery](#bigquery).
