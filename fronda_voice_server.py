"""
Fronda 1.0 - Servidor de Voz Neural, Orquestador de Skills y Memoria Viva
Expone la interfaz web, integra Ollama local con el modelo 'fronda'
y maneja síntesis neural asíncrona con edge-tts.
Puerto: 5176
"""
import os
import sys
import json
import asyncio
import tempfile
import threading
import urllib.request
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Importar módulos propios de Fronda 1.0
from fronda_memory import memory_manager
import fronda_skills
from fronda_bridge import FrondaBridge

bridge       = FrondaBridge()
VOICE        = "es-ES-AlvaroNeural"
OLLAMA_API   = "http://127.0.0.1:11434/api/chat"
MODEL        = "frondabrick"
FALLBACK_MODEL = "qwen2.5-coder:1.5b"
PORT         = 5176
GUI_FILE     = Path(__file__).parent / "fronda_voice_gui.html"

# ─── Estado global ───────────────────────────────────────────────────────────
_lock         = threading.Lock()
is_speaking   = False
is_processing = False

def _stop_audio():
    """Detiene cualquier reproducción de audio en curso."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception:
        pass

def _play_audio_thread(text: str):
    """Genera y reproduce TTS en un hilo separado no bloqueante."""
    global is_speaking
    try:
        import edge_tts
        import pygame

        clean = (text.replace("```", "")
                     .replace("`", "")
                     .replace("*", "")
                     .replace("#", "")
                     .replace("_", "")
                     .replace("•", "")
                     .strip())
        if not clean:
            return

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name

        # Sintetizar audio con Edge TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        comm = edge_tts.Communicate(clean, VOICE, rate="+4%", pitch="-1Hz")
        loop.run_until_complete(comm.save(path))
        loop.close()

        # Reproducir con pygame
        with _lock:
            is_speaking = True

        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            import time; time.sleep(0.04)
        pygame.mixer.quit()

    except Exception as e:
        print(f"[Audio Error]: {e}")
    finally:
        with _lock:
            is_speaking = False
        try:
            if 'path' in locals():
                os.remove(path)
        except Exception:
            pass

def speak(text: str):
    """Lanza reproducción de voz neural sin congelar el servidor HTTP."""
    _stop_audio()
    t = threading.Thread(target=_play_audio_thread, args=(text,), daemon=True)
    t.start()

def query_ollama(messages: list, system_context: str = "") -> str:
    """Envía la solicitud a Ollama local con inyección de memoria."""
    # Insertar el contexto de memoria al inicio como mensaje del sistema
    full_messages = []
    if system_context:
        full_messages.append({"role": "system", "content": system_context})
    
    # Agregar el resto de los mensajes de la conversación
    for m in messages:
        if m.get("role") != "system":
            full_messages.append(m)

    payload = json.dumps({
        "model": MODEL,
        "messages": full_messages,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_API,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
    except Exception as e:
        # Fallback si el modelo fronda aún se está compilando o no responde
        print(f"[Ollama Advertencia]: Error con modelo '{MODEL}': {e}. Probando fallback a '{FALLBACK_MODEL}'...")
        try:
            payload_fallback = json.dumps({
                "model": FALLBACK_MODEL,
                "messages": full_messages,
                "stream": False
            }).encode("utf-8")
            req_fb = urllib.request.Request(
                OLLAMA_API, data=payload_fallback, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req_fb, timeout=120) as res_fb:
                data_fb = json.loads(res_fb.read().decode("utf-8"))
                return data_fb.get("message", {}).get("content", "")
        except Exception as e2:
            return f"Error al comunicar con Ollama: {e2}"

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class FrondaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silenciar logs ruidosos en terminal

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/fronda_voice_gui.html", "/jarvis_voice_gui.html"):
            try:
                content = GUI_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self._cors()
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, f"{GUI_FILE.name} no encontrado")
        elif self.path == "/api/status":
            with _lock:
                data = {
                    "speaking": is_speaking,
                    "processing": is_processing,
                    "voice": VOICE,
                    "model": MODEL
                }
            self._json(200, data)
        elif self.path == "/api/memory":
            self._json(200, memory_manager.get_data())
        elif self.path == "/api/telemetry":
            self._json(200, fronda_skills.get_system_telemetry())
        else:
            self.send_error(404)

    def do_POST(self):
        global is_processing
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length).decode("utf-8")

        if self.path == "/api/chat":
            try:
                req = json.loads(body)
                messages = req.get("messages", [])
                speak_response = req.get("speak", True)

                # Extraer último mensaje de usuario
                last_user_text = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user_text = m.get("content", "")
                        break

                with _lock:
                    is_processing = True

                # 1. Evaluar si dispara un Skill directo
                has_skill, skill_name, skill_result = fronda_skills.dispatch_skill_intent(last_user_text)
                
                # Si el skill es una acción de hardware o app (ej: volumen, mute, abrir app, comando WSL), responder de inmediato
                if has_skill and skill_name in ["telemetry", "volume", "mute", "unmute", "brightness", "screenshot", "launch_app", "wsl_command"]:
                    response = skill_result
                else:
                    # 2. Inyectar contexto dinámico de memoria y/o resultados de búsqueda web/telemetría
                    system_context = memory_manager.get_system_context(last_user_text)
                    if has_skill and skill_result:
                        system_context += f"\n\n[DATOS OBTENIDOS POR SKILL '{skill_name}']:\n{skill_result}\nIntegra estos datos en tu respuesta de forma directa como Fronda 1.0."

                    response = query_ollama(messages, system_context=system_context)

                with _lock:
                    is_processing = False

                # 3. Aprendizaje continuo asíncrono sobre David
                memory_manager.record_interaction()
                if last_user_text and response:
                    memory_manager.extract_memories_async(last_user_text, response)

                # 4. Síntesis por voz
                if speak_response and response:
                    speak(response)

                self._json(200, {
                    "response": response,
                    "voice": VOICE,
                    "skill_executed": skill_name if has_skill else None
                })

            except Exception as e:
                with _lock:
                    is_processing = False
                self._json(500, {"error": str(e)})

        elif self.path == "/api/stop":
            _stop_audio()
            with _lock:
                is_speaking = False
            self._json(200, {"stopped": True})

        elif self.path == "/api/speak":
            try:
                req  = json.loads(body)
                text = req.get("text", "")
                if text:
                    speak(text)
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif self.path == "/api/memory/add":
            try:
                req = json.loads(body)
                content = req.get("content", "")
                category = req.get("category", "experiencia")
                if content:
                    mem = memory_manager.add_memory(content, category=category)
                    self._json(200, {"ok": True, "memory": mem})
                else:
                    self._json(400, {"error": "Contenido vacío"})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self.send_error(404)

    def _json(self, code: int, data: dict):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("       FRONDA 1.0 - CLON DIGITAL DE DAVID GALLEGUILLOS")
    print(f"       Modelo  : {MODEL}")
    print(f"       Voz     : {VOICE}")
    print(f"       Servidor: http://127.0.0.1:{PORT}")
    print("=" * 60)

    # Anuncio de inicio
    threading.Thread(
        target=_play_audio_thread,
        args=("Fronda 1.0 en línea. Núcleo de memoria y clon digital activos, David.",),
        daemon=True
    ).start()

    server = ThreadingHTTPServer(("127.0.0.1", PORT), FrondaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Fronda 1.0] Cerrando sistemas y guardando memoria...")
