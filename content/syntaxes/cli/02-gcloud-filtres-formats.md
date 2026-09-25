---
title: "gcloud : filtres, formats et scripts"
subgroup: gcloud
type: syntax
---

Toutes les commandes `gcloud` acceptent les mêmes options de sortie. Sur une commande `list`, elles s'appliquent dans cet ordre : `--flatten`, `--sort-by`, `--filter`, `--limit`.

### Filtrer (`--filter`)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Voir les champs disponibles | `gcloud compute instances list --limit=1 --format=yaml` | Une ressource complète : ses clés servent dans `--filter`, `--format` et `--sort-by` |
| Égalité stricte | `--filter="status=RUNNING"` | Ressources dont la clé vaut exactement la valeur |
| Une valeur parmi plusieurs | `--filter="status=(RUNNING,STAGING)"` | Équivaut à un `OR` sur chaque valeur |
| Différent de | `--filter="status!=TERMINATED"` | Équivaut à `NOT status=TERMINATED` |
| Contient un mot (*has*) | `--filter="machineType:e2-standard"` | `:` cherche le motif parmi les mots de la valeur, sans casse ; `*` final pour un préfixe (`e2*`) |
| Clé présente ou absente | `--filter="labels.env:*"` / `--filter="-labels.env:*"` | Ressources qui ont (ou n'ont pas) le label `env`, quelle que soit sa valeur |
| Filtrer sur un label | `--filter="labels.env=prod AND labels.equipe=data"` | Opérateurs logiques en majuscules : `AND`, `OR`, `NOT` |
| Mélanger `AND` et `OR` | `--filter="(zone~europe AND status=RUNNING) OR labels.critique=oui"` | Parenthèses obligatoires dès que les deux opérateurs se côtoient |
| Expression régulière | `--filter="name~'^web-[0-9]+$'"` | `~` : correspondance d'une regex Python ; `!~` : non-correspondance |
| Comparer des nombres | `--filter="diskSizeGb>=500"` | Comparaison numérique si les deux côtés sont des nombres, sinon lexicographique |
| Créé après une date | `--filter="createTime>=2026-01-01"` | Dates ISO 8601 ; `gcloud topic datetimes` liste les formats acceptés |
| Créé depuis une durée | `--filter="createTime>-P7D"` | Durée ISO 8601 relative à maintenant : `-P7D` (7 jours), `-PT12H` (12 heures) |
| Valeur ressemblant à un nombre | `--filter="'tags:30e5504145'"` | Guillemets autour du terme : sinon la valeur est lue comme un flottant |

> [!WARNING]
> Selon l'API, le filtre s'exécute côté serveur, côté client ou les deux. Un filtre sur un champ que la commande ne renvoie pas ne produit aucune erreur : juste une liste vide. Vérifier le nom exact du champ avec `--format=yaml --limit=1`.

### Mettre en forme (`--format`)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Une valeur brute pour une variable | `--format="value(networkInterfaces[0].networkIP)"` | Sans en-tête ; plusieurs clés séparées par une tabulation |
| Premier élément d'une liste | `--format="value(disks[0].source.basename())"` | Nom du disque de démarrage, sans l'URL complète |
| Tableau choisi | `--format="table(name, zone.basename(), status)"` | Colonnes nommées d'après la dernière partie de la clé, en majuscules |
| Renommer et trier une colonne | `--format="table(name:label=VM:sort=1, creationTimestamp.date('%Y-%m-%d'):label=CREEE)"` | Attributs de clé après les transformations : `label`, `sort`, `reverse`, `align`, `wrap` |
| Tableau encadré avec titre | `--format="table[box,title=VMs](name, status)"` | Attributs de format entre crochets : `box`, `no-heading`, `title` |
| JSON ou YAML complet | `--format=json` / `--format=yaml` | Ressource entière, lisible par `jq` ou `yq` |
| Sous-ensemble en JSON | `--format="json(name, labels)"` | Seulement ces clés |
| Export CSV | `--format="csv[no-heading](name, zone.basename(), status)"` | Séparateur `,` ; `separator=';'` pour le changer |
| Une ligne clé : valeur par champ | `--format=flattened` | Chemin complet de chaque feuille ; pratique pour `grep` |
| Liste jointe en une cellule | `--format="value(tags.items.join(','))"` | `join()` concatène les éléments d'une liste |
| Date lisible dans le fuseau local | `--format="table(name, creationTimestamp.date(tz=LOCAL))"` | Transformation `date()` avec format `strftime` optionnel |
| Éclater une liste imbriquée | `--flatten="bindings[].members"` | Un enregistrement par élément ; `--filter` et `--format` voient ensuite `bindings.members` comme une valeur simple |
| URI des ressources | `--uri` | Une URL `https://www.googleapis.com/...` par ligne ; `uri()` l'ajoute comme colonne |
| Trier | `--sort-by="~creationTimestamp"` | Tri côté client ; `~` inverse l'ordre ; plusieurs clés séparées par `,` |
| Limiter le nombre de résultats | `--limit=10` | Appliqué après le tri et le filtre |
| Ne rien afficher | `--format=none` | Utile quand seul le code de retour compte |

> [!TIP]
> `gcloud topic filters`, `gcloud topic formats` et `gcloud topic projections` donnent la référence complète, avec la liste des transformations (`basename()`, `date()`, `join()`, `scope()`, `segment()`, `len()`…).

### Options communes à toutes les commandes

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Viser un autre projet le temps d'une commande | `--project=PROJECT_ID` | Projet de la ressource, et projet facturé pour le quota |
| Facturer le quota à un autre projet | `--billing-project=PROJECT_ID` | Quota et facturation de l'appel sur ce projet ; la ressource reste dans `--project` |
| Agir comme un compte de service | `--impersonate-service-account=SA@PROJECT_ID.iam.gserviceaccount.com` | Jeton court émis pour le compte de service, sans clé ; exige `roles/iam.serviceAccountTokenCreator` sur ce compte |
| Emprunter une identité en chaîne | `--impersonate-service-account=SA_1,SA_2` | `SA_1` est emprunté, `SA_2` est le délégué : chacun doit avoir le rôle *Token Creator* sur le suivant |
| Désactiver les invites interactives | `--quiet` ou `-q` | Valeurs par défaut prises, erreur si une réponse est obligatoire ; équivaut à `CLOUDSDK_CORE_DISABLE_PROMPTS=1` |
| Voir les appels HTTP | `--log-http` | Requêtes et réponses sur la sortie d'erreur |
| Plus ou moins de messages | `--verbosity=debug` | Niveaux : `debug`, `info`, `warning` (défaut), `error`, `critical`, `none` |
| Utiliser un autre compte ponctuellement | `--account=ACCOUNT` | Compte déjà authentifié via `gcloud auth login` |
| Passer des options depuis un fichier | `--flags-file=flags.yaml` | Dictionnaire `--option: valeur` en YAML ou JSON ; évite l'échappement shell |
| Valeur de liste contenant des virgules | `--metadata=^:^cles=a,b:env=prod` | `^DELIM^` en tête change le séparateur ; `gcloud topic escaping` |
| [!PREVERSION] Commande `beta` ou `alpha` | `gcloud beta ...` / `gcloud alpha ...` | Même syntaxe, fonctions pas encore en disponibilité générale ; pas de garantie de stabilité |
| Trouver une commande | `gcloud help -- MOT_CLE` | Recherche dans l'aide de toutes les commandes |

### Configurations et propriétés

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer une configuration par contexte | `gcloud config configurations create NOM` | Configuration vide, activée aussitôt (sauf `--no-activate`) ; nom en minuscules |
| Changer de configuration | `gcloud config configurations activate NOM` | Compte, projet, région et zone de cette configuration deviennent actifs |
| Lister les configurations | `gcloud config configurations list` | Nom, statut actif, compte et projet de chacune |
| Une configuration pour une seule commande | `--configuration=NOM` | Aussi par variable : `CLOUDSDK_ACTIVE_CONFIG_NAME=NOM` pour tout un terminal |
| Lire une propriété | `gcloud config get compute/region` | Valeur dans la configuration active |
| Écrire une propriété | `gcloud config set compute/region REGION` | `--installation` : pour toutes les configurations |
| Retirer une propriété | `gcloud config unset compute/zone` | La commande redemande la zone ou prend son défaut |
| Voir toutes les propriétés | `gcloud config list --all` | Propriétés définies et non définies, par section |
| Surcharger une propriété par variable | `CLOUDSDK_CORE_PROJECT=PROJECT_ID gcloud ...` | Forme `CLOUDSDK_SECTION_PROPRIETE` ; prioritaire sur la configuration active |
| Emprunter une identité par défaut | `gcloud config set auth/impersonate_service_account SA@PROJECT_ID.iam.gserviceaccount.com` | Toutes les commandes passent par ce compte de service ; `unset` pour revenir |
| Diagnostiquer l'installation | `gcloud info` | Version, Python, chemins, compte et projet actifs |
| Tester le réseau et les certificats | `gcloud info --run-diagnostics` | Connectivité aux API Google, proxy |
| Chemin de la configuration active | `gcloud info --format="value(config.paths.active_config_path)"` | Fichier des propriétés sous `~/.config/gcloud` (ou `$CLOUDSDK_CONFIG`) |
| Lister, ajouter ou mettre à jour les composants | `gcloud components list` / `gcloud components install beta kubectl` / `gcloud components update` | Installation par archive uniquement : avec un paquet `apt` ou `dnf`, passer par le gestionnaire de paquets |

### Boucles en bash

Récupérer une liste en `value()` et la parcourir :

```bash
for p in $(gcloud projects list --format="value(projectId)" --filter="labels.env=dev"); do
  gcloud compute instances list --project="$p" \
    --filter="status=RUNNING" --format="csv[no-heading](name,zone.basename())" \
    | sed "s/^/$p,/"
done
```

Parcourir des lignes à plusieurs champs sans éclatement sur les espaces :

```bash
gcloud compute instances list --filter="labels.arret=nuit" \
  --format="value(name,zone.basename())" |
while IFS=$'\t' read -r nom zone; do
  gcloud compute instances stop "$nom" --zone="$zone" --async --quiet
done
```

> [!TIP]
> Dans un script, fixer `--project` explicitement plutôt que de dépendre de la configuration active : une autre session qui change de configuration modifie aussi celle du script.

Contexte : [contexte et configuration](#gcloud-config), [projets, API et IAM](#gcloud-iam-projets), [authentifier un appel](#authentifier-un-appel), [Cloud SDK](#cloud-sdk).
