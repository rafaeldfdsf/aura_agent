import json
import re
from tools.weather import get_weather
from tools.web_search import search_web
from tools.desktop import open_website, open_app, type_text, press_keys
from tools.schemas import tool_result
from tools.registry import DESKTOP_TOOL_NAMES


def extract_tool_call(text: str):
    text = text.strip()

    if not text.startswith("{"):
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    if data.get("type") != "tool_call":
        return None

    return data


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
            return tool_result(tool_name, True, get_weather(city))

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

    text = text.lower()

    if "amanhã" in text:
        return 1

    if "depois de amanhã" in text:
        return 2

    if "sábado" in text:
        return 3

    if "domingo" in text:
        return 4

    return 1
