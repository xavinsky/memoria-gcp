---
title: Cloud Workstations
subgroup: Poste de développement
icon: categories/developer-tools
schema:
  size: [760, 300]
  zones:
    - {label: "Projet GCP, réseau VPC", x: 180, y: 16, w: 566, h: 268}
  nodes:
    dev: {label: Développeur, sub: "navigateur, IDE, SSH", external: true, x: 10, y: 118, w: 165}
    gw: {label: Cluster de postes, sub: "passerelle, contrôleur", icon: categories/developer-tools, x: 200, y: 40, w: 200}
    ws: {label: Cloud Workstations, sub: "VM, disque /home", icon: categories/developer-tools, focus: true, x: 285, y: 130, w: 200, h: 60}
    ar: {label: Artifact Registry, sub: "image du poste", icon: categories/devops, x: 200, y: 216, w: 195}
    sql: {label: Cloud SQL, sub: "IP privée", icon: produits/cloud-sql, x: 560, y: 40, w: 150}
    gcs: {label: Cloud Storage, sub: "buckets du projet", icon: produits/cloud-storage, x: 555, y: 130, w: 175}
  flows:
    - {from: dev, to: gw, text: "Le développeur ouvre son poste dans le navigateur, depuis son IDE local ou en SSH ; la passerelle du cluster authentifie la requête et la route vers la bonne VM."}
    - {from: gw, to: ws, control: true, text: "Le contrôleur crée la VM à la demande, y rattache le disque persistant monté sur /home et la supprime à la fin de la session."}
    - {from: ar, to: ws, text: "Au démarrage, la VM tire l'image de conteneur déclarée dans la configuration : c'est elle qui fixe l'IDE, les langages et l'outillage."}
    - {from: ws, to: sql, from_offset: -14, text: "Le poste étant dans le VPC du projet, il atteint les bases en IP privée, sans exposer d'adresse publique ni ouvrir de tunnel."}
    - {from: ws, to: gcs, from_offset: 14, text: "Le compte de service du poste lit et écrit les buckets du projet avec ses propres droits IAM."}
captures:
  - image: https://docs.cloud.google.com/static/workstations/images/code-editor-with-terminal.png
    page: https://docs.cloud.google.com/workstations/docs/base-editor-overview
    legende: "L'éditeur de base (Code OSS for Cloud Workstations) dans le navigateur : explorateur, fichier ouvert et terminal du poste"
  - image: https://docs.cloud.google.com/static/workstations/images/console-configurations-page-create-button.png
    page: https://docs.cloud.google.com/workstations/docs/quickstart-set-up-workstations-console
    legende: "Liste des configurations de postes dans la console : état, cluster et type de machine de chaque modèle"
docs:
  Page produit: https://cloud.google.com/workstations
  Documentation: https://docs.cloud.google.com/workstations/docs
  Vue d'ensemble: https://docs.cloud.google.com/workstations/docs/overview
  Architecture: https://docs.cloud.google.com/workstations/docs/architecture
  Images de base préconfigurées: https://docs.cloud.google.com/workstations/docs/preconfigured-base-images
  Images de conteneur personnalisées: https://docs.cloud.google.com/workstations/docs/customize-container-images
  Contrôle d'accès IAM: https://docs.cloud.google.com/workstations/docs/access-control
  API REST: https://docs.cloud.google.com/workstations/docs/reference/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/workstations
  Quotas et limites: https://docs.cloud.google.com/workstations/docs/quotas
  Tarifs: https://cloud.google.com/workstations/pricing
  Notes de version: https://docs.cloud.google.com/workstations/docs/release-notes
---

## Ce que c'est

Environnements de développement gérés, décrits une fois et distribués à toute une équipe. Le poste est une VM Compute Engine du projet, dans son VPC, avec l'outillage figé dans une image de conteneur.

- **Trois ressources.** Le **cluster de postes** regroupe les postes d'une région et porte le réseau VPC auquel ils sont rattachés ; il fournit un contrôleur (cycle de vie des VM) et une passerelle (entrée du trafic). La **configuration de poste** sert de modèle : type de machine, disque, image de conteneur, IDE, délais d'inactivité, droits IAM. Le **poste** est l'instance qu'un développeur crée à partir d'une configuration.
- **Cycle de vie.** La VM est éphémère : créée au démarrage du poste, supprimée à la fin de la session. Un *idle timeout* et un *running timeout* l'arrêtent automatiquement. Toute modification de la configuration s'applique au redémarrage suivant de chaque poste.
- **Persistance.** Le répertoire `/home` est un disque persistant détaché puis réattaché d'une session à l'autre, et supprimé avec le poste sauf s'il est configuré pour être conservé. Le reste du système de fichiers disparaît à chaque arrêt.
- **Réseau.** Le contrôleur dialogue avec le VPC par Private Service Connect, sans consommer de *peering*. Chaque poste porte un nom de domaine propre, sous le domaine du cluster (`WORKSTATION.CLUSTER.cloudworkstations.dev`). Une passerelle entièrement privée limite l'accès aux seuls points d'entrée du réseau privé ; VPC Service Controls, IAP, CMEK et le VPC partagé sont pris en charge.
- **Images.** Des images de base préconfigurées fournissent l'éditeur maison **Code OSS for Cloud Workstations** (extensions Open VSX, [Cloud Code](#cloud-code) préinstallé) ou des IDE JetBrains (IntelliJ IDEA Ultimate, PyCharm Professional, GoLand, WebStorm, CLion, PhpStorm, Rider, RubyMine). Une image personnalisée étend une image de base ou repart d'un conteneur Linux quelconque ; publiée dans Artifact Registry, elle est tirée au démarrage.
- **Démarrage.** Un *pool* de VM et de disques préchauffés (option « démarrage rapide ») supprime l'attente de création ; l'*image streaming* réduit le temps de récupération de l'image de minutes à secondes, à condition que l'image soit dans Artifact Registry et que la configuration porte un compte de service.
- **Accès.** Navigateur, IDE local (VS Code ou JetBrains via un tunnel ouvert par `gcloud workstations start-tcp-tunnel`), ou SSH.
- **Facturation.** Les ressources Compute Engine et Persistent Disk au tarif habituel, plus des frais de gestion de 0,05 $ par vCPU et par heure de poste démarré, plus 0,20 $ par heure et par cluster — ce dernier étant facturé même sans poste actif.

> [!WARNING]
> Le cluster de postes coûte 0,20 $/h en permanence, poste allumé ou non : environ 145 $ par mois et par région. Un projet d'essai laissé en place se paie sans rien produire.

## À quoi ça sert

- Donner à une équipe un poste identique et reproductible, mis à jour en changeant l'image : plus de « ça marche sur ma machine ».
- Développer contre des ressources privées — bases en IP privée, services internes, dépôts Artifact Registry — sans VPN ni bastion, puisque le poste est déjà dans le VPC.
- Garder le code source hors des portables : rien ne quitte le périmètre du projet, ce qui se combine avec VPC Service Controls et les règles d'accès contextuel.
- Fournir une grosse machine (jusqu'aux GPU) à des travaux que le portable ne tient pas : compilation lourde, jeux de données volumineux.
- Intégrer des prestataires ou des équipes distantes avec un poste jetable et des droits IAM explicites.

**À éviter** pour du dépannage ponctuel ou une commande `gcloud` occasionnelle : [Cloud Shell](#cloud-shell) est gratuit, déjà authentifié et démarre en quelques secondes. À éviter aussi quand l'équipe travaille sur des projets sans ressources privées et sans contrainte de conformité : l'addition (VM + disque + frais de gestion + cluster) dépasse vite l'intérêt face à un poste local équipé de [Cloud Code](#cloud-code) et de la [gcloud CLI](#cloud-sdk).

## Alternatives en logiciel libre

- **Coder** (licence AGPL v3, hors fonctions Enterprise) : plateforme d'environnements de développement à distance, provisionnés par Terraform ou OpenTofu, avec accès navigateur, VS Code Remote et SSH ; l'équivalent le plus complet.
- **Eclipse Che** : environnements conteneurisés sur Kubernetes, décrits par un fichier `devfile` — le pendant de la configuration de poste.
- **code-server** : VS Code (Code OSS) servi dans le navigateur depuis un serveur que l'on administre ; couvre l'éditeur, pas le cycle de vie des machines.
- **Eclipse Theia** : socle d'IDE web extensible, compatible avec les extensions Open VSX, comme l'éditeur de base de Cloud Workstations.
- **DevPod** : outil client qui crée un environnement à partir d'un `devcontainer.json` sur n'importe quel fournisseur, y compris une VM Compute Engine ; pas de plan de contrôle central à payer.
- **Dev Containers** (spécification et outillage ouverts) : la brique de description d'environnement que reprennent la plupart des solutions ci-dessus.
