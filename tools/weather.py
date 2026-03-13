import requests

def get_weather():

    # Coordenadas Lisboa (podes melhorar depois)
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=38.72&longitude=-9.13"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&timezone=Europe/Lisbon"
    )

    r = requests.get(url)
    data = r.json()

    temp_max = data["daily"]["temperature_2m_max"][1]
    temp_min = data["daily"]["temperature_2m_min"][1]

    return f"Amanhã a temperatura deverá variar entre {temp_min}°C e {temp_max}°C."