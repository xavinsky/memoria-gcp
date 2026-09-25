---
title: "gcloud : contexte et configuration"
subgroup: gcloud
type: syntax
---

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lister les comptes authentifiés | `gcloud auth list` | Comptes connus, le compte actif marqué `*` |
| Afficher le projet courant | `gcloud config list project` | Section `[core]` avec `project = PROJECT_ID` |
| Récupérer l'ID du projet dans une variable | `PROJECT_ID=$(gcloud config get-value project)` | ID seul, sans décoration |
| Récupérer le numéro du projet | `gcloud projects describe $PROJECT_ID --format='value(projectNumber)'` | Numéro du projet, utile pour les agents de service |
| Fixer la région par défaut d'un service | `gcloud config set dataproc/region REGION` | Plus besoin de `--region` pour ce service |
| Afficher une ressource en JSON lisible | `gcloud ... describe ... --format=prettyjson` | Sortie complète en JSON indenté |
| Réinitialiser une API | `gcloud services disable SERVICE.googleapis.com --force` puis `gcloud services enable SERVICE.googleapis.com` | API dans un état propre ; vérifier ensuite le rôle de l'agent de service |
| Obtenir un jeton d'accès court | `gcloud auth print-access-token` | Jeton à passer en `Authorization: Bearer` |

> [!TIP]
> Dans Cloud Shell, `$GOOGLE_CLOUD_PROJECT` contient déjà l'ID du projet. Faire `echo $VAR` avant d'utiliser une variable exportée dans un autre onglet de terminal : elle y est vide, et une variable vide produit des erreurs trompeuses.

Contexte : [Authentifier un appel à une API](#authentifier-un-appel).
