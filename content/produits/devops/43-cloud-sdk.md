---
title: gcloud CLI
subgroup: Poste de développement
icon: categories/developer-tools
aka: Cloud SDK
schema:
  size: [760, 300]
  zones:
    - {label: "Poste du développeur ou machine CI", x: 10, y: 16, w: 300, h: 268}
    - {label: Projet GCP, x: 360, y: 16, w: 386, h: 268}
  nodes:
    conf: {label: Configuration active, sub: "projet, région, compte", icon: categories/management-tools, x: 30, y: 40, w: 260}
    cli: {label: gcloud CLI, sub: "gcloud, bq, gcloud storage", icon: categories/developer-tools, focus: true, x: 30, y: 120, w: 260, h: 60}
    cred: {label: Identifiants, sub: "ADC, clé, jeton d'accès", icon: categories/security-identity, x: 30, y: 216, w: 260}
    api: {label: APIs Google Cloud, sub: "points d'entrée REST", icon: categories/management-tools, x: 380, y: 120, w: 200}
    iam: {label: IAM, sub: "rôles et permissions", icon: categories/security-identity, x: 380, y: 216, w: 200}
    res: {label: Ressources, sub: "VM, buckets", icon: categories/compute, x: 610, y: 120, w: 130}
  flows:
    - {from: conf, to: cli, control: true, text: "La configuration active fournit le projet, la région et le compte : les commandes n'ont plus à les répéter, et gcloud config configurations activate fait basculer d'un contexte à l'autre."}
    - {from: cred, to: cli, text: "gcloud auth login stocke les identifiants de l'utilisateur ; gcloud auth application-default login écrit le fichier ADC que liront les bibliothèques clientes du même poste."}
    - {from: cli, to: api, text: "Chaque commande est un appel REST signé par un jeton OAuth dérivé de ces identifiants."}
    - {from: iam, to: api, control: true, text: "IAM vérifie que le principal appelant porte le rôle exigé par la méthode ; sinon l'appel repart en erreur 403."}
    - {from: api, to: res, text: "L'API crée, lit, modifie ou supprime la ressource visée dans le projet."}
docs:
  Page produit: https://cloud.google.com/sdk
  Documentation: https://docs.cloud.google.com/sdk/docs
  Vue d'ensemble de la gcloud CLI: https://docs.cloud.google.com/sdk/gcloud
  Installation: https://docs.cloud.google.com/sdk/docs/install-sdk
  Référence des commandes: https://docs.cloud.google.com/sdk/gcloud/reference
  Composants: https://docs.cloud.google.com/sdk/docs/components
  Configurations: https://docs.cloud.google.com/sdk/docs/configurations
  Propriétés: https://docs.cloud.google.com/sdk/docs/properties
  Authentification: https://docs.cloud.google.com/sdk/docs/authenticate
  Scripts et automatisation: https://docs.cloud.google.com/sdk/docs/scripting-gcloud
  Aide-mémoire: https://docs.cloud.google.com/sdk/docs/cheatsheet
  Commandes gcloud storage: https://docs.cloud.google.com/sdk/gcloud/reference/storage
  CLI bq: https://docs.cloud.google.com/bigquery/docs/reference/bq-cli-reference
  Outil gsutil: https://docs.cloud.google.com/storage/docs/gsutil
  Notes de version: https://docs.cloud.google.com/sdk/docs/release-notes
---

## Ce que c'est

L'outil en ligne de commande de Google Cloud. La documentation distingue deux niveaux : **Cloud SDK** désigne l'ensemble des outils de développement — la CLI, les bibliothèques clientes et les extensions d'IDE ; **Google Cloud CLI**, couramment appelée **gcloud CLI**, est le paquet installable qui contient les commandes.

- **Outils du paquet** : `gcloud` (toute la plateforme), `bq` (BigQuery) et `gsutil` [!DECONSEILLE] (Cloud Storage, outil hérité que remplacent les commandes `gcloud storage`). `kubectl` et divers émulateurs s'installent en composants supplémentaires.
- **Composants.** L'installation est modulaire : `gcloud components list`, `install`, `update`, `remove`. Les composants `gcloud`, `bq`, `gsutil` et `core` sont installés par défaut ; `alpha`, `beta` et `preview` ne le sont pas et sont proposés à l'installation à la première commande qui en a besoin. Le gestionnaire de composants est désactivé quand la CLI vient d'un gestionnaire de paquets système (apt, yum) : la mise à jour passe alors par ce gestionnaire.
- **Niveaux de publication** : GA (stable, sans étiquette), `preview`, `beta`, `alpha`. Les commandes sont organisées en groupes imbriqués — `gcloud compute instances list`, `gcloud beta compute`.
- **Configurations.** Une configuration est un jeu nommé de **propriétés** (projet, région, zone, compte actif, verbosité, invites). Les fichiers vivent dans `~/.config/gcloud` (ou `%APPDATA%\gcloud`, ou le chemin de `CLOUDSDK_CONFIG`). Plusieurs configurations cohabitent, activées par `gcloud config configurations activate` ou choisies à la commande par `--configuration`. Voir [Configurations gcloud](#gcloud-config).
- **Authentification.** `gcloud init` enchaîne connexion et configuration. Ensuite : identifiants stockés (`gcloud auth login`), fichier d'identifiants (fédération d'identité de charge de travail ou clé de compte de service), ou jeton d'accès fourni directement pour les environnements sans stockage. `gcloud auth application-default login` écrit les *Application Default Credentials* que lisent les bibliothèques clientes — deux mécanismes distincts, à ne pas confondre (voir [Authentifier un appel](#authentifier-un-appel)). Sur une VM Compute Engine, dans Cloud Run ou dans Cloud Build, le serveur de métadonnées fournit les identifiants sans configuration ; dans [Cloud Shell](#cloud-shell), c'est le compte de la console.
- **Sortie et scripts** : `--format` (json, yaml, csv, value), `--filter`, projections ; `gcloud topic formats`, `filters` et `projections` documentent la syntaxe. Un serveur MCP distant [!PREVERSION] expose `gcloud` et `bq` à une application d'IA.
- **Facturation** : l'outil est gratuit ; seules les ressources qu'il crée sont facturées.

> [!WARNING]
> `gsutil` est un outil hérité, peu maintenu, qui ignore les fonctions récentes de Cloud Storage (suppression réversible, dossiers gérés). Les commandes `gcloud storage` le remplacent et atteignent de meilleurs débits sans réglage manuel. Après mars 2027, `gsutil` ne sera plus livré avec la gcloud CLI et ne s'installera plus que séparément, depuis PyPI.

## À quoi ça sert

- Créer, inspecter et supprimer les ressources d'un projet sans passer par la console : c'est l'interface de référence, celle que la documentation donne en exemple.
- Scripter des tâches répétitives — création d'environnements, ménage, extraction d'inventaire — en combinant `--format` et `--filter` avec `jq` ou un shell.
- Authentifier un poste de développement : `gcloud auth application-default login` suffit à ce que le code local appelle les APIs avec le compte du développeur.
- Ouvrir un accès à une machine ou à un service : `gcloud compute ssh`, `gcloud workstations start-tcp-tunnel`, `gcloud container clusters get-credentials`.
- Copier des données : `gcloud storage cp` et `gcloud storage rsync` vers et depuis [Cloud Storage](#cloud-storage), `bq load` et `bq query` pour [BigQuery](#bigquery).

**À éviter** pour décrire une infrastructure durable : une suite de commandes impératives ne se rejoue pas et ne se compare pas à l'état réel ; c'est le domaine de l'infrastructure as code. À éviter aussi comme client applicatif : un programme doit appeler les bibliothèques clientes ou l'API REST, pas lancer des sous-processus `gcloud`, dont la sortie n'est pas un contrat stable. Pour une commande ponctuelle sans rien installer, [Cloud Shell](#cloud-shell) a déjà la CLI à jour et authentifiée.

## Alternatives en logiciel libre

La gcloud CLI n'a pas d'équivalent libre : elle parle à des APIs propriétaires. Les projets ci-dessous remplacent tel ou tel de ses usages.

- **OpenTofu** : gestion déclarative des ressources Google Cloud, sous licence MPL 2.0 — le pendant libre de Terraform, dont la licence (BSL) n'est pas libre. Remplace les commandes impératives de création.
- **Pulumi** : même rôle, l'infrastructure étant décrite dans un langage de programmation.
- **Crossplane** : provisionnement des ressources cloud depuis Kubernetes, par des manifestes réconciliés en continu.
- **Apache Libcloud** : bibliothèque Python unifiée sur plusieurs fournisseurs, pour scripter calcul et stockage sans dépendre des clients Google.
- **rclone** : copie et synchronisation vers Cloud Storage, à la place de `gcloud storage` et de `gsutil` ; **s5cmd** pour les transferts massifs via l'interface compatible S3.
- **k9s** et **kubectl** : pilotage d'un cluster GKE une fois les identifiants récupérés.
