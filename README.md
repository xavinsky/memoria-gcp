# memoria-gcp

Aide-mémoire Google Cloud pour la data, l'IA et le DevOps : un site statique, en français, qui rassemble des architectures de référence, des syntaxes, un catalogue de produits et un lexique.

| Onglet | Contenu |
|---|---|
| Accueil | Objectif du site (utiliser l'IA avec les produits Google Cloud), plan des onglets, parcours de lecture |
| Architectures Data | Stockage et bases de données, patterns de traitement (batch, streaming, CDC, lakehouse, orchestration, partage) |
| Architectures IA | Machine learning, IA générative (Gemini, RAG, réglage), agents (ADK, MCP, A2A) |
| DevOps | Chaîne CI/CD, dépôts, outils tiers, Infrastructure as Code, poste de développement |
| Plateforme | Fondations, réseau, calcul, IAM et sécurité, exploitation, coûts |
| Syntaxes | `gcloud`, `bq`, `gcloud storage`, GoogleSQL, BigQuery ML, Python |
| APIs & SDK | Bibliothèques clientes Python, APIs de machine learning |
| Produits | Une fiche par service : schéma d'intégration, usages, alternatives libres, documentation |
| Lexique | Termes, sigles et anciens noms des produits |

## Construire le site

```bash
pip install -r requirements.txt
python3 build/build.py      # content/ → www/data/content.js
```

Le build produit aussi, pour le référencement, une page `www/<id>.html` par section et pour le lexique (le site complet ouvert sur cette section, avec ses métadonnées et son contenu en HTML statique) et `www/sitemap.xml`, publié sur https://tekio.org/memoria-gcp/sitemap.xml.

Ouvrir ensuite `www/index.html` dans un navigateur : le site fonctionne sans serveur. Le workflow `.github/workflows/pages.yml` lance le build et publie `www/` sur GitHub Pages à chaque push sur `main`.

| Élément | Rôle |
|---|---|
| `content/` | Contenu en Markdown : `site.yml` (menu), `accueil.md` (page d'accueil), une section par fichier `<onglet>/<groupe>/<NN>-<slug>.md`, `lexique.md`, schémas dans `svg/` |
| `build/build.py`, `build/schema.py` | Compilation du contenu, schémas d'intégration en SVG, vérification des liens internes |
| `www/` | Site statique : `index.html`, `style.css`, `engine.js` |
| `www/icons/` | Icônes officielles Google Cloud |
| `www/captures/` | Captures de la documentation officielle Google Cloud (licence CC BY 4.0), créditées sous chaque image |

## Licence

Code et contenu sous licence MIT (voir [LICENSE](LICENSE)). Les captures et les icônes restent la propriété de Google et sont reprises selon leurs conditions d'utilisation.
