---
title: Cloud Trace
subgroup: Exploitation
icon: categories/observability
aka: Stackdriver Trace
schema:
  size: [760, 330]
  zones:
    - {label: Projet GCP, x: 150, y: 16, w: 598, h: 298}
  nodes:
    users: {label: Navigateur, sub: "requête HTTP", external: true, x: 8, y: 130, w: 130}
    front: {label: Cloud Run, sub: "SDK OpenTelemetry", icon: produits/cloud-run, x: 170, y: 60, w: 180}
    back: {label: GKE, sub: "service aval instrumenté", icon: produits/gke, x: 170, y: 200, w: 200}
    otel: {label: Collecteur OTel, sub: "exportateur OTLP", icon: categories/observability, x: 400, y: 130, w: 180}
    trace: {label: Cloud Trace, sub: "bucket _Trace", icon: categories/observability, focus: true, x: 600, y: 126, w: 140, h: 64}
    log: {label: Cloud Logging, sub: "corrélation", icon: categories/observability, x: 400, y: 236, w: 170}
  flows:
    - {from: users, to: front, from_side: right, to_side: left, text: "La requête entre dans le service de tête, dont le SDK OpenTelemetry ouvre le span racine et fabrique le contexte de trace."}
    - {from: front, to: back, text: "L'appel aval transporte l'en-tête traceparent : le service appelé rattache ses propres spans à la même trace."}
    - {from: front, to: otel, text: "Les spans terminés partent en OTLP vers le collecteur, qui échantillonne, enrichit avec les attributs de ressource et met en lot."}
    - {from: back, to: otel, text: "Le service aval exporte vers le même collecteur ; l'identifiant de trace suffit à recoller les deux moitiés de l'appel."}
    - {from: otel, to: trace, text: "Le collecteur écrit par l'API Telemetry ; les spans atterrissent dans le bucket d'observabilité _Trace du projet."}
    - {from: trace, to: log, text: "Le champ de trace porté par chaque entrée de journal fait le lien entre un span lent et les messages émis pendant son exécution."}
captures:
  - image: https://docs.cloud.google.com/static/trace/images/trace-explorer-example.png
    page: https://docs.cloud.google.com/trace/docs/finding-traces
    legende: "Explorateur de traces : carte de densité des spans par latence et par heure, filtres par service et liste des spans"
  - image: https://docs.cloud.google.com/static/trace/images/quickstart-trace-span-details.png
    page: https://docs.cloud.google.com/trace/docs/trace-app-latency
    legende: "Détail d'une trace : chronologie des spans imbriqués et durée de chaque appel"
docs:
  Documentation: https://docs.cloud.google.com/trace/docs
  Vue d'ensemble: https://docs.cloud.google.com/trace/docs/overview
  Instrumentation OpenTelemetry: https://docs.cloud.google.com/stackdriver/docs/instrumentation/overview
  Mise en place en Python: https://docs.cloud.google.com/trace/docs/setup/python-ot
  Collecteur OpenTelemetry sur GKE: https://docs.cloud.google.com/stackdriver/docs/instrumentation/opentelemetry-collector-gke
  Trouver et filtrer les traces: https://docs.cloud.google.com/trace/docs/finding-traces
  Analyser une latence: https://docs.cloud.google.com/trace/docs/trace-app-latency
  Filtres de traces: https://docs.cloud.google.com/trace/docs/trace-filters
  Stockage des traces: https://docs.cloud.google.com/trace/docs/storage-overview
  Analyse en SQL: https://docs.cloud.google.com/trace/docs/analytics
  Schéma des spans: https://docs.cloud.google.com/trace/docs/reference/trace-schema
  API REST: https://docs.cloud.google.com/trace/docs/reference/v2/rest
  Bibliothèques clientes: https://docs.cloud.google.com/trace/docs/client-libraries
  Dépannage: https://docs.cloud.google.com/trace/docs/troubleshooting
  Quotas et limites: https://docs.cloud.google.com/trace/docs/quotas
  Dépréciations: https://docs.cloud.google.com/stackdriver/docs/deprecations
  Tarifs: https://cloud.google.com/products/observability/pricing
  Notes de version: https://docs.cloud.google.com/trace/docs/release-notes
---

## Ce que c'est

Service de traçage distribué de **Google Cloud Observability**, le nom d'ensemble qui réunit [Cloud Monitoring](#cloud-monitoring), [Cloud Logging](#cloud-logging), Trace, [Error Reporting](#error-reporting), [Cloud Profiler](#cloud-profiler) et [Managed Service for Prometheus](#managed-service-for-prometheus). Il reçoit les *spans* produits par les applications, les rassemble en traces et donne à voir le chemin complet d'une requête à travers les services.

- **Modèle.** Une **trace** est un arbre de **spans**. Chaque span porte un nom, un début, une fin, un span parent et des **attributs** (jusqu'à 1 024) : code HTTP, requête SQL, nom de la file, modèle appelé. La propagation entre services se fait par l'en-tête W3C `traceparent`.
- **Instrumentation.** La voie recommandée est **OpenTelemetry** : SDK du langage, instrumentation automatique des bibliothèques courantes, export en OTLP. Les anciennes bibliothèques clientes Trace restent utilisables, mais Google oriente les nouveaux projets vers OpenTelemetry, plus simple et non spécifique à un fournisseur.
- **Ingestion.** Deux portes d'entrée : l'**API Telemetry** (`telemetry.googleapis.com`), qui accepte l'OTLP tel quel, et l'API Cloud Trace historique. Entre l'application et l'API, on place généralement le **collecteur OpenTelemetry** construit par Google — sur [GKE](#gke), [Compute Engine](#compute-engine) ou en conteneur auxiliaire — pour échantillonner et enrichir au même endroit pour tous les services.
- **Traces automatiques.** [Cloud Run](#cloud-run), les fonctions Cloud Run et App Engine standard produisent des spans sans instrumentation ; ces spans-là ne sont pas facturés.
- **Stockage.** Les spans arrivent dans un **bucket d'observabilité** `_Trace` créé d'office, avec un jeu de données `Spans` et une vue `_AllSpans`, et une rétention de 30 jours. Un **jeu de données BigQuery lié** permet de les interroger en SQL et de les joindre à d'autres tables.
- **Exploration.** L'explorateur de traces affiche un nuage de points latence/temps, des filtres par attribut, un graphe des dépendances entre services et le détail chronologique d'une trace, avec les entrées de journal du même contexte.
- **Facturation** au span ingéré, avec une franchise mensuelle par compte de facturation. Les spans produits automatiquement par les services managés n'entrent pas dans le compte.

> [!WARNING]
> Les puits de traces (*trace sinks*) [!DECONSEILLE] sont en fin de vie : ils n'acceptent ni création ni modification, et le service ferme le 18 février 2027. L'export d'analyse passe par le jeu de données BigQuery lié au bucket `_Trace`.

## À quoi ça sert

- Situer une lenteur dans une chaîne d'appels : quel service, quel appel de base de données, quelle attente de file.
- Comparer les percentiles de latence d'un point de terminaison avant et après une mise en production, filtre par version à l'appui.
- Repérer les appels en cascade et les requêtes N+1, que les seules métriques agrégées ne montrent pas.
- Relier une trace lente aux journaux émis pendant son exécution, et inversement, par l'identifiant de trace porté dans les deux.
- Suivre les appels d'une application d'IA générative : les conventions sémantiques d'OpenTelemetry décrivent les appels de modèle et les étapes d'agent comme des spans ordinaires.

**À éviter** comme source de mesure continue : échantillonner des traces sert à diagnostiquer, pas à compter. Un taux d'erreur, un débit ou un percentile suivi en permanence se calcule en métrique ([Cloud Monitoring](#cloud-monitoring), [Managed Service for Prometheus](#managed-service-for-prometheus)), avec une rétention bien plus longue que 30 jours. À éviter aussi pour mesurer où un processus unique passe son temps CPU : c'est le terrain de [Cloud Profiler](#cloud-profiler), qui travaille à l'intérieur du span et non entre les services.

## Alternatives en logiciel libre

- **OpenTelemetry** (Apache 2.0) : la spécification, les SDK et le collecteur que Cloud Trace consomme directement. Changer de backend ne demande alors que de changer d'exportateur.
- **Jaeger** (Apache 2.0) : collecte, stockage et interface de traces distribuées ; l'équivalent le plus direct de l'explorateur de traces.
- **Grafana Tempo** (AGPL v3) : stockage de traces sur objet, sans index, interrogé par TraceQL et intégré aux tableaux de bord Grafana.
- **Zipkin** (Apache 2.0) : le traceur historique, simple à déployer, toujours utilisé pour les architectures modestes.
- **SigNoz** (MIT pour le cœur) : traces, métriques et journaux dans une même interface, avec ClickHouse en stockage.
- **Apache SkyWalking** (Apache 2.0) : APM orienté agents automatiques pour la JVM et .NET, avec analyse topologique des services.
- **Pixie** (Apache 2.0) : capture eBPF du trafic d'un cluster Kubernetes, sans modifier le code — une réponse différente à la même question.
