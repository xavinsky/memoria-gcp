---
title: Pulumi GCP en Python
subgroup: Infrastructure
type: syntax
---

Commandes du CLI Pulumi (version 3.264) et appels du fournisseur `pulumi_gcp` (version 9.37), construit à partir du fournisseur Terraform `google-beta`. Imports supposés : `import pulumi`, `import pulumi_gcp as gcp`.

### CLI : projet, état, configuration

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Créer un projet Python pour GCP | `pulumi new gcp-python --name reseau --stack dev` | `Pulumi.yaml`, `__main__.py`, `requirements.txt` et environnement virtuel |
| Garder l'état dans Cloud Storage | `pulumi login gs://BUCKET_ETAT` | Un fichier d'état par stack dans le bucket ; `pulumi login --local` pour `~/.pulumi` |
| Créer une stack, secrets par Cloud KMS | `pulumi stack init prod --secrets-provider="gcpkms://projects/PROJECT_ID/locations/REGION/keyRings/KR/cryptoKeys/KEY"` | Sans ce fournisseur, une phrase de passe à distribuer (`PULUMI_CONFIG_PASSPHRASE`) |
| Changer de stack | `pulumi stack select prod`, `pulumi stack ls` | La stack active est rappelée par `pulumi stack` |
| Fixer projet et région du fournisseur | `pulumi config set gcp:project PROJECT_ID`, `pulumi config set gcp:region REGION` | Écrit dans `Pulumi.STACK.yaml` ; valeurs par défaut de toutes les ressources |
| Valeur de configuration de l'application | `pulumi config set tailleMachine e2-medium` | Lue par `pulumi.Config().require("tailleMachine")` |
| Valeur secrète | `pulumi config set --secret motDePasse VALEUR` | Chiffrée dans `Pulumi.STACK.yaml`, versionnable ; lue par `require_secret` |
| Valeur structurée | `pulumi config set --path 'reseau.cidr' 10.0.0.0/20` | Lue par `require_object("reseau")` |
| Voir les changements prévus | `pulumi preview --diff` | Création, modification, remplacement par ressource ; rien n'est appliqué |
| Détecter la dérive | `pulumi preview --refresh --expect-no-changes` | Code de sortie non nul si l'état réel s'écarte du code : un contrôle de CI |
| Appliquer | `pulumi up` ; en CI `pulumi up --yes --skip-preview` | Crée, modifie ou remplace les ressources |
| Cibler une ressource | `pulumi up --target 'URN'` (URN de `pulumi stack --show-urns`) | Seule cette ressource est traitée ; ajouter `--target-dependents` au besoin |
| Forcer un remplacement | `pulumi up --target-replace 'URN'` | Supprime puis recrée (ou l'inverse) la ressource |
| Relire l'état réel | `pulumi refresh --yes` | Met l'état à jour d'après le cloud, sans toucher aux ressources |
| Tout détruire | `pulumi destroy --yes` (`--exclude-protected` pour épargner les ressources protégées) | Ressources supprimées ; `--remove` supprime aussi la stack |
| Lire une sortie | `pulumi stack output url`, `pulumi stack output --json --show-secrets` | Valeurs exportées par `pulumi.export` |
| Reprendre une ressource existante | `pulumi import gcp:storage/bucket:Bucket etat BUCKET_ETAT` | Ajoute la ressource à l'état, marquée protégée, et affiche le code Python correspondant |
| Oublier une ressource sans la supprimer | `pulumi state delete 'URN'` | Sort de l'état ; la ressource reste dans le cloud |
| Débloquer une stack après une interruption | `pulumi cancel` | Libère le verrou ; puis `pulumi refresh` pour réaligner l'état |

### Programme : ressources et options

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Lire la configuration | `cfg = pulumi.Config()` ; `cfg.require("region")`, `cfg.get_int("replicas") or 1`, `cfg.require_secret("motDePasse")` | `require_secret` renvoie un `Output` secret, masqué partout |
| Lire la configuration du fournisseur | `gcp.config.project`, `gcp.config.region` | Valeurs de `gcp:project` et `gcp:region` |
| Nom de la stack, du projet Pulumi | `pulumi.get_stack()`, `pulumi.get_project()` | Pour nommer et étiqueter selon l'environnement |
| Protéger contre la suppression | `opts=pulumi.ResourceOptions(protect=True)` | `up` et `destroy` refusent de supprimer la ressource |
| Imposer un ordre | `opts=pulumi.ResourceOptions(depends_on=[api_run])` | Pour une dépendance que les entrées ne portent pas (activation d'API avant usage) |
| Rattacher à un composant | `opts=pulumi.ResourceOptions(parent=self)` | Arborescence lisible, options héritées |
| Travailler dans un autre projet | `autre = gcp.Provider("prod", project="PROJECT_ID_2", region="REGION")` puis `opts=pulumi.ResourceOptions(provider=autre)` | Un fournisseur par projet ou par compte de service (`impersonate_service_account=`) |
| Étiquettes sur toutes les ressources | `gcp.Provider(..., default_labels={"env": "prod", "equipe": "data"})` | Fusionnées avec les `labels` de chaque ressource |
| Ignorer un champ modifié ailleurs | `opts=pulumi.ResourceOptions(ignore_changes=["template.containers[0].image"])` | Le déploiement applicatif change l'image sans que `up` la remette |
| Remplacer en supprimant d'abord | `opts=pulumi.ResourceOptions(delete_before_replace=True)` | Nécessaire quand le nom est unique (compte de service, bucket nommé) |
| Renommer sans recréer | `opts=pulumi.ResourceOptions(aliases=[pulumi.Alias(name="ancien-nom")])` | La ressource garde son identité dans l'état |
| Garder la ressource à la suppression | `opts=pulumi.ResourceOptions(retain_on_delete=True)` | Retirée de l'état, conservée dans le cloud |

### Sorties (`Output`)

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Transformer une valeur calculée | `bucket.url.apply(lambda u: f"{u}/data")` | Nouvel `Output` ; la fonction s'exécute quand la valeur est connue |
| Combiner plusieurs sorties | `pulumi.Output.all(sa.email, projet.project_id).apply(lambda a: f"{a[0]} dans {a[1]}")` | Un seul `Output` à partir de plusieurs |
| Concaténer des chaînes | `pulumi.Output.concat("serviceAccount:", sa.email)` | Raccourci pour construire un membre IAM |
| Formater | `pulumi.Output.format("gs://{0}/in", bucket.name)` | Équivalent de `str.format` |
| Marquer comme secret | `pulumi.Output.secret(valeur)` | Chiffré dans l'état, masqué dans les journaux |
| Publier une sortie | `pulumi.export("url", service.uri)` | Lisible par `pulumi stack output` et par `StackReference` |
| Lire les sorties d'une autre stack | `ref = pulumi.StackReference("organization/reseau/prod")` ; `ref.require_output("subnet_id")` | Avec un état Cloud Storage, l'organisation est toujours `organization` |

> [!WARNING]
> `str(bucket.name)` ou un f-string sur un `Output` produit un texte d'avertissement, pas la valeur : passer par `apply`, `concat` ou `format`. Et ne jamais créer une ressource dans un `apply` : elle n'apparaît pas dans `preview`.

### Ressources courantes

| Objectif | Syntaxe | Résultat |
|---|---|---|
| Activer une API | `gcp.projects.Service("run", service="run.googleapis.com", disable_on_destroy=False)` | API laissée active si la ressource est retirée du code |
| Bucket | `gcp.storage.Bucket("data", location="EU", uniform_bucket_level_access=True, public_access_prevention="enforced", versioning={"enabled": True})` | Nom = nom logique + suffixe aléatoire, sauf `name=` explicite |
| Compte de service | `gcp.serviceaccount.Account("app", account_id="sa-app", display_name="Application")` | `.email` pour les liaisons IAM |
| Rôle sur le projet | `gcp.projects.IAMMember("app-bq", project=PROJECT_ID, role="roles/bigquery.dataViewer", member=sa.member)` | Ajoute une liaison sans toucher aux autres ; `IAMBinding` et `IAMPolicy` sont exclusifs |
| Rôle sur un bucket | `gcp.storage.BucketIAMMember("lecture", bucket=bucket.name, role="roles/storage.objectViewer", member=sa.member)` | Droit limité à ce bucket |
| Service Cloud Run | `gcp.cloudrunv2.Service("api", location=REGION, template={"containers": [{"image": IMAGE}], "service_account": sa.email}, ingress="INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER")` | `.uri` : URL du service ; `deletion_protection` vaut `True` par défaut |
| Autoriser l'appel d'un service Cloud Run | `gcp.cloudrunv2.ServiceIamMember("invoker", name=svc.name, location=REGION, role="roles/run.invoker", member=appelant.member)` | Appel authentifié par l'identité de l'appelant |
| Réseau VPC en mode personnalisé | `gcp.compute.Network("vpc", auto_create_subnetworks=False, routing_mode="GLOBAL")` | Aucun sous-réseau créé automatiquement |
| Sous-réseau | `gcp.compute.Subnetwork("app", network=vpc.id, region=REGION, ip_cidr_range="10.10.0.0/20", private_ip_google_access=True, secondary_ip_ranges=[{"range_name": "pods", "ip_cidr_range": "10.20.0.0/16"}])` | Plage secondaire pour les pods GKE |
| Instance Cloud SQL | `gcp.sql.DatabaseInstance("pg", database_version="POSTGRES_16", region=REGION, settings={"edition": "ENTERPRISE", "tier": "db-custom-2-7680", "availability_type": "REGIONAL", "ip_configuration": {"ipv4_enabled": False, "private_network": vpc.id}})` | Sans `edition`, PostgreSQL 16 et plus passe en `ENTERPRISE_PLUS`, qui refuse les types `db-custom-*` ; `deletion_protection` vaut `True` par défaut ; accès privé à préparer sur le VPC |
| Base et utilisateur Cloud SQL | `gcp.sql.Database("app", instance=pg.name)`, `gcp.sql.User("app", instance=pg.name, password=cfg.require_secret("motDePasse"))` | Mot de passe secret dans l'état |
| Dataset BigQuery | `gcp.bigquery.Dataset("ventes", dataset_id="ventes", location="EU", default_table_expiration_ms=90 * 24 * 3600 * 1000)` | `dataset_id` sans tiret ; tables expirées après 90 jours par défaut ; la suppression échoue si des tables existent, sauf `delete_contents_on_destroy=True` |
| Secret (sans sa valeur) | `gcp.secretmanager.Secret("db", secret_id="db-password", replication={"auto": {}})` | La valeur arrive hors du code, par la console ou la CI |
| Dépôt Artifact Registry | `gcp.artifactregistry.Repository("images", repository_id="images", format="DOCKER", location=REGION)` | Adresse `REGION-docker.pkg.dev/PROJECT_ID/images` |

### Composants et tests

```python
class ServiceApp(pulumi.ComponentResource):
    def __init__(self, name: str, image: str, region: str, opts=None):
        super().__init__("memoria:app:ServiceApp", name, None, opts)
        enfant = pulumi.ResourceOptions(parent=self)
        self.sa = gcp.serviceaccount.Account(f"{name}-sa", account_id=f"sa-{name}", opts=enfant)
        self.service = gcp.cloudrunv2.Service(
            f"{name}-run", location=region, deletion_protection=False,
            template={"containers": [{"image": image}], "service_account": self.sa.email},
            opts=enfant,
        )
        self.register_outputs({"uri": self.service.uri})

app = ServiceApp("catalogue", image="REGION-docker.pkg.dev/PROJECT_ID/images/catalogue:1.0", region="REGION")
pulumi.export("uri", app.service.uri)
```

```python
# test_infra.py — lancé par pytest, sans appel au cloud
import pulumi

class Mocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return f"{args.name}-id", args.inputs            # ID et état simulés
    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}, None

pulumi.runtime.set_mocks(Mocks(), project="test", stack="dev", preview=False)
import infra                                             # module du programme, importé après set_mocks

@pulumi.runtime.test
def test_bucket_prive():
    def verifier(args):
        pap, ubla = args
        assert pap == "enforced" and ubla
    return pulumi.Output.all(infra.bucket.public_access_prevention,
                             infra.bucket.uniform_bucket_level_access).apply(verifier)
```

> [!TIP]
> Mettre `pulumi preview --diff` dans la CI de chaque *pull request* et `pulumi up --yes` après fusion : la revue porte sur le plan, pas seulement sur le code (voir [Construire les fondations en code](#fondations-en-code)).

Contexte : [Choisir un outil d'IaC](#choisir-un-outil-iac), [Construire les fondations en code](#fondations-en-code), [Bonnes pratiques IAM](#iam-bonnes-pratiques), [Concevoir le réseau](#concevoir-le-reseau).
