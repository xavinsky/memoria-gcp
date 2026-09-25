---
title: Document AI en Python
---

[Document AI](#document-ai) s'appelle avec `google-cloud-documentai` (module `documentai`, qui pointe sur `documentai_v1`). On n'appelle pas un modèle mais un **processeur** créé à l'avance dans un projet et une *location* (`us` ou `eu` pour la plupart), identifié par `projects/PROJECT_ID/locations/LOCATION/processors/PROCESSOR_ID`. Le client doit viser l'endpoint de cette même *location*. La réponse est toujours un objet `Document` : texte intégral, pages, entités, et coordonnées de chaque élément. Le principal qui appelle a besoin de `roles/documentai.apiUser` ; en lot, le processeur lit et écrit dans Cloud Storage. Les exemples suivent `google-cloud-documentai` 3.15 et `google-cloud-documentai-toolbox` 0.17.

## Choisir le processeur

| Processeur (type dans l'API) | Ce qu'il renvoie | Pages en ligne / en lot | Usage |
|---|---|---|---|
| Enterprise Document OCR (`OCR_PROCESSOR`) | Texte, blocs, lignes, jetons, langues, qualité du scan | 15 / 500 | Numériser, rendre cherchable |
| Form Parser (`FORM_PARSER_PROCESSOR`) | OCR, paires clé/valeur (`form_fields`), cases à cocher, tableaux | 15 / 100 | Formulaires génériques |
| Layout Parser (`LAYOUT_PARSER_PROCESSOR`) | `document_layout` (titres, paragraphes, listes, tableaux) et `chunked_document` | 15 / 500 | Préparer un corpus pour du [RAG](#rag) ; PDF, HTML, DOCX, PPTX, XLSX |
| Custom Extractor (`CUSTOM_EXTRACTION_PROCESSOR`) | `entities` selon un schéma défini par l'utilisateur | 15 / 200 | Champs métier ; génératif (Gemini) ou modèle entraîné |
| Custom Classifier, Custom Splitter | Type de document, découpage d'un lot en documents | 15 / 200, 15 / 1 000 | Trier un flux hétérogène avant extraction |
| Spécialisés : Invoice, Expense, Bank Statement, Pay Slip, W2, pièces d'identité | Entités normalisées (`normalized_value`) | de 2 à 15 / de 2 à 200 | Documents normalisés, sans entraînement |

En ligne, `imageless_mode=True` porte la limite à 30 pages, à condition de traiter les pages à la suite depuis la première. Un fichier en ligne pèse 40 Mo au plus (20 Mo pour le Layout Parser) ; un lot compte 5 000 fichiers et 1 Go par fichier au plus.

**Versions.** Chaque processeur a une version par défaut, et on peut viser une version précise par `.../processors/PROCESSOR_ID/processorVersions/VERSION_ID` (par exemple `pretrained-ocr-v2.1-2024-08-07`). Figer la version en production évite qu'un changement de version par défaut modifie les résultats. `list_processor_versions` et `set_default_processor_version` gèrent ce choix.

## Traitement en ligne

```python
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

LOCATION = "eu"
client = documentai.DocumentProcessorServiceClient(
    client_options=ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com"),
)
nom = client.processor_path("PROJECT_ID", LOCATION, "PROCESSOR_ID")

with open("facture.pdf", "rb") as f:
    brut = documentai.RawDocument(content=f.read(), mime_type="application/pdf")

resultat = client.process_document(
    request=documentai.ProcessRequest(
        name=nom,
        raw_document=brut,          # ou gcs_document=documentai.GcsDocument(gcs_uri="gs://BUCKET/f.pdf", mime_type="application/pdf")
        imageless_mode=True,        # 30 pages au lieu de 15, sans les images des pages dans la réponse
        process_options=documentai.ProcessOptions(from_start=5),   # ou individual_page_selector, from_end
    )
)
doc = resultat.document
```

## Lire l'objet `Document`

Les éléments ne contiennent pas leur texte : ils pointent dans `doc.text` par un `text_anchor`, liste de segments `start_index`/`end_index`. Un élément peut avoir plusieurs segments (une valeur coupée par un saut de ligne), et un `start_index` à zéro est omis dans le JSON.

```python
def texte(ancre: documentai.Document.TextAnchor, doc: documentai.Document) -> str:
    return "".join(doc.text[s.start_index:s.end_index] for s in ancre.text_segments).strip()

for page in doc.pages:
    for champ in page.form_fields:                       # Form Parser
        print(texte(champ.field_name.text_anchor, doc), "=", texte(champ.field_value.text_anchor, doc))
    for tableau in page.tables:
        entete = [texte(c.layout.text_anchor, doc) for c in tableau.header_rows[0].cells]

for e in doc.entities:                                   # Custom Extractor, processeurs spécialisés
    print(e.type_, e.mention_text, e.normalized_value.text, round(e.confidence, 2))
```

| Champ | Contenu |
|---|---|
| `text` | Texte intégral dans l'ordre de lecture |
| `pages[].blocks`, `paragraphs`, `lines`, `tokens` | Mise en page ; `layout.bounding_poly.normalized_vertices` donne les coordonnées de 0 à 1 |
| `pages[].form_fields`, `tables` | Paires clé/valeur, tableaux (`header_rows`, `body_rows`, `cells`) |
| `entities` | Champs typés : `type_`, `mention_text`, `normalized_value`, `confidence`, `properties` (sous-champs), `page_anchor` |
| `document_layout`, `chunked_document` | Structure et fragments du Layout Parser |
| `shard_info`, `error` | Position dans un résultat de lot découpé, erreur de traitement |

## Traitement par lots

```python
operation = client.batch_process_documents(
    request=documentai.BatchProcessRequest(
        name=nom,
        input_documents=documentai.BatchDocumentsInputConfig(
            gcs_prefix=documentai.GcsPrefix(gcs_uri_prefix="gs://BUCKET/entree/"),
        ),
        document_output_config=documentai.DocumentOutputConfig(
            gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                gcs_uri="gs://BUCKET/sortie/",
                field_mask="text,entities,pages.pageNumber",   # n'écrire que ce qui sert
            ),
        ),
    )
)
operation.result(timeout=6 * 3600)
metadata = documentai.BatchProcessMetadata(operation.metadata)
for statut in metadata.individual_process_statuses:
    print(statut.input_gcs_source, statut.status.code, statut.output_gcs_destination)
```

Chaque fichier source produit un dossier `gs://BUCKET/sortie/OPERATION_ID/INDEX/` qui peut contenir **plusieurs JSON** (*shards*), un par tranche de pages ; `sharding_config` en règle la taille. Lire ces fichiers un par un demande de recoller le texte. La bibliothèque **Document AI Toolbox** [!PREVERSION] (`pip install google-cloud-documentai-toolbox`) le fait, et simplifie la lecture :

```python
from google.cloud.documentai_toolbox import document

for d in document.Document.from_batch_process_metadata(metadata):   # shards regroupés
    for page in d.search_pages(pattern=r"Total\s+TTC"):
        for tableau in page.tables:
            df = tableau.to_dataframe()                              # pandas
    d.entities_to_bigquery(dataset_name="DATASET", table_name="entites", project_id="PROJECT_ID")
    fusion = d.to_merged_documentai_document()                       # un seul Document
```

Toolbox charge aussi un résultat par `from_gcs(gcs_bucket_name, gcs_prefix)`, `from_document_path` ou `from_documentai_document`, exporte en hOCR, découpe un PDF d'après la sortie d'un Custom Splitter (`split_pdf`) et convertit vers le format de réponse de Vision AI. Sans code Python, un **modèle distant** [BigQuery](#bigquery) appelle le processeur par `ML.PROCESS_DOCUMENT` sur une table d'objets (voir la fiche [Document AI](#document-ai)).

## Fragments pour le RAG

Le Layout Parser découpe le document en fragments qui respectent les titres et les tableaux ; c'est l'entrée d'un index vectoriel ([RAG](#rag)).

```python
nom_layout = client.processor_path("PROJECT_ID", LOCATION, "LAYOUT_PROCESSOR_ID")
gcs_doc = documentai.GcsDocument(gcs_uri="gs://BUCKET/guide.pdf", mime_type="application/pdf")
options = documentai.ProcessOptions(
    layout_config=documentai.ProcessOptions.LayoutConfig(
        chunking_config=documentai.ProcessOptions.LayoutConfig.ChunkingConfig(
            chunk_size=1024,                 # en jetons
            include_ancestor_headings=True,  # jusqu'à deux niveaux de titres ajoutés au fragment
        ),
    ),
)
resultat = client.process_document(
    request=documentai.ProcessRequest(name=nom_layout, gcs_document=gcs_doc, process_options=options)
)
for fragment in resultat.document.chunked_document.chunks:
    print(fragment.chunk_id, fragment.page_span.page_start, fragment.content[:80])
```

## Document AI ou Gemini

Un appel à Gemini avec le PDF et un schéma JSON ([Appeler Gemini](#appeler-gemini)) suffit pour quelques dizaines de documents, un schéma qui change souvent, ou une question ouverte sur le document ; aucun processeur n'est à créer. Document AI reste le bon choix pour les **coordonnées** de chaque champ (surlignage, contrôle humain), les tableaux et cases à cocher fidèles, des lots de milliers de fichiers à tarif fixe par page, et les processeurs prêts à l'emploi. Le Custom Extractor génératif est lui-même bâti sur Gemini : il en apporte la souplesse dans ce cadre. La frontière générale est dans [Choisir une approche ML](#choisir-une-approche-ml).

## Pièges

- **Endpoint et *location* différents.** Le client vise `us` (`documentai.googleapis.com`) par défaut. Un processeur créé en `eu` s'appelle avec `api_endpoint="eu-documentai.googleapis.com"` ; appelé par l'endpoint par défaut, la requête échoue.
- **Limite de pages dépassée.** 15 pages en ligne pour la plupart des processeurs, parfois 2 ou 10 : au-delà, erreur `INVALID_ARGUMENT`. Passer en lot, activer `imageless_mode`, ou découper le PDF en amont.
- **Coût à la page.** De 1,50 $ (OCR) à 30 $ (Form Parser, Custom Extractor) les 1 000 pages : faire passer tout un fonds par un extracteur alors qu'une page sur dix porte l'information coûte cher. Classer ou sélectionner les pages d'abord (`individual_page_selector`, Custom Classifier). Un processeur personnalisé déployé se facture aussi à l'heure, sans trafic.
- **Résidence non garantie par certaines versions.** Les versions génératives les plus récentes (par exemple `pretrained-layout-parser-v1.6-2026-01-13`) passent par l'endpoint global de Gemini, même appelées en `eu`. Vérifier la version avant de promettre une résidence européenne.
- **Custom Extractor génératif et langue.** Seul l'anglais y est officiellement pris en charge ; tester sur ses propres documents en français avant de s'y fier.
- **Lecture d'un seul JSON de lot.** Un gros document est découpé en plusieurs fichiers : ne lire que le premier donne un texte tronqué, et les `text_anchor` de chaque shard pointent dans son propre `text`. Toolbox ou `shard_info.text_offset` pour recoller.
- **Lot trop long.** Un lot aboutit en général en 12 à 24 heures et est annulé au-delà de 24 heures : ce n'est pas un chemin pour du temps réel. Seules les requêtes terminées sont facturées.

## Alternatives en logiciel libre

Les équivalents libres — Tesseract et OCRmyPDF, PaddleOCR, Docling et unstructured pour le découpage — sont décrits sur la fiche [Document AI](#document-ai).
