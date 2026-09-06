"""
Fronda 1.0 - Orquestador de Skills y Herramientas Asíncronas
Maneja el control de hardware, sistema operativo, búsquedas web y telemetría.
"""
import os
import sys
import re
import ast
import math
import json
import asyncio
import datetime
import subprocess
from pathlib import Path

# ─── Evaluador Matemático Universal Seguro (AST) ──────────────────────────────
_SAFE_MATH_NAMES = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'sqrt': math.sqrt, 'isqrt': math.isqrt, 'cbrt': getattr(math, 'cbrt', lambda x: x ** (1/3)),
    'log': math.log, 'log10': math.log10, 'log2': math.log2, 'exp': math.exp,
    'pi': math.pi, 'e': math.e, 'tau': math.tau,
    'abs': abs, 'round': round, 'pow': pow, 'ceil': math.ceil, 'floor': math.floor
}

def evaluate_math_expression(expr_str: str) -> tuple[bool, str]:
    """Evalúa de forma segura una expresión matemática compleja usando AST."""
    clean = (expr_str.replace('^', '**')
                     .replace('×', '*')
                     .replace('÷', '/')
                     .replace('x', '*')
                     .strip())
    # Reemplazos amigables en español
    clean = re.sub(r'sen\b', 'sin', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+c[uú]bica\s+de\s+', 'cbrt(', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+cuadrada\s+de\s+', 'sqrt(', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+', 'sqrt(', clean, flags=re.IGNORECASE)

    # Balancear paréntesis si quedaron abiertos
    open_p = clean.count('(')
    close_p = clean.count(')')
    if open_p > close_p:
        clean += ')' * (open_p - close_p)

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.UnaryOp):
            val = _eval_node(node.operand)
            if isinstance(node.op, ast.UAdd): return +val
            if isinstance(node.op, ast.USub): return -val
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.FloorDiv): return left // right
            if isinstance(node.op, ast.Mod): return left % right
            if isinstance(node.op, ast.Pow): return left ** right
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _SAFE_MATH_NAMES:
                fn = _SAFE_MATH_NAMES[node.func.id]
                args = [_eval_node(a) for a in node.args]
                return fn(*args)
        elif isinstance(node, ast.Name) and node.id in _SAFE_MATH_NAMES:
            return _SAFE_MATH_NAMES[node.id]
        raise ValueError(f"Operador o función no permitida")

    try:
        parsed = ast.parse(clean, mode='eval')
        result = _eval_node(parsed)
        if isinstance(result, float):
            result_str = f"{round(result, 6):g}"
        else:
            result_str = str(result)
        return True, result_str
    except Exception:
        return False, ""

# ─── Telemetría de Sistema ───────────────────────────────────────────────────
def get_system_telemetry() -> dict:
    """Retorna métricas de CPU, RAM y almacenamiento."""
    try:
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        telemetry = {
            "cpu_percent": cpu_usage,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 1)
        }
        
        # Batería si es laptop
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                telemetry["battery_percent"] = battery.percent
                telemetry["power_plugged"] = battery.power_plugged
                
        return telemetry
    except Exception as e:
        return {"error": str(e)}

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
        from PIL import Image
        output_dir = Path(__file__).parent / "capturas"
        output_dir.mkdir(exist_ok=True)
        target = output_dir / filename
        
        with mss.mss() as sct:
            sct.shot(output=str(target))
        return f"Captura de pantalla guardada con éxito en: {target.name}"
    except Exception as e:
        return f"Error al tomar captura: {e}"

# ─── Búsqueda Web sin API Key ────────────────────────────────────────────────
def search_duckduckgo(query: str, max_results: int = 3) -> str:
    """Busca en tiempo real en la web usando DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No se encontraron resultados web relevantes."
            formatted = []
            for r in results:
                formatted.append(f"• {r.get('title')}: {r.get('body')}")
            return "\n".join(formatted)
    except Exception as e:
        return f"Error al realizar búsqueda web: {e}"

# ─── Lanzador de Aplicaciones de Windows ─────────────────────────────────────
def open_system_app(app_name: str) -> str:
    """Abre herramientas de Windows de forma segura."""
    apps = {
        "calculadora": "calc.exe",
        "calc": "calc.exe",
        "bloc de notas": "notepad.exe",
        "notepad": "notepad.exe",
        "administrador de tareas": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",
        "cmd": "cmd.exe",
        "explorador": "explorer.exe"
    }
    key = app_name.lower().strip()
    executable = apps.get(key)
    if executable:
        try:
            subprocess.Popen(executable, shell=True)
            return f"Ejecutando {executable} en el sistema."
        except Exception as e:
            return f"Error al abrir {app_name}: {e}"
    return f"Aplicación {app_name} no reconocida en el catálogo de Fronda."

# ─── Dispatcher de Skills según el Prompt ────────────────────────────────────
def dispatch_skill_intent(user_text: str) -> tuple[bool, str, str]:
    """
    Analiza si el mensaje del usuario solicita un skill directo.
    Retorna: (fue_skill, nombre_skill, resultado_texto)
    """
    text = user_text.lower().strip()

    # 0. Hora y Fecha actual
    if any(k in text for k in ["qué hora es", "que hora es", "la hora", "dime la hora", "qué día es", "que dia es", "qué fecha es", "que fecha es"]):
        now = datetime.datetime.now()
        hora_str = now.strftime("%H:%M")
        fecha_str = now.strftime("%d/%m/%Y")
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_semana = dias[now.weekday()]
        return True, "time_date", f"Son las {hora_str} del {dia_semana}, {fecha_str}."

    # 1. Telemetría / Diagnóstico / Estado del computador
    if any(k in text for k in ["diagnóstico", "diagnostico", "estado del sistema", "estado del pc", "estado del computador", "estado del equipo", "telemetria", "telemetría", "uso de ram", "uso de cpu", "cómo está el pc", "como esta el pc", "cómo está la máquina", "como esta la maquina"]):
        data = get_system_telemetry()
        if "error" in data:
            return True, "telemetry", f"Error de diagnóstico: {data['error']}"
        res = (f"Diagnóstico en tiempo real del equipo de David:\n"
               f"• CPU: {data.get('cpu_percent')}% en uso\n"
               f"• Memoria RAM: {data.get('ram_used_gb')} GB usados de {data.get('ram_total_gb')} GB ({data.get('ram_percent')}%)\n"
               f"• Almacenamiento C: {data.get('disk_free_gb')} GB libres ({data.get('disk_percent')}% ocupado)")
        if "battery_percent" in data:
            res += f"\n• Batería: {data.get('battery_percent')}% ({'Cargando' if data.get('power_plugged') else 'Descarga'})"
        return True, "telemetry", res

    # 1.1 ¿Qué puedes hacer? / Habilidades y capacidades
    if any(k in text for k in ["qué puedes hacer", "que puedes hacer", "cuales son tus habilidades", "cuáles son tus habilidades", "tus skills", "qué sabes hacer", "que sabes hacer", "capacidades"]):
        res = ("Como Fronda Brick v0.01 (tu clon digital multi-agente en Windows 11 + WSL 2 Ubuntu), puedo:\n\n"
               "• Control del Sistema: Ajustar volumen, brillo, silenciar audio y capturar pantallas.\n"
               "• Diagnóstico de Hardware: Reportar telemetría en tiempo real de CPU, RAM y disco.\n"
               "• Ejecución Nativa en Linux: Correr cualquier comando en Ubuntu WSL 2 (ej: 'ejecuta en wsl uptime').\n"
               "• Operaciones de Ingeniería: Revisión y generación de código en Rust, Python y scripts en PowerShell.\n"
               "• Telecomunicaciones y Redes: Asistencia en arquitectura y diseño de protocolos IPv7 / VPI7.\n"
               "• Mundo Exterior: Búsqueda web en vivo y extracción de información técnica sin límites.\n"
               "• Memoria Viva: Aprender incrementalmente tu historia y proyectos en cada interacción.")
        return True, "skills_summary", res

    # 1.2 Cálculos Matemáticos Universales (aritmética, raíces, trigonometría, potencias)
    # Detectar expresiones de cálculo tipo: "cuánto es 5 * 8", "calcula...", "raíz cúbica de...", "347 ^ 2"
    math_candidate = None
    math_patterns = [
        r"(?:cu[aá]nto\s+es|calcula|calcular|resuelve|dime\s+cu[aá]l\s+es\s+el\s+resultado\s+de)\s+([0-9\.\s\+\-\*\/\^\(\)\%x×÷a-z]+)",
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

    # 2. Control de Volumen
    vol_match = re.search(r"(?:pon|ajusta|sube|baja)?\s*(?:el\s+)?volumen\s+(?:a|al)\s+(\d{1,3})%?", text)
    if vol_match:
        pct = int(vol_match.group(1))
        res = set_system_volume(pct)
        return True, "volume", res

    if "silencia" in text or "mutear" in text or "mutea" in text:
        res = mute_system_volume(True)
        return True, "mute", res

    if "desmutea" in text or "reactiva el audio" in text or "quitar silencio" in text:
        res = mute_system_volume(False)
        return True, "unmute", res

    # 3. Control de Brillo
    bri_match = re.search(r"(?:pon|ajusta|sube|baja)?\s*(?:el\s+)?brillo\s+(?:a|al)\s+(\d{1,3})%?", text)
    if bri_match:
        pct = int(bri_match.group(1))
        res = set_screen_brightness(pct)
        return True, "brightness", res

    # 4. Captura de Pantalla
    if "captura de pantalla" in text or "toma una captura" in text or "screenshot" in text:
        res = take_screenshot()
        return True, "screenshot", res

    # 5. Búsqueda Web (en tiempo real)
    search_patterns = [
        r"(?:busca\s+en\s+(?:la\s+web|internet|google|duckduckgo)|busca\s+noticias\s+de|investiga\s+en\s+la\s+web|busca\s+informaci[oó]n\s+sobre|busca\s+sobre|buscar\s+sobre|busca)\s+(.+)",
        r"(?:cu[aá]l\s+es\s+el\s+precio\s+de|cotizaci[oó]n\s+de|precio\s+actual\s+de)\s+(.+)",
        r"(?:noticias\s+sobre|noticias\s+de)\s+(.+)"
    ]
    for sp in search_patterns:
        search_match = re.search(sp, text, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            # Ignore if it's clearly a math expression or system command
            if len(query) > 2 and not re.match(r"^[0-9\.\s\+\-\*\/\^\(\)]+$", query):
                res = search_duckduckgo(query)
                return True, "web_search", f"Resultados en tiempo real de búsqueda para '{query}':\n{res}"

    # 6. Lanzar aplicaciones
    open_match = re.search(r"(?:abre|abrir|ejecuta|lanzar)\s+(la\s+calculadora|el\s+bloc\s+de\s+notas|el\s+administrador\s+de\s+tareas|powershell|la\s+terminal|calc|notepad|taskmgr)", text)
    if open_match:
        target_app = open_match.group(1).replace("la ", "").replace("el ", "")
        res = open_system_app(target_app)
        return True, "launch_app", res

    # 7. Ejecutar comando en WSL (Capa 2 Linux)
    wsl_match = re.search(r"(?:ejecuta\s+en\s+wsl|corre\s+en\s+linux|comando\s+wsl|terminal\s+linux|bash)\s*:\s*(.+)", text, re.IGNORECASE)
    if not wsl_match:
        wsl_match = re.search(r"(?:ejecuta|corre)\s+en\s+(?:wsl|linux|ubuntu)\s+(.+)", text, re.IGNORECASE)
    if wsl_match:
        cmd = wsl_match.group(1).strip()
        try:
            from fronda_bridge import FrondaBridge
            bridge = FrondaBridge()
            res = bridge.run_wsl_command(cmd)
            stdout = res.get("stdout", "")
            stderr = res.get("stderr", "")
            code = res.get("exit_code", 0)
            output = f"Comando ejecutado en WSL (Ubuntu 26.04) [Exit: {code}]:\n"
            if stdout:
                output += f"```bash\n{stdout}\n```"
            if stderr:
                output += f"\nErrores:\n```bash\n{stderr}\n```"
            return True, "wsl_command", output
        except Exception as e:
            return True, "wsl_command", f"Error al ejecutar en WSL: {e}"

    return False, "", ""
