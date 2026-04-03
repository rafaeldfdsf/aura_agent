TOOLS = [
    {
        "name": "get_weather",
        "description": "Obtém a previsão do tempo para uma cidade.",
        "parameters": {
            "city": "string"
        }
    },
    {
        "name": "search_web",
        "description": "Pesquisa informação atual na web.",
        "parameters": {
            "query": "string"
        }
    },
    {
        "name": "open_website",
        "description": "Abre um site no navegador.",
        "parameters": {
            "url": "string"
        }
    },
    {
        "name": "open_app",
        "description": "Abre uma aplicação local conhecida.",
        "parameters": {
            "app_name": "string"
        }
    },
    {
        "name": "type_text",
        "description": "Escreve texto no campo ativo.",
        "parameters": {
            "text": "string"
        }
    },
    {
        "name": "press_keys",
        "description": "Prime combinações de teclas conhecidas, como ctrl+s.",
        "parameters": {
            "keys": "string"
        }
    }
]

LOCAL_AUTOMATION_TOOL_NAMES = {
    "type_text",
    "press_keys",
}

CLIENT_ACTION_TOOL_NAMES = {
    "open_website",
    "open_app",
}


def available_tools(enable_local_automation: bool = True) -> list[dict]:
    if enable_local_automation:
        return list(TOOLS)

    return [
        tool
        for tool in TOOLS
        if tool["name"] not in LOCAL_AUTOMATION_TOOL_NAMES
    ]


API_SAFE_TOOLS = available_tools(enable_local_automation=False)
