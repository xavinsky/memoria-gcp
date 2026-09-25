---
title: Secure Source Manager
subgroup: Dépôts
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: "Projet GCP, périmètre VPC Service Controls", x: 176, y: 16, w: 572, h: 268}
  nodes:
    dev: {label: Développeurs, sub: "clone, push, revues", external: true, x: 8, y: 124, w: 150}
    dc: {label: Developer Connect, sub: "proxy Git en lecture", icon: categories/developer-tools, x: 246, y: 36, w: 220}
    ssm: {label: Secure Source Manager, sub: "instance régionale", icon: categories/developer-tools, focus: true, x: 246, y: 120, w: 220, h: 64}
    kms: {label: Cloud KMS, sub: "clé CMEK", icon: categories/security-identity, x: 246, y: 216, w: 220}
    cb: {label: Cloud Build, sub: "fichier de déclencheurs", icon: categories/devops, x: 540, y: 80, w: 200}
    ar: {label: Artifact Registry, sub: "images produites", icon: categories/devops, x: 540, y: 180, w: 200}
  flows:
    - {from: dev, to: ssm, to_offset: -16, text: "Les développeurs clonent et poussent en HTTPS ou en SSH ; l'accès est accordé par IAM, au niveau de l'instance puis de chaque dépôt."}
    - {from: dev, to: ssm, to_offset: 16, text: "Les revues se font dans l'interface web de l'instance : pull requests, relecteurs requis, fils de commentaires et tickets."}
    - {from: ssm, to: cb, text: "Un fichier de déclencheurs versionné dans le dépôt lance une exécution Cloud Build à chaque commit ou pull request, et renvoie son état comme contrôle de fusion."}
    - {from: cb, to: ar, text: "La construction publie ses images et ses paquets dans Artifact Registry."}
    - {from: kms, to: ssm, control: true, text: "L'instance chiffre ses données au repos avec une clé gérée dans Cloud KMS ; clé désactivée, les dépôts deviennent illisibles."}
    - {from: dc, to: ssm, control: true, text: "Branchée sur Developer Connect, l'instance se laisse cloner par le proxy Git en accès privé, sans exposer son adresse publique ; le proxy ne gère que la lecture."}
docs:
  Page produit: https://cloud.google.com/products/secure-source-manager
  Documentation: https://docs.cloud.google.com/secure-source-manager/docs
  Vue d'ensemble: https://docs.cloud.google.com/secure-source-manager/docs/overview
  Créer une instance: https://docs.cloud.google.com/secure-source-manager/docs/create-instance
  Tickets et pull requests: https://docs.cloud.google.com/secure-source-manager/docs/work-with-issues-pull-requests
  Protection des branches: https://docs.cloud.google.com/secure-source-manager/docs/branch-protection-overview
  Contrôle d'accès IAM: https://docs.cloud.google.com/secure-source-manager/docs/access-control
  Connexion à Cloud Build: https://docs.cloud.google.com/secure-source-manager/docs/connect-cloud-build
  Clés de chiffrement CMEK: https://docs.cloud.google.com/secure-source-manager/docs/cmek
  Périmètre VPC Service Controls: https://docs.cloud.google.com/secure-source-manager/docs/configure-service-perimeter
  API REST: https://docs.cloud.google.com/secure-source-manager/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/source-manager
  Client Python: https://docs.cloud.google.com/python/docs/reference/securesourcemanager/latest
  Quotas et limites: https://docs.cloud.google.com/secure-source-manager/docs/quotas
  Tarifs: https://cloud.google.com/products/secure-source-manager/pricing
  Notes de version: https://docs.cloud.google.com/secure-source-manager/docs/release-notes
---

## Ce que c'est

Forge Git gérée par Google, déployée en région et **mono-locataire** : l'instance n'est partagée avec aucun autre client.

- **Instance et dépôts.** On crée d'abord une instance dans une région, joignable par son URI ; les dépôts se créent ensuite dedans, depuis l'interface web ou l'API. Instances et dépôts sont deux niveaux de ressources IAM distincts, avec leurs propres rôles. Une instance ne doit réunir que les utilisateurs d'un seul client, sauf collaboration contractuelle entre entreprises.
- **Git complet.** Tous les clients Git standard fonctionnent, en HTTPS comme en SSH, avec authentification par clé publique.
- **Revue de code.** Pull requests et tickets sont intégrés : relecteurs, libellés, jalons, assignations, dates d'échéance, fils de commentaires, notifications sur les dépôts suivis.
- **Protection des branches.** Des règles par branche, ou pour toutes : exiger une pull request avant fusion, un nombre minimal de relecteurs et d'approbateurs, bloquer la fusion si de nouveaux commits arrivent après approbation, exiger que les commentaires soient résolus, imposer un historique linéaire, exiger des contrôles de build réussis.
- **Chiffrement et isolement.** Chiffrement au repos par défaut avec des clés Google, ou **CMEK** avec une clé gérée dans Cloud Key Management Service. L'instance se place dans un périmètre **VPC Service Controls** pour se prémunir de l'exfiltration. Le service est conforme FedRAMP High et HIPAA.
- **Intégrations.** Un fichier de déclencheurs versionné dans le dépôt relie celui-ci à [Cloud Build](#cloud-build) ; des webhooks branchent Jenkins ou tout autre service. Via [Developer Connect](#developer-connect), le proxy Git donne un accès privé en lecture aux dépôts, sans exposer l'instance sur Internet.
- **Facturation** à l'instance et au mois, quel que soit le nombre d'utilisateurs — 1 000 $ par mois et par instance, au prorata pour un mois entamé.

> [!WARNING]
> Cloud Source Repositories est fermé aux nouveaux clients : seule une organisation qui l'utilise déjà peut en activer l'API, et un projet sans organisation ne le peut pas. Secure Source Manager est l'hébergement de code que Google recommande. Ni les dépôts Cloud Build (2ᵉ génération) ni Developer Connect ne savent se rattacher à un dépôt Cloud Source Repositories.

## À quoi ça sert

- Héberger le code source dans Google Cloud, dans une région choisie, quand la sortie des sources hors du périmètre est proscrite.
- Imposer une revue de code et des contrôles de build réussis avant fusion, avec des droits gérés par IAM comme le reste du projet.
- Répondre à une exigence de mono-location, de clés gérées par le client ou de conformité FedRAMP High et HIPAA sur le dépôt lui-même.
- Servir de source aux chaînes CI/CD du projet : fichier de déclencheurs vers [Cloud Build](#cloud-build), qui publie ensuite ses artefacts dans [Artifact Registry](#artifact-registry), ou webhook vers un moteur existant.

**À éviter** quand le code vit déjà chez GitHub, GitLab ou Bitbucket et qu'on ne cherche qu'à le brancher sur Google Cloud : [Developer Connect](#developer-connect) fait le pont sans migration ni coût fixe. À éviter aussi pour un projet isolé ou une petite équipe : le forfait mensuel par instance est le même pour deux personnes que pour deux cents, et l'écosystème d'extensions d'une forge publique n'a pas d'équivalent ici.

## Alternatives en logiciel libre

- **Forgejo** : forge Git légère sous licence GPLv3, tickets et pull requests intégrés, la plus proche en usage d'une instance auto-hébergée.
- **Gitea** : même famille, licence MIT, écosystème d'actions compatible avec la syntaxe GitHub Actions.
- **GitLab CE** : licence MIT, forge complète avec intégration continue native ; les règles de protection de branche les plus fines relèvent en revanche de l'édition Enterprise, qui n'est pas libre.
- **Gerrit** : licence Apache 2.0, revue commit par commit avec notation explicite — le modèle le plus strict pour imposer une relecture.
- **Apache Allura**, **Gogs** : forges plus légères, pour un besoin d'hébergement simple.
