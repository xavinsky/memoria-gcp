---
title: Partager des données
---

Partager une donnée BigQuery, c'est d'abord choisir **qui la consomme** : une équipe de la même organisation, un partenaire qui écrit du SQL, un analyste qui vit dans un tableur, un lecteur de tableau de bord, un outil hors de Google Cloud. La règle de fond reste la même partout : on donne accès à la donnée en place, sans copie, tant que le consommateur peut l'interroger dans BigQuery ; la copie (export) ne sert qu'aux destinataires qui ne le peuvent pas.

![Arbre de décision : du consommateur au mode de partage](../../svg/choix-partage-donnees.svg)

## Matrice des options

| Option | Destinataire | Copie ? | Qui paie | Contrôle principal |
|---|---|---|---|---|
| **IAM sur dataset ou table** | Équipe interne, compte de service | Non | Le lecteur paie ses requêtes | Rôles BigQuery ; lignes, colonnes et masquage (voir [Données sensibles et gouvernance](#donnees-sensibles-et-gouvernance)) |
| **Vue, dataset ou routine autorisés** | Équipe interne, sous-ensemble ou agrégat | Non | Le lecteur | Le lecteur n'a de droit que sur la vue, jamais sur la table source |
| **Partage BigQuery, fiche de dataset** | Autre projet ou organisation, en privé ou en public | Non : dataset lié en lecture seule | Éditeur : stockage ; abonné : requêtes | Accès par échange et par fiche, restrictions d'export |
| **Partage BigQuery, fiche commerciale** | Clients payants | Non | Abonnement vendu par Google Cloud Marketplace, plus les requêtes de l'abonné | Idem, plus les conditions commerciales |
| **Partage BigQuery, sujet Pub/Sub** | Partenaire qui consomme un flux | Non : abonnement Pub/Sub lié | Éditeur : publication ; abonné : lecture | Accès par fiche, livraison choisie par l'abonné |
| **Salle blanche** (*data clean room*) | Partenaire avec qui croiser des données sensibles | Non | Contributeur : stockage ; abonné : requêtes | Règles d'analyse, modèles de requêtes, export bloqué |
| **Connected Sheets** | Utilisateurs de Google Sheets | Aperçu et extraits dans la feuille | Le projet choisi dans la feuille paie les requêtes | IAM BigQuery ; sans droit BigQuery, pas d'actualisation |
| **[Data Studio](#data-studio) ou [Looker](#looker)** | Lecteurs de tableaux de bord, internes ou externes | Non (cache) | Le projet des identifiants utilisés | Identifiants du propriétaire ou du lecteur ; modèle LookML |
| **Export vers Cloud Storage** | Outil ou plateforme hors de BigQuery | Oui | Export par job d'extraction sans frais de traitement ; transfert facturé s'il change de région | Droits sur le bucket ; la donnée échappe aux contrôles BigQuery |

## Partage BigQuery

Le partage BigQuery (*BigQuery sharing*, ex-Analytics Hub) publie des datasets et des sujets Pub/Sub d'un projet vers d'autres projets, dans ou hors de l'organisation, sur un modèle éditeur-abonné. La console l'appelle **Sharing (Analytics Hub)** ; l'API reste `analyticshub.googleapis.com` et les rôles `roles/analyticshub.*`.

- **Échange** (*data exchange*) : conteneur de fiches, créé dans un projet et une région. **Privé** par défaut, visible des seuls principaux qui y ont accès ; **public**, il est ouvert à tout compte Google Cloud (`allAuthenticatedUsers`). L'accès se donne au niveau de l'échange ou de la fiche, sans droit sur les ressources sous-jacentes.
- **Fiche** (*listing*) : référence vers une ressource partagée, avec sa description, des exemples de requêtes et un contact. Le **dataset partagé** doit être dans la région de l'échange et ne change plus une fois la fiche créée. Il peut contenir tables, vues, vues matérialisées, tables externes, routines, modèles BigQuery ML, et porter une sécurité au niveau ligne ou colonne.
- **Abonnement** : l'abonné crée dans son projet un **dataset lié**, en lecture seule, qui pointe vers le dataset partagé. Aucune copie, pas de stockage facturé à l'abonné, et une modification de schéma chez l'éditeur est visible tout de suite. Un dataset partagé accepte jusqu'à 1 000 datasets liés. Pour un sujet Pub/Sub, l'abonnement crée un **abonnement Pub/Sub lié**, dont l'abonné choisit la livraison (y compris vers BigQuery) ; un sujet partagé accepte 10 000 abonnements.
- **Rôles** : *Analytics Hub Admin* crée les échanges et gère les droits ; *Publisher* crée les fiches, *Listing Admin* les modifie, les supprime et les partage sans en créer ; *Subscriber* s'abonne, *Subscription Owner* gère ses abonnements ; *Viewer* parcourt les fiches et peut demander l'accès.
- **Restrictions d'export** (*data egress*), choisies sur la fiche : bloquer la copie et l'export du dataset partagé, ou aussi celui des résultats de requête, ou l'export des tables par l'API. Une fois bloqués : ni copie, clone, instantané ou export, ni BigQuery Data Transfer Service, ni `CREATE TABLE AS SELECT` ou table de destination.
- **Fiches commerciales** : un échange public intégré à Google Cloud Marketplace vend des abonnements payants, gratuits ou d'essai, pour une durée donnée. L'abonné achète depuis Marketplace ou depuis la page de partage.
- **Suivi** : la vue `INFORMATION_SCHEMA.SHARED_DATASET_USAGE` donne à l'éditeur les jobs, les projets et organisations abonnés, les lignes et octets traités. La journalisation des e-mails des abonnés est une option de l'échange ; une fois enregistrée, elle ne se désactive qu'en recréant l'échange.
- **Coût** : échanges et fiches ne sont pas facturés ; l'éditeur paie le stockage, l'abonné ses requêtes, à la demande ou en slots.

## Salles blanches

Une salle blanche est un échange de partage BigQuery réservé aux données sensibles : plusieurs parties y joignent et analysent leurs données sans voir les lignes des autres. Le **propriétaire** gère l'accès (rôle *Admin*), le **contributeur** publie (*Publisher*), l'**abonné** interroge (*Subscriber* et *Subscription Owner*).

- **Ressources partagées** : tables, vues et fonctions table, jusqu'à 100 par salle ; pas de dataset entier, pas de modèle.
- **Export** : la copie et l'export des données brutes sont bloqués d'office ; le contributeur peut bloquer aussi les résultats de requête.
- **Règles d'analyse**, posées sur une **vue** — une table partagée sans vue à règle reste lisible en clair :

| Règle | Ce qu'elle impose |
|---|---|
| **Seuil d'agrégation** | Requêtes d'agrégation seulement (`SELECT WITH AGGREGATION_THRESHOLD`) ; un groupe qui compte moins d'unités de confidentialité distinctes que le seuil est omis du résultat |
| **Confidentialité différentielle** | Bruit ajouté aux agrégats et budget de confidentialité (epsilon, delta) : l'abonné ne peut plus interroger quand la somme de ses requêtes atteint le budget |
| **Recouvrement de listes** | Seules les lignes présentes des deux côtés d'une jointure sont interrogeables |
| **Restriction de jointure** | Option des trois règles : jointure interne obligatoire sur toutes (`JOIN_ALL`) ou une (`JOIN_ANY`) des colonnes autorisées |

- **Modèles de requêtes** : le propriétaire publie des requêtes approuvées, sous forme de fonctions table, au lieu de laisser l'abonné écrire son SQL. La documentation prévient que les règles d'analyse n'arrêtent pas toute requête conçue pour extraire des lignes : les modèles limitent l'abonné aux requêtes approuvées.
- Les règles d'analyse existent aussi hors salle blanche, posées par `CREATE VIEW ... OPTIONS (privacy_policy = ...)`.

## Région et multicloud

- Une requête BigQuery joint des datasets de la même région ; les requêtes globales [!PREVERSION] lisent d'autres régions en y copiant les données. Le dataset lié se place donc à côté des données de l'abonné. L'éditeur rend sa fiche disponible dans d'autres régions en activant la **réplication inter-régions** du dataset partagé ; l'abonné choisit alors la région principale de son dataset lié, et des répliques, parmi celles de la fiche.
- Les fiches multirégions ne valent ni pour les sujets Pub/Sub, ni pour les salles blanches, ni pour les régions BigQuery Omni.
- Le partage fonctionne dans les régions BigQuery Omni (AWS, Azure) listées par la documentation : on y partage des données qui restent chez l'autre fournisseur.

## Connected Sheets

Connected Sheets ouvre une table, une vue ou une requête enregistrée BigQuery dans Google Sheets (**Data > Data connectors > Connect to BigQuery**). Tableaux croisés, formules et graphiques portent sur toute la table : chacun déclenche une requête BigQuery, à la demande ou selon une planification, facturée au projet choisi. Le détail et le choix face à Data Studio sont dans la fiche [Data Studio](#data-studio).

- Limites : aperçu de 500 lignes ; 200 000 lignes au plus pour le résultat d'un tableau croisé ; extrait vers une feuille sans limite de cellules jusqu'à 50 000 lignes, 5 millions de cellules jusqu'à 500 000 lignes, impossible au-delà.
- Un utilisateur qui n'a accès qu'à la feuille, sans droit BigQuery, analyse les données présentes mais ne peut ni actualiser ni planifier.

## Catalogue interne ou publication

[Knowledge Catalog](#knowledge-catalog) et le partage BigQuery répondent à deux questions différentes :

- **Knowledge Catalog** : *trouver et gouverner* dans l'organisation — recherche, sens métier, lignage, qualité, produits de données. Il décrit les actifs ; les droits restent portés par IAM.
- **Partage BigQuery** : *publier* vers d'autres projets ou organisations, avec abonnement, dataset lié et contrôle de l'export.

Les deux se rejoignent : les datasets et sujets partagés sont indexés dans Knowledge Catalog. Au-delà de 100 abonnés ou de 100 tables dans un dataset partagé, l'indexation d'une modification de schéma peut prendre jusqu'à 18 heures.

## Questions qui départagent

- **IAM ou partage BigQuery ?** Pour quelques équipes de l'organisation, un rôle sur un dataset ou une vue autorisée suffit. Dès qu'il y a des dizaines de consommateurs, des organisations externes, un besoin de catalogue de fiches, de suivi de la consommation ou de blocage de l'export, le partage BigQuery l'emporte.
- **Partage ou salle blanche ?** Si le partenaire peut lire les lignes partagées, une fiche ordinaire suffit, filtrée par vue autorisée ou politique de lignes. S'il faut croiser deux jeux de clients sans que personne ne voie les lignes de l'autre, c'est une salle blanche avec des règles d'analyse.
- **Dataset lié ou export ?** Tant que le consommateur a un projet Google Cloud, le dataset lié évite la copie, reste à jour et laisse l'éditeur couper l'accès. L'export vers Cloud Storage (CSV, JSON, Avro, Parquet ; 1 Go par fichier, au-delà un nom à caractère générique) ne se justifie que pour un outil qui ne lit pas BigQuery.
- **Connected Sheets, Data Studio ou Looker ?** Des analystes qui font leurs propres tableaux croisés : Connected Sheets. Un rapport figé à diffuser largement : Data Studio. Des indicateurs à définition unique partagés par toute l'entreprise : Looker, dont le modèle se lit aussi depuis Connected Sheets et Data Studio.
- **Quel format pour une plateforme de lakehouse ouverte ?** Des tables Iceberg exposées par le catalogue d'exécution se lisent depuis Spark ou d'autres moteurs (voir [Lakehouse](#lakehouse-architecture)) ; le partage BigQuery ne concerne que les consommateurs BigQuery et Pub/Sub.

## Pièges

- **Vue partagée sans autorisation.** Pour interroger une vue d'un dataset lié, l'abonné doit avoir un droit sur le dataset source, sauf si la vue est autorisée. Partager des vues autorisées évite de lui ouvrir la source.
- **Définitions visibles.** Le plan de requête révèle le SQL des vues et routines partagées, avec les ID de projets et les datasets qu'elles lisent : rien de sensible dans ce SQL.
- **Sécurité de lignes et coût de l'abonné.** Une table partagée avec une politique d'accès aux lignes ou un masquage exige de l'abonné une édition Enterprise ou Enterprise Plus pour l'interroger.
- **Droits au niveau table dans un dataset lié.** Impossible : IAM et tags se posent sur le dataset lié entier.
- **Politique d'organisation.** `iam.allowedPolicyMemberDomains` empêche d'accorder un rôle à une identité d'une autre organisation (voir [Hiérarchie des ressources](#hierarchie-des-ressources)).
- **Périmètre VPC Service Controls.** Un échange ou un dataset partagé dans un périmètre demande des règles d'entrée et de sortie pour les projets de l'éditeur, de l'échange et de l'abonné (voir [Périmètres VPC Service Controls](#perimetres-vpc-sc)). Pour Connected Sheets, il faut une règle de sortie vers le projet de Sheets, et une actualisation planifiée échoue si le périmètre filtre sur le contexte de l'utilisateur (adresse IP, appareil).
- **Export sans restriction.** Une fiche sans restriction d'export laisse l'abonné copier tout le dataset dans son projet ; l'éditeur perd alors la main sur la donnée.

## Alternatives en logiciel libre

- **Delta Sharing** (Apache 2.0) : protocole REST ouvert de partage de tables Delta Lake et Parquet posées sur un stockage objet ; le destinataire lit avec pandas ou Spark sans déployer la même plateforme. C'est l'équivalent le plus proche du dataset lié, sans les restrictions d'export.
- **Apache Polaris** (Apache 2.0) : catalogue REST pour Apache Iceberg, avec contrôle d'accès ; plusieurs moteurs lisent les mêmes tables sans copie, comme avec le catalogue d'exécution du lakehouse de Google Cloud.
- **OpenDP** (MIT) : bibliothèque de confidentialité différentielle en Rust, avec des interfaces Python et R ; le mécanisme de la règle de confidentialité différentielle d'une salle blanche, à intégrer soi-même.
- **Differential Privacy de Google** (Apache 2.0) : bibliothèques de statistiques différentiellement privées, dont des variantes pour Apache Beam ; même usage qu'OpenDP.
- **PySyft** (Apache 2.0) : le data scientist soumet un calcul que le propriétaire exécute sur ses données privées ; l'idée des modèles de requêtes approuvés d'une salle blanche.
