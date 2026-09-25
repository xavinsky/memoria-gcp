---
title: Secret Manager
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 180, y: 60, w: 568, h: 246}
  nodes:
    admin: {label: Administrateur, sub: "gcloud secrets", external: true, x: 8, y: 16, w: 165}
    run: {label: Cloud Run, sub: "volume monté", icon: produits/cloud-run, x: 200, y: 96, w: 180}
    gke: {label: GKE, sub: "pilote CSI", icon: produits/gke, x: 200, y: 230, w: 180}
    sm: {label: Secret Manager, sub: "versions, alias", icon: categories/security-identity, focus: true, x: 410, y: 150, w: 200, h: 64}
    kms: {label: Cloud KMS, sub: "clé CMEK", icon: categories/security-identity, x: 410, y: 240, w: 200}
    sql: {label: Cloud SQL, sub: "mot de passe", icon: produits/cloud-sql, x: 620, y: 96, w: 128}
  flows:
    - {from: admin, to: sm, from_side: right, to_side: top, text: "Une nouvelle valeur est ajoutée comme version du secret ; les versions précédentes restent lisibles tant qu'on ne les a pas désactivées ou détruites."}
    - {from: kms, to: sm, control: true, text: "Si le secret porte une clé gérée par le client, Cloud KMS intervient à chaque accès : révoquer la clé rend le secret illisible sans avoir à le supprimer."}
    - {from: run, to: sm, to_offset: -12, text: "Le service Cloud Run lit la version latest, soit une fois au démarrage dans une variable d'environnement, soit à chaque lecture par un volume monté."}
    - {from: gke, to: sm, to_offset: 12, text: "Sur GKE, le pilote CSI Secrets Store monte la version dans le pod sans la recopier dans un objet Secret Kubernetes."}
    - {from: run, to: sql, text: "La valeur obtenue ouvre la connexion à la base ; la rotation programmée publie une notification Pub/Sub à laquelle le service réagit pour recharger."}
docs:
  Page produit: https://cloud.google.com/security/products/secret-manager
  Documentation: https://docs.cloud.google.com/secret-manager/docs
  Vue d'ensemble: https://docs.cloud.google.com/secret-manager/docs/overview
  Contrôle d'accès: https://docs.cloud.google.com/secret-manager/docs/access-control
  Rotation des secrets: https://docs.cloud.google.com/secret-manager/docs/secret-rotation
  Secrets régionaux et résidence: https://docs.cloud.google.com/secret-manager/regional-secrets/data-residency
  Parameter Manager: https://docs.cloud.google.com/secret-manager/parameter-manager/docs/overview
  API REST: https://docs.cloud.google.com/secret-manager/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/secrets
  Client Python: https://docs.cloud.google.com/python/docs/reference/secretmanager/latest
  Quotas et limites: https://docs.cloud.google.com/secret-manager/quotas
  Tarifs: https://cloud.google.com/secret-manager/pricing
  Notes de version: https://docs.cloud.google.com/secret-manager/docs/release-notes
---

## Ce que c'est

Un coffre pour les données sensibles qu'une application doit lire à l'exécution : mots de passe, clés d'API, jetons, certificats. Le service stocke la valeur, la versionne et en contrôle l'accès ; il ne fait aucune opération cryptographique pour le compte de l'appelant.

- **Deux ressources.** Un **secret** porte le nom, les libellés, la politique de réplication et les autorisations. Une **version de secret** porte la valeur elle-même. On lit toujours une version : par son numéro, par l'alias `latest`, ou par un **alias** défini à la main et déplacé d'une version à l'autre.
- **Cycle de vie des versions.** Ajouter une version n'écrase rien : les anciennes restent lisibles, ce qui permet un déploiement progressif et un retour arrière immédiat. Une version se **désactive** (réversible) puis se **détruit** (définitif). L'historique dit qui a modifié quoi et quand.
- **Chiffrement.** Tout est chiffré en transit par TLS et au repos en AES-256 avec des clés gérées par Google. Pour un contrôle plus fin, un secret peut être protégé par une clé **CMEK** de [Cloud KMS](#cloud-kms) : détruire la clé rend les valeurs inexploitables, sans toucher aux ressources.
- **Réplication.** Un secret **global** est répliqué **automatiquement** — Google choisit les emplacements, et la facturation ne compte qu'un seul emplacement — ou selon une liste de régions choisies, facturée par emplacement. Un secret **régional** reste dans une région donnée, pour répondre à une obligation de résidence des données.
- **Accès.** Les rôles IAM séparent l'administration (`roles/secretmanager.admin`) de la simple lecture de la valeur (`roles/secretmanager.secretAccessor`), et s'appliquent au projet ou à un secret précis. Les conditions IAM permettent par exemple de n'autoriser qu'un préfixe de nom.
- **Rotation.** Une période de rotation et une prochaine échéance déclenchent une notification **Pub/Sub** ; c'est au code abonné de produire la nouvelle valeur et d'ajouter la version. Le service ne fait pas tourner les identifiants tout seul.
- **Consommation.** [Cloud Run](#cloud-run) et [GKE](#gke) savent injecter un secret comme variable d'environnement — lue une fois au démarrage — ou comme fichier monté, relu à chaque accès. Les bibliothèques clientes et `gcloud secrets versions access` couvrent le reste.
- **Parameter Manager.** Extension du même service pour la configuration non sensible — chaînes de connexion, drapeaux de fonctionnalité, noms d'environnement — avec la possibilité de référencer un secret depuis un paramètre.
- **Facturation** au nombre de versions actives par mois, aux opérations d'accès et aux emplacements de réplication ; un palier gratuit couvre les usages modestes.

> [!TIP]
> Secret Manager stocke une valeur et vous la rend en clair ; [Cloud KMS](#cloud-kms) garde une clé que personne ne peut extraire et chiffre pour vous. Un mot de passe de base relève du premier, le chiffrement d'une colonne du second.

## À quoi ça sert

- Sortir les identifiants de base de données, les clés d'API partenaires et les jetons d'un dépôt Git ou d'un fichier de configuration.
- Donner à chaque service son compte de service et son secret, avec un rôle d'accès posé sur ce secret précis plutôt que sur le projet.
- Changer un identifiant compromis sans redéployer : ajouter une version, déplacer l'alias, désactiver l'ancienne — et retourner en arrière si la nouvelle échoue.
- Partager un certificat ou une clé privée entre plusieurs services de plusieurs projets, avec un seul point de révocation.
- Alimenter une chaîne [Cloud Build](#cloud-build) en identifiants de publication sans les écrire dans le fichier de build.
- Répondre à une obligation de résidence en créant des secrets régionaux dans le pays concerné.

**À éviter** pour du chiffrement applicatif ou pour de gros volumes de données : la manipulation de clés, la signature et le chiffrement par enveloppe relèvent de [Cloud KMS](#cloud-kms). À éviter aussi pour de la configuration ordinaire, plus simple à gérer dans Parameter Manager ou dans les variables d'environnement du service — chaque version de secret est facturée. Enfin, ce n'est pas un gestionnaire d'identifiants dynamiques : il ne sait pas créer un compte de base à la demande avec une durée de vie, il ne fait que garder la valeur qu'on lui donne.

## Alternatives en logiciel libre

- **OpenBao** : fork libre de Vault sous licence MPL-2.0 — stockage de secrets, moteurs d'identifiants dynamiques, location avec durée de vie et révocation, bien au-delà du simple stockage versionné.
- **Infisical** : gestionnaire de secrets pour équipes de développement, avec agent d'injection, intégrations CI/CD et détection de fuites dans les dépôts.
- **SOPS** : chiffrement de fichiers de configuration (YAML, JSON, .env) champ par champ, avec des clés age ou PGP — l'approche « secrets dans le dépôt, mais chiffrés ».
- **Sealed Secrets** de Bitnami : même idée côté Kubernetes, un contrôleur du cluster étant le seul à pouvoir déchiffrer les manifestes publiés.
- **External Secrets Operator** : la brique qui synchronise un coffre externe vers des objets Secret Kubernetes, comme le pilote CSI le fait pour Secret Manager.
- **Barbican**, le service de secrets d'OpenStack : stockage de valeurs et de certificats adossé à un HSM, pour un environnement sur site complet.
