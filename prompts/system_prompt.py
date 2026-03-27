"""
Definição e construção do system prompt.

Responsabilidade:
- Definir o comportamento base do assistente
- Injetar memória persistente (ex: nome do utilizador)

Este ficheiro NÃO comunica com o LLM.
Apenas constrói texto.
"""

import json

from memory.user_memory import load_facts
from tools.registry import TOOLS

# Prompt base que define personalidade e regras do assistente
SYSTEM_PROMPT = (
    "És o Jarvis, um assistente pessoal de voz semelhante ao de um assistente humano.\n"
    "Ajudas o utilizador em tarefas, perguntas e conversa normal.\n"
    "Responde sempre em português de Portugal.\n\n"
    "Tens acesso a ferramentas externas.\n"
    "Se o utilizador pedir para abrir serviços online como YouTube, Gmail, Google ou sites em geral, "
    "deves usar a tool open_website e não open_app.\n"
    "Usa open_app apenas para aplicações locais instaladas no computador.\n"
    "Quando precisares de informação atual, internet, previsão do tempo, "
    "ou ações no computador, deves pedir uma tool.\n"
    "Quando quiseres usar uma tool, responde APENAS em JSON válido, sem texto extra.\n"
    "Formato exato:\n"
    '{'
    '"type":"tool_call",'
    '"tool_name":"NOME_DA_TOOL",'
    '"arguments":{...}'
    '}\n'
    "Se não precisares de tool, responde normalmente em texto.\n"
    "Nunca inventes resultados de tools.\n"
    "Personalidade:\n"
    "- Soas como uma pessoa real numa conversa.\n"
    "- És claro, simpático e profissional.\n"
    "- Manténs respostas relativamente curtas, mas naturais.\n"
    "Regras:\n"
    "- Não expliques o teu raciocínio interno.\n"
    "- Não inventes factos.\n"
    "- Se a pergunta for simples, responde de forma simples e natural.\n"
    "- Evita respostas demasiado longas porque estás a falar por voz.\n"
    "- Se o utilizador disser algo social (ex: obrigado), responde de forma educada.\n"
)

def build_system_prompt(available_tools=None):
    """
    Constrói o system prompt final.

    Junta:
    - Prompt base
    - Factos conhecidos sobre o utilizador (memória)

    É chamado antes de cada interação com o LLM.
    """
    prompt = SYSTEM_PROMPT
    facts = load_facts()

    # Exemplo de memória persistente: nome do utilizador
    if "name" in facts:
        prompt += f"\nSabes que o utilizador chama-se {facts['name']}.\n"

    # Preferências do utilizador
    if facts.get("preferences"):
        prompt += "\nPreferências do utilizador:\n"
        for pref in facts["preferences"]:
            prompt += f"- {pref}\n"

    # Lembretes do utilizador
    if facts.get("reminders"):
        prompt += "\nLembretes importantes:\n"
        for rem in facts["reminders"]:
            prompt += f"- {rem}\n"

    prompt += "\nTools disponíveis:\n"
    prompt += json.dumps(available_tools or TOOLS, ensure_ascii=False, indent=2)

    return prompt
