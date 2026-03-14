"""
Ponto de entrada da aplicação.

Responsabilidade:
- Orquestrar todos os módulos
- Controlar o ciclo principal do assistente
- Ligar os componentes:
  STT (voz → texto)
  LLM (texto → resposta / tool)
  TTS (texto → voz)
"""

# STT
from audio.stt import listen, wait_for_wake_word, calibrate_noise

# TTS
from audio.tts import speak

# LLM
from llm.ollama import call_llm

# prompts
from prompts.system_prompt import build_system_prompt

# memória
from memory.user_memory import init_db
from memory.extract import extract_user_facts

# config
from config import MAX_TURNS

# tools
from tools.executor import extract_tool_call, execute_tool

import json


def main():

    # ---------------------------------
    # Inicializar memória persistente
    # ---------------------------------
    init_db()

    # ---------------------------------
    # Calibração do microfone
    # (mantido para compatibilidade)
    # ---------------------------------
    voice_threshold = calibrate_noise()

    # ---------------------------------
    # Histórico da conversa
    # ---------------------------------
    messages = [{"role": "system", "content": build_system_prompt()}]

    print("🟢 Assistente com voz iniciado")
    print("Diz 'Jarvis' para começar a falar\n")

    # ---------------------------------
    # LOOP PRINCIPAL DO ASSISTENTE
    # ---------------------------------
    while True:

        # ---------------------------------
        # Esperar palavra de ativação
        # ---------------------------------
        wait_for_wake_word()

        speak("Sim?")

        # ---------------------------------
        # MODO CONVERSA
        # ---------------------------------
        while True:

            # ouvir utilizador
            user = listen(voice_threshold)

            # se não houve fala válida
            if not user:
                continue

            # sair do modo conversa
            if user.lower() in {"sair", "exit", "quit"}:
                speak("Ok, fico à espera.")
                break

            # guardar mensagem do utilizador
            messages.append({"role": "user", "content": user})

            # tentar extrair factos do utilizador
            extract_user_facts(user)

            # atualizar system prompt com memória
            messages[0]["content"] = build_system_prompt()

            # ---------------------------------
            # PRIMEIRA CHAMADA AO LLM
            # ---------------------------------
            try:

                first_reply = call_llm(messages)

            except Exception as e:

                print(f"❌ Erro LLM: {e}")
                speak("Houve um erro ao contactar o modelo.")
                continue

            # ---------------------------------
            # VERIFICAR TOOL CALL
            # ---------------------------------
            tool_call = extract_tool_call(first_reply)

            if tool_call:

                # executar ferramenta
                result = execute_tool(
                    tool_call["tool_name"],
                    tool_call.get("arguments", {})
                )

                # guardar pedido de tool
                messages.append({"role": "assistant", "content": first_reply})

                # guardar resultado da tool
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False)
                })

                # ---------------------------------
                # SEGUNDA CHAMADA AO LLM
                # ---------------------------------
                try:

                    reply = call_llm(messages)

                except Exception as e:

                    print(f"❌ Erro após tool: {e}")
                    speak("Houve um erro ao executar a ferramenta.")
                    continue

            else:

                # resposta direta do modelo
                reply = first_reply

            # guardar resposta final
            messages.append({"role": "assistant", "content": reply})

            # ---------------------------------
            # LIMITAR HISTÓRICO
            # ---------------------------------
            if len(messages) > 1 + MAX_TURNS * 2:
                messages = messages[:1] + messages[-MAX_TURNS * 2:]

            # mostrar no terminal
            print(f"\nAssistente: {reply}\n")

            # falar resposta
            speak(reply)


# ponto de entrada do programa
if __name__ == "__main__":
    main()