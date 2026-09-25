---
title: Artifact Registry
subgroup: CI/CD
icon: categories/devops
aka: Container Registry
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 308}
  nodes:
    ext: {label: Sources publiques, sub: "Docker Hub, PyPI", external: true, x: 10, y: 150, w: 150}
    cb: {label: Cloud Build, sub: construction des images, icon: categories/devops, x: 186, y: 36, w: 210}
    ar: {label: Artifact Registry, sub: dépôts Docker et paquets, icon: categories/devops, focus: true, x: 186, y: 140, w: 210, h: 60}
    aa: {label: Artifact Analysis, sub: "vulnérabilités, SBOM", icon: categories/devops, x: 186, y: 248, w: 210}
    run: {label: Cloud Run, sub: service déployé, icon: produits/cloud-run, x: 520, y: 36, w: 210}
    gke: {label: GKE, sub: cluster Kubernetes, icon: produits/gke, x: 520, y: 140, w: 210}
    cd: {label: Cloud Deploy, sub: pipeline de livraison, icon: categories/devops, x: 520, y: 248, w: 210}
  flows:
    - {from: ext, to: ar, text: "Un dépôt distant met en cache les dépendances publiques (Docker Hub, PyPI, Maven Central, Debian)"}
    - {from: cb, to: ar, text: "Le build pousse l'image, le paquet ou l'archive dans un dépôt standard"}
    - {from: ar, to: aa, text: "Chaque poussée déclenche l'analyse de vulnérabilités et l'écriture des métadonnées"}
    - {from: ar, to: run, from_offset: -15, text: "Cloud Run tire l'image par son digest au démarrage d'une révision"}
    - {from: ar, to: cd, from_offset: 15, text: "Cloud Deploy crée une release qui référence l'image du dépôt"}
    - {from: cd, to: gke, text: "Le rollout déploie cette image sur le cluster"}
captures:
  - image: https://docs.cloud.google.com/static/artifact-registry/docs/images/fingerprint-file-list.png
    page: https://docs.cloud.google.com/artifact-registry/docs/fingerprint
    legende: "Une version de paquet Maven dans un dépôt : fichiers publiés, tailles et empreintes, avec la commande gcloud de téléchargement"
docs:
  Documentation: https://docs.cloud.google.com/artifact-registry/docs
  Vue d'ensemble: https://docs.cloud.google.com/artifact-registry/docs/overview
  Formats pris en charge: https://docs.cloud.google.com/artifact-registry/docs/supported-formats
  Dépôts distants: https://docs.cloud.google.com/artifact-registry/docs/repositories/remote-repo
  Dépôts virtuels: https://docs.cloud.google.com/artifact-registry/docs/repositories/virtual-repo
  Règles de nettoyage: https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy
  Transition depuis Container Registry: https://docs.cloud.google.com/artifact-registry/docs/transition/transition-from-gcr
  API REST: https://docs.cloud.google.com/artifact-registry/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/artifacts
  Bibliothèques clientes: https://docs.cloud.google.com/artifact-registry/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/artifactregistry/latest
  Quotas et limites: https://docs.cloud.google.com/artifact-registry/quotas
  Tarifs: https://cloud.google.com/artifact-registry/pricing
  Notes de version: https://docs.cloud.google.com/artifact-registry/docs/release-notes
---

## Ce que c'est

Registre géré d'artefacts : images de conteneurs et paquets de langage ou de système, dans des dépôts régionaux ou multirégionaux d'un projet, sur le domaine `pkg.dev`.

- **Formats.** Docker (images OCI et chartes Helm empaquetées en OCI), Maven, npm, Python, Go, Apt, Yum, Kubeflow (modèles de pipelines), Generic (artefacts versionnés et immuables sans format particulier), ainsi que Ruby [!PREVERSION] et Conda [!PREVERSION].
- **Modes de dépôt.** *Standard* stocke les artefacts du projet. *Distant* (*remote*) sert de mandataire vers une source amont — Docker Hub, Maven Central, PyPI, Debian, CentOS, GitHub Container Registry, ou un autre dépôt standard — et met en cache à la première demande. *Connecteur* fait le même travail de mandataire sans rien mettre en cache, ce qui garde la source amont auditable. *Virtuel* regroupe plusieurs dépôts standard et distants derrière un seul point d'accès, avec une priorité par dépôt qui décide de l'ordre de recherche.
- **Nommage.** `LOCATION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE:TAG`, ou `@sha256:...` pour désigner une version par son *digest*. Les dépôts `gcr.io` restent servis par Artifact Registry.
- **Contrôle d'accès** IAM au niveau du dépôt, pas seulement du projet ; chiffrement par clés gérées par le client (CMEK), périmètre VPC Service Controls, journaux d'audit par dépôt.
- **Nettoyage.** Chaque dépôt porte des *règles de nettoyage* en JSON : règles de suppression (âge minimum ou maximum d'une version, filtres sur les tags et les préfixes) et règles de conservation (conditions, ou nombre de versions récentes à garder). En cas de conflit, la conservation l'emporte. Le mode *dry run* liste ce qui serait supprimé sans rien effacer.
- **Accélération.** Le *streaming* d'images réduit le temps de démarrage des charges GKE et de Managed Service for Apache Spark, en ne téléchargeant que les blocs lus.
- **Facturation** au stockage à la demi-gibioctet-mois près (les 0,5 premiers Gio par compte de facturation sont gratuits), au transfert sortant, et à l'analyse de vulnérabilités quand elle est activée. Un dépôt virtuel ne stocke rien : le coût revient à ses dépôts amont.

> [!TIP]
> Un dépôt distant pointant sur Docker Hub évite les limites de débit du registre public et rend les dépendances analysables et reproductibles. Pour les images Docker Hub les plus courantes, `mirror.gcr.io` fournit déjà un cache public entretenu par Google.

## À quoi ça sert

- Stocker les images produites par [Cloud Build](#cloud-build) et les servir à Cloud Run, GKE, Compute Engine ou App Engine, dans la même région que la charge.
- Héberger les paquets internes d'une entreprise (Maven, npm, Python, Debian) avec un contrôle d'accès par dépôt.
- Maîtriser les dépendances publiques : un dépôt distant les met en cache, [Artifact Analysis](#artifact-analysis) les analyse, un dépôt virtuel expose le tout derrière une URL unique aux postes de développement et aux builds.
- Servir de point de contrôle de la chaîne logicielle : les images y sont analysées à la poussée, et [Binary Authorization](#binary-authorization) peut n'autoriser au déploiement que celles qui viennent d'un dépôt de confiance.

**À éviter** comme espace de stockage générique : un artefact volumineux qui n'a pas vocation à être versionné et tiré par un gestionnaire de paquets coûte moins cher dans un bucket Cloud Storage (voir [Cloud Storage](#cloud-storage)). Éviter également de laisser un dépôt d'images de CI sans règle de nettoyage : chaque commit y dépose une image, et la facture de stockage suit.

## Alternatives en logiciel libre

- **Harbor** : registre d'images de la CNCF, le plus proche dans les usages — dépôts par projet, réplication, mandataire de cache vers un registre amont, analyse de vulnérabilités intégrée, signature.
- **Distribution** (l'implémentation de référence du registre OCI) : le socle minimal pour héberger des images, sans interface ni contrôle d'accès élaboré.
- **Zot** : registre conforme OCI, léger, avec analyse et synchronisation vers d'autres registres.
- **Pulp** : dépôts de paquets multiformats (Maven, npm, PyPI, images de conteneurs, RPM, Debian), avec synchronisation depuis des dépôts amont, pour l'équivalent des dépôts standard et distants.
- **devpi** (Python), **Verdaccio** (npm), **aptly** (Debian), **Athens** (modules Go) : mandataires et dépôts privés spécialisés par écosystème.
