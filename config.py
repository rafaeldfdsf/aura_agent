"""
Configuração global da aplicação.

Este ficheiro contém APENAS constantes e flags globais.
Não deve conter lógica de negócio.

Qualquer valor que possa mudar entre ambientes
(dev, prod, máquina diferente) deve viver aqui.
"""

# Endereço do servidor Ollama (LLM local)
OLLAMA_URL = "http://127.0.0.1:11434"

# Modelo LLM a usar
MODEL = "llama3.1:8b"


# Configuração de áudio
# Whisper funciona melhor a 16 kHz
SAMPLE_RATE = 16000

# Histórico de conversa (perguntas + respostas)
MAX_TURNS = 6

# Base de dados local para memória persistente
DB_FILE = "memory.db"

# Flag global usada para interromper o TTS (barge-in)
STOP_TTS = False