from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_id: str
    tools: list[dict]
    desktop_tools_enabled: bool


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_result: dict | None = None
    desktop_tools_enabled: bool
