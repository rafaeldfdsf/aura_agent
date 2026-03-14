"""
Comunicação com o LLM (Ollama).

Responsabilidade única:
- Enviar mensagens ao Ollama
- Receber a resposta do modelo

Este módulo NÃO:
- controla fluxo da conversa
- executa tools
- mantém estado

Ele apenas faz a chamada HTTP ao Ollama.
"""

import requests
from config import OLLAMA_URL, MODEL


def call_llm(messages):
    """
    Envia a conversa ao Ollama e devolve a resposta do modelo.

    :param messages: lista de mensagens no formato OpenAI
                     exemplo:
                     [
                       {"role": "system", "content": "..."},
                       {"role": "user", "content": "..."}
                     ]

    :return: texto da resposta do modelo
    """

    # ---------------------------------
    # Payload enviado ao Ollama
    # ---------------------------------
    payload = {
        "model": MODEL,      # modelo configurado (ex: qwen2.5, llama3, mistral)
        "messages": messages,
        "stream": False,     # queremos resposta completa (não streaming)

        # opções que controlam o comportamento do modelo
        "options": {
            "temperature": 0.7,   # criatividade moderada
            "top_p": 0.9,         # diversidade de resposta
        }
    }

    # ---------------------------------
    # Fazer pedido HTTP ao Ollama
    # ---------------------------------
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=60
    )

    # se houver erro HTTP lança exceção
    r.raise_for_status()

    data = r.json()

    # ---------------------------------
    # Extrair texto da resposta
    # ---------------------------------
    reply = data["message"]["content"]

    # remover espaços extras
    reply = reply.strip()

    return reply