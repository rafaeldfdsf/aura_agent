import requests
import sounddevice as sd
import numpy as np
import tempfile
import os
import sqlite3
import re
import queue
import time
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
from gtts import gTTS
from playsound import playsound

# ================= CONFIG =================
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"
SAMPLE_RATE = 16000
RECORD_SECONDS = 5
MAX_TURNS = 6  # 3 perguntas + 3 respostas
DB_FILE = "memory.db"

SYSTEM_PROMPT = (
    "És o Darian, um assistente direto, objetivo e eficiente.\n"
    "Responde sempre em português de Portugal.\n\n"
    "Regras obrigatórias:\n"
    "- Responde de forma curta e direta.\n"
    "- Não expliques raciocínio.\n"
    "- Não acrescentes contexto desnecessário.\n"
    "- Não faças conversa.\n"
    "- Se a pergunta for factual (ex: tempo, horas, datas), responde apenas com o facto.\n"
    "- Usa frases simples e claras.\n"
)

def build_system_prompt():
    prompt = SYSTEM_PROMPT
    facts = load_facts()

    if "name" in facts:
        prompt += f"\nFACTO CONHECIDO:\nO utilizador chama-se {facts['name']}.\n"

    return prompt

# ================ LLM ====================
def call_llm(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["message"]["content"]

# ================ TTS ====================
def speak(text):
    # Força pausas naturais
    text = text.replace(",", ", ").replace(".", ". ")
    
    tts = gTTS(
        text=text,
        lang="pt",
        tld="pt",
        slow=False  # mantém natural mas com pausas
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        path = f.name
        tts.save(path)

    playsound(path)
    os.remove(path)

# ================ STT ====================
whisper = WhisperModel("small", device="cpu", compute_type="int8")

def listen(voice_threshold):
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
        callback=callback
    ):
        audio_chunks = []
        silence_start = None
        start_time = time.time()
        speech_started = False

        while True:
            try:
                chunk = q.get(timeout=0.1)
            except queue.Empty:
                continue

            audio_chunks.append(chunk)

            volume = np.linalg.norm(chunk) * 10

            # ainda ninguém começou a falar
            if not speech_started:
                if volume > voice_threshold:
                    speech_started = True
                    silence_start = None
                else:
                    continue  # ignora ruído antes da fala
            else:
                # já houve fala, agora esperamos silêncio
                if volume > voice_threshold:
                    silence_start = None
                else:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > 0.4:
                        break

            if time.time() - start_time > 15:
                break

    audio = np.concatenate(audio_chunks).squeeze()

    if audio.size == 0:
        print("❌ Não percebi.")
        return None

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
    threshold = noise_level * 1.8  # margem de segurança

    print(f"🔈 Ruído base: {noise_level:.4f}")
    print(f"🎚️ Limiar de voz: {threshold:.4f}")

    return threshold

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_fact(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO user_memory (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def load_facts():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM user_memory")
    facts = dict(c.fetchall())
    conn.close()
    return facts

def extract_user_facts(text):
    text_l = text.lower()

    patterns = [
        r"chamo-me\s+(.+)",
        r"o meu nome é\s+(.+)",
        r"meu nome é\s+(.+)",
        r"eu sou o\s+(.+)",
        r"eu sou a\s+(.+)",
        r"eu sou da\s+(.+)",
        r"eu sou das\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_l)
        if match:
            name = match.group(1)

            # limpa pontuação final
            name = re.sub(r"[^\w\sÀ-ÿ]", "", name)

            # capitaliza corretamente nomes compostos
            name = " ".join(w.capitalize() for w in name.split())

            save_fact("name", name)
            print(f"🧠 Nome guardado: {name}")
            return

# ================ MAIN ===================
def main():
    init_db()
    voice_threshold = calibrate_noise()

    messages = [{"role": "system", "content": build_system_prompt()}]

    print("🟢 Assistente com voz iniciado")
    print("Diz 'sair' para terminar\n")

    while True:
        user = listen(voice_threshold)
        if not user:
            continue

        if user.lower() in {"sair", "exit", "quit"}:
            speak("Até logo!")
            break

        messages.append({"role": "user", "content": user})

        # extrai e guarda factos (ex: nome)
        extract_user_facts(user)

        # atualiza o prompt com memória persistente
        messages[0]["content"] = build_system_prompt()

        try:
            reply = call_llm(messages)
        except Exception as e:
            print(f"❌ Erro LLM: {e}")
            speak("Houve um erro ao contactar o modelo.")
            continue

        messages.append({"role": "assistant", "content": reply})

        # limita histórico
        if len(messages) > 1 + MAX_TURNS * 2:
            messages = messages[:1] + messages[-MAX_TURNS * 2:]

        print(f"\nAssistente: {reply}\n")
        speak(reply)

if __name__ == "__main__":
    main()
