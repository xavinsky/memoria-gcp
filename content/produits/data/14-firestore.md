---
title: Firestore
subgroup: Bases de données
icon: categories/databases
aka: Cloud Firestore, Cloud Datastore
schema:
  size: [760, 320]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 576, h: 288}
  nodes:
    clients: {label: Applis, sub: "mobile, web", external: true, x: 8, y: 132, w: 120}
    rules: {label: Règles de sécurité, icon: categories/security-identity, x: 196, y: 40, w: 190}
    fs: {label: Firestore, sub: "collections, documents", icon: categories/databases, focus: true, x: 196, y: 132, w: 200, h: 70}
    fn: {label: Cloud Run functions, sub: déclencheurs, icon: produits/cloud-run, x: 430, y: 36, w: 200}
    gcs: {label: Cloud Storage, sub: exports planifiés, icon: produits/cloud-storage, x: 430, y: 132, w: 160}
    bq: {label: BigQuery, sub: chargement, icon: produits/bigquery, x: 616, y: 132, w: 126}
    backup: {label: Sauvegardes, sub: PITR 7 jours, icon: categories/storage, x: 430, y: 232, w: 150}
  flows:
    - {from: clients, to: fs, text: "Les SDK mobiles et web parlent à la base sans serveur intermédiaire, et s'abonnent aux documents pour recevoir les changements en temps réel"}
    - {from: rules, to: fs, control: true, text: "Les règles de sécurité filtrent chaque requête venue d'un client, document par document, avant qu'elle n'atteigne les données"}
    - {from: fs, to: fn, from_side: top, from_offset: 60, text: "Chaque création, modification ou suppression de document déclenche une fonction par Eventarc"}
    - {from: fs, to: gcs, text: "Export planifié des collections vers un bucket, au format d'export Firestore"}
    - {from: gcs, to: bq, text: "L'export est chargé dans BigQuery pour l'analyse et les rapprochements"}
    - {from: fs, to: backup, from_offset: 20, text: "Sauvegardes planifiées et restauration à un instant donné dans les sept derniers jours"}
captures:
  - image: https://docs.cloud.google.com/static/firestore/native/docs/images/firestore-query-builder.png
    page: https://docs.cloud.google.com/firestore/native/docs/using-console
    legende: "Constructeur de requêtes de la console : chemin de collection, clauses de filtre et résultats en tableau"
  - image: https://docs.cloud.google.com/static/firestore/native/docs/images/firestore-console-edit-path.png
    page: https://docs.cloud.google.com/firestore/native/docs/using-console
    legende: "Firestore Studio en vue panneaux : la base, ses collections et les documents d'une collection, avec le chemin en fil d'Ariane"
docs:
  Page produit: https://cloud.google.com/products/firestore
  Documentation: https://docs.cloud.google.com/firestore/native/docs
  Éditions: https://docs.cloud.google.com/firestore/native/docs/editions-overview
  Modèle de données: https://docs.cloud.google.com/firestore/native/docs/data-model
  Règles de sécurité: https://docs.cloud.google.com/firestore/native/docs/security/get-started
  Recherche vectorielle: https://docs.cloud.google.com/firestore/native/docs/vector-search
  Compatibilité MongoDB: https://docs.cloud.google.com/firestore/mongodb-compatibility/docs
  Compatibilité Datastore: https://docs.cloud.google.com/datastore/docs
  API REST: https://docs.cloud.google.com/firestore/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/firestore
  Bibliothèques clientes: https://docs.cloud.google.com/firestore/native/docs/reference/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/firestore/latest
  Quotas et limites: https://docs.cloud.google.com/firestore/quotas
  Tarifs: https://cloud.google.com/firestore/pricing
  Notes de version: https://docs.cloud.google.com/firestore/docs/release-notes
---

## Ce que c'est

Base de **documents** serverless : pas d'instance à dimensionner, la capacité suit la charge et la facturation se fait à l'usage. Les données sont rangées en *collections* de *documents*, chaque document portant des champs typés et, éventuellement, ses propres sous-collections.

- **Trois interfaces pour une même base.** Les bibliothèques clientes Firestore (avec les SDK mobiles et web du côté Firebase) ; une API compatible **MongoDB**, qui accepte `mongosh`, Compass et les pilotes MongoDB ; une couche de compatibilité **Datastore** pour les applications App Engine existantes.
- **Temps réel et hors ligne.** Les SDK mobiles et web s'abonnent à un document ou à une requête et reçoivent chaque changement ; ils gardent un cache local et rejouent les écritures à la reconnexion.
- **Règles de sécurité.** Comme les clients attaquent la base directement, l'autorisation se décrit en *Security Rules*, évaluées à chaque requête. C'est ce fichier qui tient lieu de couche d'accès, pas du code serveur.
- **Deux éditions.** *Standard* : moteur de requêtes de base, indexation automatique de tous les champs, toute requête exige un index couvrant. *Enterprise* : moteur avancé (plus de 180 étapes et opérateurs, agrégations, jointures), index personnalisables, requêtes sans index, recherche plein texte et géospatiale [!PREVERSION], et l'API compatible MongoDB.
- **Cohérence et disponibilité** : requêtes fortement cohérentes, transactions ACID, réplication automatique. SLA de 99,99 % pour une base régionale, 99,999 % en multirégional.
- **Limites** : un document fait au plus 1 Mio (16 Mio avec l'API MongoDB en édition Enterprise), une requête API au plus 10 Mio, une transaction dure au plus 270 secondes.
- **Recherche vectorielle** intégrée, pour la recherche sémantique sur les documents.
- **Reprise** : sauvegardes planifiées et restauration à un instant donné sur sept jours, export et import vers Cloud Storage.
- **Facturation** : l'édition Standard compte les documents lus et écrits ; l'édition Enterprise compte les octets lus et écrits. S'y ajoutent le stockage et la sortie réseau.

> [!WARNING]
> Une collection dont les documents portent un champ indexé à valeurs croissantes (un horodatage, par exemple) plafonne à environ 500 écritures par seconde. Et en montée en charge sur une nouvelle collection, la règle « 500/50/5 » s'applique : démarrer à 500 opérations par seconde, puis augmenter de 50 % toutes les cinq minutes.

## À quoi ça sert

- Application web ou mobile dont les clients lisent et écrivent directement la base, avec synchronisation entre appareils : messagerie, collaboration, suivi d'état, jeu.
- Catalogues, profils et préférences : des documents indépendants, de forme variable, lus par identifiant.
- Reprise d'une application MongoDB sans réécrire les requêtes, quand on cherche un service géré à l'usage.
- Backend de fonctions événementielles : chaque écriture déclenche un traitement par Eventarc.

**À éviter** quand les données sont fortement relationnelles, avec des jointures et des contraintes d'intégrité : préférer [Cloud SQL](#cloud-sql) ou [AlloyDB](#alloydb). À éviter aussi pour des compteurs très sollicités et des séries temporelles à haut débit ([Bigtable](#bigtable)), et pour l'analyse sur l'ensemble des documents, qui passe par un export vers [BigQuery](#bigquery). Voir [Choisir une base de données](#choisir-une-base).

## Alternatives en logiciel libre

- **FerretDB** (licence Apache 2.0) : le modèle document avec le protocole MongoDB, rejoué au-dessus de PostgreSQL. MongoDB lui-même est sous licence SSPL, qui n'est pas libre.
- **CouchDB** : documents JSON, réplication bidirectionnelle et synchronisation hors ligne avec **PouchDB** côté client — le plus proche de l'expérience temps réel de Firestore.
- **RethinkDB** : requêtes qui poussent leurs changements au client, l'équivalent des écoutes en temps réel.
- **Supabase Realtime** (PostgreSQL et sa réplication logique) : la synchronisation temps réel bâtie sur une base relationnelle.
- **PostgreSQL** avec des colonnes `jsonb` : ranger des documents sans quitter le relationnel, quand le volume le permet.
