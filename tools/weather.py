import requests

CITY_COORDS = {
    "lisboa": (38.72, -9.13),
    "porto": (41.15, -8.61),
    "braga": (41.55, -8.42),
    "coimbra": (40.21, -8.43),
    "faro": (37.02, -7.93),
    "caldas da rainha": (39.40, -9.14),
}


def get_weather(city: str = "Lisboa") -> str:
    """
    Obtém previsão do tempo.

    day_offset:
    1 = amanhã
    2 = depois de amanhã
    3+ = dias seguintes
    """

    city_key = city.lower()
    lat, lon = CITY_COORDS.get(city_key, CITY_COORDS["lisboa"])

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&timezone=Europe/Lisbon"
    )

    r = requests.get(url)
    data = r.json()

    temp_max = data["daily"]["temperature_2m_max"][day_offset]
    temp_min = data["daily"]["temperature_2m_min"][day_offset]

    return (
        f"No dia previsto em {city.title()}, a temperatura deverá variar "
        f"entre {temp_min}°C e {temp_max}°C."
    )