"""
Fronda 1.0 - Orquestador de Skills y Herramientas
Maneja control de hardware, sistema operativo, búsquedas web y telemetría.
- Sin código duplicado: usa skills/math_engine.py y skills/system_engine.py
- Dispatcher dinámico con registro de skills
- Valores configurables desde config.py
- Keywords del dispatcher cargadas desde skills/dispatcher_keywords.json (C11)
"""
import os
import re
import json
import datetime
import subprocess
from pathlib import Path
from typing import Tuple, List, Dict

import config
from fronda_logger import get_logger

# ─── Importar desde módulos canónicos (sin duplicación) ──────────────────────
from skills.math_engine import evaluate_math_expression
from skills.system_engine import get_system_telemetry, get_os_info
from skills.research_engine import synthesize_research, search_wikipedia, search_github
from skills.hardware_analyzer import get_deep_hardware_analysis
from skills.weather_engine import get_current_weather
from skills.pdf_engine import extract_text_from_pdf
from skills.media_engine import convert_media_file
from skills.cognitive_graph import generate_cognitive_graph
from skills.calendar_engine import get_september_18_info, get_next_holiday, get_holidays_summary
from skills.vision_engine import analyze_screen_vision
from core.governor import governor

log = get_logger("fronda.skills")

# ─── Cargador de Keywords multi-idioma (C11) ──────────────────────────────────
_KEYWORDS_FILE = Path(__file__).parent / "skills" / "dispatcher_keywords.json"
_keywords_cache: Dict[str, Dict] = {}

# Fallback en español (por si no existe el JSON)
_KW_FALLBACK: Dict[str, list] = {
    "time_date":      ["qué hora es", "que hora es", "la hora", "qué día es", "qué fecha es", "fecha actual"],
    "telemetry":      ["diagnóstico", "diagnostico", "estado del sistema", "telemetria", "telemetría", "uso de ram", "uso de cpu"],
    "os_info":        ["sistema operativo", "qué sistema tengo", "que sistema tengo", "versón de windows"],
    "skills_summary": ["qué puedes hacer", "que puedes hacer", "tus skills", "capacidades", "qué sabes hacer"],
    "mute":           ["silencia", "mutear", "mutea"],
    "unmute":         ["desmutea", "reactiva el audio", "quitar silencio"],
    "screenshot":     ["captura de pantalla", "toma una captura", "screenshot"],
    "screen_vision":  ["mira mi pantalla", "qué hay en mi pantalla", "analiza mi pantalla", "qué ves en mi pantalla", "lee este error"],
    "wsl_prefix":     ["ejecuta en wsl", "corre en linux", "comando wsl", "bash"],
}

def _load_keywords(lang: str = "es") -> Dict[str, list]:
    """Carga el diccionario de keywords para el idioma solicitado."""
    global _keywords_cache
    if lang in _keywords_cache:
        return _keywords_cache[lang]
    try:
        if _KEYWORDS_FILE.exists():
            with open(_KEYWORDS_FILE, "r", encoding="utf-8") as f:
                all_kw = json.load(f)
            _keywords_cache[lang] = all_kw.get(lang, all_kw.get("es", _KW_FALLBACK))
        else:
            _keywords_cache[lang] = _KW_FALLBACK
    except Exception as e:
        log.warning(f"No se pudo cargar keywords para idioma '{lang}': {e}")
        _keywords_cache[lang] = _KW_FALLBACK
    return _keywords_cache[lang]

def _kw(skill: str) -> list:
    """Obtiene las keywords de un skill en el idioma configurado."""
    lang = config.get().user.dispatcher_lang
    return _load_keywords(lang).get(skill, [])


# ─── Control de Volumen ──────────────────────────────────────────────────────
def set_system_volume(percent: int) -> str:
    """Ajusta el volumen maestro de Windows (0-100%)."""
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        pct = max(0, min(100, int(percent)))
        volume.SetMasterVolumeLevelScalar(pct / 100.0, None)
        return f"Volumen ajustado al {pct}%."
    except Exception as e:
        return f"Error al cambiar volumen: {e}"


def mute_system_volume(mute: bool = True) -> str:
    """Mutea o desmutea el volumen de Windows."""
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMute(1 if mute else 0, None)
        return "Audio silenciado." if mute else "Audio reactivado."
    except Exception as e:
        return f"Error con mute: {e}"


# ─── Control de Brillo ───────────────────────────────────────────────────────
def set_screen_brightness(percent: int) -> str:
    """Ajusta el brillo de la pantalla."""
    try:
        import screen_brightness_control as sbc
        pct = max(10, min(100, int(percent)))
        sbc.set_brightness(pct)
        return f"Brillo ajustado al {pct}%."
    except Exception as e:
        return f"No se pudo ajustar el brillo en este monitor: {e}"


# ─── Captura de Pantalla ─────────────────────────────────────────────────────
def take_screenshot(filename: str = "fronda_capture.png") -> str:
    """Captura la pantalla y guarda la imagen."""
    try:
        import mss
        output_dir = config.captures_dir()
        target = output_dir / filename
        with mss.mss() as sct:
            sct.shot(output=str(target))
        return f"Captura de pantalla guardada en: {target.name}"
    except Exception as e:
        return f"Error al tomar captura: {e}"


# ─── Búsqueda Web ────────────────────────────────────────────────────────────
def search_duckduckgo(query: str, max_results: int = 3) -> str:
    """Busca en tiempo real en la web usando DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No se encontraron resultados web relevantes."
            return "\n".join(f"• {r.get('title')}: {r.get('body')}" for r in results)
    except Exception as e:
        return f"Error al realizar búsqueda web: {e}"


# ─── Lanzador de Aplicaciones ────────────────────────────────────────────────
_WINDOWS_APPS = {
    "calculadora": "calc.exe", "calc": "calc.exe",
    "bloc de notas": "notepad.exe", "notepad": "notepad.exe",
    "administrador de tareas": "taskmgr.exe", "taskmgr": "taskmgr.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "explorador": "explorer.exe",
    "paint": "mspaint.exe",
    "configuración": "ms-settings:",
}

def open_system_app(app_name: str) -> str:
    """Abre herramientas de Windows de forma segura."""
    key = app_name.lower().strip()
    executable = _WINDOWS_APPS.get(key)
    if executable:
        try:
            subprocess.Popen(executable, shell=True)
            return f"Ejecutando {executable} en el sistema."
        except Exception as e:
            return f"Error al abrir {app_name}: {e}"
    return f"Aplicación '{app_name}' no reconocida en el catálogo de Fronda."


# ─── Skills Summary dinámico ──────────────────────────────────────────────────
def _build_skills_summary() -> str:
    """Construye dinámicamente la lista de capacidades disponibles."""
    cfg = config.get()
    nickname = cfg.user.nickname
    has_wsl = _wsl_available()

    skills_list = [
        "• Control del Sistema: Ajustar volumen, brillo, silenciar audio y capturar pantallas.",
        "• Diagnóstico de Hardware: Telemetría en tiempo real de CPU, RAM, disco y batería.",
        "• Operaciones de Ingeniería: Revisión y generación de código en Rust, Python y PowerShell.",
        "• Telecomunicaciones y Redes: Asistencia en arquitectura de protocolos IPv7 / VPI7.",
        "• Mundo Exterior: Búsqueda web en vivo sin API keys vía DuckDuckGo.",
        "• Investigación Profunda: Consultas multi-fuente en Wikipedia, GitHub y noticias web.",
        "• Cálculo Científico: Aritmética, trigonometría, logaritmos y raíces de forma exacta.",
        "• Visión Multimodal: Análisis visual en tiempo real de tu pantalla usando Moondream.",
        "• Memoria Viva: Aprendizaje incremental de tu historia y proyectos.",
        "• Hora y Fecha: Información temporal en tiempo real.",
    ]
    if has_wsl:
        skills_list.append("• Ejecución Nativa en Linux: Correr comandos en Ubuntu WSL 2.")

    header = f"Como Fronda 1.0 (tu clon digital en Windows + WSL 2), puedo:\n\n"
    return header + "\n".join(skills_list)


def _wsl_available() -> bool:
    """Detecta si WSL2 está disponible en el sistema."""
    if not config.get().wsl.enabled:
        return False
    try:
        res = subprocess.run(
            ["wsl.exe", "--status"],
            capture_output=True, text=True, timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


# ─── Dispatcher de Skills ─────────────────────────────────────────────────────
def dispatch_skill_intent(user_text: str) -> Tuple[bool, str, str]:
    """
    Analiza si el mensaje del usuario solicita un skill directo.
    Retorna: (fue_skill, nombre_skill, resultado_texto)
    """
    text = user_text.lower().strip()
    cfg  = config.get()
    nickname = cfg.user.nickname

    # ── 0. Hora y Fecha ──────────────────────────────────────────────────────
    if any(k in text for k in (
        _kw("time_date") or [
            "qué hora es", "que hora es", "la hora", "dime la hora",
            "qué día es", "que dia es", "qué fecha es", "que fecha es"
        ]
    )):
        now = datetime.datetime.now()
        hora_str   = now.strftime("%H:%M")
        fecha_str  = now.strftime("%d/%m/%Y")
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_semana = dias[now.weekday()]
        return True, "time_date", f"Son las {hora_str} del {dia_semana}, {fecha_str}."

    # ── 1. Telemetría del Sistema ───────────────────────────────────────────────
    if any(k in text for k in (
        _kw("telemetry") or [
            "diagnóstico", "diagnostico", "estado del sistema", "estado del pc",
            "telemetria", "telemetría", "uso de ram", "uso de cpu",
            "cómo está el pc", "como esta el pc",
        ]
    )):
        data = get_system_telemetry()
        if "error" in data:
            return True, "telemetry", f"Error de diagnóstico: {data['error']}"
        res = (
            f"Diagnóstico en tiempo real del equipo de {nickname}:\n"
            f"• CPU: {data.get('cpu_percent')}% en uso\n"
            f"• Memoria RAM: {data.get('ram_used_gb')} GB usados de "
            f"{data.get('ram_total_gb')} GB ({data.get('ram_percent')}%)\n"
            f"• Almacenamiento: {data.get('disk_free_gb')} GB libres "
            f"({data.get('disk_percent')}% ocupado)"
        )
        if "battery_percent" in data:
            res += (
                f"\n• Batería: {data.get('battery_percent')}% "
                f"({'Cargando' if data.get('power_plugged') else 'Descargando'})"
            )
        return True, "telemetry", res

    # ── 1.05 Sistema Operativo ────────────────────────────────────────────────
    if any(k in text for k in (
        _kw("os_info") or [
            "sistema operativo", "qué sistema tengo", "que sistema tengo",
            "qué os tengo", "que os tengo", "versión de windows", "version de windows"
        ]
    )):
        return True, "os_info", get_os_info()

    # ── 1.06 Análisis Profundo de Computador / Hardware ───────────────────────
    if any(k in text for k in (
        _kw("hardware_analysis") or [
            "analiza mi computador", "analizar mi computador", "analiza mi pc",
            "analizar mi pc", "analiza mi equipo", "especificaciones de mi pc",
            "hardware de mi pc", "qué computador tengo", "que computador tengo"
        ]
    )):
        return True, "hardware_analysis", get_deep_hardware_analysis()

    # ── 1.07 Clima y Meteorología en Tiempo Real ──────────────────────────────
    if any(k in text for k in (
        _kw("weather") or [
            "cómo va estar el clima", "como va estar el clima", "cómo va a estar el clima",
            "el clima hoy", "pronóstico del tiempo", "pronostico del tiempo", "qué clima hace"
        ]
    )):
        # Extraer ciudad si se menciona ej "clima en Madrid"
        city = ""
        m_city = re.search(r"(?:clima|tiempo)\s+(?:en|de)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)", text)
        if m_city:
            city = m_city.group(1).strip()
        return True, "weather", get_current_weather(city)

    # ── 1.08 Grafo de Memoria Cognitiva ───────────────────────────────────────
    if any(k in text for k in (
        _kw("cognitive_graph") or [
            "grafo de tu memoria", "grafo de memoria", "grafo cognitivo",
            "hazme un grafo", "hazme un grafo de tu memoria cognitiva", "mapa de tu memoria"
        ]
    )):
        return True, "cognitive_graph", generate_cognitive_graph()

    # ── 1.09 Lector de Documentos PDF ─────────────────────────────────────────
    if any(k in text for k in (_kw("pdf_reader") or ["leer pdf", "lee el pdf", "lee este pdf", "extraer pdf"])):
        # Buscar archivo .pdf mencionado en el texto o buscar el primer pdf en el directorio
        pdf_match = re.search(r"([a-zA-Z0-9_\-\.\s\\\/]+\.pdf)", text, re.IGNORECASE)
        pdf_target = pdf_match.group(1).strip() if pdf_match else ""
        if not pdf_target or not os.path.exists(pdf_target):
            # Buscar si hay un PDF en el directorio actual
            pdfs = [f for f in os.listdir(".") if f.endswith(".pdf")]
            if pdfs:
                pdf_target = pdfs[0]
        if pdf_target and os.path.exists(pdf_target):
            return True, "pdf_reader", extract_text_from_pdf(pdf_target)
        return True, "pdf_reader", "Por favor indica el nombre o ruta del archivo PDF que deseas que lea."

    # ── 1.10 Conversión Multimedia (MKV a MP4) ────────────────────────────────
    if any(k in text for k in (_kw("media_convert") or ["convierte este archivo de video", "convertir mkv a mp4", "convertir video"])):
        media_match = re.search(r"([a-zA-Z0-9_\-\.\s\\\/]+\.(?:mkv|avi|mov|mp4|webm))", text, re.IGNORECASE)
        media_target = media_match.group(1).strip() if media_match else ""
        if media_target and os.path.exists(media_target):
            return True, "media_convert", convert_media_file(media_target, target_format="mp4")
        return True, "media_convert", "Para convertir video con ffmpeg, especifica la ruta del archivo (ejemplo: 'convierte video.mkv a mp4')."

    # ── 1.11 Fiestas Patrias / 18 de Septiembre ───────────────────────────────
    if any(k in text for k in (
        _kw("september_18") or [
            "18 de septiembre", "dieciocho de septiembre", "fiestas patrias",
            "qué se celebra el 18", "que se celebra el 18", "cuánto falta para el 18", "cuanto falta para el 18"
        ]
    )):
        return True, "september_18", get_september_18_info()

    # ── 1.12 Próximo Feriado y Calendario ─────────────────────────────────────
    if any(k in text for k in (
        _kw("holidays") or [
            "próximo feriado", "proximo feriado", "cuándo es feriado", "cuando es feriado",
            "feriados de este año", "calendario de feriados", "qué feriado viene"
        ]
    )):
        return True, "holidays", get_next_holiday()

    # ── 1.13 Visión por Computadora / Multimodalidad ──────────────────────────
    if any(k in text for k in (
        _kw("screen_vision") or [
            "mira mi pantalla", "qué hay en mi pantalla", "que hay en mi pantalla",
            "analiza lo que estoy viendo", "analiza mi pantalla", "analizar mi pantalla",
            "lee este error", "qué ves en mi pantalla", "que ves en mi pantalla",
            "visión de pantalla", "vision de pantalla", "analiza la imagen"
        ]
    )):
        return True, "screen_vision", analyze_screen_vision(user_text)

    # ── 1.1 Skills / Capacidades ──────────────────────────────────────────────
    if any(k in text for k in (
        _kw("skills_summary") or [
            "qué puedes hacer", "que puedes hacer", "cuales son tus habilidades",
            "cuáles son tus habilidades", "tus skills", "qué sabes hacer",
            "que sabes hacer", "capacidades"
        ]
    )):
        return True, "skills_summary", _build_skills_summary()

    # ── 1.2 Cálculos Matemáticos ─────────────────────────────────────────────
    math_candidate = None
    math_patterns = [
        r"(?:cu[aá]nto\s+es|calcula|calcular|resuelve|dime\s+cu[aá]l\s+es\s+el\s+resultado\s+de)\s+"
        r"([0-9\.\s\+\-\*\/\^\(\)\%x×÷a-z]+)",
        r"(?:ra[ií]z\s+(?:c[uú]bica|cuadrada)?\s+de\s+[0-9\.]+)",
        r"^[0-9\.\s\+\-\*\/\^\(\)]+$"
    ]
    for p in math_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            math_candidate = m.group(1) if m.groups() else m.group(0)
            break

    if math_candidate:
        ok, res_val = evaluate_math_expression(math_candidate)
        if ok:
            return True, "math_calc", f"El resultado de {math_candidate.strip()} es {res_val}."

    # ── 2. Control de Volumen ─────────────────────────────────────────────────
    vol_match = re.search(
        r"(?:pon|ajusta|sube|baja)?\s*(?:el\s+)?volumen\s+(?:a|al)\s+(\d{1,3})%?", text
    )
    if vol_match:
        return True, "volume", set_system_volume(int(vol_match.group(1)))

    if any(k in text for k in (_kw("mute") or ["silencia", "mutear", "mutea"])):
        return True, "mute", mute_system_volume(True)

    if any(k in text for k in (_kw("unmute") or ["desmutea", "reactiva el audio", "quitar silencio"])):
        return True, "unmute", mute_system_volume(False)

    # ── 3. Control de Brillo ──────────────────────────────────────────────────
    bri_match = re.search(
        r"(?:pon|ajusta|sube|baja)?\s*(?:el\s+)?brillo\s+(?:a|al)\s+(\d{1,3})%?", text
    )
    if bri_match:
        return True, "brightness", set_screen_brightness(int(bri_match.group(1)))

    # ── 4. Captura de Pantalla ────────────────────────────────────────────────
    if any(k in text for k in (_kw("screenshot") or ["captura de pantalla", "toma una captura", "screenshot"])):
        return True, "screenshot", take_screenshot()

    # ── 5. Investigación Multi-Fuente y Búsqueda Web (Inspirado en CynCo) ───
    search_patterns = [
        r"(?:busca\s+en\s+(?:la\s+web|internet|google|duckduckgo)|busca\s+noticias\s+de|"
        r"investiga\s+en\s+la\s+web|busca\s+informaci[oó]n\s+sobre|investiga|averigua|busca\s+sobre|busca)\s+(.+)",
        r"(?:cu[aá]l\s+es\s+el\s+precio\s+de|cotizaci[oó]n\s+de|precio\s+actual\s+de)\s+(.+)",
        r"(?:noticias\s+sobre|noticias\s+de)\s+(.+)",
        r"(?:qu[eé]\s+dice\s+wikipedia\s+de|resumen\s+de|biograf[ií]a\s+de)\s+(.+)",
        r"(?:busca\s+en\s+github|repositorio\s+de|proyectos\s+de)\s+(.+)"
    ]
    for sp in search_patterns:
        search_match = re.search(sp, text, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            if len(query) > 2 and not re.match(r"^[0-9\.\s\+\-\*\/\^\(\)]+$", query):
                pref = "auto"
                if "github" in text or "repositorio" in text:
                    pref = "github"
                elif "wikipedia" in text or "biografía" in text or "biografia" in text:
                    pref = "wiki"

                if not governor.is_tool_allowed("deep_research"):
                    return True, "deep_research", "El servicio de investigación externa está en cuarentena preventiva temporal (Regla C2)."

                try:
                    res = synthesize_research(query, preferred_source=pref)
                    governor.record_tool_result("deep_research", success=True)
                    return True, "deep_research", res
                except Exception as e:
                    governor.record_tool_result("deep_research", success=False, error_msg=str(e))
                    return True, "deep_research", f"Error durante la investigación: {e}"

    # ── 6. Lanzar aplicaciones ────────────────────────────────────────────────
    open_match = re.search(
        r"(?:abre|abrir|ejecuta|lanzar)\s+"
        r"(la\s+calculadora|el\s+bloc\s+de\s+notas|el\s+administrador\s+de\s+tareas|"
        r"powershell|la\s+terminal|calc|notepad|taskmgr|paint|configuraci[oó]n)",
        text
    )
    if open_match:
        target_app = open_match.group(1).replace("la ", "").replace("el ", "")
        return True, "launch_app", open_system_app(target_app)

    # ── 7. Comandos WSL ───────────────────────────────────────────────────────
    wsl_match = re.search(
        r"(?:ejecuta\s+en\s+wsl|corre\s+en\s+linux|comando\s+wsl|terminal\s+linux|bash)\s*:\s*(.+)",
        text, re.IGNORECASE
    )
    if not wsl_match:
        wsl_match = re.search(
            r"(?:ejecuta|corre)\s+en\s+(?:wsl|linux|ubuntu)\s+(.+)", text, re.IGNORECASE
        )
    if wsl_match and config.get().wsl.enabled:
        cmd = wsl_match.group(1).strip()
        if not governor.is_tool_allowed("wsl_command"):
            return True, "wsl_command", "El subsistema WSL está temporalmente aislado por el gobernador cibernético (Regla C2)."

        try:
            from fronda_bridge import FrondaBridge
            bridge = FrondaBridge()
            res = bridge.run_wsl_command(cmd)
            stdout = res.get("stdout", "")
            stderr = res.get("stderr", "")
            code   = res.get("exit_code", 0)

            if code == 0:
                governor.record_tool_result("wsl_command", success=True)
            else:
                governor.record_tool_result("wsl_command", success=False, error_msg=stderr or f"Exit {code}")

            output = f"Comando ejecutado en WSL [Exit: {code}]:\n"
            if stdout:
                output += f"```bash\n{stdout}\n```"
            if stderr:
                output += f"\nErrores:\n```bash\n{stderr}\n```"
            return True, "wsl_command", output
        except Exception as e:
            governor.record_tool_result("wsl_command", success=False, error_msg=str(e))
            return True, "wsl_command", f"Error al ejecutar en WSL: {e}"

    return False, "", ""


# ─── Registro de Solicitudes de Habilidades ──────────────────────────────────
SKILLS_REQUESTS_FILE = config.skills_requests_file()

LIMITATION_PATTERNS = [
    r"\bno\s+s[eé]\b",
    r"\bno\s+puedo\b",
    r"\bno\s+tengo\s+(?:la\s+capacidad|acceso|la\s+habilidad|permiso|instalado|soporte|informaci[oó]n|herramientas?)\b",
    r"\bno\s+dispongo\s+de\b",
    r"\bno\s+est[aá]\s+a\s+mi\s+alcance\b",
    r"\bno\s+me\s+es\s+posible\b",
    r"\bno\s+poseo\b",
    r"\bno\s+cuento\s+con\b"
]


def check_for_skill_limitation(user_prompt: str, bot_response: str) -> dict | None:
    """
    Analiza si la respuesta del modelo expresa una limitación técnica.
    Si es así, genera un ticket de solicitud para el Asistente Desarrollador.
    """
    if not bot_response:
        return None

    resp_lower = bot_response.lower()
    if not any(re.search(pat, resp_lower) for pat in LIMITATION_PATTERNS):
        return None

    prompt_clean = user_prompt.strip()
    ticket_id    = f"REQ-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    category     = "general"
    p_lower      = prompt_clean.lower()

    if any(k in p_lower for k in ["pdf", "excel", "csv", "doc", "archivo", "leer", "texto"]):
        category = "procesamiento_archivos"
    elif any(k in p_lower for k in ["clima", "tiempo", "temperatura", "meteorología"]):
        category = "clima_meteorologia"
    elif any(k in p_lower for k in ["audio", "video", "youtube", "música", "mp3", "sonido"]):
        category = "multimedia"
    elif any(k in p_lower for k in ["red", "ip", "ipv7", "ping", "puerto", "socket", "servidor"]):
        category = "redes_telecomunicaciones"
    elif any(k in p_lower for k in ["pantalla", "raton", "teclado", "click", "ventana", "abrir"]):
        category = "automatizacion_os"

    ticket = {
        "id":               ticket_id,
        "fecha":            datetime.datetime.now().isoformat(),
        "categoria":        category,
        "peticion_usuario": prompt_clean,
        "respuesta_original": bot_response,
        "estado":           "PENDIENTE_DESARROLLO",
        "descripcion":      f"Habilidad requerida para responder: '{prompt_clean}'",
        "responsable":      "Asistente Desarrollador (Antigravity)",
        "notas":            "Pendiente de codificación e instalación de librerías."
    }

    try:
        solicitudes: list = []
        if SKILLS_REQUESTS_FILE.exists():
            with open(SKILLS_REQUESTS_FILE, "r", encoding="utf-8") as f:
                try:
                    solicitudes = json.load(f)
                except Exception:
                    solicitudes = []

        # Evitar duplicados pendientes con la misma petición exacta
        if not any(
            s.get("peticion_usuario", "").lower() == prompt_clean.lower()
            for s in solicitudes
            if s.get("estado") == "PENDIENTE_DESARROLLO"
        ):
            solicitudes.append(ticket)
            with open(SKILLS_REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump(solicitudes, f, indent=2, ensure_ascii=False)
            log.info(f"Ticket de solicitud creado: {ticket_id}")
    except Exception as e:
        log.error(f"No se pudo guardar la solicitud: {e}")

    return ticket


def get_skill_requests(filtro_estado: str = None) -> list[dict]:
    """Lee las solicitudes de habilidades guardadas."""
    if not SKILLS_REQUESTS_FILE.exists():
        return []
    try:
        with open(SKILLS_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if filtro_estado:
                return [d for d in data if d.get("estado") == filtro_estado]
            return data
    except Exception:
        return []


def update_skill_request(ticket_id: str, new_estado: str) -> bool:
    """Actualiza el estado de un ticket (ej: PENDIENTE → INSTALADO)."""
    if not SKILLS_REQUESTS_FILE.exists():
        return False
    try:
        with open(SKILLS_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            if item.get("id") == ticket_id:
                item["estado"] = new_estado
                item["fecha_actualizacion"] = datetime.datetime.now().isoformat()
                break
        else:
            return False
        with open(SKILLS_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log.error(f"Error al actualizar ticket {ticket_id}: {e}")
        return False


def delete_skill_request(ticket_id: str) -> bool:
    """Elimina un ticket de la lista."""
    if not SKILLS_REQUESTS_FILE.exists():
        return False
    try:
        with open(SKILLS_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        original_len = len(data)
        data = [item for item in data if item.get("id") != ticket_id]
        if len(data) == original_len:
            return False
        with open(SKILLS_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log.error(f"Error al eliminar ticket {ticket_id}: {e}")
        return False
