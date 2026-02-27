"""
Text-to-Speech (fala do assistente).

Responsabilidade:
- Converter texto em áudio
- Reproduzir o áudio

Nota:
- Usa gTTS (MP3)
- Não tenta reconhecimento nem interrupção aqui
"""

import tempfile
import os
from gtts import gTTS
from playsound import playsound
from config import STOP_TTS

def speak(text):
    """
    Converte texto em fala e reproduz.

    :param text: texto a ser falado
    """
    # Pequenas pausas naturais
    text = text.replace(",", ", ").replace(".", ". ")

    tts = gTTS(text=text, lang="pt", tld="pt", slow=False)

    # Ficheiro temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        path = f.name
        tts.save(path)

    playsound(path)
    os.remove(path)