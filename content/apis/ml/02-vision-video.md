---
title: Vision et Video Intelligence en Python
---

Deux bibliothèques : `google-cloud-vision` (module `google.cloud.vision`, API v1) pour les images, PDF et TIFF, `google-cloud-videointelligence` (module `google.cloud.videointelligence`, API v1) pour les vidéos. Même principe des deux côtés : une requête porte un média et une **liste de fonctions**, chaque fonction est facturée séparément, et la réponse est un objet d'annotations typé. Les clients s'authentifient par ADC (voir [Authentifier un appel à une API](#authentifier-un-appel)) ; le périmètre des services et leurs tarifs sont dans les fiches [Vision AI](#vision-ai) et [Video Intelligence API](#video-intelligence).

## Vision : fonctions et champs de réponse

| Besoin | `vision.Feature.Type` | Champ de `AnnotateImageResponse` |
|---|---|---|
| Libellés généraux | `LABEL_DETECTION` | `label_annotations` (`description`, `score`, `topicality`) |
| Texte épars (photo, panneau) | `TEXT_DETECTION` | `text_annotations`, `full_text_annotation` |
| Texte dense, manuscrit, PDF/TIFF | `DOCUMENT_TEXT_DETECTION` | `full_text_annotation` : page → bloc → paragraphe → mot → symbole |
| Objets avec boîtes | `OBJECT_LOCALIZATION` | `localized_object_annotations` (sommets normalisés 0-1) |
| Visages (sans identification) | `FACE_DETECTION` | `face_annotations` : boîte, points, vraisemblance des émotions |
| Monuments, logos | `LANDMARK_DETECTION`, `LOGO_DETECTION` | `landmark_annotations`, `logo_annotations` |
| Modération | `SAFE_SEARCH_DETECTION` | `safe_search_annotation` : `adult`, `spoof`, `medical`, `violence`, `racy` |
| Couleurs, recadrage, web | `IMAGE_PROPERTIES`, `CROP_HINTS`, `WEB_DETECTION` | `image_properties_annotation`, `crop_hints_annotation`, `web_detection` |

Les vraisemblances sont un `vision.Likelihood` de `UNKNOWN` à `VERY_LIKELY` : on compare à un seuil (`>= vision.Likelihood.LIKELY`), pas à un pourcentage. `Feature(type_=..., max_results=, model="builtin/latest")` fixe le nombre de résultats et la version du modèle ; `ImageContext(language_hints=["fr"])` oriente l'OCR.

## Vision : modes d'appel

| Besoin | Méthode | Limites | Sortie |
|---|---|---|---|
| Une image, une fonction | `client.label_detection(image=...)`, `text_detection`, `safe_search_detection`… | Image de 20 Mo, requête JSON de 10 Mo | Réponse directe |
| Quelques images, plusieurs fonctions | `client.batch_annotate_images(requests=[AnnotateImageRequest(...)])` | 16 images par requête | `response.responses`, dans l'ordre des requêtes |
| Quelques pages d'un PDF ou TIFF | `client.batch_annotate_files(requests=[AnnotateFileRequest(...)])` | 1 fichier, 5 pages (`pages=[1, 2, 3]`) | Réponse directe |
| Gros lot d'images | `client.async_batch_annotate_images(requests=, output_config=)` | 2 000 images, opération longue | JSON dans Cloud Storage, `batch_size` réponses par fichier |
| PDF ou TIFF complet | `client.async_batch_annotate_files(requests=[AsyncAnnotateFileRequest(...)])` | 2 000 pages, fichier sur Cloud Storage uniquement | JSON dans Cloud Storage |

L'image s'envoie en octets (`vision.Image(content=octets)`, encodée en base64 dans la requête, donc +37 %) ou par référence (`vision.Image(source=vision.ImageSource(image_uri="gs://BUCKET/x.jpg"))`). La référence Cloud Storage évite la limite de 10 Mo et le transfert ; une URL HTTP publique est acceptée mais sans garantie que Google parvienne à la lire.

```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()
fonctions = [
    vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
    vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
]
requetes = [
    vision.AnnotateImageRequest(image=vision.Image(source=vision.ImageSource(image_uri=uri)), features=fonctions)
    for uri in ["gs://BUCKET/photos/1.jpg", "gs://BUCKET/photos/2.jpg"]
]
reponse = client.batch_annotate_images(requests=requetes)
for uri, r in zip([q.image.source.image_uri for q in requetes], reponse.responses):
    if r.error.message:                       # une image en échec ne lève pas d'exception
        print(uri, "erreur :", r.error.message)
        continue
    a_moderer = r.safe_search_annotation.adult >= vision.Likelihood.LIKELY
    print(uri, [l.description for l in r.label_annotations], a_moderer)
```

OCR d'un PDF de Cloud Storage, résultat écrit dans un bucket :

```python
operation = client.async_batch_annotate_files(requests=[
    vision.AsyncAnnotateFileRequest(
        input_config=vision.InputConfig(
            gcs_source=vision.GcsSource(uri="gs://BUCKET/scans/contrat.pdf"), mime_type="application/pdf",
        ),
        features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)],
        output_config=vision.OutputConfig(
            gcs_destination=vision.GcsDestination(uri="gs://BUCKET/ocr/contrat-"), batch_size=20,
        ),
    ),
])
operation.result(timeout=900)  # fichiers contrat-output-1-to-20.json, etc.
```

Chaque JSON produit contient `responses[i].fullTextAnnotation` ; les boîtes y sont en coordonnées normalisées. Pour garder données et traitement en Europe, le client prend `ClientOptions(api_endpoint="eu-vision.googleapis.com")` et la requête `parent="projects/PROJECT_ID/locations/eu"` ; l'équivalent existe pour `us`.

## Video Intelligence

Toute annotation passe par `annotate_video`, qui ouvre une **opération longue**, même pour une vidéo de quelques secondes. La vidéo est lue sur Cloud Storage (`input_uri`, jokers `*` et `?` acceptés) ou envoyée en octets (`input_content`) ; 50 Go et 3 heures au plus, une vidéo par requête.

| Besoin | `videointelligence.Feature` | Réglage dans `VideoContext` | Champ du résultat |
|---|---|---|---|
| Libellés par vidéo, plan ou image | `LABEL_DETECTION` | `label_detection_config` : `label_detection_mode=SHOT_AND_FRAME_MODE`, `stationary_camera` | `segment_label_annotations`, `shot_label_annotations`, `frame_label_annotations` |
| Découpage en plans | `SHOT_CHANGE_DETECTION` | — | `shot_annotations` |
| Contenu explicite | `EXPLICIT_CONTENT_DETECTION` | — | `explicit_annotation.frames[i].pornography_likelihood` |
| Texte à l'écran | `TEXT_DETECTION` | `text_detection_config.language_hints` | `text_annotations` |
| Suivi d'objets | `OBJECT_TRACKING` | — | `object_annotations` (boîte image par image) |
| Personnes, visages | `PERSON_DETECTION`, `FACE_DETECTION` | `include_bounding_boxes`, `include_attributes`, `include_pose_landmarks` | `person_detection_annotations`, `face_detection_annotations` |
| Logos | `LOGO_RECOGNITION` | — | `logo_recognition_annotations` |
| Parole | `SPEECH_TRANSCRIPTION` | `speech_transcription_config` : `language_code="en-US"` obligatoire | `speech_transcriptions` |

```python
from google.cloud import videointelligence as vi

client_video = vi.VideoIntelligenceServiceClient()
operation = client_video.annotate_video(request=vi.AnnotateVideoRequest(
    input_uri="gs://BUCKET/videos/episode-12.mp4",
    features=[vi.Feature.LABEL_DETECTION, vi.Feature.SHOT_CHANGE_DETECTION],
    video_context=vi.VideoContext(
        label_detection_config=vi.LabelDetectionConfig(label_detection_mode=vi.LabelDetectionMode.SHOT_MODE),
    ),
    output_uri="gs://BUCKET/annotations/episode-12.json",  # facultatif : copie JSON du résultat
    location_id="europe-west1",
))
print(operation.operation.name)           # à conserver pour reprendre le suivi
resultat = operation.result(timeout=3600).annotation_results[0]
for label in resultat.segment_label_annotations:
    debut = label.segments[0].segment.start_time_offset
    print(label.entity.description, round(label.segments[0].confidence, 2), debut)
```

`location_id` accepte `us-east1`, `us-west1`, `europe-west1` et `asia-east1` ; sans lui, la région suit l'emplacement du fichier. Pendant le traitement, `operation.metadata.annotation_progress[i].progress_percent` donne l'avancement par fonction. L'annotation d'un direct passe par un service gRPC distinct [!PREVERSION] (module `videointelligence_v1p3beta1`, `StreamingVideoIntelligenceServiceClient`), limité aux libellés, aux plans, au contenu explicite et au suivi d'objets.

## Gemini ou API dédiée ?

Gemini prend images, PDF et vidéos en entrée et répond à une question ouverte, dans le format demandé (voir [Appeler Gemini](#appeler-gemini)). Il remplace ces API dès qu'il faut **interpréter** : décrire une scène, vérifier une règle métier sur une photo, classer selon une taxonomie maison, résumer une vidéo ou retrouver un moment décrit en langage courant. La documentation de Gemini fixe elle-même la limite : localisation imprécise du texte et des objets, comptages approximatifs, hallucinations possibles sur le manuscrit ou les images de mauvaise qualité, vidéo échantillonnée à une image par seconde, 45 minutes environ avec le son. Vision et Video Intelligence restent préférables pour des sorties **géométriques et stables** (boîtes, sommets, horodatage à l'image), un OCR avec coordonnées, une modération à catégories fixes, un tarif à l'unité et des volumes de millions d'images ; pour un document structuré, [Document AI](#document-ai) passe avant les deux. Le cadre général est dans [Choisir une approche ML](#choisir-une-approche-ml).

## Pièges

- **Erreurs silencieuses dans un lot.** `batch_annotate_images` réussit même si une image échoue : l'erreur est dans `responses[i].error`. Même logique pour les lots asynchrones, où les fichiers en échec sont à renvoyer seuls pour ne pas repayer les autres.
- **Image trop lourde en ligne.** Une image de 8 Mo encodée en base64 dépasse la limite de 10 Mo de la requête. Passer par `image_uri` sur Cloud Storage, ou réduire l'image : 640×480 suffit pour les libellés, 1024×768 pour l'OCR, 1600×1200 pour les visages.
- **URL externe en production.** `image_uri` en HTTP dépend de l'hôte distant, qui peut limiter ou bloquer les requêtes de Google. Copier l'image dans un bucket avant l'appel.
- **PDF envoyé en synchrone.** `batch_annotate_files` ne traite que 5 pages ; un PDF plus long passe par `async_batch_annotate_files`, qui n'accepte que Cloud Storage en entrée comme en sortie, et pas de clé API.
- **Quotas à deux étages.** Vision compte les requêtes par minute (1 800) et, séparément, les images ou pages traitées : un lot de 16 images consomme 16 unités de quota de fonction. Côté vidéo, 180 secondes de traitement par minute et par projet, soit environ trois vidéos en parallèle : une file trop longue renvoie `RESOURCE_EXHAUSTED` (voir [Erreurs, quotas et relances](#erreurs-quotas-relances)).
- **`operation.result()` qui expire.** Une vidéo d'une heure demande bien plus que les délais des exemples ; le `TimeoutError` n'annule pas l'opération. Conserver `operation.operation.name` et relire l'opération plus tard, ou lire directement le JSON d'`output_uri`.
- **Transcription vidéo en français.** `SPEECH_TRANSCRIPTION` ne prend que l'anglais (`en-US`). Pour une autre langue, extraire la bande son et la passer à [Speech-to-Text](#speech-to-text-tts).
- **Sortie hors périmètre.** VPC Service Controls n'applique pas ses restrictions de sortie à l'`output_uri` de Video Intelligence : le service peut écrire dans un bucket hors du périmètre. Contrôler la destination dans le code.
- **Fonctions payées en double.** Chaque fonction est facturée sur toute la durée de la vidéo, ou sur chaque page d'un PDF. Restreindre la liste, et découper avec `VideoContext(segments=[...])` quand seule une partie compte.

## Alternatives en logiciel libre

OCR, détection et suivi d'objets, découpage en plans en logiciel libre (Tesseract, PaddleOCR, YOLO, PySceneDetect…) : voir les fiches [Vision AI](#vision-ai) et [Video Intelligence API](#video-intelligence).
