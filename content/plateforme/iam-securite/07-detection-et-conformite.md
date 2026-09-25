---
title: Détection et conformité
subgroup: Détection et conformité
---

La détection repose sur trois couches : des **journaux** qui disent qui a fait quoi, des **détecteurs** qui transforment journaux et configurations en résultats, et une **réponse** qui traite ces résultats avant qu'ils ne s'accumulent. Le [plan de fondations d'entreprise](https://docs.cloud.google.com/architecture/blueprints/security-foundations/detective-controls) de l'Architecture Center en fait le socle de toute organisation : journaux agrégés dans un projet dédié, [Security Command Center](#security-command-center) activé, résultats exportés vers les outils du centre opérationnel de sécurité (SOC). La conformité s'appuie sur les mêmes briques, plus les contrôles sur l'accès du fournisseur.

![Chaîne de détection et de réponse](../../svg/detection-reponse.svg)

## Quel outil pour quelle question

| Question | Réponse | Condition |
|---|---|---|
| Qui a modifié cette ressource, ce rôle, ce pare-feu ? | Journaux d'audit **activité d'administration** | Toujours écrits |
| Qui a lu cette table, cet objet, ce secret ? | Journaux d'audit **accès aux données** | À activer, sauf pour BigQuery |
| Bucket public, clé de compte de service ancienne, pare-feu ouvert ? | Security Health Analytics, dans Security Command Center | Niveau Premium |
| Compte compromis, minage, exfiltration, octroi IAM anormal ? | Event Threat Detection, Virtual Machine Threat Detection | Niveau Premium |
| Shell inattendu ou binaire ajouté dans un conteneur ? | Container Threat Detection (GKE), Cloud Run Threat Detection | Niveau Premium |
| La configuration s'écarte-t-elle de la référence ? | Posture de sécurité, Compliance Manager | Premium ; Compliance Manager réduit à un cadre en Standard |
| Corréler avec les postes, le réseau interne, les SaaS ? | [Google Security Operations](#google-security-operations) (SIEM et SOAR) | Offre séparée |
| Le personnel de Google a-t-il accédé à nos données ? | Access Transparency ; Access Approval pour l'autoriser au cas par cas | Organisation |
| FedRAMP, ITAR, frontière de données de l'UE ? | [Assured Workloads](#assured-workloads) | Dossier dédié |
| Certifications du fournisseur (ISO/IEC 27001, SOC 2) ? | [Compliance reports manager](https://cloud.google.com/security/compliance/compliance-reports-manager) | Accès libre, certains documents après connexion |

## Journaux d'audit

| Journal | Contenu | Écrit par défaut | Stockage | Coût |
|---|---|---|---|---|
| **Activité d'administration** | Appels qui modifient la configuration ou les métadonnées : création de VM, changement d'IAM | Toujours, ni désactivable ni excluable | `_Required`, 400 jours, non modifiable | Aucun |
| **Événements système** | Actions de Google Cloud sur la configuration, sans utilisateur : autoscaling d'un groupe d'instances | Toujours, ni désactivable ni excluable | `_Required`, 400 jours | Aucun |
| **Accès aux données** | Lecture de configuration (`ADMIN_READ`), lecture et écriture des données (`DATA_READ`, `DATA_WRITE`) | Non, sauf BigQuery | `_Default`, 30 jours par défaut | Ingestion facturée, volume élevé |
| **Refus de règle** | Accès refusé par une règle de sécurité : [VPC Service Controls](#perimetres-vpc-sc), règles d'administration | Oui, non désactivable, mais excluable | `_Default` | Ingestion facturée |

Les **journaux Access Transparency** (`cloudaudit.googleapis.com%2Faccess_transparency`) forment une cinquième famille : ils enregistrent les accès du personnel de Google, avec le motif, la localisation et la fonction de l'intervenant, là où les journaux d'audit enregistrent ceux des principaux de l'organisation. Access Transparency est un contrôle par défaut des organisations ; vérifier son état dans **IAM > Paramètres**.

Les journaux d'accès aux données s'activent par une configuration d'audit IAM, au niveau de l'organisation, d'un dossier ou d'un projet ; un niveau inférieur ne peut pas désactiver ce qu'un parent a activé. Les activer d'abord sur les services qui portent des données sensibles (Cloud Storage, Cloud SQL, Secret Manager, Cloud KMS), en exemptant au besoin les comptes de service des traitements massifs. Plusieurs détecteurs d'Event Threat Detection s'appuient sur ces journaux : sans eux, ils ne voient rien.

## Centraliser les journaux

Chaque projet garde ses journaux 30 jours dans `_Default` et ses journaux d'audit d'administration 400 jours dans `_Required`. Pour une enquête, il faut plus long et en un seul endroit : un **puits agrégé** au niveau de l'organisation ou d'un dossier (voir [Hiérarchie des ressources](#hierarchie-des-ressources)) route les journaux de toute l'arborescence vers un **projet de journaux** central.

- **Bucket de journaux** avec Log Analytics : recherche en SQL et jeu de données BigQuery lié, rétention de 1 à 3 650 jours, verrouillage possible (irréversible).
- **Cloud Storage** pour l'archive réglementaire longue, avec une politique de conservation verrouillée.
- **Pub/Sub** vers un SIEM tiers ; Google SecOps ingère directement les données Google Cloud, sans ce détour.
- **Non interceptant** par défaut : les projets gardent leur copie. Un puits **interceptant** empêche les puits des niveaux inférieurs de recevoir les entrées qu'il capte, sauf `_Required` : les équipes perdent alors leurs journaux locaux.

```python
import pulumi_gcp as gcp

ORG_ID = "ORGANIZATION_ID"
LOGS_PROJECT = "PROJECT_ID"  # projet central de journaux

gcp.logging.ProjectBucketConfig("audit-org",
    project=LOGS_PROJECT,
    location="REGION",
    bucket_id="audit-org",
    retention_days=400,
    enable_analytics=True)  # Log Analytics : requêtes SQL

puits = gcp.logging.OrganizationSink("audit-org",
    name="audit-org",
    org_id=ORG_ID,
    include_children=True,
    destination=f"logging.googleapis.com/projects/{LOGS_PROJECT}/locations/REGION/buckets/audit-org",
    filter='logName:"cloudaudit.googleapis.com"')  # audit et Access Transparency

gcp.projects.IAMMember("audit-org-writer",
    project=LOGS_PROJECT,
    role="roles/logging.bucketWriter",
    member=puits.writer_identity)

# Journaux d'accès aux données sur Cloud Storage, pour toute l'organisation
gcp.organizations.IamAuditConfig("audit-storage",
    org_id=ORG_ID,
    service="storage.googleapis.com",
    audit_log_configs=[{"log_type": "DATA_READ"}, {"log_type": "DATA_WRITE"}])
```

## Security Command Center

| Niveau | Ce qu'il apporte | Activation | Facturation |
|---|---|---|---|
| **Standard** | Posture de base sur Google Cloud : détection d'anomalies, actions sensibles, Compliance Manager limité | Organisation | Gratuit |
| **Premium** | Tout Standard, plus Security Health Analytics complet et ses modules personnalisés, Event Threat Detection, Container, VM et Cloud Run Threat Detection, simulations de chemins d'attaque, posture de sécurité, audit de conformité | Projet ou organisation | À l'usage ou par abonnement |
| [!DECONSEILLE] **Enterprise** | Couverture AWS et Azure, fonctions Google SecOps incluses | Organisation | Arrêt le 21 mai 2027, bascule automatique vers Premium |

Source : [niveaux de service](https://docs.cloud.google.com/security-command-center/docs/service-tiers), consultés en septembre 2026.

- **Activer à l'organisation.** Certaines fonctions n'existent qu'à ce niveau : lecture des journaux Google Workspace par Event Threat Detection, écriture des résultats dans Cloud Logging, investigation dans Google SecOps.
- **Un résultat a un propriétaire.** Une notification Pub/Sub par famille de résultats, filtrée sur la gravité, route chaque résultat vers l'équipe qui le corrige ; une règle de mise en sourdine (*mute rule*) documente un risque accepté au lieu de le laisser traîner.
- **Du constat à la prévention.** Un résultat qui revient se traite par une contrainte de règle d'administration, déployée au besoin dans une **posture de sécurité** qui réunit contraintes et détecteurs, pas par une correction manuelle répétée.

```bash
# Résultats actifs critiques de toute l'organisation vers un sujet Pub/Sub
gcloud scc notifications create scc-critiques \
  --organization=ORGANIZATION_ID --location=global \
  --pubsub-topic=projects/PROJECT_ID/topics/scc-critiques \
  --filter='state="ACTIVE" AND severity="CRITICAL"'
```

**Google Security Operations** prend le relais quand un SOC existe : il ingère les journaux Google Cloud et les résultats de Security Command Center à côté de ceux des postes, des pare-feux et des SaaS, applique des détections gérées et des règles YARA-L, et ouvre des cas traités par des *playbooks* SOAR. Sans équipe pour traiter les cas, Security Command Center Premium et des notifications vers la gestion d'incidents suffisent.

## Réponse à incident

1. **Détecter** : un résultat Event Threat Detection signale, par exemple, une clé de compte de service utilisée depuis une adresse inhabituelle.
2. **Notifier** : la notification Pub/Sub déclenche l'alerte d'astreinte ou ouvre un cas SecOps (voir [Notifications et tickets](#notifications-tickets)).
3. **Contenir** : désactiver la clé, retirer le rôle, isoler la VM ; une fonction Cloud Run abonnée au sujet automatise les gestes sans ambiguïté, un *playbook* avec approbation les autres.
4. **Enquêter** : les journaux d'audit centralisés, interrogés en SQL, reconstituent ce que le principal a fait depuis sa première action suspecte.
5. **Empêcher le retour** : contrainte d'administration (par exemple, interdire la création de clés de compte de service), correction de la posture, puis clôture du résultat.

## Conformité

- **Environnement réglementé** : un dossier [Assured Workloads](#assured-workloads) applique un package de contrôles (résidence, personnel, clés) à tout ce qui y est créé. Sa création se décide avant le premier projet : un dossier ne change pas de package.
- **Accès du fournisseur** : Access Transparency journalise, **Access Approval** exige une approbation explicite, signée, notifiée par e-mail ou Pub/Sub, avant tout accès du support aux données. Access Transparency exclut les accès que la loi interdit de signaler, ceux des systèmes automatisés soumis à revue de code, et ceux qu'un rôle IAM accordé par le client autorise (tracés dans les journaux d'audit). Avec [Cloud EKM](#chiffrement), les **Key Access Justifications** donnent le motif de chaque utilisation de la clé externe.
- **Preuve continue** : Compliance Manager déploie des cadres sous forme de contrôles cloud qui détectent les écarts. Le niveau Standard se limite au cadre *Security Essentials* ; Premium ajoute les cadres CIS, NIST SP 800-53, PCI DSS, ISO 27001 ou SOC 2, la collecte des preuves et les rapports d'audit.
- **Preuve du fournisseur** : le Compliance reports manager fournit les certificats ISO/IEC, les rapports SOC et les auto-évaluations de Google Cloud, sans frais.

## Pièges

- **Journaux d'accès aux données désactivés.** À l'incident, personne ne peut dire qui a lu quoi, sauf dans BigQuery. Les activer après coup ne rattrape rien.
- **Rétention de 30 jours.** Une compromission se découvre souvent des mois plus tard : sans puits vers un bucket central à longue rétention, les preuves ont disparu.
- **Filtre d'exclusion trop large.** Exclure les journaux d'accès aux données du puits `_Default` pour réduire la facture fait aussi disparaître la preuve ; les router plutôt vers un bucket dédié à rétention adaptée.
- **Projet de journaux ouvert.** Qui lit le bucket central lit l'activité de toute l'organisation : droits limités à l'équipe sécurité, `roles/logging.privateLogViewer` pour les accès aux données.
- **Téléchargements Cloud Storage en 403.** Avec les journaux d'accès aux données activés sur Cloud Storage, un téléchargement authentifié depuis le navigateur (`storage.cloud.google.com`) échoue, faute de pouvoir journaliser un accès par cookie.
- **Standard pris pour de la détection.** Le niveau Standard ne détecte aucune menace active ; Event Threat Detection et les détecteurs d'exécution demandent Premium.
- **Access Approval sur un service critique.** Chaque intervention du support attend l'approbation : le délai de résolution d'un incident s'allonge d'autant.

## Alternatives en logiciel libre

- **Wazuh** (GPL v2) : SIEM avec agents, règles de corrélation, contrôles de conformité (PCI DSS, RGPD) et réponse active ; couvre à la fois la collecte et une partie de la détection.
- **OpenSearch** avec **Security Analytics** (Apache 2.0) : ingestion de journaux, détection par règles Sigma, corrélation et tableaux de bord, sur un moteur d'indexation à exploiter soi-même.
- **Falco** (Apache 2.0) : détection à l'exécution dans les conteneurs et sur l'hôte à partir des appels système, le pendant de Container Threat Detection.
- **Prowler** (Apache 2.0) : contrôles de posture sur Google Cloud, AWS, Azure et Kubernetes, rattachés à CIS, NIST et PCI DSS ; l'équivalent de Security Health Analytics et des rapports de conformité.
- **Cloud Custodian** (Apache 2.0) : règles déclaratives qui détectent une dérive et appliquent la correction, pour la remédiation automatique.
- **DFIR-IRIS** (LGPL v3) : gestion des cas d'incident, chronologie et preuves, le volet cas de SecOps.
- **Shuffle** (AGPL v3) : orchestration de *playbooks* de réponse, le volet SOAR.
