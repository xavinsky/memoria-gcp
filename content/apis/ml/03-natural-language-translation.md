---
title: Natural Language et Translation en Python
---

Deux API de traitement du texte, chacune avec sa bibliothèque : `google-cloud-language` pour [Natural Language AI](#natural-language-ai) et `google-cloud-translate` pour [Translation AI](#translation-ai). Les deux publient plusieurs versions d'API dans le même paquet, et le module importé par défaut n'est pas toujours celui qu'on croit : `from google.cloud import language` donne la **v1**, `from google.cloud import translate` donne la **v3**. Importer le module versionné (`language_v2`, `translate_v3`) lève l'ambiguïté. Les clients s'authentifient par ADC (voir [Authentifier un appel](#authentifier-un-appel)) ; le principal a besoin de `roles/cloudtranslate.user` pour Translation. Les exemples suivent `google-cloud-language` 2.21 et `google-cloud-translate` 3.27.

## Natural Language : v1 ou v2

| Fonction | Méthode Python | v2 | v1 | Remarque |
|---|---|---|---|---|
| Sentiment du document et des phrases | `analyze_sentiment` | oui | oui | `score` de −1 à 1, `magnitude` de 0 à l'infini |
| Entités nommées | `analyze_entities` | oui | oui | v2 : `probability` par mention, sans `salience` ni lien Wikipédia |
| Classification | `classify_text` | oui | oui | Taxonomie de 1 091 catégories ; en v1, `classification_model_options` choisit le modèle |
| Modération | `moderate_text` | oui | oui | 16 catégories ; `model_version=MODEL_VERSION_2` ajoute la `severity` |
| Plusieurs fonctions en un appel | `annotate_text` | oui | oui | Facturé comme la somme des fonctions demandées |
| Sentiment par entité | `analyze_entity_sentiment` | — | oui | |
| Syntaxe (jetons, nature, dépendances) | `analyze_syntax` | — | oui | |

La v2 [!PREVERSION] s'appuie sur des modèles plus récents pour le sentiment et les entités, et chaque réponse porte `language_code` et `language_supported` : une langue non prise en charge officiellement est traitée au mieux au lieu d'échouer. Seule la v1 fournit la syntaxe et le sentiment par entité. Rien n'empêche de mêler les deux modules dans un même programme.

```python
from google.cloud import language_v2

client = language_v2.LanguageServiceClient()   # ou client_options={"api_endpoint": "eu-language.googleapis.com"}

doc = language_v2.Document(
    content="Livraison rapide, mais le colis est arrivé abîmé.",
    type_=language_v2.Document.Type.PLAIN_TEXT,    # ou HTML ; gcs_content_uri="gs://BUCKET/avis.txt" à la place de content
    language_code="fr",                            # facultatif : détectée sinon
)
sentiment = client.analyze_sentiment(document=doc, encoding_type=language_v2.EncodingType.UTF32)
print(sentiment.document_sentiment.score, sentiment.language_supported)
for phrase in sentiment.sentences:
    print(phrase.text.begin_offset, phrase.sentiment.score, phrase.text.content)

entites = client.analyze_entities(document=doc, encoding_type=language_v2.EncodingType.UTF32)
for e in entites.entities:
    print(e.name, e.type_.name, [m.probability for m in e.mentions])

moderation = client.moderate_text(
    document=doc, model_version=language_v2.ModerateTextRequest.ModelVersion.MODEL_VERSION_2,
)
print({c.name: (round(c.confidence, 2), round(c.severity, 2)) for c in moderation.moderation_categories})
```

- **`encoding_type`** fixe l'unité des positions (`begin_offset`) renvoyées. Sans lui, elles valent −1. En Python, `UTF32` donne des positions en points de code, directement utilisables pour découper une `str` ; `UTF8` compte des octets.
- **Limites par requête** : 1 000 000 d'octets de texte (au-delà, erreur), 100 000 jetons analysés (le surplus est ignoré sans erreur), 5 000 mentions d'entités. Quotas : 600 requêtes par minute, 800 000 par jour.
- **Facturation** par unité de 1 000 caractères Unicode, arrondie au supérieur à chaque requête, espaces et balises HTML compris ; par unité de 100 caractères pour la modération. Envoyer 800 caractères coûte une unité, 1 500 en coûtent deux : regrouper des textes très courts dans un document réduit la facture, au prix du détail par texte. Les prix sont sur la fiche [Natural Language AI](#natural-language-ai).
- **Résidence** : l'endpoint par défaut, `language.googleapis.com`, est global ; `eu-language.googleapis.com` et `us-language.googleapis.com` gardent le traitement dans l'Union européenne ou aux États-Unis.

## Translation : l'API v3

Tout appel passe par un `parent` de la forme `projects/PROJECT_ID/locations/LOCATION`. La *location* n'est pas un détail : elle détermine les ressources accessibles.

| Besoin | Méthode | `location` | Modèle ou option |
|---|---|---|---|
| Texte court, faible latence | `translate_text` | `global` | `general/nmt`, par défaut |
| Meilleure qualité, contexte sur plusieurs phrases | `translate_text` | une région (`us-central1` dans la documentation) | `model=".../models/general/translation-llm"` |
| Terminologie imposée | `translate_text` avec `glossary_config` | `us-central1`, celle du glossaire | NMT, Translation LLM ou modèle personnalisé |
| Style calqué sur des exemples | `adaptive_mt_translate` | une région | Jusqu'à 5 paires dans la requête, ou un jeu de données de 5 à 30 000 paires |
| Modèle entraîné sur ses paires | `translate_text` | celle du modèle | `.../models/MODEL_ID` |
| Fichiers dans Cloud Storage | `batch_translate_text`, `batch_translate_document` | `us-central1` | Opération longue ; `models=` et `glossaries=` par langue cible |
| Document bureautique en ligne | `translate_document` | `global` ou région | PDF de 20 Mo, 20 pages scannées ou 300 natives |
| Détecter la langue | `detect_language` | `global` | `languages[0].language_code`, `confidence` |

```python
from google.cloud import translate_v3

client = translate_v3.TranslationServiceClient()

reponse = client.translate_text(
    parent="projects/PROJECT_ID/locations/global",
    contents=["<p>Votre commande est <b>expédiée</b>.</p>", "<p>Merci !</p>"],
    mime_type="text/html",                  # valeur par défaut ; "text/plain" pour du texte brut
    source_language_code="fr",               # facultatif : détectée sinon
    target_language_code="de",
)
for t in reponse.translations:
    print(t.translated_text, t.detected_language_code)
```

Glossaire et Translation LLM, dans la région du glossaire :

```python
region = "projects/PROJECT_ID/locations/us-central1"
reponse = client.translate_text(
    request={
        "parent": region,
        "contents": ["Le module Facturation Pro est disponible dans la console."],
        "source_language_code": "fr",
        "target_language_code": "en",
        "model": f"{region}/models/general/translation-llm",
        "glossary_config": translate_v3.TranslateTextGlossaryConfig(
            glossary=f"{region}/glossaries/GLOSSARY_ID",
            contextual_translation_enabled=True,
        ),
    }
)
print(reponse.glossary_translations[0].translated_text)
```

Un glossaire se crée par `create_glossary` (opération longue) à partir d'un fichier CSV, TSV ou TMX dans Cloud Storage, sans ligne d'en-tête, de 10 Mo au plus. Traduction par lots d'un dossier de fichiers :

```python
operation = client.batch_translate_text(
    request={
        "parent": region,
        "source_language_code": "fr",
        "target_language_codes": ["en", "es"],
        "input_configs": [{"gcs_source": {"input_uri": "gs://BUCKET/entree/*"}, "mime_type": "text/plain"}],
        "output_config": {"gcs_destination": {"output_uri_prefix": "gs://BUCKET_SORTIE/lot-01/"}},
    }
)
resultat = operation.result(timeout=3600)
print(resultat.translated_characters, resultat.failed_characters)
```

Le compte appelant doit lire le bucket source et écrire dans le bucket de destination, et le préfixe de sortie doit être **vide** au lancement. Le service y tient à jour un `index.csv` qui donne, pour chaque fichier et chaque langue cible, le fichier traduit et le fichier d'erreurs : c'est lui qu'on lit pour retrouver les résultats. Un fichier TSV est traduit ligne à ligne (10 000 points de code par ligne au plus), un fichier texte ou HTML d'un seul bloc.

La v2, dite *Basic* (`translate_v2.Client`), ne connaît ni glossaire, ni document, ni lots, ni modèle personnalisé : tout code neuf part de la v3. Pour la résidence, les endpoints multirégionaux `translate-eu.googleapis.com` et `translate-us.googleapis.com` se passent en `client_options` ; ils n'acceptent que le modèle NMT préentraîné, et les ressources créées par un endpoint ne sont pas visibles de l'autre.

## API dédiée ou Gemini

La frontière est tracée dans [Choisir une approche ML](#choisir-une-approche-ml) et dans la section « À éviter » de chaque fiche.

- **Natural Language** gagne pour un grand volume de textes courts, facturés à l'unité de 1 000 caractères, et pour une note de sentiment ou une taxonomie qui doivent rester comparables dans le temps. **Gemini** ([Appeler Gemini](#appeler-gemini)) gagne dès qu'il faut une catégorie maison, un champ hors des types d'entités, une explication, ou une sortie au schéma libre.
- **Translation** : le Translation LLM est lui-même un modèle Gemini spécialisé dans la traduction. L'API reste le bon choix pour la traduction pure : glossaire, format de document conservé, lots depuis Cloud Storage, coût au caractère prévisible. **Gemini** gagne quand la traduction se mêle à une autre tâche : résumer dans une autre langue, réécrire selon une consigne de ton, adapter plutôt que traduire.

## Pièges

- **Mauvaise version importée.** `from google.cloud import language` donne la v1, pas la v2. Les champs diffèrent (`language` en v1, `language_code` en v2) : un code écrit pour l'une échoue en silence ou à l'exécution sur l'autre.
- **Positions à −1 ou décalées.** Sans `encoding_type`, pas de positions ; avec `UTF8`, des positions en octets qui ne tombent plus juste sur une `str` dès qu'un accent apparaît. En Python, `UTF32`.
- **`classify_text` sur un texte court.** La fonction attend au moins 20 mots : elle n'est pas faite pour un titre, une étiquette ou un message bref.
- **Glossaire introuvable.** Un glossaire vit dans `us-central1` et ne s'utilise qu'avec un `parent` dans cette même région. Une requête en `global` qui le cite échoue.
- **Réponse vide avec un glossaire contextuel.** Avec `contextual_translation_enabled=True`, la traduction est dans `glossary_translations` et `translations` est vide.
- **Requête trop longue.** 30 000 points de code par requête en v3 (erreur 400 au-delà), 5 000 recommandés pour la latence. Découper le texte côté client, par paragraphes plutôt qu'au caractère près. Le quota est de 6 000 requêtes par minute en v3, 900 pour le Translation LLM.
- **Texte brut lu comme du HTML.** Sans `mime_type`, `translate_text` suppose `text/html` : les sauts de ligne sont perdus et un `<` ou un `&` du texte est interprété comme du balisage. Passer `mime_type="text/plain"` pour du texte brut. Le XML et les autres balisages ne sont pas pris en charge : le résultat est indéfini.
- **Traduction adaptative en parallèle.** `adaptive_mt_translate` est limitée à une requête par seconde et par projet : ce n'est pas un chemin pour le volume.
- **Lot mal placé.** `batch_translate_text` et `batch_translate_document` refusent la *location* `global` : le `parent` est `us-central1`. Le préfixe de sortie doit être vide, et un lot annulé laisse dans la destination les fichiers déjà traduits.

## Alternatives en logiciel libre

Les équivalents libres — spaCy et Stanza pour l'analyse de texte, OPUS-MT, Argos Translate et LibreTranslate pour la traduction — sont décrits sur les fiches [Natural Language AI](#natural-language-ai) et [Translation AI](#translation-ai).
