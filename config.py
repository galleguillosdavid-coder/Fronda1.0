"""
Fronda 1.0 - Sistema de Configuración Central
Carga en cascada: config.json → variables de entorno → valores por defecto.
Editar config.json para personalizar sin tocar código Python.
"""
import os
import json
import copy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

# ─── Ruta base del proyecto ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# ─── Schemas de configuración ────────────────────────────────────────────────

@dataclass
class OllamaConfig:
    url: str = "http://127.0.0.1:11434"
    default_model: str = "frondabrick"
    fallback_model: str = "qwen2.5-coder:1.5b"
    timeout: int = 120
    options: Dict[str, Any] = field(default_factory=lambda: {
        "temperature": 0.3,
        "num_ctx": 2048,
        "num_predict": 512,
        "repeat_penalty": 1.15,
    })

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 5176
    allowed_origins: str = "*"
    max_body_bytes: int = 1_048_576  # 1 MB
    auth_token: str = ""            # vacío = sin autenticación
    rate_limit_per_sec: int = 10

@dataclass
class AudioConfig:
    voice: str = "es-ES-AlvaroNeural"
    tts_rate: str = "+4%"
    tts_pitch: str = "-1Hz"

@dataclass
class PathsConfig:
    memory_file: str = "fronda_memory.json"
    skills_requests_file: str = "solicitudes_habilidades.json"
    gui_file: str = "fronda_voice_gui.html"
    logs_dir: str = "logs"
    captures_dir: str = "capturas"
    profile_default_file: str = "profile_default.json"

@dataclass
class WSLConfig:
    distro: str = ""          # vacío = auto-detección
    enabled: bool = True
    allowed_commands_blacklist: list = field(default_factory=lambda: [
        "rm -rf", "mkfs", "dd if=", ":(){:|:&};:", ">()", "shutdown", "halt", "reboot"
    ])

@dataclass
class UserConfig:
    name: str = "David Galleguillos"
    nickname: str = "David"
    cpu_threads: int = 4        # 4 hilos = deja 50% de CPU libre en un i5 de 8 threads
    cpu_headroom_target_percent: int = 15  # Mínimo de CPU libre para el sistema operativo
    dispatcher_lang: str = "es"
    welcome_message: str = "Fronda 1.0 inicializado. Clon digital en línea con memoria y skills activos. ¿En qué trabajamos hoy?"

@dataclass
class FrondaConfig:
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    wsl: WSLConfig = field(default_factory=WSLConfig)
    user: UserConfig = field(default_factory=UserConfig)

# ─── Instancia global ────────────────────────────────────────────────────────
_config: Optional[FrondaConfig] = None

def _merge_dict(base: dict, override: dict) -> dict:
    """Fusión profunda de dos diccionarios."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and k in result and isinstance(result[k], dict):
            result[k] = _merge_dict(result[k], v)
        else:
            result[k] = v
    return result

def _apply_env(raw: dict) -> dict:
    """Sobreescribe valores desde variables de entorno con prefijo FRONDA_."""
    env_map = {
        "FRONDA_OLLAMA_URL":        ("ollama", "url"),
        "FRONDA_MODEL":             ("ollama", "default_model"),
        "FRONDA_FALLBACK_MODEL":    ("ollama", "fallback_model"),
        "FRONDA_TIMEOUT":           ("ollama", "timeout"),
        "FRONDA_PORT":              ("server", "port"),
        "FRONDA_HOST":              ("server", "host"),
        "FRONDA_AUTH_TOKEN":        ("server", "auth_token"),
        "FRONDA_VOICE":             ("audio", "voice"),
        "FRONDA_WSL_DISTRO":        ("wsl", "distro"),
        "FRONDA_USER_NAME":         ("user", "name"),
        "FRONDA_USER_NICKNAME":     ("user", "nickname"),
        "FRONDA_CPU_THREADS":       ("user", "cpu_threads"),
    }
    for env_key, (section, param) in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            if section not in raw:
                raw[section] = {}
            # Convertir tipos
            if param in ("port", "timeout", "cpu_threads", "max_body_bytes", "rate_limit_per_sec"):
                try:
                    val = int(val)
                except ValueError:
                    pass
            raw[section][param] = val
    return raw

def _load_dotenv():
    """Carga manual de .env si existe (sin dependencia de python-dotenv)."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

def _dict_to_config(raw: dict) -> FrondaConfig:
    """Convierte un diccionario plano a FrondaConfig."""
    def _get(section, dataclass_cls):
        section_data = raw.get(section, {})
        defaults = dataclass_cls()
        for k, v in section_data.items():
            if hasattr(defaults, k):
                setattr(defaults, k, v)
        return defaults

    return FrondaConfig(
        ollama  = _get("ollama", OllamaConfig),
        server  = _get("server", ServerConfig),
        audio   = _get("audio", AudioConfig),
        paths   = _get("paths", PathsConfig),
        wsl     = _get("wsl", WSLConfig),
        user    = _get("user", UserConfig),
    )

def load(force_reload: bool = False) -> FrondaConfig:
    """Carga la configuración en cascada. Cachea el resultado."""
    global _config
    if _config is not None and not force_reload:
        return _config

    # 1. Valores por defecto
    raw: dict = {}

    # 2. Cargar desde config.json
    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            raw = _merge_dict(raw, file_data)
        except Exception as e:
            print(f"[Config] Advertencia: No se pudo leer config.json: {e}")

    # 3. Cargar .env
    _load_dotenv()

    # 4. Aplicar variables de entorno
    raw = _apply_env(raw)

    _config = _dict_to_config(raw)

    # 5. Auto-detectar threads de CPU si no está configurado
    if _config.user.cpu_threads == 0:
        _config.user.cpu_threads = os.cpu_count() or 4

    return _config

def reload() -> FrondaConfig:
    """Recarga la configuración en caliente."""
    return load(force_reload=True)

def get() -> FrondaConfig:
    """Retorna la instancia de configuración, cargando si es necesario."""
    return load()

# ─── Acceso rápido a rutas absolutas ─────────────────────────────────────────
def memory_file() -> Path:
    return BASE_DIR / get().paths.memory_file

def skills_requests_file() -> Path:
    return BASE_DIR / get().paths.skills_requests_file

def gui_file() -> Path:
    return BASE_DIR / get().paths.gui_file

def logs_dir() -> Path:
    d = BASE_DIR / get().paths.logs_dir
    d.mkdir(exist_ok=True)
    return d

def captures_dir() -> Path:
    d = BASE_DIR / get().paths.captures_dir
    d.mkdir(exist_ok=True)
    return d

def profile_default_file() -> Path:
    return BASE_DIR / get().paths.profile_default_file

# ─── Carga automática al importar ────────────────────────────────────────────
load()
