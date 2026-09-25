---
title: VPC Service Controls
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Périmètre de service, x: 250, y: 16, w: 330, h: 290}
  nodes:
    vsc: {label: VPC Service Controls, sub: "règles d'entrée et de sortie", icon: categories/security-identity, focus: true, x: 8, y: 130, w: 230, h: 56}
    vm: {label: Compute Engine, sub: "VM sans IP externe", icon: produits/compute-engine, x: 270, y: 40, w: 230}
    bq: {label: BigQuery, sub: "données protégées", icon: produits/bigquery, x: 270, y: 130, w: 230}
    gcs: {label: Cloud Storage, sub: "bucket du périmètre", icon: produits/cloud-storage, x: 270, y: 220, w: 230}
    public: {label: Cloud Storage, sub: "bucket public", icon: produits/cloud-storage, x: 600, y: 40, w: 150}
    partner: {label: Projet partenaire, sub: "autre organisation", external: true, x: 600, y: 130, w: 155}
    onprem: {label: Réseau sur site, sub: "accès privé étendu", external: true, x: 600, y: 220, w: 155}
  flows:
    - {from: vsc, to: bq, control: true, text: "Le périmètre est décrit dans une règle d'accès de l'organisation : il liste les projets protégés et les services restreints, indépendamment des rôles IAM."}
    - {from: vm, to: bq, text: "À l'intérieur, les appels circulent librement : la VM interroge BigQuery par l'accès privé à Google, sans adresse IP externe ni passage par internet."}
    - {from: bq, to: public, from_offset: -16, text: "Une copie vers un bucket situé hors du périmètre est refusée, même si l'appelant détient les rôles nécessaires : c'est le blocage d'exfiltration."}
    - {from: partner, to: bq, to_offset: 16, text: "Une règle d'entrée autorise explicitement un compte de service du projet partenaire à lire un jeu de données donné, et rien d'autre."}
    - {from: gcs, to: onprem, control: true, text: "Le périmètre s'étend au réseau sur site par un tunnel VPN ou un Interconnect : les postes de l'entreprise atteignent le bucket, l'internet public non."}
    - {from: vsc, to: gcs, control: true, text: "Le mode simulation journalise les appels qui seraient refusés sans les bloquer : c'est par là qu'on commence, avant de basculer le périmètre en application."}
docs:
  Page produit: https://cloud.google.com/security/vpc-service-controls
  Documentation: https://docs.cloud.google.com/vpc-service-controls/docs
  Vue d'ensemble: https://docs.cloud.google.com/vpc-service-controls/docs/overview
  Périmètres de service: https://docs.cloud.google.com/vpc-service-controls/docs/service-perimeters
  Règles d'entrée et de sortie: https://docs.cloud.google.com/vpc-service-controls/docs/ingress-egress-rules
  Créer un périmètre: https://docs.cloud.google.com/vpc-service-controls/docs/create-service-perimeters
  Produits compatibles: https://docs.cloud.google.com/vpc-service-controls/docs/supported-products
  Mode simulation: https://docs.cloud.google.com/vpc-service-controls/docs/dry-run-mode
  Dépannage: https://docs.cloud.google.com/vpc-service-controls/docs/troubleshooting
  Access Context Manager: https://docs.cloud.google.com/access-context-manager/docs/overview
  API REST (Access Context Manager): https://docs.cloud.google.com/access-context-manager/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/access-context-manager
  Quotas et limites: https://docs.cloud.google.com/vpc-service-controls/quotas
  Notes de version: https://docs.cloud.google.com/vpc-service-controls/docs/release-notes
---

## Ce que c'est

Une frontière autour de ressources Google Cloud, indépendante des identités. Là où [IAM](#cloud-iam) répond « ce principal a-t-il le droit ? », VPC Service Controls répond « cet appel vient-il d'un contexte autorisé, et la donnée a-t-elle le droit de sortir ? ». Les deux se cumulent : un appel doit passer les deux contrôles.

- **Périmètre de service.** Une liste de projets et de **services restreints** (Cloud Storage, BigQuery, Cloud KMS, Secret Manager, et la plupart des APIs). À l'intérieur, tout communique librement ; en travers de la frontière, tout est refusé par défaut. Le périmètre ne bloque ni les APIs tierces ni internet en général : il ne s'applique qu'aux services Google gérés.
- **Ce qu'il empêche.** L'usage d'identifiants volés depuis un réseau non autorisé, la copie de données vers une ressource extérieure (`gcloud storage cp` vers un bucket public, `bq mk` vers une table externe), et l'exposition provoquée par une stratégie IAM trop permissive — un bucket ouvert à `allUsers` reste inaccessible depuis l'extérieur du périmètre.
- **Règles d'entrée et de sortie.** Les seules ouvertures : une règle d'**entrée** décrit qui, depuis où, peut appeler quelle méthode sur quelles ressources du périmètre ; une règle de **sortie** décrit ce que les clients internes peuvent atteindre à l'extérieur. C'est ainsi qu'on organise un échange contrôlé avec un partenaire ou entre deux périmètres.
- **Niveaux d'accès.** Fournis par **Access Context Manager** : plage d'adresses IPv4 ou IPv6, identité, appareil géré, région. Ils servent de condition dans les règles d'entrée, et ce sont eux qui permettent à un administrateur d'utiliser la console sur des ressources protégées.
- **Extension au sur site.** Un réseau relié par [Cloud VPN](#cloud-vpn) ou [Cloud Interconnect](#cloud-interconnect) entre dans le périmètre si le VPC qui l'accueille en fait partie, avec l'**accès privé à Google** ; l'adresse IP virtuelle **restreinte** (`restricted.googleapis.com`) force les requêtes vers les seules APIs compatibles.
- **Portée.** Configuration au niveau de l'organisation par défaut, ou par **stratégie d'accès à portée réduite** sur un dossier ou un projet, ce qui permet de déléguer l'administration.
- **Mode simulation.** Un périmètre en *dry run* journalise ce qu'il refuserait sans rien bloquer. C'est l'outil indispensable : les dépendances cachées entre services se découvrent là, pas en production.
- **Données et métadonnées.** Le périmètre vise le contenu des ressources. Certaines métadonnées — noms de buckets, structure de projets — peuvent traverser sans contrôle complet ; c'est IAM, y compris par rôles personnalisés, qui les protège.
- Le service est **gratuit**.

> [!WARNING]
> Un périmètre activé d'emblée casse à peu près tout : chaînes de build, exports de journaux, agents de service, accès console. Commencer en mode simulation, lire les refus dans les journaux d'audit pendant plusieurs jours, écrire les règles d'entrée et de sortie correspondantes, puis seulement basculer.

## À quoi ça sert

- Isoler un entrepôt [BigQuery](#bigquery) de données personnelles ou réglementées, pour qu'aucune requête ne puisse l'exporter vers un projet extérieur.
- Empêcher qu'un identifiant compromis — clé de compte de service ou jeton OAuth volé — serve depuis une machine quelconque sur internet.
- Reproduire dans le cloud une architecture réseau fermée en prolongeant le périmètre jusqu'au réseau sur site par Interconnect.
- Organiser un échange de données avec un partenaire : une règle d'entrée nominative pour son compte de service, sur une méthode et une ressource précises.
- Séparer les environnements : un périmètre production et un périmètre développement, entre lesquels aucune copie n'est possible sans règle explicite.
- Détecter les tentatives d'accès inattendues grâce à un périmètre « pot de miel » et aux journaux d'audit du service.

**À éviter** comme substitut au contrôle d'accès : un périmètre n'accorde aucun droit et n'en retire aucun, il ajoute une condition de contexte — les rôles restent à écrire avec soin. À éviter aussi sur des projets dont les dépendances ne sont pas connues : la mise en place représente un vrai travail d'inventaire, et un périmètre mal réglé se traduit par des pannes difficiles à diagnostiquer. Enfin, il ne filtre pas le trafic réseau : pour limiter ce qui sort d'un VPC vers internet, ce sont [Cloud NGFW](#cloud-ngfw) et [Cloud NAT](#cloud-nat) qui s'en chargent.

## Alternatives en logiciel libre

Il n'existe pas d'équivalent direct : le périmètre est appliqué par les APIs Google elles-mêmes, ce qu'aucun logiciel tiers ne peut reproduire. Sur une infrastructure que l'on exploite soi-même, la même intention se construit à partir de plusieurs briques.

- **Open Policy Agent** : décision centralisée sur chaque appel d'API, avec des règles qui prennent en compte l'origine de la requête autant que l'identité — la partie « conditions de contexte ».
- **Istio** et sa ressource `AuthorizationPolicy`, ou **Cilium** en couche réseau : autorisation entre services d'après l'identité de charge de travail, le port et le chemin, avec refus par défaut.
- **NetworkPolicy** de Kubernetes : la même idée de cloisonnement, appliquée aux pods d'un cluster.
- **Squid** ou **Envoy** en proxy de sortie, avec liste d'autorisation de destinations : le contrôle d'*egress*, qui empêche une charge de travail de parler à un service non prévu.
- **Ceph RGW** et ses politiques de compartiment, ou **Apache Ranger** : contrôle d'accès contextuel au niveau du magasin de données lui-même.
