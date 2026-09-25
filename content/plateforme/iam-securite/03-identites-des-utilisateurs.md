---
title: "Identités des utilisateurs : Cloud Identity, SSO, fédération"
subgroup: Identités et accès
---

IAM accorde des rôles à des identités, mais ne les crée pas. Pour les personnes, deux décisions précèdent toute liaison : **quel système fait autorité** sur la liste des collaborateurs (création, départ, groupes), et **quel fournisseur d'identité** vérifie le mot de passe et le second facteur. Google Cloud s'adapte aux deux cas courants : l'annuaire vit chez Google ([Cloud Identity](#cloud-identity) ou Google Workspace), ou il reste dans l'annuaire existant (Active Directory, Microsoft Entra ID, Okta), dont Google reçoit une copie ou qu'il interroge à chaque connexion. Les clients d'une application sont un sujet séparé, traité par [Identity Platform](#identity-platform).

![Arbre de décision : d'où viennent les identités des utilisateurs](../../svg/choix-identites-utilisateurs.svg)

## Matrice de choix

| Montage | Comptes Google | Authentification | Cycle de vie | Quand |
|---|---|---|---|---|
| **Cloud Identity** (ou Workspace) seul | Oui, créés dans la console d'administration | Google : mot de passe et validation en deux étapes | Console d'administration, API Directory, ou un SIRH par API | Pas d'annuaire existant ; Workspace déjà en place |
| **Cloud Identity + GCDS + SSO** | Oui, copies des comptes AD | AD FS (ou un autre IdP SAML) | Active Directory ou LDAP, synchronisé à sens unique par Google Cloud Directory Sync | Active Directory sur site comme source de vérité |
| **Cloud Identity + connecteur IdP + SSO** | Oui, provisionnés par l'IdP | Entra ID, Okta, Ping en SAML | L'IdP, par son application Google Cloud / Workspace | Un IdP en nuage (IDaaS) déjà en place |
| **Fédération d'identité de personnel** | Non | IdP externe en OIDC ou SAML | L'IdP ; rien à synchroniser | Prestataires, filiales, contraintes de résidence des identités, refus de copier l'annuaire chez Google |
| **Identity Platform** | Non | E-mail, téléphone, réseaux sociaux, SAML ou OIDC par client | L'application | Utilisateurs d'un produit, pas des collaborateurs |

Le modèle recommandé par la [fondation d'entreprise](https://docs.cloud.google.com/architecture/blueprints/security-foundations/authentication-authorization) est le deuxième ou le troisième : l'IdP existant reste la source de vérité, Cloud Identity n'en détient qu'une copie sans mot de passe, et la connexion est renvoyée vers l'IdP par [SAML](#lexterm-saml-2-0). Les [architectures de référence](https://docs.cloud.google.com/architecture/identity/reference-architectures) détaillent chaque variante.

## Cloud Identity ou Workspace

Les deux partagent la même plateforme : mêmes comptes, même console d'administration, mêmes API. Une organisation Google Cloud s'attache à **un seul** compte Cloud Identity ou Workspace, identifié par son domaine principal.

- **Cloud Identity Free** : comptes, groupes, unités organisationnelles, validation en deux étapes et clés de sécurité, SSO SAML entrant, GCDS, gestion de base des terminaux. Le plafond d'utilisateurs de départ se relève sans frais pour un client Google Cloud. C'est suffisant pour Google Cloud.
- **Cloud Identity Premium** : accès contextuel selon l'appareil, gestion avancée des terminaux, LDAP sécurisé, provisionnement vers des applications tierces, export des journaux vers BigQuery, SLA de 99,9 % et assistance 24/7 ([comparatif des éditions](https://docs.cloud.google.com/identity/docs/editions)).
- **Workspace** : Cloud Identity plus Gmail, Drive, Agenda. Une entreprise déjà sur Workspace n'a rien à ajouter ; ses comptes servent directement dans Google Cloud.

## Raccorder un annuaire existant

- **Deux flux indépendants.** Le *provisionnement* crée, suspend et supprime les comptes et les groupes côté Google, à sens unique et sans les mots de passe. Le *SSO* renvoie chaque connexion vers l'IdP. On peut avoir l'un sans l'autre, mais le montage complet utilise les deux.
- **Active Directory.** Google Cloud Directory Sync, outil gratuit fourni par Google, lit AD ou un annuaire LDAP et réplique utilisateurs et groupes ; il tourne sur site ou sur une VM. Une instance par forêt. AD FS, ou tout IdP SAML, assure la connexion.
- **Entra ID, Okta, Ping.** L'application de galerie de l'IdP (*Google Cloud / G Suite Connector by Microsoft* pour Entra ID) fait à la fois le provisionnement et le SSO. Entra ID peut ne provisionner qu'un sous-ensemble d'utilisateurs, par groupe.
- **Correspondance des identités.** Même adresse e-mail, routable, dans l'IdP et chez Google ; les comptes Google doivent rester un sous-ensemble des identités de l'IdP. Une suspension ou une suppression dans l'IdP doit se propager : sans cela, un ancien salarié garde une session et ses jetons.
- **Comptes personnels existants.** Des collaborateurs ont souvent créé des comptes Google grand public avec leur adresse professionnelle. Ils entrent en conflit avec les comptes gérés : les transférer vers le compte géré, ou les écarter, avant le premier provisionnement ([bonnes pratiques de fédération](https://docs.cloud.google.com/architecture/identity/best-practices-for-federating)).

## Fédération d'identité de personnel

*Workforce Identity Federation* (voir [Workload Identity Federation](#workload-identity-federation) pour le pendant côté charges de travail) fait entrer les utilisateurs d'un IdP OIDC ou SAML dans Google Cloud **sans aucun compte Google** : un *workforce identity pool*, rattaché à l'organisation, reçoit les assertions de l'IdP, et IAM accorde des rôles à `principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/group/GROUPE` ou à un attribut mappé.

- **Accès.** Une console dédiée, la **console (fédérée)**, `gcloud` (fichier de configuration de connexion produit par `gcloud iam workforce-pools create-login-config`, puis `gcloud auth login`) et les API. La durée de session du pool va de 15 minutes à 12 heures (une heure par défaut).
- **Limites.** Tous les produits ne sont pas pris en charge : Cloud Shell, App Engine, Cloud Profiler, Looker (Google Cloud core) ne le sont pas, et plusieurs consoles ont des fonctions réduites ; vérifier la [liste des produits et limitations](https://docs.cloud.google.com/iam/docs/federated-identity-supported-services) avant de choisir. Un utilisateur qui appartient à plus de 400 groupes voit sa connexion échouer : ne mapper que les groupes utiles.
- **Ce qui reste nécessaire.** L'organisation elle-même s'attache toujours à un compte Cloud Identity ou Workspace, avec au moins un super-administrateur. Les identités fédérées n'accèdent pas à Workspace.

## Groupes

Les groupes sont l'unité de gestion des accès (voir [IAM : rôles, comptes de service, moindre privilège](#iam-bonnes-pratiques)). Ils se créent et se remplissent dans l'IdP, puis se propagent.

- Un groupe par fonction et par portée : `grp-gcp-org-admin`, `grp-gcp-billing-viewer`, `grp-gcp-data-eng-prod`. Le nom dit le rôle et l'environnement.
- Étiqueter comme **groupes de sécurité** ceux qui portent des rôles IAM, pour les distinguer des listes de diffusion (l'étiquette ne se retire pas), et **verrouiller** ceux que synchronise l'IdP : seuls quelques administrateurs peuvent alors en modifier les membres, et le groupe ne diverge pas de sa source.
- Éviter les imbrications profondes : un changement de membre d'un groupe imbriqué met plus longtemps à se refléter dans les accès.
- Qui peut modifier la composition d'un groupe détient, de fait, les rôles du groupe : restreindre la gestion des membres.

## Second facteur et super-administrateurs

- **Validation en deux étapes pour tous.** Google l'impose progressivement pour accéder à la console Google Cloud ([2-step verification requirement](https://docs.cloud.google.com/docs/authentication/mfa-requirement)) ; avec le SSO, le second facteur de l'IdP suffit. Préférer des facteurs résistants à l'hameçonnage : la méthode imposée « clé de sécurité uniquement » accepte clés de sécurité et *passkeys*.
- **Super-administrateurs à part.** Le super-administrateur de Cloud Identity peut tout faire, y compris sur l'organisation Google Cloud. Des comptes dédiés (`admin-alice@example.com`), deux ou plus pour pouvoir se dépanner, jamais utilisés au quotidien, protégés par clé de sécurité et, si possible, par le programme Protection Avancée. Le rôle *Organization Administrator* passe par un groupe distinct qui ne les contient pas.
- **Le SSO ne les couvre pas.** Un super-administrateur qui se connecte sur une page Google n'est pas redirigé vers l'IdP : il s'authentifie par mot de passe Google, hors des règles de l'IdP. Lui imposer la validation en deux étapes de Google, et désactiver le SSO pour son unité organisationnelle.
- **Compte technique de synchronisation.** GCDS ou le connecteur Entra ID agissent sous un compte d'administration. La documentation de GCDS recommande un utilisateur dédié, super-administrateur et exempté du SSO pour pouvoir réautoriser l'outil en cas de panne de l'IdP : c'est l'un des comptes les plus sensibles de l'organisation, à protéger par la validation en deux étapes et à ne jamais utiliser pour autre chose.

## Accès aux applications

- **[Identity-Aware Proxy](#identity-aware-proxy)** ouvre une application interne (sur un load balancer, Cloud Run ou App Engine) ou un port de VM aux collaborateurs, sans VPN : l'accès se décide par rôle IAM (`roles/iap.httpsResourceAccessor`) sur des comptes Cloud Identity ou des identités fédérées. Les niveaux d'accès par adresse IP ou pays sont inclus ; ceux qui portent sur l'état de l'appareil demandent une licence **Chrome Enterprise Premium**.
- **Chrome Enterprise Premium** étend ce modèle *zero trust* : accès contextuel selon l'appareil, protection contre la fuite de données et l'hameçonnage dans Chrome, accès à des applications sur site ou dans d'autres clouds.
- **Identity Platform** gère les comptes des clients d'un produit (e-mail, téléphone, réseaux sociaux, SAML par client en multi-locataire). Il peut aussi servir de source d'identité à IAP, pour ouvrir une application à des partenaires sans leur créer de compte Google.

## Pièges

- **Supprimer puis recréer un compte.** Un compte supprimé puis recréé sous la même adresse (erreur de filtre de synchronisation, changement d'unité d'IdP) est une nouvelle identité : ses anciennes liaisons IAM deviennent `deleted:user:...` et ne s'appliquent pas. Tester les règles de GCDS ou du connecteur en simulation avant de les appliquer.
- **Unités organisationnelles et dossiers.** Les premières rangent des personnes et portent des paramètres (validation en deux étapes, durée de session) ; les seconds rangent des projets et portent des rôles. Aucune raison qu'ils se ressemblent.
- **Durées de session incohérentes.** Une session Google plus longue que celle de l'IdP laisse un compte désactivé dans l'IdP actif chez Google jusqu'à l'expiration : aligner les deux.
- **Masques réseau sur le SSO.** Restreindre le SSO par plage d'adresses permet de contourner le second facteur de l'IdP ; la documentation le déconseille.
- **Identity Platform pour les employés**, ou Cloud Identity pour les clients : les deux annuaires ne se mélangent pas, et un jeton Identity Platform ne donne aucun droit sur les API Google Cloud.

## Alternatives en logiciel libre

- **Keycloak** (Apache 2.0) : fournisseur d'identité complet, fédération LDAP et Active Directory, SAML et OIDC, second facteur et WebAuthn ; il tient à la fois le rôle de l'IdP et celui d'Identity Platform, dans des *realms* séparés.
- **authentik** (MIT, hors module entreprise) : IdP SAML, OIDC et LDAP avec provisionnement SCIM sortant et flux de connexion configurables, plus un proxy d'accès aux applications.
- **Kanidm** (MPL 2.0) : annuaire et IdP intégrés, OIDC, LDAP en lecture, passkeys et groupes, pensé pour remplacer un annuaire d'entreprise sans empiler plusieurs briques.
- **FreeIPA** (GPL v3) : domaine d'identité Linux avec LDAP, Kerberos, PKI et politiques d'hôtes ; la source de vérité que GCDS ou un IdP SAML peuvent ensuite exposer.
- **Samba** (GPL v3) en contrôleur de domaine Active Directory : garde la compatibilité avec des postes Windows et avec des outils qui, comme GCDS, lisent un annuaire AD.
- **Pomerium** (Apache 2.0) et **oauth2-proxy** (MIT) : proxys d'accès identifiés devant des applications internes, avec politique par route et contexte, dans le rôle d'IAP.
