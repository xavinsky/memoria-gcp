---
title: Certificate Authority Service
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 190, y: 16, w: 558, h: 290}
  nodes:
    racine: {label: Racine d'entreprise, sub: "AC existante hors GCP", external: true, x: 8, y: 40, w: 180}
    hsm: {label: Cloud HSM, sub: "clés privées des AC", icon: categories/security-identity, x: 300, y: 30, w: 220}
    cas: {label: CA Service, sub: "pool d'AC, modèles", icon: categories/security-identity, focus: true, x: 300, y: 130, w: 220, h: 64}
    cm: {label: Certificate Manager, sub: "émetteur du LB", icon: categories/security-identity, x: 300, y: 230, w: 220}
    gke: {label: GKE, sub: "cert-manager, mTLS", icon: produits/gke, x: 548, y: 30, w: 190}
    mesh: {label: Cloud Service Mesh, sub: "certificats de charge", icon: categories/networking, x: 548, y: 130, w: 200}
    vm: {label: Compute Engine, sub: "identité de machine", icon: produits/compute-engine, x: 548, y: 230, w: 200}
  flows:
    - {from: racine, to: cas, text: "Une AC subordonnée créée dans CA Service chaîne vers la racine de l'entreprise, qui reste hors de Google Cloud : les postes gardent leur magasin de confiance."}
    - {from: hsm, to: cas, control: true, text: "La clé privée de chaque autorité est générée et conservée dans Cloud HSM, certifié FIPS 140-2 niveau 3, et n'est jamais exportable."}
    - {from: cas, to: gke, text: "Dans le cluster, cert-manager demande les certificats par l'émetteur CA Service et les renouvelle avant expiration, sans intervention."}
    - {from: cas, to: mesh, text: "Le maillage émet un certificat par charge de travail et s'en sert pour le TLS mutuel entre services, avec une rotation de l'ordre de l'heure."}
    - {from: cas, to: vm, text: "Les machines et les objets connectés reçoivent un certificat client qui leur sert d'identité, à la place d'un secret partagé."}
    - {from: cm, to: cas, control: true, text: "Certificate Manager peut désigner un pool d'AC comme émetteur : le load balancer sert alors des certificats privés plutôt que des certificats publics."}
captures:
  - image: https://docs.cloud.google.com/static/certificate-authority-service/images/view-ca-expiration.png
    page: https://docs.cloud.google.com/certificate-authority-service/docs/deleting-certificate-authorities
    legende: "Pool d'AC dans la console : niveau, région, et liste des autorités de certification du pool avec leur type, état et date d'expiration"
docs:
  Page produit: https://cloud.google.com/security/products/certificate-authority-service
  Documentation: https://docs.cloud.google.com/certificate-authority-service/docs
  Vue d'ensemble: https://docs.cloud.google.com/certificate-authority-service/docs/ca-service-overview
  Concepts: https://docs.cloud.google.com/certificate-authority-service/docs/ca-service-concepts
  Pools d'autorités: https://docs.cloud.google.com/certificate-authority-service/docs/ca-pool
  Niveaux de service: https://docs.cloud.google.com/certificate-authority-service/docs/tiers
  Modèles de certificats: https://docs.cloud.google.com/certificate-authority-service/docs/creating-certificate-template
  Contrôles de règles: https://docs.cloud.google.com/certificate-authority-service/docs/policy-controls
  Choisir un algorithme de clé: https://docs.cloud.google.com/certificate-authority-service/docs/choosing-key-algorithm
  Intégrations Google Cloud: https://docs.cloud.google.com/certificate-authority-service/docs/cas-integrations-cloud-services
  Intégrations tierces: https://docs.cloud.google.com/certificate-authority-service/docs/cas-integrations-third-party
  Bonnes pratiques: https://docs.cloud.google.com/certificate-authority-service/docs/best-practices
  Emplacements: https://docs.cloud.google.com/certificate-authority-service/docs/locations
  API REST: https://docs.cloud.google.com/certificate-authority-service/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/privateca
  Tarifs: https://cloud.google.com/certificate-authority-service/pricing
  Notes de version: https://docs.cloud.google.com/certificate-authority-service/docs/release-notes
---

## Ce que c'est

Une infrastructure à clés publiques **privée**, gérée : on y crée ses propres autorités de certification et on émet des certificats pour ses machines, ses services et ses utilisateurs, sans exploiter de serveur d'AC ni de HSM.

- **Autorités.** On crée des AC **racines** et des AC **subordonnées**, en choisissant le sujet, l'algorithme de clé, la durée de vie et l'emplacement. Une subordonnée peut vivre dans une région différente de sa racine, ou chaîner vers une racine externe, restée sur site ou chez un tiers — ce qui évite de redistribuer un nouveau magasin de confiance.
- **Pool d'autorités.** Le point d'émission : plusieurs AC derrière un même point de terminaison, entre lesquelles les demandes sont réparties. C'est le pool, et non l'AC, que les clients et les intégrations désignent, ce qui rend la rotation d'une autorité transparente.
- **Débit.** Le niveau **DevOps** accepte jusqu'à **25 certificats par seconde et par AC**, soit une centaine par seconde avec plusieurs AC dans un pool — de quoi émettre des millions de certificats. Le niveau **Enterprise** conserve chaque certificat émis et gère la révocation par listes de révocation et OCSP, au prix d'un débit plus faible.
- **Clés.** Les clés privées des AC sont générées et conservées dans **Cloud HSM** (FIPS 140-2 niveau 3), dans plusieurs régions des Amériques, d'Europe et d'Asie-Pacifique.
- **Modèles et contrôles.** Un **modèle de certificat** fige un profil réutilisable — usages de clé, extensions, durée, contraintes de nom — et la politique d'émission du pool limite ce que les demandeurs peuvent obtenir, quel que soit ce qu'ils demandent dans la requête.
- **Accès et audit.** Les rôles IAM séparent l'administration des AC de la simple demande de certificat ; [VPC Service Controls](#vpc-service-controls) permet d'enfermer le service dans un périmètre, et les journaux d'audit tracent chaque émission.
- **Intégrations.** cert-manager pour Kubernetes, [Cloud Service Mesh](#cloud-service-mesh) pour le TLS mutuel entre services, [Certificate Manager](#certificate-manager) pour servir des certificats privés derrière un load balancer, et des connecteurs tiers (Istio, SPIFFE, agents d'entreprise).
- **Pourquoi une PKI privée.** Une AC publique doit valider la possession d'un nom de domaine public et journaliser chaque certificat dans les registres de **Certificate Transparency**. Une PKI privée s'affranchit des deux : on peut émettre pour des noms courts internes, pour des identifiants qui ne sont pas des noms de domaine (SPIFFE, par exemple), et sans publier la topologie interne.
- **Facturation** à l'AC active et au certificat émis, à des tarifs différents selon le niveau de service.

## À quoi ça sert

- Donner une identité cryptographique à chaque service d'un maillage et n'accepter que du TLS mutuel entre eux, avec des certificats de très courte durée renouvelés automatiquement.
- Émettre des certificats clients pour un parc de machines, de terminaux industriels ou d'objets connectés, à la place d'identifiants partagés impossibles à révoquer individuellement.
- Servir des applications internes en HTTPS sur des noms courts (`app.interne`) qu'aucune AC publique n'accepterait.
- Signer du code et des artefacts dans une chaîne [Cloud Build](#cloud-build), pour attester l'origine de ce qui est déployé.
- Émettre des certificats d'authentification utilisateur pour un VPN, une carte à puce ou un accès sans mot de passe.
- Reprendre une PKI interne vieillissante sans changer la racine : la nouvelle subordonnée est hébergée, la racine historique reste hors ligne.

**À éviter** pour des certificats destinés au grand public : un navigateur ne fait pas confiance à une racine privée, et c'est [Certificate Manager](#certificate-manager) qui obtient des certificats publics gratuits pour un site ou une API exposés sur internet. À éviter aussi pour un besoin ponctuel de quelques certificats internes sans exigence de disponibilité ni d'audit : une AC hors ligne gérée à la main coûte moins cher, tant qu'elle ne devient pas une dépendance de production. Enfin, le niveau DevOps ne conserve pas les certificats émis : si la traçabilité de chaque certificat ou la révocation sont attendues, il faut le niveau Enterprise dès le départ.

## Alternatives en logiciel libre

- **step-ca** (Smallstep) : autorité de certification en ligne avec ACME, OIDC et jetons d'attestation, conçue pour émettre des certificats de très courte durée — l'équivalent le plus direct pour une PKI interne.
- **cert-manager** : le contrôleur Kubernetes qui demande et renouvelle les certificats ; il fonctionne aussi bien avec CA Service qu'avec une AC locale ou Let's Encrypt.
- **EJBCA Community Edition** : PKI d'entreprise complète (profils, révocation, OCSP, CMP, EST), la plus proche du niveau Enterprise.
- **Dogtag PKI** : l'AC intégrée à FreeIPA, avec gestion du cycle de vie des certificats pour un parc Linux.
- **OpenBao** : le moteur PKI émet des certificats courts à la demande, avec rôles et contraintes de nom, sans serveur d'AC dédié.
- **SPIRE** : pour le cas particulier de l'identité de charge de travail, il émet lui-même les certificats X.509 (SVID) à partir d'attestations de la plateforme.
