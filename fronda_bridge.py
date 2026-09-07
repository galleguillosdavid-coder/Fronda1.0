"""
Fronda Brick Layer Bridge - Inter-Agent Bridge (Windows Host <-> WSL2 <-> Ollama)
Permite a Antigravity (Capa 1) orquestar tareas en WSL (Capa 2) y consultar
al clon cognitivo Fronda Brick (Capa 3).
- Modelo y distro WSL leídos desde config.py
- Auto-detección de distro WSL disponible
- Validación de comandos para prevenir inyección shell
"""
import json
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

import config
from fronda_logger import get_logger

log = get_logger("fronda.bridge")


def _detect_wsl_distro() -> str:
    """
    Detecta la distro WSL activa. Prioridad:
    1. config.wsl.distro (si está definido)
    2. Primera distro listada por 'wsl.exe -l -q'
    3. Fallback a 'Ubuntu'
    """
    cfg_distro = config.get().wsl.distro
    if cfg_distro:
        return cfg_distro

    try:
        res = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True, timeout=5
        )
        # wsl -l -q usa UTF-16 LE en Windows
        output = res.stdout.decode("utf-16-le", errors="ignore")
        distros = [
            line.strip().replace("\x00", "")
            for line in output.splitlines()
            if line.strip() and line.strip() != "\x00"
        ]
        distros = [d for d in distros if d and not d.startswith("Windows")]
        if distros:
            # Preferir Ubuntu si está disponible
            ubuntu_distros = [d for d in distros if "ubuntu" in d.lower()]
            return ubuntu_distros[0] if ubuntu_distros else distros[0]
    except Exception as e:
        log.warning(f"No se pudo detectar la distro WSL: {e}")

    return "Ubuntu"


def _validate_wsl_command(command: str) -> tuple[bool, str]:
    """
    Valida que el comando no contenga patrones peligrosos.
    Retorna (es_seguro, motivo_si_no_lo_es).
    """
    blacklist = config.get().wsl.allowed_commands_blacklist
    cmd_lower = command.lower()

    for forbidden in blacklist:
        if forbidden.lower() in cmd_lower:
            return False, f"Comando rechazado por política de seguridad: patrón '{forbidden}' no permitido."

    return True, ""


class FrondaBridge:
    def __init__(self, model: str = None):
        cfg        = config.get()
        self.model = model or cfg.ollama.default_model
        self._wsl_distro   = _detect_wsl_distro()
        self.ollama_url    = self._resolve_ollama_url()

    def _resolve_ollama_url(self) -> str:
        """Determina la URL óptima para conectar con Ollama en WSL."""
        candidates = [
            config.get().ollama.url,
            "http://127.0.0.1:11434",
            "http://localhost:11434",
        ]
        for candidate in candidates:
            try:
                with urllib.request.urlopen(f"{candidate}/api/tags", timeout=2) as resp:
                    if resp.status == 200:
                        log.debug(f"Ollama encontrado en: {candidate}")
                        return candidate
            except Exception:
                continue

        # Último intento vía IP directa de WSL
        try:
            res = subprocess.run(
                ["wsl.exe", "-d", self._wsl_distro, "-e", "bash", "-c", "hostname -I"],
                capture_output=True, text=True, timeout=5
            )
            parts = res.stdout.strip().split()
            if parts:
                wsl_ip    = parts[0]
                candidate = f"http://{wsl_ip}:11434"
                try:
                    with urllib.request.urlopen(f"{candidate}/api/tags", timeout=2) as resp:
                        if resp.status == 200:
                            return candidate
                except Exception:
                    return candidate
        except Exception as e:
            log.warning(f"No se pudo obtener la IP de WSL: {e}")

        return config.get().ollama.url

    def check_health(self) -> Dict[str, Any]:
        """Verifica disponibilidad de Ollama y lista de modelos."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data   = json.loads(resp.read().decode())
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status":              "online",
                    "url":                 self.ollama_url,
                    "wsl_distro":          self._wsl_distro,
                    "models":              models,
                    "target_model_ready":  any(self.model in m for m in models),
                }
        except Exception as e:
            return {
                "status":    "offline",
                "url":       self.ollama_url,
                "wsl_distro": self._wsl_distro,
                "error":     str(e),
            }

    def ask_clone(self, prompt: str, system: Optional[str] = None, num_ctx: int = 2048) -> str:
        """Consulta directa al clon cognitivo Fronda Brick (Capa 3)."""
        cfg = config.get()
        payload = {
            "model":  self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": cfg.ollama.options.get("temperature", 0.3),
                "num_ctx":     num_ctx,
            }
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.ollama.timeout) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[Error de conexión con Fronda Brick en WSL]: {e}"

    def is_running_in_wsl(self) -> bool:
        """Determina si el proceso actual se ejecuta dentro de WSL 2."""
        try:
            return os.path.exists("/proc/version") and "microsoft" in open("/proc/version").read().lower()
        except Exception:
            return False

    def run_wsl_command(self, command: str, as_root: bool = False) -> Dict[str, Any]:
        """
        Ejecuta un comando en el entorno Linux de WSL 2 (Capa 2).
        Si as_root=True, lo ejecuta con privilegios elevados de root.
        """
        is_safe, reason = _validate_wsl_command(command)
        if not is_safe:
            log.warning(f"Comando WSL rechazado: {command} — {reason}")
            return {
                "exit_code": -2,
                "stdout":    "",
                "stderr":    reason,
                "as_root":   as_root,
            }

        try:
            if self.is_running_in_wsl():
                cmd_list = ["sudo", "-n", "bash", "-c", command] if as_root else ["bash", "-c", command]
            else:
                if as_root:
                    cmd_list = ["wsl.exe", "-d", self._wsl_distro, "-u", "root", "-e", "bash", "-c", command]
                else:
                    cmd_list = ["wsl.exe", "-d", self._wsl_distro, "-e", "bash", "-c", command]

            res = subprocess.run(
                cmd_list,
                capture_output=True, text=True,
                timeout=config.get().ollama.timeout,
            )
            return {
                "exit_code": res.returncode,
                "stdout":    res.stdout.strip(),
                "stderr":    res.stderr.strip(),
                "as_root":   as_root,
            }
        except Exception as e:
            log.error(f"Error al ejecutar comando WSL: {e}")
            return {
                "exit_code": -1,
                "stdout":    "",
                "stderr":    str(e),
                "as_root":   as_root,
            }

    def run_windows_command(self, command: str, as_admin: bool = False) -> Dict[str, Any]:
        """
        Ejecuta un comando en Windows mediante PowerShell.
        Si as_admin=True, ejecuta con privilegios elevados.
        """
        is_safe, reason = _validate_wsl_command(command)
        if not is_safe:
            log.warning(f"Comando Windows rechazado: {command} — {reason}")
            return {
                "exit_code": -2,
                "stdout":    "",
                "stderr":    reason,
                "as_admin":  as_admin,
            }

        try:
            if self.is_running_in_wsl():
                ps_exe = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
                if not os.path.exists(ps_exe):
                    ps_exe = "powershell.exe"
            else:
                ps_exe = "powershell.exe"

            if as_admin:
                escaped = command.replace('"', '`"')
                cmd_list = [
                    ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                    f"Start-Process {ps_exe} -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"{escaped}\"' -Verb RunAs -Wait"
                ]
            else:
                cmd_list = [ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]

            res = subprocess.run(
                cmd_list,
                capture_output=True, text=True,
                timeout=config.get().ollama.timeout,
            )
            return {
                "exit_code": res.returncode,
                "stdout":    res.stdout.strip(),
                "stderr":    res.stderr.strip(),
                "as_admin":  as_admin,
            }
        except Exception as e:
            log.error(f"Error al ejecutar comando Windows: {e}")
            return {
                "exit_code": -1,
                "stdout":    "",
                "stderr":    str(e),
                "as_admin":  as_admin,
            }

    def list_wsl_distros(self) -> List[str]:
        """Lista las distribuciones WSL disponibles."""
        try:
            res = subprocess.run(
                ["wsl.exe", "-l", "-q"],
                capture_output=True, timeout=5
            )
            output = res.stdout.decode("utf-16-le", errors="ignore")
            return [
                line.strip().replace("\x00", "")
                for line in output.splitlines()
                if line.strip() and line.strip() != "\x00"
            ]
        except Exception:
            return []


if __name__ == "__main__":
    bridge = FrondaBridge()
    health = bridge.check_health()
    print("[Fronda Bridge Health Check]:")
    print(json.dumps(health, indent=2))
