---
title: Active Assist
subgroup: Exploitation
icon: categories/management-tools
schema:
  size: [760, 330]
  zones:
    - {label: Projet GCP, x: 8, y: 16, w: 590, h: 298}
  nodes:
    gce: {label: Compute Engine, sub: "VM inactive", icon: produits/compute-engine, x: 28, y: 44, w: 170}
    iam: {label: Stratégies IAM, sub: "droits non utilisés", icon: categories/security-identity, x: 28, y: 128, w: 180}
    sql: {label: Cloud SQL, sub: "instance surdimensionnée", icon: produits/cloud-sql, x: 28, y: 212, w: 210}
    hub: {label: FinOps hub, sub: "console", icon: categories/management-tools, x: 290, y: 36, w: 130}
    aa: {label: Recommender, sub: "recommandations, insights", icon: categories/management-tools, focus: true, x: 290, y: 120, w: 210, h: 64}
    bq: {label: BigQuery, sub: "export planifié", icon: produits/bigquery, x: 290, y: 236, w: 160}
    ops: {label: Équipe plateforme, sub: "applique ou ignore", external: true, x: 608, y: 120, w: 150}
  flows:
    - {from: gce, to: aa, text: "Les moteurs observent la consommation réelle sur plusieurs semaines avant de proposer la suppression ou le redimensionnement d'une ressource."}
    - {from: iam, to: aa, text: "Le moteur de stratégies IAM compare les droits accordés aux droits réellement exercés et propose des rôles plus étroits."}
    - {from: sql, to: aa, text: "Chaque produit a ses propres moteurs : inactivité, surdimensionnement, réglages de sécurité et de performance."}
    - {from: aa, to: hub, text: "Les propositions remontent dans la page Active Assist, dans le FinOps hub côté facturation et en contexte dans chaque produit."}
    - {from: aa, to: bq, text: "Un transfert planifié copie recommandations et insights dans BigQuery, pour les suivre dans le temps et les répartir par équipe."}
    - {from: aa, to: ops, text: "Une recommandation reste une proposition : elle est appliquée, reportée ou refusée par une personne ; rien n'est modifié tout seul."}
captures:
  - image: https://docs.cloud.google.com/static/recommender/docs/images/rec-hub-apply.png
    page: https://docs.cloud.google.com/recommender/docs/active-assist/apply-dismiss-restore-recommendations
    legende: "Hub de recommandations : liste par catégorie et détail d'un redimensionnement de VM, configuration actuelle et recommandée, économie mensuelle"
docs:
  Page produit: https://cloud.google.com/solutions/active-assist
  Documentation: https://docs.cloud.google.com/recommender/docs
  Présentation d'Active Assist: https://docs.cloud.google.com/recommender/docs/whatis-activeassist
  Liste des moteurs de recommandation: https://docs.cloud.google.com/recommender/docs/recommenders
  VM inactives: https://docs.cloud.google.com/compute/docs/instances/idle-vm-recommendations-overview
  Recommandations de stratégie IAM: https://docs.cloud.google.com/policy-intelligence/docs/role-recommendations-overview
  Projets inutilisés: https://docs.cloud.google.com/recommender/docs/unattended-project-recommender
  Export vers BigQuery: https://docs.cloud.google.com/recommender/docs/bq-export/export-recommendations-to-bq
  API REST: https://docs.cloud.google.com/recommender/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/recommender
  Client Python: https://docs.cloud.google.com/python/docs/reference/recommender/latest
  Quotas et limites: https://docs.cloud.google.com/recommender/quotas
  Notes de version: https://docs.cloud.google.com/recommender/docs/release-notes
---

## Ce que c'est

Nom de l'ensemble des outils de recommandation de Google Cloud. Le service qui les porte s'appelle **Recommender** : il analyse l'usage réel des ressources et produit deux types d'objets, les **insights** (un constat mesuré, « cette VM n'a pas dépassé 3 % de CPU depuis 14 jours ») et les **recommandations** (l'action proposée, avec son gain estimé et son niveau de risque).

- **Six axes.** Les propositions sont classées par coût, sécurité, performance, fiabilité, facilité d'exploitation et durabilité. Un même moteur peut alimenter plusieurs axes.
- **Un moteur par produit et par sujet.** Chacun porte un identifiant stable, utilisé par l'API et par les rôles IAM : `google.compute.instance.IdleResourceRecommender` (VM inactives), `google.compute.instance.MachineTypeRecommender` (redimensionnement), `google.compute.disk.IdleResourceRecommender` (disques oubliés), `google.compute.address.IdleResourceRecommender` (adresses IP réservées inutilisées), `google.compute.commitment.UsageCommitmentRecommender` (engagements d'usage à souscrire), `google.iam.policy.Recommender` (droits excédentaires), `google.cloudsql.instance.*` (inactivité, surdimensionnement, sécurité, performance de [Cloud SQL](#cloud-sql)), `google.resourcemanager.projectUtilization.Recommender` (projets délaissés), `google.bigquery.table.PartitionClusterRecommender` (partitionnement et *clustering* de tables [BigQuery](#bigquery)), `google.container.DiagnosisRecommender` ([GKE](#gke)), `google.storage.bucket.SoftDeleteRecommender` ([Cloud Storage](#cloud-storage)).
- **Où on les voit.** Page **Active Assist** de la console, **FinOps hub** du compte de facturation, page d'optimisation de Cloud Hub, et surtout en contexte : la liste des VM signale elle-même celles qui dorment.
- **État.** Une recommandation est active, revendiquée, appliquée, ignorée ou échue. L'état se met à jour par l'API, ce qui permet de suivre un plan d'optimisation sans tableur.
- **Export.** Un transfert planifié par BigQuery Data Transfer Service copie recommandations et insights dans un jeu de données, pour les historiser, les croiser avec les coûts et les répartir par équipe.
- **Accès.** Chaque moteur a ses propres permissions (`recommender.<type>.get`, `.list`, `.update`), ce qui permet de donner la lecture des recommandations de coût sans ouvrir celles de sécurité. Les actions sont tracées dans les journaux d'audit.
- **Facturation.** Le service n'est pas facturé ; seul l'export vers [BigQuery](#bigquery) consomme du stockage et des requêtes.

> [!WARNING]
> Une recommandation se juge, elle ne s'applique pas en lot. Une VM « inactive » peut être un secours de reprise, un droit IAM « inutilisé » peut ne servir qu'une fois l'an à la clôture, et un engagement proposé sur trois ans se fonde sur la consommation passée. Le gain affiché est une estimation, pas un engagement.

## À quoi ça sert

- Récupérer la dépense évidente : VM éteintes mais facturées, disques non attachés, adresses IP réservées, instances surdimensionnées.
- Resserrer les droits IAM sur la base de l'usage observé plutôt que d'un audit déclaratif, avec un rôle de remplacement proposé.
- Décider d'un engagement d'usage sur des bases chiffrées, et voir si les engagements déjà souscrits sont consommés.
- Repérer les projets que plus personne n'utilise avant qu'ils ne deviennent des zones d'ombre.
- Suivre un plan d'optimisation dans la durée en exportant les recommandations vers [BigQuery](#bigquery) et en les restituant dans [Looker](#looker).
- Alimenter un rituel FinOps : un score et une liste de gains potentiels à passer en revue périodiquement.

**À éviter** comme unique source de décision d'architecture : les moteurs regardent l'usage passé d'une ressource isolée, sans connaître les contraintes de reprise d'activité, les pics saisonniers ou les dépendances entre services. À éviter aussi comme outil de gouvernance des coûts à lui seul : il propose des actions ponctuelles mais ne pose ni budget ni limite — c'est le rôle de [Cost Management](#cost-management) et de [Cloud Quotas](#cloud-quotas). Enfin, pour l'optimisation fine des conteneurs, les mécanismes natifs de [GKE](#gke) (autoscaler vertical, mise à l'échelle automatique des nœuds) agissent en continu là où une recommandation arrive après coup.

## Alternatives en logiciel libre

- **Cloud Custodian** (Apache 2.0) : moteur de règles déclaratives qui inventorie, signale, étiquette ou corrige les ressources d'un compte cloud — le pendant direct, avec en plus l'application automatique que Recommender laisse à l'humain.
- **OpenCost** (Apache 2.0) : allocation du coût Kubernetes par espace de noms et par charge de travail, base des décisions de redimensionnement dans un cluster.
- **Robusta KRR** (MIT) : recommandations de `requests` et `limits` pour les charges Kubernetes, calculées à partir des métriques Prometheus.
- **Goldilocks** (Apache 2.0) : exploitation de l'autoscaler vertical de Kubernetes pour proposer les bons dimensionnements de pods.
- **Polaris** (Apache 2.0) et **kube-score** (MIT) : contrôles de bonnes pratiques sur les manifestes et les ressources d'un cluster, l'équivalent des axes fiabilité et exploitabilité.
- **Steampipe** (AGPL v3) : requêtes SQL sur l'inventaire d'un compte cloud, avec des jeux de contrôles prêts à l'emploi pour la sécurité et le gaspillage.
- **Prowler** (Apache 2.0) : audit de configuration de sécurité multi-cloud, proche des recommandations de l'axe sécurité.
