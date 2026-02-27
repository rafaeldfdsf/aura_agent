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
    "És o Darian, um assistente direto, objetivo e eficiente.\n"
    "Responde sempre em português de Portugal.\n\n"
    "Regras obrigatórias:\n"
    "- Responde de forma curta e direta.\n"
    "- Não expliques raciocínio.\n"
    "- Não acrescentes contexto desnecessário.\n"
    "- Não faças conversa.\n"
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
        prompt += f"\nFACTO CONHECIDO:\nO utilizador chama-se {facts['name']}.\n"

    return prompt