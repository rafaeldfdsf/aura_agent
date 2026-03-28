"""Nucleo reutilizavel do assistente para modo local e modo servidor."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from datetime import datetime
from threading import Lock
from uuid import uuid4

from config import MAX_TURNS, DB_FILE
from llm.ollama import call_llm
from memory.extract import extract_user_facts
from memory.user_memory import init_db, load_facts, delete_preference, delete_reminder
from prompts.system_prompt import build_system_prompt
from tools.executor import execute_tool, extract_tool_call, parse_day
from tools.registry import TOOLS
from tools.weather import CITY_COORDS


WEEKDAYS_PT = (
    "segunda-feira",
    "terca-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sabado",
    "domingo",
)

MONTHS_PT = (
    "janeiro",
    "fevereiro",
    "marco",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", (text or "").lower().strip())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def build_time_reply(now: datetime) -> str:
    if now.hour == 0 and now.minute == 0:
        return "E meia-noite."

    if now.hour == 0:
        if now.minute == 1:
            return "E meia-noite e 1 minuto."
        return f"E meia-noite e {now.minute} minutos."

    if now.hour == 12 and now.minute == 0:
        return "E meio-dia."

    if now.hour == 12:
        if now.minute == 1:
            return "E meio-dia e 1 minuto."
        return f"E meio-dia e {now.minute} minutos."

    if now.hour == 1:
        if now.minute == 0:
            return "E 1 hora."
        if now.minute == 1:
            return "E 1 hora e 1 minuto."
        return f"E 1 hora e {now.minute} minutos."

    if now.minute == 0:
        return f"Sao {now.hour} horas."

    if now.minute == 1:
        return f"Sao {now.hour} horas e 1 minuto."

    return f"Sao {now.hour} horas e {now.minute} minutos."


def build_date_reply(now: datetime) -> str:
    weekday = WEEKDAYS_PT[now.weekday()]
    month = MONTHS_PT[now.month - 1]
    return f"Hoje e {weekday}, {now.day} de {month} de {now.year}."


def build_weekday_reply(now: datetime) -> str:
    return f"Hoje e {WEEKDAYS_PT[now.weekday()]}."


class AssistantService:
    """Mantem sessoes em memoria e processa mensagens do utilizador."""

    def __init__(self, enable_desktop_tools: bool = False):
        self.enable_desktop_tools = enable_desktop_tools
        self.available_tools = TOOLS
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
            msg = normalize_text(user_message)

            if any(x in msg for x in ["que horas", "horas sao", "as horas", "hora atual"]):
                now = datetime.now().astimezone()
                return {
                    "session_id": session_id,
                    "reply": build_time_reply(now),
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            if any(x in msg for x in ["que dia e hoje", "qual e a data", "data de hoje", "em que dia estamos", "dia de hoje"]):
                now = datetime.now().astimezone()
                return {
                    "session_id": session_id,
                    "reply": build_date_reply(now),
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            if any(x in msg for x in ["que dia da semana", "dia da semana"]):
                now = datetime.now().astimezone()
                return {
                    "session_id": session_id,
                    "reply": build_weekday_reply(now),
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # =========================
            # COMANDOS DIRETOS (PC)
            # =========================

            if any(x in msg for x in ["fecha", "fechar"]) and "janela" in msg:
                return {
                    "session_id": session_id,
                    "reply": "A fechar a janela.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": {
                        "type": "pc_action",
                        "action": "close_window"
                    }
                }

            if "volume" in msg and ("aumenta" in msg or "subir" in msg):
                return {
                    "session_id": session_id,
                    "reply": "A aumentar o volume.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": {
                        "type": "pc_action",
                        "action": "volume_up"
                    }
                }

            if "volume" in msg and ("baixa" in msg or "diminuir" in msg):
                return {
                    "session_id": session_id,
                    "reply": "A baixar o volume.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": {
                        "type": "pc_action",
                        "action": "volume_down"
                    }
                }

            if "screenshot" in msg or "captura" in msg:
                return {
                    "session_id": session_id,
                    "reply": "A tirar screenshot.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": {
                        "type": "pc_action",
                        "action": "screenshot"
                    }
                }

            # =========================
            # COMANDOS DE MEMÃƒÆ’Ã¢â‚¬Å“RIA
            # =========================

            if any(x in msg for x in ["memÃƒÆ’Ã‚Â³ria", "memoria", "lembretes", "preferÃƒÆ’Ã‚Âªncias", "preferencias"]) and any(y in msg for y in ["mostra", "lista", "ver", "mostrar"]):
                facts = load_facts()
                table_format = "tabela" in msg or "table" in msg

                if table_format:
                    # Formato de tabela
                    reply_lines = ["| ID | Tipo | ConteÃƒÆ’Ã‚Âºdo |", "|----|------|---------|"]

                    if "name" in facts:
                        reply_lines.append(f"| - | Nome | {facts['name']} |")

                    preferences = facts.get("preferences", [])
                    for i, pref in enumerate(preferences, 1):
                        reply_lines.append(f"| {i} | PreferÃƒÆ’Ã‚Âªncia | {pref} |")

                    reminders = facts.get("reminders", [])
                    for i, rem in enumerate(reminders, 1):
                        reply_lines.append(f"| {i} | Lembrete | {rem} |")

                    if not preferences and not reminders and "name" not in facts:
                        reply_lines.append("| - | - | Nenhuma informaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o guardada |")

                    reply = "\n".join(reply_lines)
                else:
                    # Formato de lista (original)
                    response_parts = []

                    if "name" in facts:
                        response_parts.append(f"Nome guardado: {facts['name']}")

                    preferences = facts.get("preferences", [])
                    if preferences:
                        response_parts.append("PreferÃƒÆ’Ã‚Âªncias:")
                        for i, pref in enumerate(preferences, 1):
                            response_parts.append(f"  {i}. {pref}")
                    else:
                        response_parts.append("Nenhuma preferÃƒÆ’Ã‚Âªncia guardada.")

                    reminders = facts.get("reminders", [])
                    if reminders:
                        response_parts.append("Lembretes:")
                        for i, rem in enumerate(reminders, 1):
                            response_parts.append(f"  {i}. {rem}")
                    else:
                        response_parts.append("Nenhum lembrete guardado.")

                    reply = "\n".join(response_parts)

                return {
                    "session_id": session_id,
                    "reply": reply,
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # Remover preferÃƒÆ’Ã‚Âªncia
            import re
            match = re.search(r"remove\s+preferÃƒÆ’Ã‚Âªncia\s+(\d+)|remover\s+preferencia\s+(\d+)", msg, re.IGNORECASE)
            if match:
                index = int(match.group(1) or match.group(2))
                delete_preference(index)
                return {
                    "session_id": session_id,
                    "reply": f"PreferÃƒÆ’Ã‚Âªncia {index} removida da memÃƒÆ’Ã‚Â³ria.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # Remover lembrete
            match = re.search(r"remove\s+lembrete\s+(\d+)|remover\s+lembrete\s+(\d+)", msg, re.IGNORECASE)
            if match:
                index = int(match.group(1) or match.group(2))
                delete_reminder(index)
                return {
                    "session_id": session_id,
                    "reply": f"Lembrete {index} removido da memÃƒÆ’Ã‚Â³ria.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # Limpar toda a memÃƒÆ’Ã‚Â³ria
            if any(x in msg for x in ["limpa", "limpar", "esquece", "esquecer"]) and "memÃƒÆ’Ã‚Â³ria" in msg or "memoria" in msg:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM user_memory")
                conn.commit()
                conn.close()
                return {
                    "session_id": session_id,
                    "reply": "Toda a memÃƒÆ’Ã‚Â³ria foi limpa.",
                    "tool_result": None,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # =========================
            # COMANDOS DE CLIMA (fallback local rápido)
            # =========================

            if "tempo" in msg:
                day_offset = parse_day(msg)
                city = "Lisboa"

                # Verificar preferencias para cidade padrão
                facts = load_facts()
                preferences = facts.get("preferences", [])
                for pref in preferences:
                    if "tempo" in pref.lower() and "caldas da rainha" in pref.lower():
                        city = "caldas da rainha"
                        break

                for known_city in CITY_COORDS.keys():
                    if known_city in msg:
                        city = known_city
                        break

                executed_tool = execute_tool("get_weather", {"city": city, "day_offset": day_offset})

                # passar resultado para LLM para resposta mais natural
                tool_call = {
                    "type": "tool_call",
                    "tool_name": "get_weather",
                    "arguments": {"city": city, "day_offset": day_offset},
                }

                messages.append({"role": "user", "content": user_message})
                messages.append({"role": "assistant", "content": json.dumps(tool_call, ensure_ascii=False)})
                messages.append({"role": "tool", "content": json.dumps(executed_tool, ensure_ascii=False)})

                reply = call_llm(messages)

                return {
                    "session_id": session_id,
                    "reply": reply,
                    "tool_result": executed_tool,
                    "desktop_tools_enabled": self.enable_desktop_tools,
                    "client_action": None,
                }

            # =========================
            # CONTINUA FLUXO NORMAL
            # =========================

            messages.append({"role": "user", "content": user_message})

            extract_user_facts(user_message)
            messages[0]["content"] = build_system_prompt(self.available_tools)

            first_reply = call_llm(messages)

            # Tentar converter resposta em JSON
            parsed = None
            try:
                parsed = json.loads(first_reply)
            except Exception:
                pass

            tool_call = None

            if isinstance(parsed, dict) and parsed.get("type") == "tool_call":
                tool_call = parsed

            if not tool_call:
                tool_call = extract_tool_call(first_reply)

            client_action = None
            executed_tool = None
            reply = first_reply

            # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â§ Converter tool ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ aÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o Flutter
            def build_client_action(tool_call: dict):
                tool_name = tool_call.get("tool_name")
                args = tool_call.get("arguments", {}) or {}

                if tool_name in ["open_app", "open_youtube"]:
                    app_name = (args.get("app_name") or "").strip().lower()

                    if tool_name == "open_youtube":
                        app_name = "youtube"

                    if not app_name:
                        return None

                    if app_name in ["youtube", "yt"]:
                        return {
                            "type": "open_url",
                            "url": "https://www.youtube.com",
                        }

                    return {
                        "type": "open_app",
                        "app_name": app_name,
                    }

                if tool_name == "open_website":
                    url = (args.get("url") or "").strip()

                    if not url:
                        return None

                    if not url.startswith("http"):
                        url = "https://" + url

                    return {
                        "type": "open_url",
                        "url": url,
                    }

                return None

            # PROCESSAMENTO DE TOOL
            if tool_call:
                try:
                    args = tool_call.get("arguments", {})

                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}

                    if not isinstance(args, dict):
                        args = {}

                    tool_call["arguments"] = args
                    tool_name = tool_call.get("tool_name")

                    # ÃƒÂ°Ã…Â¸Ã¢â‚¬ËœÃ¢â‚¬Â° aÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes mobile
                    if tool_name in {"open_website", "open_app", "open_youtube"}:
                        client_action = build_client_action(tool_call)

                        if client_action:
                            executed_tool = {
                                "tool_name": tool_name,
                                "ok": True,
                                "data": "AÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o enviada para o cliente.",
                            }

                            reply = "A executar a aÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o."
                        else:
                            executed_tool = {
                                "tool_name": tool_name,
                                "ok": False,
                                "data": "Erro ao converter aÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o.",
                            }

                            reply = executed_tool["data"]

                    # ÃƒÂ°Ã…Â¸Ã¢â‚¬ËœÃ¢â‚¬Â° outras tools backend
                    else:
                        executed_tool = execute_tool(
                            tool_name,
                            args,
                            allow_desktop_tools=self.enable_desktop_tools,
                        )

                        messages.append({
                            "role": "assistant",
                            "content": json.dumps(tool_call, ensure_ascii=False),
                        })

                        messages.append({
                            "role": "tool",
                            "content": json.dumps(executed_tool, ensure_ascii=False),
                        })

                        if executed_tool.get("ok"):
                            if tool_name in {"get_weather", "search_web"}:
                                # fornecer a resposta da tool ao LLM e deixar o LLM reformular para a pergunta
                                reply = call_llm(messages)
                            else:
                                reply = call_llm(messages)
                        else:
                            reply = f"Nao consegui executar: {executed_tool.get('data')}"

                except Exception as e:
                    print("ERRO TOOL:", e)
                    reply = f"Erro ao executar ferramenta: {str(e)}"

            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 1 + MAX_TURNS * 2:
                messages[:] = messages[:1] + messages[-MAX_TURNS * 2:]

            return {
                "session_id": session_id,
                "reply": reply,
                "tool_result": executed_tool,
                "desktop_tools_enabled": self.enable_desktop_tools,
                "client_action": client_action,
            }
        
def build_client_action(tool_call: dict) -> dict | None:
    tool_name = tool_call.get("tool_name")
    args = tool_call.get("arguments", {}) or {}

    if tool_name == "open_website":
        url = args.get("url", "").strip()
        if not url:
            return None

        if not url.startswith("http"):
            url = "https://" + url

        return {
            "type": "open_url",
            "url": url,
        }

    if tool_name == "open_app":
        app_name = args.get("app_name", "").strip().lower()

        if app_name in ["youtube", "yt"]:
            return {
                "type": "open_url",
                "url": "https://www.youtube.com",
            }

        return {
            "type": "show_message",
            "message": f"A app '{app_name}' ainda nÃƒÆ’Ã‚Â£o estÃƒÆ’Ã‚Â¡ mapeada no telemÃƒÆ’Ã‚Â³vel.",
        }

    return None
