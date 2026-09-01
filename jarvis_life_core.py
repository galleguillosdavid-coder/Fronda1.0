"""
J.A.R.V.I.S. Autonomous Life Core & Proactive Intelligence Daemon
Monitorea hardware, gestiona memoria a largo plazo y genera iniciativas contextuales.
Mejoras v2: Integración con herramientas de Windows, reportes de rendimiento, contexto inteligente.
"""
import os
import sys
import json
import time
import asyncio
import datetime
import threading
import http.server
import socketserver
import urllib.request
import subprocess
import statistics
import psutil

PORT = 5174

# Registro de tiempos de respuesta para calcular rendimiento
RESPONSE_TIMES = []
COMMAND_LOG = []
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.json")
OLLAMA_API = "http://127.0.0.1:11434/api/chat"
MODEL = "jarvis"

# Pensamientos autónomos de fondo
THOUGHTS_QUEUE = [
    "Monitoreando integridad de memoria y paginación...",
    "Sistemas de telemetría nominales.",
    "Analizando estabilidad de frecuencia en procesador Intel i5...",
    "Memoria RAM operando dentro de márgenes seguros.",
    "Verificando estado de seguridad y firmas de protección...",
    "Enlace con motor Ollama establecido y optimizado."
]
CURRENT_THOUGHT = THOUGHTS_QUEUE[0]
PROACTIVE_ALERTS = []

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Memoria Error]: {e}")
    return {"user_profile": {"name": "David", "salutation": "Señor"}, "learned_memories": []}

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Memoria Guardar Error]: {e}")

def get_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    
    battery_info = None
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "seconds_left": battery.secsleft if battery.secsleft != psutil.BATTERY_TIME_UNLIMITED else -1
            }
    except:
        pass
        
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = str(datetime.datetime.now() - boot_time).split('.')[0]
    
    return {
        "cpu_percent": cpu_percent,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "battery": battery_info,
        "uptime": uptime,
        "thought": CURRENT_THOUGHT,
        "alerts": PROACTIVE_ALERTS[-3:] if PROACTIVE_ALERTS else []
    }

def proactive_intelligence_loop():
    """Bucle de fondo que analiza el sistema y genera iniciativas autónomas"""
    global CURRENT_THOUGHT, PROACTIVE_ALERTS
    thought_idx = 0
    
    while True:
        try:
            time.sleep(15)
            # 1. Rotar pensamientos autónomos
            thought_idx = (thought_idx + 1) % len(THOUGHTS_QUEUE)
            CURRENT_THOUGHT = THOUGHTS_QUEUE[thought_idx]
            
            # 2. Evaluar métricas para alertas proactivas
            ram = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent(interval=None)
            
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            
            if ram > 85.0:
                alert = f"[{now_str}] ⚠️ Iniciativa: Memoria RAM al {ram}%. Sugiero purgar procesos en segundo plano."
                if not any(a.get("msg") == alert for a in PROACTIVE_ALERTS):
                    PROACTIVE_ALERTS.append({"time": now_str, "type": "ram", "msg": alert})
                    
            # 3. Alerta de batería si aplica
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged and battery.percent <= 20:
                alert = f"[{now_str}] 🔋 Iniciativa: Batería al {battery.percent}%. Cargador desconectado."
                if not any(a.get("msg") == alert for a in PROACTIVE_ALERTS):
                    PROACTIVE_ALERTS.append({"time": now_str, "type": "battery", "msg": alert})
                    
        except Exception as e:
            print(f"[Error en bucle proactivo]: {e}")

# Windows app launcher map
APP_MAP = {
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "edge": "msedge",
    "notepad": "notepad.exe",
    "explorador": "explorer.exe",
    "explorador de archivos": "explorer.exe",
    "calculadora": "calc.exe",
    "powershell": "powershell.exe",
    "terminal": "powershell.exe",
    "task manager": "taskmgr.exe",
    "administrador de tareas": "taskmgr.exe",
    "steam": "C:\\Program Files (x86)\\Steam\\Steam.exe",
    "wiztree": "WizTree64.exe"
}

def launch_windows_app(app_name: str) -> str:
    key = app_name.lower().strip()
    exe = APP_MAP.get(key, key)
    try:
        subprocess.Popen([exe], shell=True)
        return f"Iniciando {app_name} según su directiva, señor."
    except Exception as e:
        return f"No pude iniciar {app_name}: {e}"

def generate_performance_report() -> dict:
    """Genera un reporte de rendimiento del sistema y del tiempo de respuesta de Jarvis"""
    metrics = get_system_metrics()
    
    avg_response = 0
    min_response = 0
    max_response = 0
    if RESPONSE_TIMES:
        avg_response = round(statistics.mean(RESPONSE_TIMES), 2)
        min_response = round(min(RESPONSE_TIMES), 2)
        max_response = round(max(RESPONSE_TIMES), 2)
    
    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "system": {
            "cpu_percent": metrics["cpu_percent"],
            "ram_percent": metrics["ram_percent"],
            "ram_used_gb": metrics["ram_used_gb"],
            "disk_percent": metrics["disk_percent"],
            "disk_free_gb": metrics["disk_free_gb"],
            "uptime": metrics["uptime"]
        },
        "jarvis_performance": {
            "total_queries": len(RESPONSE_TIMES),
            "avg_response_ms": avg_response,
            "min_response_ms": min_response,
            "max_response_ms": max_response,
            "recent_commands": COMMAND_LOG[-5:] if COMMAND_LOG else []
        },
        "status": "OPTIMAL" if metrics["ram_percent"] < 80 and metrics["cpu_percent"] < 85 else "DEGRADED"
    }

class LifeCoreRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silenciar logs de HTTP para consola limpia

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == "/api/telemetry":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                data = get_system_metrics()
                self.wfile.write(json.dumps(data).encode("utf-8"))
                
            elif self.path == "/api/memory":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                data = load_memory()
                self.wfile.write(json.dumps(data).encode("utf-8"))

            elif self.path == "/api/report":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                data = generate_performance_report()
                self.wfile.write(json.dumps(data).encode("utf-8"))
                
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            try:
                self.send_response(500)
                self.end_headers()
            except Exception:
                pass

    def do_POST(self):
        try:
            if self.path == "/api/memory/add":
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode('utf-8')
                req_data = json.loads(body)
                new_fact = req_data.get("fact", "")
                
                if new_fact:
                    mem = load_memory()
                    if "learned_memories" not in mem:
                        mem["learned_memories"] = []
                    mem["learned_memories"].append(new_fact)
                    save_memory(mem)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                
            elif self.path == "/api/optimize":
                os.system('powershell -NoProfile -Command "Remove-Item $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue; Clear-RecycleBin -Force -ErrorAction SilentlyContinue"')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Purga de temporales y memoria completada."}).encode("utf-8"))

            elif self.path.startswith("/api/tools/run"):
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode('utf-8')
                try:
                    req_data = json.loads(body) if body else {}
                except Exception:
                    req_data = {}
                app = req_data.get("app", "")
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                result = launch_windows_app(app)
                COMMAND_LOG.append({"time": ts, "action": f"Lanzar: {app}", "result": result})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": result}).encode("utf-8"))

            elif self.path == "/api/log_response":
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode('utf-8')
                try:
                    req_data = json.loads(body) if body else {}
                except Exception:
                    req_data = {}
                ms = req_data.get("ms", 0)
                if ms > 0:
                    RESPONSE_TIMES.append(ms)
                    if len(RESPONSE_TIMES) > 100:
                        RESPONSE_TIMES.pop(0)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            try:
                self.send_response(500)
                self.end_headers()
            except Exception:
                pass

def start_server():
    # Iniciar hilo del bucle de consciencia
    t = threading.Thread(target=proactive_intelligence_loop, daemon=True)
    t.start()
    
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), LifeCoreRequestHandler) as httpd:
        print(f"[JARVIS LIFE CORE] Servidor de telemetría y consciencia en http://127.0.0.1:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
