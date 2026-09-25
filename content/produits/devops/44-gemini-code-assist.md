---
title: Gemini Code Assist
subgroup: Poste de développement
icon: categories/developer-tools
aka: Duet AI for Developers
schema:
  size: [760, 300]
  zones:
    - {label: Poste du développeur, x: 10, y: 16, w: 290, h: 268}
    - {label: Projet GCP, x: 350, y: 16, w: 396, h: 268}
  nodes:
    ide: {label: IDE, sub: "VS Code, JetBrains", icon: categories/developer-tools, x: 28, y: 46, w: 250}
    mcp: {label: Outils de l'agent, sub: "grep, terminal, MCP", icon: categories/integration-services, x: 28, y: 128, w: 250}
    code: {label: Code source local, sub: "fichiers ouverts, dépôt", icon: categories/devops, x: 28, y: 210, w: 250}
    gca: {label: Gemini Code Assist, sub: "complétion, chat, agent", icon: categories/ai-machine-learning, focus: true, x: 380, y: 120, w: 230, h: 60}
    cons: {label: Console Google Cloud, sub: "Gemini Cloud Assist", icon: categories/management-tools, x: 380, y: 30, w: 250}
    repo: {label: Dépôts privés, sub: "GitHub, GitLab, Bitbucket", icon: categories/devops, x: 380, y: 216, w: 250}
  flows:
    - {from: ide, to: gca, to_offset: -14, text: "L'extension envoie le prompt et le contexte des fichiers ouverts ; complétions, chat et citations de sources reviennent dans l'éditeur."}
    - {from: gca, to: code, from_offset: 14, text: "En mode agent, le modèle propose un plan puis des éditions de fichiers, présentées en différentiel et appliquées après validation."}
    - {from: mcp, to: gca, control: true, text: "Les outils intégrés (lecture, écriture, recherche, terminal) et les serveurs MCP déclarés étendent ce que l'agent peut faire ; toute action modifiante demande une autorisation."}
    - {from: repo, to: gca, text: "L'édition Enterprise indexe les dépôts privés de l'organisation pour aligner les suggestions sur ses pratiques internes."}
    - {from: gca, to: cons, text: "La même licence ouvre l'assistance hors de l'IDE : Gemini Cloud Assist dans la console, insights BigQuery, génération de SQL dans les bases."}
captures:
  - image: https://docs.cloud.google.com/static/gemini/images/intellij-quick-preview.png
    page: https://docs.cloud.google.com/gemini/docs/codeassist/chat-gemini
    legende: "Le chat Gemini Code Assist dans IntelliJ : une demande, les modifications proposées sur un fichier et leur validation"
  - image: https://docs.cloud.google.com/static/gemini/images/intellij-accept-reject-diff.png
    page: https://docs.cloud.google.com/gemini/docs/codeassist/chat-gemini
    legende: "Les modifications proposées affichées dans l'éditeur, à accepter ou rejeter une par une"
docs:
  Documentation: https://docs.cloud.google.com/gemini/docs/codeassist/overview
  Configurer Gemini Code Assist: https://docs.cloud.google.com/gemini/docs/codeassist/set-up-gemini
  Écrire du code: https://docs.cloud.google.com/gemini/docs/codeassist/write-code-gemini
  Chat dans l'IDE: https://docs.cloud.google.com/gemini/docs/codeassist/chat-overview
  Mode agent: https://docs.cloud.google.com/gemini/docs/codeassist/agent-mode
  Personnalisation du code: https://docs.cloud.google.com/gemini/docs/codeassist/code-customization-overview
  Revue de code sur un dépôt: https://docs.cloud.google.com/gemini/docs/code-review/review-repo-code
  Fichier .aiexclude: https://docs.cloud.google.com/gemini/docs/codeassist/create-aiexclude-file
  Langages pris en charge: https://docs.cloud.google.com/gemini/docs/codeassist/supported-languages
  Gestion des licences: https://docs.cloud.google.com/gemini/docs/codeassist/manage-licenses
  Sécurité et conformité: https://docs.cloud.google.com/gemini/docs/codeassist/security-privacy-compliance
  APIs et références: https://docs.cloud.google.com/gemini/docs/api-and-reference
  Quotas: https://docs.cloud.google.com/gemini/docs/quotas
  Tarifs: https://cloud.google.com/products/gemini/pricing
  Notes de version: https://docs.cloud.google.com/gemini/docs/release-notes
---

## Ce que c'est

Assistance au code adossée aux modèles Gemini, vendue par licence nommée dans deux éditions, **Standard** et **Enterprise**, au sein de l'offre Gemini for Google Cloud.

- **Dans l'IDE.** Extension pour VS Code, les IDE JetBrains (IntelliJ, PyCharm) et Android Studio ; disponible aussi dans l'éditeur [Cloud Shell](#cloud-shell) et dans les images [Cloud Workstations](#cloud-workstations). Elle apporte la complétion au fil de la frappe, la génération de blocs à partir d'un commentaire, un chat conversationnel qui voit les fichiers ouverts, des *smart actions* au clic droit et des commandes préfixées par `/` (générer, expliquer, tester, corriger). Le code proposé est présenté en différentiel avant d'être accepté.
- **Contexte local.** La *local codebase awareness* étend la lecture au-delà du fichier courant, sur les dossiers et fichiers désignés dans le tiroir de contexte. Un fichier `.aiexclude` retire des chemins du contexte envoyé.
- [!PREVERSION] **Mode agent** (VS Code et IntelliJ). Le prompt part avec une liste d'outils : lecture et écriture de fichiers, `grep`, terminal, recherche Google, plus les serveurs **MCP** déclarés. Pour une tâche complexe, l'agent propose un plan à approuver, puis enchaîne action et évaluation ; toute opération modifiante demande une autorisation, qui peut être accordée une fois ou durablement. Les citations de sources ne sont pas disponibles dans ce mode.
- **Personnalisation (Enterprise seulement).** Indexation des dépôts privés de l'organisation — GitHub, GitLab, Bitbucket — pour que les suggestions reprennent les bibliothèques et les conventions internes.
- **Hors de l'IDE.** La licence Standard ouvre l'assistance dans Cloud Run, Colab Enterprise, les *data insights* de [BigQuery](#bigquery), la génération de SQL dans les bases et Gemini in Firebase. L'édition Enterprise y ajoute Gemini Cloud Assist dans la console, Apigee et Application Integration.
- **Propriété intellectuelle et gouvernance.** Citation des sources quand une suggestion reprend longuement un code existant, indemnisation contractuelle sur les suggestions, prise en charge de VPC Service Controls, de l'accès privé à Google, des clés CMEK et des journaux d'audit.
- **Facturation** : par utilisateur, mesurée à l'heure, avec un tarif réduit en engagement annuel. L'édition Enterprise coûte environ le double de la Standard.

> [!WARNING]
> Le modèle produit un texte plausible, pas nécessairement exact : la documentation demande de vérifier toute sortie avant de l'utiliser. En mode agent, cette vérification porte aussi sur les commandes que l'agent demande à exécuter.

## À quoi ça sert

- Écrire plus vite le code répétitif : squelettes de fonctions, tests unitaires, conversions de format, appels d'API Google Cloud.
- Comprendre un code inconnu : expliquer une fonction, reconstituer l'intention d'un module, documenter l'existant.
- Rester dans l'IDE pour les questions sur Google Cloud, avec des réponses orientées par la documentation du fournisseur.
- Confier à l'agent une tâche à plusieurs étapes — corriger une série de `TODO`, appliquer un changement transverse — sous contrôle par plan et par autorisation d'outil.
- Aligner les suggestions sur les pratiques d'une organisation grâce à la personnalisation sur dépôts privés, en édition Enterprise.

**À éviter** là où l'exactitude prime sur la vitesse : calculs de sécurité, cryptographie, règles métier réglementaires — la relecture humaine y coûte plus cher que l'écriture. À éviter aussi comme porte d'entrée unique vers les modèles : pour appeler Gemini depuis une application, c'est l'API de [Gemini Enterprise Agent Platform](#gemini-enterprise-agent-platform) qu'il faut, pas une licence de poste. Enfin, l'édition Standard ne personnalise rien : si l'attente est que l'assistant connaisse le code maison, seule l'édition Enterprise y répond.

## Alternatives en logiciel libre

- **Continue** (Apache 2.0) : extension VS Code et JetBrains qui branche complétion et chat sur le modèle de son choix, local ou distant — l'équivalent fonctionnel le plus direct.
- **Tabby** (Apache 2.0) : serveur de complétion auto-hébergé, avec extensions d'IDE ; tout reste sur l'infrastructure de l'organisation.
- **Aider** (Apache 2.0) : assistant en ligne de commande qui édite le dépôt et valide dans Git, proche de l'esprit du mode agent.
- **Cline** et **OpenHands** : agents de codage ouverts, avec outils, plan et exécution de commandes sous validation.
- **Ollama**, **llama.cpp** et **vLLM** : service local ou interne des modèles ouverts que ces clients appellent, pour une chaîne complète sans envoi de code à l'extérieur.
- **Open VSX** : registre libre d'extensions d'IDE, par lequel passent ces greffons dans les éditeurs dérivés de Code OSS.
