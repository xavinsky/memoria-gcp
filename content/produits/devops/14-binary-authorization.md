---
title: Binary Authorization
subgroup: CI/CD
icon: categories/devops
schema:
  size: [760, 340]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 578, h: 308}
  nodes:
    ar: {label: Artifact Registry, sub: image par digest, icon: categories/devops, x: 186, y: 36, w: 210}
    cb: {label: Cloud Build, sub: signe l'image, icon: categories/devops, x: 186, y: 140, w: 210}
    aa: {label: Artifact Analysis, sub: "attestations, notes", icon: categories/devops, x: 186, y: 248, w: 210}
    gke: {label: GKE, sub: contrôleur d'admission, icon: produits/gke, x: 506, y: 36, w: 230}
    ba: {label: Binary Authorization, sub: règle de déploiement, icon: categories/devops, focus: true, x: 506, y: 140, w: 230, h: 60}
    run: {label: Cloud Run, sub: révision admise ou refusée, icon: produits/cloud-run, x: 506, y: 248, w: 230}
  flows:
    - {from: cb, to: ar, text: "Le build pousse l'image dans le dépôt, où elle est identifiée par son digest"}
    - {from: cb, to: aa, text: "Le build signe le digest avec une clé KMS et dépose l'attestation en métadonnée"}
    - {from: ar, to: gke, text: "Un déploiement demande à GKE de lancer cette image"}
    - {from: gke, to: ba, control: true, text: "Le contrôleur d'admission interroge la règle avant de créer le pod"}
    - {from: run, to: ba, control: true, text: "Cloud Run soumet chaque nouvelle révision à la même règle"}
    - {from: ba, to: aa, control: true, text: "La règle exige une attestation : l'attestor en vérifie la signature auprès d'Artifact Analysis"}
captures:
  - image: https://docs.cloud.google.com/static/binary-authorization/docs/images/default-rule-policy-tab.png
    page: https://docs.cloud.google.com/binary-authorization/docs/run/configure-policy-cloud-run
    legende: "La stratégie Binary Authorization du projet : règle par défaut, règles par cluster, mode test et images exemptées"
docs:
  Documentation: https://docs.cloud.google.com/binary-authorization/docs
  Vue d'ensemble: https://docs.cloud.google.com/binary-authorization/docs/overview
  Concepts: https://docs.cloud.google.com/binary-authorization/docs/key-concepts
  Référence YAML de la règle: https://docs.cloud.google.com/binary-authorization/docs/policy-yaml-reference
  Attestations: https://docs.cloud.google.com/binary-authorization/docs/attestations
  Créer des attestations: https://docs.cloud.google.com/binary-authorization/docs/making-attestations
  Mode dry-run: https://docs.cloud.google.com/binary-authorization/docs/enabling-dry-run
  Activer sur un cluster GKE: https://docs.cloud.google.com/binary-authorization/docs/enable-cluster
  Binary Authorization pour Cloud Run: https://docs.cloud.google.com/binary-authorization/docs/run/overview
  Validation continue: https://docs.cloud.google.com/binary-authorization/docs/overview-cv
  Intégration Cloud Build: https://docs.cloud.google.com/binary-authorization/docs/cloud-build
  Bris de glace: https://docs.cloud.google.com/binary-authorization/docs/using-breakglass
  API REST: https://docs.cloud.google.com/binary-authorization/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/container/binauthz
  Quotas et limites: https://docs.cloud.google.com/binary-authorization/quotas
  Tarifs: https://cloud.google.com/binary-authorization/pricing
  Notes de version: https://docs.cloud.google.com/binary-authorization/docs/release-notes
---

## Ce que c'est

Contrôle au moment du déploiement : seules les images de conteneurs conformes à une règle du projet peuvent être lancées. Le produit reprend la spécification **Kritis** du projet ouvert **Grafeas**.

- **Deux usages.** *Appliquer* : un point d'application refuse le déploiement des images non conformes. *Surveiller* : la validation continue (CV) [!PREVERSION] réexamine périodiquement les images des pods déjà en cours d'exécution et journalise les écarts dans Cloud Logging, sans rien interrompre.
- **Plateformes** : GKE, Cloud Run, Cloud Service Mesh, Google Distributed Cloud, GKE sur AWS et clusters rattachés.
- **Règle.** Chaque projet a exactement une règle (*project-singleton policy*), définie dans le projet où tourne la plateforme de déploiement. Elle contient une **règle par défaut** (`defaultAdmissionRule`), des **règles spécifiques** (`clusterAdmissionRule`, et sur GKE par espace de noms ou par compte de service Kubernetes ; Cloud Run n'accepte que la règle par défaut) et une **liste d'images exemptées** (`admissionWhitelistPatterns`). La validation continue utilise un autre type de règle, la *platform policy*.
- **Modes d'évaluation** (`evaluationMode`) : tout autoriser, tout refuser, ou **exiger des attestations** — un signataire doit avoir signé le *digest* de l'image, et un **attestor** vérifie cette signature au déploiement.
- **Modes d'application** (`enforcementMode`) : *Block and Audit Log* refuse le déploiement et journalise le motif ; **Dry Run: Audit Log Only** laisse passer l'image non conforme mais écrit le détail dans les journaux d'audit. Le mode *dry-run* sert à éprouver une règle en production avant de la rendre bloquante.
- **Attestations et attestors.** Une attestation certifie qu'une image a franchi une étape : construction par une chaîne de confiance, passage des tests, validation manuelle. Elle est signée avec une clé (Cloud KMS ou PGP) et stockée en occurrence [Artifact Analysis](#artifact-analysis). Un attestor est la ressource qui porte la clé publique correspondante. Une configuration multiprojet permet de séparer la plateforme de déploiement, les attestors et les attestations.
- **Images exemptées.** Le drapeau `globalPolicyEvaluationMode` fait confiance aux images système entretenues par Google — à préférer à un ajout manuel dans la liste d'exemptions, sous peine de bloquer le démarrage d'un cluster.
- **Bris de glace.** L'annotation *breakglass* sur un pod, ou l'option équivalente sur Cloud Run, contourne la règle en cas d'urgence, en laissant une trace dans les journaux d'audit.
- **Facturation** : gratuit sur Cloud Run. Sur GKE, 0,01613 $ par cluster et par heure — environ 12 $ par mois — quelle que soit la taille du cluster, avec 12 $ de crédit mensuel par compte de facturation, soit un cluster gratuit.

> [!WARNING]
> La règle s'évalue sur le *digest* de l'image. Un déploiement qui désigne l'image par un tag mouvant est refusé ou résolu de façon imprévisible : figer `IMAGE@sha256:...` est la condition d'un contrôle fiable. [Cloud Deploy](#cloud-deploy) reprend la référence qu'on lui passe : c'est au build de fournir le digest.

## À quoi ça sert

- Garantir qu'aucune image ne peut être lancée en production sans être passée par la chaîne officielle : construite par [Cloud Build](#cloud-build), analysée, attestée.
- Restreindre les déploiements aux images d'un dépôt [Artifact Registry](#artifact-registry) donné, et exclure toute image tirée directement d'un registre public.
- Matérialiser une séparation des tâches : l'équipe qui signe les attestations de qualité n'est pas celle qui déploie, et les attestors vivent dans un projet distinct.
- Détecter une dérive sur l'existant : la validation continue signale les pods dont l'image ne respecte plus la règle, même s'ils tournaient déjà.

**À éviter** comme unique contrôle d'admission Kubernetes : Binary Authorization ne juge que la provenance et les attestations d'une image, pas le contenu du manifeste. Les contraintes sur les privilèges, les limites de ressources, les *labels* ou les réseaux relèvent de Policy Controller, de Kyverno ou d'OPA Gatekeeper. Éviter aussi d'activer directement le mode bloquant sur un cluster existant : passer d'abord par *dry-run*, lire les journaux d'audit, puis durcir.

## Alternatives en logiciel libre

- **Kritis** : l'implémentation de référence de la spécification dont Binary Authorization est issu, contrôleur d'admission qui vérifie les attestations Grafeas sur un cluster Kubernetes.
- **Sigstore** — `cosign` pour signer et vérifier les images, **Fulcio** pour les certificats éphémères, **Rekor** pour le journal de transparence : la chaîne de signature d'artefacts la plus répandue aujourd'hui.
- **Kyverno** : moteur de règles Kubernetes, dont la règle `verifyImages` vérifie les signatures `cosign` et les attestations à l'admission — l'équivalent fonctionnel le plus direct.
- **OPA Gatekeeper** : contrôleur d'admission générique piloté par des règles Rego, pour un contrôle plus large que la seule provenance des images.
- **Connaisseur** : contrôleur d'admission spécialisé dans la vérification des signatures d'images (Notary v1, `cosign`).
- **in-toto** : cadre d'attestation de bout en bout d'une chaîne logicielle, le format que reprennent les provenances SLSA et les attestations DSSE.
