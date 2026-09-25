---
title: Cloud Quotas
subgroup: Exploitation
icon: categories/management-tools
schema:
  size: [760, 320]
  zones:
    - {label: Organisation GCP, x: 8, y: 16, w: 600, h: 288}
    - {label: Projet, x: 24, y: 110, w: 330, h: 180}
  nodes:
    res: {label: Compute Engine, sub: "vCPU consommés", icon: produits/compute-engine, x: 40, y: 140, w: 170}
    api: {label: API Google Cloud, sub: "requêtes par minute", icon: categories/management-tools, x: 40, y: 216, w: 180}
    adj: {label: Ajusteur de quota, sub: "hausse automatique", icon: categories/management-tools, x: 400, y: 44, w: 190}
    cq: {label: Cloud Quotas, sub: "valeurs et préférences", icon: categories/management-tools, focus: true, x: 400, y: 150, w: 190, h: 64}
    mon: {label: Cloud Monitoring, sub: "alerte à 80 %", icon: categories/observability, x: 400, y: 236, w: 172}
    tf: {label: Terraform, sub: "préférence de quota", external: true, x: 618, y: 150, w: 140}
  flows:
    - {from: res, to: cq, text: "La consommation de chaque ressource est comparée en continu à la valeur du quota qui la borne, par projet, par région ou par zone."}
    - {from: api, to: cq, text: "Les quotas de débit comptent les appels sur une fenêtre glissante ; au-delà, l'API répond 429 au lieu de servir la requête."}
    - {from: tf, to: cq, from_side: left, to_side: right, control: true, text: "Une préférence de quota déclarée par l'API, gcloud ou Terraform demande une valeur plus haute, accordée d'emblée ou après examen."}
    - {from: adj, to: cq, control: true, text: "L'ajusteur relève lui-même le quota de 10 à 20 % quand la consommation de pointe s'en approche, sur les services compatibles."}
    - {from: cq, to: mon, text: "Les métriques d'utilisation et de limite alimentent des règles d'alerte : on est prévenu avant le refus, pas après."}
docs:
  Documentation: https://docs.cloud.google.com/docs/quotas
  Vue d'ensemble: https://docs.cloud.google.com/docs/quotas/overview
  Consulter et gérer les quotas: https://docs.cloud.google.com/docs/quotas/view-manage
  Ajusteur de quota: https://docs.cloud.google.com/docs/quotas/quota-adjuster
  API Cloud Quotas: https://docs.cloud.google.com/docs/quotas/api-overview
  API REST: https://docs.cloud.google.com/docs/quotas/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/quotas
  Métriques de quota: https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z
  Notes de version: https://docs.cloud.google.com/docs/quotas/release-notes
---

## Ce que c'est

Service transverse qui expose, en lecture et en écriture, les **quotas** de toutes les API Google Cloud : combien de ressources un projet peut détenir, à quelle cadence il peut appeler un service, et comment relever ces bornes. Il remplace les pages de quotas propres à chaque produit par une API, une CLI et une ressource Terraform uniques.

- **Trois familles de quotas.** Les **quotas d'allocation** bornent un stock : nombre de VM, de vCPU, d'adresses IP, de buckets. Les **quotas de débit** bornent une cadence : appels d'API par minute ou par jour, remis à zéro sur une fenêtre glissante ou à minuit heure du Pacifique. Les **quotas de simultanéité** bornent le nombre d'opérations longues en cours.
- **Portée.** Un quota s'applique à un projet, un dossier, une organisation ou un utilisateur, et vaut globalement, par région ou par zone. Une même limite peut donc être atteinte dans une zone alors qu'il reste de la place ailleurs.
- **Limites du système.** À distinguer des quotas : taille maximale d'un fichier, nombre de colonnes d'une table, longueur d'un nom. Elles ne se demandent pas et ne se relèvent pas.
- **Relever une valeur.** Une **préférence de quota** (*quota preference*) déclare la valeur souhaitée pour un quota donné sur un conteneur donné. Certaines demandes sont accordées automatiquement, d'autres passent par un examen qui tient compte de l'historique de consommation, de l'ancienneté du compte et de la disponibilité des ressources. Les demandes en cours et passées se suivent dans la console.
- **Ajusteur de quota.** Activé sur un projet, un dossier ou une organisation, il surveille la consommation de pointe et déclenche de lui-même une hausse de 10 à 20 % quand le seuil approche, sur la liste de services qu'il couvre (Compute Engine, Cloud Run, Cloud Build, Artifact Registry, Vertex AI, Logging, Monitoring, KMS, Filestore et d'autres). Il ne baisse jamais une valeur. Au niveau dossier et organisation, il ne se règle que par API ou par `gcloud`.
- **Outillage.** Console (*IAM et administration → Quotas et limites du système*), `gcloud quotas info` et `gcloud quotas preferences`, API REST, Terraform. Les rôles **Lecteur de quotas** et **Administrateur de quotas** séparent la consultation de la demande.
- **Surveillance.** Les métriques `serviceruntime.googleapis.com/quota/allocation/usage` et `serviceruntime.googleapis.com/quota/rate/net_usage`, accompagnées de la métrique de limite, permettent des règles d'alerte sur le ratio consommation/quota dans [Cloud Monitoring](#cloud-monitoring).
- **Facturation.** Le service n'est pas facturé : seules les ressources consommées le sont.

> [!WARNING]
> Un quota atteint ne se traduit pas par une dégradation mais par un refus sec — création de VM impossible, réponse 429, échec de déploiement. La bonne pratique est d'alerter à 80 % d'un quota structurant (vCPU par région, adresses IP externes, requêtes d'écriture) plutôt que de découvrir la borne au pire moment.

## À quoi ça sert

- Diagnostiquer un échec de création de ressource ou une erreur 429 : le quota en cause, sa portée et sa valeur courante sont visibles au même endroit.
- Préparer une montée en charge annoncée en demandant les hausses à l'avance, projet par projet ou pour toute une organisation.
- Éviter les demandes manuelles répétitives sur un environnement qui grossit, en confiant la hausse à l'ajusteur.
- Contenir un projet bac à sable : laisser des quotas bas y tient lieu de garde-fou pour la consommation comme pour le coût.
- Industrialiser la création de projets : les préférences de quota se déclarent dans le même Terraform que le reste de l'infrastructure.

**À éviter** comme outil de maîtrise des coûts : un quota borne un volume, pas une dépense, et il ne prévient de rien financièrement. Le suivi budgétaire relève de [Cost Management](#cost-management), l'optimisation des ressources inutilisées d'[Active Assist](#active-assist). À éviter aussi comme mécanisme de limitation interne entre équipes : une politique d'organisation ou un découpage par projet exprime mieux une règle d'usage qu'une limite technique héritée du fournisseur.

## Alternatives en logiciel libre

Il n'existe pas d'équivalent direct : un quota Google Cloud est une propriété du fournisseur, pas un logiciel à installer. Les mécanismes comparables, dans une infrastructure que l'on administre soi-même, sont les suivants.

- **Kubernetes** (Apache 2.0) : `ResourceQuota` borne ce qu'un espace de noms peut consommer (CPU, mémoire, nombre d'objets) et `LimitRange` fixe les valeurs par pod — le même modèle de quota d'allocation par conteneur logique.
- **OpenStack** (Apache 2.0) : quotas par projet sur les instances, les vCPU, les volumes et les adresses IP flottantes, avec la même notion de valeur ajustable par un administrateur.
- **Envoy** (Apache 2.0) et **NGINX** (BSD 2 clauses) : limitation de débit locale ou globale, l'équivalent des quotas de débit d'API.
- **Prometheus** (Apache 2.0) et **Alertmanager** (Apache 2.0) : suivi du ratio consommation/limite et alerte avant saturation, ce que les métriques de quota permettent ici.
- **Cloud Custodian** (Apache 2.0) : règles déclaratives qui inventorient et bornent les ressources d'un compte cloud, utile pour poser des garde-fous que les quotas ne couvrent pas.
