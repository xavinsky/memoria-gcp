---
title: Cloud Endpoints
subgroup: Intégration et API
icon: categories/integration-services
deprecie: "Produit hérité : il ne se justifie que devant un backend déjà équipé d'ESP ou d'ESPv2. Pour une nouvelle API, préférer [API Gateway](#api-gateway) ou, si la gestion du cycle de vie compte, [Apigee](#apigee)."
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 150, y: 10, w: 598, h: 282}
  nodes:
    clients: {label: Clients, sub: "clé d'API", external: true, x: 8, y: 120, w: 130}
    sm: {label: Service Management, sub: config de service, icon: categories/management-tools, x: 166, y: 26, w: 210}
    ep: {label: Cloud Endpoints, sub: ESPv2, icon: categories/integration-services, focus: true, x: 166, y: 118, w: 190, h: 64}
    sc: {label: Service Control, sub: quotas et rapports, icon: categories/management-tools, x: 166, y: 214, w: 210}
    run: {label: Cloud Run, sub: backend sans serveur, icon: produits/cloud-run, x: 396, y: 26, w: 200}
    gke: {label: Backend GKE, sub: API REST ou gRPC, icon: produits/gke, x: 396, y: 118, w: 190}
  flows:
    - {from: sm, to: ep, control: true, text: "La description OpenAPI ou le descripteur gRPC est déployé dans Service Management ; le proxy y lit sa configuration au démarrage."}
    - {from: clients, to: ep, text: "Tous les appels passent d'abord par le proxy, qui valide la clé d'API ou le jeton JWT avant tout traitement."}
    - {from: ep, to: gke, from_offset: 16, text: "La requête validée part vers le backend, ici un conteneur du même pod que le proxy déployé en side-car."}
    - {from: ep, to: run, from_offset: -16, text: "En mandataire distant, le même ESPv2 tourne comme service Cloud Run devant un backend sans serveur."}
    - {from: ep, to: sc, text: "Le proxy interroge Service Control pour les quotas, puis lui remet les rapports d'usage qui alimentent métriques et facturation."}
docs:
  Documentation: https://docs.cloud.google.com/endpoints/docs
  Choisir une option: https://docs.cloud.google.com/endpoints/docs/choose-endpoints-option
  Architecture: https://docs.cloud.google.com/endpoints/docs/openapi/architecture-overview
  Endpoints pour OpenAPI: https://docs.cloud.google.com/endpoints/docs/openapi/about-cloud-endpoints
  Extensions OpenAPI: https://docs.cloud.google.com/endpoints/docs/openapi/openapi-extensions
  Endpoints pour gRPC: https://docs.cloud.google.com/endpoints/docs/grpc/about-grpc
  Transcodage HTTP vers gRPC: https://docs.cloud.google.com/endpoints/docs/grpc/transcoding
  Endpoints Frameworks: https://docs.cloud.google.com/endpoints/docs/frameworks/about-cloud-endpoints-frameworks
  Authentification: https://docs.cloud.google.com/endpoints/docs/openapi/authentication-method
  Quotas par consommateur: https://docs.cloud.google.com/endpoints/docs/openapi/quotas-overview
  Déployer ESPv2 sur Cloud Run: https://docs.cloud.google.com/endpoints/docs/openapi/set-up-cloud-run-espv2
  Migrer vers ESPv2: https://docs.cloud.google.com/endpoints/docs/openapi/migrate-to-esp-v2
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/endpoints
  Tarifs: https://cloud.google.com/endpoints/pricing
  Notes de version: https://docs.cloud.google.com/endpoints/docs/release-notes
---

## Ce que c'est

Système de gestion d'API construit autour d'un **mandataire que l'on déploie soi-même** devant son backend. Le proxy applique les règles décrites dans une configuration de service — authentification, clés, quotas — et rend compte de chaque appel à l'infrastructure de services de Google.

- **Quatre composants.** Le **proxy** (ESP ou ESPv2) intercepte les requêtes. **Service Management** stocke la configuration de service, produite à partir d'une description OpenAPI ou d'un fichier de configuration gRPC et déployée par `gcloud`. **Service Control** applique les règles à l'exécution : vérification des clés, quotas, remontée des métriques et des journaux. La console sert de vue de suivi.
- **Deux proxys.** **ESP** repose sur NGINX et ne se déploie qu'en conteneur, devant un backend [GKE](#gke), Kubernetes, [Compute Engine](#compute-engine) ou App Engine flexible. **ESPv2**, fondé sur Envoy, est celui qu'on utilise aujourd'hui : il ajoute [Cloud Run](#cloud-run), les fonctions, Knative serving et App Engine standard.
- **Deux modes de déploiement.** En **side-car**, le proxy tourne dans le même pod ou la même VM que le backend : pas de saut réseau supplémentaire. En **mandataire distant**, ESPv2 est déployé comme service Cloud Run et gère plusieurs backends sans serveur désignés par `x-google-backend`.
- **Trois options d'API.** *Endpoints for OpenAPI* décrit l'API en OpenAPI 2.0 ou 3.0. *Endpoints for gRPC* part des fichiers `.proto` et sait transcoder HTTP/JSON en gRPC ; gRPC n'est pas disponible sur App Engine ni sur les fonctions, faute de HTTP/2. *Endpoints Frameworks* [!DECONSEILLE] est un cadre applicatif limité aux exécutions Java 8 et Python 2.7 d'App Engine standard de 1re génération, hors support, avec sa propre passerelle intégrée.
- **Contrôle d'accès.** Clés d'API pour identifier le projet appelant et compter les quotas, jetons JWT signés par un compte de service, jetons d'identité Google, ou fournisseur tiers (Firebase, Auth0). Les quotas se définissent par méthode et par consommateur.
- **Exploitation.** Il n'existe pas de portail développeur : la documentation et la distribution des clés sont à la charge du projet. Les métriques et les traces sont visibles dans la page Endpoints Services de la console.
- **Facturation** identique à celle d'[API Gateway](#api-gateway), par appels comptés par Service Control : deux premiers millions d'appels mensuels gratuits, puis 3 $ par million jusqu'à un milliard et 1,50 $ au-delà. Le calcul et le réseau du proxy s'ajoutent, puisque c'est l'utilisateur qui l'héberge.

> [!WARNING]
> Le proxy est à la charge du projet : il faut le dimensionner, le mettre à jour et le surveiller. C'est la différence de fond avec API Gateway, qui exploite le même moteur Envoy mais sous la responsabilité de Google.

## À quoi ça sert

- Maintenir une API déjà gérée par ESP ou ESPv2, sans réécrire sa description ni changer son modèle d'authentification.
- Placer une gestion d'API devant un backend qui n'est pas sans serveur — un service [GKE](#gke) ou une VM — là où API Gateway n'atteint qu'un point d'entrée HTTPS public.
- Exposer en HTTP/JSON une API gRPC hébergée ailleurs que sur Cloud Run, seul cas que la passerelle managée ne couvre pas.
- Garder le contrôle de la version et de la configuration du mandataire, par exemple pour des options Envoy particulières.

**À éviter** pour toute API nouvelle. [API Gateway](#api-gateway) rend le même service — mêmes extensions OpenAPI, même transcodage gRPC, mêmes clés et quotas — sans proxy à exploiter ni à mettre à jour, et au même tarif à l'appel. Dès qu'il faut un portail développeur, des produits d'API, des transformations de message ou une politique de sécurité partagée, c'est [Apigee](#apigee) qu'il faut regarder. Et pour du trafic interne entre services d'un cluster, [Cloud Service Mesh](#cloud-service-mesh) évite le passage par une passerelle.

## Alternatives en logiciel libre

- **ESPv2** (Apache 2.0) : le proxy lui-même est publié en logiciel libre et s'utilise devant n'importe quel backend, même sans les services de gestion Google.
- **Envoy** (Apache 2.0) : la brique sous-jacente, qui sait seule valider un JWT, limiter le débit et transcoder gRPC-JSON.
- **grpc-gateway** (BSD 3 clauses) : génère un mandataire REST depuis un fichier `.proto`, l'équivalent direct du transcodage d'Endpoints for gRPC.
- **Kong Gateway** (Apache 2.0) et **Apache APISIX** (Apache 2.0) : passerelles à plugins couvrant clés d'API, quotas et authentification, déployables en side-car comme en point central.
- **Emissary-ingress** (Apache 2.0) : passerelle Kubernetes sur Envoy, configurée par ressources déclaratives, pour les backends en cluster.
