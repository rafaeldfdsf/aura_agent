from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from openai import OpenAI

from api.schemas import (
    ChatRequest,
    ChatResponse,
    MemoryEntryResponse,
    MemoryUpdateRequest,
    SessionResponse,
)
from assistant.service import AssistantService
from audio.tts import synthesize_speech
from llm.ollama import LLMUnavailableError
from memory.user_memory import clear_memory, delete_memory_entry, list_memory_entries, update_memory_entry

import tempfile

client = OpenAI()

router = APIRouter()

app = FastAPI(
    title='Jarvis Codex API',
    version='1.0.0',
    description='API HTTP para ligar o assistente a aplicacoes Windows, Android e iPhone.',
)

assistant = AssistantService(enable_desktop_tools=False)


@app.get('/health')
def healthcheck():
    return {'status': 'ok'}


@app.post('/sessions', response_model=SessionResponse)
def create_session():
    return assistant.create_session()


@app.delete('/sessions/{session_id}')
def delete_session(session_id: str):
    deleted = assistant.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Sessao nao encontrada.')
    return {'deleted': True}


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        return assistant.chat(payload.session_id, payload.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get('/memory', response_model=list[MemoryEntryResponse])
def get_memory_entries():
    return list_memory_entries()


@app.put('/memory/{memory_key}', response_model=MemoryEntryResponse)
def put_memory_entry(memory_key: str, payload: MemoryUpdateRequest):
    try:
        return update_memory_entry(memory_key, payload.value)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f'Memoria nao encontrada: {memory_key}') from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete('/memory/{memory_key}')
def remove_memory_entry(memory_key: str):
    deleted = delete_memory_entry(memory_key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f'Memoria nao encontrada: {memory_key}')
    return {'deleted': True}


@app.delete('/memory')
def remove_all_memory():
    deleted_count = clear_memory()
    return {'deleted': True, 'count': deleted_count}


@app.post('/transcribe')
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    with open(tmp_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
            language='pt',
        )

    return transcript.text


@router.post('/tts')
async def tts_endpoint(data: dict):
    text = data.get('text')
    audio = synthesize_speech(text)
    return {'audio': audio}


app.include_router(router)