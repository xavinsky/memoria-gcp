---
title: Text-to-Speech
subgroup: APIs ML
icon: categories/ai-machine-learning
schema:
  size: [760, 300]
  zones:
    - {label: Projet GCP, x: 170, y: 16, w: 470, h: 268}
  nodes:
    cms: {label: Rédaction, sub: "articles, scripts", external: true, x: 8, y: 128, w: 146}
    run: {label: Cloud Run, sub: "service de synthèse", icon: produits/cloud-run, x: 196, y: 128, w: 196}
    tts: {label: Text-to-Speech, sub: "Chirp 3 HD, SSML", icon: categories/ai-machine-learning, focus: true, x: 440, y: 36, w: 190, h: 66}
    fs: {label: Firestore, sub: "état des synthèses", icon: categories/databases, x: 196, y: 216, w: 196}
    gcs: {label: Cloud Storage, sub: "MP3, LINEAR16", icon: produits/cloud-storage, x: 440, y: 216, w: 190}
    app: {label: Auditeurs, sub: "lecteur web", external: true, x: 660, y: 216, w: 96}
  flows:
    - {from: cms, to: run, text: "Le texte à vocaliser est envoyé au service, en clair ou en SSML"}
    - {from: run, to: tts, offset: -14, text: "synthesize renvoie l'audio encodé en base64 pour un texte de 5 000 octets au plus"}
    - {from: run, to: tts, offset: 14, text: "synthesizeLongAudio ouvre une opération longue pour un texte allant jusqu'à 1 Mo"}
    - {from: tts, to: gcs, text: "L'opération longue écrit le fichier audio à l'adresse donnée par output_gcs_uri"}
    - {from: run, to: fs, text: "Le service suit l'état de chaque synthèse et l'adresse du fichier produit"}
    - {from: gcs, to: app, text: "Le fichier est servi aux auditeurs par une URL signée"}
docs:
  Page produit: https://cloud.google.com/text-to-speech
  Documentation: https://docs.cloud.google.com/text-to-speech/docs
  API REST: https://docs.cloud.google.com/text-to-speech/docs/reference/rest
  Bibliothèques clientes: https://docs.cloud.google.com/text-to-speech/docs/libraries
  Client Python: https://docs.cloud.google.com/python/docs/reference/texttospeech/latest
  Voix et langues: https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types
  Référence SSML: https://docs.cloud.google.com/text-to-speech/docs/ssml
  Modèles Gemini-TTS: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
  Synthèse de textes longs: https://docs.cloud.google.com/text-to-speech/docs/create-audio-text-long-audio-synthesis
  Quotas et limites: https://docs.cloud.google.com/text-to-speech/quotas
  Tarifs: https://cloud.google.com/text-to-speech/pricing
  Notes de version: https://docs.cloud.google.com/text-to-speech/docs/release-notes
---

## Ce que c'est

API de **synthèse vocale** : on envoie du texte et le choix d'une voix, le service renvoie un fichier audio. Aucun modèle à héberger, appel en REST ou par bibliothèque cliente.

- **Familles de voix.** *Chirp 3: HD* pour le conversationnel, avec contrôles audio avancés et diffusion du texte en flux ; *Studio* pour la narration ; *Neural2*, *WaveNet* et *Standard*, plus anciennes et moins chères. Les modèles *Gemini-TTS* s'appellent par la même API et se pilotent par une consigne en langage naturel plutôt que par des balises.
- **Entrée** : texte brut ou **SSML** (pauses, prononciation, emphase, épellation). Chirp 3 et Gemini-TTS ne prennent que du texte ; le contrôle du style, de l'accent et du débit passe par une consigne, dans la limite de 8 192 jetons en entrée, avec la possibilité de faire dialoguer plusieurs voix.
- **Trois modes.** *Synchrone* (`text:synthesize`), limité à **5 000 octets** par requête, réponse audio en base64. *Textes longs* (`synthesizeLongAudio`), jusqu'à **1 Mo** de texte : opération longue dont la sortie est écrite directement dans un bucket Cloud Storage. *Flux bidirectionnel*, pour vocaliser au fil de l'eau la sortie d'un modèle de langue.
- **Sorties** : LINEAR16, MP3, OGG Opus, MULAW et ALAW, avec choix du taux d'échantillonnage, de la vitesse, de la hauteur et du gain.
- **Voix personnalisées** : clonage instantané à partir d'un court enregistrement de référence, et voix sur mesure entraînées sur un corpus dédié.
- **Facturation au caractère envoyé**, espaces et balises SSML compris, par palier mensuel gratuit puis par million de caractères : 30 $ pour Chirp 3: HD, 16 $ pour Neural2, 4 $ pour Standard et WaveNet. Les modèles Gemini-TTS sont facturés en jetons d'entrée et de sortie.

> [!WARNING]
> La limite de 5 000 **octets** n'est pas une limite de 5 000 caractères : un texte accentué, et plus encore un texte en japonais ou en arabe, atteint le plafond bien avant. Découper sur les phrases, ou passer par la synthèse de textes longs.

## À quoi ça sert

- Donner une version audio d'un contenu écrit : articles, documentation, notifications.
- Serveurs vocaux et centres de contacts : messages d'accueil, réponses dynamiques, voix d'un agent conversationnel.
- Doublage d'une vidéo, en chaînant [Speech-to-Text](#speech-to-text), [Translation AI](#translation-ai) puis la synthèse.
- Accessibilité : lecture à voix haute dans une application web ou mobile.

**À éviter** quand la voix doit porter un jeu d'acteur précis, des émotions dirigées ou un dialogue à plusieurs personnages : les modèles Gemini-TTS, appelés par cette même API ou dans un modèle multimodal, se pilotent par consigne et couvrent ces cas. À l'inverse, l'API reste préférable pour du volume à coût prévisible, pour une voix rigoureusement stable d'un appel à l'autre, pour un contrôle fin de la prononciation en SSML, et pour la latence d'un serveur vocal.

## Alternatives en logiciel libre

- **Piper** (licence GPL v3) : synthèse neuronale rapide sur processeur, nombreuses voix ; le choix courant pour l'embarqué et l'auto-hébergement.
- [!SOMMEIL] **Coqui TTS** (MPL 2.0) : boîte à outils complète, entraînement et clonage de voix ; vérifier la licence de chaque modèle préentraîné, certaines sont restreintes.
- **eSpeak NG** (GPL) : synthèse par formants, minuscule et très rapide, sans réalisme.
- **Kokoro** (Apache 2.0) : modèle récent à la qualité proche des voix commerciales.
- **Festival** et **MaryTTS** : moteurs historiques, encore utilisés pour leur contrôle phonétique fin.
