---
title: Network Intelligence Center
subgroup: Réseau
icon: categories/networking
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 176, y: 16, w: 570, h: 268}
  nodes:
    ops: {label: Équipe réseau, sub: "console, API", external: true, x: 8, y: 126, w: 150}
    nic: {label: Network Intelligence Center, sub: "tests, topologie, analyses", icon: categories/observability, focus: true, x: 190, y: 114, w: 270, h: 64}
    logs: {label: VPC Flow Logs, sub: "journaux de flux 5-tuple", icon: categories/observability, x: 190, y: 214, w: 270}
    vm: {label: Compute Engine, sub: "VM source et cible", icon: produits/compute-engine, x: 490, y: 36, w: 210}
    fw: {label: Cloud NGFW, sub: "règles évaluées", icon: categories/networking, x: 490, y: 122, w: 210}
    vpn: {label: Cloud VPN, sub: "tunnel vers le site", icon: categories/networking, x: 490, y: 208, w: 210}
  flows:
    - {from: ops, to: nic, text: "Un test de connectivité est décrit par sa source, sa destination, son protocole et ses ports."}
    - {from: nic, to: fw, text: "L'analyse de configuration rejoue le chemin attendu du paquet : routes, règles de pare-feu, règles de transfert et appairages."}
    - {from: nic, to: vm, from_side: right, to_side: left, from_offset: -22, text: "Quand le scénario s'y prête, une sonde réelle traverse le plan de données et mesure la latence et le taux de perte."}
    - {from: nic, to: vpn, from_side: right, to_side: left, from_offset: 22, text: "Le même test suit le chemin sortant par un tunnel VPN ou un rattachement d'interconnexion jusqu'au réseau sur site."}
    - {from: logs, to: nic, text: "L'analyseur de flux lit les journaux de flux VPC du bucket de journaux et détaille le trafic entrant et sortant de chaque instance."}
    - {from: nic, to: ops, from_offset: 20, to_offset: 20, control: true, text: "Les constats de l'analyseur de réseau et de Firewall Insights reviennent en recommandations, avec la cause probable de chaque échec."}
captures:
  - image: https://docs.cloud.google.com/static/network-intelligence-center/docs/network-topology/images/use-cases/auditing-traffic.png
    page: https://docs.cloud.google.com/network-intelligence-center/docs/network-topology/concepts/auditing-network-performance
    legende: "Network Topology : trafic entre la région EMEA, un équilibreur de charge externe et deux régions Google Cloud, avec le débit de chaque lien"
  - image: https://docs.cloud.google.com/static/network-intelligence-center/docs/connectivity-tests/images/tutorial-successful-trace.png
    page: https://docs.cloud.google.com/network-intelligence-center/docs/connectivity-tests/tutorials/tutorial-troubleshooting-workflow
    legende: "Test de connectivité : chaque étape du chemin simulé, pare-feu, route et NAT, jusqu'à la VM de destination"
docs:
  Page produit: https://cloud.google.com/network-intelligence-center
  Documentation: https://docs.cloud.google.com/network-intelligence-center/docs
  Vue d'ensemble: https://docs.cloud.google.com/network-intelligence-center/docs/overview
  Tests de connectivité: https://docs.cloud.google.com/network-intelligence-center/docs/connectivity-tests/concepts/overview
  Accessibilité et états: https://docs.cloud.google.com/network-intelligence-center/docs/connectivity-tests/concepts/reachability
  Topologie réseau: https://docs.cloud.google.com/network-intelligence-center/docs/network-topology/concepts/overview
  Tableau de bord de performance: https://docs.cloud.google.com/network-intelligence-center/docs/performance-dashboard/concepts/overview
  Firewall Insights: https://docs.cloud.google.com/network-intelligence-center/docs/firewall-insights/concepts/overview
  Analyseur de réseau: https://docs.cloud.google.com/network-intelligence-center/docs/network-analyzer/overview
  Types d'insights: https://docs.cloud.google.com/network-intelligence-center/docs/network-analyzer/insight-groups-types
  Analyseur de flux: https://docs.cloud.google.com/network-intelligence-center/docs/flow-analyzer/overview
  Cloud Network Insights: https://docs.cloud.google.com/network-intelligence-center/docs/cloud-network-insights/overview
  Journaux de flux VPC: https://docs.cloud.google.com/vpc/docs/flow-logs
  API REST: https://docs.cloud.google.com/network-intelligence-center/docs/reference/networkmanagement/rest
  Commandes gcloud: https://docs.cloud.google.com/sdk/gcloud/reference/network-management/connectivity-tests
  Tarifs: https://cloud.google.com/products/network-intelligence-center/pricing
  Notes de version: https://docs.cloud.google.com/network-intelligence-center/docs/release-notes
---

## Ce que c'est

Console unique de visibilité, de surveillance et de dépannage du réseau, faite de modules indépendants qui partagent la configuration et la télémétrie déjà collectées par Google Cloud. Aucun agent à installer : les modules lisent la configuration des ressources, les métriques d'infrastructure et, pour certains, les journaux de flux.

- **Tests de connectivité.** Un test nomme une source et une destination — VM, cluster [GKE](#gke), règle de transfert d'un équilibreur, adresse sur internet — un protocole et des ports. Le module **simule le chemin attendu** à travers le réseau VPC, les tunnels VPN et les rattachements d'interconnexion, et rend une trace étape par étape avec l'état final : accessible, abandonné (en nommant la règle ou la route fautive), non déterminé. Pour les scénarios pris en charge, il envoie aussi une **sonde réelle dans le plan de données** qui confirme la connectivité et donne une mesure de latence et de perte. Un test se réexécute à la demande, ce qui sert de non-régression après un changement de règles.
- **Topologie réseau.** Graphe des réseaux VPC, de leur connectivité hybride, des services gérés et du trafic entre eux, construit à partir de la configuration et de la télémétrie en temps réel. Une vue *GKE Enterprise* descend jusqu'aux clusters, espaces de noms, charges et pods. Les arêtes portent les métriques de débit, y compris entre régions et entre VPC partagés.
- **Tableau de bord de performance.** Latence et perte de paquets telles que Google les mesure, dans deux périmètres : la performance de l'ensemble du réseau Google Cloud, et celle des ressources du projet. C'est ce qui permet de trancher entre « le réseau est dégradé » et « l'application est lente », et de revenir sur un incident passé.
- **Firewall Insights.** Statistiques d'utilisation des règles de pare-feu, détection des règles jamais déclenchées, des règles masquées par une autre et des règles trop permissives, avec prédiction de l'usage à venir. C'est l'outil de nettoyage d'un jeu de règles [Cloud NGFW](#cloud-ngfw) accumulé au fil des ans.
- **Analyseur de réseau.** Surveillance continue de la configuration qui signale les erreurs et les choix sous-optimaux : adresses épuisées dans un sous-réseau, route au saut suivant invalide, route dynamique masquée, backend d'équilibreur mal configuré, adresses inutilisées, écarts aux bonnes pratiques GKE. Chaque constat vient avec sa cause probable et une correction suggérée, et se déclenche à la modification plutôt qu'à intervalle fixe.
- **Analyseur de flux.** Analyse des journaux de flux VPC avec une granularité de quintuplet (adresses et ports source et destination, protocole), sans écrire de SQL ; il s'appuie sur l'analytique d'observabilité et BigQuery, et suppose un bucket de journaux qui contient déjà ces journaux.
- **Cloud Network Insights**, en partenariat avec AppNeta : sondage synthétique actif des chemins réseau entre environnements multicloud et hybrides, y compris quand aucun trafic utilisateur ne circule — de quoi voir venir une dégradation de la connectivité de dernier kilomètre.

> [!TIP]
> Un test de connectivité qui répond « accessible » vaut pour la configuration au moment du test. Sur un incident intermittent, c'est l'analyse du plan de données — ou les journaux de flux via l'analyseur de flux — qui apporte la preuve, pas la simulation.

## À quoi ça sert

- Diagnostiquer une connexion qui ne passe pas, en obtenant le nom exact de la règle de pare-feu, de la route ou de l'appairage qui l'interrompt, au lieu de relire les configurations à la main.
- Valider une architecture avant la mise en service : tester tous les flux prévus entre sous-réseaux, vers les services gérés et vers le réseau sur site, puis rejouer la même batterie après chaque changement.
- Arbitrer entre le réseau et l'application lors d'un ralentissement, avec des mesures de latence et de perte indépendantes de l'instrumentation applicative.
- Faire le ménage dans un jeu de règles de pare-feu en supprimant celles qui ne servent jamais et en resserrant celles qui ouvrent trop large.
- Découvrir la topologie réelle d'un environnement hérité : quels réseaux se parlent, par où, et avec quel volume.
- Comprendre qui consomme le trafic sortant d'une instance, par adresse, par port et par protocole.

**À éviter** comme outil de surveillance applicative : les latences applicatives, les taux d'erreur et les traces distribuées relèvent de Cloud Monitoring et de Cloud Trace. À éviter aussi comme source d'audit de sécurité — les journaux de flux servent à l'analyse du trafic, pas au suivi des accès, qui passe par les journaux d'audit Cloud. Enfin, les modules ne configurent rien : ils constatent et recommandent, les corrections se font dans les produits concernés.

## Alternatives en logiciel libre

- **Batfish** : analyse statique de configurations réseau qui simule les chemins possibles et répond à des questions d'accessibilité — l'équivalent le plus proche de la partie simulation des tests de connectivité.
- **SuzieQ** : collecte de l'état des équipements et interrogation de la topologie et des chemins, avec comparaison entre deux instants.
- **Prometheus** avec **Blackbox Exporter** ou **smokeping_prober**, et **Grafana** : sondage actif de latence et de perte, l'équivalent du tableau de bord de performance et des sondes synthétiques.
- **nfdump**, **GoFlow2** et **Akvorado** : collecte et exploration de flux NetFlow, IPFIX et sFlow, pour l'analyse par quintuplet que fait l'analyseur de flux.
- **NetBox** : source de vérité de l'inventaire et de la topologie réseau, lorsque la carte doit être déclarée plutôt que découverte.
- **Skydive** et **Hubble** (Cilium) : cartographie et suivi des flux à l'intérieur d'un cluster Kubernetes, avec identification des politiques qui les bloquent.
