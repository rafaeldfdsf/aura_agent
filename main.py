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
from memory.user_memory import init_db
from memory.extract import extract_user_facts
from config import MAX_TURNS
from tools.router import use_tool

def main():

    # Inicialização
    init_db()

    # calibração de ruído do microfone
    voice_threshold = calibrate_noise()

    # histórico da conversa
    messages = [{"role": "system", "content": build_system_prompt()}]

    print("🟢 Assistente com voz iniciado")
    print("Diz 'sair' para terminar\n")

    while True:

        # ouvir utilizador
        user = listen(voice_threshold)

        if not user:
            continue

        # comando para sair
        if user.lower() in {"sair", "exit", "quit"}:
            speak("Até logo!")
            break

        # guardar mensagem do utilizador
        messages.append({"role": "user", "content": user})

        # extrair factos do utilizador (memória)
        extract_user_facts(user)

        # atualizar system prompt com memória
        messages[0]["content"] = build_system_prompt()

        # -----------------------------
        # VERIFICAR SE EXISTE UMA TOOL
        # -----------------------------
        tool_response = use_tool(user)

        if tool_response:

            reply = tool_response

        else:

            # chamar LLM se nenhuma tool resolver
            try:
                reply = call_llm(messages)

            except Exception as e:
                print(f"❌ Erro LLM: {e}")
                speak("Houve um erro ao contactar o modelo.")
                continue

        # guardar resposta no histórico
        messages.append({"role": "assistant", "content": reply})

        # limitar histórico para não crescer demasiado
        if len(messages) > 1 + MAX_TURNS * 2:
            messages = messages[:1] + messages[-MAX_TURNS * 2:]

        print(f"\nAssistente: {reply}\n")

        # falar resposta
        speak(reply)


if __name__ == "__main__":
    main()