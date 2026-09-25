---
title: Connecter un dépôt de code
---

Le code reste en général chez son hébergeur (GitHub, GitLab, Bitbucket) : on le **connecte** à Google Cloud pour déclencher des builds et nourrir d'autres services. Deux mécanismes le font, [Developer Connect](#developer-connect) et les **dépôts Cloud Build de 2ᵉ génération**, pour les mêmes six forges. Quand le code doit vivre dans Google Cloud, on l'**héberge** dans [Secure Source Manager](#secure-source-manager). Cloud Source Repositories n'est pas ouvert aux nouveaux clients : une organisation qui ne l'a jamais utilisé ne peut pas en activer l'API, et aucun des deux mécanismes de connexion ne sait s'y rattacher.

## Matrice des options

| Option | Forges | Déclencheurs Cloud Build | Automatisation | Qui d'autre l'utilise | Coût |
|---|---|---|---|---|---|
| **Developer Connect** | GitHub, GitHub Enterprise (Cloud et Server), GitLab, GitLab Enterprise, Bitbucket Cloud, Bitbucket Data Center ; instances sur réseau privé | Poussée de branche ou de tag, *pull request* | `gcloud developer-connect`, API, ressource Terraform `google_developer_connect_connection` | Cloud Run, Dataform, Firebase App Hosting, Gemini Code Assist, Agent Platform, App Lifecycle Manager | Gratuit ; seul le trafic du proxy Git est facturé |
| **Dépôts Cloud Build (2ᵉ gén.)** | Les mêmes six | Les mêmes, plus **manuel**, **Pub/Sub** et **webhook** | `gcloud builds connections`, API, Terraform (sauf Bitbucket) | Cloud Build seulement | Gratuit |
| **Secure Source Manager** | Forge hébergée par Google | Fichier `.cloudbuild/triggers.yaml` dans le dépôt ; webhooks vers Jenkins ou autre | `gcloud source-manager`, API | Developer Connect (proxy Git), Cloud Build | 1 000 $ par instance et par mois |
| **Déclencheur webhook** seul | Toute forge capable d'appeler une URL (Gitea, Forgejo, Azure Repos…) | Webhook, filtré sur la charge utile | `gcloud builds triggers create webhook` | Cloud Build | Gratuit |

- **Developer Connect par défaut.** Une seule connexion sert plusieurs produits et plusieurs projets, et son proxy Git ramène l'accès au dépôt à une autorisation IAM, sans jeton manipulé par l'appelant. Le proxy ne sert que la lecture : `git clone` passe, `git push` non.
- **2ᵉ génération** quand Cloud Build doit être déclenché par autre chose qu'un événement de dépôt (appel manuel, message Pub/Sub, webhook d'un outil tiers), ou quand toute la connexion doit être décrite en Terraform, jetons compris.
- **Webhook seul** pour une forge qu'aucun des deux mécanismes ne connaît : Cloud Build reçoit l'événement sur une URL authentifiée par un secret de Secret Manager, et clone le dépôt dans une étape, avec une clé SSH elle aussi rangée dans Secret Manager.

## Ce que demande chaque connexion

| Forge | Côté forge | Stocké dans Secret Manager |
|---|---|---|
| **GitHub**, GitHub Enterprise | Installer l'application GitHub (Developer Connect ou Cloud Build) sur le compte ou l'organisation, en choisissant les dépôts ; droits d'administration sur le dépôt pour la première connexion | Le jeton OAuth de l'utilisateur qui autorise l'application. En mode programmatique, un jeton classique avec `repo`, `read:user` et `read:org` : les jetons à granularité fine ne sont pas acceptés par Cloud Build |
| **GitLab**, GitLab Enterprise | Deux jetons : `api` (connecter et déconnecter des dépôts) et `read_api` (lecture) ; jetons personnels, de groupe ou de projet avec le rôle *Maintainer* | Les deux jetons et un secret de webhook |
| **Bitbucket** Cloud, Data Center | Deux jetons d'accès, administration et lecture | Les deux jetons et un secret de webhook |
| Instance sur réseau privé | Joignable depuis un VPC | En plus : service **Service Directory** et certificat de l'autorité interne (`--ssl-ca-file`) |

Les secrets sont créés dans le projet de la connexion, avec une clé CMEK si besoin. L'agent de service Cloud Build (`service-PROJECT_NUMBER@gcp-sa-cloudbuild.iam.gserviceaccount.com`) doit pouvoir les lire : quand les secrets sont créés à la main, pour `gcloud` ou Terraform, lui accorder `roles/secretmanager.secretAccessor` sur chacun.

## Commandes

```bash
# Developer Connect : connexion GitHub, lien vers un dépôt, déclencheur Cloud Build
gcloud developer-connect connections create github-conn \
  --location=REGION --github-config-app=DEVELOPER_CONNECT
gcloud developer-connect connections describe github-conn --location=REGION   # lien d'installation de l'application
gcloud developer-connect connections git-repository-links create app \
  --connection=github-conn --location=REGION --clone-uri=https://github.com/ORG/REPO.git
gcloud beta builds triggers create developer-connect --name=build-main --region=REGION \
  --git-repository-link=projects/PROJECT_ID/locations/REGION/connections/github-conn/gitRepositoryLinks/app \
  --branch-pattern='^main$' --build-config=cloudbuild.yaml \
  --service-account=projects/PROJECT_ID/serviceAccounts/build-push@PROJECT_ID.iam.gserviceaccount.com

# Dépôts Cloud Build 2e génération : connexion GitLab par jetons, dépôt, déclencheur de merge request
gcloud builds connections create gitlab gitlab-conn --region=REGION \
  --authorizer-token-secret-version=projects/PROJECT_ID/secrets/gitlab-api/versions/1 \
  --read-authorizer-token-secret-version=projects/PROJECT_ID/secrets/gitlab-read/versions/1 \
  --webhook-secret-secret-version=projects/PROJECT_ID/secrets/gitlab-webhook/versions/1
gcloud builds repositories create app --connection=gitlab-conn --region=REGION \
  --remote-uri=https://gitlab.com/GROUPE/PROJET.git
gcloud builds triggers create gitlab --name=mr-main --region=REGION \
  --repository=projects/PROJECT_ID/locations/REGION/connections/gitlab-conn/repositories/app \
  --pull-request-pattern='^main$' --comment-control=COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY \
  --build-config=cloudbuild.yaml \
  --service-account=projects/PROJECT_ID/serviceAccounts/build-pr@PROJECT_ID.iam.gserviceaccount.com
```

Pour GitHub en 2ᵉ génération, `gcloud builds connections create github github-conn --region=REGION` affiche le lien d'autorisation de l'application Cloud Build ; `gcloud builds connections describe` doit ensuite montrer `installationState: COMPLETE`. Les déclencheurs de *pull request* prennent `--comment-control` : `COMMENTS_ENABLED` exige un commentaire `/gcbrun` d'un propriétaire ou d'un collaborateur pour toute PR, `COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY` seulement pour les contributeurs extérieurs ; `--require-approval` ajoute une approbation dans Cloud Build avant exécution.

## Secure Source Manager : quand héberger plutôt que connecter

C'est le bon choix quand **le code source ne doit pas sortir de Google Cloud** : dépôt dans une région choisie, instance mono-locataire, clés CMEK, périmètre VPC Service Controls, conformité FedRAMP High ou HIPAA exigée sur le dépôt lui-même, droits gérés par IAM comme le reste du projet. Pour une équipe dont le code vit bien chez GitHub ou GitLab, Developer Connect fait le pont sans migration ni forfait.

```bash
gcloud source-manager instances create forge --region=REGION   # jusqu'à 60 minutes
gcloud source-manager repos create app --instance=forge --region=REGION
git config --global credential.'https://*.*.sourcemanager.dev'.helper gcloud.sh
```

```yaml
# .cloudbuild/triggers.yaml, sur la branche par défaut du dépôt
triggers:
  - name: build-main
    project: PROJECT_ID
    configFilePath: cloudbuild.yaml
    eventType: push
    includedGitRefs: ^main$
    serviceAccount: projects/PROJECT_ID/serviceAccounts/build-push@PROJECT_ID.iam.gserviceaccount.com
```

Le compte de build reçoit `roles/securesourcemanager.instanceAccessor` sur l'instance et `roles/securesourcemanager.repoReader` sur le dépôt. Pour isoler les équipes, un compte de service géré par l'utilisateur est associé au dépôt : c'est lui qui lance les builds, à la place de l'agent de service de Secure Source Manager.

## Miroir

Un miroir garde une copie en lecture d'un dépôt qui continue de vivre ailleurs : copie de continuité dans Google Cloud, étape d'une migration, ou source d'un build qui doit tourner à l'intérieur d'un périmètre. Il se monte du côté de la forge source :

- **Depuis GitLab** : le *push mirroring*, disponible dès l'offre gratuite, pousse chaque commit vers le dépôt aval en cinq minutes (une minute si seules les branches protégées sont copiées). Vers Secure Source Manager, passer par SSH : la clé publique du miroir est enregistrée pour un compte de service de l'instance, qui a le rôle d'écriture sur le dépôt.
- **Depuis GitHub** : un job qui s'authentifie par fédération d'identité (voir [Déployer sans clé](#deployer-sans-cle)) puis fait `git push --mirror` vers l'instance en HTTPS, avec l'assistant d'authentification `gcloud.sh`.
- **Sens unique.** Personne ne pousse dans le miroir : les commits et les revues restent du côté de la source, seuls les déclencheurs peuvent vivre du côté du miroir.

## Pièges

- **Région.** Une connexion et ses liens sont régionaux, jamais globaux : le déclencheur doit être créé dans la même région, sans quoi le dépôt n'apparaît pas.
- **Jeton personnel d'un salarié.** Son départ ou la révocation de son compte coupe tous les déclencheurs. Autoriser l'application avec un compte robot ou un compte d'équipe.
- **Jetons GitLab à durée de vie limitée.** 365 jours au plus par défaut : à leur expiration, les builds s'arrêtent sans alerte côté Google. Ajouter une nouvelle version du secret avant l'échéance.
- **Pull requests d'un dépôt public.** Toute personne ayant accès en lecture peut ouvrir une PR qui exécute le `cloudbuild.yaml` modifié : garder `--comment-control` actif et donner au déclencheur de PR un compte de service sans droit de publication ni de déploiement.
- **Résidence des données.** Une connexion GitHub de Developer Connect n'est conforme aux exigences de résidence que créée dans la console avec l'option dédiée ; créée par `gcloud`, elle ne l'est pas.
- **Deux mécanismes sur le même dépôt.** Chaque connexion pose son propre webhook : un dépôt branché à la fois par Developer Connect et par la 2ᵉ génération, avec un déclencheur de chaque côté, construit deux fois chaque commit.

## Alternatives en logiciel libre

Hors de Google Cloud, le raccordement d'un dépôt se répartit entre la forge, qui émet les webhooks, et le moteur d'intégration continue, qui les reçoit.

- **Forgejo** (GPL v3+) et **Gitea** (MIT) : forges auto-hébergées, avec webhooks, jetons de déploiement et moteur d'actions intégré ; l'équivalent d'une instance Secure Source Manager.
- **GitLab CE** (MIT) : forge et intégration continue réunies, sans connexion à déclarer entre les deux ; miroir *pull* ou *push* vers un autre dépôt.
- **Gerrit** (Apache 2.0) : serveur Git à revue commit par commit, dont les événements déclenchent Jenkins ou Tekton.
- **Tekton Triggers** et **Argo Events** (Apache 2.0) : réception d'un webhook, filtrage de la charge utile, puis lancement d'un pipeline — le chemin webhook → déclencheur.
- **OpenBao** (MPL 2.0) avec **External Secrets Operator** (Apache 2.0) : stockage et rotation des jetons d'accès aux dépôts, projetés dans les pipelines qui les consomment.
