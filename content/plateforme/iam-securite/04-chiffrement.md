---
title: "Chiffrement : Cloud KMS, HSM, EKM"
subgroup: Protection des données
---

Toutes les données au repos sur Google Cloud sont déjà chiffrées, en AES-256, par des clés que Google gère sans aucune action du client. Choisir une option de chiffrement ne consiste donc pas à « activer le chiffrement » mais à décider **qui détient la clé** et **qui peut la couper** : Google, le client dans [Cloud KMS](#cloud-kms), un module matériel dédié, ou un gestionnaire externe hors de Google. Le chiffrement en transit est lui aussi automatique ; seul le chiffrement **en cours d'utilisation**, en mémoire, demande un choix de machine (Confidential Computing).

Le pilier sécurité du [Well-Architected Framework](#well-architected) résume la démarche : partir du chiffrement par défaut, ajouter des clés gérées par le client (CMEK) là où une exigence le justifie, en privilégiant Autokey, et réserver Cloud EKM aux clés qui ne doivent pas quitter l'entreprise ([*Implement security by design*](https://docs.cloud.google.com/architecture/framework/security/implement-security-by-design)).

![Arbre de décision : de l'exigence sur les clés au niveau de protection](../../svg/choix-protection-cles.svg)

## Matrice de choix

| Option | Qui détient la clé | Ce qu'on contrôle | Coût (USD) | Exploitation |
|---|---|---|---|---|
| **Chiffrement par défaut** | Google, clés internes invisibles | Rien | Inclus | Aucune |
| **CMEK logiciel** (`SOFTWARE`) | Cloud KMS, projet du client | Emplacement, rotation, désactivation, destruction, IAM, journaux d'accès | 0,06 $ par version active et par mois ; 0,03 $ les 10 000 opérations | Trousseaux, clés, rôles et rotation à gérer |
| **Autokey** | Cloud KMS, clés `HSM` créées à la demande | Comme une clé HSM ; l'administrateur KMS garde la main | Prix des clés HSM ; 100 versions gratuites par mois | Configuration unique par dossier ou projet |
| **Cloud HSM** (`HSM`) | Modules matériels Google certifiés FIPS 140-2 niveau 3, partagés | Idem CMEK, plus une attestation par clé | 1 $ par version et par mois (AES-256, RSA 2048) ; 2,50 $ pour RSA 3072/4096 et EC | Comme CMEK logiciel |
| **Cloud HSM mono-locataire** (`HSM_SINGLE_TENANT`) | Partitions HSM dédiées, administrées par le client | Isolement cryptographique, accès de Google accordé ou retiré, quorum d'administrateurs | 3 500 $ par instance et par mois, clés comprises jusqu'à 15 000 versions | Quorum, clés de contrôle hors Google, rafraîchissement tous les 730 jours ; régions limitées |
| **Cloud EKM** (`EXTERNAL`, `EXTERNAL_VPC`) | Gestionnaire externe d'un partenaire | Google ne voit jamais le matériel de la clé ; le gestionnaire peut refuser chaque opération | 3 $ par version et par mois, plus la facture du partenaire | Disponibilité du gestionnaire externe à garantir ; tous les services CMEK ne l'acceptent pas |
| **CSEK** (clé fournie à chaque requête) | Le client, hors de Google | Tout, y compris la perte définitive | Inclus | Clé à transmettre à chaque appel ; Cloud Storage seulement |

Tarifs de la [page de prix Cloud KMS](https://cloud.google.com/kms/pricing), consultée en septembre 2026. Tout est facturé au projet qui porte la clé, même quand elle protège une ressource d'un autre projet. Une version désactivée ou programmée pour destruction reste facturée ; seule une version détruite est gratuite.

- **CMEK** (*customer-managed encryption keys*) : le service chiffre ses données avec ses propres clés de données, que la clé KMS **enveloppe**. Désactiver la clé rend les données illisibles ; détruire sa version les rend irrécupérables (*crypto-shredding*). La liste des services compatibles, et de ceux qui acceptent Cloud EKM, est sur la page [CMEK integrations](https://docs.cloud.google.com/kms/docs/compatible-services).
- **Autokey** est le choix recommandé par Google dès que ses clés conviennent : protection HSM, AES-256-GCM, rotation annuelle, clé dans l'emplacement de la ressource, trousseau nommé `autokey`, rôle de chiffrement accordé à l'agent de service du produit. Le développeur ou le pipeline IaC n'a besoin d'aucun droit élevé : il demande une clé en créant la ressource. Il fonctionne avec un projet de clés dédié par dossier ou avec des clés dans le projet de la ressource ; il ne couvre ni les emplacements sans Cloud HSM ni tous les services.
- **Cloud EKM** passe par internet ou par un réseau VPC. La voie VPC est plus disponible, mais n'existe pas dans les emplacements multirégionaux ; la voie internet n'existe pas en `global` ni en `nam-eur-asia1`. **Key Access Justifications** ajoute à chaque opération un code de justification que le gestionnaire externe peut utiliser pour refuser.
- **CSEK** (*customer-supplied encryption keys*) : Cloud Storage reçoit une clé AES-256 en base64 à chaque requête, ne la conserve pas, et ne garde qu'une empreinte. Sur Compute Engine, les CSEK [!DECONSEILLE] sont dépréciées : aucune nouvelle ressource ne peut en utiliser, et leur suppression complète est fixée au 20 juillet 2027 ([page de dépréciation](https://docs.cloud.google.com/compute/docs/deprecations/csek-deprecation-in-compute-engine)). La migration passe par une copie chiffrée en CMEK.

## Concevoir la gestion des clés

- **Trousseau, clé, version.** Le trousseau (*key ring*) fixe l'emplacement et porte les rôles communs ; la clé porte l'usage et la période de rotation ; la version contient le matériel. Trousseaux et clés ne se suppriment jamais, et aucune ressource KMS ne change d'emplacement après sa création.
- **Emplacement aligné sur la donnée.** La clé doit être dans l'emplacement de la ressource qu'elle protège : trousseau `europe-west1` pour un bucket `EUROPE-WEST1`, trousseau `us` pour un bucket en birégion configurable `US-EAST1` + `US-WEST1`, `nam4` pour la birégion prédéfinie `NAM4`. Une clé `global` ne protège pas une ressource régionale.
- **Projet de clés séparé.** Les clés vivent dans un projet dédié, par environnement ou par dossier, comme dans le [plan de fondations d'entreprise](https://docs.cloud.google.com/architecture/blueprints/security-foundations/organization-structure) (`prj-c-kms`, `prj-{env}-kms`). L'équipe qui administre les clés (`roles/cloudkms.admin`) n'a pas le droit de chiffrer ni de déchiffrer ; l'agent de service du produit (voir [agent de service](#lexterm-agent-de-service)) reçoit `roles/cloudkms.cryptoKeyEncrypterDecrypter` sur la seule clé qu'il utilise. Voir [IAM : bonnes pratiques](#iam-bonnes-pratiques).
- **Granularité.** Une clé par ressource sensible, ou par ensemble de ressources qui partagent le même cycle de vie : la destruction d'une clé doit viser exactement ce qu'on veut effacer.
- **Rotation.** Automatique pour les clés symétriques, à une période choisie (90 jours est la valeur courante) ; à la main pour les clés asymétriques et EKM. Une rotation crée une nouvelle version primaire mais ne rechiffre pas les données existantes : les anciennes versions restent actives, donc facturées, tant qu'elles protègent quelque chose.
- **Imposer par règle d'administration.** `constraints/gcp.restrictNonCmekServices` refuse la création de ressources sans CMEK pour les services listés ; `constraints/gcp.restrictCmekCryptoKeyProjects` n'accepte que les clés des projets de clés désignés ; `constraints/cloudkms.allowedProtectionLevels` limite les niveaux de protection. Voir [Hiérarchie des ressources](#hierarchie-des-ressources).
- **Suivi.** Le tableau de bord Cloud KMS indique, pour chaque clé, les ressources qu'elle protège (*key usage tracking*) : à consulter avant toute désactivation.

## Exemple Pulumi

Clé HSM dans un projet de clés, accordée à l'agent de service Cloud Storage du projet de données, puis bucket chiffré par défaut avec cette clé :

```python
import pulumi
import pulumi_gcp as gcp

cfg = pulumi.Config()
projet_cles = cfg.require("projet_cles")        # projet dédié aux clés
projet_donnees = cfg.require("projet_donnees")

trousseau = gcp.kms.KeyRing("trousseau",
    project=projet_cles, name="donnees", location="europe-west1")

cle = gcp.kms.CryptoKey("cle-brut",
    key_ring=trousseau.id, name="bucket-brut",
    rotation_period="7776000s",                 # 90 jours
    version_template={
        "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION",
        "protection_level": "HSM",
    },
    opts=pulumi.ResourceOptions(protect=True))  # la détruire rendrait le bucket illisible

agent_gcs = gcp.storage.get_project_service_account(project=projet_donnees)

acces = gcp.kms.CryptoKeyIAMMember("agent-gcs",
    crypto_key_id=cle.id,
    role="roles/cloudkms.cryptoKeyEncrypterDecrypter",
    member=f"serviceAccount:{agent_gcs.email_address}")

bucket = gcp.storage.Bucket("brut",
    project=projet_donnees, location="EUROPE-WEST1",  # même emplacement que le trousseau
    uniform_bucket_level_access=True,
    encryption={"default_kms_key_name": cle.id},
    opts=pulumi.ResourceOptions(depends_on=[acces]))
```

`depends_on` évite une course : un bucket créé avant le rôle échoue. Un `pulumi destroy` sur une `CryptoKey` ne supprime pas la clé mais **détruit toutes ses versions** ; d'où `protect=True`. Avec Autokey, on remplace les trois premières ressources par un `gcp.kms.KeyHandle` (`resource_type_selector="storage.googleapis.com/Bucket"`) et on passe sa sortie `kms_key` au bucket.

## Chiffrement en transit et en cours d'utilisation

**En transit.** Le trafic entre un client et les API ou load balancers de Google passe en TLS (ou QUIC), terminé par le Google Front End. Entre services Google, ALTS authentifie et chiffre. Le trafic entre VM d'un VPC ou de VPC appairés est chiffré et authentifié au niveau du réseau virtuel, **à condition de passer par des adresses internes** : entre adresses IP externes, il ne l'est pas automatiquement ([*Encryption in transit*](https://docs.cloud.google.com/docs/security/encryption-in-transit)). Pour les liens vers le site : IPsec avec [Cloud VPN](#cloud-vpn), MACsec en option sur [Cloud Interconnect](#cloud-interconnect). Le TLS applicatif, mTLS compris, se règle sur le [load balancer](#cloud-load-balancing) et dans [Cloud Service Mesh](#cloud-service-mesh).

**En cours d'utilisation.** Confidential Computing chiffre la mémoire dans un environnement d'exécution de confiance (*TEE*) matériel, avec attestation à distance :

| Produit | Ce qu'il protège | Technologie | Quand |
|---|---|---|---|
| **Confidential VM** | Mémoire d'une VM Compute Engine, inaccessible à l'hyperviseur | AMD SEV (N2D, C2D, C3D, C4D), AMD SEV-SNP, Intel TDX ; GPU NVIDIA H100 confidentiels sur A3 | Données réglementées traitées en clair, exigence de chiffrement en mémoire |
| **Confidential GKE Nodes** | Nœuds GKE en Confidential VM, sur tout le cluster ou par pool | Mêmes technologies, selon le type de machine | Conteneurs sur données sensibles, Standard ou Autopilot |
| **Confidential Space** | Charge conteneurisée sur image durcie, qui ne reçoit ses secrets qu'après attestation | Confidential VM, Google Cloud Attestation ou Intel Trust Authority | Calcul à plusieurs parties sur des données qu'aucune ne doit voir, opérateur compris |

Dataflow, Managed Service for Apache Spark et Vertex AI Workbench acceptent aussi des workers en Confidential VM. Le surcoût est un forfait par vCPU et par Go de mémoire en plus du prix de la VM ; seules les machines AMD SEV en N2D et C3D gardent la migration à chaud.

## Pièges

- **Désactiver une clé, c'est couper le service.** Les lectures et écritures échouent dès que la désactivation se propage, en général en moins d'une minute, parfois après plusieurs heures. Certains services perdent définitivement des données si la clé reste indisponible trop longtemps. Vérifier le suivi d'usage de la clé avant de toucher à son état.
- **La destruction est programmée, puis définitive.** Une version reste 30 jours en « programmée pour destruction » par défaut (réglable à la création, avec un minimum imposable par règle d'administration), puis son matériel disparaît. Une sauvegarde chiffrée par cette clé ne vaut plus rien. Sur Cloud Storage, les objets restent facturés tant qu'on ne les supprime pas.
- **L'agent de service oublié.** L'erreur la plus fréquente : le rôle est accordé à l'utilisateur ou au compte de service de l'application, alors que c'est l'agent de service du produit (`service-PROJECT_NUMBER@...`) qui appelle la clé. Certains agents n'existent qu'après un premier appel à l'API ou une création explicite (commande [!PREVERSION] `gcloud beta services identity create`).
- **Clé et ressource dans des emplacements différents.** La création échoue, ou la ressource ne peut pas être déplacée ensuite. Pour une ressource multirégionale, la clé doit être dans la multirégion correspondante, où Cloud EKM par VPC n'existe pas.
- **Cloud EKM par internet.** La disponibilité des données dépend alors du gestionnaire externe et du chemin internet ; Google recommande Cloud HSM ou EKM par VPC.
- **HSM mono-locataire non rafraîchi.** Sans opération de rafraîchissement approuvée par le quorum avant la date limite, l'instance se désactive et toutes ses clés avec. Perdre le quorum des clés de contrôle rend l'instance irrécupérable, et supprimer le projet détruit ses clés.
- **CMEK partout par principe.** Chaque clé ajoute un point de panne, un coût et une dépendance entre projets. Réserver CMEK aux données qui ont une exigence réelle ; le reste relève de la [gouvernance des données](#donnees-sensibles-et-gouvernance) et des [périmètres](#perimetres-vpc-sc).

## Alternatives en logiciel libre

- **OpenBao** (MPL 2.0) : le moteur *transit* chiffre, déchiffre, signe et fait tourner les clés sans jamais les rendre, comme Cloud KMS ; il s'adosse à un HSM par PKCS#11 pour le niveau matériel.
- **PyKMIP** (Apache 2.0) : serveur et client KMIP, le protocole standard des gestionnaires de clés, pour relier un HSM d'entreprise à des applications, dans le rôle d'un EKM.
- **SoftHSM** (BSD) : jeton PKCS#11 logiciel, pour développer et tester contre l'interface d'un HSM sans matériel.
- **Tink** (Apache 2.0, dépôts `tink-crypto/tink-py`, `tink-java`…) : bibliothèque de Google qui implémente le chiffrement par enveloppe et la rotation, avec une clé locale ou un KMS distant comme clé maîtresse.
- **SOPS** (MPL 2.0) : chiffrement de fichiers de configuration valeur par valeur, avec des clés age, PGP ou un KMS ; la version libre du « chiffrer côté client ».
- **Confidential Containers** (Apache 2.0, projet CNCF) : pods Kubernetes exécutés dans des VM confidentielles (SEV-SNP, TDX), avec un service d'attestation qui ne libère les secrets qu'aux charges vérifiées ; le pendant ouvert de Confidential GKE Nodes et de Confidential Space.
- **LUKS / cryptsetup** (GPL v2) : chiffrement de disque sous Linux, avec une clé que l'on détient ; ce que CSEK offrait pour les disques Compute Engine.
