---
title: Workflows
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 10, w: 578, h: 282}
  nodes:
    ext: {label: API partenaire, sub: "HTTPS, hors GCP", external: true, x: 8, y: 120, w: 150}
    sched: {label: Cloud Scheduler, sub: déclenchement quotidien, icon: categories/integration-services, x: 186, y: 26, w: 220}
    wf: {label: Workflows, sub: "définition YAML, étapes", icon: categories/integration-services, focus: true, x: 186, y: 120, w: 210, h: 64}
    docai: {label: Document AI, sub: extraction de champs, icon: categories/ai-machine-learning, x: 470, y: 26, w: 200}
    run: {label: Cloud Run, sub: règles métier, icon: produits/cloud-run, x: 470, y: 120, w: 200}
    bq: {label: BigQuery, sub: table de résultats, icon: produits/bigquery, x: 470, y: 214, w: 200}
  flows:
    - {from: sched, to: wf, control: true, text: "Cloud Scheduler crée chaque nuit une exécution du workflow, avec ses arguments d'entrée."}
    - {from: wf, to: docai, text: "La première étape appelle Document AI par son connecteur, qui attend seul la fin de l'opération longue."}
    - {from: wf, to: run, text: "L'étape suivante passe le résultat à un service Cloud Run, authentifiée par un jeton d'identité."}
    - {from: wf, to: bq, text: "Une étape d'écriture insère les lignes produites dans BigQuery, là encore par connecteur."}
    - {from: wf, to: ext, text: "Un appel HTTP vers une API partenaire compte comme étape externe ; la réponse est rangée dans une variable."}
captures:
  - image: https://docs.cloud.google.com/static/workflows/images/steps-history-screenshot.png
    page: https://docs.cloud.google.com/workflows/docs/debug-steps
    legende: "Détail d'une exécution : historique des étapes avec leur état et graphe du workflow, dans la console"
  - image: https://docs.cloud.google.com/static/workflows/images/workflow-execution-with-rate-limits.png
    page: https://docs.cloud.google.com/workflows/docs/tutorials/buffer-workflows-executions
    legende: "Page d'un workflow : liste des exécutions en cours avec leur révision, heure de début et durée"
docs:
  Page produit: https://cloud.google.com/workflows
  Documentation: https://docs.cloud.google.com/workflows/docs
  Vue d'ensemble: https://docs.cloud.google.com/workflows/docs/overview
  Référence de la syntaxe: https://docs.cloud.google.com/workflows/docs/reference/syntax
  Bibliothèque standard: https://docs.cloud.google.com/workflows/docs/reference/stdlib/overview
  Connecteurs: https://docs.cloud.google.com/workflows/docs/connectors
  Requêtes HTTP: https://docs.cloud.google.com/workflows/docs/http-requests
  Étapes parallèles: https://docs.cloud.google.com/workflows/docs/execute-parallel-steps
  Points de rappel: https://docs.cloud.google.com/workflows/docs/creating-callback-endpoints
  API REST: https://docs.cloud.google.com/workflows/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/workflows
  Client Python: https://docs.cloud.google.com/python/docs/reference/workflows/latest
  Quotas et limites: https://docs.cloud.google.com/workflows/quotas
  Tarifs: https://cloud.google.com/workflows/pricing
  Notes de version: https://docs.cloud.google.com/workflows/docs/release-notes
---

## Ce que c'est

Orchestrateur sans serveur : un **workflow** décrit en YAML ou JSON une suite d'étapes qui appellent des services et enchaînent leurs résultats. Il n'y a ni code ni dépendance à maintenir, donc rien à corriger en sécurité ; une exécution qui n'a pas lieu ne coûte rien.

- **Définition et exécution.** On écrit la définition, on la **déploie**, puis on crée des **exécutions** indépendantes les unes des autres. Une exécution se lance depuis la console, `gcloud`, les bibliothèques clientes, une requête HTTP sur l'URL d'invocation, [Cloud Scheduler](#cloud-scheduler) ou un déclencheur [Eventarc](#eventarc). Le workflow est une ressource régionale et s'exécute dans sa région.
- **Structure.** Étapes séquentielles par défaut, blocs `switch` pour les conditions, boucles `for`, **sous-workflows** qui jouent le rôle de fonctions, et **étapes parallèles** — jusqu'à 10 branches, 2 niveaux d'imbrication et 20 branches ou itérations simultanées. Les erreurs se traitent par `try`/`retry`, avec des politiques de réessai prédéfinies ou une fonction de délai maison.
- **Appels.** Une étape peut émettre une requête HTTP ou HTTPS vers n'importe quelle API, avec authentification OAuth 2.0 ou OIDC gérée par le service. Les **connecteurs** encapsulent les APIs Google Cloud : ils construisent la requête, gèrent la pagination et, pour les opérations longues, font l'attente active à la place du workflow. Un point d'entrée privé s'atteint par le registre de Service Directory, et un point protégé par Identity-Aware Proxy est également accessible.
- **Attente.** Un workflow peut dormir, sonder une ressource ou attendre un **rappel** (*callback*) : il publie une URL, suspend l'exécution et reprend quand quelqu'un l'appelle — le mécanisme des validations humaines. La durée maximale d'une exécution est d'**un an**.
- **Limites.** Définition de 128 Kio, 100 000 étapes par exécution, 512 Kio cumulés pour les variables, les arguments et l'événement déclencheur, 2 Mio pour une réponse HTTP, 10 000 exécutions simultanées par région avec mise en file d'attente au-delà, historique conservé 90 jours.
- **Facturation** au nombre d'étapes exécutées, réessais compris. Une étape **interne** reste dans Google Cloud (appel à `*.googleapis.com`, à un service `run.app`, affectation de variable, évaluation de condition, appel de connecteur) : 5 000 gratuites par mois, puis 0,01 $ par tranche de 1 000. Une étape **externe** sort de Google Cloud ou attend un rappel : 2 000 gratuites, puis 0,025 $ par tranche de 1 000.

> [!TIP]
> Un service Cloud Run atteint par son domaine personnalisé compte comme étape externe, deux fois et demie plus chère qu'un appel à la même révision par son URL `run.app`.

## À quoi ça sert

- Enchaîner plusieurs APIs dans un ordre explicite, en rendant les dépendances visibles au lieu de les cacher dans des services qui s'appellent entre eux.
- Automatiser des traitements par lots planifiés : préparer puis lancer un job [BigQuery](#bigquery), produire un rapport, purger des ressources en fin de journée.
- Coder un processus métier qui dure — commande à honorer, demande à approuver — grâce aux rappels et à l'attente sur un an.
- Piloter des opérations d'infrastructure : créer un projet locataire, démarrer et arrêter des environnements sur événement.
- Servir de destination à un déclencheur [Eventarc](#eventarc) quand la réaction à un événement demande plusieurs appels.

**À éviter** pour la logique elle-même : la syntaxe n'est pas un langage de programmation, et un calcul, une transformation de données ou une règle métier un peu dense s'écrivent mieux dans un service [Cloud Run](#cloud-run) que le workflow appelle. À éviter aussi pour un pipeline de données volumineux — [Dataflow](#dataflow) ou un DAG [Airflow](#managed-service-for-apache-airflow) sont taillés pour ça — et pour un simple travail différé sans enchaînement, où [Cloud Tasks](#cloud-tasks) suffit.

## Alternatives en logiciel libre

- **Temporal** (MIT) : moteur de workflows durables où le processus s'écrit dans un vrai langage, avec reprise sur panne, réessais et signaux ; l'équivalent le plus puissant, au prix d'un serveur à exploiter.
- **Argo Workflows** (Apache 2.0) : enchaînements d'étapes en conteneurs sur Kubernetes, avec DAG, parallélisme et reprise.
- **Apache Airflow** (Apache 2.0) : orchestration par DAG planifiés, plus orientée données que services, avec un large catalogue d'opérateurs.
- **Conductor OSS** (Apache 2.0) : orchestration de microservices par définitions JSON, très proche du modèle « étapes qui appellent des APIs ».
- **SonataFlow** (Apache 2.0) : implémentation de la spécification CNCF Serverless Workflow, dont la description déclarative ressemble beaucoup à celle de Workflows.
- **Apache Camel** (Apache 2.0) : routes d'intégration entre systèmes, pour les enchaînements qui tiennent surtout de la médiation.
