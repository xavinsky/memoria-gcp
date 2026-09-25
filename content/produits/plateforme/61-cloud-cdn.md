---
title: Cloud CDN
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 268}
  nodes:
    users: {label: Clients internet, sub: "navigateurs, mobiles", external: true, x: 8, y: 122, w: 152}
    cdn: {label: Cloud CDN, sub: "cache de périphérie", icon: categories/networking, focus: true, x: 178, y: 114, w: 182, h: 64}
    mon: {label: Cloud Monitoring, sub: "taux de hits", icon: categories/observability, x: 178, y: 214, w: 182}
    lb: {label: Load balancer, sub: "mappage d'URL", icon: categories/networking, x: 388, y: 118, w: 176}
    gcs: {label: Cloud Storage, sub: "bucket de backend", icon: produits/cloud-storage, x: 586, y: 36, w: 158}
    mig: {label: Compute Engine, sub: "serveur d'origine", icon: produits/compute-engine, x: 586, y: 200, w: 158}
  flows:
    - {from: users, to: cdn, from_side: right, to_side: left, from_offset: -12, to_offset: -16, text: "La requête GET atteint le Google Front End le plus proche du client, qui cherche l'objet dans son cache d'après la clé de cache."}
    - {from: cdn, to: users, from_side: left, to_side: right, from_offset: 16, to_offset: 12, text: "En cas de succès (cache hit), la réponse part directement du cache, sans que l'origine soit sollicitée."}
    - {from: cdn, to: lb, text: "En cas d'échec (cache miss), la requête est transmise au service ou au bucket de backend désigné par le mappage d'URL."}
    - {from: lb, to: gcs, from_side: right, to_side: left, from_offset: -18, text: "Un bucket de backend sert les objets statiques ; la réponse alimente le cache (cache fill) si elle est jugée stockable."}
    - {from: lb, to: mig, from_side: right, to_side: left, from_offset: 18, text: "Un service de backend sert le contenu dynamique depuis les instances d'origine, avec les en-têtes de cache qu'elles choisissent."}
    - {from: cdn, to: mon, control: true, text: "Le taux de hits, le volume servi et le volume de remplissage remontent en métriques, par origine et par backend."}
docs:
  Page produit: https://cloud.google.com/cdn
  Documentation: https://docs.cloud.google.com/cdn/docs
  Vue d'ensemble: https://docs.cloud.google.com/cdn/docs/overview
  Choisir un produit de CDN: https://docs.cloud.google.com/cdn/docs/choose-cdn-product
  Contenu stockable et modes de cache: https://docs.cloud.google.com/cdn/docs/caching
  Clés de cache: https://docs.cloud.google.com/cdn/docs/using-cache-keys
  Invalidation: https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview
  Contenu authentifié: https://docs.cloud.google.com/cdn/docs/authenticate-content
  Mise en place avec un bucket: https://docs.cloud.google.com/cdn/docs/setting-up-cdn-with-bucket
  Journalisation et surveillance: https://docs.cloud.google.com/cdn/docs/cdn-logging-monitoring
  Emplacements de cache: https://docs.cloud.google.com/cdn/docs/locations
  Bonnes pratiques: https://docs.cloud.google.com/cdn/docs/best-practices
  API REST: https://docs.cloud.google.com/cdn/docs/apis
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/compute/backend-services/update
  Tarifs: https://cloud.google.com/cdn/pricing
  Notes de version: https://docs.cloud.google.com/cdn/docs/release-notes
---

## Ce que c'est

Cache de périphérie activé sur un **Application Load Balancer externe** global ou classique (voir [Cloud Load Balancing](#cloud-load-balancing)). Ce n'est pas un service séparé mais une option du service ou du bucket de backend : le Google Front End qui reçoit déjà la requête sert la réponse depuis son cache au lieu de la faire remonter jusqu'à l'origine.

- **Origines.** Tout backend admis par l'équilibreur fait office de serveur d'origine : bucket [Cloud Storage](#cloud-storage), groupe d'instances [Compute Engine](#compute-engine), Ingress ou Gateway [GKE](#gke), service [Cloud Run](#cloud-run) par un NEG sans serveur, ou origine externe (sur site, autre cloud) par un NEG internet.
- **Succès et échecs.** Un *cache hit* est servi depuis le point de présence ; un *cache miss* remonte à l'origine, et la réponse est stockée si elle est jugée cacheable — d'où la distinction de facturation entre **cache egress** (octets servis depuis le cache) et **cache fill** (octets rapatriés de l'origine). Un *partial hit* sert une partie de la réponse depuis le cache, le reste depuis l'origine, pour les requêtes par plages d'octets.
- **Trois modes de cache.** `CACHE_ALL_STATIC` (défaut via gcloud et l'API) met en cache les contenus statiques reconnus et les réponses qui portent des directives valides ; `USE_ORIGIN_HEADERS` n'obéit qu'aux en-têtes `Cache-Control` de l'origine ; `FORCE_CACHE_ALL` met en cache toutes les réponses réussies en ignorant les directives — à proscrire sur un backend qui sert du contenu par utilisateur.
- **Clé de cache.** Par défaut, protocole, hôte, chemin et chaîne de requête complète. On retire ou on restreint chacun de ces éléments, et on ajoute des en-têtes ou des cookies nommés ; réduire la clé augmente mécaniquement le taux de hits.
- **En-têtes.** `Cache-Control` vaut pour le CDN et pour le navigateur ; `CDN-Cache-Control` ne s'adresse qu'à Cloud CDN, ce qui permet une durée de vie longue en périphérie et courte chez le client. Un en-tête `Vary` mal maîtrisé multiplie les entrées et fait chuter le taux de hits.
- **Fraîcheur et éviction.** L'expiration (durée de vie) et l'éviction (place disponible dans un cache donné) sont indépendantes : un objet peu demandé disparaît d'un point de présence avant d'expirer. Le remplissage est réactif, il n'existe pas de préchargement ; le service de contenu périmé (`stale-while-revalidate`, `stale-if-error`) évite de faire attendre le client pendant une revalidation.
- **Invalidation** par hôte, par chemin ou par motif, à l'échelle de l'équilibreur. Elle s'applique à tous les points de présence, mais reste une opération exceptionnelle : la pratique recommandée est de **versionner les URL** plutôt que d'invalider.
- **Contenu protégé.** *URLs signées* et *cookies signés* limitent l'accès à un préfixe et à une durée ; l'accès authentifié à un bucket privé et l'authentification d'origine évitent d'exposer publiquement le stockage.
- **Traitements en périphérie.** Compression dynamique (gzip, Brotli), optimisation d'images (redimensionnement et conversion de format à la volée), et extensions de service pour insérer du code au fil de la requête.
- **Observation.** Journal de requêtes exportable vers Cloud Logging et métriques de taux de hits par origine, indispensables pour savoir ce que le cache économise réellement.

> [!WARNING]
> `FORCE_CACHE_ALL` sur un backend qui sert des pages personnalisées ou des réponses d'API expose le contenu d'un utilisateur à un autre : le cache ignore alors les directives de l'origine, y compris `private` et `no-store`.

## À quoi ça sert

- Accélérer un site web en servant depuis la périphérie les fichiers CSS, JavaScript, polices et images — le cas pour lequel le produit est optimisé : beaucoup de petits objets à forte cadence.
- Décharger l'origine : sur un catalogue ou un site de presse, un taux de hits élevé divise le nombre de requêtes à traiter et le trafic sortant facturé depuis les VM ou les buckets.
- Publier un site statique depuis un bucket [Cloud Storage](#cloud-storage) avec domaine propre, certificat géré et cache, sans aucune instance de calcul.
- Distribuer des images générées par les utilisateurs, avec redimensionnement en périphérie plutôt qu'une variante stockée par format.
- Servir des téléchargements protégés par URL signée quand ils restent une part minoritaire du trafic web.

**À éviter** pour la diffusion vidéo en continu et les très gros téléchargements : [Media CDN](#media-cdn) est dimensionné pour ce débit, avec protection d'origine et journalisation adaptées. À éviter aussi devant un backend dont les réponses sont toutes personnalisées — le cache ne sert alors à rien et ajoute une facturation de recherche en cache. Le CDN ne remplace enfin ni le filtrage applicatif ([Cloud Armor](#cloud-armor)) ni l'équilibrage lui-même : il s'ajoute à un [Application Load Balancer](#cloud-load-balancing) externe et n'existe pas sans lui.

## Alternatives en logiciel libre

- **Varnish Cache** : cache HTTP inverse dont le langage VCL exprime la clé de cache, les durées de vie et l'invalidation avec beaucoup plus de finesse que les modes de cache managés.
- **NGINX** avec `proxy_cache` : cache de proxy inverse intégré au serveur web, souvent suffisant pour un ou deux nœuds de périphérie.
- **Apache Traffic Server** : proxy cache conçu pour les opérateurs, avec hiérarchie de caches parents et enfants — l'équivalent du bouclier d'origine.
- **Envoy** et son filtre de cache HTTP, quand la périphérie est déjà un maillage de proxys.
- **Souin** : cache HTTP conforme à la RFC 9111, greffable dans Caddy, Traefik ou NGINX.
