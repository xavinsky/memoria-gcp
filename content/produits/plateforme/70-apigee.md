---
title: Apigee
subgroup: Intégration et API
icon: produits/apigee
aka: Apigee Edge
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 180, y: 10, w: 568, h: 282}
  nodes:
    apps: {label: Apps clientes, sub: "mobile, partenaires", external: true, x: 8, y: 120, w: 150}
    portal: {label: Portail développeur, sub: "doc, clés d'API", icon: produits/apigee, x: 206, y: 26, w: 196}
    proxy: {label: Apigee, sub: "proxy d'API, politiques", icon: produits/apigee, focus: true, x: 206, y: 118, w: 210, h: 64}
    run: {label: Cloud Run, sub: service backend, icon: produits/cloud-run, x: 470, y: 26, w: 180}
    legacy: {label: Service existant, sub: "SOAP, on-premises", icon: categories/hybrid-multicloud, x: 470, y: 120, w: 190}
    analytics: {label: Analytics Apigee, sub: "trafic, latence, erreurs", icon: categories/observability, x: 470, y: 214, w: 200}
  flows:
    - {from: portal, to: apps, from_side: left, to_side: right, control: true, text: "Le portail développeur publie la documentation des produits d'API et délivre aux développeurs les clés de leurs applications."}
    - {from: apps, to: proxy, text: "Les applications appellent l'API sur l'URL du proxy, en présentant leur clé d'API ou un jeton OAuth."}
    - {from: proxy, to: run, text: "Une fois les politiques de sécurité, de quota et de limitation passées, le proxy relaie la requête au backend."}
    - {from: proxy, to: legacy, text: "Le même proxy peut router vers un service existant et convertir SOAP ou XML en JSON au passage."}
    - {from: proxy, to: analytics, text: "Chaque appel alimente les analyses : volume, latence et taux d'erreur par produit d'API, par application et par développeur."}
captures:
  - image: https://docs.cloud.google.com/static/apigee/docs/api-platform/develop/images/edit-proxy-add-policy.png
    page: https://docs.cloud.google.com/apigee/docs/api-platform/develop/ui-edit-proxy
    legende: "Éditeur de proxy : politiques, points de terminaison proxy et cible avec leurs PreFlow et PostFlow, et le XML de la politique sélectionnée"
  - image: https://docs.cloud.google.com/static/apigee/docs/api-platform/debug/images/timeline-debug-v2.png
    page: https://docs.cloud.google.com/apigee/docs/api-platform/debug/trace
    legende: "Trace d'une requête : politiques traversées dans l'ordre, chronologie et variables de flux"
docs:
  Page produit: https://cloud.google.com/apigee
  Documentation: https://docs.cloud.google.com/apigee/docs
  Vue d'ensemble: https://docs.cloud.google.com/apigee/docs/api-platform/get-started/what-apigee
  APIs et proxys d'API: https://docs.cloud.google.com/apigee/docs/api-platform/fundamentals/understanding-apis-and-api-proxies
  Politiques: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/reference-overview-policy
  Environnements et groupes: https://docs.cloud.google.com/apigee/docs/api-platform/fundamentals/environments-overview
  Produits d'API: https://docs.cloud.google.com/apigee/docs/api-platform/publish/what-api-product
  Portail développeur intégré: https://docs.cloud.google.com/apigee/docs/api-platform/publish/portal/build-integrated-portal
  Sessions de débogage: https://docs.cloud.google.com/apigee/docs/api-platform/debug/trace
  Advanced API Security: https://docs.cloud.google.com/apigee/docs/api-security
  Monétisation: https://docs.cloud.google.com/apigee/docs/api-platform/monetization/overview
  Développement local: https://docs.cloud.google.com/apigee/docs/api-platform/local-development/overview
  Comparaison Apigee et Apigee hybrid: https://docs.cloud.google.com/apigee/docs/api-platform/get-started/apigee-feature-summary
  API REST: https://docs.cloud.google.com/apigee/docs/reference/apis/apigee/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/apigee
  Quotas et limites: https://docs.cloud.google.com/apigee/docs/api-platform/reference/limits
  Tarifs: https://cloud.google.com/apigee/pricing
  Notes de version: https://docs.cloud.google.com/apigee/docs/release-notes
---

## Ce que c'est

Plateforme de gestion du cycle de vie des APIs. Entre les applications clientes et les services de backend, Apigee interpose un **proxy d'API** dont on contrôle la sécurité, le trafic, le format des messages et la mesure, sans toucher au code du backend. Elle couvre REST, gRPC unaire, SOAP et GraphQL.

- **Organisation, environnements, groupes.** Une *organisation* Apigee est rattachée à un projet Google Cloud et s'étend sur une ou plusieurs régions. Les proxys se déploient dans des **environnements** (test, préproduction, production), regroupés en **groupes d'environnements** qui portent les noms d'hôte publics. Les rôles passent par IAM.
- **Proxy d'API.** Il a deux extrémités : le **ProxyEndpoint** définit l'URL exposée aux applications et porte en général la sécurité, les quotas et le contrôle d'accès ; le **TargetEndpoint** décrit la connexion au backend. Chaque modification crée une **révision** numérotée, immuable une fois déployée : revenir en arrière consiste à redéployer une révision antérieure.
- **Deux types de proxy.** Un proxy **Standard** n'utilise qu'un sous-ensemble de politiques, ne peut pas entrer dans un produit d'API, et coûte cinq fois moins cher à l'appel. Un proxy **Extensible** comporte au moins une politique extensible ou un *flow hook*, et donne accès à tout le reste : flux partagés, produits d'API, portails, transformations complexes.
- **Politiques.** Une politique est un module de configuration XML attaché à une étape du flux requête ou réponse, sans code. Les familles couvrent la sécurité (`VerifyAPIKey`, `OAuthv2`, `VerifyJWT`, `SAMLAssertion`), le trafic (`Quota`, `SpikeArrest`, `ResponseCache`), la médiation (`XMLtoJSON`, `JSONtoXML`, `AssignMessage`, `ExtractVariables`) et l'extension (`JavaScript`, `Java`, `ServiceCallout`, `MessageLogging`). Les **flux partagés** factorisent une séquence de politiques réutilisée par plusieurs proxys.
- **Publication.** Un **produit d'API** regroupe des ressources de plusieurs proxys avec un quota et une portée d'accès ; un **développeur** enregistre une **application** qui reçoit une clé et un secret. Le **portail développeur intégré** publie la documentation issue des descriptions OpenAPI, avec pages en Markdown ou HTML et inscription en libre-service ; un portail Drupal reste possible pour un site plus travaillé.
- **Débogage.** Une **session de débogage** capture les transactions réelles d'un proxy déployé et montre la chronologie des politiques, les variables de flux et les messages à chaque étape. La session dure 5 minutes lancée par API, 10 minutes depuis la console, capture 10 requêtes par processeur de messages (15 au maximum) et les données sont conservées 24 heures.
- **Mesure et sécurité.** Les analyses fournissent volumes, latences et erreurs par produit d'API et par développeur. **Advanced API Security** y ajoute la détection des mauvaises configurations, des bots et des abus. La **monétisation** facture l'usage aux développeurs.
- **Apigee hybrid.** Même plan de gestion hébergé par Google, mais le plan d'exécution (les processeurs de messages) tourne dans un cluster Kubernetes chez le client : les données d'API ne quittent pas son réseau.
- **Facturation** en paiement à l'usage ou par abonnement, après un essai de 60 jours. Trois types d'environnement par région : **Base** (365 $ par mois, 50 QPS, 20 proxys, proxys Standard uniquement), **Intermédiaire** (1 460 $, 100 QPS, 50 proxys ou flux partagés, proxys Extensibles et portails), **Complet** (3 431 $, QPS ajusté automatiquement, 100 proxys, multi-région, SLA jusqu'à 99,99 % sur deux régions). S'y ajoutent les appels : 20 $ par million pour un proxy Standard, 100 $ pour un proxy Extensible, dégressifs au volume, plus les options API Analytics (20 $ par million) et Advanced API Security (350 $ par million).

> [!TIP]
> Le type de proxy est le premier levier de coût. Un proxy qui ne fait que vérifier une clé et router vers un backend n'a pas besoin d'être Extensible : le déclarer Standard divise la facture d'appels par cinq.

## À quoi ça sert

- Exposer à des partenaires ou à des clients externes un catalogue d'APIs cohérent, avec inscription, clés, quotas et documentation en libre-service.
- Placer une façade stable devant un existant hétérogène : un proxy convertit SOAP en JSON, réécrit les chemins et masque la migration du backend.
- Appliquer une politique de sécurité uniforme — OAuth 2.0, JWT, limitation de débit, détection d'abus — sans la réimplémenter dans chaque service.
- Facturer l'usage d'une API, ou simplement mesurer qui consomme quoi, par produit d'API et par application.
- Garder les données d'API dans son propre réseau avec Apigee hybrid, quand la réglementation l'impose.

**À éviter** pour une API interne unique posée devant un service [Cloud Run](#cloud-run) : le coût plancher d'un environnement Apigee est sans rapport avec le besoin, et [API Gateway](#api-gateway) fait l'authentification, les clés et les quotas pour quelques dollars au million d'appels. À éviter aussi comme routeur entre microservices d'un même cluster : c'est le rôle d'un maillage de services comme [Cloud Service Mesh](#cloud-service-mesh), qui travaille au niveau du *sidecar* sans passer par un point central.

## Alternatives en logiciel libre

- **Kong Gateway** (Apache 2.0) : passerelle d'API fondée sur NGINX, avec un système de *plugins* — clés, OAuth, limitation de débit, transformations — qui recouvre la plupart des politiques Apigee.
- **Apache APISIX** (Apache 2.0) : passerelle dynamique sur OpenResty, configuration à chaud par etcd, plus de cent plugins et un tableau de bord.
- **Tyk Gateway** (MPL 2.0) : passerelle en Go livrée avec un portail développeur et un catalogue de produits d'API, la partie publication la plus proche d'Apigee.
- **Gravitee APIM** (Apache 2.0) et **WSO2 API Manager** (Apache 2.0) : plateformes complètes — gestion, portail, analyses — plutôt qu'une simple passerelle.
- **KrakenD** (Apache 2.0) : passerelle sans état, déclarative, orientée agrégation de plusieurs backends en une seule réponse.
- **Envoy** (Apache 2.0) : le mandataire sur lequel s'appuient plusieurs de ces projets, utile seul quand on ne veut que du routage, du TLS et de la limitation de débit.
