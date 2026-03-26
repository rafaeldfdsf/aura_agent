import json
import re
from tools.weather import get_weather
from tools.web_search import search_web
from tools.desktop import open_website, open_app, type_text, press_keys
from tools.schemas import tool_result
from tools.registry import DESKTOP_TOOL_NAMES


def extract_tool_call(text: str):
    if not isinstance(text, str):
        return None

    text = text.strip()

    def parse_json_fragment(fragment: str):
        try:
            data = json.loads(fragment)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict) and data.get("type") == "tool_call":
            return data
        return None

    # quick path: exact JSON
    if text.startswith("{") and text.endswith("}"):
        result = parse_json_fragment(text)
        if result:
            return result

    # search any JSON object inside the text
    depth = 0
    in_string = False
    escaped = False
    start = None

    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
            continue

        if ch == '}':
            if depth > 0:
                depth -= 1
            if depth == 0 and start is not None:
                candidate = text[start:i+1]
                result = parse_json_fragment(candidate)
                if result:
                    return result

    return None


def execute_tool(tool_name: str, arguments: dict, allow_desktop_tools: bool = True):
    try:
        if tool_name in DESKTOP_TOOL_NAMES and not allow_desktop_tools:
            return tool_result(
                tool_name,
                False,
                "Esta tool esta desativada neste modo de execucao."
            )

        if tool_name == "get_weather":
            city = arguments.get("city", "Lisboa")
            day_offset = arguments.get("day_offset")
            if day_offset is None:
                # suporta parâmetro de texto p.ex. "amanhã" -> 1
                text = arguments.get("text", "")
                day_offset = parse_day(text)
            try:
                day_offset = int(day_offset)
            except (TypeError, ValueError):
                day_offset = 1
            return tool_result(tool_name, True, get_weather(city, day_offset))

        if tool_name == "search_web":
            query = arguments.get("query", "")
            return tool_result(tool_name, True, search_web(query))

        if tool_name == "open_website":
            url = arguments.get("url", "")
            return tool_result(tool_name, True, open_website(url))

        if tool_name == "open_app":
            app_name = arguments.get("app_name", "")
            return tool_result(tool_name, True, open_app(app_name))

        if tool_name == "type_text":
            text = arguments.get("text", "")
            return tool_result(tool_name, True, type_text(text))

        if tool_name == "press_keys":
            keys = arguments.get("keys", "")
            return tool_result(tool_name, True, press_keys(keys))

        return tool_result(tool_name, False, f"Tool desconhecida: {tool_name}")

    except Exception as e:
        return tool_result(tool_name, False, str(e))
    
def parse_day(text):

    text = (text or "").lower()

    if "depois de amanhã" in text or "depois de amanha" in text:
        return 2

    if "amanhã" in text or "amanha" in text:
        return 1

    if "hoje" in text:
        return 0

    if "sábado" in text or "sabado" in text:
        return 3

    if "domingo" in text:
        return 4

    return 0
