---
title: API Gateway
subgroup: Intégration et API
icon: categories/integration-services
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 156, y: 10, w: 592, h: 282}
  nodes:
    clients: {label: Clients, sub: "mobile, web", external: true, x: 8, y: 120, w: 120}
    spec: {label: Description OpenAPI, sub: x-google-backend, icon: categories/devops, x: 172, y: 26, w: 210}
    gw: {label: API Gateway, sub: "config déployée", icon: categories/integration-services, focus: true, x: 172, y: 118, w: 200, h: 64}
    run: {label: Cloud Run, sub: service backend, icon: produits/cloud-run, x: 436, y: 26, w: 180}
    fn: {label: Cloud Run functions, sub: traitement léger, icon: produits/cloud-run, x: 436, y: 120, w: 200}
    sc: {label: Service Control, sub: "quotas, clés d'API", icon: categories/management-tools, x: 436, y: 214, w: 190}
  flows:
    - {from: spec, to: gw, control: true, text: "La description OpenAPI, annotée par x-google-backend, est déployée comme configuration d'API immuable."}
    - {from: clients, to: gw, text: "Les appels arrivent sur le nom d'hôte gateway.dev de la passerelle, avec une clé d'API ou un jeton JWT."}
    - {from: gw, to: run, text: "La passerelle route chaque chemin vers son backend et signe un jeton d'identité pour l'appeler."}
    - {from: gw, to: fn, text: "Un même déploiement répartit les chemins entre plusieurs backends, ici une fonction."}
    - {from: gw, to: sc, text: "Service Control vérifie la clé d'API et le quota du consommateur, puis enregistre l'appel pour les métriques et la facturation."}
docs:
  Documentation: https://docs.cloud.google.com/api-gateway/docs
  Vue d'ensemble: https://docs.cloud.google.com/api-gateway/docs/about-api-gateway
  Description OpenAPI: https://docs.cloud.google.com/api-gateway/docs/openapi-overview
  Démarrage avec Cloud Run: https://docs.cloud.google.com/api-gateway/docs/get-started-cloud-run
  Méthodes d'authentification: https://docs.cloud.google.com/api-gateway/docs/authentication-method
  Quotas par consommateur: https://docs.cloud.google.com/api-gateway/docs/quotas-overview
  gRPC et transcodage: https://docs.cloud.google.com/api-gateway/docs/grpc-overview
  Derrière un load balancer: https://docs.cloud.google.com/api-gateway/docs/gateway-serverless-neg
  Routage de modèles: https://docs.cloud.google.com/api-gateway/docs/model-routing-overview
  Serveur MCP: https://docs.cloud.google.com/api-gateway/docs/mcp-overview
  API REST: https://docs.cloud.google.com/api-gateway/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/api-gateway
  Tarifs: https://cloud.google.com/api-gateway/pricing
  Notes de version: https://docs.cloud.google.com/api-gateway/docs/release-notes
---

## Ce que c'est

Passerelle d'API managée, sans serveur ni mandataire à administrer. On lui fournit une description OpenAPI annotée ; elle en déduit les routes, l'authentification et les quotas, et expose l'ensemble sur un point d'entrée HTTPS unique.

- **Trois ressources.** Une **API** est le conteneur logique. Une **configuration d'API** est produite à partir d'une description OpenAPI 2.0 ou 3.x (ou d'un descripteur gRPC) et devient immuable une fois créée. Une **passerelle** déploie une configuration dans une région et reçoit un nom d'hôte de la forme `https://GATEWAY_ID-HASH.REGION.gateway.dev`. Changer de configuration revient à en déployer une nouvelle sur la même passerelle.
- **Routage vers le backend.** L'extension `x-google-backend` porte l'adresse du service, le délai d'attente, la traduction du chemin et l'audience du jeton. En OpenAPI 3.x, les backends se déclarent une fois sous `x-google-api-management` et se référencent par leur nom. Les backends possibles sont [Cloud Run](#cloud-run), les fonctions, [App Engine](#app-engine), [Compute Engine](#compute-engine), [GKE](#gke) et tout point d'entrée HTTPS accessible.
- **Authentification.** Quatre méthodes, combinables par opération : **clé d'API** — une chaîne qui identifie le projet appelant et sert de base aux quotas ; **compte de service** signant un JWT, pour les appels entre services ; **jeton d'identité Google** ; et fournisseur d'identité tiers (Firebase, Auth0, Okta) validé sur ses clés publiques. La passerelle rejette la requête avant qu'elle n'atteigne le backend.
- **Quotas.** Un quota se définit par méthode et par consommateur identifié par sa clé d'API : tant d'appels par minute et par projet client. Depuis la mise à jour du moteur d'exécution, un dépassement de quota fait échouer la requête plutôt que de la laisser passer.
- **gRPC.** Une passerelle gRPC accepte un descripteur de service et **transcode** HTTP/JSON en appels gRPC, ce qui permet à un client navigateur d'atteindre un serveur gRPC. Elle ne gère que des backends Cloud Run, ne compresse pas les charges utiles et échoue au-delà d'un mégaoctet de requête ou de réponse transcodée.
- **Réseau.** La passerelle est régionale et publique. On la place derrière un load balancer d'application externe par un *groupe de points de terminaison du réseau sans serveur* pour lui donner un domaine propre, un certificat géré et un CDN.
- [!PREVERSION] **MCP et routage de modèles.** Une passerelle peut exposer ses opérations REST comme outils d'un **serveur MCP** pour des agents, et faire du **routage de modèles** : elle accepte des requêtes au format OpenAI, les transcode à la volée et les dirige vers des modèles de Model Garden.
- **Facturation** à l'appel, par compte de facturation : les deux premiers millions d'appels mensuels sont gratuits, puis 3 $ par million jusqu'à un milliard et 1,50 $ au-delà. Le trafic sortant est facturé au tarif réseau Premium.

> [!WARNING]
> Une configuration d'API ne se modifie pas. Toute correction, même d'un chemin, impose de créer une configuration et de la redéployer ; il faut donc versionner la description OpenAPI dans le dépôt et automatiser le déploiement.

## À quoi ça sert

- Poser une façade unique devant plusieurs services sans serveur, avec un seul domaine et une authentification homogène.
- Protéger une API publique par clé d'API et quota par consommateur, sans écrire de code de contrôle dans les services.
- Faire consommer par un navigateur ou un client HTTP un backend gRPC, grâce au transcodage.
- Découpler l'interface publique des backends : les chemins restent stables pendant qu'on déplace un service d'une fonction vers Cloud Run.

**À éviter** dès que le besoin dépasse le routage et le contrôle d'accès : pas de transformation de charge utile, pas de flux partagés, pas de portail développeur ni de catalogue de produits d'API. Ces sujets relèvent d'[Apigee](#apigee). À éviter aussi pour du trafic interne à un cluster, où [Cloud Service Mesh](#cloud-service-mesh) évite le détour par un point d'entrée public, et pour un simple service exposé tel quel : [Cloud Run](#cloud-run) sait déjà vérifier une identité et porter un domaine personnalisé.

## Alternatives en logiciel libre

- **KrakenD** (Apache 2.0) : passerelle sans état configurée par un seul fichier déclaratif, le plus proche du modèle « une description, une passerelle immuable ».
- **Envoy** (Apache 2.0) : le mandataire qui fait tourner ce genre de passerelle, capable de transcodage gRPC-JSON, de validation JWT et de limitation de débit.
- **Kong Gateway** (Apache 2.0) et **Apache APISIX** (Apache 2.0) : passerelles à plugins, pour les clés d'API, les quotas et l'authentification.
- **Traefik** (MIT) : routeur avec découverte automatique des services, intéressant quand les backends sont des conteneurs.
- **Emissary-ingress** (Apache 2.0) : passerelle Kubernetes sur Envoy, configurée par des ressources déclaratives.
- **grpc-gateway** (BSD 3 clauses) : génère depuis un fichier `.proto` un mandataire REST devant un service gRPC, l'équivalent direct du transcodage.
