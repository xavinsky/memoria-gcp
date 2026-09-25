---
title: Artifact Analysis
subgroup: CI/CD
icon: categories/devops
aka: Container Analysis
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 308}
  nodes:
    cb: {label: Cloud Build, sub: provenance SLSA, icon: categories/devops, x: 186, y: 36, w: 210}
    ar: {label: Artifact Registry, sub: images et paquets, icon: categories/devops, x: 186, y: 140, w: 210}
    gcs: {label: Cloud Storage, sub: SBOM au format SPDX, icon: produits/cloud-storage, x: 186, y: 248, w: 210}
    scc: {label: Security Command Center, sub: vue centralisée des risques, icon: produits/security-command-center, x: 504, y: 36, w: 230}
    aa: {label: Artifact Analysis, sub: "notes, occurrences", icon: categories/devops, focus: true, x: 504, y: 140, w: 230, h: 60}
    ba: {label: Binary Authorization, sub: contrôle au déploiement, icon: categories/devops, x: 504, y: 248, w: 230}
  flows:
    - {from: ar, to: aa, text: "Chaque image poussée dans un dépôt est analysée une fois, d'après son digest"}
    - {from: cb, to: aa, to_offset: -20, text: "Cloud Build dépose la provenance du build et les attestations signées en métadonnées"}
    - {from: aa, to: gcs, from_offset: 20, text: "Le SBOM généré est écrit dans un bucket du projet, avec une occurrence qui pointe dessus"}
    - {from: aa, to: scc, text: "Les vulnérabilités trouvées remontent dans Security Command Center"}
    - {from: ba, to: aa, control: true, text: "Au déploiement, Binary Authorization vérifie les attestations stockées ici"}
captures:
  - image: https://docs.cloud.google.com/artifact-analysis/images/vulnerabilities-tab.png
    page: https://docs.cloud.google.com/artifact-analysis/docs/scan-os-automatically
    legende: "Résultats d'analyse d'une image : vulnérabilités par gravité, correctifs disponibles et liste des CVE par paquet"
docs:
  Documentation: https://docs.cloud.google.com/artifact-analysis/docs
  Vue d'ensemble: https://docs.cloud.google.com/artifact-analysis/docs/artifact-analysis
  Types d'analyse: https://docs.cloud.google.com/artifact-analysis/docs/scanning-types
  Analyse des conteneurs: https://docs.cloud.google.com/artifact-analysis/docs/container-scanning-overview
  Analyse à la demande: https://docs.cloud.google.com/artifact-analysis/docs/scan-os-on-demand
  Gestion des métadonnées: https://docs.cloud.google.com/artifact-analysis/docs/metadata-management-overview
  SBOM: https://docs.cloud.google.com/artifact-analysis/docs/sbom-overview
  Générer et stocker les SBOM: https://docs.cloud.google.com/artifact-analysis/docs/generate-store-sboms
  Déclarations VEX: https://docs.cloud.google.com/artifact-analysis/docs/create-vex
  Niveaux de gravité: https://docs.cloud.google.com/artifact-analysis/docs/severity-levels
  APIs du service: https://docs.cloud.google.com/artifact-analysis/docs/apis
  API REST: https://docs.cloud.google.com/artifact-analysis/docs/reference/rest
  Bibliothèques clientes: https://docs.cloud.google.com/artifact-analysis/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/containeranalysis/latest
  Maîtriser les coûts: https://docs.cloud.google.com/artifact-analysis/docs/controlling-costs
  Tarifs: https://cloud.google.com/artifact-analysis/pricing
---

## Ce que c'est

Famille de services d'analyse de composition logicielle et de stockage de métadonnées. Ses points de détection sont intégrés à d'autres produits — [Artifact Registry](#artifact-registry), GKE — et ses métadonnées sont lisibles par n'importe quel outil de la chaîne.

- **Analyse automatique.** Activée par dépôt, elle se déclenche à chaque poussée d'une image dans un dépôt Docker d'Artifact Registry. L'image n'est analysée qu'une fois, d'après son *digest* : ajouter ou modifier un tag ne relance rien. Elle couvre les paquets système (Debian, Ubuntu, Alpine, RHEL et UBI, Rocky, AlmaLinux, SLES, CentOS, Wolfi, Chainguard, Distroless) et les paquets applicatifs (Go, Java, Node.js, Python, PHP, Ruby, Rust, .NET). Les paquets malveillants recensés par l'OpenSSF sont signalés en gravité CRITICAL. La détection de secrets [!PREVERSION] repère les clés d'API et les clés de comptes de service.
- **Analyse continue.** Après l'analyse initiale, les métadonnées sont réactualisées plusieurs fois par jour à mesure que les bases de vulnérabilités évoluent : occurrences créées, mises à jour ou supprimées. Une image qui n'a pas été tirée depuis 30 jours cesse d'être suivie ; ses résultats deviennent obsolètes, puis archivés après 90 jours. Tirer l'image relance le suivi, sous 24 heures.
- **Analyse à la demande.** `gcloud artifacts docker images scan` analyse une image locale ou distante sans la pousser dans un dépôt. Les résultats restent disponibles 48 heures et ne sont pas réactualisés — pratique pour bloquer un pipeline avant publication.
- **Métadonnées.** Le service repose sur **Grafeas**, dont le modèle distingue la *note* (une métadonnée générique, écrite par un fournisseur : une vulnérabilité, un builder de confiance) et l'*occurrence* (l'instanciation de cette note sur un artefact précis). Les types pris en charge : vulnérabilité, build (provenance), paquet, découverte, attestation, évaluation de vulnérabilité (VEX) et référence SBOM. Notes et occurrences se placent volontiers dans des projets distincts, pour séparer les droits d'écriture et de lecture.
- **SBOM.** Artifact Analysis génère les nomenclatures logicielles au format SPDX 2.3, et accepte l'import de SBOM produits ailleurs. Le fichier est stocké dans un bucket Cloud Storage du projet ; une occurrence de type *référence SBOM* en donne l'emplacement, l'empreinte et une signature DSSE de charge utile `application/vnd.in-toto+json`, vérifiable.
- **Attestations.** Une attestation est un document signé qui certifie qu'une image a franchi une étape : build par une chaîne de confiance, passage des tests, validation manuelle. Elle est stockée en occurrence et lue au déploiement par [Binary Authorization](#binary-authorization).
- **VEX.** Une déclaration VEX (*Vulnerability Exploitability eXchange*) dit qu'une vulnérabilité détectée n'est pas exploitable dans ce contexte ; elle est stockée en note d'évaluation de vulnérabilité et évite de traiter un faux positif à chaque analyse.
- **Facturation** à l'analyse : 0,26 $ par analyse automatique d'image, facturée une seule fois par *digest* ; les analyses suivantes de la même image sont gratuites. L'analyse de paquets hors conteneur n'est pas dédupliquée. Les clients Security Command Center relèvent d'une tarification propre à leur niveau de service.

> [!WARNING]
> Activer l'API lance la facturation immédiatement, mais n'analyse pas les images déjà présentes : il faut les pousser à nouveau pour obtenir un premier résultat.

## À quoi ça sert

- Connaître les vulnérabilités des images d'un projet, en continu, sans étape d'analyse à écrire dans le pipeline.
- Bloquer un build : une étape `gcloud artifacts docker images scan` suivie d'un seuil de gravité arrête la chaîne avant la poussée.
- Produire et conserver les preuves attendues par un audit : SBOM, provenance de build, attestations, avec un horodatage et une signature.
- Alimenter les décisions de déploiement : [Binary Authorization](#binary-authorization) s'appuie sur les attestations, et les tableaux de bord de sécurité de Cloud Build, Cloud Run et GKE sur les résultats d'analyse.

**À éviter** comme audit de sécurité complet : c'est une analyse de composition, qui compare les paquets installés à des bases publiques de vulnérabilités. Elle ne dit rien du code maison, des erreurs de configuration ou des droits IAM — ce terrain relève de Security Command Center et des analyses statiques. Éviter aussi de laisser l'analyse automatique activée sur un dépôt de CI qui reçoit des dizaines d'images par jour sans règle de nettoyage : la facture suit le nombre de *digests* distincts.

## Alternatives en logiciel libre

- **Trivy** : analyseur d'images, de systèmes de fichiers et de dépôts, qui couvre paquets système, dépendances applicatives, secrets et erreurs de configuration ; l'équivalent le plus complet.
- **Grype** et **Syft** (Anchore) : l'un analyse les vulnérabilités, l'autre produit le SBOM (SPDX, CycloneDX) ; ensemble, ils reprennent le couple analyse et nomenclature.
- **OSV-Scanner** et la base **OSV.dev** : détection des vulnérabilités des dépendances à partir d'un format de données ouvert.
- **Clair** : analyseur de vulnérabilités de conteneurs orienté service, celui qu'embarque Harbor.
- **Grafeas** : le modèle de notes et d'occurrences sur lequel Artifact Analysis est bâti, utilisable seul comme entrepôt de métadonnées.
- **Sigstore** (`cosign`, Rekor, Fulcio) : signature et attestations *in-toto* d'artefacts, avec journal de transparence, face aux attestations d'Artifact Analysis.
- **Dependency-Track** : plateforme de suivi des SBOM dans la durée, pour la partie conservation et exploitation des nomenclatures.
