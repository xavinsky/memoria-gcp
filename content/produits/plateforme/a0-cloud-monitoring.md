---
title: Cloud Monitoring
subgroup: Exploitation
icon: categories/observability
aka: Stackdriver Monitoring
schema:
  size: [760, 350]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 420, h: 318}
  nodes:
    vm: {label: Compute Engine, sub: "agent Ops", icon: produits/compute-engine, x: 190, y: 44, w: 166}
    run: {label: Cloud Run, sub: "métriques intégrées", icon: produits/cloud-run, x: 190, y: 118, w: 180}
    gke: {label: GKE, sub: "métriques Prometheus", icon: produits/gke, x: 190, y: 192, w: 180}
    log: {label: Cloud Logging, sub: "métrique de journal", icon: categories/observability, x: 190, y: 266, w: 180}
    mon: {label: Cloud Monitoring, sub: "séries temporelles", icon: categories/observability, focus: true, x: 410, y: 150, w: 172, h: 64}
    notif: {label: PagerDuty / Slack, sub: "canal de notification", external: true, x: 606, y: 60, w: 150}
    site: {label: Site public, sub: "URL surveillée", external: true, x: 606, y: 250, w: 140}
  flows:
    - {from: vm, to: mon, text: "L'agent Ops installé sur la VM relève les métriques système, celles du matériel et celles des applications tierces qu'il reconnaît."}
    - {from: run, to: mon, text: "Les services managés publient d'office leurs métriques — requêtes, latences, instances actives — sans agent ni configuration."}
    - {from: gke, to: mon, text: "Les métriques Prometheus du cluster arrivent par Managed Service for Prometheus et se lisent en PromQL dans le même projet."}
    - {from: log, to: mon, from_side: right, to_side: left, text: "Une métrique basée sur les journaux compte les entrées qui correspondent à un filtre et devient une série temporelle comme les autres."}
    - {from: mon, to: notif, text: "La condition d'une règle d'alerte est franchie : un incident s'ouvre et part vers les canaux de notification déclarés."}
    - {from: mon, to: site, text: "Une vérification de disponibilité interroge l'URL depuis plusieurs régions ; l'échec simultané de plusieurs sondes déclenche une alerte."}
captures:
  - image: https://docs.cloud.google.com/static/monitoring/images/percent-used-by-state.png
    page: https://docs.cloud.google.com/monitoring/docs/monitoring-overview
    legende: "Graphique de métrique : utilisation CPU moyenne regroupée par type de machine, avec la valeur courante de chaque série"
  - image: https://docs.cloud.google.com/static/monitoring/images/chartdef-style-alert.png
    page: https://docs.cloud.google.com/monitoring/alerts/manage-alerts
    legende: "Graphique d'une règle d'alerte : séries surveillées, ligne de seuil à 80 % et état des incidents"
docs:
  Page produit: https://cloud.google.com/monitoring
  Documentation: https://docs.cloud.google.com/monitoring/docs
  Vue d'ensemble: https://docs.cloud.google.com/monitoring/docs/monitoring-overview
  Tableaux de bord: https://docs.cloud.google.com/monitoring/dashboards
  Explorateur de métriques: https://docs.cloud.google.com/monitoring/charts/metrics-explorer
  Alertes: https://docs.cloud.google.com/monitoring/alerts
  Canaux de notification: https://docs.cloud.google.com/monitoring/support/notification-options
  Vérifications de disponibilité: https://docs.cloud.google.com/monitoring/uptime-checks
  Surveillance des SLO: https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring
  Champ d'application des métriques: https://docs.cloud.google.com/monitoring/settings
  PromQL: https://docs.cloud.google.com/monitoring/promql
  Métriques personnalisées: https://docs.cloud.google.com/monitoring/custom-metrics
  Liste des métriques Google Cloud: https://docs.cloud.google.com/monitoring/api/metrics_gcp
  Agent Ops: https://docs.cloud.google.com/monitoring/agent/ops-agent
  API REST: https://docs.cloud.google.com/monitoring/api/v3
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/monitoring
  Client Python: https://docs.cloud.google.com/python/docs/reference/monitoring/latest
  Quotas et limites: https://docs.cloud.google.com/monitoring/quotas
  Tarifs: https://cloud.google.com/products/observability/pricing
  Notes de version: https://docs.cloud.google.com/monitoring/docs/release-notes
---

## Ce que c'est

Service de métriques de **Google Cloud Observability**, le nom d'ensemble sous lequel Google réunit Monitoring, [Cloud Logging](#cloud-logging), [Cloud Trace](#cloud-trace), [Error Reporting](#error-reporting), [Cloud Profiler](#cloud-profiler) et [Managed Service for Prometheus](#managed-service-for-prometheus). Il stocke les séries temporelles dans Monarch, la base de métriques qui sert aussi la surveillance interne de Google, et fournit les tableaux de bord, les alertes et les SLO qui vont avec.

- **Modèle de données.** Une série temporelle est identifiée par un **type de métrique** (`compute.googleapis.com/instance/cpu/utilization`), une **ressource surveillée** (`gce_instance`, `k8s_container`, `cloud_run_revision`) et des étiquettes. Chaque point porte un type (jauge, delta, cumul) et une valeur (booléen, entier, réel, chaîne, **distribution** pour les histogrammes de latence).
- **Sources.** Plus de 6 500 types de métriques Google Cloud sont collectés sans configuration et sans facturation. S'y ajoutent les **métriques personnalisées** écrites par l'application, les métriques OTLP, les métriques Prometheus, les métriques basées sur les journaux et les métriques remontées par l'**agent Ops**.
- **Agent Ops.** Agent unique pour les VM Linux et Windows : Fluent Bit pour les journaux, OpenTelemetry Collector pour les métriques et les traces, configuré en YAML. Il couvre les métriques système, les GPU et une quarantaine d'applications tierces (MySQL, PostgreSQL, NGINX, Kafka, Redis). Il se déploie à la création de la VM, par une règle d'agent, par `gcloud` ou par Terraform.
- **Champ d'application des métriques** (*metrics scope*). Un projet de rattachement agrège les métriques de plusieurs projets pour les afficher dans une même vue. La limite recommandée est de 375 projets par champ d'application, 3 500 au maximum. Le champ d'application ne change ni où la donnée est reçue ni qui la paie.
- **Interrogation.** **PromQL** est le langage recommandé, y compris sur les métriques Google Cloud ; l'explorateur de métriques propose aussi une construction guidée et un mode SQL. Monitoring Query Language (MQL) est hors support et absent de la console ; les requêtes MQL restent exécutables par l'API.
- **Tableaux de bord.** Tableaux prédéfinis par service, tableaux personnalisés en widgets (courbes, jauges, tableaux, *heatmaps*, *treemaps*, cartes de scores, journaux, incidents) avec variables de filtrage. Un tableau de bord se décrit en JSON et se versionne comme du code (API, `gcloud`, Terraform).
- **Alertes.** Une **règle d'alerte** associe une ou plusieurs conditions (seuil sur métrique, absence de métrique, requête PromQL, correspondance de journal, prévision) à des **canaux de notification** : e-mail, SMS, application mobile Cloud, Slack, PagerDuty, webhook, [Pub/Sub](#pubsub), et Google Chat [!PREVERSION]. Une alerte s'ouvre au franchissement et se ferme au retour à la normale (l'API et les notifications la décrivent comme un objet `incident`) ; la documentation de la règle, écrite en Markdown avec des variables, part dans la notification.
- **Disponibilité.** Les **vérifications de disponibilité** interrogent une URL, une adresse IP ou une ressource depuis plusieurs régions, en public ou en privé. Les **moniteurs synthétiques** vont plus loin : une fonction Node.js exécute un scénario complet, y compris un parcours de navigateur avec Puppeteer.
- **SLO.** Un **service** (Cloud Run, GKE, App Engine, maillage de services ou service déclaré à la main) porte des **SLI** de disponibilité ou de latence, des **SLO** sur période calendaire ou glissante, et des alertes sur la vitesse de consommation du budget d'erreur.
- **Facturation** au volume ingéré : les métriques Google Cloud sont gratuites, les autres sont facturées à partir de 150 Mio par compte de facturation et par mois. Les métriques Prometheus sont comptées en échantillons. Les appels d'API en écriture ne sont pas facturés ; la lecture l'est au-delà d'un quota gratuit, sauf depuis la console.

> [!WARNING]
> La rétention n'est pas la même partout : six semaines pour les métriques Google Cloud, vingt-quatre mois pour les métriques personnalisées, externes et Prometheus, avec un ré-échantillonnage progressif. Une analyse sur plusieurs trimestres suppose donc soit une métrique personnalisée, soit un export vers [BigQuery](#bigquery).

## À quoi ça sert

- Voir l'état d'un service managé sans rien installer : [Cloud Run](#cloud-run), [GKE](#gke), [Cloud SQL](#cloud-sql) et les autres publient leurs métriques d'office.
- Surveiller une flotte de VM ([Compute Engine](#compute-engine)) et les serveurs applicatifs qu'elles hébergent, avec l'agent Ops et ses intégrations tierces.
- Porter l'astreinte : règles d'alerte, incidents, canaux de notification et documentation d'intervention attachée à la règle.
- Suivre un engagement de service par des SLO et alerter sur la consommation du budget d'erreur plutôt que sur chaque pic.
- Vérifier de l'extérieur qu'un site ou une API répond, depuis plusieurs continents, et mesurer un parcours complet avec un moniteur synthétique.
- Centraliser la vue de plusieurs projets d'un même environnement dans un champ d'application des métriques unique.

**À éviter** comme socle d'une supervision multi-cloud dont Google Cloud n'est qu'une partie : les métriques d'autres fournisseurs doivent y être poussées une à une, et un Prometheus ou un Grafana déjà en place ailleurs fera moins de travail. À éviter aussi pour l'analyse fine et rétrospective d'incidents : les métriques agrégées ne remplacent pas les journaux ([Cloud Logging](#cloud-logging)) ni les traces ([Cloud Trace](#cloud-trace)), et un tableau de bord n'explique pas une latence. Enfin, pour des métriques Prometheus produites en masse par des clusters, passer directement par [Managed Service for Prometheus](#managed-service-for-prometheus) : le modèle de facturation à l'échantillon y est plus avantageux que la facturation à l'octet.

## Alternatives en logiciel libre

- **Prometheus** (Apache 2.0) : collecte par *scraping*, base de séries temporelles et langage PromQL — celui-là même que Cloud Monitoring a adopté. L'équivalent le plus direct pour la partie métriques.
- **Grafana** (AGPL v3) : tableaux de bord et alertes sur des sources multiples ; c'est le pendant de la partie visualisation, et il sait interroger Cloud Monitoring directement.
- **Alertmanager** (Apache 2.0) : routage, regroupement, mise en sourdine et escalade des alertes de Prometheus, l'équivalent des canaux de notification et du cycle de vie des incidents.
- **Thanos** (Apache 2.0) et **Grafana Mimir** (AGPL v3) : rétention longue et requêtes globales sur plusieurs Prometheus, ce que Monarch fournit nativement ici.
- **VictoriaMetrics** (Apache 2.0) : base de séries temporelles compatible PromQL, réputée pour sa compacité, avec sa propre chaîne d'agents et d'alertes.
- **Zabbix** (AGPL v3) et **Icinga 2** (GPL v2) : supervision d'infrastructure par agent et par sonde, proche de l'usage « flotte de VM » et des vérifications de disponibilité.
- **Blackbox exporter** (Apache 2.0) et **Uptime Kuma** (MIT) : sondes HTTP, TCP et DNS depuis l'extérieur, l'équivalent des vérifications de disponibilité.
- **Pyrra** (Apache 2.0) et **Sloth** (Apache 2.0) : déclaration de SLO et génération des règles Prometheus correspondantes, y compris les alertes de budget d'erreur.
