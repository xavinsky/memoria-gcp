---
title: Cloud Identity
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Compte Cloud Identity, x: 195, y: 16, w: 290, h: 290}
    - {label: Google Cloud, x: 550, y: 16, w: 200, h: 290}
  nodes:
    ad: {label: Active Directory, sub: "annuaire existant", external: true, x: 8, y: 40, w: 175}
    idpext: {label: Fournisseur SAML, sub: "Entra ID, Okta, ADFS", external: true, x: 8, y: 210, w: 175}
    ou: {label: Unités organisationnelles, sub: "paramètres hérités", icon: categories/security-identity, x: 210, y: 30, w: 250}
    ci: {label: Cloud Identity, sub: "comptes gérés", icon: categories/security-identity, focus: true, x: 210, y: 120, w: 250, h: 64}
    grp: {label: Groupes, sub: "adhésions, groupes dynamiques", icon: categories/security-identity, x: 210, y: 226, w: 250}
    iam: {label: IAM, sub: "rôles sur les projets", icon: categories/security-identity, x: 565, y: 120, w: 185}
  flows:
    - {from: ad, to: ci, text: "Google Cloud Directory Sync, ou un connecteur SCIM, recopie les utilisateurs et les groupes de l'annuaire existant dans le compte Cloud Identity."}
    - {from: idpext, to: ci, control: true, text: "La connexion elle-même est déléguée au fournisseur SAML de l'entreprise : Google ne détient plus de mot de passe, seulement l'identité et ses attributs."}
    - {from: ci, to: ou, text: "Chaque compte appartient à une seule unité organisationnelle, qui porte les paramètres hérités : validation en deux étapes, gestion des appareils, services autorisés."}
    - {from: ci, to: grp, text: "Les groupes rassemblent les comptes par fonction ; un groupe dynamique se remplit tout seul à partir d'une requête sur les attributs des utilisateurs."}
    - {from: grp, to: iam, text: "C'est au groupe qu'IAM accorde les rôles sur les dossiers et les projets : l'arrivée ou le départ d'un collaborateur se règle dans l'annuaire, jamais dans les stratégies."}
docs:
  Documentation: https://docs.cloud.google.com/identity/docs
  Vue d'ensemble: https://docs.cloud.google.com/identity/docs/overview
  Éditions: https://docs.cloud.google.com/identity/docs/editions
  Groupes: https://docs.cloud.google.com/identity/docs/groups
  Groupes dynamiques: https://docs.cloud.google.com/identity/docs/concepts/overview-dynamic-groups
  Créer un groupe dynamique: https://docs.cloud.google.com/identity/docs/how-to/create-dynamic-groups
  Appareils: https://docs.cloud.google.com/identity/docs/concepts/overview-devices
  APIs disponibles: https://docs.cloud.google.com/identity/docs/apis
  Configurer l'API Groups: https://docs.cloud.google.com/identity/docs/how-to/setup
  API REST: https://docs.cloud.google.com/identity/docs/reference/rest
  Modèle d'identité Google: https://docs.cloud.google.com/architecture/identity/overview-google-authentication
  Architectures de référence: https://docs.cloud.google.com/architecture/identity/reference-architectures
  Fédérer avec Active Directory: https://docs.cloud.google.com/architecture/identity/federating-gcp-with-active-directory-introduction
  Notes de version: https://docs.cloud.google.com/identity/docs/release-notes
---

## Ce que c'est

L'annuaire des **collaborateurs** : comptes, groupes, unités organisationnelles et appareils, pour une organisation qui utilise Google Cloud sans forcément utiliser Gmail ou Drive. Cloud Identity et Google Workspace partagent la même plateforme technique — mêmes APIs, même console d'administration, même notion de compte comme conteneur d'utilisateurs identifié par un nom de domaine ; pour gérer des identités, les deux sont équivalents, Workspace ajoutant par-dessus les services de collaboration.

- **Compte géré.** Un compte utilisateur dont l'organisation contrôle entièrement le cycle de vie, identifié par son adresse e-mail principale, qui doit appartenir à un domaine vérifié (principal, secondaire ou alias). Les alias et l'adresse de récupération ne sont pas des identités et ne servent pas à se connecter. Adopter Cloud Identity, c'est aussi reprendre la main sur les **comptes personnels non gérés** créés avec une adresse du domaine.
- **Unité organisationnelle.** Un conteneur hiérarchique de comptes, auquel s'appliquent des paramètres hérités par les sous-unités : validation en deux étapes, gestion des appareils, attribution de licences. Un compte appartient à une seule unité. Les unités organisationnelles ne servent pas à gérer les accès — cela reste le travail des groupes — et elles n'ont aucun rapport avec les dossiers Google Cloud.
- **Groupes.** L'unité de gestion des accès. Un groupe peut contenir des utilisateurs, d'autres groupes et des comptes de service. Un **groupe dynamique** définit ses membres par une requête sur les attributs (service, intitulé de poste, localisation) et se met à jour tout seul. Les **groupes de sécurité** se distinguent des listes de diffusion et sont les seuls à accepter certains usages sensibles.
- **Fédération.** Deux axes indépendants. La **synchronisation** des comptes et des groupes depuis un annuaire existant — Active Directory via Google Cloud Directory Sync, Microsoft Entra ID ou Okta via SCIM. L'**authentification unique** SAML, qui renvoie la connexion vers le fournisseur d'identité de l'entreprise : Google ne détient alors plus de mot de passe.
- **Appareils.** L'inventaire et la gestion des terminaux (mobile, ordinateurs) qui accèdent aux données de l'organisation, avec verrouillage et effacement à distance ; c'est aussi la source des signaux d'appareil utilisés par l'accès contextuel.
- **Deux éditions.** **Free** : gestion des comptes, des groupes et gestion fondamentale des terminaux. **Premium** : SLA de 99,9 %, assistance 24/7, gestion avancée et d'entreprise des appareils, accès contextuel, audit et journaux d'événements étendus, gestion des applications tierces. L'édition premium n'est pas nécessaire pour utiliser Google Cloud.
- **APIs.** L'API Cloud Identity couvre les groupes et leurs adhésions, les appareils, les domaines autorisés et les règles ; l'API Admin SDK Directory complète pour les utilisateurs et les unités organisationnelles.

> [!WARNING]
> Les comptes de service n'appartiennent pas au domaine Cloud Identity : partager un document « avec tout le domaine » ne les inclut pas, et ils ne peuvent pas posséder de fichier Workspace.

## À quoi ça sert

- Donner une identité d'entreprise aux personnes qui travaillent sur Google Cloud, quand l'organisation n'utilise pas Google Workspace.
- Accorder les rôles [IAM](#cloud-iam) à des groupes plutôt qu'à des personnes : le départ d'un collaborateur se traite dans l'annuaire, sans relire les stratégies de chaque projet.
- Conserver Active Directory ou Entra ID comme source de vérité, Google Cloud n'en recevant qu'une copie synchronisée et déléguant la connexion au fournisseur existant.
- Faire correspondre automatiquement l'organigramme et les droits, avec des groupes dynamiques fondés sur le service ou le poste.
- Imposer la validation en deux étapes et les règles de session par unité organisationnelle, y compris pour les seuls administrateurs.
- Reprendre le contrôle de comptes personnels créés avec une adresse professionnelle, en les transférant vers le compte géré.

**À éviter** pour les utilisateurs d'une application que l'on édite : leurs comptes n'ont rien à faire dans l'annuaire interne, c'est [Identity Platform](#identity-platform) qui les gère. À éviter aussi comme substitut aux dossiers de la hiérarchie des ressources : les unités organisationnelles rangent des personnes, les dossiers rangent des projets, et les deux arborescences n'ont pas à se ressembler. Enfin, l'édition premium ne se justifie que si l'on a besoin de la gestion avancée des appareils, de l'accès contextuel ou du SLA — sans cela, l'édition gratuite couvre tout l'usage Google Cloud.

## Alternatives en logiciel libre

- **Keycloak** : annuaire d'utilisateurs et de groupes, fédération LDAP et SAML, authentification unique — le socle le plus proche pour une organisation qui veut héberger son propre fournisseur d'identité.
- **Authentik** : même rôle, avec des flux d'inscription et de provisionnement (SCIM) configurables, et une administration plus légère.
- **FreeIPA** : annuaire, Kerberos, PKI et gestion des politiques de machines, l'équivalent libre d'un domaine Active Directory pour un parc Linux.
- **Samba** en contrôleur de domaine Active Directory : pour garder la compatibilité avec des postes Windows existants.
- **OpenLDAP** et **LLDAP** : l'annuaire lui-même, du plus complet au plus simple, quand seul le référentiel d'utilisateurs et de groupes est nécessaire.
- **Zitadel** : plateforme d'identité avec organisations, rôles et audit intégré, utilisable à la fois pour les collaborateurs et pour les utilisateurs d'une application.
