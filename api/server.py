from fastapi import FastAPI, HTTPException

from api.schemas import ChatRequest, ChatResponse, SessionResponse
from assistant.service import AssistantService


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
