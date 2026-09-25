---
title: Developer Connect
subgroup: Dépôts
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 196, y: 16, w: 552, h: 268}
  nodes:
    scm: {label: Fournisseur Git, sub: "GitHub, GitLab, Bitbucket", external: true, x: 8, y: 122, w: 180, h: 60}
    dc: {label: Developer Connect, sub: "connexion et liens", icon: categories/developer-tools, focus: true, x: 260, y: 120, w: 210, h: 64}
    sm: {label: Secret Manager, sub: "jeton d'accès", icon: categories/security-identity, x: 260, y: 216, w: 210}
    cb: {label: Cloud Build, sub: "déclencheur de build", icon: categories/devops, x: 538, y: 36, w: 200}
    gca: {label: Gemini Code Assist, sub: "indexation du dépôt", icon: categories/ai-machine-learning, x: 538, y: 124, w: 200}
    log: {label: Cloud Logging, sub: "insights de déploiement", icon: categories/observability, x: 538, y: 216, w: 200}
  flows:
    - {from: dc, to: scm, control: true, from_offset: -16, to_offset: -16, text: "La création d'une connexion installe l'application Google sur l'organisation GitHub, GitLab ou Bitbucket et en obtient l'autorisation ; on lie ensuite les dépôts un par un."}
    - {from: dc, to: sm, text: "Le jeton délivré par le fournisseur est rangé dans Secret Manager : la connexion y renvoie au lieu de le porter en clair."}
    - {from: scm, to: dc, from_offset: 16, to_offset: 16, text: "La liaison d'un dépôt y pose un webhook : commits et pull requests remontent vers Developer Connect."}
    - {from: dc, to: cb, from_offset: -20, text: "Un déclencheur Cloud Build pointe sur le dépôt lié et démarre une exécution à chaque événement reçu."}
    - {from: dc, to: gca, text: "Gemini Code Assist emprunte la même connexion pour cloner et indexer le dépôt, y compris derrière un réseau privé grâce au proxy Git."}
    - {from: dc, to: log, from_offset: 20, text: "Les insights consignent dans Cloud Logging les événements de déploiement : artefact livré, commit d'origine, dépendances."}
docs:
  Documentation: https://docs.cloud.google.com/developer-connect/docs
  Vue d'ensemble: https://docs.cloud.google.com/developer-connect/docs/overview
  Connexions de dépôt Git: https://docs.cloud.google.com/developer-connect/docs/git-repo-connections
  Connecteurs de compte: https://docs.cloud.google.com/developer-connect/docs/account-connectors
  Connexions HTTP: https://docs.cloud.google.com/developer-connect/docs/http-connections
  Proxy Git: https://docs.cloud.google.com/developer-connect/docs/configure-git-proxy
  Se connecter à GitHub: https://docs.cloud.google.com/developer-connect/docs/connect-github-repo
  Insights: https://docs.cloud.google.com/developer-connect/docs/insights
  API REST: https://docs.cloud.google.com/developer-connect/docs/api/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/developer-connect
  Emplacements: https://docs.cloud.google.com/developer-connect/docs/locations
  Tarifs: https://cloud.google.com/developer-connect/pricing
  Notes de version: https://docs.cloud.google.com/developer-connect/docs/release-notes
---

## Ce que c'est

Service de connexion entre Google Cloud et les outils de gestion de code source qui vivent ailleurs. Il centralise l'authentification, l'autorisation et le réseau d'un seul côté, puis prête ces connexions aux produits qui en ont besoin.

- **Connexions système** — elles rattachent un *compte de service* à un système extérieur, et fonctionnent sans que l'utilisateur qui les a créées soit présent au moment de l'appel. Deux formes : les **connexions de dépôt Git**, vers GitHub, GitHub Enterprise, GitLab, GitLab Enterprise, Bitbucket Cloud et Bitbucket Data Center ; les **connexions HTTP**, vers un point de terminaison HTTP quelconque.
- **Connecteurs de compte** — ils relient le compte Google d'une personne à son compte individuel chez un fournisseur tiers, avec des *scopes* choisis. Créé une fois pour l'organisation, un connecteur sert ensuite à chaque utilisateur qui s'y autorise. C'est la forme employée quand l'appel doit se faire au nom de la personne, par exemple pour les dépôts Git de BigQuery Studio.
- **Connexion et lien** — la connexion est le pont vers la plateforme, le lien l'association à un dépôt précis. Une connexion porte plusieurs liens ; créer un lien pose un webhook sur le dépôt.
- **Proxy Git** — activé par défaut pour les connexions créées dans la console, il fait passer les requêtes Git par un serveur géré par Google. Les appelants s'authentifient alors par IAM, sans manipuler de jeton, et les dépôts hébergés sur un réseau privé deviennent atteignables. Le proxy ne couvre que la lecture, `git clone` par exemple ; `git push` n'est pas pris en charge.
- **Insights** — des entrées de journal d'événements de déploiement, envoyées à Cloud Logging, qui relient runtime, artefact déployé, provenance de la construction, fichiers sources et dépendances. Gemini Cloud Assist s'en sert pour remonter à la cause d'un incident.
- **Facturation** — le service lui-même n'est pas facturé. Seul le trafic sortant du proxy Git l'est, au tarif du transfert de données inter-région, avec 10 Gio gratuits par mois.

Les produits qui consomment ces connexions : déclencheurs [Cloud Build](#cloud-build), Cloud Run, Firebase App Hosting, Dataform, Application Design Center, App Lifecycle Manager, Agent Runtime, la personnalisation de code de Gemini Code Assist et son agent de revue.

## À quoi ça sert

- Brancher un dépôt GitHub, GitLab ou Bitbucket sur Google Cloud une seule fois, et réutiliser la même connexion pour plusieurs produits et plusieurs projets.
- Déclencher des constructions sur les commits et les pull requests d'un dépôt qui reste chez son hébergeur.
- Donner à Gemini Code Assist accès au code interne pour la personnalisation et la revue, y compris sur une instance auto-hébergée derrière un réseau privé.
- Éviter de gérer à la main des jetons d'accès dans Secret Manager : le proxy Git ramène l'accès au dépôt à une autorisation IAM.

**À éviter** quand il faut des déclencheurs Cloud Build manuels, Pub/Sub ou webhook : ces cas relèvent des **dépôts Cloud Build (2ᵉ génération)**, qui couvrent les mêmes fournisseurs mais offrent ces fonctions en plus. Les deux mécanismes coexistent, et ni l'un ni l'autre ne permet de rattacher un dépôt Cloud Source Repositories. Pour héberger le dépôt dans Google Cloud plutôt que de s'y connecter, voir [Secure Source Manager](#secure-source-manager).

> [!TIP]
> Une connexion et ses liens sont régionaux : le déclencheur Cloud Build qui les consomme doit vivre dans la même région, sans quoi le dépôt n'apparaît pas dans la liste.

## Alternatives en logiciel libre

Il n'existe pas de brique équivalente isolée : hors de Google Cloud, le rôle de Developer Connect se répartit entre le serveur Git, le moteur d'intégration continue et le coffre à secrets.

- **Gitea**, **Forgejo**, **GitLab CE** : côté serveur, ce sont leurs webhooks natifs et leurs jetons de déploiement qui jouent le rôle des liens.
- **Argo Events**, **Tekton Triggers** : réception et filtrage des événements de dépôt, puis déclenchement d'un pipeline — l'équivalent du chemin webhook → déclencheur.
- **OpenBao** : coffre à secrets sous licence MPL-2.0, pour stocker et faire tourner les jetons d'accès aux dépôts, face à Secret Manager. Vault, dont il dérive, est sous licence BSL : source disponible, pas libre.
- **External Secrets Operator** : projette ces secrets dans les pipelines et les clusters qui les consomment.
- **cloudflared**, **frp**, ou un simple *runner* auto-hébergé : atteindre un dépôt sur réseau privé, ce que fait le proxy Git.
