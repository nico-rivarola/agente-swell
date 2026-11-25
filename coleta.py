"""
Coleta: llama a las 2 APIs de Open-Meteo y devuelve una lista de "registros"
(un diccionario por hora) con todo junto.

¿Por qué convertir a registros? La API devuelve el JSON en formato
"columnar" (una lista por variable). Para puntuar es mucho más cómodo tener
una fila por hora, como en una planilla.
"""
import logging
from datetime import datetime

import requests

from praias import DIAS_PREVISAO

URL_MARINE = "https://marine-api.open-meteo.com/v1/marine"
URL_TEMPO = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "America/Bahia"  # Salvador no tiene horario de verano: UTC-3 fijo

log = logging.getLogger(__name__)


def buscar_dados(lat, lon):
    params_marine = {
        "latitude": lat, "longitude": lon,
        "hourly": ",".join([
            "swell_wave_height",     # altura del swell (m)
            "swell_wave_direction",  # de dónde viene (°)
            "swell_wave_period",     # período (s): lo que da FUERZA a la ola
            "wave_height",           # ola total = swell + mar de viento
            "sea_level_height_msl",  # nivel del mar, incluye marea (m)
        ]),
        "timezone": TIMEZONE,
        "forecast_days": DIAS_PREVISAO,
    }
    params_tempo = {
        "latitude": lat, "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "wind_speed_unit": "kn",   # nudos, igual que Windguru
        "timezone": TIMEZONE,
        "forecast_days": DIAS_PREVISAO,
    }

    # timeout SIEMPRE: sin él, si la API se cuelga, el GitHub Action
    # queda esperando hasta que GitHub lo mata (y gasta tus minutos gratis).
    r1 = requests.get(URL_MARINE, params=params_marine, timeout=20)
    r2 = requests.get(URL_TEMPO, params=params_tempo, timeout=20)
    r1.raise_for_status()  # error HTTP → excepción, no datos basura
    r2.raise_for_status()
    marine = r1.json()["hourly"]
    tempo = r2.json()["hourly"]

    # "Join" por hora (como un JOIN en SQL): no asumimos que las dos APIs
    # devuelven exactamente las mismas horas en el mismo orden.
    vento_por_hora = {
        t: (tempo["wind_speed_10m"][i], tempo["wind_direction_10m"][i],
            tempo["wind_gusts_10m"][i])
        for i, t in enumerate(tempo["time"])
    }

    registros = []
    for i, t in enumerate(marine["time"]):
        vel, dire, raj = vento_por_hora.get(t, (None, None, None))
        registros.append({
            "hora": datetime.fromisoformat(t),
            "swell_altura": marine["swell_wave_height"][i],
            "swell_direcao": marine["swell_wave_direction"][i],
            "swell_periodo": marine["swell_wave_period"][i],
            "onda_total": marine["wave_height"][i],
            "nivel_mar": marine["sea_level_height_msl"][i],
            "vento_vel": vel,
            "vento_direcao": dire,
            "vento_rajada": raj,
        })
    log.debug("Open-Meteo (%s, %s): %d horas", lat, lon, len(registros))
    return registros
