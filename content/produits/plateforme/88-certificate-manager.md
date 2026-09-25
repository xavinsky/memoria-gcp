---
title: Certificate Manager
subgroup: IAM et sécurité
icon: categories/security-identity
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 190, y: 16, w: 558, h: 290}
  nodes:
    dns: {label: Cloud DNS, sub: "enregistrement CNAME", icon: categories/networking, x: 210, y: 30, w: 220}
    cm: {label: Certificate Manager, sub: "mappage, entrées", icon: categories/security-identity, focus: true, x: 210, y: 130, w: 220, h: 64}
    cas: {label: CA Service, sub: "émetteur privé", icon: categories/security-identity, x: 210, y: 230, w: 220}
    pubca: {label: Public CA, sub: "ACME, Let's Encrypt", icon: categories/security-identity, x: 470, y: 30, w: 230}
    lb: {label: Cloud Load Balancing, sub: "proxy HTTPS cible", icon: categories/networking, x: 470, y: 130, w: 220}
    mcdn: {label: Media CDN, sub: "certificats globaux", icon: categories/media-services, x: 470, y: 230, w: 220}
  flows:
    - {from: dns, to: cm, control: true, text: "L'autorisation DNS crée un enregistrement CNAME dédié : Google valide la propriété du domaine sans exiger que le trafic passe déjà par le load balancer."}
    - {from: pubca, to: cm, text: "Un certificat géré par Google est émis par Public CA ou par Let's Encrypt, puis renouvelé avant expiration sans que la clé privée soit jamais exposée."}
    - {from: cas, to: cm, control: true, text: "Un pool d'autorités de Certificate Authority Service peut remplacer l'émetteur public : le certificat devient privé, valable pour les seuls clients qui font confiance à cette racine."}
    - {from: cm, to: lb, from_offset: -14, text: "Le mappage de certificats est attaché au proxy HTTPS cible ; chaque entrée associe un nom d'hôte, éventuellement à joker, au certificat à présenter en fonction du SNI."}
    - {from: cm, to: mcdn, from_offset: 14, text: "Les mêmes certificats globaux servent Media CDN ; une configuration de confiance permet en plus d'exiger un certificat client (TLS mutuel) sur le load balancer."}
docs:
  Documentation: https://docs.cloud.google.com/certificate-manager/docs
  Vue d'ensemble: https://docs.cloud.google.com/certificate-manager/docs/overview
  Certificats: https://docs.cloud.google.com/certificate-manager/docs/certificates
  Mappages de certificats: https://docs.cloud.google.com/certificate-manager/docs/maps
  Configurations de confiance: https://docs.cloud.google.com/certificate-manager/docs/trust-configs
  Public CA: https://docs.cloud.google.com/certificate-manager/docs/public-ca
  Certificats SSL des load balancers: https://docs.cloud.google.com/load-balancing/docs/ssl-certificates
  API REST: https://docs.cloud.google.com/certificate-manager/docs/reference/certificate-manager/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/certificate-manager
  Quotas et limites: https://docs.cloud.google.com/certificate-manager/docs/quotas
  Tarifs: https://cloud.google.com/certificate-manager/pricing
  Notes de version: https://docs.cloud.google.com/certificate-manager/docs/release-notes
---

## Ce que c'est

Le service qui obtient, stocke et déploie les certificats TLS des points d'entrée Google Cloud. Il remplace les certificats SSL attachés un par un aux ressources [Compute Engine](#compute-engine) par un modèle à deux étages — un stock de certificats d'un côté, un mappage nom d'hôte → certificat de l'autre — qui passe à l'échelle de milliers de domaines.

- **Où il s'applique.** Sur les proxys HTTPS cibles et les proxys SSL cibles de [Cloud Load Balancing](#cloud-load-balancing) : Application Load Balancers externes (global, classique, régional) et internes (régional, interrégional), et Proxy Network Load Balancers. Également sur les proxys **Secure Web Proxy** en régional et sur [Media CDN](#media-cdn) en global. Le load balancer doit être compatible avec le [niveau de service réseau](#network-service-tiers) retenu.
- **Deux sortes de certificats.** Les certificats **gérés par Google** sont émis et renouvelés automatiquement ; la clé privée n'est jamais exposée. Les certificats **auto-gérés** sont obtenus ailleurs puis téléversés, y compris des certificats auto-signés ou issus d'une AC tierce.
- **Émetteurs.** Pour les certificats publics gérés, Certificate Manager s'appuie uniquement sur **Google Trust Services (Public CA)** et sur **Let's Encrypt**. Pour une chaîne de confiance interne, on désigne un pool d'autorités de [Certificate Authority Service](#certificate-authority-service) comme émetteur.
- **Validation de domaine.** Deux méthodes : par **DNS**, avec une autorisation qui crée un enregistrement CNAME dédié dans [Cloud DNS](#cloud-dns) ou chez un autre hébergeur — le certificat peut alors être émis **avant** que le trafic bascule, ce qui rend une migration sans coupure possible ; ou par **load balancer**, qui suppose que le domaine pointe déjà sur l'équilibreur.
- **Mappage de certificats.** Une carte attachée au proxy cible, composée d'**entrées** qui associent un nom d'hôte — exact ou à joker — à un certificat, plus une entrée par défaut. C'est ce qui permet de servir un très grand nombre de domaines derrière une seule adresse IP, le choix se faisant sur le SNI présenté par le client.
- **Configurations de confiance.** Un magasin d'ancres de confiance et de certificats intermédiaires, que le load balancer utilise pour valider les certificats **clients** : c'est la brique du TLS mutuel.
- **Public CA.** L'autorité publique de Google, utilisable directement par le protocole **ACME** pour des points d'entrée qui ne sont pas derrière un load balancer Google Cloud.
- **Facturation** à l'entrée de mappage et au certificat géré au-delà des quotas inclus ; les certificats auto-gérés ne sont pas facturés à l'émission.

> [!TIP]
> Émettre les certificats par autorisation DNS avant de basculer les enregistrements évite l'erreur classique de la migration : un certificat qui ne peut pas être validé parce que le domaine pointe encore sur l'ancienne infrastructure.

## À quoi ça sert

- Servir un site ou une API en HTTPS sur un domaine propre, avec un certificat public renouvelé tout seul et aucune clé privée à manipuler.
- Héberger des milliers de domaines clients derrière un seul load balancer, chacun avec son certificat, sans toucher au proxy cible à chaque ajout.
- Migrer une infrastructure existante vers Google Cloud sans interruption TLS, en provisionnant les certificats à l'avance.
- Présenter des certificats issus d'une PKI interne sur un load balancer interne, pour des services qui ne sortent pas du VPC.
- Exiger un certificat client sur un point d'entrée d'API partenaire, via une configuration de confiance et le TLS mutuel.
- Obtenir des certificats par ACME pour des serveurs hébergés hors de Google Cloud, avec Public CA.

**À éviter** pour émettre des certificats à des machines, à des utilisateurs ou à des services internes : Certificate Manager équipe des points d'entrée, il ne délivre pas d'identités — c'est [Certificate Authority Service](#certificate-authority-service) qui fait ce travail. À éviter aussi pour un service [Cloud Run](#cloud-run) joignable sur son URL `run.app`, déjà servie en HTTPS avec un certificat géré, ou pour un unique domaine sur un load balancer simple, où les certificats SSL classiques de Compute Engine restent plus directs. Enfin, il ne gère ni les certificats de ressources hors Google Cloud (hors Public CA par ACME) ni les certificats des VM elles-mêmes.

## Alternatives en logiciel libre

- **cert-manager** : le standard de fait sur Kubernetes — ressources Certificate et Issuer, validation ACME par HTTP ou DNS, renouvellement automatique et injection dans les Ingress.
- **Certbot** : le client ACME de référence pour obtenir et renouveler des certificats Let's Encrypt sur un serveur classique.
- **acme.sh** et **lego** : clients ACME légers, avec une longue liste de fournisseurs DNS pris en charge pour la validation par enregistrement.
- **Caddy** : serveur web qui obtient et renouvelle ses certificats tout seul dès qu'un nom de domaine est configuré, sans étape supplémentaire.
- **Traefik** : proxy qui découvre ses routes dans l'orchestrateur et provisionne un certificat par domaine, l'équivalent le plus proche du mappage de certificats.
- **step-ca** avec **step cli** : pour la variante privée, avec ACME interne et rotation courte.
