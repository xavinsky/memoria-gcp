---
title: Sécuriser la chaîne logicielle
---

Sécuriser la chaîne logicielle, c'est pouvoir **prouver** que ce qui tourne en production vient d'un code relu, a été construit par un *builder* de confiance à partir de dépendances maîtrisées, et n'a pas été modifié en chemin. Le cadre de référence est [SLSA](#lexterm-slsa-supply-chain-levels-for-software-artifacts) (*Supply-chain Levels for Software Artifacts*). Sur Google Cloud, chaque étape a son contrôle : la provenance signée de [Cloud Build](#cloud-build), l'analyse d'[Artifact Analysis](#artifact-analysis), l'admission par [Binary Authorization](#binary-authorization), et, en transverse, [Secret Manager](#secret-manager) et des identités sans clé.

![Contrôles le long de la chaîne logicielle](../../svg/chaine-logicielle-controles.svg)

## Risque → contrôle

| Risque | Étape | Contrôle | Où le régler |
|---|---|---|---|
| Commit non relu fusionné sur la branche livrée | Source | Branches protégées, revue obligatoire, déclencheur limité à `main` | Forge ou [Secure Source Manager](#secure-source-manager) ; déclencheur Cloud Build |
| *Pull request* externe qui exécute un build avec des droits | Source, build | Contrôle par commentaire `/gcbrun`, approbation (`--require-approval`), compte de service sans droit de production | Déclencheur Cloud Build (voir [Connecter un dépôt](#connecter-un-depot)) |
| Paquet malveillant, confusion de dépendances | Dépendances | Dépôt virtuel qui donne priorité aux paquets privés, dépôt distant analysé, Assured OSS | [Artifact Registry](#artifact-registry) |
| Build falsifié ou exécuté hors de la chaîne | Build | Provenance SLSA niveau 3 signée par Cloud Build, pool privé | `cloudbuild.yaml` : `images`, `requestedVerifyOption` |
| Identifiant écrit dans le dépôt ou le fichier de build | Build, exécution | Secret Manager lu à l'exécution ; fédération d'identité au lieu d'une clé | `availableSecrets`, `--set-secrets` (voir [Déployer sans clé](#deployer-sans-cle)) |
| Compte de service de build trop large | Build | Compte dédié par déclencheur, rôles limités à ce qu'il pousse et déploie | Champ `serviceAccount`, `--service-account` |
| Image vulnérable publiée | Registre | Analyse à la demande bloquante avant la poussée, analyse continue après | Étape de build ; dépôt Artifact Registry |
| Image non construite par la chaîne, ou tag déplacé | Déploiement | Règle Binary Authorization qui exige l'attestation du build, image désignée par son [digest](#lexterm-digest) | Règle du projet ; [Cloud Deploy](#cloud-deploy) fige le digest |
| Pod devenu non conforme, déploiement en bris de glace | Exécution | Validation continue (GKE) | Règle de plateforme Binary Authorization |

## Provenance SLSA de Cloud Build

Cloud Build produit une **provenance** de build conforme au niveau 3 de SLSA (spécifications 0.1 et 1.0) : un document *in-toto* signé qui donne le *digest* de l'image, le dépôt et le commit source, le déclencheur, les étapes et les dépendances résolues. Elle est stockée en occurrence Artifact Analysis et n'existe que pour les artefacts d'Artifact Registry : images de conteneurs, et paquets Go, Maven, Python et npm.

Deux conditions : l'image est poussée par le champ `images`, jamais par une étape `docker push` explicite, et `requestedVerifyOption: VERIFIED` fait échouer le build si la provenance n'a pas pu être produite. Cette option est aussi celle qui active les attestations dans un [pool privé](#lexterm-pool-prive-private-pool).

```yaml
# cloudbuild.yaml : construire, analyser, bloquer au-delà de HIGH, puis pousser par `images`
steps:
  - id: build
    name: gcr.io/cloud-builders/docker
    args: ["build", "-t", "${_IMAGE}:$SHORT_SHA", "."]
  - id: analyse
    name: gcr.io/google.com/cloudsdktool/cloud-sdk
    entrypoint: bash
    args:
      - -c
      - |
        gcloud artifacts docker images scan ${_IMAGE}:$SHORT_SHA \
          --format='value(response.scan)' > /workspace/scan_id.txt
        if gcloud artifacts docker images list-vulnerabilities "$(cat /workspace/scan_id.txt)" \
          --format='value(vulnerability.effectiveSeverity)' | grep -Exq 'CRITICAL|HIGH'; then
          echo "Vulnérabilité CRITICAL ou HIGH" && exit 1
        fi
images: ["${_IMAGE}:$SHORT_SHA"]
substitutions:
  _IMAGE: REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE
serviceAccount: projects/PROJECT_ID/serviceAccounts/build-push@PROJECT_ID.iam.gserviceaccount.com
options:
  requestedVerifyOption: VERIFIED
  logging: CLOUD_LOGGING_ONLY
```

Les images du champ `images` ne sont poussées qu'une fois toutes les étapes réussies : une image refusée par l'analyse n'atteint jamais le registre. La provenance se lit avec `gcloud artifacts docker images describe IMAGE@sha256:HASH --show-provenance`, et se vérifie hors de Google avec l'outil libre `slsa-verifier` (`--builder-id=https://cloudbuild.googleapis.com/GoogleHostedWorker`).

## Artifact Analysis : avant et après la poussée

| | Analyse automatique | Analyse à la demande (*On-Demand Scanning*) |
|---|---|---|
| Déclenchement | Chaque poussée dans un dépôt Docker où elle est activée | `gcloud artifacts docker images scan`, sur une image locale ou `--remote` |
| Suivi | Réactualisée plusieurs fois par jour ; arrêtée pour une image non tirée depuis 30 jours | Aucun : résultats figés, conservés 48 heures |
| Usage | Tableau de bord continu, contrôles de validation continue | Bloquer un build avant publication |
| Rôle requis | — | `roles/ondemandscanning.admin` pour le compte de build |
| Prix | 0,26 $ par *digest*, une seule fois | 0,26 $ par image analysée |

- **[SBOM](#lexterm-sbom-software-bill-of-materials).** `gcloud artifacts sbom export --uri=IMAGE` produit la nomenclature au format SPDX 2.3 dans un bucket `artifactanalysis-REGION-PROJECT_NUMBER`, créé au besoin ; un SBOM produit ailleurs peut aussi être importé.
- **[VEX](#lexterm-vex-vulnerability-exploitability-exchange).** Une déclaration au format CSAF 2.0 attribue à chaque CVE de l'image un statut `known_affected`, `known_not_affected`, `under_investigation` ou `fixed`. Elle se charge par `gcloud artifacts vulnerabilities load-vex --uri=IMAGE --source=vex.json` et évite de retraiter le même faux positif à chaque analyse.

> [!WARNING]
> Le filtre de gravité de l'analyse à la demande ne bloque que les niveaux listés : `HIGH` seul laisse passer une vulnérabilité `CRITICAL`. Écrire l'expression régulière complète, `CRITICAL|HIGH`.

## Binary Authorization : n'admettre que ce que la chaîne a produit

Au premier build d'un projet, Cloud Build crée l'[attestor](#lexterm-attestation) `built-by-cloud-build` et signe une attestation pour chaque image qu'il pousse par `images`. La règle du projet peut alors n'admettre que ces images :

```yaml
# gcloud container binauthz policy export > policy.yaml, puis import après modification
defaultAdmissionRule:
  evaluationMode: REQUIRE_ATTESTATION
  enforcementMode: DRYRUN_AUDIT_LOG_ONLY     # puis ENFORCED_BLOCK_AND_AUDIT_LOG
  requireAttestationsBy:
    - projects/PROJECT_ID/attestors/built-by-cloud-build
globalPolicyEvaluationMode: ENABLE
name: projects/PROJECT_ID/policy
```

| | Cloud Run | GKE |
|---|---|---|
| Activation | `gcloud run deploy SERVICE --binary-authorization=default` (ou `services update`, `jobs update`) | `gcloud container clusters update CLUSTER --region=REGION --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE` |
| Moment du contrôle | Chaque nouvelle révision d'un service ; chaque exécution d'un job | Chaque création de pod |
| Règles spécifiques | Règle par défaut seulement | Par cluster, espace de noms, compte de service Kubernetes |
| Imposer le contrôle | Contrainte d'organisation `run.allowedBinaryAuthorizationPolicies` | Activation cluster par cluster |
| [!PREVERSION] Validation continue | Non | Oui |
| Prix | Gratuit | Facturé par cluster et par heure |

**Validation continue** [!PREVERSION]. Elle repose sur des règles de plateforme distinctes de la règle du projet, faites de contrôles : `slsaCheck` (provenance d'un builder de confiance, Cloud Build étant le seul accepté), `simpleSigningAttestationCheck`, `sigstoreSignatureCheck`, `trustedDirectoryCheck`, `vulnerabilityCheck` (seuils de gravité, CVE autorisées ou bloquées), `imageFreshnessCheck`. Chaque pod est réexaminé au moins toutes les 24 heures et les écarts sont écrits dans Cloud Logging ; aucun pod n'est arrêté. Le mode `POLICY_BINDINGS_AND_PROJECT_SINGLETON_POLICY_ENFORCE` garde l'application à l'admission en ajoutant la surveillance.

## Secrets : lus à l'exécution, jamais écrits

- **Dans un build.** `availableSecrets.secretManager` associe une version de secret à un nom de variable ; seules les étapes qui le déclarent dans `secretEnv` le reçoivent, et seulement dans `args`, écrit `$$NOM` avec `entrypoint: bash`. Le compte de service du build reçoit `roles/secretmanager.secretAccessor` sur ce secret précis, pas sur le projet.
- **À l'exécution.** Cloud Run injecte un secret en variable d'environnement (`--set-secrets=DB_PASS=db-pass:3`), résolue au démarrage de l'instance : figer un numéro de version plutôt que `latest`. Monté en fichier (`--set-secrets=/secrets/db=db-pass:latest`), il est relu à chaque accès et suit les nouvelles versions.
- **Rotation.** Une période de rotation (une heure au minimum) et une prochaine échéance font publier un message `SECRET_ROTATE` sur un sujet [Pub/Sub](#pubsub) ; c'est l'abonné qui produit la nouvelle valeur et ajoute la version. Désactiver l'ancienne version une fois les consommateurs passés.
- **Jamais dans le dépôt.** Ni fichier `.env`, ni clé JSON de compte de service, ni jeton dans `substitutions`. Pour les pipelines extérieurs, la [fédération d'identité de charge de travail](#workload-identity-federation) remplace la clé (voir [Déployer sans clé](#deployer-sans-cle)).

## Comptes de service de build

Selon les réglages de l'organisation, un build sans compte explicite s'exécute sous le compte de service Compute Engine par défaut ou sous le compte Cloud Build historique (`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`, rôle `roles/cloudbuild.builds.builder`), tous deux plus larges que nécessaire. Un compte par usage :

- **Construire et pousser** : `roles/artifactregistry.writer` sur le dépôt, `roles/ondemandscanning.admin`, `roles/logging.logWriter`.
- **Déployer** : `roles/run.developer` sur le projet ou le service (ou les rôles Cloud Deploy équivalents), et `roles/iam.serviceAccountUser` sur le seul compte d'exécution du service.
- **Pull requests** : un compte sans aucun droit de publication ni de déploiement.

Avec un compte choisi, les journaux doivent aller dans Cloud Logging (`logging: CLOUD_LOGGING_ONLY`) ou dans un bucket du projet. La personne qui crée le déclencheur doit pouvoir agir en tant que ce compte (`roles/iam.serviceAccountUser`).

## Dépendances : un point d'entrée contrôlé

Un **dépôt distant** Artifact Registry sert de cache à PyPI, npm, Maven Central ou Docker Hub : les paquets tirés sont analysés et restent disponibles si la source amont tombe. Un **dépôt virtuel** réunit ce cache et le dépôt interne derrière une seule URL, avec une priorité par dépôt amont (la valeur la plus haute gagne) : placer le dépôt privé en tête empêche un paquet public homonyme de passer devant un paquet interne.

```bash
gcloud artifacts repositories create pypi-cache --location=REGION \
  --repository-format=python --mode=remote-repository --remote-python-repo=PYPI
gcloud artifacts repositories create pypi --location=REGION \
  --repository-format=python --mode=virtual-repository --upstream-policy-file=amont.json
# amont.json : [{"id":"interne","repository":"projects/PROJECT_ID/locations/REGION/repositories/pypi-interne","priority":100},
#               {"id":"cache","repository":"projects/PROJECT_ID/locations/REGION/repositories/pypi-cache","priority":10}]
```

**Assured OSS** fournit plus d'un millier de paquets Java, Go, Python et JavaScript construits par Google au niveau 3 de SLSA, avec provenance signée, SBOM (SPDX) et informations VEX (CycloneDX). Ils vivent dans un dépôt Artifact Registry géré par Google, qu'on atteint par un dépôt distant, par un dépôt virtuel ou directement avec un compte de service. Le niveau gratuit couvre Python, Go et Java avec une configuration manuelle ; le niveau Premium, inclus dans Security Command Center Premium ou Enterprise, ajoute JavaScript et la configuration automatique.

## Pièges

- **`docker push` dans une étape.** Pas de provenance, pas d'attestation, et Binary Authorization refuse l'image : pousser par le champ `images`.
- **Construire et déployer dans le même `cloudbuild.yaml`.** L'attestation n'existe qu'une fois le build terminé ; l'étape de déploiement du même build la précède. Séparer le build du déploiement, confié à un second build ou à Cloud Deploy.
- **Binary Authorization désactivable sur Cloud Run.** Sans la contrainte d'organisation, un développeur retire l'option au déploiement suivant. Les fonctions déployées depuis la source demandent d'exempter `REGION-docker.pkg.dev/PROJECT_ID/cloud-run-source-deploy/**`.
- **Mode bloquant d'emblée.** Passer d'abord par `DRYRUN_AUDIT_LOG_ONLY`, lire les journaux d'audit, puis durcir ; une modification de la règle ne s'applique pas aux révisions et aux pods déjà lancés.
- **Tags mouvants.** La règle et les contrôles jugent un *digest* ; déployer `IMAGE@sha256:...`.
- **Activer l'analyse sur un registre existant.** Les images déjà présentes ne sont pas analysées tant qu'elles ne sont pas poussées à nouveau.
- **Secret accordé au compte Cloud Build historique.** Toute personne qui peut lancer un déclencheur utilisant ce compte lit alors le secret pendant le build, sans en avoir le rôle.
- **Afficher un secret dans le journal.** Rien n'empêche une étape de faire `echo $$TOKEN` : les journaux de build sont lisibles par tous ceux qui voient l'historique.

## Alternatives en logiciel libre

- **Tekton Chains** (Apache 2.0) : observe les exécutions Tekton, génère une provenance SLSA au format *in-toto* et la signe, l'équivalent de la provenance produite par Cloud Build.
- **Sigstore** (Apache 2.0) : `cosign` signe images et attestations, **Fulcio** délivre des certificats éphémères à partir d'une identité OIDC, **Rekor** tient le journal de transparence ; une signature sans clé à garder, là où Binary Authorization s'appuie sur des attesteurs et des clés Cloud KMS.
- **Kyverno** et **OPA Gatekeeper** (Apache 2.0) : contrôle d'admission Kubernetes ; la règle `verifyImages` de Kyverno exige signature et attestations comme une règle Binary Authorization, sans équivalent pour Cloud Run.
- **Trivy** (Apache 2.0) : analyse de vulnérabilités, de secrets et de configuration, à lancer en étape de build avant la poussée, comme l'analyse à la demande.
- **Syft** et **Grype** (Apache 2.0), avec **Dependency-Track** (Apache 2.0) : production du SBOM, analyse de ses composants, puis suivi dans la durée des vulnérabilités découvertes après la poussée.
- **OpenBao** (MPL 2.0) et **SOPS** (MPL 2.0) : secrets lus à l'exécution depuis un coffre, ou chiffrés dans le dépôt, face à Secret Manager. Vault, dont OpenBao dérive, est sous BSL et n'est pas libre.
- **Harbor** (Apache 2.0) en cache d'un registre amont, **devpi** (MIT) pour PyPI : un point d'entrée contrôlé pour les dépendances, comme les dépôts distants et virtuels d'Artifact Registry.
