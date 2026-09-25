---
title: Identity Platform
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 250, y: 16, w: 498, h: 290}
  nodes:
    users: {label: Utilisateurs finaux, sub: "web, mobile", external: true, x: 8, y: 40, w: 180}
    idps: {label: Fournisseurs d'identité, sub: "Google, SAML, OIDC", external: true, x: 8, y: 220, w: 210}
    bf: {label: Blocking functions, sub: "Cloud Run functions", icon: produits/cloud-run, x: 270, y: 30, w: 220}
    ip: {label: Identity Platform, sub: "locataires, jetons", icon: categories/security-identity, focus: true, x: 270, y: 120, w: 220, h: 64}
    iap: {label: Identity-Aware Proxy, sub: "applications internes", icon: categories/security-identity, x: 270, y: 226, w: 220}
    api: {label: Cloud Run, sub: "API applicative", icon: produits/cloud-run, x: 530, y: 120, w: 200}
  flows:
    - {from: users, to: ip, text: "L'application appelle le SDK client ; l'utilisateur s'authentifie par e-mail et mot de passe, par SMS, en anonyme ou par un fournisseur fédéré."}
    - {from: idps, to: ip, text: "Un fournisseur SAML ou OIDC déclaré dans le projet prend en charge les utilisateurs d'un client d'entreprise, isolés dans leur propre locataire."}
    - {from: ip, to: bf, control: true, text: "Les blocking functions s'exécutent avant la création du compte et avant chaque connexion : elles peuvent refuser l'inscription ou enrichir le jeton de revendications."}
    - {from: ip, to: api, text: "Le SDK reçoit un jeton d'identité JWT d'une heure ; le backend le vérifie avec l'Admin SDK avant de servir la requête."}
    - {from: ip, to: iap, control: true, text: "Les mêmes identités servent de source d'authentification à Identity-Aware Proxy, pour ouvrir une application interne à des personnes qui n'ont pas de compte Google."}
captures:
  - image: https://docs.cloud.google.com/static/identity-platform/img/multi-tenancy-access-control.png
    page: https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-access-control
    legende: "Identity Platform : la liste des locataires du projet et les autorisations IAM de l'un d'eux, dans la console"
docs:
  Documentation: https://docs.cloud.google.com/identity-platform/docs
  Concepts d'authentification: https://docs.cloud.google.com/identity-platform/docs/concepts-authentication
  Différences avec Firebase Authentication: https://docs.cloud.google.com/identity-platform/docs/product-comparison
  Multi-locataire: https://docs.cloud.google.com/identity-platform/docs/multi-tenancy
  Authentification multifacteur (web): https://docs.cloud.google.com/identity-platform/docs/web/mfa
  Blocking functions: https://docs.cloud.google.com/identity-platform/docs/blocking-functions
  Fournisseur SAML: https://docs.cloud.google.com/identity-platform/docs/web/saml
  Fournisseur OIDC: https://docs.cloud.google.com/identity-platform/docs/web/oidc
  Revendications personnalisées: https://docs.cloud.google.com/identity-platform/docs/how-to-configure-custom-claims
  Admin SDK: https://docs.cloud.google.com/identity-platform/docs/install-admin-sdk
  Migrer des utilisateurs: https://docs.cloud.google.com/identity-platform/docs/migrating-users
  reCAPTCHA Enterprise: https://docs.cloud.google.com/identity-platform/docs/recaptcha-enterprise
  API REST: https://docs.cloud.google.com/identity-platform/docs/reference/rest
  Quotas: https://docs.cloud.google.com/identity-platform/docs/quota-management
  Tarifs: https://cloud.google.com/identity-platform/pricing
  Notes de version: https://docs.cloud.google.com/identity-platform/docs/release-notes
---

## Ce que c'est

Le service d'authentification des **utilisateurs finaux** d'une application : inscription, connexion, gestion du cycle de vie des comptes, émission de jetons. C'est le même moteur que Firebase Authentication — Identity Platform en est le backend — avec les fonctions attendues d'un déploiement d'entreprise.

- **Méthodes de connexion.** E-mail et mot de passe, numéro de téléphone par SMS, comptes anonymes convertibles ensuite, fournisseurs fédérés (Google, Apple, Facebook, GitHub, Microsoft…), et tout fournisseur **SAML 2.0** ou **OpenID Connect**. Un système d'authentification maison se raccorde par jeton personnalisé.
- **Ce qu'il apporte au-dessus de Firebase Authentication.** L'authentification **multifacteur**, les **blocking functions**, les fournisseurs **OIDC** et **SAML**, le **multi-locataire**, l'intégration à [Identity-Aware Proxy](#identity-aware-proxy), la couverture par un contrat d'associé de traitement (BAA) et un SLA de **99,95 %**. Les applications n'ont rien à changer pour passer de l'un à l'autre.
- **Jetons.** Une connexion réussie produit un **jeton d'identité** JWT signé par Google, valable une heure, et un jeton d'actualisation. Le backend le vérifie avec l'Admin SDK ou avec les clés publiques de Google : il n'a pas besoin d'appeler le service à chaque requête.
- **Multi-locataire.** Un projet peut contenir plusieurs **locataires**, chacun avec ses propres utilisateurs, ses fournisseurs et ses paramètres — le découpage naturel d'un produit SaaS où chaque client d'entreprise arrive avec son propre SAML.
- **Blocking functions.** Deux points d'extension exécutés de façon synchrone par Google : avant la création d'un compte et avant chaque connexion. On y refuse une inscription hors d'un domaine, on y attribue des rôles applicatifs, on y enregistre l'utilisateur dans une base métier.
- **Revendications personnalisées.** L'Admin SDK ajoute au jeton des champs propres à l'application (rôle, identifiant d'organisation), que le backend et les règles de sécurité peuvent lire sans requête supplémentaire.
- **Protections.** Politique de mot de passe, protection contre l'énumération des adresses e-mail, restriction des régions pour les SMS, et intégration à **reCAPTCHA Enterprise** contre les abus d'inscription et le bourrage d'identifiants.
- **Facturation** au nombre d'utilisateurs actifs mensuels, par palier, avec un tarif distinct pour les identités fédérées d'entreprise (SAML, OIDC) ; les SMS de vérification sont facturés à part.

> [!TIP]
> Le SDK client et l'Admin SDK portent encore la marque Firebase, et la console Firebase reste utilisable sur le même projet : c'est voulu, les deux produits partagent le même backend.

## À quoi ça sert

- Gérer les comptes d'une application grand public — web, iOS, Android — sans écrire de code de mot de passe, de réinitialisation ni de vérification d'e-mail.
- Construire un SaaS multi-clients où chaque client d'entreprise se connecte par son propre fournisseur SAML ou OIDC, isolé dans un locataire.
- Ajouter un second facteur (SMS ou TOTP) à une application existante sans toucher au reste de l'authentification.
- Vérifier l'identité de l'appelant dans une API [Cloud Run](#cloud-run) ou derrière [API Gateway](#api-gateway), en validant le jeton d'identité plutôt qu'en gérant des sessions.
- Ouvrir une application interne à des utilisateurs sans compte Google, en branchant Identity Platform comme source d'identité d'Identity-Aware Proxy.
- Reprendre un annuaire applicatif existant : l'import accepte les empreintes de mots de passe (bcrypt, scrypt, PBKDF2, HMAC) sans forcer une réinitialisation générale.

**À éviter** pour les identités des collaborateurs de l'entreprise : c'est [Cloud Identity](#cloud-identity) ou Google Workspace qui tient l'annuaire interne, et [IAM](#cloud-iam) qui accorde les droits sur les ressources Google Cloud. À éviter aussi comme moyen d'autoriser des appels aux APIs Google Cloud : un jeton Identity Platform authentifie un utilisateur auprès de *votre* backend, il ne donne aucun droit sur un bucket ou une table. Enfin, pour un projet mobile qui n'a besoin ni de SAML, ni de multi-locataire, ni de SLA, Firebase Authentication seul suffit et coûte moins cher.

## Alternatives en logiciel libre

- **Keycloak** : serveur d'identité complet (OIDC, SAML, fédération, MFA, *realms* qui jouent le rôle des locataires), le plus proche fonctionnellement, à héberger soi-même.
- **Authentik** : même périmètre, administration plus moderne, avec des flux d'inscription et de connexion composables.
- **Zitadel** : conçu dès le départ pour le multi-locataire et l'audit, avec API et SDK pour applications web et mobiles.
- **Ory Kratos** : gestion des identités sans interface imposée — l'application fournit ses écrans, Kratos tient les flux et les sessions ; **Ory Hydra** complète pour la partie serveur OAuth 2.0.
- **Supabase Auth** (*GoTrue*) : service d'authentification léger pour applications web et mobiles, avec e-mail, magic link et fournisseurs sociaux.
- **Logto** : alternative récente orientée produit, avec SDK clients et console d'administration intégrée.
