"""
Fronda 1.0 - Persistencia entre Sesiones y Handoff (Inspirado en CynCo)
Permite a Fronda mantener la continuidad cognitiva entre reinicios:
- Registra el último estado de trabajo, temas activos y decisiones clave.
- Genera un resumen de bienvenida contextual (Session Handoff Briefing)
  para que Fronda salude sabiendo exactamente en qué se quedaron.
"""
import os
import json
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

import config
from fronda_logger import get_logger

log = get_logger("fronda.handoff")

_DEFAULT_HANDOFF_FILE = Path(__file__).parent.parent / "session_handoff.json"


class SessionHandoffManager:
    """Gestiona el diario de decisiones y el relevo entre sesiones."""

    def __init__(self, filepath: Path = None):
        self.filepath = Path(filepath or _DEFAULT_HANDOFF_FILE)
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        if not self.filepath.exists():
            initial_data = {
                "last_session_timestamp": "",
                "last_user_intent": "",
                "active_topics": [],
                "recent_decisions": [],
                "session_notes": []
            }
            self._save(initial_data)

    def _load(self) -> Dict[str, Any]:
        try:
            if self.filepath.exists():
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"No se pudo cargar session_handoff.json: {e}")
        return {
            "last_session_timestamp": "",
            "last_user_intent": "",
            "active_topics": [],
            "recent_decisions": [],
            "session_notes": []
        }

    def _save(self, data: Dict[str, Any]):
        try:
            temp_file = self.filepath.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.filepath)
        except Exception as e:
            log.error(f"Error al guardar session_handoff: {e}")

    def record_turn(self, user_query: str, topic: str = "", decision: str = ""):
        """Actualiza el estado de la sesión actual."""
        if not user_query or not user_query.strip():
            return

        with self._lock:
            data = self._load()
            data["last_session_timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
            data["last_user_intent"] = user_query.strip()

            if topic and topic.strip():
                clean_topic = topic.strip()
                topics = data.setdefault("active_topics", [])
                if clean_topic in topics:
                    topics.remove(clean_topic)
                topics.insert(0, clean_topic)
                data["active_topics"] = topics[:5]

            if decision and decision.strip():
                clean_decision = decision.strip()
                decisions = data.setdefault("recent_decisions", [])
                decisions.insert(0, {
                    "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                    "decision": clean_decision
                })
                data["recent_decisions"] = decisions[:10]

            self._save(data)

    def get_greeting_briefing(self, nickname: str = "") -> str:
        """
        Genera un saludo contextual al iniciar el asistente basado en la sesión previa.
        """
        user_name = nickname or "David"
        with self._lock:
            data = self._load()

        last_time_str = data.get("last_session_timestamp", "")
        last_intent   = data.get("last_user_intent", "")
        active_topics = data.get("active_topics", [])

        if not last_time_str or not last_intent:
            return f"¡Hola {user_name}! Sistemas de Fronda inicializados y listos para colaborar."

        try:
            last_dt = datetime.datetime.fromisoformat(last_time_str)
            diff = datetime.datetime.now() - last_dt
            hours = diff.total_seconds() / 3600.0

            if hours < 1:
                time_desc = "hace un momento"
            elif hours < 24:
                time_desc = f"hace {int(hours)} horas"
            elif hours < 48:
                time_desc = "ayer"
            else:
                days = int(hours // 24)
                time_desc = f"hace {days} días"
        except Exception:
            time_desc = "en la sesión anterior"

        topic_str = active_topics[0] if active_topics else last_intent[:40]
        return f"¡Hola {user_name}! Bienvenido de vuelta. {time_desc.capitalize()} estuvimos tratando: '{topic_str}'. ¿Deseas continuar con eso o necesitas otra tarea?"

    def get_handoff_summary(self) -> Dict[str, Any]:
        """Obtiene una copia limpia del estado del handoff."""
        with self._lock:
            return self._load()


session_handoff = SessionHandoffManager()
