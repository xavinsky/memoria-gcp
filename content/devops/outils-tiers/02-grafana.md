---
title: Brancher Grafana sur Google Cloud
---

Grafana lit Google Cloud par quatre sources de données : **Google Cloud Monitoring** (préinstallée), **Prometheus** pointée sur [Managed Service for Prometheus](#managed-service-for-prometheus), et deux plugins à installer, **Google Cloud Logging** (maintenu par Google) et **Google BigQuery** (maintenu par Grafana Labs). Toutes appellent les API Google côté serveur Grafana, avec un compte de service : l'enjeu est de l'authentifier **sans clé JSON**, ce que permettent [GKE](#gke) et [Cloud Run](#cloud-run), pas Grafana Cloud. Cette section traite de l'installation et du câblage ; la conception des tableaux de bord et des alertes relève du groupe Exploitation de l'onglet Plateforme.

![Sources de données Grafana sur Google Cloud et leur authentification](../../svg/grafana-sources.svg)

## Les quatre sources de données

| Source (type Grafana) | Interroge | Langages | Rôles du compte de service |
|---|---|---|---|
| **Google Cloud Monitoring** (`stackdriver`) | Métriques Google Cloud, personnalisées, basées sur les journaux ; SLO | Constructeur, PromQL, SLO ; MQL encore présent | `roles/monitoring.viewer` |
| **Prometheus** (`prometheus`) sur Managed Service for Prometheus | API compatible Prometheus de [Cloud Monitoring](#cloud-monitoring) | PromQL | `roles/monitoring.viewer`, plus `roles/iam.serviceAccountTokenCreator` pour le *data source syncer* |
| **Google Cloud Logging** (`googlecloud-logging-datasource`) | Entrées de journal, par projet et par bucket | Langage de requête Logging | `roles/logging.viewer`, `roles/logging.viewAccessor` |
| **Google BigQuery** (`grafana-bigquery-datasource`) | Tables et vues, dont les exports de facturation et les journaux liés | GoogleSQL, éditeur visuel | `roles/bigquery.dataViewer`, `roles/bigquery.jobUser` |

- **Monitoring ou Prometheus pour les métriques ?** La source Cloud Monitoring voit toutes les métriques, Prometheus compris, et parle PromQL ; elle suffit tant qu'on n'importe pas de tableaux de bord communautaires. Ceux-ci attendent une source de type `prometheus` : c'est le cas d'usage de Managed Service for Prometheus. Les deux interrogent le même magasin, Monarch.
- **PromQL sur les métriques Google Cloud.** Les noms suivent la syntaxe UTF-8 : `sum by (metadata_system_region) ({"compute.googleapis.com/instance/cpu/utilization"})`. Les tableaux plus anciens utilisent la forme convertie `compute_googleapis_com:instance_cpu_utilization`.
- **MQL.** Le langage est hors support Google (fin au 22 juillet 2025) et absent de la console ; les requêtes existantes tournent par l'API, donc aussi dans Grafana. Écrire les nouvelles en PromQL.
- **Portée.** Une source Cloud Monitoring ou Prometheus lit un projet, ou un **champ d'application des métriques** entier si l'on vise son projet de rattachement : une source par champ d'application, pas une par projet. Activer aussi l'API Cloud Resource Manager, qui alimente la liste des projets.
- **Sans Grafana.** Cloud Monitoring importe les tableaux de bord Grafana au format JSON : pour quelques tableaux, pas d'instance à exploiter.

## Où héberger Grafana

| Hébergement | Identité | Base de Grafana | Alertes Grafana | Quand |
|---|---|---|---|---|
| **GKE**, chart Helm `grafana-community/grafana` | Workload Identity Federation for GKE, sans clé | SQLite sur volume persistant, ou [Cloud SQL](#cloud-sql) pour plusieurs réplicas | Réplicas en haute disponibilité (`ha_peers`) | Cluster existant, Prometheus déjà collecté dans le cluster |
| **Cloud Run**, image `grafana/grafana` | Compte de service attaché au service, sans clé | Base externe (Cloud SQL) : le disque d'une instance est éphémère | Une seule instance, toujours active | Pas de cluster ; quelques dizaines d'utilisateurs |
| **Grafana Cloud** (SaaS de Grafana Labs) | Clé JSON réduite à l'emprunt d'identité ; fédération par utilisateur, sans alertes | Gérée | Gérées | Pas d'exploitation ; Grafana déjà utilisé pour d'autres clouds |

Grafana est publié sous licence AGPL v3 ; Grafana Cloud et Grafana Enterprise sont les offres commerciales de Grafana Labs.

## Authentification sans clé

Les sources Cloud Monitoring, Cloud Logging et BigQuery acceptent le type d'authentification **GCE Default Service Account** (`authenticationType: gce`) ; la source Prometheus passe par le syncer (plus bas). Le nom est trompeur : ce mode s'appuie sur les ADC (*Application Default Credentials*) et sur le serveur de métadonnées, qui fournissent aussi l'identité fédérée d'un pod GKE et le compte de service attaché à un service Cloud Run. La même configuration sert donc sur les trois environnements Google.

```bash
# GKE : droits accordés directement au compte de service Kubernetes monitoring/grafana
KSA=principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/monitoring/sa/grafana
for ROLE in monitoring.viewer logging.viewer logging.viewAccessor bigquery.dataViewer bigquery.jobUser; do
  gcloud projects add-iam-policy-binding PROJECT_ID --role=roles/$ROLE --member=$KSA --condition=None
done
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm install grafana grafana-community/grafana -n monitoring --create-namespace -f values.yaml
```

Sur GKE Standard, Workload Identity Federation for GKE s'active sur le cluster et le pool de nœuds ; Autopilot l'active d'office. Sur Cloud Run, les mêmes rôles vont au compte de service `grafana@PROJECT_ID.iam.gserviceaccount.com`, passé par `--service-account`. Les rôles s'accordent dans chaque projet à lire (ou sur les jeux de données BigQuery visés), et au projet de rattachement pour un champ d'application des métriques.

Le fichier de provisionnement, placé dans `provisioning/datasources/` (ou sous la clé `datasources` du `values.yaml` du chart) :

```yaml
apiVersion: 1
datasources:
  - name: Google Cloud Monitoring
    type: stackdriver
    access: proxy
    jsonData: {authenticationType: gce}
  - name: Google Cloud Logging
    type: googlecloud-logging-datasource
    access: proxy
    jsonData: {authenticationType: gce}
  - name: BigQuery
    type: grafana-bigquery-datasource
    jsonData: {authenticationType: gce, defaultProject: PROJECT_ID, processingLocation: EU}
```

Les deux plugins s'installent au démarrage par `GF_PLUGINS_PREINSTALL_SYNC=googlecloud-logging-datasource,grafana-bigquery-datasource`, ou par la clé `plugins` du chart.

## Managed Service for Prometheus : le data source syncer

La source `prometheus` de Grafana ne sait pas obtenir un jeton OAuth2 Google. Google recommande le **data source syncer** : un job qui génère un jeton d'accès du compte de service et le réécrit, avec l'URL et les réglages, dans la source Prometheus par l'API de Grafana. Le jeton vivant une heure, le job tourne toutes les 10 minutes : *CronJob* dans le cluster de Grafana, ou job [Cloud Run](#cloud-run) déclenché par [Cloud Scheduler](#cloud-scheduler) pour une instance joignable depuis Internet (Grafana Cloud). Le *frontend* Prometheus de Google, un mandataire d'authentification déployé dans le cluster, n'est documenté qu'à titre de référence pour les installations qui l'emploient.

Le syncer reçoit l'UID de la source (`--datasource-uids`), l'URL de Grafana, le projet, et un jeton de compte de service **Grafana** (rôle *Data Sources > Writer*) rangé dans [Secret Manager](#secret-manager). Côté Google, son compte de service a `roles/monitoring.viewer` et `roles/iam.serviceAccountTokenCreator`, plus `secretmanager.secretAccessor` et `run.invoker` en version Cloud Run. La source pointe alors sur `https://monitoring.googleapis.com/v1/projects/PROJECT_ID/location/global/prometheus`, en méthode `GET`, avec des délais de 2 minutes.

## Grafana sur Cloud Run

```bash
gcloud run deploy grafana --image=docker.io/grafana/grafana:GRAFANA_VERSION --port=3000 \
  --region=REGION --service-account=grafana@PROJECT_ID.iam.gserviceaccount.com \
  --min-instances=1 --max-instances=1 --no-cpu-throttling --network=VPC --subnet=SUBNET \
  --set-env-vars="^;^GF_DATABASE_TYPE=postgres;GF_DATABASE_HOST=IP_PRIVEE:5432;GF_DATABASE_NAME=grafana;GF_DATABASE_USER=grafana;GF_PLUGINS_PREINSTALL_SYNC=googlecloud-logging-datasource,grafana-bigquery-datasource" \
  --set-secrets=GF_DATABASE_PASSWORD=grafana-db:latest,GF_SECURITY_ADMIN_PASSWORD=grafana-admin:latest
```

Une instance unique et toujours allouée, parce que Grafana évalue ses règles d'alerte en tâche de fond et que plusieurs instances les évalueraient chacune. La base PostgreSQL de Cloud SQL est jointe par son adresse privée, par la sortie VPC directe. Le préfixe `^;^` change le séparateur de `--set-env-vars`, la liste de plugins contenant une virgule. L'accès des utilisateurs passe par la connexion Google de Grafana ou par [Identity-Aware Proxy](#identity-aware-proxy).

## Pièges

- **Tableaux perdus au redémarrage.** Le chart Helm désactive la persistance par défaut, et une instance Cloud Run n'a pas de disque durable : la base SQLite, donc les tableaux et les utilisateurs, disparaît avec le pod ou l'instance. Volume persistant (`persistence.enabled: true`) ou Cloud SQL, et tableaux versionnés en JSON dans Git.
- **Source Prometheus provisionnée.** Une source décrite en YAML est en lecture seule pour l'API, sauf `editable: true` : le syncer ne peut alors pas y écrire son jeton. La créer une fois par l'interface ou l'API et laisser le syncer la tenir à jour.
- **Étendue d'accès de la VM.** Sur Compute Engine, le compte de service ne suffit pas : l'étendue d'accès de la VM doit inclure l'API Cloud Monitoring (ou `cloud-platform`). Sur GKE et Cloud Run, seuls les rôles IAM comptent.
- **Grafana Cloud et les clés.** Grafana Cloud ne tourne pas sur une identité Google : il faut une clé JSON. La réduire à un compte qui n'a que `roles/iam.serviceAccountTokenCreator` sur le compte lecteur, et activer l'**emprunt d'identité** dans la source. L'option *Workload Identity Federation* de Grafana Cloud fait agir l'utilisateur connecté : alertes, rapports planifiés et tableaux publics ne fonctionnent pas avec elle.
- **Coût des lectures.** Les appels de lecture de l'API Monitoring sont facturés au-delà d'un quota gratuit, contrairement à la console. Un mur d'écrans rafraîchi toutes les 10 secondes sur des dizaines de panneaux se voit sur la facture : allonger l'intervalle de rafraîchissement et agréger dans la requête.
- **BigQuery lu à chaque rafraîchissement.** Chaque panneau lance une requête facturée aux octets lus : tables partitionnées, filtre sur `$__timeFilter`, et intervalle de rafraîchissement long.
- **Requêtes en POST.** L'API Prometheus de Google n'accepte la route `/api/v1/series` qu'en `GET` ; le syncer règle la source en conséquence, une source configurée à la main doit l'être aussi.

## Alternatives en logiciel libre

Grafana lui-même est libre (AGPL v3) ; les projets ci-dessous le remplacent ou remplacent ce qu'il interroge sur Google Cloud.

- **Perses** (Apache 2.0) : tableaux de bord décrits comme du code et versionnés, pour les sources compatibles Prometheus, dont Managed Service for Prometheus derrière son proxy d'interface ; moins de sources et de greffons que Grafana.
- **Prometheus** et **Alertmanager** (Apache 2.0) : collecte, stockage et alertes gérés soi-même, à la place de Cloud Monitoring comme source ; Grafana les interroge sans authentification Google.
- **Thanos** (Apache 2.0) et **Grafana Mimir** (AGPL v3) : rétention longue et vue globale sur plusieurs Prometheus, là où Monarch l'apporte côté Google.
- **Grafana Loki** et **Grafana Tempo** (AGPL v3) : journaux et traces stockés sur un bucket, lus par Grafana à la place des sources Cloud Logging et Cloud Trace.
- **Apache Superset** (Apache 2.0), **Metabase** (AGPL v3 pour l'édition libre) et **Redash** (BSD 2-Clause) : tableaux de bord SQL branchés directement sur BigQuery, quand la source est l'entrepôt plutôt que les métriques.
