"""
Fronda 1.0 - Motor de Calendario, Feriados y Efemérides Históricas
Especializado en festividades de Chile y efemérides culturales.
Calcula en tiempo real fechas patrias, días restantes y festividades oficiales.
"""

import datetime
from typing import Dict, Any, List, Optional


CHILE_HOLIDAYS = [
    {"dia": 1, "mes": 1, "nombre": "Año Nuevo", "tipo": "Civil e Irrenunciable"},
    {"dia": 1, "mes": 5, "nombre": "Día Nacional del Trabajo", "tipo": "Laboral e Irrenunciable"},
    {"dia": 21, "mes": 5, "nombre": "Día de las Glorias Navales (Combate Naval de Iquique)", "tipo": "Histórico"},
    {"dia": 16, "mes": 7, "nombre": "Día de la Virgen del Carmen", "tipo": "Religioso"},
    {"dia": 15, "mes": 8, "nombre": "Asunción de la Virgen", "tipo": "Religioso"},
    {"dia": 18, "mes": 9, "nombre": "Fiestas Patrias (Primera Junta Nacional de Gobierno)", "tipo": "Patrio e Irrenunciable"},
    {"dia": 19, "mes": 9, "nombre": "Día de las Glorias del Ejército", "tipo": "Patrio e Irrenunciable"},
    {"dia": 12, "mes": 10, "nombre": "Encuentro de Dos Mundos", "tipo": "Civil"},
    {"dia": 31, "mes": 10, "nombre": "Día Nacional de las Iglesias Evangélicas y Protestantes", "tipo": "Religioso"},
    {"dia": 1, "mes": 11, "nombre": "Día de Todos los Santos", "tipo": "Religioso"},
    {"dia": 8, "mes": 12, "nombre": "Inmaculada Concepción", "tipo": "Religioso"},
    {"dia": 25, "mes": 12, "nombre": "Navidad", "tipo": "Religioso e Irrenunciable"},
]


def get_september_18_info() -> str:
    """Genera la información cultural, histórica y conteo exacto para el 18 de septiembre."""
    hoy = datetime.date.today()
    año = hoy.year
    fecha_18 = datetime.date(año, 9, 18)

    # Si ya pasó este año, contar para el próximo
    if hoy > fecha_18:
        fecha_18 = datetime.date(año + 1, 9, 18)

    dias_faltantes = (fecha_18 - hoy).days

    if dias_faltantes == 0:
        conteo_str = "🎉 ¡HOY ES 18 DE SEPTIEMBRE! ¡FELICES FIESTAS PATRIAS!"
    elif dias_faltantes == 1:
        conteo_str = "⏳ ¡Mañana es 18 de septiembre! La previa dieciochera está lista."
    else:
        conteo_str = f"⏳ Faltan exactamente **{dias_faltantes} días** para el 18 de septiembre de {fecha_18.year}."

    return (
        f"🇨🇱 **18 DE SEPTIEMBRE — FIESTAS PATRIAS DE CHILE**\n\n"
        f"{conteo_str}\n\n"
        f"• **¿Qué se celebra?**: Se conmemora la proclamación de la **Primera Junta Nacional de Gobierno** de 1810, "
        f"el hito histórico que inició el proceso de independencia de Chile.\n"
        f"• **Tradiciones y Cultura**: Días de celebración con fondas y ramadas, baile nacional (la cueca), "
        f"empanadas de pino, asados, anticuchos, chicha, terremoto y juegos típicos como el volantín y la rayuela.\n"
        f"• **Feriados Oficiales**: El **18 y 19 de septiembre** son feriados obligatorios e irrenunciables en todo el territorio nacional chileno.\n\n"
        f"¡Tikitikiti! 🇨🇱🍷🥩"
    )


def get_next_holiday() -> str:
    """Calcula el próximo feriado oficial desde la fecha actual."""
    hoy = datetime.date.today()
    año = hoy.year

    # Buscar en este año
    candidatos = []
    for h in CHILE_HOLIDAYS:
        f = datetime.date(año, h["mes"], h["dia"])
        if f >= hoy:
            candidatos.append((f, h))

    # Si no quedan este año, buscar al inicio del próximo
    if not candidatos:
        for h in CHILE_HOLIDAYS:
            f = datetime.date(año + 1, h["mes"], h["dia"])
            candidatos.append((f, h))

    candidatos.sort(key=lambda x: x[0])
    proximo_fecha, proximo_h = candidatos[0]
    dias = (proximo_fecha - hoy).days

    if dias == 0:
        tiempo_str = "¡Hoy es feriado!"
    elif dias == 1:
        tiempo_str = "¡Mañana es feriado!"
    else:
        tiempo_str = f"Faltan {dias} días (el {proximo_fecha.strftime('%d/%m/%Y')})"

    return (
        f"📅 **PRÓXIMO FERIADO OFICIAL EN CHILE**\n\n"
        f"• **Festividad**: {proximo_h['nombre']}\n"
        f"• **Fecha**: {proximo_fecha.strftime('%d de %B de %Y')}\n"
        f"• **Tipo**: {proximo_h['tipo']}\n"
        f"• **Estado**: {tiempo_str}"
    )


def get_holidays_summary() -> str:
    """Lista los feriados del año en curso con indicación de días restantes."""
    hoy = datetime.date.today()
    año = hoy.year

    lineas = [f"📅 **CALENDARIO DE FERIADOS EN CHILE ({año})**\n"]
    for h in CHILE_HOLIDAYS:
        f = datetime.date(año, h["mes"], h["dia"])
        dias = (f - hoy).days
        if dias < 0:
            status = "✓ Pasado"
        elif dias == 0:
            status = "🎉 ¡Hoy!"
        else:
            status = f"en {dias} días"

        lineas.append(f"• **{h['dia']:02d}/{h['mes']:02d}** - {h['nombre']} ({status})")

    return "\n".join(lineas)
