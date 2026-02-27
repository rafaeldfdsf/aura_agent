"""
Ponto de entrada da aplicação.

Responsabilidade:
- Orquestrar os módulos
- Controlar o ciclo principal
- Ligar STT → LLM → TTS
"""

from audio.stt import listen, calibrate_noise
from audio.tts import speak
from llm.ollama import call_llm
from prompts.system_prompt import build_system_prompt
from memory.user_memory import init_db, save_fact
from memory.extract import extract_user_facts  # se quiseres separar
from config import MAX_TURNS

def main():
    # Inicialização
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
        extract_user_facts(user)

        messages[0]["content"] = build_system_prompt()

        try:
            reply = call_llm(messages)
        except Exception as e:
            print(f"❌ Erro LLM: {e}")
            speak("Houve um erro ao contactar o modelo.")
            continue

        messages.append({"role": "assistant", "content": reply})

        # Limitar histórico
        if len(messages) > 1 + MAX_TURNS * 2:
            messages = messages[:1] + messages[-MAX_TURNS * 2:]

        print(f"\nAssistente: {reply}\n")
        speak(reply)

if __name__ == "__main__":
    main()