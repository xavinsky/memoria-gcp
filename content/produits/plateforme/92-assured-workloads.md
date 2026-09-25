---
title: Assured Workloads
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Organisation, x: 190, y: 16, w: 558, h: 290}
  nodes:
    support: {label: Assistance Google, sub: "personnel habilité", external: true, x: 8, y: 220, w: 175}
    orgpol: {label: Règles d'administration, sub: "contraintes appliquées", icon: categories/management-tools, x: 210, y: 30, w: 240}
    aw: {label: Assured Workloads, sub: "dossier sous contrôles", icon: categories/security-identity, focus: true, x: 210, y: 120, w: 240, h: 56}
    proj: {label: Projets conformes, sub: "régions autorisées", icon: categories/management-tools, x: 210, y: 220, w: 240}
    kms: {label: Cloud KMS, sub: "CMEK obligatoire", icon: categories/security-identity, x: 495, y: 30, w: 240}
    viol: {label: Suivi des violations, sub: "écarts détectés", icon: categories/security-identity, x: 495, y: 120, w: 240}
    at: {label: Access Transparency, sub: "journaux d'accès", icon: categories/security-identity, x: 495, y: 220, w: 240}
  flows:
    - {from: orgpol, to: aw, control: true, text: "Le package de contrôles choisi à la création du dossier se traduit en contraintes de règles d'administration : régions autorisées, chiffrement imposé, partage limité au domaine."}
    - {from: aw, to: proj, text: "Tous les projets créés dans le dossier héritent de ces contraintes ; un service que le package ne couvre pas ne peut tout simplement pas y être activé."}
    - {from: aw, to: kms, from_offset: -14, text: "Plusieurs packages imposent des clés gérées par le client, dans un projet de clés distinct et dans un emplacement conforme."}
    - {from: aw, to: viol, from_offset: 14, text: "Le suivi permanent signale la dérive : une ressource créée hors de la frontière ou une contrainte désactivée ouvre une violation."}
    - {from: aw, to: at, from_offset: 24, text: "Access Transparency journalise chaque accès du personnel Google aux ressources du dossier, avec le motif de l'intervention."}
    - {from: support, to: proj, control: true, text: "L'assistance n'intervient que par du personnel qui remplit les critères du package : localisation géographique, vérifications d'antécédents, périmètre d'action."}
docs:
  Page produit: https://cloud.google.com/security/products/assured-workloads
  Documentation: https://docs.cloud.google.com/assured-workloads/docs
  Vue d'ensemble: https://docs.cloud.google.com/assured-workloads/docs/overview
  Packages de contrôles: https://docs.cloud.google.com/assured-workloads/docs/control-packages
  Produits compatibles: https://docs.cloud.google.com/assured-workloads/docs/supported-products
  Référence des contrôles: https://docs.cloud.google.com/assured-workloads/docs/cloud-control-reference
  Résidence des données: https://docs.cloud.google.com/assured-workloads/docs/data-residency
  Gestion des clés: https://docs.cloud.google.com/assured-workloads/docs/key-management
  Surveiller un dossier: https://docs.cloud.google.com/assured-workloads/docs/monitor-folder
  Access Transparency: https://docs.cloud.google.com/assured-workloads/docs/access-transparency
  Approbation d'accès: https://docs.cloud.google.com/assured-workloads/docs/access-approval
  VPC Service Controls: https://docs.cloud.google.com/assured-workloads/docs/configure-vpc-sc
  Journaux d'audit: https://docs.cloud.google.com/assured-workloads/docs/audit-logging
  API REST: https://docs.cloud.google.com/assured-workloads/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/assured
  Tarifs: https://cloud.google.com/assured-workloads/pricing
  Notes de version: https://docs.cloud.google.com/assured-workloads/docs/release-notes
---

## Ce que c'est

Un mécanisme qui applique à un **dossier** de la hiérarchie des ressources un jeu de contrôles prédéfini, pour que tout ce qui y est créé respecte une réglementation ou une exigence de souveraineté — sans quitter l'infrastructure commerciale de Google Cloud.

- **Package de contrôles.** Le cœur du produit : choisi à la création du dossier, il fixe les garde-fous appliqués à tous les projets et à toutes les ressources qui s'y trouvent, par des contraintes de règles d'administration et par des réglages internes. La liste des produits utilisables dépend du package.
- **Frontières régionales.** Des packages de **résidence des données** qui limitent les régions où les ressources peuvent exister : frontière de données de l'UE, du Canada, de l'Australie, du Japon, de l'Inde, de la Suisse, d'Israël, du Brésil, de l'Arabie saoudite et d'autres. Certains y ajoutent le contrôle de l'accès du fournisseur, par approbation motivée.
- **Frontières réglementaires.** Des packages calés sur un texte : FedRAMP Moderate et High, IL2, IL4, IL5, CJIS, ITAR, IRS Publication 1075, Canada Controlled Goods Program, contrôles santé et sciences de la vie pour HIPAA et HITRUST.
- **Sovereign Controls by Partners.** Des packages opérés avec un partenaire local, qui détient les clés, instruit les justifications d'accès et conduit les audits — la réponse aux exigences de souveraineté les plus strictes.
- **Accès du personnel Google.** L'**Assured Support**, disponible avec les offres d'assistance Enhanced ou Premium, impose aux intervenants Google des critères de localisation et d'habilitation propres au package. **Access Transparency** journalise chaque accès avec son motif, et **Access Approval** permet de l'autoriser au cas par cas.
- **Clés.** Selon le package, l'usage de **clés gérées par le client** ([Cloud KMS](#cloud-kms)) est imposé, souvent dans un projet de clés séparé et dans un emplacement conforme, pour garantir la séparation des tâches.
- **Surveillance.** Le service détecte en continu les **violations** — ressource créée hors de la frontière, contrainte désactivée — et les remonte pour correction. Les mises à jour de conformité publiées par Google s'appliquent au dossier existant.
- **Ce que ça ne fait pas.** Assured Workloads ne certifie pas l'application : il fournit l'environnement et la preuve technique. La conformité reste une responsabilité partagée, et l'architecture applicative, les traitements et les contrats en font partie.

> [!WARNING]
> Un package restreint fortement le catalogue disponible : de nombreux services n'existent pas dans un dossier FedRAMP High ou ITAR, et une région conforme n'offre pas toutes les fonctions. Vérifier la liste des produits compatibles **avant** de concevoir l'architecture, pas après.

## À quoi ça sert

- Héberger dans l'UE une charge de travail dont les données ne doivent ni être stockées ni être traitées ailleurs, avec la preuve que la contrainte est appliquée par la plateforme.
- Répondre à une exigence FedRAMP, ITAR ou CJIS sans monter un environnement séparé : le dossier suffit, le reste de l'organisation continue normalement.
- Démontrer à un régulateur qui, chez le fournisseur, a pu accéder aux données, quand et pour quel motif.
- Cloisonner une filiale ou un marché soumis à une réglementation locale, avec son propre dossier et son propre package.
- Repérer immédiatement une dérive : un projet créé dans une région non autorisée, une contrainte levée par erreur.
- Satisfaire une exigence contractuelle de chiffrement par clés client sur toute une branche de la hiérarchie, sans compter sur la discipline des équipes.

**À éviter** quand le besoin se résume à « garder les données dans telle région » : une contrainte d'organisation `gcp.resourceLocations` couvre ce cas, sans les restrictions de catalogue d'un package. À éviter aussi comme protection contre l'exfiltration, que le produit ne traite pas directement — c'est [VPC Service Controls](#vpc-service-controls), que les packages recommandent d'ailleurs de configurer en complément. Enfin, un dossier Assured Workloads ne se convertit pas d'un package à un autre : le choix se fait à la création et engage les projets qu'il contiendra.

## Alternatives en logiciel libre

Il n'existe pas d'équivalent : les contrôles reposent sur des engagements contractuels et opérationnels du fournisseur (localisation du personnel, habilitations, transparence des accès), qu'un logiciel ne peut pas fournir. Sur un environnement que l'on exploite soi-même, les briques suivantes couvrent la partie technique.

- **Open Policy Agent** avec **Gatekeeper**, ou **Kyverno** : refus des ressources qui ne respectent pas une règle — région, chiffrement, étiquetage — au moment de leur création, ce que font les contraintes d'organisation.
- **Cloud Custodian** : inventaire, détection de dérive et correction automatique à partir de règles déclaratives.
- **OpenSCAP** et les profils **SCAP Security Guide** : évaluation de conformité d'un système à un référentiel (CIS, DISA STIG), avec rapport exploitable en audit.
- **Checkov** et **tfsec** : contrôle des mêmes exigences en amont, dans le code d'infrastructure, avant tout déploiement.
- **Wazuh** : surveillance continue avec modules de conformité PCI DSS, HIPAA et GDPR, pour la partie preuve permanente.
