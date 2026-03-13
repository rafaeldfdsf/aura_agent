import os
import queue
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from openai import OpenAI

from config import SAMPLE_RATE

# Cria o cliente da OpenAI usando a variável de ambiente OPENAI_API_KEY
client = OpenAI()

# Cria o VAD.
# Níveis possíveis: 0, 1, 2, 3
# 0 = menos agressivo (apanha mais som, mais permissivo)
# 3 = mais agressivo (ignora mais ruído, mais exigente)
vad = webrtcvad.Vad(2)


def calibrate_noise():
    """
    Mantemos esta função só para compatibilidade com o main.py.
    Como agora usamos VAD, já não precisamos de calibrar ruído.
    """
    return 1


def listen(_voice_threshold=None):
    """
    Escuta o microfone até detetar uma frase.
    Usa VAD para perceber quando a fala começa e quando termina.
    Depois envia o áudio para o Whisper da OpenAI e devolve o texto.
    """

    print("🎤 Fala agora...")

    # Fila para receber os blocos de áudio do callback do microfone
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        """
        Esta função é chamada automaticamente pelo sounddevice
        sempre que chega um novo bloco de áudio do microfone.
        """
        if status:
            print(status)
        q.put(indata.copy())

    # 30 ms por frame a 16 kHz = 480 samples
    # O WebRTC VAD aceita frames de 10, 20 ou 30 ms.
    frame_duration_ms = 30
    frame_size = int(SAMPLE_RATE * frame_duration_ms / 1000)  # 480

    # Quantos frames de silêncio vamos aceitar antes de concluir que a pessoa acabou de falar.
    max_silence_frames = 20  # ~600 ms de silêncio

    # Quantos frames de pré-buffer guardamos para não cortar o início da frase.
    pre_buffer_max = 10

    # Aqui vamos acumulando os pequenos blocos imediatamente anteriores
    # ao início da fala, para não perder as primeiras sílabas.
    pre_buffer = []

    # Aqui vamos guardar o áudio final da fala
    recorded_frames = []

    # Estado interno
    speech_started = False
    silence_count = 0

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",      # WebRTC VAD espera áudio PCM 16-bit
        blocksize=frame_size,
        callback=callback
    ):
        while True:
            # Espera pelo próximo frame do microfone
            chunk = q.get()

            # Guarda no pré-buffer enquanto ainda não começou a fala
            if not speech_started:
                pre_buffer.append(chunk)
                if len(pre_buffer) > pre_buffer_max:
                    pre_buffer.pop(0)

            # O VAD recebe bytes crus do áudio
            is_speech = vad.is_speech(chunk.tobytes(), SAMPLE_RATE)

            if not speech_started:
                # Ainda não começámos a gravar a frase
                if is_speech:
                    # Assim que detetamos fala:
                    # 1) mudamos de estado
                    # 2) copiamos o pré-buffer
                    # 3) juntamos o frame atual
                    speech_started = True
                    recorded_frames.extend(pre_buffer)
                    recorded_frames.append(chunk)
                    pre_buffer.clear()
            else:
                # Já começámos a gravar
                recorded_frames.append(chunk)

                if is_speech:
                    # Se ainda há fala, reset ao contador de silêncio
                    silence_count = 0
                else:
                    # Se este frame já não parece fala, conta como silêncio
                    silence_count += 1

                    # Se tivermos silêncio suficiente, terminamos a frase
                    if silence_count >= max_silence_frames:
                        break

    # Se por algum motivo não gravou nada, devolve None
    if not recorded_frames:
        return None

    # Junta todos os frames numa única array
    audio = np.concatenate(recorded_frames, axis=0)

    # Converte para float32 para gravar WAV com soundfile sem problemas
    audio_float = audio.astype(np.float32) / 32768.0

    # Guarda temporariamente o áudio num ficheiro WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        sf.write(temp_path, audio_float, SAMPLE_RATE)

    try:
        # Envia o ficheiro para a API Whisper da OpenAI
        with open(temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt"
            )

        text = transcript.text.strip()

    finally:
        # Apaga o ficheiro temporário
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Se o Whisper não devolveu texto útil, ignora
    if not text:
        return None

    print(f"Tu: {text}")
    return text