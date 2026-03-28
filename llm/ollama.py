"""
Comunicacao com o LLM (Ollama).

Responsabilidade unica:
- Enviar mensagens ao Ollama
- Receber a resposta do modelo
"""

import requests

from config import MODEL, OLLAMA_URL


class LLMUnavailableError(RuntimeError):
    """Erro levantado quando o Ollama nao esta acessivel."""


def call_llm(messages):
    """
    Envia a conversa ao Ollama e devolve a resposta do modelo.
    """
    payload = {
        'model': MODEL,
        'messages': messages,
        'stream': False,
        'options': {
            'temperature': 0.7,
            'top_p': 0.9,
        },
    }

    try:
        response = requests.post(
            f'{OLLAMA_URL}/api/chat',
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise LLMUnavailableError(
            f'Ollama indisponivel em {OLLAMA_URL}. Inicia o servidor Ollama e confirma que o modelo "{MODEL}" esta carregado.'
        ) from exc

    try:
        data = response.json()
        reply = data['message']['content'].strip()
    except (ValueError, KeyError, TypeError) as exc:
        raise LLMUnavailableError('O Ollama respondeu num formato inesperado.') from exc

    return reply