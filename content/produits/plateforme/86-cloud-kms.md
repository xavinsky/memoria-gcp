---
title: Cloud KMS
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet de clés, x: 195, y: 16, w: 290, h: 290}
    - {label: Projet de données, x: 505, y: 16, w: 243, h: 290}
  nodes:
    ekm: {label: Gestionnaire externe, sub: "clés hors de Google", external: true, x: 8, y: 130, w: 175}
    kr: {label: Trousseau de clés, sub: "REGION", icon: categories/security-identity, x: 210, y: 40, w: 250}
    key: {label: Cloud KMS, sub: "clé CMEK, rotation", icon: categories/security-identity, focus: true, x: 210, y: 130, w: 250, h: 64}
    hsm: {label: Cloud HSM, sub: "FIPS 140-2 niveau 3", icon: categories/security-identity, x: 210, y: 230, w: 250}
    gcs: {label: Cloud Storage, sub: "bucket chiffré", icon: produits/cloud-storage, x: 520, y: 40, w: 210}
    agent: {label: Agent de service, sub: "Encrypter/Decrypter", icon: categories/security-identity, x: 520, y: 130, w: 210}
    bq: {label: BigQuery, sub: "ensemble de données", icon: produits/bigquery, x: 520, y: 230, w: 210}
  flows:
    - {from: kr, to: key, control: true, text: "Le trousseau fixe l'emplacement et sert d'unité d'administration : les rôles IAM s'y posent une fois pour toutes les clés qu'il contient."}
    - {from: hsm, to: key, text: "Le niveau de protection HSM confie la génération et l'usage de la clé à un cluster de modules matériels certifiés FIPS 140-2 niveau 3 ; le matériel ne sort jamais du module."}
    - {from: ekm, to: key, control: true, text: "Une clé Cloud EKM ne contient aucun matériel cryptographique : chaque opération est relayée au gestionnaire externe, par internet ou par un VPC, et celui-ci peut la refuser."}
    - {from: key, to: agent, text: "L'agent de service du produit consommateur reçoit le rôle CryptoKey Encrypter/Decrypter sur la clé : c'est lui, et non l'appelant, qui demande le déchiffrement."}
    - {from: agent, to: gcs, text: "Le bucket déclare la clé comme clé par défaut ; à chaque écriture, la clé de chiffrement des données est enveloppée par la clé KMS."}
    - {from: agent, to: bq, text: "Le même mécanisme protège un ensemble de données BigQuery ; détruire la version de clé rend toutes les données qu'elle protège définitivement illisibles."}
docs:
  Page produit: https://cloud.google.com/security/products/security-key-management
  Documentation: https://docs.cloud.google.com/kms/docs
  Vue d'ensemble: https://docs.cloud.google.com/kms/docs/key-management-service
  Hiérarchie des ressources: https://docs.cloud.google.com/kms/docs/resource-hierarchy
  Algorithmes: https://docs.cloud.google.com/kms/docs/algorithms
  Rotation des clés: https://docs.cloud.google.com/kms/docs/key-rotation
  Clés gérées par le client (CMEK): https://docs.cloud.google.com/kms/docs/cmek
  Chiffrement par enveloppe: https://docs.cloud.google.com/kms/docs/envelope-encryption
  Cloud HSM: https://docs.cloud.google.com/kms/docs/hsm
  Cloud EKM: https://docs.cloud.google.com/kms/docs/ekm
  Autokey: https://docs.cloud.google.com/kms/docs/autokey-overview
  Emplacements: https://docs.cloud.google.com/kms/docs/locations
  API REST: https://docs.cloud.google.com/kms/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/kms
  Client Python: https://docs.cloud.google.com/python/docs/reference/cloudkms/latest
  Quotas et limites: https://docs.cloud.google.com/kms/quotas
  Tarifs: https://cloud.google.com/kms/pricing
  Notes de version: https://docs.cloud.google.com/kms/docs/release-notes
---

## Ce que c'est

Le service de gestion de clés cryptographiques : on y crée, importe ou référence des clés, on les utilise à travers l'API, et le matériel de la clé reste inaccessible — il n'existe aucun moyen de l'exporter.

- **Ressources.** Un **trousseau de clés** (*key ring*) appartient à un emplacement et regroupe des **clés** ; chaque clé possède des **versions**, et l'une d'elles est primaire. Trousseaux et clés ne se suppriment pas : seules les versions se détruisent, après un délai d'attente de 30 jours par défaut, réglable de 24 heures à 120 jours à la création de la clé.
- **Quatre niveaux de protection.** **Software** : clés logicielles, uniques au client, primitives validées FIPS 140-3 niveau 1 (module BoringCrypto), 0,06 $ par version active et par mois. **Cloud HSM** : clés générées et utilisées dans un cluster de modules matériels certifiés **FIPS 140-2 niveau 3**, de 1 à 2,50 $ par version et par mois, avec l'option d'une instance HSM **mono-locataire** pour un isolement supplémentaire. **Cloud EKM** : la clé vit chez un partenaire externe, Google ne fait que relayer chaque opération, 3 $ par version et par mois. **External** via un gestionnaire tiers relié par VPC, avec possibilité de piloter le cycle de vie depuis Cloud KMS pour les partenaires qui gèrent le plan de contrôle.
- **Usages.** Chiffrement et déchiffrement symétriques ou asymétriques, signature numérique et vérification, MAC, et encapsulation de clé. Les algorithmes disponibles dépendent du niveau de protection.
- **CMEK et chiffrement par enveloppe.** Dans plus de quarante services intégrés, la clé KMS ne chiffre pas les données elles-mêmes : elle **enveloppe** la clé de chiffrement des données produite par le service. Ce sont les *customer-managed encryption keys*, qui donnent le contrôle de l'emplacement, de la rotation, de la révocation et de la destruction — donc la possibilité d'effacer des données par destruction de clé (*crypto-shredding*).
- **Qui appelle la clé.** L'intégration CMEK passe par l'**agent de service** du produit consommateur, à qui l'on accorde le rôle `roles/cloudkms.cryptoKeyEncrypterDecrypter` sur la clé. Retirer ce rôle coupe l'accès aux données sans les supprimer.
- **Rotation.** Les clés symétriques se font tourner automatiquement selon une période choisie : une nouvelle version devient primaire, les anciennes restent actives pour déchiffrer. Les clés asymétriques et les clés EKM se font tourner à la main.
- **Autokey.** Provisionnement à la demande : au lieu de préparer trousseaux, clés et comptes de service, ils sont créés au moment où la ressource l'est, avec des réglages conformes aux recommandations (protection HSM, séparation des rôles, rotation, emplacement). Autokey ne coûte rien de plus que les clés HSM produites, et il n'exige pas de privilèges élevés pour le développeur ou le pipeline d'infrastructure.
- **Emplacements.** Une clé est régionale, birégionale ou multirégionale ; une ressource ne peut être protégée que par une clé d'un emplacement compatible avec le sien.
- **Chiffrement par défaut.** Sans rien configurer, toutes les données au repos de Google Cloud sont déjà chiffrées par des clés internes que l'on ne voit pas. Passer en CMEK n'ajoute pas du chiffrement : cela transfère le contrôle des clés.

> [!WARNING]
> Détruire une version de clé est irréversible passé le délai d'attente, et rend illisibles **toutes** les données qu'elle protégeait, dans tous les services. C'est la contrepartie du contrôle : la sauvegarde d'une donnée chiffrée ne vaut rien sans la clé.

## À quoi ça sert

- Répondre à une exigence réglementaire ou contractuelle de maîtrise des clés sur des buckets [Cloud Storage](#cloud-storage), des ensembles [BigQuery](#bigquery), des disques [Compute Engine](#compute-engine) ou des instances [Cloud SQL](#cloud-sql).
- Établir une frontière cryptographique par client ou par environnement : une clé dédiée, un trousseau dédié, un projet de clés séparé du projet de données.
- Garantir qu'une donnée redevient illisible à la fin d'un contrat, en détruisant la clé plutôt qu'en traquant chaque copie.
- Conserver le contrôle hors de Google avec Cloud EKM, quand la politique interne impose que les clés ne quittent pas le HSM de l'entreprise ou d'un tiers de confiance.
- Chiffrer côté client dans une application, avec le chiffrement par enveloppe : la clé de données reste locale et n'est envoyée à KMS que pour être enveloppée.
- Signer des artefacts ou des jetons avec une clé asymétrique qui ne quitte jamais le service.

**À éviter** pour stocker une valeur qu'on doit pouvoir relire en clair : un mot de passe ou un jeton relève de [Secret Manager](#secret-manager), pas d'un magasin de clés. À éviter aussi pour chiffrer de gros volumes en appelant l'API à chaque bloc — les quotas de chiffrement et la latence y font obstacle, le chiffrement par enveloppe est fait pour ça. Enfin, activer CMEK partout par principe a un coût réel, en argent et en exploitation : une clé mal répliquée ou mal localisée rend un service indisponible, et le chiffrement par défaut de Google suffit à la plupart des données.

## Alternatives en logiciel libre

- **OpenBao** : le moteur de transit fait exactement le travail de Cloud KMS — chiffrement, déchiffrement, signature et rotation sans jamais rendre la clé — sous licence MPL-2.0.
- **Barbican** : service de gestion de clés et de secrets d'OpenStack, capable de s'adosser à un HSM par PKCS#11.
- **SoftHSM** : implémentation logicielle d'un jeton PKCS#11, pour développer et tester contre l'interface d'un HSM sans matériel.
- **PyKMIP** : serveur et client KMIP, le protocole standard des gestionnaires de clés d'entreprise, utile pour s'interfacer avec un HSM existant.
- **Tink** : bibliothèque cryptographique publiée par Google, qui implémente le chiffrement par enveloppe et sait utiliser indifféremment une clé locale ou un service de KMS distant.
- **age** et **SOPS** : pour le cas plus modeste du chiffrement de fichiers et de configurations, avec des clés gérées par l'équipe.
