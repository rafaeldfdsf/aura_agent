import subprocess
import webbrowser
import pyautogui


KNOWN_APPS = {
    "calculadora": "calc",
    "bloco de notas": "notepad",
    "notepad": "notepad",
    "explorador": "explorer",
    "cmd": "cmd",
}


def open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"A abrir {url}."


def open_app(app_name: str) -> str:
    name = app_name.strip().lower()

    if name not in KNOWN_APPS:
        return f"Não conheço a aplicação '{app_name}'."

    subprocess.Popen(KNOWN_APPS[name], shell=True)
    return f"A abrir {app_name}."


def type_text(text: str) -> str:
    pyautogui.write(text, interval=0.02)
    return "Texto escrito."


def press_keys(keys: str) -> str:
    parts = [k.strip().lower() for k in keys.split("+") if k.strip()]
    pyautogui.hotkey(*parts)
    return f"Teclas premidas: {keys}."