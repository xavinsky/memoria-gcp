---
title: "Périmètres : VPC Service Controls"
subgroup: Protection des données
---

IAM répond à « ce principal a-t-il le droit ? ». Il ne dit rien de **l'endroit d'où vient l'appel** ni de **l'endroit où part la donnée** : une clé de compte de service volée fonctionne depuis n'importe quel poste sur internet, et un utilisateur légitime peut copier une table vers un projet personnel avec `bq cp` ou `gcloud storage cp`. C'est l'exfiltration. [VPC Service Controls](#vpc-service-controls) ajoute un second contrôle, indépendant d'IAM : un **périmètre de service** autour de projets, où les API Google protégées ne répondent qu'aux appels venus d'un contexte autorisé et refusent toute opération qui ferait sortir la donnée. Un appel doit passer les deux contrôles.

![Périmètre de service : libre à l'intérieur, entrée et sortie par règles explicites](../../svg/perimetre-vpc-sc.svg)

Le périmètre ne vise que les services Google gérés : il ne filtre ni internet ni les API tierces, qui relèvent de [Cloud NGFW](#cloud-ngfw) et de l'absence de route de sortie. Il protège le **contenu** des ressources ; certaines métadonnées (noms de buckets, par exemple) peuvent traverser sans contrôle complet, et restent à protéger par IAM.

## Les briques

| Brique | Rôle | À retenir |
|---|---|---|
| **Stratégie d'accès** (*access policy*) | Conteneur des périmètres et niveaux d'accès | Une seule au niveau de l'organisation ; des stratégies **à portée réduite** sur un dossier ou un projet délèguent l'administration |
| **Périmètre de service** | Liste de projets (ou de réseaux VPC) et de **services restreints** | Un projet appartient à un seul périmètre appliqué et à un seul périmètre en simulation |
| **Niveau d'accès** (Access Context Manager) | Condition sur l'origine : plage IPv4/IPv6, région, identité, état de l'appareil | Voir [niveau d'accès](#lexterm-niveau-d-acces) ; sert de source dans les règles d'entrée ; pas de mode simulation propre |
| **Règle d'entrée** (*ingress*) | Autorise un client **hors** périmètre à appeler des ressources **dedans** | Bloc `from` (identités ou type d'identité, sources : niveau d'accès, projet, réseau VPC, point de terminaison PSC) et bloc `to` (services, méthodes ou permissions, rôles IAM, ressources) |
| **Règle de sortie** (*egress*) | Autorise un appel qui implique une ressource **hors** périmètre depuis l'intérieur | Nécessaire dès qu'une même opération touche une ressource dedans et une ressource dehors, quel que soit le sens de la donnée |
| **Pont de périmètre** (*bridge*) | Échange bidirectionnel entre projets de deux périmètres | Même organisation et même stratégie ; Google recommande à sa place des règles d'entrée et de sortie, plus fines |
| **Services accessibles depuis le VPC** | Liste des API joignables depuis les réseaux du périmètre | `RESTRICTED-SERVICES` = tous les services protégés ; s'applique au trafic VPC → API, pas entre services Google |
| **VIP restreinte** (`restricted.googleapis.com`) | Plage `199.36.153.4/30`, non annoncée sur internet, qui ne sert que les API compatibles avec VPC Service Controls | DNS `*.googleapis.com` en CNAME vers elle, route et pare-feu associés ; voir [Concevoir le réseau](#concevoir-le-reseau) |
| **Mode simulation** (*dry run*) | Évalue une configuration sans bloquer, et journalise ce qu'elle refuserait | Le seul moyen sûr de découvrir les dépendances |

Le service est gratuit. Règles et ressources en simulation comptent dans les quotas de la stratégie d'accès.

## Concevoir le périmètre

Les recommandations de Google ([*Design and architect service perimeters*](https://docs.cloud.google.com/vpc-service-controls/docs/architect-perimeters), [plan de fondations](https://docs.cloud.google.com/architecture/blueprints/security-foundations/operation-best-practices)) tiennent en quelques règles :

- **Un grand périmètre commun** (*common unified perimeter*) plutôt que plusieurs petits. À l'intérieur, IAM et le réseau suffisent ; l'équipe du périmètre ne gère que les flux nord-sud, depuis et vers l'extérieur. Chaque périmètre supplémentaire ajoute des flux est-ouest à ouvrir règle par règle.
- **Plusieurs périmètres seulement pour une vraie frontière de données** : données réglementées (PCI DSS) séparées du reste, données brutes séparées de données dé-identifiées destinées à être partagées, un périmètre par locataire quand l'organisation héberge des clients.
- **Protéger tous les services compatibles** dès la création. Un service laissé hors de la liste est une voie de sortie ; toute exception se justifie par écrit.
- **Aucune route vers la VIP privée** (`private.googleapis.com`) depuis un réseau du périmètre : elle donne accès aux services non couverts et annule la protection contre l'exfiltration interne. Un service non compatible s'utilise depuis un projet hors périmètre.
- **Shared VPC** : le projet hôte et tous ses projets de service dans le même périmètre. Même règle pour l'accès aux services privés (Cloud SQL, par exemple).
- **Accès de secours** (*breakglass*) : une identité et un chemin documentés pour modifier le périmètre quand il bloque le pipeline qui le déploie.
- **Le périmètre ne remplace pas IAM.** Il n'accorde ni ne retire aucun droit ; le moindre privilège reste la règle (voir [IAM : bonnes pratiques](#iam-bonnes-pratiques)).

## Ce qui casse

| Symptôme | Cause | Remède |
|---|---|---|
| Pages de la console vides ou en erreur sur les services protégés | La console est un client internet, donc hors périmètre ; l'accès via l'accès privé à Google n'est pas pris en charge | Niveau d'accès sur les plages IP publiques des postes d'administration (sortie NAT de l'entreprise), éventuellement restreint à des utilisateurs |
| Builds Cloud Build refusés | Seuls les **pools privés** sont protégés ; les déclencheurs Pub/Sub ne sont pas pris en charge | Pool privé dans un projet du périmètre, compte de service choisi ; règle d'entrée pour le compte hérité ou pour les déclencheurs (voir [Cloud Build](#cloud-build-builds)) |
| `docker pull` ou `pip install` en échec | DNS de `*.pkg.dev` non dirigé vers la VIP ; dépôts distants bloqués vers leur source amont ; `mirror.gcr.io` hors périmètre | Zone DNS `pkg.dev` vers `restricted.googleapis.com` ; `gcloud artifacts vpcsc-config allow` par emplacement ; règle de sortie documentée pour `mirror.gcr.io` |
| Requête BigQuery entre projets refusée (`RESOURCES_NOT_IN_SAME_SERVICE_PERIMETER`) | Le job tourne dans un projet, le jeu de données est dans un autre, hors du périmètre ou dans un autre périmètre | Règle de sortie vers le projet du jeu de données, ou job exécuté dans le projet du périmètre ; voir [BigQuery : organiser les tables](#organiser-bigquery) |
| Export de journaux, extraction BigQuery vers un bucket hors périmètre | L'agent de service qui écrit (rédacteur du récepteur de journaux, par exemple) est un client interne qui sort | Règle de sortie pour cette identité et cette ressource, ou destination dans le périmètre |
| Pipeline IaC ou CI externe refusé (`NO_MATCHING_ACCESS_LEVEL`) | Terraform, Pulumi ou GitHub Actions appellent les API depuis internet | Règle d'entrée nominative pour le compte de service du pipeline, sur les services qu'il déploie ; voir [Déployer sans clé](#deployer-sans-cle) |
| Appels depuis une VM refusés (`SERVICE_NOT_ALLOWED_FROM_VPC`) | Le service n'est pas dans les services accessibles depuis le VPC | L'ajouter, souvent `iam.googleapis.com` en plus de `RESTRICTED-SERVICES` |

Chaque refus porte un identifiant unique ; l'**analyseur de violations** (*violation analyzer*) de la console évalue l'appel contre toutes les configurations en jeu et indique la règle manquante. Les journaux d'audit de type `policy` en donnent le détail (`violationReason`, `ingressViolations`, `egressViolations`).

## Méthode de déploiement

Le plan de fondations d'entreprise ne déploie VPC Service Controls qu'en simulation, parce que le passage en mode appliqué demande une préparation propre à chaque organisation. La [méthode de Google](https://docs.cloud.google.com/vpc-service-controls/docs/enable) se déroule charge par charge :

1. **Inventorier les accès.** Pour chaque application : qui appelle quelles API depuis l'extérieur (administrateurs, CI, outils de sécurité, partenaires, sites), et ce que les services internes appellent à l'extérieur.
2. **Préparer le réseau.** DNS `*.googleapis.com` vers la VIP restreinte, aucune sortie internet ni route vers la VIP privée.
3. **Créer le périmètre en simulation**, avec tous les services compatibles et `RESTRICTED-SERVICES` comme services accessibles, plus les accès déjà connus (plages IP, comptes de CI).
4. **Collecter les refus** par un récepteur agrégé qui envoie les journaux `cloudaudit.googleapis.com/policy` dans BigQuery.
5. **Faire tourner tous les cas d'usage**, puis analyser et écrire les règles d'entrée et de sortie.
6. **Appliquer**, puis garder une configuration de simulation pour chaque changement suivant et un processus d'entrée pour les nouveaux projets.

```bash
# 3. Périmètre en simulation seule
gcloud access-context-manager perimeters dry-run create donnees \
  --policy=POLICY_ID --perimeter-title="Données" --perimeter-type=regular \
  --perimeter-resources=projects/PROJECT_NUMBER \
  --perimeter-restricted-services=bigquery.googleapis.com,storage.googleapis.com \
  --perimeter-enable-vpc-accessible-services \
  --perimeter-vpc-allowed-services=RESTRICTED-SERVICES \
  --perimeter-ingress-policies=entree.yaml

# 6. La configuration de simulation devient la configuration appliquée
gcloud access-context-manager perimeters dry-run enforce donnees --policy=POLICY_ID
```

```yaml
# entree.yaml : le compte de service du pipeline peut déployer depuis la CI
- ingressFrom:
    identities:
    - serviceAccount:deployeur@PROJECT_ID.iam.gserviceaccount.com
    sources:
    - accessLevel: "*"
  ingressTo:
    operations:
    - serviceName: bigquery.googleapis.com
      methodSelectors:
      - method: "*"
    resources:
    - projects/PROJECT_NUMBER
```

```sql
-- 5. Refus en simulation, regroupés par service, méthode, appelant et raison
SELECT
  resource.labels.service AS service,
  protopayload_auditlog.methodName AS methode,
  protopayload_auditlog.authenticationInfo.principalEmail AS appelant,
  JSON_VALUE(protopayload_auditlog.metadataJson, '$.violationReason') AS raison,
  COUNT(*) AS refus
FROM `PROJECT_ID.DATASET.cloudaudit_googleapis_com_policy_*`
WHERE JSON_VALUE(protopayload_auditlog.metadataJson, '$.dryRun') = 'true'
GROUP BY service, methode, appelant, raison
ORDER BY refus DESC
```

En Pulumi, `gcp.accesscontextmanager.ServicePerimeter` porte la configuration appliquée dans `status` et celle de simulation dans `spec`, avec `use_explicit_dry_run_spec=True`. Passer en mode appliqué revient à recopier `spec` dans `status`, dans une revue de code.

## Pièges

- **Appliquer d'emblée.** Chaînes de build, exports de journaux, agents de service et console cessent de fonctionner en même temps. Toujours passer par la simulation, sur une durée qui couvre les traitements mensuels et les opérations rares.
- **Croire que la simulation couvre tout.** Elle ne teste pas la bascule DNS vers la VIP restreinte : vérifier auparavant que chaque API utilisée y est servie. Les niveaux d'accès n'ont pas de mode simulation ; pour en tester un changement, créer un nouveau niveau et l'utiliser dans la configuration de simulation.
- **Lire « entrée » et « sortie » comme des sens de données.** Ils décrivent la position du client et des ressources par rapport au périmètre, pas le sens de la copie : une même règle de sortie autorise une copie de bucket dans les deux sens.
- **`ANY_IDENTITY` avec `accessLevel: "*"`.** Cette règle d'entrée ouvre le périmètre à tout internet, requêtes anonymes comprises, pour les méthodes visées. Nommer les identités, ou au moins le type d'identité.
- **Des ponts en chaîne.** Un pont ne se traverse pas en cascade (A–B et B–C ne relient pas A et C), il est bidirectionnel, et un projet relié par un pont ne peut plus ajouter ses réseaux VPC au périmètre. Préférer des règles d'entrée et de sortie.
- **Projets supprimés, principaux supprimés.** Une règle qui cite un projet ou un compte supprimé peut disparaître ou bloquer la mise à jour du périmètre : vérifier les références lors d'un diagnostic.
- **Services non compatibles dans le périmètre.** Ils peuvent ne pas fonctionner du tout, surtout quand Cloud Storage ou Pub/Sub sont restreints. Les placer dans un projet hors périmètre, relié par une règle précise.

## Alternatives en logiciel libre

Aucun logiciel ne peut reproduire un contrôle appliqué par les API de Google elles-mêmes ; sur une infrastructure que l'on exploite, la même intention se construit à partir de plusieurs briques.

- **Open Policy Agent** (Apache 2.0) : décision centralisée sur chaque appel d'API, avec des règles qui combinent identité et contexte (réseau source, appareil), la partie « niveau d'accès ».
- **Istio** (Apache 2.0) : `AuthorizationPolicy` en refus par défaut entre services, et passerelle de sortie qui n'autorise que des destinations déclarées ; le couple entrée et sortie à l'échelle d'un maillage.
- **Cilium** (Apache 2.0) : politiques réseau Kubernetes par identité de charge et par nom DNS de destination, qui bloquent la sortie vers un service non prévu.
- **Envoy** (Apache 2.0) ou **Squid** (GPL v2) en proxy de sortie à liste d'autorisation : tout appel sortant passe par un point unique, journalisé et filtré.
- **Apache Ranger** (Apache 2.0) : politiques d'accès contextuelles et audit au niveau des magasins de données (Hive, HDFS, Kafka), là où le périmètre agit sur BigQuery et Cloud Storage.
