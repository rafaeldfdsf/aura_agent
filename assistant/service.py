"""Nucleo reutilizavel do assistente para modo local e modo servidor."""

from __future__ import annotations

import json
from threading import Lock
from uuid import uuid4

from config import MAX_TURNS
from llm.ollama import call_llm
from memory.extract import extract_user_facts
from memory.user_memory import init_db
from prompts.system_prompt import build_system_prompt
from tools.executor import execute_tool, extract_tool_call
from tools.registry import API_SAFE_TOOLS, TOOLS


class AssistantService:
    """Mantem sessoes em memoria e processa mensagens do utilizador."""

    def __init__(self, enable_desktop_tools: bool = False):
        self.enable_desktop_tools = enable_desktop_tools
        self.available_tools = TOOLS if enable_desktop_tools else API_SAFE_TOOLS
        self.sessions = {}
        self.lock = Lock()
        init_db()

    def create_session(self) -> dict:
        session_id = str(uuid4())
        messages = [{"role": "system", "content": build_system_prompt(self.available_tools)}]

        with self.lock:
            self.sessions[session_id] = messages

        return {
            "session_id": session_id,
            "tools": self.available_tools,
            "desktop_tools_enabled": self.enable_desktop_tools,
        }

    def delete_session(self, session_id: str) -> bool:
        with self.lock:
            return self.sessions.pop(session_id, None) is not None

    def chat(self, session_id: str, user_message: str) -> dict:
        with self.lock:
            messages = self.sessions.get(session_id)

            if messages is None:
                raise KeyError(f"Sessao desconhecida: {session_id}")

            if not user_message or not user_message.strip():
                raise ValueError("A mensagem do utilizador nao pode estar vazia.")

            user_message = user_message.strip()
            messages.append({"role": "user", "content": user_message})
            extract_user_facts(user_message)
            messages[0]["content"] = build_system_prompt(self.available_tools)

            first_reply = call_llm(messages)
            tool_call = extract_tool_call(first_reply)

            executed_tool = None
            reply = first_reply

            if tool_call:
                executed_tool = execute_tool(
                    tool_call["tool_name"],
                    tool_call.get("arguments", {}),
                    allow_desktop_tools=self.enable_desktop_tools,
                )

                messages.append({"role": "assistant", "content": first_reply})
                messages.append({
                    "role": "tool",
                    "content": json.dumps(executed_tool, ensure_ascii=False),
                })
                reply = call_llm(messages)

            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 1 + MAX_TURNS * 2:
                messages[:] = messages[:1] + messages[-MAX_TURNS * 2:]

            return {
                "session_id": session_id,
                "reply": reply,
                "tool_result": executed_tool,
                "desktop_tools_enabled": self.enable_desktop_tools,
            }
