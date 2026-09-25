---
title: Identity-Aware Proxy
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 200, y: 16, w: 548, h: 290}
  nodes:
    users: {label: Utilisateurs, sub: "navigateur, SSH", external: true, x: 8, y: 120, w: 170}
    lb: {label: Cloud Load Balancing, sub: "proxy HTTPS", icon: categories/networking, x: 218, y: 46, w: 216}
    iap: {label: Identity-Aware Proxy, sub: "authentifie, autorise", icon: categories/security-identity, focus: true, x: 218, y: 140, w: 216, h: 64}
    iam: {label: IAM, sub: "IAP-secured Web App User", icon: categories/security-identity, x: 218, y: 244, w: 216}
    run: {label: Cloud Run, sub: "service protégé", icon: produits/cloud-run, x: 480, y: 46, w: 200}
    vm: {label: Compute Engine, sub: "SSH par tunnel IAP", icon: produits/compute-engine, x: 480, y: 244, w: 250}
  flows:
    - {from: users, to: lb, from_offset: -12, text: "La requête HTTPS arrive sur le load balancer externe, dont le service de backend a IAP activé."}
    - {from: lb, to: iap, text: "Avant d'atteindre le backend, la requête part vers le serveur d'authentification d'IAP, qui redirige le navigateur vers la connexion Google si aucun cookie valide n'est présent."}
    - {from: iam, to: iap, control: true, text: "IAP vérifie ensuite que l'identité obtenue porte le rôle IAP-secured Web App User ; un niveau d'accès peut y ajouter des conditions d'appareil, d'adresse IP ou de pays."}
    - {from: iap, to: run, from_offset: -14, text: "La requête autorisée repart vers le service, enrichie d'un en-tête signé qui porte l'adresse e-mail et l'identifiant de l'utilisateur."}
    - {from: users, to: iap, from_offset: 12, text: "Pour une session d'administration, gcloud ouvre un tunnel vers IAP plutôt qu'une connexion directe."}
    - {from: iap, to: vm, from_offset: 14, text: "Le transfert TCP relaie alors le flux vers le port 22 d'une VM dépourvue d'adresse IP externe, sans ouvrir ce port sur internet."}
docs:
  Page produit: https://cloud.google.com/security/products/iap
  Documentation: https://docs.cloud.google.com/iap/docs
  Concepts: https://docs.cloud.google.com/iap/docs/concepts-overview
  Gérer les accès: https://docs.cloud.google.com/iap/docs/managing-access
  Transfert TCP: https://docs.cloud.google.com/iap/docs/tcp-forwarding-overview
  Utiliser le transfert TCP: https://docs.cloud.google.com/iap/docs/using-tcp-forwarding
  En-têtes signés: https://docs.cloud.google.com/iap/docs/signed-headers-howto
  Identités externes: https://docs.cloud.google.com/iap/docs/external-identities
  Activer sur Cloud Run: https://docs.cloud.google.com/iap/docs/enabling-cloud-run
  Personnaliser la page de connexion: https://docs.cloud.google.com/iap/docs/customizing
  Access Context Manager: https://docs.cloud.google.com/access-context-manager/docs/overview
  API REST: https://docs.cloud.google.com/iap/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/iap
  Tarifs: https://cloud.google.com/iap/pricing
  Notes de version: https://docs.cloud.google.com/iap/docs/release-notes
---

## Ce que c'est

Une couche d'autorisation centrale placée devant des applications servies en HTTPS, et devant les ports d'administration des machines. Plutôt que d'ouvrir un VPN ou de filtrer par adresse IP, on décide qui a le droit d'entrer à partir d'une identité et du rôle IAM qu'elle porte.

- **Où il s'insère.** Sur un service de backend de [Cloud Load Balancing](#cloud-load-balancing), sur un service [Cloud Run](#cloud-run) directement, ou sur une application [App Engine](#app-engine). L'infrastructure de service vérifie que IAP est activé et adresse la requête au serveur d'authentification avant de laisser passer quoi que ce soit.
- **Authentification.** Trois sources d'identité : les **comptes Google** du domaine, les identités d'un fournisseur externe via la **fédération d'identité de personnel**, et les utilisateurs finaux d'une application via [Identity Platform](#identity-platform) — e-mail et mot de passe, ou connexion sociale. Une fois authentifié, le navigateur conserve un jeton dans un cookie.
- **Autorisation.** Le rôle **IAP-secured Web App User** (`roles/iap.httpsResourceAccessor`) accordé sur la ressource ou sur le projet suffit à ouvrir l'accès. Les conditions IAM et les **niveaux d'accès** d'Access Context Manager (adresse IP, région, état de l'appareil géré) s'y ajoutent : c'est l'accès contextuel.
- **En-têtes signés.** IAP transmet au backend un JWT signé par Google (`X-Goog-IAP-JWT-Assertion`) qui contient l'adresse e-mail et l'identifiant stable de l'utilisateur. L'application doit **vérifier cette signature** : c'est ce qui la protège d'une requête qui contournerait le proxy.
- **Transfert TCP.** Un tunnel chiffré vers un port arbitraire d'une VM ou d'un groupe d'instances, sans adresse IP externe ni bastion : `gcloud compute ssh --tunnel-through-iap` pour SSH, un relais local pour RDP ou pour une base. Le rôle correspondant est **IAP-secured Tunnel User**.
- **Client OAuth.** L'activation crée automatiquement un ID client et un secret OAuth 2.0 ; les supprimer casse le service. On peut personnaliser l'écran de connexion et la page de refus.
- **Limites de responsabilité.** Sur [Compute Engine](#compute-engine) et [GKE](#gke), du code qui tourne sur la même VM atteint le port applicatif sans passer par IAP : les règles de pare-feu doivent interdire tout ce qui ne vient pas des plages du proxy. Sur Cloud Run, activer IAP sur le service protège toutes les entrées, y compris l'URL `run.app` ; l'activer sur le load balancer seulement laisse cette URL ouverte — et il ne faut jamais l'activer aux deux endroits à la fois.
- **Facturation.** Le proxy lui-même n'est pas facturé ; ce sont les ressources placées derrière (load balancer, VM, service) qui le sont.

> [!WARNING]
> Un service Cloud Run derrière un load balancer garde son URL `run.app` publique tant qu'on n'a pas restreint son entrée au trafic interne et aux load balancers. Activer IAP sur le load balancer sans fermer cette URL revient à laisser la porte de service ouverte.

## À quoi ça sert

- Publier une application interne — outil d'administration, tableau de bord, préproduction — sur internet, avec un contrôle d'accès par groupe plutôt qu'un VPN pour tout le monde.
- Ouvrir une application à des prestataires ou à des clients dont on ne veut pas gérer les comptes Google, en s'appuyant sur Identity Platform pour leurs identités.
- Remplacer un bastion SSH : les VM n'ont plus d'adresse IP externe, le port 22 n'est ouvert qu'aux plages du proxy, et chaque connexion est tracée et soumise à un rôle IAM.
- Appliquer une politique contextuelle uniforme : accès refusé hors d'un pays, ou hors d'un appareil géré par l'entreprise, sans modifier les applications.
- Déléguer l'authentification d'une application héritée qui n'en a pas : le backend n'a plus qu'à lire l'en-tête signé pour connaître l'utilisateur.

**À éviter** pour un appel de service à service : entre deux services Cloud Run, un jeton d'identité et le rôle `roles/run.invoker` suffisent, sans passer par une interface de connexion. À éviter aussi pour un protocole qui n'est ni HTTPS ni un flux TCP relayé — pour ouvrir un réseau entier à des postes distants, c'est [Cloud VPN](#cloud-vpn) ou un accès privé par [Private Service Connect](#private-service-connect). Et pour filtrer le trafic sur son contenu plutôt que sur l'identité — injections, robots, volumétrie — c'est [Cloud Armor](#cloud-armor) qui travaille en amont.

## Alternatives en logiciel libre

- **oauth2-proxy** : proxy inverse qui délègue l'authentification à un fournisseur OIDC ou OAuth puis transmet l'identité au backend par en-tête — l'équivalent le plus direct, souvent placé devant un Ingress.
- **Pomerium** : passerelle d'accès identifiée avec politique par route et prise en compte du contexte (appareil, réseau), très proche du modèle d'IAP.
- **Authelia** : portail d'authentification et d'autorisation pour proxy inverse, avec second facteur et règles par domaine et par chemin.
- **Teleport** : accès identifié à SSH, Kubernetes, bases de données et applications web, avec certificats courts et enregistrement des sessions — le pendant du transfert TCP, en plus complet.
- **Keycloak** avec **mod_auth_openidc** ou le module OIDC de NGINX : la même mécanique construite à partir d'un serveur d'identité et d'un serveur web classique.
