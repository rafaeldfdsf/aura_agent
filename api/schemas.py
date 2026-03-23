from pydantic import BaseModel
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    session_id: str
    message: str


class SessionResponse(BaseModel):
    session_id: str
    tools: list
    desktop_tools_enabled: bool


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_result: Optional[Dict[str, Any]] = None
    desktop_tools_enabled: bool
    client_action: Optional[Dict[str, Any]] = None