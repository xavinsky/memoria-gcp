---
title: Le Well-Architected Framework de Google
subgroup: Repères
---

Le [Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) est le référentiel de conception de Google Cloud : des principes et des recommandations, validés par des experts de Google, pour construire et exploiter des charges **sûres, fiables, performantes, économes et durables**. Il vaut pour une application née dans le cloud comme pour une charge migrée, hybride ou multicloud. Cette page en donne la structure et renvoie, pilier par pilier, vers les sections du site qui l'appliquent ; elle ne remplace pas la lecture des recommandations elles-mêmes.

## Structure

- **Cinq principes fondamentaux**, communs à tous les piliers.
- **Six piliers**, un par exigence non fonctionnelle : excellence opérationnelle ; sécurité, confidentialité et conformité ; fiabilité ; optimisation des coûts ; optimisation des performances ; durabilité. Chacun se découpe en principes, puis en recommandations.
- **Deux perspectives** transverses, qui relisent cinq piliers (tous sauf la durabilité) pour un domaine : **IA et ML**, **services financiers** (FSI). Leurs recommandations déclinent celles des piliers : la perspective FSI demande par exemple une reprise d'activité qui respecte la résidence des données, ce qui applique le principe d'objectifs réalistes du pilier fiabilité.

La page [What's new](https://docs.cloud.google.com/architecture/framework/whats-new) liste les mises à jour ; chaque page porte sa date de dernière relecture.

## Principes fondamentaux

- **Concevoir pour le changement** : livrer de petites modifications souvent, mesurer la livraison par les indicateurs DORA.
- **Documenter l'architecture** : une documentation claire et tenue à jour, avec l'historique des décisions, par exemple sous forme d'[ADR](https://docs.cloud.google.com/architecture/architecture-decision-records) rangés près du code.
- **Simplifier et préférer les services gérés** : partir d'un produit minimal, résister à la sur-ingénierie.
- **Découpler** : des composants indépendants, que l'on met à jour, sécurise, surveille et dimensionne séparément.
- **Viser le sans état** : l'état dans un stockage partagé, pour monter en charge et redémarrer vite.

## Les six piliers

**Excellence opérationnelle** — déployer, exploiter, surveiller et gérer les charges.
- Préparer l'exploitation : SLO, surveillance, tests de performance et planification de capacité.
- Gérer les incidents et les problèmes : observabilité, procédures de réponse, rétrospectives.
- Automatiser le changement ; gérer et optimiser les ressources ; améliorer en continu.

**Sécurité, confidentialité et conformité**
- Sécurité dès la conception, et *zero trust* : aucun accès sans vérification continue.
- Sécurité en amont (*shift left*) dans la chaîne logicielle ; défense préventive, fondée sur le renseignement sur les menaces.
- Utiliser l'IA de façon sûre et responsable, et l'IA au service de la sécurité.
- Respecter les exigences réglementaires, de conformité et de confidentialité.

**Fiabilité**
- Définir la fiabilité par l'expérience utilisateur et se fixer des objectifs réalistes.
- Redondance, montée en charge horizontale, dégradation progressive, détection des pannes par l'observabilité.
- Tester la reprise après panne et après perte de données ; mener des postmortems approfondis.

**Optimisation des coûts**
- Aligner les dépenses sur la valeur métier, et diffuser une culture de la conscience des coûts.
- N'allouer et ne payer que ce qui sert ; optimiser en continu. Le pilier suit les principes FinOps.

**Optimisation des performances**
- Planifier l'allocation des ressources ; tirer parti de l'élasticité.
- Concevoir en modules ; surveiller et améliorer les performances en continu.

**Durabilité**
- Choisir des régions à énergie bas carbone ; optimiser l'usage des ressources, des données et du stockage.
- Rendre efficaces le logiciel et les charges IA et ML.
- Mesurer en continu, diffuser une culture de la durabilité, suivre les référentiels du secteur.

## Où ce site applique chaque pilier

| Pilier | Plateforme | Autres onglets | Fiches repères |
|---|---|---|---|
| **Excellence opérationnelle** | [Fondations en code](#fondations-en-code), [Observabilité](#observabilite), [Alertes et incidents](#alertes-et-incidents), [Diagnostiquer Dataflow](#diagnostiquer-dataflow), [Quotas et limites](#quotas-et-limites) | [Chaîne CI/CD](#chaine-cicd), [Cloud Deploy](#cloud-deploy-livrer), [Choisir un outil IaC](#choisir-un-outil-iac), [Orchestration](#orchestration) | [Cloud Monitoring](#cloud-monitoring), [Cloud Logging](#cloud-logging) |
| **Sécurité** | [Hiérarchie des ressources](#hierarchie-des-ressources), [IAM](#iam-bonnes-pratiques), [Identités des utilisateurs](#identites-des-utilisateurs), [Authentifier un appel](#authentifier-un-appel), [Chiffrement](#chiffrement), [Périmètres VPC-SC](#perimetres-vpc-sc), [Données sensibles](#donnees-sensibles-et-gouvernance), [Détection et conformité](#detection-et-conformite) | [Sécuriser la chaîne](#securiser-la-chaine), [Déployer sans clé](#deployer-sans-cle), [Évaluer et sécuriser une application générative](#evaluer-et-securiser) | [Security Command Center](#security-command-center), [Assured Workloads](#assured-workloads) |
| **Fiabilité** | [Régions, zones et reprise](#regions-zones-resilience), [Choisir un load balancer](#choisir-un-load-balancer), [Alertes et incidents](#alertes-et-incidents), [Quotas et limites](#quotas-et-limites) | [Choisir une base](#choisir-une-base), [Streaming](#streaming), [Cloud Deploy](#cloud-deploy-livrer) | [Backup and DR](#backup-and-dr), [Cloud Load Balancing](#cloud-load-balancing) |
| **Coûts** | [Facturation et budgets](#facturation-et-budgets), [Optimiser les coûts](#optimiser-les-couts), [Choisir le calcul](#choisir-le-calcul) | [Organiser BigQuery](#organiser-bigquery), [Classes Cloud Storage](#cloud-storage-classes), [Choisir un moteur](#choisir-un-moteur) | [Cost Management](#cost-management), [Active Assist](#active-assist) |
| **Performances** | [Choisir le calcul](#choisir-le-calcul), [Concevoir le réseau](#concevoir-le-reseau), [Choisir un load balancer](#choisir-un-load-balancer), [Diagnostiquer Dataflow](#diagnostiquer-dataflow) | [Choisir une base](#choisir-une-base), [Organiser BigQuery](#organiser-bigquery) | [Cloud Profiler](#cloud-profiler), [Cloud Trace](#cloud-trace) |
| **Durabilité** | [Régions, zones et reprise](#regions-zones-resilience) (choix de la région), [Optimiser les coûts](#optimiser-les-couts) | [Classes Cloud Storage](#cloud-storage-classes) | [Carbon Footprint](#carbon-footprint) |
| **Perspective IA et ML** | — | [Choisir une approche ML](#choisir-une-approche-ml), [Entraîner et servir](#entrainer-et-servir), [MLOps](#mlops), [Évaluer et sécuriser](#evaluer-et-securiser), [Déployer un agent](#deployer-un-agent) | [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) |
| **Perspective services financiers** | [Régions, zones et reprise](#regions-zones-resilience), [Chiffrement](#chiffrement) | — | [Assured Workloads](#assured-workloads) |

## S'en servir

- **Revue de conception.** Avant une mise en production, dérouler les principes de chaque pilier comme une liste de questions sur l'architecture proposée. Chaque pilier et chaque perspective existe en version une page (*printable*), exportable en PDF, pratique pour une revue.
- **Arbitrages explicites.** Les piliers se contredisent : une architecture multirégionale gagne en fiabilité et perd en coût. Consigner l'arbitrage dans un ADR plutôt que de l'oublier.
- **Contrôles continus.** Une partie des recommandations se vérifie en continu : [Active Assist](#active-assist) classe ses propositions selon six axes calqués sur les piliers (coût, sécurité, performance, fiabilité, facilité d'exploitation, durabilité) ; [Security Command Center](#security-command-center) signale les écarts de configuration ; [Cost Management](#cost-management) et [Carbon Footprint](#carbon-footprint) donnent les mesures des piliers coûts et durabilité.
- **Socle commun.** Les recommandations de sécurité et d'exploitation se posent une fois pour toute l'organisation, dans la [zone d'atterrissage](https://docs.cloud.google.com/architecture/landing-zones) et le [blueprint des fondations d'entreprise](https://docs.cloud.google.com/architecture/blueprints/security-foundations) : voir [Hiérarchie des ressources](#hierarchie-des-ressources) et [Fondations en code](#fondations-en-code).

## Responsabilité partagée, destin partagé

Le modèle de **responsabilité partagée** répartit la sécurité entre Google et le client selon le type de service. Google reste toujours responsable de l'infrastructure physique et du réseau sous-jacent ; le client, toujours de ses **politiques d'accès** et de ses **données**.

| Modèle | Exemples | Part du client |
|---|---|---|
| IaaS | Compute Engine, Cloud Storage, Cloud VPN, Cloud Load Balancing | L'essentiel : système, réseau, application, accès, données |
| PaaS | GKE, BigQuery, App Engine | Contrôles applicatifs et IAM partagés avec Google ; sécurité des données |
| SaaS, fonctions | Google Security Operations, Cloud Run functions | Contrôle d'accès et données confiées au service |

La résidence des données et les référentiels sectoriels (PCI DSS, HIPAA, RGPD) ajoutent leurs propres partages : il faut savoir quels contrôles sont hérités de Google, et donc présentables à un auditeur, et lesquels restent à configurer.

Google y ajoute le **destin partagé** (*shared fate*) : la plupart des incidents viennent d'erreurs de configuration, donc le fournisseur s'engage à fournir une configuration sûre par défaut. Concrètement : le blueprint des fondations d'entreprise et d'autres *blueprints* en IaC, les guides de zone d'atterrissage, le Well-Architected Framework lui-même, des produits de gouvernance ([Assured Workloads](#assured-workloads), [Security Command Center](#security-command-center), règles d'administration, Confidential Computing), et le [Risk Protection Program](https://cloud.google.com/security/products/risk-protection-program), qui partage une évaluation de posture avec des assureurs cyber. Source : [*Shared responsibilities and shared fate on Google Cloud*](https://docs.cloud.google.com/architecture/framework/security/shared-responsibility-shared-fate).

## Alternatives en logiciel libre

- **Prowler** (Apache 2.0) : audit de configuration multi-cloud, dont Google Cloud, avec des contrôles CIS et des référentiels de conformité ; la vérification outillée du pilier sécurité.
- **Cloud Custodian** (Apache 2.0) : règles de gouvernance écrites en YAML, qui détectent et corrigent les écarts (ressources non étiquetées, inactives, exposées) ; un contrôle continu couvrant coûts, sécurité et exploitation.
- **Open Policy Agent** (Apache 2.0) et **Checkov** (Apache 2.0) : politiques en code appliquées au plan IaC ou aux manifestes Kubernetes, pour qu'une revue d'architecture devienne un test automatique.
- **OpenCost** (Apache 2.0) : répartition du coût Kubernetes par espace de noms et par charge ; la mesure du pilier coûts dans un cluster.
- **LitmusChaos** et **Chaos Mesh** (Apache 2.0) : injection de pannes pour éprouver le pilier fiabilité, en particulier le test de reprise.
- **Kepler** (Apache 2.0) et **Cloud Carbon Footprint** (Apache 2.0) : estimation de la consommation électrique des conteneurs et de l'empreinte carbone d'un compte cloud, pour le pilier durabilité.
