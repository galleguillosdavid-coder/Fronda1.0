"""
Fronda 1.0 - Motor de Consulta Meteorológica en Tiempo Real
Permite consultar el clima actual y pronóstico sin requerir API keys externas.
Usa wttr.in y Open-Meteo como proveedores de alta disponibilidad.
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any


def get_current_weather(location: str = "") -> str:
    """Consulta el clima actual y pronóstico para una ubicación dada."""
    clean_loc = location.strip()
    encoded_loc = urllib.parse.quote(clean_loc) if clean_loc else ""
    url = f"https://wttr.in/{encoded_loc}?format=j1" if encoded_loc else "https://wttr.in/?format=j1"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "curl/7.68.0", "Accept-Language": "es"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        city = area["areaName"][0]["value"]
        country = area["country"][0]["value"]

        temp_c = current.get("temp_C", "--")
        feels_like = current.get("FeelsLikeC", temp_c)
        desc = current.get("lang_es", [{}])[0].get("value") or current.get("weatherDesc", [{}])[0].get("value", "Despejado")
        humidity = current.get("humidity", "--")
        wind_kmph = current.get("windspeedKmph", "--")

        today_forecast = data.get("weather", [{}])[0]
        max_temp = today_forecast.get("maxtempC", "--")
        min_temp = today_forecast.get("mintempC", "--")

        return (
            f"🌤️ **CLIMA ACTUAL EN {city.upper()}, {country.upper()}**\n\n"
            f"• **Condición**: {desc}\n"
            f"• **Temperatura**: {temp_c}°C (Sensación térmica: {feels_like}°C)\n"
            f"• **Máxima / Mínima hoy**: {max_temp}°C / {min_temp}°C\n"
            f"• **Humedad**: {humidity}%\n"
            f"• **Viento**: {wind_kmph} km/h"
        )
    except Exception as e:
        return f"No se pudo obtener la información meteorológica en este momento ({e})."
