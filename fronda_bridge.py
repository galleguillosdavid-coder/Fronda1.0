"""
Fronda Brick Layer Bridge - Inter-Agent Bridge (Windows Host <-> WSL2 <-> Ollama)
Permite a Antigravity (Capa 1) orquestar tareas en WSL (Capa 2) y consultar
al clon cognitivo Fronda Brick (Capa 3).
"""

import json
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

MODEL_NAME = "frondabrick"

class FrondaBridge:
    def __init__(self, model: str = MODEL_NAME):
        self.model = model
        self.ollama_url = self._resolve_ollama_url()

    def _resolve_ollama_url(self) -> str:
        """Determina la URL óptima para conectar con Ollama en WSL."""
        for candidate in ["http://127.0.0.1:11434", "http://localhost:11434"]:
            try:
                with urllib.request.urlopen(f"{candidate}/api/tags", timeout=1) as resp:
                    if resp.status == 200:
                        return candidate
            except Exception:
                pass

        # Intento vía IP directa de WSL
        try:
            res = subprocess.run(
                ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", "hostname -I"],
                capture_output=True,
                text=True,
                timeout=5
            )
            wsl_ip = res.stdout.strip().split()[0]
            candidate = f"http://{wsl_ip}:11434"
            try:
                with urllib.request.urlopen(f"{candidate}/api/tags", timeout=2) as resp:
                    if resp.status == 200:
                        return candidate
            except Exception:
                return candidate
        except Exception:
            pass

        return "http://127.0.0.1:11434"

    def check_health(self) -> Dict[str, Any]:
        """Verifica disponibilidad de Ollama en WSL y estado del host."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "online",
                    "url": self.ollama_url,
                    "models": models,
                    "target_model_ready": any(self.model in m for m in models)
                }
        except Exception as e:
            return {
                "status": "offline",
                "url": self.ollama_url,
                "error": str(e)
            }

    def ask_clone(self, prompt: str, system: Optional[str] = None, num_ctx: int = 2048) -> str:
        """Consulta directa al clon cognitivo Fronda Brick (Capa 3)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": num_ctx
            }
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[Error de conexión con Fronda Brick en WSL]: {e}"

    def run_wsl_command(self, command: str) -> Dict[str, Any]:
        """Ejecuta un comando en el entorno Linux de WSL 2 (Capa 2)."""
        try:
            res = subprocess.run(
                ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

if __name__ == "__main__":
    bridge = FrondaBridge()
    health = bridge.check_health()
    print("[Fronda Bridge Health Check]:")
    print(json.dumps(health, indent=2))
