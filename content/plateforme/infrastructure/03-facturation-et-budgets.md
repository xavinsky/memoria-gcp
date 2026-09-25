---
title: Facturation, budgets et plafonds de coût
subgroup: Fondations
---

La dépense Google Cloud se maîtrise à trois niveaux, qui n'ont ni la même garantie ni le même délai. Un **budget** compare la dépense à un montant et prévient : il n'arrête rien, et il réagit avec plusieurs heures de retard. Une **automatisation** branchée sur ses messages Pub/Sub peut arrêter des ressources, avec le même retard. Seuls les **quotas** et les limites de mise à l'échelle bornent la consommation avant qu'elle ait lieu. Le plafond de dépense (*spend cap*) [!PREVERSION] se situe entre les deux : il met un service en pause, mais sur des coûts estimés, donc pas instantanément.

![Chaîne d'alerte de coût : de l'usage à l'action automatique](../../svg/budget-alerte-action.svg)

## Compte de facturation et rôles

- **Compte de facturation Cloud Billing** : il suit tous les coûts et remises des projets qui lui sont liés, dans une seule devise, et porte les budgets, rapports et exports (voir [Cost Management](#cost-management)). Un projet est lié à un seul compte ; sans compte actif, ses services Google Cloud s'arrêtent, même gratuits.
- **Profil de paiement Google** (*payments profile*) : objet de niveau Google, géré dans le centre de paiements et partagé avec les autres services Google (Ads, Workspace). Il porte le nom, l'adresse, le numéro fiscal et les moyens de paiement. Le compte est en libre-service (*self-serve*, payé par carte ou prélèvement) ou sur facture (*invoiced*, sous conditions d'éligibilité).
- **Sous-comptes** : réservés aux revendeurs, pour isoler les coûts de chaque client sous un compte parent qui paie l'ensemble.
- **Verrouillage du lien** projet-compte : empêche de délier le projet ou de le rattacher à un autre compte sans déverrouiller d'abord. Il ne protège pas contre la fermeture ou la suspension du compte lui-même.

| Rôle (console) | Nom IAM | Accordé sur | Ce qu'il permet |
|---|---|---|---|
| Billing Account Creator | `roles/billing.creator` | Organisation | Créer des comptes en libre-service ; à donner à très peu de monde |
| Billing Account Administrator | `roles/billing.admin` | Organisation, compte | Tout : paiements, exports, liaison des projets, droits des autres |
| Billing Account Costs Manager | `roles/billing.costsManager` | Organisation, compte | Budgets, lecture des coûts, export vers BigQuery ; ni tarifs négociés ni liaison de projets |
| Billing Account Viewer | `roles/billing.viewer` | Organisation, compte | Lecture des coûts et des paiements : le rôle de l'équipe finance |
| Billing Account User | `roles/billing.user` | Organisation, compte | Rattacher des projets au compte, combiné à un rôle sur le projet |
| Project Billing Manager | `roles/billing.projectManager` | Organisation, dossier, projet | Lier ou délier le projet, sans aucun droit sur ses ressources |
| Project Billing Costs Manager | `roles/billing.projectCostsManager` | Organisation, compte | Rapports, budgets et FinOps hub limités aux projets dont on voit les coûts |

Lier un projet demande **Billing Account User** sur le compte et **Project Billing Manager** (ou Propriétaire) sur le projet. Le délier ne demande que l'un des deux : Administrator sur le compte, ou Project Billing Manager sur le projet. La hiérarchie qui porte ces rôles est décrite dans [Hiérarchie des ressources](#hierarchie-des-ressources).

## Attribuer la dépense : étiquettes et balises

- **Étiquettes** (*labels*) : paires clé-valeur posées sur les projets et les ressources. L'export les restitue dans `labels` (ressource) et `project.labels` (projet) ; GKE ajoute des étiquettes système (`goog-k8s-cluster-name`, `k8s-namespace`) quand la répartition des coûts GKE est activée dans l'export détaillé.
- **Balises** (*tags*) : définies au niveau de l'organisation, avec des valeurs contrôlées et **héritées** dans la hiérarchie. L'export les restitue dans `tags`, avec un indicateur `inherited`.
- Rapports, budgets et export regroupent ou filtrent sur ces clés. Un budget ne filtre que sur **une** paire clé-valeur d'étiquette.
- Rien n'est rétroactif : une dépense passée sans étiquette le reste. Fixer les clés obligatoires (`equipe`, `env`, `produit`) et les poser dans le code d'infrastructure dès la création (voir [Fondations en code](#fondations-en-code)).

## Export vers BigQuery

| Export | Table | Contenu | À utiliser pour |
|---|---|---|---|
| Coût d'usage standard | `gcp_billing_export_v1_…` | Compte, facture, service, SKU, projet, étiquettes, lieu, coût, crédits | Tendances, refacturation par équipe |
| Coût d'usage détaillé | `gcp_billing_export_resource_v1_…` | Le standard plus le nom de chaque ressource (VM, disque) | Trouver la ressource qui coûte |
| Tarifs | `cloud_pricing_export` | Prix catalogue et négociés par SKU, paliers | Recalculer une facture, simuler |
| [!PREVERSION] FOCUS | `gcp_billing_export_focus_…` | Coûts au format ouvert FOCUS de la FinOps Foundation | Comparer plusieurs fournisseurs |
| [!PREVERSION] Métadonnées CUD | table quotidienne | Engagements souscrits | Suivre la couverture des engagements |

- **Activer dès la création du compte**, dans un projet FinOps dédié. Avec un dataset multirégional (`EU` ou `US`), l'export reprend le mois en cours et le précédent (jusqu'à cinq jours de rattrapage) ; avec un dataset régional, seulement à partir de l'activation. Les tarifs ne sont jamais rétroactifs, et changer de dataset ne recopie pas l'historique.
- Le chargement est gratuit ; stockage et requêtes sont facturés comme toute table BigQuery.
- Les crédits (remises, palier gratuit, promotions) sont des montants **négatifs** dans le tableau `credits` : le coût net est `cost` plus leur somme.

```sql
-- Coût net du mois en cours, par projet et par équipe
SELECT
  project.id AS projet,
  (SELECT value FROM UNNEST(labels) WHERE key = "equipe") AS equipe,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS cout_net
FROM `PROJECT_ID.DATASET.gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX`
WHERE invoice.month = FORMAT_DATE("%Y%m", CURRENT_DATE())
GROUP BY projet, equipe
ORDER BY cout_net DESC;
```

## Budgets et alertes

- **Portée** : tout le compte, des organisations, dossiers ou projets, des services, une étiquette. Période mensuelle, trimestrielle, annuelle ou personnalisée. Montant fixe, ou égal à la dépense de la période précédente.
- **Seuils** en pourcentage, par défaut 50, 90 et 100 % de la dépense **réelle**. Un seuil sur la dépense **prévue** prévient dès que la projection de fin de période dépasse le montant ; il n'existe pas pour une période personnalisée.
- **Destinataires** : par défaut les titulaires de `roles/billing.admin` et `roles/billing.user` du compte ; les propriétaires du projet pour un budget limité à un projet ; jusqu'à cinq canaux de notification [Cloud Monitoring](#cloud-monitoring) ; un sujet [Pub/Sub](#pubsub).
- **Retard** : la première notification peut prendre plusieurs heures après la création, et les coûts remontent avec un décalage sur l'usage. La documentation recommande de fixer le montant **sous les fonds réellement disponibles**. Un budget mensuel continue de compter les coûts arrivés pendant les deux premiers jours du mois suivant.
- **Messages Pub/Sub** : envoyés **plusieurs fois par jour** avec l'état courant, pas seulement au franchissement d'un seuil. Attributs `billingAccountId`, `budgetId`, `schemaVersion` ; données JSON `costAmount`, `budgetAmount`, `costIntervalStart`, `currencyCode`, et `alertThresholdExceeded` ou `forecastThresholdExceeded` quand un seuil est dépassé.

Budget d'un projet bac à sable, avec notifications sur un sujet du projet FinOps :

```python
import pulumi
import pulumi_gcp as gcp

compte = pulumi.Config().require("billingAccount")  # XXXXXX-XXXXXX-XXXXXX
projet = gcp.organizations.get_project(project_id="PROJECT_ID")

sujet = gcp.pubsub.Topic("budget-alertes", project="FINOPS_PROJECT")

gcp.billing.Budget("bac-a-sable",
    billing_account=compte,
    display_name="Bac à sable PROJECT_ID",
    budget_filter={
        "projects": [f"projects/{projet.number}"],
        "calendar_period": "MONTH",
    },
    amount={"specified_amount": {"currency_code": "EUR", "units": "200"}},  # devise du compte
    threshold_rules=[
        {"threshold_percent": 0.5},
        {"threshold_percent": 0.9},
        {"threshold_percent": 1.0},
        {"threshold_percent": 1.0, "spend_basis": "FORECASTED_SPEND"},
    ],
    all_updates_rule={"pubsub_topic": sujet.id, "schema_version": "1.0"},
)
```

L'identité qui exécute Pulumi doit pouvoir modifier la stratégie IAM du sujet (`pubsub.topics.setIamPolicy`) : Cloud Billing s'y accorde le droit de publier. Avec des identifiants utilisateur, l'API Budget répond 403 tant que le fournisseur n'a pas de projet de quota : `pulumi config set gcp:billingProject FINOPS_PROJECT` et `pulumi config set gcp:userProjectOverride true`.

## Réagir automatiquement

| Réaction | Mécanisme | Effet | À réserver à |
|---|---|---|---|
| **Prévenir** | Pub/Sub → fonction → Slack, ticket (voir [Notifications et tickets](#notifications-tickets)) | Rien ne s'arrête | Tous les budgets |
| **Réduire** | La fonction arrête des VM, abaisse le nombre maximal d'instances, vide un pool de nœuds | Service dégradé, données conservées | Développement, recette, lots |
| **Couper la facturation** | La fonction délie le projet de son compte | Tous les services du projet s'arrêtent, gratuits compris ; des ressources peuvent être supprimées sans retour possible | Bac à sable, formation, projet jetable |
| [!PREVERSION] **Plafond de dépense** | Budget de type *Spend cap enforcement*, un projet et un service éligible, période mensuelle | Nouvel usage du service mis en pause jusqu'à levée manuelle ; ressources et données conservées ; coûts fixes toujours facturés | Gemini API, [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform), [Cloud Run](#cloud-run), Cloud Run functions |

La documentation de Cloud Billing publie l'exemple « couper la facturation » en Node.js et en Python. Version réduite, avec un mode simulation à garder tant que le budget n'a pas été testé :

```python
import base64
import json

import functions_framework
from google.cloud import billing_v1

PROJET = "projects/PROJECT_ID"   # projet surveillé, distinct du projet de la fonction
SIMULATION = True

client = billing_v1.CloudBillingClient()


@functions_framework.cloud_event
def couper_facturation(cloud_event):
    budget = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    if budget["costAmount"] <= budget["budgetAmount"]:
        return  # message périodique, budget respecté
    if not client.get_project_billing_info(name=PROJET).billing_enabled:
        return  # déjà coupé : le même état revient plusieurs fois par jour
    print(f"Dépassement : {budget['costAmount']} > {budget['budgetAmount']} {budget['currencyCode']}")
    if not SIMULATION:
        client.update_project_billing_info(
            name=PROJET,
            project_billing_info=billing_v1.ProjectBillingInfo(billing_account_name=""),
        )
```

```bash
# requirements.txt : functions-framework, google-cloud-billing
gcloud functions deploy couper-facturation --gen2 --runtime=python314 \
  --region=REGION --source=. --entry-point=couper_facturation \
  --trigger-topic=TOPIC --project=FINOPS_PROJECT
# Délier le projet suffit : pas besoin d'administrer le compte de facturation
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SA_EMAIL --role=roles/billing.projectManager
```

L'exemple de Google accorde `roles/billing.admin` sur le compte au compte de service ; **Project Billing Manager** sur le seul projet surveillé suffit à le délier. La réactivation est manuelle : relier le projet, puis redémarrer les services qui ne repartent pas seuls, avec jusqu'à 24 heures de délai.

## Plafonds durs : quotas et limites de mise à l'échelle

Un quota refuse la consommation au lieu de la constater. C'est la seule protection qui ne dépend pas du délai de facturation (voir [Cloud Quotas](#cloud-quotas) et [Quotas et limites](#quotas-et-limites)).

| Levier | Où | Effet |
|---|---|---|
| `QueryUsagePerDay`, `QueryUsagePerUserPerDay` | Quotas de l'API [BigQuery](#bigquery) | Refus `usageQuotaExceeded` au-delà d'un volume lu par jour, par projet ou par utilisateur ; tarification à la demande uniquement ; valeurs par défaut 200 Tio par projet, illimité par utilisateur ; approximatif |
| `maximum_bytes_billed` | Chaque requête BigQuery | La requête échoue avant lecture, sans frais, si elle dépasse le plafond |
| Taille maximale de réservation | Éditions BigQuery | L'autoscaling ne dépasse pas le nombre de slots fixé |
| Nombre maximal d'instances | Service Cloud Run | 100 par révision par défaut, 3 suggéré par Google pour démarrer ; dépassement bref possible lors d'un pic |
| Minimum et maximum de nœuds | Pools [GKE](#gke), limites du provisionnement automatique | Le cluster ne grossit pas au-delà |
| Quotas de vCPU et de GPU par région | Compute Engine, par préférence de quota | Création de VM refusée au-delà ; laisser des valeurs basses dans les bacs à sable |

## Pièges

- **Prendre un budget pour un plafond.** Un budget classique (*alerts-only*) ne bloque rien, et une automatisation qui s'y branche agit avec des heures de retard. Pour une somme à ne jamais dépasser : quotas, limites d'instances, plafond de dépense sur les services éligibles, et montant fixé sous les fonds disponibles.
- **Mettre la fonction dans le projet qu'elle coupe.** Elle s'arrête avec lui, sujet Pub/Sub compris. Sujet et fonction vont dans un projet FinOps séparé.
- **Oublier le verrouillage.** Un projet verrouillé sur son compte ne peut pas être délié : la fonction échoue. Les deux se combinent mal, choisir par projet.
- **Traiter chaque message comme un franchissement.** Les messages arrivent plusieurs fois par jour, et `costAmount` repart de zéro au début de chaque période : la fonction doit être idempotente et ne rien réactiver d'elle-même.
- **Oublier les crédits.** Les seuils sont calculés après remises et crédits : un crédit promotionnel qui s'épuise fait monter la dépense sans hausse d'usage. Le plafond de dépense, lui, compte en coût brut.
- **Politique d'organisation `iam.allowedPolicyMemberDomains`.** Elle empêche Cloud Billing de publier sur le sujet : exempter le projet FinOps.
- **Activer l'export trop tard ou en région.** L'historique manquant ne se récupère pas.

## Alternatives en logiciel libre

- **OpenCost** (Apache 2.0) : allocation des coûts Kubernetes par espace de noms et par étiquette, avec import de la facture cloud ; la vue par équipe que donnent ici les étiquettes et l'export.
- **Cloud Custodian** (Apache 2.0) : règles déclaratives, exécutées périodiquement ou sur événement, qui étiquettent, arrêtent ou suppriment des ressources Google Cloud ; la réaction automatique écrite en YAML plutôt que dans une fonction.
- **Infracost** (Apache 2.0) : chiffre le coût d'un plan Terraform ou OpenTofu avant application et l'affiche dans la *merge request* ; la prévention, là où le budget constate.
- **Grafana** (AGPL v3) : tableaux de bord et règles d'alerte sur les tables d'export de facturation, avec les mêmes canaux que le reste de l'exploitation.
- **Kubernetes `ResourceQuota`** (Apache 2.0) : plafond dur de CPU, de mémoire et d'objets par espace de noms ; l'équivalent des quotas pour un cluster partagé.
