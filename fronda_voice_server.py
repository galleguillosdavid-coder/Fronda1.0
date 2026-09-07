"""
Fronda 1.0 - Servidor de Voz Neural, Orquestador de Skills y Memoria Viva
- Puerto, modelo, voz y opciones leídos desde config.py
- Usa FrondaInferenceEngine como único motor de Ollama (sin duplicación)
- Watchdog de Ollama con auto-reinicio automático
- Race condition en audio corregida con lock
- Rate limiting básico por IP
- Indicador de desconexión en /api/status
- Tempfiles MP3 con limpieza robusta
"""
import os
import sys
import re
import json
import time
import asyncio
import tempfile
import threading
import collections
import urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import config
from fronda_logger import get_logger
from fronda_memory import memory_manager
import fronda_skills
from fronda_bridge import FrondaBridge
from core.engine import FrondaInferenceEngine
from core.governor import governor
from core.session_handoff import session_handoff

log = get_logger("fronda.server")

# ─── Configuración desde config.py ───────────────────────────────────────────
cfg           = config.get()
VOICE         = memory_manager.get_profile().get("voice_preferred", cfg.audio.voice)
PORT          = cfg.server.port
MODEL         = cfg.ollama.default_model
FALLBACK_MODEL = cfg.ollama.fallback_model
GUI_FILE      = config.gui_file()

# ─── Motor de inferencia unificado ───────────────────────────────────────────
engine = FrondaInferenceEngine()

# ─── Bridge WSL ──────────────────────────────────────────────────────────────
bridge = FrondaBridge()

# ─── Estado global ────────────────────────────────────────────────────────────
_lock              = threading.Lock()
is_speaking        = False
is_processing      = False
ollama_online      = True
_last_audio_bytes  = None
_audio_lock        = threading.Lock()   # lock dedicado para audio bytes
_audio_cache: dict = {}                 # {audio_id: bytes}
_audio_events: dict = {}                # {audio_id: threading.Event}
_audio_cache_lock  = threading.Lock()

# ─── Historial de telemetría (C13) ───────────────────────────────────────────
_TELEM_MAX_SAMPLES = 60
_telem_history: collections.deque = collections.deque(maxlen=_TELEM_MAX_SAMPLES)
_telem_lock = threading.Lock()

# ─── Rate limiting ────────────────────────────────────────────────────────────
_rate_buckets: dict = {}   # {ip: deque de timestamps}
MAX_REQ_PER_SEC = cfg.server.rate_limit_per_sec

def _check_rate_limit(ip: str) -> bool:
    """Retorna True si la IP está dentro del límite de requests."""
    now = time.time()
    bucket = _rate_buckets.setdefault(ip, collections.deque())
    # Purgar entradas antiguas (> 1 segundo)
    while bucket and now - bucket[0] > 1.0:
        bucket.popleft()
    if len(bucket) >= MAX_REQ_PER_SEC:
        return False
    bucket.append(now)
    return True


# ─── Pensamiento interno y telemetría cognitiva ──────────────────────────────
def _extract_thought_and_clean_response(text: str):
    """Extrae bloques <think>...</think> si existen y limpia la respuesta."""
    if not text:
        return "", ""
    match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if match:
        thought_content = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return thought_content, cleaned_response
    return "", text


def _build_thought_data(last_user_text: str, has_skill: bool, skill_name: str, raw_response: str):
    """Construye metadatos de pensamiento interno cognitivo y de recursos."""
    model_thought, cleaned_response = _extract_thought_and_clean_response(raw_response)
    relevant_mems = memory_manager.get_relevant_memories(last_user_text, limit=3)
    headroom_data = governor.get_cpu_headroom()
    cpu_free = headroom_data.get("cpu_headroom_percent", 100)

    reasoning_text = model_thought if model_thought else (
        f"Análisis sintáctico: '{last_user_text[:60]}...'. "
        f"Memoria relevante: {len(relevant_mems)} nodos contextuales. "
        f"Térmica/CPU Headroom: {cpu_free:.1f}% disponible. "
        + (f"Invocando habilidad de sistema: {skill_name}." if has_skill else "Sintetizando razonamiento cognitivo neuronal.")
    )

    thought = {
        "intent": skill_name if has_skill else "conversational_reasoning",
        "has_skill": has_skill,
        "skill_name": skill_name if has_skill else None,
        "reasoning": reasoning_text,
        "memories": [m.get("content") for m in relevant_mems],
        "cpu_headroom": cpu_free,
        "governor_active": governor.cpu_guard_active
    }
    return thought, (cleaned_response if model_thought else raw_response)


# ─── Auto-inicio de Ollama ───────────────────────────────────────────────────────────
def _ensure_ollama_running() -> bool:
    """
    Verifica si Ollama está corriendo. Si no, lo lanza automáticamente.
    Detecta si está corriendo en WSL o en Windows nativo.
    Retorna True si Ollama quedó operativo.
    """
    import subprocess
    global ollama_online

    # 1. Verificar si ya está online
    if engine.is_online():
        ollama_online = True
        return True

    log.warning("[Ollama] No detectado. Intentando iniciar automáticamente...")

    # 2. Detectar entorno: ¿corremos dentro de WSL o en Windows?
    running_in_wsl = os.path.exists("/proc/version") and "microsoft" in open("/proc/version").read().lower()

    try:
        if running_in_wsl:
            # Dentro de WSL: lanzar ollama serve directamente
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        else:
            # Windows: lanzar via wsl.exe
            subprocess.Popen(
                ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c",
                 "nohup ollama serve > /tmp/ollama_auto.log 2>&1 &"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except FileNotFoundError as e:
        log.error(f"[Ollama] No se encontró el ejecutable: {e}")
        return False
    except Exception as e:
        log.error(f"[Ollama] Error al iniciar: {e}")
        return False

    # 3. Esperar hasta 15s a que Ollama responda
    log.info("[Ollama] Esperando que el servidor arranque...")
    for i in range(15):
        time.sleep(1)
        if engine.is_online():
            ollama_online = True
            log.info(f"[Ollama] ¡Operativo! (tardó {i+1}s)")
            return True

    log.error("[Ollama] Tiempo agotado. No pudo iniciar en 15 segundos.")
    ollama_online = False
    return False


# ─── Watchdog de Ollama ───────────────────────────────────────────────────────
def _ollama_watchdog():
    """Thread en background que verifica el estado de Ollama cada 30s
    y colecta telemetría para el historial.
    Si detecta que Ollama cayó, lo reinicia automáticamente."""
    global ollama_online
    while True:
        time.sleep(30)
        try:
            online = engine.is_online()
            if online != ollama_online:
                ollama_online = online
                status_str = "ONLINE" if online else "OFFLINE"
                log.info(f"[Watchdog] Ollama cambió a: {status_str}")

            # Auto-reinicio si Ollama caíyó
            if not online:
                log.warning("[Watchdog] Ollama offline. Intentando reiniciar...")
                threading.Thread(target=_ensure_ollama_running, daemon=True).start()
        except Exception:
            pass

def _telemetry_collector():
    """Colecta telemetría cada 5s y la guarda en el historial circular."""
    from skills.system_engine import get_system_telemetry
    while True:
        time.sleep(5)
        try:
            sample = get_system_telemetry()
            if "error" not in sample:
                sample["ts"] = time.time()
                with _telem_lock:
                    _telem_history.append(sample)
        except Exception:
            pass

# ─── Asegurar Ollama al inicio ────────────────────────────────────────────────────────
# Se ejecuta en thread para no bloquear el arranque del servidor HTTP
threading.Thread(target=_ensure_ollama_running, daemon=True).start()

threading.Thread(target=_ollama_watchdog, daemon=True).start()
threading.Thread(target=_telemetry_collector, daemon=True).start()


# ─── Audio TTS ───────────────────────────────────────────────────────────────
def _stop_audio():
    """Detiene cualquier reproducción de audio en curso."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception:
        pass


def _play_audio_thread(text: str, audio_id: str = None):
    """Genera audio TTS y lo guarda para streaming al navegador."""
    global is_speaking, _last_audio_bytes
    path = None
    try:
        import edge_tts
        clean = (text
                 .replace("```", "").replace("`", "").replace("*", "")
                 .replace("#", "").replace("_", "").replace("•", "").strip())
        if not clean:
            if audio_id:
                with _audio_cache_lock:
                    evt = _audio_events.get(audio_id)
                    if evt:
                        evt.set()
            return

        # Usar voz del perfil actual
        active_voice = memory_manager.get_profile().get("voice_preferred", cfg.audio.voice)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        comm = edge_tts.Communicate(clean, active_voice,
                                    rate=cfg.audio.tts_rate,
                                    pitch=cfg.audio.tts_pitch)
        loop.run_until_complete(comm.save(path))
        loop.close()

        # Guardar en memoria con lock para evitar race condition
        try:
            with open(path, "rb") as af:
                audio_bytes = af.read()
            with _audio_lock:
                _last_audio_bytes = audio_bytes
            if audio_id:
                with _audio_cache_lock:
                    _audio_cache[audio_id] = audio_bytes
                    if len(_audio_cache) > 10:
                        oldest = next(iter(_audio_cache))
                        _audio_cache.pop(oldest, None)
                        _audio_events.pop(oldest, None)
                    evt = _audio_events.get(audio_id)
                    if evt:
                        evt.set()
        except Exception as e:
            log.warning(f"No se pudo leer audio generado: {e}")

        # Reproducción local con pygame (opcional)
        try:
            import pygame
            with _lock:
                is_speaking = True
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
            pygame.mixer.quit()
        except Exception:
            pass

    except Exception as e:
        log.error(f"Error en TTS: {e}")
        if audio_id:
            with _audio_cache_lock:
                evt = _audio_events.get(audio_id)
                if evt:
                    evt.set()
    finally:
        with _lock:
            is_speaking = False
        if path:
            try:
                os.remove(path)
            except Exception:
                pass


def speak(text: str, audio_id: str = None):
    """Lanza reproducción de voz neural sin congelar el servidor HTTP."""
    _stop_audio()
    if audio_id:
        with _audio_cache_lock:
            _audio_events[audio_id] = threading.Event()
    threading.Thread(target=_play_audio_thread, args=(text, audio_id), daemon=True).start()


# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class FrondaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silenciar logs HTTP ruidosos en terminal

    def _cors(self):
        origin = cfg.server.allowed_origins
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Fronda-Token")

    def _check_auth(self) -> bool:
        required = cfg.server.auth_token
        if not required:
            return True
        token = self.headers.get("X-Fronda-Token", "")
        return token == required

    def _get_client_ip(self) -> str:
        return self.client_address[0]

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if not self._check_auth():
            return self._json(401, {"error": "No autorizado"})

        if self.path in ("/", "/fronda_voice_gui.html"):
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
                    "speaking":      is_speaking,
                    "processing":    is_processing,
                    "voice":         memory_manager.get_profile().get("voice_preferred", cfg.audio.voice),
                    "model":         engine.default_model,
                    "ollama_online": ollama_online,
                    "wsl_available": config.get().wsl.enabled,
                    "governance":    governor.get_status_report(),
                }
            self._json(200, data)

        elif self.path == "/api/config":
            try:
                available_models = engine.list_models()
                c = config.get()
                self._json(200, {
                    "default_model":   engine.default_model,
                    "fallback_model":  engine.fallback_model,
                    "available_models": available_models,
                    "voice":           c.audio.voice,
                    "port":            c.server.port,
                    "welcome_message": c.user.welcome_message,
                    "user_nickname":   c.user.nickname,
                    "handoff_greeting": session_handoff.get_greeting_briefing(c.user.nickname),
                })
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif self.path == "/api/handoff":
            self._json(200, session_handoff.get_handoff_summary())

        elif self.path == "/api/memory":
            self._json(200, memory_manager.get_data())

        elif self.path == "/api/telemetry":
            self._json(200, fronda_skills.get_system_telemetry())

        elif self.path == "/api/skills/requests":
            self._json(200, fronda_skills.get_skill_requests())

        elif self.path == "/api/skills":
            # Lista de skills disponibles
            self._json(200, {
                "skills": [
                    {"name": "time_date",      "description": "Hora y fecha actual"},
                    {"name": "telemetry",      "description": "Diagnóstico de hardware en tiempo real"},
                    {"name": "os_info",        "description": "Información del sistema operativo"},
                    {"name": "skills_summary", "description": "Lista de capacidades de Fronda"},
                    {"name": "math_calc",      "description": "Calculadora científica AST"},
                    {"name": "volume",         "description": "Control de volumen de Windows"},
                    {"name": "mute",           "description": "Silenciar audio"},
                    {"name": "unmute",         "description": "Activar audio"},
                    {"name": "brightness",     "description": "Control de brillo"},
                    {"name": "screenshot",     "description": "Captura de pantalla"},
                    {"name": "web_search",     "description": "Búsqueda web DuckDuckGo"},
                    {"name": "deep_research",  "description": "Investigación multi-fuente (DDG, Wikipedia, GitHub)"},
                    {"name": "launch_app",     "description": "Lanzar aplicaciones de Windows"},
                    {"name": "wsl_command",    "description": "Ejecutar comandos en WSL 2"},
                ]
            })

        elif self.path.startswith("/api/audio"):
            import urllib.parse
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            audio_id = query_params.get("id", [None])[0]

            audio = None
            if audio_id:
                evt = None
                with _audio_cache_lock:
                    evt = _audio_events.get(audio_id)
                if evt:
                    evt.wait(timeout=15.0)
                with _audio_cache_lock:
                    audio = _audio_cache.get(audio_id)

            if not audio:
                with _audio_lock:
                    audio = _last_audio_bytes

            if audio:
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(audio)))
                self.send_header("Cache-Control", "no-cache")
                self._cors()
                self.end_headers()
                self.wfile.write(audio)
            else:
                self.send_error(404, "No audio synthesized yet")

        elif self.path.startswith("/api/logs"):
            self._serve_logs()

        elif self.path == "/api/telemetry/history":
            with _telem_lock:
                history = list(_telem_history)
            self._json(200, {"samples": history, "count": len(history)})

        elif self.path == "/api/docs":
            self._serve_docs()

        else:
            self.send_error(404)

    def do_POST(self):
        global is_processing
        if not self._check_auth():
            return self._json(401, {"error": "No autorizado"})
        if not _check_rate_limit(self._get_client_ip()):
            return self._json(429, {"error": "Rate limit excedido"})

        max_bytes = cfg.server.max_body_bytes
        length = min(int(self.headers.get("Content-Length", 0)), max_bytes)
        body   = self.rfile.read(length).decode("utf-8")

        if self.path == "/api/chat":
            try:
                req       = json.loads(body)
                messages  = req.get("messages", [])
                speak_rsp = req.get("speak", True)

                last_user_text = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user_text = m.get("content", "")
                        break

                with _lock:
                    is_processing = True

                # 1. Evaluar si dispara un Skill directo
                has_skill, skill_name, skill_result = fronda_skills.dispatch_skill_intent(last_user_text)

                DIRECT_SKILLS = {
                    "telemetry", "volume", "mute", "unmute", "brightness",
                    "screenshot", "launch_app", "wsl_command", "time_date",
                    "math_calc", "skills_summary", "os_info",
                    "hardware_analysis", "weather", "cognitive_graph",
                    "pdf_reader", "media_convert", "september_18", "holidays",
                    "screen_vision"
                }

                if has_skill and skill_name in DIRECT_SKILLS:
                    response = skill_result
                else:
                    system_context = memory_manager.get_system_context(last_user_text)
                    if has_skill and skill_result:
                        system_context += (
                            f"\n\n[DATOS OBTENIDOS POR SKILL '{skill_name}']:\n"
                            f"{skill_result}\nIntegra estos datos en tu respuesta."
                        )
                    if not ollama_online:
                        response = "⚠️ Ollama no está disponible en este momento. Reintentando conexión..."
                    else:
                        response = engine.chat(messages, system_context=system_context)

                # 2. Detectar limitaciones y generar ticket
                ticket_created = None
                if not has_skill:
                    ticket_created = fronda_skills.check_for_skill_limitation(last_user_text, response)
                    if ticket_created:
                        response += (
                            f"\n\n📌 [Solicitud {ticket_created['id']} registrada para "
                            f"el Asistente Desarrollador (Antigravity)]."
                        )

                with _lock:
                    is_processing = False

                # 3. Procesar pensamiento interno y limpiar respuesta para voz
                thought_data, response = _build_thought_data(last_user_text, has_skill, skill_name, response)

                # 4. Aprendizaje continuo y persistencia de sesión
                memory_manager.record_interaction()
                if last_user_text and response:
                    memory_manager.extract_memories_async(last_user_text, response)
                    session_handoff.record_turn(user_query=last_user_text)

                # 5. Síntesis de voz
                audio_id = f"aud_{int(time.time() * 1000)}"
                if speak_rsp and response:
                    speak(response, audio_id=audio_id)

                self._json(200, {
                    "response":       response,
                    "thought":        thought_data,
                    "audio_id":       audio_id,
                    "voice":          memory_manager.get_profile().get("voice_preferred", cfg.audio.voice),
                    "skill_executed": skill_name if has_skill else None,
                    "skill_request":  ticket_created,
                })

            except Exception as e:
                with _lock:
                    is_processing = False
                log.error(f"Error en /api/chat: {e}")
                self._json(500, {"error": str(e)})

        elif self.path == "/api/command/run":
            try:
                req = json.loads(body)
                command = req.get("command", "").strip()
                target = req.get("target", "windows").lower()
                as_admin = bool(req.get("admin", False))

                if not command:
                    self._json(400, {"error": "Comando no proporcionado"})
                    return

                log.info(f"Ejecutando comando ({target}, admin={as_admin}): {command}")
                if target == "wsl":
                    res = bridge.run_wsl_command(command, as_root=as_admin)
                else:
                    res = bridge.run_windows_command(command, as_admin=as_admin)

                self._json(200, res)
            except Exception as e:
                log.error(f"Error en /api/command/run: {e}")
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

        elif self.path == "/api/model/switch":
            try:
                req    = json.loads(body)
                target = req.get("model", "")
                # Consultar modelos disponibles dinámicamente
                available = engine.list_models()
                # También aceptar prefijos de modelos
                matched = next((m for m in available if m == target or m.startswith(target)), None)
                if matched or target in (engine.default_model, engine.fallback_model):
                    engine.default_model = matched or target
                    log.info(f"Modelo cambiado a: {engine.default_model}")
                    self._json(200, {"ok": True, "model": engine.default_model})
                else:
                    self._json(400, {"error": f"Modelo '{target}' no disponible. Disponibles: {available}"})
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif self.path == "/api/memory/add":
            try:
                req      = json.loads(body)
                content  = req.get("content", "")
                category = req.get("category", "experiencia")
                if content:
                    mem = memory_manager.add_memory(content, category=category)
                    self._json(200, {"ok": True, "memory": mem})
                else:
                    self._json(400, {"error": "Contenido vacío"})
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif self.path == "/api/chat/stream":
            self._handle_chat_stream(body)

        else:
            self.send_error(404)

    def _handle_chat_stream(self, body: str):
        """POST /api/chat/stream — Server-Sent Events para streaming de tokens (C3.2)."""
        global is_processing
        try:
            req      = json.loads(body)
            messages = req.get("messages", [])

            last_user_text = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    last_user_text = m.get("content", "")
                    break

            # Habilidades directas no usan SSE
            has_skill, skill_name, skill_result = fronda_skills.dispatch_skill_intent(last_user_text)
            DIRECT_SKILLS = {
                "telemetry", "volume", "mute", "unmute", "brightness",
                "screenshot", "launch_app", "wsl_command", "time_date",
                "math_calc", "skills_summary", "os_info",
                "hardware_analysis", "weather", "cognitive_graph",
                "pdf_reader", "media_convert", "september_18", "holidays",
                "screen_vision"
            }

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self._cors()
            self.end_headers()

            def _sse(event: str, data: str):
                payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                try:
                    self.wfile.write(payload.encode("utf-8"))
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

            with _lock:
                is_processing = True

            thought_init, _ = _build_thought_data(last_user_text, has_skill, skill_name, "")
            _sse("thought", thought_init)

            if has_skill and skill_name in DIRECT_SKILLS:
                _sse("token", skill_result)
                _sse("done", {"skill": skill_name})
            elif not ollama_online:
                _sse("token", "⚠️ Ollama no está disponible en este momento.")
                _sse("done", {})
            else:
                system_context = memory_manager.get_system_context(last_user_text)
                if has_skill and skill_result:
                    system_context += (
                        f"\n\n[DATOS OBTENIDOS POR SKILL '{skill_name}']:\n"
                        f"{skill_result}\nIntegra estos datos en tu respuesta."
                    )
                full_response = ""
                try:
                    for token in engine.stream_chat(messages, system_context=system_context):
                        full_response += token
                        _sse("token", token)
                except Exception as e:
                    _sse("error", str(e))
                _sse("done", {})

                # Procesar pensamiento final y síntesis de voz
                thought_final, cleaned_speech = _build_thought_data(last_user_text, has_skill, skill_name, full_response)
                if last_user_text and full_response:
                    memory_manager.extract_memories_async(last_user_text, cleaned_speech)
                    speak(cleaned_speech)

            with _lock:
                is_processing = False
            memory_manager.record_interaction()

        except Exception as e:
            with _lock:
                is_processing = False
            log.error(f"Error en /api/chat/stream: {e}")
            try:
                self.wfile.write(f"event: error\ndata: {json.dumps(str(e))}\n\n".encode())
                self.wfile.flush()
            except Exception:
                pass

    def do_PATCH(self):
        if not self._check_auth():
            return self._json(401, {"error": "No autorizado"})

        # PATCH /api/skills/requests/{id}
        if self.path.startswith("/api/skills/requests/"):
            ticket_id = self.path.split("/api/skills/requests/")[-1].strip("/")
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length).decode("utf-8")
            try:
                req      = json.loads(body)
                new_est  = req.get("estado", "INSTALADO")
                success  = fronda_skills.update_skill_request(ticket_id, new_est)
                if success:
                    self._json(200, {"ok": True, "id": ticket_id, "estado": new_est})
                else:
                    self._json(404, {"error": f"Ticket {ticket_id} no encontrado"})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self.send_error(404)

    def do_DELETE(self):
        if not self._check_auth():
            return self._json(401, {"error": "No autorizado"})

        # DELETE /api/skills/requests/{id}
        if self.path.startswith("/api/skills/requests/"):
            ticket_id = self.path.split("/api/skills/requests/")[-1].strip("/")
            success   = fronda_skills.delete_skill_request(ticket_id)
            if success:
                self._json(200, {"ok": True})
            else:
                self._json(404, {"error": f"Ticket {ticket_id} no encontrado"})
        else:
            self.send_error(404)

    def _serve_logs(self):
        """Sirve los últimos N lines del log de Fronda."""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            n_lines = int(params.get("lines", ["50"])[0])
            log_path = config.logs_dir() / "fronda.log"
            if not log_path.exists():
                self._json(200, {"lines": []})
                return
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self._json(200, {"lines": [l.rstrip() for l in lines[-n_lines:]]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _serve_docs(self):
        """GET /api/docs — Documentación interactiva de la API (C16.2)."""
        c = config.get()
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Fronda 1.0 — API Docs</title>
  <style>
    body{{font-family:system-ui,sans-serif;background:#0a0f1a;color:#e2e8f5;margin:0;padding:24px}}
    h1{{color:#00ffaa;font-size:2rem}}h2{{color:#00e5ff;margin-top:32px;border-bottom:1px solid #1e3a4a;padding-bottom:6px}}
    .ep{{background:#111c2a;border:1px solid #1e3a4a;border-radius:8px;padding:16px;margin:12px 0}}
    .method{{display:inline-block;padding:3px 10px;border-radius:4px;font-weight:700;font-size:12px;margin-right:8px}}
    .get{{background:#064e3b;color:#34d399}}.post{{background:#1e3a8a;color:#93c5fd}}
    .patch{{background:#78350f;color:#fcd34d}}.delete{{background:#7f1d1d;color:#fca5a5}}
    code{{background:#0f172a;padding:2px 6px;border-radius:4px;color:#00ffaa;font-family:'Fira Code',monospace}}
    pre{{background:#0f172a;padding:14px;border-radius:6px;overflow:auto;font-size:13px;color:#94a3b8}}
    .badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;background:#1e3a4a;color:#64748b;margin-left:8px}}
    a{{color:#00ffaa}}
  </style>
</head>
<body>
  <h1>⚡ Fronda 1.0 — API Reference</h1>
  <p>Servidor corriendo en puerto <code>{c.server.port}</code> &bull; Modelo activo: <code>{engine.default_model}</code></p>

  <h2>Estado y Configuración</h2>
  <div class="ep"><span class="method get">GET</span><code>/api/status</code>
    <p>Estado actual del servidor (speaking, processing, ollama_online, wsl_available).</p></div>
  <div class="ep"><span class="method get">GET</span><code>/api/config</code>
    <p>Configuración pública: modelos disponibles, voz, mensaje de bienvenida.</p></div>
  <div class="ep"><span class="method get">GET</span><code>/api/logs?lines=50</code>
    <p>Últimos N líneas del archivo <code>logs/fronda.log</code>.</p></div>

  <h2>Chat e Inferencia</h2>
  <div class="ep"><span class="method post">POST</span><code>/api/chat</code>
    <p>Chat estándar (respuesta completa en JSON).</p>
    <pre>Body: {{"messages": [{{"role":"user","content":"Hola"}}], "speak": true}}</pre></div>
  <div class="ep"><span class="method post">POST</span><code>/api/chat/stream</code>
    <p>Chat en streaming via Server-Sent Events. Eventos: <code>token</code>, <code>done</code>, <code>error</code>.</p>
    <pre>Body: {{"messages": [{{"role":"user","content":"Hola"}}]}}</pre></div>
  <div class="ep"><span class="method post">POST</span><code>/api/speak</code>
    <p>Sintetizar texto a voz directamente.</p>
    <pre>Body: {{"text": "Hola David"}}</pre></div>
  <div class="ep"><span class="method post">POST</span><code>/api/stop</code>
    <p>Detener reproducción de audio en curso.</p></div>

  <h2>Modelos</h2>
  <div class="ep"><span class="method post">POST</span><code>/api/model/switch</code>
    <p>Cambiar el modelo activo. Valida contra modelos instalados en Ollama.</p>
    <pre>Body: {{"model": "qwen2.5-coder:1.5b"}}</pre></div>

  <h2>Memoria</h2>
  <div class="ep"><span class="method get">GET</span><code>/api/memory</code>
    <p>Retorna el JSON completo de memoria persistente.</p></div>
  <div class="ep"><span class="method post">POST</span><code>/api/memory/add</code>
    <p>Agrega un recuerdo manualmente.</p>
    <pre>Body: {{"content": "David prefiere Rust", "category": "preferencia"}}</pre></div>

  <h2>Skills y Telemetría</h2>
  <div class="ep"><span class="method get">GET</span><code>/api/skills</code>
    <p>Lista de skills disponibles y sus descripciones.</p></div>
  <div class="ep"><span class="method get">GET</span><code>/api/telemetry</code>
    <p>Snapshot actual de CPU, RAM, disco, batería.</p></div>
  <div class="ep"><span class="method get">GET</span><code>/api/telemetry/history</code>
    <p>Historial circular de hasta 60 muestras (una cada 5s = ~5 minutos).</p></div>

  <h2>Tickets de Skills</h2>
  <div class="ep"><span class="method get">GET</span><code>/api/skills/requests</code>
    <p>Lista de tickets de habilidades pendientes.</p></div>
  <div class="ep"><span class="method patch">PATCH</span><code>/api/skills/requests/{{id}}</code>
    <p>Actualizar estado de un ticket.</p>
    <pre>Body: {{"estado": "INSTALADO"}}</pre></div>
  <div class="ep"><span class="method delete">DELETE</span><code>/api/skills/requests/{{id}}</code>
    <p>Eliminar un ticket.</p></div>

  <h2>Audio</h2>
  <div class="ep"><span class="method get">GET</span><code>/api/audio</code>
    <p>Stream del último audio MP3 sintetizado por TTS.</p></div>

  <p style="margin-top:40px;color:#334155">Fronda 1.0 &mdash; <a href="/">Volver a la GUI</a></p>
</body></html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

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
    c = config.get()
    log.info("=" * 60)
    log.info("       FRONDA 1.0 — CLON DIGITAL DE DAVID GALLEGUILLOS")
    log.info(f"       Modelo  : {engine.default_model}")
    log.info(f"       Fallback: {engine.fallback_model}")
    log.info(f"       Voz     : {memory_manager.get_profile().get('voice_preferred', c.audio.voice)}")
    log.info(f"       Servidor: http://127.0.0.1:{PORT}")
    log.info("=" * 60)

    # Anuncio de inicio
    threading.Thread(
        target=_play_audio_thread,
        args=(f"Fronda 1.0 en línea. Núcleo de memoria y clon digital activos, {c.user.nickname}.",),
        daemon=True
    ).start()

    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((c.server.host, PORT), FrondaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Cerrando sistemas y guardando memoria...")
