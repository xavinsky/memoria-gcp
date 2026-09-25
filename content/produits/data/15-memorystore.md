---
title: Memorystore
subgroup: Bases de données
icon: categories/databases
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 140, y: 16, w: 606, h: 268}
  nodes:
    clients: {label: Utilisateurs, external: true, x: 8, y: 122, w: 112}
    run: {label: Cloud Run, sub: application, icon: produits/cloud-run, x: 164, y: 118, w: 160}
    vk: {label: Memorystore, sub: "Valkey, 3 partitions", icon: categories/databases, focus: true, x: 372, y: 110, w: 200, h: 70}
    rep: {label: Réplicas, sub: autres zones, icon: categories/databases, x: 372, y: 224, w: 200, h: 50}
    sql: {label: Cloud SQL, sub: source de vérité, icon: produits/cloud-sql, x: 164, y: 224, w: 180}
    mon: {label: Cloud Monitoring, sub: métriques Valkey, icon: categories/observability, x: 568, y: 36, w: 176}
  flows:
    - {from: clients, to: run, text: "Les requêtes des utilisateurs arrivent sur l'application"}
    - {from: run, to: vk, text: "L'application interroge d'abord le cache, par le point de terminaison de découverte de l'instance"}
    - {from: run, to: sql, text: "Absence dans le cache : l'application lit la base, renvoie la réponse et réécrit la valeur dans le cache avec une durée de vie"}
    - {from: vk, to: rep, text: "Chaque partition réplique vers un à cinq nœuds répliques répartis sur d'autres zones, avec bascule automatique"}
    - {from: vk, to: mon, text: "Taux de succès du cache, mémoire, connexions et évictions remontent dans Cloud Monitoring"}
docs:
  Page produit: https://cloud.google.com/memorystore
  Documentation: https://docs.cloud.google.com/memorystore/docs
  Memorystore for Valkey: https://docs.cloud.google.com/memorystore/docs/valkey
  Memorystore for Redis Cluster: https://docs.cloud.google.com/memorystore/docs/cluster
  Memorystore for Redis: https://docs.cloud.google.com/memorystore/docs/redis
  Commandes prises en charge: https://docs.cloud.google.com/memorystore/docs/valkey/supported-commands
  Haute disponibilité et réplicas: https://docs.cloud.google.com/memorystore/docs/valkey/ha-and-replicas
  API REST: https://docs.cloud.google.com/memorystore/docs/valkey/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/memorystore
  Exemples de code client: https://docs.cloud.google.com/memorystore/docs/valkey/client-library-code-samples
  Quotas et limites: https://docs.cloud.google.com/memorystore/docs/valkey/quotas
  Tarifs: https://cloud.google.com/memorystore/valkey/pricing
  Notes de version: https://docs.cloud.google.com/memorystore/docs/valkey/release-notes
---

## Ce que c'est

Magasin **clé-valeur en mémoire** géré, décliné en quatre services qui exposent chacun le protocole de leur moteur d'origine : **Memorystore for Valkey**, **Memorystore for Redis Cluster**, **Memorystore for Redis**, et **Memorystore for Memcached** [!DECONSEILLE], ce dernier obsolète et appelé à fermer : Memorystore for Valkey est la cible de migration indiquée par Google. Les clients existants se connectent sans modification.

- **Partitions et nœuds.** Une instance Valkey ou Redis Cluster est faite de *partitions* (*shards*) de taille égale, chacune avec un nœud primaire et de zéro à cinq nœuds répliques, que le service répartit entre zones. En mode cluster désactivé, l'instance tient sur une seule partition.
- **Points de terminaison** : en mode cluster activé, un point de découverte permet au client de trouver les nœuds ; en mode cluster désactivé, un point d'écriture vers le primaire et un point de lecture qui répartit entre les répliques.
- **Disponibilité** : 99,99 % pour une instance Valkey ou Redis Cluster multizone avec haute disponibilité, 99,9 % en zone unique ou pour Memorystore for Redis en niveau Standard. Le type de nœud `shared-core-nano` n'a pas de SLA : c'est un type pour le développement.
- **Versions** : Valkey 7.2, 8.0, 9.0 et 9.1. Seul un sous-ensemble des commandes du moteur est exposé : celles qui administrent ou reconfigurent le serveur restent du ressort de Google.
- **Au-delà du cache** : recherche vectorielle, documents JSON et filtres de Bloom sont disponibles côté Valkey.
- **Réseau** : l'instance vit dans un VPC, joignable par IP privée ; le chiffrement en transit et l'authentification IAM sont optionnels.
- **Facturation** : à la capacité provisionnée, c'est-à-dire au nombre de nœuds et à leur type, pas au trafic.

> [!WARNING]
> Un cache n'est pas une base. La mémoire est volatile, les évictions surviennent dès que l'instance se remplit, et un redimensionnement ou une bascule peut perdre des clés. Toute donnée qui doit survivre appartient à une base durable ; Memorystore n'en détient qu'une copie.

## À quoi ça sert

- Cache devant une base relationnelle ou une API lente, selon le schéma *cache-aside* : lire le cache, retomber sur la base en cas d'absence, réécrire avec une durée de vie.
- Sessions applicatives, jetons, limitation de débit, verrous distribués.
- Classements, compteurs et files légères, en s'appuyant sur les structures de données du moteur : ensembles triés, listes, hachages.
- Mémoire partagée entre instances d'un service serverless, qui n'en a aucune en propre.

**À éviter** comme stockage principal, et pour des volumes qui ne tiennent pas en mémoire : la mémoire est ce qui coûte cher. À éviter aussi pour une file de messages durable (préférer [Pub/Sub](#pubsub)) et pour des accès clé-valeur à très gros volume sur disque (préférer [Bigtable](#bigtable)). Voir [Choisir une base de données](#choisir-une-base).

## Alternatives en logiciel libre

- **Valkey** : le fork de Redis maintenu par la Linux Foundation sous licence BSD ; c'est le moteur que Memorystore exécute.
- **Redis** : le moteur d'origine, proposé au choix sous licence AGPL v3, RSAL ou SSPL ; seule l'AGPL v3 en fait un logiciel libre.
- **Memcached** : cache clé-valeur minimal, sans persistance ni structures de données.
- **Apache Ignite** : grille de données en mémoire, avec calcul rapproché des données et requêtes SQL.
- [!SOMMEIL] **KeyDB** (BSD 3-Clause) : dérivé multithread de Redis.
