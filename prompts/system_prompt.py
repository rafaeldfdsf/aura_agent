"""
Definição e construção do system prompt.

Responsabilidade:
- Definir o comportamento base do assistente
- Injetar memória persistente (ex: nome do utilizador)

Este ficheiro NÃO comunica com o LLM.
Apenas constrói texto.
"""

from memory.user_memory import load_facts

# Prompt base que define personalidade e regras do assistente
SYSTEM_PROMPT = (
    "És o Jarvis, um assistente pessoal de voz semelhante ao de um assistente humano.\n"
    "Ajudas o utilizador em tarefas, perguntas e conversa normal.\n"
    "Responde sempre em português de Portugal.\n\n"
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

def build_system_prompt():
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

    return prompt