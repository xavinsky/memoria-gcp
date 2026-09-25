---
title: Application Integration
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 10, w: 568, h: 282}
  nodes:
    sf: {label: "Salesforce, SAP", sub: applications métier, external: true, x: 8, y: 214, w: 160}
    ps: {label: Pub/Sub, sub: message déclencheur, icon: categories/data-analytics, x: 196, y: 26, w: 200}
    ai: {label: Application Integration, sub: tâches et mappages, icon: categories/integration-services, focus: true, x: 196, y: 118, w: 230, h: 64}
    conn: {label: Integration Connectors, sub: nœuds de connexion, icon: categories/integration-services, x: 196, y: 214, w: 230}
    bq: {label: BigQuery, sub: suivi des exécutions, icon: produits/bigquery, x: 480, y: 26, w: 190}
    mail: {label: Tâche Send Email, sub: notification, icon: categories/collaboration, x: 480, y: 118, w: 200}
  flows:
    - {from: ps, to: ai, text: "Un message Pub/Sub déclenche l'exécution de l'intégration ; un déclencheur d'API ou de planification ferait aussi bien."}
    - {from: ai, to: conn, control: true, text: "Une tâche Connectors demande au connecteur de lire ou d'écrire dans l'application métier."}
    - {from: conn, to: sf, text: "Le connecteur ouvre la connexion vers Salesforce ou SAP, exécute l'action et rend le résultat en variable."}
    - {from: ai, to: mail, from_offset: 20, text: "Après un mappage de données qui compose le message, une tâche Send Email prévient l'équipe."}
    - {from: ai, to: bq, from_offset: -20, text: "Une dernière tâche écrit le suivi de l'exécution dans BigQuery."}
captures:
  - image: https://docs.cloud.google.com/static/application-integration/images/integrations_editor_layout.png
    page: https://docs.cloud.google.com/application-integration/docs/integration-designer-layout
    legende: "Éditeur d'intégration : volet des variables, canevas avec déclencheur d'API, tâches et conditions sur les arêtes, volet de configuration"
  - image: https://docs.cloud.google.com/static/application-integration/images/data-mapping-editor-screen.png
    page: https://docs.cloud.google.com/application-integration/docs/retrieve-api-payload-send-email
    legende: "Éditeur de mappage : variables d'entrée, fonctions de transformation et variable de sortie"
docs:
  Page produit: https://cloud.google.com/application-integration
  Documentation: https://docs.cloud.google.com/application-integration/docs
  Vue d'ensemble: https://docs.cloud.google.com/application-integration/docs/overview
  Concepts: https://docs.cloud.google.com/application-integration/docs/concepts
  Déclencheurs et tâches: https://docs.cloud.google.com/application-integration/docs/all-triggers-tasks
  Versions d'une intégration: https://docs.cloud.google.com/application-integration/docs/integration-versions
  Fonctions de mappage: https://docs.cloud.google.com/application-integration/docs/data-mapping-functions-reference
  Utiliser les connecteurs: https://docs.cloud.google.com/application-integration/docs/using-integration-connectors
  Integration Connectors: https://docs.cloud.google.com/integration-connectors/docs/overview
  Activer le service: https://docs.cloud.google.com/application-integration/docs/setup-application-integration
  API REST: https://docs.cloud.google.com/application-integration/docs/reference/rest
  Quotas et limites: https://docs.cloud.google.com/application-integration/docs/quotas
  Tarifs: https://cloud.google.com/application-integration/pricing
  Notes de version: https://docs.cloud.google.com/application-integration/docs/release-notes
---

## Ce que c'est

Plateforme d'intégration d'applications (*iPaaS*) : on décrit dans un éditeur graphique un enchaînement de tâches qui relient des applications d'entreprise, des SaaS et des services Google Cloud, sans écrire de code ou presque. Le service est sans serveur, régional et s'ajuste seul.

- **Intégration.** L'unité est l'**intégration** : un **déclencheur** en entrée, des **tâches** reliées par des **arêtes** porteuses de conditions, et des **variables** qui circulent entre elles. Les *fourches* et *jonctions* décrivent ce qui part en parallèle et ce qui attend le reste.
- **Déclencheurs.** Appel d'API, planification, message [Pub/Sub](#pubsub), tâche [Cloud Scheduler](#cloud-scheduler), déclencheur privé, capteur d'erreur, et une famille de déclencheurs d'événements portés par les connecteurs : Kafka, IBM MQ, RabbitMQ, Solace, TIBCO EMS, SAP, ServiceNow, Salesforce, Jira, HubSpot, Zendesk, HL7, webhook.
- **Tâches.** Trois familles. Les tâches d'**intégration** structurent le flux : mappage de données, boucles `for` séquentielles ou parallèles, `while`, appel d'une autre intégration, suspension, minuterie, validation humaine, `Send Email`, `Call REST Endpoint`, JavaScript. Les tâches **Google Cloud** appellent directement un service : Cloud Run functions, Dataflow, Firestore, Secret Manager, Document AI, Vertex AI, Sheets, Drive, et `Workflows - Execute`. La tâche **Connectors** passe par Integration Connectors.
- **Mappage de données.** Un éditeur visuel relie variables d'entrée et de sortie et applique des fonctions de transformation — conversion JSON, extraction de propriété, manipulation de chaînes, dates — sans code intermédiaire.
- **Connecteurs.** Integration Connectors fournit le catalogue de connexions vers les bases, les SaaS et les applications d'entreprise. Une **connexion** se matérialise par des **nœuds** — des répliques qui traitent les transactions — que l'on ajoute quand le volume monte, et qui constituent l'essentiel de la facture.
- **Versions.** Une intégration se développe en versions : brouillon modifiable à plusieurs, puis publication. Une version publiée continue de tourner pendant qu'on prépare la suivante.
- **Exploitation.** Journal d'exécution par intégration, métriques dans Cloud Monitoring, journalisation locale des variables, fédération d'identité pour l'accès des utilisateurs, et assistance de Gemini pour construire une intégration à partir d'une description en langage naturel.
- **Facturation** sur trois axes : les **exécutions** (0,50 $ par millier, qu'elles réussissent ou non), les **nœuds de connexion** actifs (0,35 $ l'heure pour un connecteur Google, 0,70 $ pour un connecteur tiers) et le **volume de données** traité. Un palier gratuit couvre 400 exécutions, 20 Gio par mois et les deux premiers nœuds vers des services Google ; un abonnement existe pour les usages réguliers.

> [!WARNING]
> Un nœud de connexion est facturé tant qu'il existe, pas seulement quand l'intégration tourne. Une connexion oubliée après une maquette coûte plusieurs centaines de dollars par an : il faut la suspendre ou la supprimer.

## À quoi ça sert

- Relier un CRM, un ERP et une base interne sans écrire ni héberger de code de connexion : le connecteur gère l'authentification, la pagination et le format.
- Automatiser un processus métier qui traverse plusieurs applications — création d'un compte client, routage d'un ticket, suivi d'une commande — avec validation humaine quand il en faut une.
- Déverser dans [BigQuery](#bigquery) des données d'applications SaaS, à l'événement ou selon un horaire.
- Ouvrir la construction des flux à des équipes qui ne développent pas, tout en gardant les exécutions visibles et journalisées.

**À éviter** pour orchestrer des services que l'on écrit soi-même : [Workflows](#workflows) coûte une fraction du prix, se versionne dans le dépôt et se relit comme du code. À éviter aussi pour un transfert de données volumineux, qui relève de [Dataflow](#dataflow) ou de [Cloud Data Fusion](#cloud-data-fusion), et pour un simple appel d'API à heure fixe, où [Cloud Scheduler](#cloud-scheduler) suffit.

## Alternatives en logiciel libre

- **Apache Camel** (Apache 2.0) : le catalogue de connecteurs de référence, plus de trois cents composants et les *Enterprise Integration Patterns* ; **Camel K** le déploie sur Kubernetes.
- **Apache NiFi** (Apache 2.0) : flux de données construits dans une interface graphique, avec traçabilité de chaque enregistrement — le plus proche de l'éditeur visuel.
- **Node-RED** (Apache 2.0) : enchaînement de nœuds par glisser-déposer, léger, très fourni en connecteurs communautaires.
- **Kestra** (Apache 2.0) : orchestration déclarative en YAML avec une interface web, à mi-chemin entre l'intégration et l'ordonnancement.
- **Activepieces** (MIT pour l'édition communautaire) : automatisation entre SaaS par interface graphique, l'équivalent le plus direct côté métier.
- **Debezium** (Apache 2.0) : pour la partie « réagir aux changements d'une base applicative » que couvrent certains déclencheurs de connecteur.
