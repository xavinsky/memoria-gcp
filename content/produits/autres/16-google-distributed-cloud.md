---
title: Google Distributed Cloud
subgroup: Migration et hybride
icon: produits/distributed-cloud
aka: "GDC Edge, GDC Hosted, GDC Virtual, Anthos clusters on bare metal et on VMware"
schema:
  size: [760, 330]
  zones:
    - {label: Site du client, x: 6, y: 10, w: 370, h: 310}
    - {label: Projet GCP, x: 396, y: 10, w: 350, h: 310}
  nodes:
    dev: {label: Équipements locaux, sub: "capteurs, caisses, usagers", external: true, x: 20, y: 36, w: 210, h: 56}
    gdc: {label: Distributed Cloud connected, sub: "clusters GKE et VM sur site", icon: produits/distributed-cloud, focus: true, x: 20, y: 140, w: 280, h: 72}
    lan: {label: Données locales, sub: "stockage, bases sur site", external: true, x: 20, y: 256, w: 210, h: 50}
    fleet: {label: Console et gcloud, sub: "flotte GKE, API Edge", icon: produits/gke, x: 470, y: 36, w: 260}
    obs: {label: Cloud Logging, sub: "journaux et métriques", icon: categories/observability, x: 470, y: 148, w: 260}
    vpc: {label: VPC, sub: "services et VM du projet", icon: categories/networking, x: 470, y: 256, w: 260}
  flows:
    - {from: fleet, to: gdc, control: true, from_side: left, to_side: top, to_offset: 110, text: "L'administrateur crée clusters et pools de nœuds sur les machines de la zone depuis la console ou gcloud ; Google applique les mises à jour à distance"}
    - {from: dev, to: gdc, from_side: bottom, to_side: top, to_offset: -35, text: "Les équipements du site appellent les applications déployées sur les clusters locaux, sans aller-retour vers une région"}
    - {from: gdc, to: lan, from_side: bottom, to_side: top, from_offset: -35, text: "Les charges lisent et écrivent les données qui doivent rester sur place"}
    - {from: gdc, to: obs, from_side: right, to_side: left, text: "Journaux, métriques et audit remontent dans Cloud Logging et Cloud Monitoring"}
    - {from: gdc, to: vpc, from_side: right, to_side: left, from_offset: 24, text: "Un tunnel Cloud VPN relie la zone au réseau VPC : les charges locales joignent les services et les VM du projet"}
docs:
  Page produit: https://cloud.google.com/distributed-cloud
  Documentation: https://docs.cloud.google.com/distributed-cloud/docs
  Connected, vue d'ensemble: https://docs.cloud.google.com/distributed-cloud/connected/latest/docs/overview
  Connected, fonctionnement: https://docs.cloud.google.com/distributed-cloud/connected/latest/docs/how-it-works
  Connected, API: https://docs.cloud.google.com/distributed-cloud/connected/latest/docs/apis
  Connected, quotas: https://docs.cloud.google.com/distributed-cloud/connected/latest/docs/quotas
  Connected, tarifs: https://cloud.google.com/distributed-cloud/edge/pricing
  Connected, notes de version: https://docs.cloud.google.com/distributed-cloud/connected/latest/docs/release-notes
  Commandes gcloud (connected): https://docs.cloud.google.com/sdk/gcloud/reference/edge-cloud
  Air-gapped: https://docs.cloud.google.com/distributed-cloud/hosted/docs/latest/gdcag/overview
  Air-gapped appliance: https://docs.cloud.google.com/distributed-cloud/hosted/docs/latest/appliance/overview
  GDC Sandbox: https://docs.cloud.google.com/distributed-cloud/sandbox/latest/overview
  Logiciel seul, bare metal: https://docs.cloud.google.com/kubernetes-engine/distributed-cloud/bare-metal/docs/concepts/about-bare-metal
  Logiciel seul, VMware: https://docs.cloud.google.com/kubernetes-engine/distributed-cloud/vmware/docs/overview
  Tarifs du logiciel seul: https://cloud.google.com/kubernetes-engine/pricing
captures:
  - image: https://docs.cloud.google.com/static/distributed-cloud/hosted/docs/latest/gdcag/images/cluster-details.png
    page: https://docs.cloud.google.com/distributed-cloud/hosted/docs/latest/gdcag/platform-application/pa-ao-operations/cluster
    legende: "Console GDC air-gapped : liste des clusters Kubernetes d'une zone, avec leur état, leur nombre de nœuds, leurs ressources et leur version"
---

## Ce que c'est

Famille d'offres qui installe l'infrastructure et les services de Google Cloud hors de ses régions : dans le centre de données du client, sur un site distant ou sur le terrain. Toutes reposent sur **Kubernetes** (une distribution de GKE) et exécutent conteneurs et machines virtuelles. Trois formes :

- **Distributed Cloud connected** : du matériel certifié par Google (trois serveurs Dell en configuration standard, un seul possible) installé et maintenu par un intégrateur agréé, branché sur les commutateurs du client. Le plan de contrôle Kubernetes tourne sur place ; Google surveille et met à jour le logiciel à distance. Le site doit rester relié à Google Cloud par Cloud VPN : les charges continuent de tourner jusqu'à **7 jours** sans connexion (mode de survie), puis la zone doit se reconnecter pour renouveler jetons et clés de chiffrement. On pilote clusters et pools de nœuds avec la console, `gcloud edge-cloud` et l'API Edge Container ; les clusters s'inscrivent dans la flotte GKE du projet.
- **Distributed Cloud air-gapped** : un cloud souverain entièrement déconnecté d'internet et de Google Cloud, livré en baies intégrées après une étude du site (espace, énergie, refroidissement). Il a sa propre console, sa CLI `gdcloud` et ses propres API : organisations et projets, clusters Kubernetes, VM, stockage bloc et objet, service de bases de données (PostgreSQL, Oracle), KMS, et services d'IA de Gemini Enterprise Agent Platform (OCR, traduction, reconnaissance vocale, modèles génératifs). Le logiciel entre dans le périmètre isolé par support physique, après vérification de sa somme de contrôle. Deux variantes : l'**appliance**, boîtier durci et transportable d'environ 45 kg pour le terrain, et le **Sandbox**, un environnement simulé hébergé sur Google Cloud pour développer et tester sans matériel.
- **Distributed Cloud (logiciel seul)** : le logiciel seul, installé par le client sur ses propres serveurs *bare metal* ou sur son infrastructure VMware vSphere. Le client gère matériel, système et réseau ; les clusters se gèrent depuis Google Cloud via l'agent Connect.

**Facturation** : *connected* au mois, avec un engagement de 36 ou 60 mois sur le matériel et le support Enhanced au minimum ; les services Google Cloud consommés (VPN, observabilité) sont facturés à part. *Air-gapped* sur contrat. *Logiciel seul* à l'heure par vCPU géré dans les clusters utilisateur, au tarif de GKE pour les environnements sur site.

## À quoi ça sert

- Exécuter des applications qui exigent une latence minimale ou une connexion stable avec des équipements locaux : usines, magasins, réseaux de télécommunications, hôpitaux.
- Traiter sur place des volumes de données trop coûteux ou trop lents à transférer vers une région.
- Répondre à une obligation de résidence ou de souveraineté des données, jusqu'à l'isolement total pour la défense et le secteur public (*air-gapped*).
- Déployer des modèles d'IA, dont Gemini, à l'intérieur du périmètre réseau de l'entreprise.
- Unifier l'exploitation de clusters Kubernetes sur site et dans le cloud avec les mêmes outils et la même flotte (*logiciel seul*).

**À éviter** quand une région Google Cloud répond aux contraintes de latence et de conformité : [GKE](#gke) et [Compute Engine](#compute-engine) n'imposent ni engagement pluriannuel ni matériel à héberger. Pour une exigence de souveraineté qui porte sur le contrôle des accès et de la localisation plutôt que sur l'isolement physique, [Assured Workloads](#assured-workloads) dans une région publique suffit souvent. Pour reprendre un parc vSphere existant dans le cloud plutôt que moderniser sur site, [VMware Engine](#vmware-engine).

> [!WARNING]
> *Connected* n'est pas autonome : au-delà de 7 jours sans lien avec Google Cloud, la zone cesse de fonctionner. Un site qui doit tenir indéfiniment sans réseau relève d'*air-gapped*, pas de *connected*.

## Alternatives en logiciel libre

- **Kubernetes** avec **k3s** ou **RKE2** : distributions légères pour clusters en périphérie ou sur site, sans service de gestion à distance.
- **KubeVirt** : VM dans Kubernetes, l'équivalent du runtime de VM de GDC.
- **OpenStack** : cloud privé IaaS complet, exploitable sans aucune connexion extérieure — l'approche la plus proche d'*air-gapped*, avec toute l'exploitation à la charge du client.
- **Rancher** (licence Apache 2.0) ou **Open Cluster Management** : gestion centralisée d'une flotte de clusters Kubernetes répartis sur plusieurs sites.
- **Harbor** et **Flux** ou **Argo CD** : registre d'images et déploiement GitOps, les briques pour alimenter des clusters isolés.
