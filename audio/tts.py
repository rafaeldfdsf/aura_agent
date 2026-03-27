"""
Text-to-Speech (fala do assistente).

Responsabilidade:
- Converter texto em áudio
- Reproduzir o áudio

Nota:
- Usa Cloud Text-to-Speech API da google
"""

from google.cloud import texttospeech
import base64

client = texttospeech.TextToSpeechClient()

def synthesize_speech(text: str):
    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="pt-PT",
        name="pt-PT-Wavenet-D",
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    # devolver em base64 (mais fácil para Flutter)
    audio_base64 = base64.b64encode(response.audio_content).decode("utf-8")

    return audio_base64