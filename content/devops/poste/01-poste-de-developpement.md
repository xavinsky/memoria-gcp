---
title: Le poste de développement
---

Le poste d'un développeur Google Cloud se décide sur deux questions : **où tourne le code** pendant qu'on l'écrit — sa propre machine, [Cloud Shell](#cloud-shell) ou [Cloud Workstations](#cloud-workstations) — et **avec quelle identité** il appelle les APIs. La réponse à la seconde ne varie pas : l'identité du développeur, ou un compte de service emprunté pour une durée courte, jamais une clé de compte de service posée sur le disque.

![Arbre de décision : où tourne le poste de développement](../../svg/choix-poste-dev.svg)

## Matrice des options

| | **Poste local** | **Cloud Shell** | **Cloud Workstations** |
|---|---|---|---|
| Où tourne le code | Machine du développeur | VM Debian gérée par Google, hors de tout projet | VM Compute Engine du projet, dans son VPC |
| Installation | [gcloud CLI](#cloud-sdk), Docker, IDE, à tenir à jour | Rien : outillage préinstallé, image mise à jour chaque semaine | Rien sur le portable ; l'outillage est figé dans l'image de la configuration |
| Identité | `gcloud auth login` et `gcloud auth application-default login` | Compte connecté à la console, autorisé au premier appel | Compte de l'utilisateur après connexion ; sinon, compte de service de la VM |
| Accès aux ressources privées | Par VPN, Interconnect ou tunnel IAP | Aucun accès au VPC | Direct : le poste est dans le VPC |
| Persistance | Disque local | 5 Gio dans `$HOME`, effacés après 120 jours sans session | Disque persistant sur `/home`, le reste est recréé à chaque démarrage |
| Limites | Celles de la machine | 50 h par semaine, 12 h par session, arrêt après 1 h d'inactivité | Délais d'inactivité et de fonctionnement fixés par la configuration |
| Coût | Aucun côté Google | Gratuit | VM et disque, 0,05 $ par vCPU et par heure de poste démarré, 0,20 $ par heure et par cluster en permanence |
| Choisir quand | Développement courant sans contrainte réseau ni de conformité | Dépannage, tutoriel, commande occasionnelle | Ressources privées, code qui ne doit pas quitter le projet, équipe à outiller à l'identique, grosse machine |

Pour Cloud Workstations, l'administrateur crée un **cluster** (région, VPC), puis des **configurations** (type de machine, disque, image, IDE, délais) ; chaque développeur crée son poste à partir d'une configuration. L'accès se fait par le navigateur, par SSH, ou depuis un IDE local à travers `gcloud workstations start-tcp-tunnel`. Le cluster facturé à l'heure en permanence rend le service coûteux pour une équipe de deux personnes : c'est à l'échelle d'une équipe, ou sous contrainte de conformité, qu'il se justifie.

## Dans l'IDE

- **[Cloud Code](#cloud-code)** (VS Code et JetBrains, gratuit) : le cycle conteneur — manifestes Kubernetes, skaffold, émulateur Cloud Run, débogage local, Secret Manager. Préinstallé dans l'éditeur Cloud Shell et les images Cloud Workstations. Il ne fait pas d'assistance par modèle.
- **[Gemini Code Assist](#gemini-code-assist)**, éditions **Standard** et **Enterprise**, licence par utilisateur : complétion, chat, mode agent [!PREVERSION] (VS Code et IntelliJ) avec outils et serveurs MCP. L'édition Enterprise ajoute la personnalisation sur les dépôts privés de l'organisation. Les comptes individuels et les offres Google AI Pro et Ultra passent par [Antigravity](#antigravity).
- **Configurations gcloud** : une configuration nommée par projet ou par environnement évite d'agir sur la production depuis le mauvais terminal (voir [Configurations gcloud](#gcloud-config)).

## Tester sans le cloud : les émulateurs

La gcloud CLI fournit des émulateurs locaux, en mémoire, qui exposent la même API que le service. Les bibliothèques clientes basculent dessus d'elles-mêmes quand la variable d'environnement correspondante est définie ; `env-init` affiche la commande `export` à exécuter.

| Service | Démarrage | Variable | Ce qui manque |
|---|---|---|---|
| [!PREVERSION] [Pub/Sub](#pubsub) | `gcloud beta emulators pubsub start --project=PROJECT_ID` | `PUBSUB_EMULATOR_HOST` | IAM ; les abonnements BigQuery n'écrivent rien ; les *Single Message Transforms* ne s'appliquent pas ; rétention illimitée |
| [Firestore](#firestore) | `gcloud emulators firestore start --host-port=localhost:8080` | `FIRESTORE_EMULATOR_HOST` | Comportement transactionnel et limites de production ; index composites non suivis |
| [Spanner](#spanner) | `gcloud emulators spanner start` (ou l'image Docker `gcr.io/cloud-spanner-emulator/emulator`) | `SPANNER_EMULATOR_HOST=localhost:9010` | TLS, authentification, IAM ; performances non représentatives |
| [!PREVERSION] [Bigtable](#bigtable) | `gcloud beta emulators bigtable start` | `BIGTABLE_EMULATOR_HOST=localhost:8086` | Persistance, connexion sécurisée |
| [!PREVERSION] Firestore en mode Datastore | `gcloud beta emulators datastore start` | `DATASTORE_EMULATOR_HOST` | Mêmes réserves que Firestore |

```bash
gcloud beta emulators pubsub start --project=PROJECT_ID &
$(gcloud beta emulators pubsub env-init)   # exporte PUBSUB_EMULATOR_HOST
python publier.py                          # le client Python parle à l'émulateur
```

BigQuery, Cloud Storage et Agent Platform n'ont pas d'émulateur Google : ils se testent dans un **projet de dev**, avec un dataset ou un bucket par développeur. Un pipeline Beam tourne en local sur le *DirectRunner* avant d'aller sur [Dataflow](#dataflow).

## Tester un service Cloud Run

- **Une fonction** : le *Functions Framework* (`pip install functions-framework`, puis `functions-framework --target=NOM_FONCTION`) sert la fonction en HTTP sur le port 8080, sans conteneur.
- **Un conteneur** : `docker run -p 9090:8080 -e PORT=8080 IMAGE_URL`, ou `gcloud beta code dev` [!PREVERSION], qui construit la source (Dockerfile ou *buildpacks*), la lance sur minikube et la reconstruit à chaque modification ; `--application-default-credential` lui passe les ADC du poste.
- **Un service déjà déployé et protégé par IAM** : `gcloud run services proxy SERVICE --region=REGION --port=8080` ouvre `localhost:8080` et ajoute le jeton d'identité du compte actif à chaque requête. Un service en entrée interne seulement reste inaccessible depuis l'extérieur du VPC.

## Identité sur le poste

```bash
gcloud auth login                              # identité de la gcloud CLI
gcloud auth application-default login          # ADC, lues par les bibliothèques clientes
gcloud auth application-default set-quota-project PROJECT_ID

# Agir avec les droits d'un compte de service, sans clé
gcloud config set auth/impersonate_service_account SA@PROJECT_ID.iam.gserviceaccount.com
gcloud auth application-default login --impersonate-service-account SA@PROJECT_ID.iam.gserviceaccount.com
```

- **Deux jeux d'identifiants.** `gcloud auth login` sert aux commandes `gcloud` ; `application-default login` écrit les ADC, que lisent le code et les outils comme Terraform ou la CLI Dataform. L'un ne remplace pas l'autre (voir [Authentifier un appel à une API](#authentifier-un-appel)).
- **Emprunt d'identité.** Pour vérifier qu'un compte de service applicatif a bien les droits nécessaires, l'emprunter plutôt que d'en télécharger une clé : il faut le rôle *Service Account Token Creator* (`roles/iam.serviceAccountTokenCreator`) sur ce compte, et les jetons obtenus sont de courte durée. Les journaux d'audit nomment le compte de service et, en général, le développeur qui l'a emprunté (`serviceAccountDelegationInfo`).
- **Pas de clé.** La contrainte d'organisation gérée `iam.managed.disableServiceAccountKeyCreation` interdit d'en créer ; la CI se passe aussi de clé grâce à [Workload Identity Federation](#deployer-sans-cle).

## Pièges

- **Une variable `GOOGLE_APPLICATION_CREDENTIALS` oubliée.** Elle passe avant tout le reste dans l'ordre de recherche des ADC : le code utilise alors une vieille clé au lieu des identifiants du développeur.
- **Une variable d'émulateur restée définie.** Le client écrit dans l'émulateur en croyant écrire dans le projet, ou l'inverse dans un autre terminal. `gcloud beta emulators datastore env-unset` existe pour Datastore ; pour les autres, `unset`.
- **Le compte de service d'un Cloud Workstations trop large.** Sans connexion de l'utilisateur, les ADC retombent sur le compte de service de la VM : lui donner le strict nécessaire (journaux, métriques, lecture de l'image dans Artifact Registry).
- **Cloud Shell comme poste de travail ou comme automate.** Quota hebdomadaire, session coupée à 12 h, tâches non interactives arrêtées au bout de 40 minutes, aucun accès au VPC.
- **Un cluster Cloud Workstations d'essai laissé en place.** Environ 145 $ par mois et par région, sans aucun poste démarré.
- **Déployer depuis le poste.** Un `gcloud run deploy` lancé depuis un portable n'est ni revu ni reproductible : la production passe par une chaîne CI (voir [La chaîne CI/CD](#chaine-cicd)).

## Alternatives en logiciel libre

- **Dev Containers** (spécification et CLI sous MIT) : l'environnement de développement décrit dans le dépôt par `devcontainer.json`, reproductible sur un poste, dans un IDE ou sur une VM ; le pendant de l'image d'une configuration Cloud Workstations.
- **Coder** (AGPL v3) : plateforme d'environnements distants décrits par des gabarits en HCL, sur des VM ou dans Kubernetes ; l'équivalent le plus complet de Cloud Workstations, plan de contrôle à exploiter.
- **Eclipse Che** (EPL 2.0) : espaces de travail conteneurisés sur Kubernetes décrits par un `devfile`, avec IDE dans le navigateur.
- **code-server** (MIT) : Code OSS servi dans le navigateur depuis une machine que l'on administre, pour la seule partie éditeur de Cloud Shell ou de Cloud Workstations.
- **Testcontainers** (MIT pour Java, Apache 2.0 pour Python) : lance les émulateurs Google en conteneurs depuis le code de test, avec des modules prêts pour Pub/Sub, Firestore, Spanner, Bigtable et Datastore, et les arrête à la fin.
- **fake-gcs-server** (BSD 2-Clause) et **bigquery-emulator** (MIT) : émulateurs tiers de Cloud Storage et de BigQuery, que Google ne fournit pas ; couverture partielle de l'API et du SQL, à doubler d'un test dans le projet de dev.
