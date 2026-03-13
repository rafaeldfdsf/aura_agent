import os

def open_app(command):

    command = command.lower()

    if "youtube" in command:
        os.system("start https://youtube.com")
        return "A abrir o YouTube."

    if "google" in command:
        os.system("start https://google.com")
        return "A abrir o Google."

    if "calculadora" in command:
        os.system("calc")
        return "A abrir a calculadora."

    return None