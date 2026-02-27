"""
Comunicação com o LLM (Ollama).

Responsabilidade única:
- Enviar mensagens ao Ollama
- Devolver a resposta do modelo

Não deve conter lógica de conversa nem estado.
"""

import requests
from config import OLLAMA_URL, MODEL

def call_llm(messages):
    """
    Envia uma conversa ao Ollama e devolve a resposta do modelo.

    :param messages: lista de mensagens no formato OpenAI
    :return: texto da resposta do assistente
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["message"]["content"]