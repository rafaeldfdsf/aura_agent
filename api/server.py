from fastapi import FastAPI, HTTPException, UploadFile, File
from api.schemas import ChatRequest, ChatResponse, SessionResponse
from assistant.service import AssistantService
from openai import OpenAI
import tempfile

client = OpenAI()

app = FastAPI(
    title="Jarvis Codex API",
    version="1.0.0",
    description="API HTTP para ligar o assistente a aplicacoes Windows, Android e iPhone.",
)

assistant = AssistantService(enable_desktop_tools=False)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/sessions", response_model=SessionResponse)
def create_session():
    return assistant.create_session()


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    deleted = assistant.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    return {"deleted": True}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        return assistant.chat(payload.session_id, payload.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    return transcript.text
