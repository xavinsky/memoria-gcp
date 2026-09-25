---
title: Media CDN
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 380, h: 268}
  nodes:
    viewers: {label: Lecteurs vidéo, sub: "HLS, DASH", external: true, x: 8, y: 122, w: 146}
    armor: {label: Cloud Armor, sub: "règles de périphérie", icon: categories/security-identity, x: 182, y: 36, w: 180}
    mcdn: {label: Media CDN, sub: "routes et cache", icon: categories/media-services, focus: true, x: 182, y: 118, w: 180, h: 64}
    keys: {label: Jeux de clés, sub: "requêtes signées", icon: categories/security-identity, x: 182, y: 214, w: 180}
    gcs: {label: Cloud Storage, sub: "origine HLS/DASH", icon: produits/cloud-storage, x: 382, y: 36, w: 164}
    log: {label: Cloud Logging, sub: "journaux détaillés", icon: categories/observability, x: 382, y: 200, w: 164}
    ext: {label: Origine externe, sub: "sur site, autre cloud", external: true, x: 584, y: 118, w: 160}
  flows:
    - {from: viewers, to: mcdn, text: "Le lecteur demande le manifeste puis les segments ; le proxy inverse du point de présence rattache chaque URI à une route de l'EdgeCacheService."}
    - {from: armor, to: mcdn, control: true, text: "La règle de sécurité de périphérie autorise ou refuse la requête sur l'adresse IP, le pays ou le numéro de système autonome, avant toute recherche en cache."}
    - {from: keys, to: mcdn, control: true, text: "Le jeu de clés valide la signature de l'URL ou du cookie, qui restreint l'accès à un préfixe de chemin et à une durée."}
    - {from: mcdn, to: gcs, from_side: right, to_side: left, from_offset: -18, text: "Un défaut de cache déclenche un remplissage depuis l'origine Cloud Storage, authentifié pour que le bucket reste privé."}
    - {from: mcdn, to: ext, from_side: right, to_side: left, text: "Une autre route tire son contenu d'une origine hors de Google Cloud, avec bascule vers une origine de secours en cas d'erreur."}
    - {from: mcdn, to: log, from_side: right, to_side: left, from_offset: 18, text: "Chaque requête client et chaque requête d'origine est journalisée en quasi temps réel, exportable vers Cloud Storage ou Pub/Sub."}
docs:
  Page produit: https://cloud.google.com/cdn
  Documentation: https://docs.cloud.google.com/media-cdn/docs
  Vue d'ensemble: https://docs.cloud.google.com/media-cdn/docs/overview
  Choisir un produit de CDN: https://docs.cloud.google.com/media-cdn/docs/choose-cdn-product
  Configuration: https://docs.cloud.google.com/media-cdn/docs/configuration
  Routage: https://docs.cloud.google.com/media-cdn/docs/routing
  Mise en cache: https://docs.cloud.google.com/media-cdn/docs/caching
  Origines: https://docs.cloud.google.com/media-cdn/docs/origins
  Requêtes signées: https://docs.cloud.google.com/media-cdn/docs/signed-requests
  Règles de sécurité: https://docs.cloud.google.com/media-cdn/docs/security-policies
  Emplacements de cache: https://docs.cloud.google.com/media-cdn/docs/locations
  API REST: https://docs.cloud.google.com/media-cdn/docs/reference/rest/v1/projects.locations.edgeCacheServices
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/edge-cache
  Démarrage rapide: https://docs.cloud.google.com/media-cdn/docs/quickstart
  Notes de version: https://docs.cloud.google.com/media-cdn/docs/release-notes
---

## Ce que c'est

Réseau de diffusion de contenu autonome, dimensionné pour le débit : vidéo en continu et téléchargements volumineux. Contrairement à [Cloud CDN](#cloud-cdn), il ne s'accroche pas à un load balancer — c'est un service à part entière, servi depuis l'infrastructure de périphérie de Google et depuis des caches installés chez des opérateurs partenaires.

- **Trois composants.** Un **routeur** termine les requêtes HTTP en proxy inverse et les associe à une route ; un **cache** répond ou signale un défaut ; un **remplisseur de cache** va chercher l'objet auprès de l'origine configurée.
- **Trois ressources.** `EdgeCacheService` porte les adresses, les protocoles, les règles de sécurité et la configuration de routage ; `EdgeCacheOrigin` décrit une origine, ses délais, ses tentatives et son origine de secours ; `EdgeCacheKeyset` contient les clés de validation des requêtes signées.
- **Routage avancé.** Les routes se déclarent par hôte, par préfixe, par chemin exact, par expression régulière, par en-tête ou par paramètre de requête. Chacune fixe son origine, sa politique de cache, ses réécritures et ses manipulations d'en-têtes — on règle ainsi séparément le manifeste, les segments et les clés de chiffrement d'un même flux.
- **Origines.** Tout point de terminaison HTTP public : bucket [Cloud Storage](#cloud-storage), bucket compatible S3, autre cloud, infrastructure sur site. L'**authentification d'origine** permet de garder un bucket Cloud Storage privé ; le **bouclier d'origine** concentre les remplissages pour épargner l'origine.
- **Connectivité client.** HTTP/2 et QUIC de bout en bout, compression dynamique, et certificats TLS gérés par Google sur le domaine du client, sans supplément de prix.
- **Contrôle d'accès.** Requêtes signées par URL ou par cookie, avec portée de préfixe et durée limitée, authentification à double jeton, et règles de sécurité de périphérie Cloud Armor (adresses, pays, numéros de système autonome, en-têtes de couche 7, renseignement sur les menaces).
- **Invalidation** par hôte et chemin, par préfixe avec caractère générique, ou par **étiquettes de cache** — y compris des étiquettes intégrées d'état, d'origine et de type de média, ce qui permet de purger une saison ou un format sans toucher au reste.
- **Extensibilité.** Les extensions de service insèrent du code au fil de la requête et de la réponse pour normaliser des en-têtes ou implémenter un schéma de jetons propriétaire.
- **Observation.** Chaque requête client et chaque requête d'origine part dans Cloud Logging en quasi temps réel, avec export vers Cloud Storage ou Pub/Sub.

> [!WARNING]
> Media CDN ne s'active pas en libre-service : l'accès au produit s'obtient auprès de l'équipe commerciale Google Cloud avant tout démarrage. Il n'a pas non plus de page de tarifs publique, à la différence de Cloud CDN.

## À quoi ça sert

- Diffuser de la vidéo en direct ou à la demande en HLS et DASH à grande échelle, avec des débits de l'ordre du térabit par seconde.
- Distribuer de gros téléchargements — images système, mises à jour de firmware, jeux, modèles — quand ils constituent le cœur du trafic et non un appoint.
- Servir un catalogue dont les origines sont ailleurs : sur site, chez un autre fournisseur, ou dans un bucket compatible S3, sans les recopier dans Google Cloud.
- Protéger un catalogue payant par requêtes signées à portée de préfixe et durée courte, avec des clés renouvelables sans interruption.
- Réduire la charge de l'origine sur des pics prévisibles (lancement, événement en direct) grâce au bouclier d'origine et à un taux de remplissage maîtrisé.

**À éviter** pour du contenu web classique — feuilles de style, scripts, polices, petites images : [Cloud CDN](#cloud-cdn) est optimisé pour ce profil de petits objets très demandés, et s'active d'une case à cocher sur un équilibreur existant. À éviter aussi pour les protocoles temps réel : ni RTMP ni WebRTC ne passent par Media CDN, il faut un [Network Load Balancer *passthrough*](#cloud-load-balancing) régional ; et le trafic WebSocket, non stockable, relève d'un Application Load Balancer externe.

## Alternatives en logiciel libre

- **Apache Traffic Server** : le plus proche, y compris dans le modèle de hiérarchie de caches parents et enfants qui correspond au bouclier d'origine ; utilisé comme socle par plusieurs CDN publics.
- **Varnish Cache** : cache HTTP à forte capacité, dont le module de stockage massif convient aux gros objets, avec une politique décrite en VCL.
- **NGINX** avec `proxy_cache` et `slice` : découpage des gros fichiers en tranches mises en cache séparément, ce qui reproduit le remplissage par plages d'octets.
- **Shaka Packager** et **FFmpeg** : empaquetage HLS et DASH et chiffrement des segments, pour produire le contenu que le CDN distribue.
