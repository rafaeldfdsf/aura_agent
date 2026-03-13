from tools.weather import get_weather
from tools.web_search import search_web
from tools.system_control import open_app

def use_tool(user_text):

    text = user_text.lower()

    # tempo
    if "tempo" in text or "meteorologia" in text:
        return get_weather()

    # abrir aplicações
    app = open_app(text)
    if app:
        return app

    # pesquisa web
    if "quem é" in text or "o que é" in text or "pesquisa" in text:
        return search_web(text)

    return None