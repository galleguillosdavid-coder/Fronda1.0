"""
Jarvis Voice GUI Server
Servidor HTTP que expone la voz neural de Jarvis (es-ES-AlvaroNeural)
a una interfaz web. El audio se reproduce en el servidor vía pygame.
Puerto: 5176
"""
import os
import sys
import json
import asyncio
import tempfile
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

VOICE        = "es-ES-AlvaroNeural"
OLLAMA_API   = "http://127.0.0.1:11434/api/chat"
MODEL        = "jarvis"
PORT         = 5176
GUI_FILE     = Path(__file__).parent / "jarvis_voice_gui.html"

# ─── Estado global de audio ──────────────────────────────────────────────────
_lock         = threading.Lock()
is_speaking   = False
is_processing = False

def _stop_audio():
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception:
        pass

def _play_audio_thread(text: str):
    """Genera y reproduce TTS en un hilo separado."""
    global is_speaking
    try:
        import edge_tts, pygame

        clean = (text.replace("```", "").replace("*", "")
                     .replace("#", "").replace("_", "").strip())
        if not clean:
            return

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name

        # Generar audio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        comm = edge_tts.Communicate(clean, VOICE, rate="+5%", pitch="-2Hz")
        loop.run_until_complete(comm.save(path))
        loop.close()

        # Reproducir
        with _lock:
            is_speaking = True
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            import time; time.sleep(0.05)
        pygame.mixer.quit()

    except Exception as e:
        print(f"[Audio Error]: {e}")
    finally:
        with _lock:
            is_speaking = False
        try: os.remove(path)
        except: pass

def speak(text: str):
    """Lanza reproducción de TTS sin bloquear el servidor HTTP."""
    _stop_audio()
    t = threading.Thread(target=_play_audio_thread, args=(text,), daemon=True)
    t.start()

def query_ollama(messages: list) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"Error al conectar con Ollama: {e}"

# ─── Handler HTTP ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar logs del servidor

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/jarvis_voice_gui.html"):
            try:
                content = GUI_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self._cors()
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "jarvis_voice_gui.html no encontrado")
        elif self.path == "/api/status":
            with _lock:
                data = {"speaking": is_speaking, "processing": is_processing, "voice": VOICE}
            self._json(200, data)
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

                with _lock:
                    is_processing = True

                response = query_ollama(messages)

                with _lock:
                    is_processing = False

                if speak_response and response:
                    speak(response)

                self._json(200, {"response": response, "voice": VOICE})

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
        else:
            self.send_error(404)

    def _json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  JARVIS VOICE GUI SERVER")
    print(f"  Voz : {VOICE}")
    print(f"  Puerto : http://127.0.0.1:{PORT}")
    print("=" * 55)

    # Anuncio de inicio
    threading.Thread(
        target=_play_audio_thread,
        args=("Sistemas de voz neural activos. Interfaz web lista, señor.",),
        daemon=True
    ).start()

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Jarvis] Apagando servidor...")
