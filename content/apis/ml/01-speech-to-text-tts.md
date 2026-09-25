---
title: Speech-to-Text et Text-to-Speech en Python
---

Deux bibliothèques distinctes : `google-cloud-speech` pour la transcription et `google-cloud-texttospeech` pour la synthèse. Pour la transcription, tout code neuf passe par l'**API v2** (module `google.cloud.speech_v2`) : c'est la seule qui expose les *recognizers*, la transcription par lots vers Cloud Storage et le modèle `chirp_3`. Le module `google.cloud.speech` sans suffixe appelle l'API v1. Les deux clients s'authentifient par ADC (voir [Authentifier un appel à une API](#authentifier-un-appel)) ; ce que font les services et leurs tarifs sont dans les fiches [Speech-to-Text](#speech-to-text) et [Text-to-Speech](#text-to-speech).

## Speech-to-Text : client, région et recognizer

Chaque requête v2 désigne un *recognizer* : `projects/PROJECT_ID/locations/LOCATION/recognizers/ID`. L'identifiant `_` désigne le recognizer implicite, sans ressource à créer : la configuration complète voyage alors dans chaque requête. La région du recognizer et celle de l'endpoint du client doivent concorder.

```python
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

REGION = "eu"  # chirp_3 : "eu" ou "us"
client = SpeechClient(client_options=ClientOptions(api_endpoint=f"{REGION}-speech.googleapis.com"))
RECOGNIZER = f"projects/PROJECT_ID/locations/{REGION}/recognizers/_"

config = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),  # WAV, FLAC, MP3, OGG/WebM Opus, AAC…
    language_codes=["fr-FR"],                                       # ou ["auto"] avec chirp_3
    model="chirp_3",
    features=cloud_speech.RecognitionFeatures(enable_automatic_punctuation=True),
)
```

| Modèle | Emplacements | Pour quoi |
|---|---|---|
| `chirp_3` | `us`, `eu` | Modèle par défaut : multilingue, détection de langue (`["auto"]`), diarisation, débruitage (`denoiser_config`), consigne de mise en forme (`custom_prompt_config`) [!PREVERSION] |
| `chirp_2` | Régions (`europe-west4`, `us-central1`, `asia-southeast1`) | Langues absentes de `chirp_3`, traduction de la parole |
| `telephony`, `telephony_short` | `global`, `us`, `eu` | Audio téléphonique à 8 kHz |

La liste à jour des langues et des fonctions par modèle et par emplacement se lit dans le tableau des [langues prises en charge](https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages), ou par `client.list_locations`. Un recognizer nommé (`client.create_recognizer(parent=, recognizer_id=, recognizer=)`, opération longue) fige modèle, langues et options par défaut : utile quand plusieurs services partagent la même configuration.

## Speech-to-Text : trois modes d'appel

| Besoin | Méthode | Limites | Résultat |
|---|---|---|---|
| Extrait court, réponse immédiate | `client.recognize(request=RecognizeRequest(...))`, audio en `content=` ou `uri=` | 1 minute et 10 Mo | `response.results` |
| Fichier long | `client.batch_recognize(...)` : opération longue | Audio sur Cloud Storage uniquement ; 8 h par fichier (1 h pour `chirp_3`, 20 min avec horodatage au mot) ; 5 fichiers par requête | En ligne (un seul fichier) ou JSON dans un bucket |
| Direct (micro, téléphonie) | `client.streaming_recognize(requests=générateur)` | 5 minutes par flux, 25 Ko d'audio par message, envoi au rythme du temps réel | Itérateur de réponses, résultats intermédiaires possibles |
| Coût réduit, délai accepté | `batch_recognize(..., processing_strategy=DYNAMIC_BATCHING)` | Lots uniquement | Facturé 0,003 $ la minute au lieu de 0,016 $ |

Transcription par lots avec diarisation, résultat écrit dans Cloud Storage :

```python
config_lot = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    language_codes=["fr-FR"],
    model="chirp_3",
    features=cloud_speech.RecognitionFeatures(
        diarization_config=cloud_speech.SpeakerDiarizationConfig(min_speaker_count=2, max_speaker_count=4),
    ),
)
operation = client.batch_recognize(request=cloud_speech.BatchRecognizeRequest(
    recognizer=RECOGNIZER,
    config=config_lot,
    files=[cloud_speech.BatchRecognizeFileMetadata(uri="gs://BUCKET/appels/a-001.flac")],
    recognition_output_config=cloud_speech.RecognitionOutputConfig(
        gcs_output_config=cloud_speech.GcsOutputConfig(uri="gs://BUCKET/transcriptions/"),
    ),
))
response = operation.result(timeout=3600)
for uri, resultat in response.results.items():
    print(uri, resultat.error.message or resultat.cloud_storage_result.uri)
```

Le fichier de sortie se relit avec `cloud_speech.BatchRecognizeResults.from_json(contenu, ignore_unknown_fields=True)` ; chaque `alternatives[0].words[i]` porte `speaker_label` avec la diarisation, `start_offset` et `end_offset` avec `enable_word_time_offsets`. L'échec d'un fichier ne fait pas échouer l'opération : il est dans `resultat.error`.

Reconnaissance en flux : le premier message porte la configuration, les suivants l'audio.

```python
def requetes(morceaux):
    yield cloud_speech.StreamingRecognizeRequest(
        recognizer=RECOGNIZER,
        streaming_config=cloud_speech.StreamingRecognitionConfig(
            config=cloud_speech.RecognitionConfig(
                explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                    encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000, audio_channel_count=1,
                ),
                language_codes=["fr-FR"], model="chirp_3",
            ),
            streaming_features=cloud_speech.StreamingRecognitionFeatures(interim_results=True),
        ),
    )
    for morceau in morceaux:  # blocs PCM de 100 ms environ, jamais plus de 25 Ko
        yield cloud_speech.StreamingRecognizeRequest(audio=morceau)

for reponse in client.streaming_recognize(requests=requetes(lire_micro())):
    for r in reponse.results:
        print("final" if r.is_final else "provisoire", r.alternatives[0].transcript)
```

Les options se posent dans `RecognitionFeatures` : `enable_word_time_offsets`, `enable_word_confidence`, `enable_automatic_punctuation`, `profanity_filter`, `max_alternatives`, `diarization_config` ; le vocabulaire métier passe par `adaptation=SpeechAdaptation(phrase_sets=[...])` (1 000 expressions au plus avec `chirp_3`). Avec `chirp_3`, la diarisation n'est proposée que dans une quinzaine de langues (français compris) ; l'horodatage au mot figure parmi les fonctions non garanties : activable en `recognize` et en lots, avec une perte de précision annoncée et des lots limités à 20 minutes.

## Text-to-Speech

```python
from google.cloud import texttospeech as tts

client_tts = tts.TextToSpeechClient()
for voix in client_tts.list_voices(language_code="fr-FR").voices:
    print(voix.name, voix.natural_sample_rate_hertz)

reponse = client_tts.synthesize_speech(
    input=tts.SynthesisInput(text="Votre commande est prête."),
    voice=tts.VoiceSelectionParams(language_code="fr-FR", name="fr-FR-Chirp3-HD-Charon"),
    audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.OGG_OPUS),
)
open("message.ogg", "wb").write(reponse.audio_content)
```

| Famille | Nom de voix | Entrée | Réglages |
|---|---|---|---|
| *Chirp 3: HD* | `fr-FR-Chirp3-HD-Charon` (30 styles nommés) | Texte ; SSML partiel, synchrone seulement [!PREVERSION] | Pas de `pitch` ; flux possible ; `speaking_rate` [!PREVERSION] |
| *Gemini-TTS* | `name="Charon"` avec `model_name="gemini-2.5-flash-tts"` | Texte et consigne de style (`SynthesisInput(text=, prompt=)`), 4 000 octets chacun | Style, débit et émotion par la consigne ; dialogue à plusieurs voix |
| *Studio* | `fr-FR-Studio-A` | SSML sauf `<mark>`, `<emphasis>`, `<prosody pitch>`, `<lang>` | Narration |
| *Neural2*, *WaveNet*, *Standard* | `fr-FR-Neural2-F`, `fr-FR-Wavenet-F`, `fr-FR-Standard-F` | SSML complet | `speaking_rate`, `pitch`, `volume_gain_db`, `effects_profile_id` |

Pour garder les données en Europe ou aux États-Unis, le client prend `ClientOptions(api_endpoint="eu-texttospeech.googleapis.com")` ; ces endpoints servent Chirp 3: HD et Gemini-TTS, pas toutes les familles. La tarification suit la famille : au caractère, de 4 $ (Standard) à 160 $ (Studio) le million, 30 $ pour Chirp 3: HD ; aux jetons pour Gemini-TTS.

| Besoin | Méthode | Limite |
|---|---|---|
| Phrase ou paragraphe | `synthesize_speech(input=, voice=, audio_config=)` | 5 000 octets par requête |
| Vocaliser un texte produit au fil de l'eau (sortie d'un LLM) | `streaming_synthesize(requests=générateur)` : premier message `StreamingSynthesizeConfig`, puis `StreamingSynthesisInput(text=...)` | Chirp 3: HD et Gemini-TTS ; sortie PCM, OGG Opus, MULAW ou ALAW |
| [!PREVERSION] Livre, long article | `TextToSpeechLongAudioSynthesizeClient().synthesize_long_audio(...)` : opération longue, fichier écrit dans Cloud Storage | 1 Mo de texte |

```python
lot = tts.TextToSpeechLongAudioSynthesizeClient().synthesize_long_audio(
    request=tts.SynthesizeLongAudioRequest(
        parent="projects/PROJECT_ID/locations/global",
        input=tts.SynthesisInput(text=texte_long),
        voice=tts.VoiceSelectionParams(language_code="fr-FR", name="fr-FR-Standard-F"),
        audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16),
        output_gcs_uri="gs://BUCKET/audio/chapitre-01.wav",
    ),
)
lot.result(timeout=1800)
```

## Gemini ou API dédiée ?

Gemini prend l'audio en entrée (jusqu'à 8,4 h environ, un fichier par *prompt*) et répond à une consigne : c'est le bon choix pour **comprendre** un enregistrement — résumer une réunion, extraire des champs d'un appel, répondre à une question, traduire et reformuler en un seul appel (voir [Appeler Gemini](#appeler-gemini)). Speech-to-Text reste le bon choix pour une transcription **verbatim** et exploitable par programme : horodatage au mot, locuteurs étiquetés, flux temps réel, audio téléphonique, adaptation au vocabulaire, facturation à la minute et lots massifs. Côté synthèse, Gemini-TTS passe par la même API Text-to-Speech : on le choisit pour une voix dirigée par consigne ou un dialogue à plusieurs voix, Chirp 3: HD pour une voix stable et une latence faible. Le cadre général est dans [Choisir une approche ML](#choisir-une-approche-ml).

## Pièges

- **Encodage mal déclaré.** `auto_decoding_config` ne lit que les formats à conteneur (WAV, FLAC, MP3, Ogg, WebM, MP4). Du PCM brut, typique d'un flux micro, exige `explicit_decoding_config` avec `sample_rate_hertz` et `audio_channel_count`, sans quoi la transcription est vide ou incohérente. 16 kHz est le taux recommandé ; ne pas rééchantillonner un audio téléphonique à 8 kHz, choisir `telephony`.
- **Modèle absent de la région.** Le tableau des langues ne sert `chirp_3` qu'en `us` et `eu`, même si quelques exemples de la documentation l'appellent sur `global` : vérifier par `list_locations` avant de fixer l'emplacement. L'endpoint (`eu-speech.googleapis.com`) et l'emplacement du recognizer doivent être le même.
- **Audio long envoyé en synchrone.** `recognize` refuse au-delà d'une minute. Au-delà, déposer le fichier dans Cloud Storage et passer par `batch_recognize` ; un flux qui dépasse 5 minutes doit être rouvert par l'application.
- **Bucket d'un autre projet.** La lecture des fichiers d'un lot se fait sous l'identité de l'agent de service `service-PROJECT_NUMBER@gcp-sa-speech.iam.gserviceaccount.com`, qui n'a accès par défaut qu'aux buckets de son projet.
- **`operation.result()` trop court.** Les exemples de la documentation attendent 120 secondes ; une heure d'audio prend plus. Donner un délai réaliste, ou conserver `operation.operation.name` et interroger plus tard.
- **5 000 octets, pas 5 000 caractères.** Un texte accentué atteint la limite de `synthesize_speech` avant 5 000 caractères. Découper sur les phrases, en mesurant `len(texte.encode("utf-8"))`.
- **Voix substituée en silence.** Sans `name`, le service choisit une voix et peut changer de variante régionale, voire de genre. En production, toujours nommer la voix.
- **En-tête WAV en double.** `LINEAR16` renvoie un fichier WAV complet ; pour concaténer des morceaux ou alimenter un lecteur temps réel, demander `PCM`, sans en-tête.
- **SSML ignoré.** Avec Chirp 3: HD, les balises hors de la liste prise en charge sont ignorées sans erreur, et le SSML ne passe pas en flux. Vérifier le rendu à l'écoute avant de conclure qu'une balise agit.

## Alternatives en logiciel libre

Transcription et synthèse libres (Whisper, faster-whisper, pyannote.audio, Piper, Kokoro…) : voir les fiches [Speech-to-Text](#speech-to-text) et [Text-to-Speech](#text-to-speech).
