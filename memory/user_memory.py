"""
Memória persistente do utilizador (SQLite).

Responsabilidade:
- Guardar factos simples (nome, preferências, etc.)
- Disponibilizar leitura desses factos

Não contém lógica de NLP.
"""

import sqlite3
from config import DB_FILE

def init_db():
    """
    Cria a base de dados se não existir.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_fact(key, value):
    """
    Guarda ou atualiza um facto do utilizador.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO user_memory (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def load_facts():
    """
    Devolve todos os factos conhecidos como dicionário.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM user_memory")
    facts = dict(c.fetchall())
    conn.close()
    return facts