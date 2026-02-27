"""
Speech-to-Text (escuta e transcrição).

Responsabilidades:
- Captar áudio do microfone
- Detetar início e fim da fala
- Filtrar ruído / TV
- Transcrever com Whisper

Este ficheiro concentra TODA a lógica de escuta.
"""

import sounddevice as sd
import numpy as np
import queue
import time
import tempfile
import os
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

from config import SAMPLE_RATE, STOP_TTS
from audio.signals import beep

# Modelo Whisper carregado uma única vez
whisper = WhisperModel("small", device="cpu", compute_type="int8")

def listen(voice_threshold):
    global STOP_TTS

    print("🎤 Fala agora...")

    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        q.put(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=512,
        callback=callback
    ):
        audio_chunks = []
        silence_start = None
        start_time = time.time()
        speech_started = False
        voice_start_time = None

        while True:
            try:
                chunk = q.get(timeout=0.05)
            except queue.Empty:
                continue

            volume = np.linalg.norm(chunk) * 10

            # 🔇 Antes da fala começar
            if not speech_started:
                if volume > voice_threshold:
                    if voice_start_time is None:
                        voice_start_time = time.time()
                    elif time.time() - voice_start_time > 0.2:  # 200 ms contínuos
                        STOP_TTS = True          # 🔴 barge-in
                        speech_started = True
                        silence_start = None
                        beep()                  # 🔔 feedback
                        audio_chunks.append(chunk)
                else:
                    voice_start_time = None
                    continue

            # 🔊 Depois da fala começar
            else:
                audio_chunks.append(chunk)

                if volume > voice_threshold:
                    silence_start = None
                else:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > 0.25:
                        break

            # ⛑️ limite de segurança
            if speech_started and time.time() - start_time > 6:
                break

    if not audio_chunks:
        print("❌ Não percebi.")
        return None

    audio = np.concatenate(audio_chunks).squeeze()

    # normalizar
    audio = audio / np.max(np.abs(audio))
    audio_int16 = np.int16(audio * 32767)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        wav_path = f.name
        write(wav_path, SAMPLE_RATE, audio_int16)

    segments, _ = whisper.transcribe(
        wav_path,
        language="pt",
        beam_size=5,
        vad_filter=True
    )

    os.remove(wav_path)

    text = "".join(seg.text for seg in segments).strip()

    if not text:
        print("❌ Não percebi.")
        return None

    print(f"Tu: {text}")
    return text

def calibrate_noise(duration=1.5):
    """
    Mede o ruído ambiente para definir um limiar de voz dinâmico.

    Deve ser chamado UMA vez no arranque.
    """
    print("🔇 A calibrar ruído ambiente... fica em silêncio")

    samples = []
    start = time.time()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    ) as stream:
        while time.time() - start < duration:
            chunk, _ = stream.read(1024)
            volume = np.linalg.norm(chunk) * 10
            samples.append(volume)

    noise_level = np.mean(samples)
    threshold = noise_level * 1.5  # margem de segurança

    print(f"🔈 Ruído base: {noise_level:.4f}")
    print(f"🎚️ Limiar de voz: {threshold:.4f}")

    return threshold