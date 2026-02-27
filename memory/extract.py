"""
Extração de factos a partir da fala do utilizador.

Responsabilidade:
- Detetar padrões simples (ex: nome)
- Guardar na memória persistente

Não é NLP avançado, é heurística.
"""

import re
from memory.user_memory import save_fact

def extract_user_facts(text):
    """
    Analisa texto e extrai factos simples do utilizador.
    """
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

            name = re.sub(r"[^\w\sÀ-ÿ]", "", name)
            name = " ".join(w.capitalize() for w in name.split())

            save_fact("name", name)
            print(f"🧠 Nome guardado: {name}")
            return