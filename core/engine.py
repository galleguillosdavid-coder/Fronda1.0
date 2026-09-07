"""
Fronda 1.0 - Core Inference Engine
Gestiona la comunicación de alta velocidad con Ollama,
aplicando optimizaciones de latencia y penalizaciones dinámicas contra bucles.
Soporta modelo primario con fallback automático.
"""
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Iterator

import config
from fronda_logger import get_logger
from core.governor import governor

log = get_logger("fronda.engine")


class FrondaInferenceEngine:
    """Motor de inferencia unificado para Ollama. Soporta chat, generate y streaming."""

    def __init__(self, base_url: str = None, default_model: str = None):
        cfg = config.get()
        self.base_url      = (base_url or cfg.ollama.url).rstrip("/")
        self.default_model = default_model or cfg.ollama.default_model
        self.fallback_model = cfg.ollama.fallback_model
        self.timeout       = cfg.ollama.timeout
        self._options      = dict(cfg.ollama.options)

        self.chat_url     = f"{self.base_url}/api/chat"
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url     = f"{self.base_url}/api/tags"

    # ─── API pública ─────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_context: str = "",
        model: str = None,
        temperature: float = None,
        use_fallback: bool = True,
    ) -> str:
        """Envía conversación estructurada a Ollama con inyección de contexto."""
        chosen_model = model or self.default_model
        full_messages = self._build_messages(messages, system_context)
        options = dict(self._options)
        if temperature is not None:
            options["temperature"] = temperature

        response = self._do_chat(full_messages, chosen_model, options)
        if not response and use_fallback and chosen_model != self.fallback_model:
            log.warning(f"Modelo '{chosen_model}' sin respuesta, cambiando a fallback '{self.fallback_model}'")
            response = self._do_chat(full_messages, self.fallback_model, options)

        # Regla C4 (CynCo S5): Interceptar bucles infinitos de inferencia
        if response and governor.check_doom_loop(response):
            log.warning("[S5 Governor] Doom loop detectado en chat. Interrumpiendo repetición.")
            response = "He detectado una reiteración en mi análisis. ¿Podrías indicarme qué enfoque específico prefieres tomar?"

        return response

    def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = None,
        temperature: float = None,
        use_fallback: bool = True,
    ) -> str:
        """Consulta de generación directa sin historial de mensajes."""
        chosen_model = model or self.default_model
        options = dict(self._options)
        if temperature is not None:
            options["temperature"] = temperature

        response = self._do_generate(prompt, chosen_model, system, options)
        if not response and use_fallback and chosen_model != self.fallback_model:
            log.warning(f"Modelo '{chosen_model}' sin respuesta, cambiando a fallback '{self.fallback_model}'")
            response = self._do_generate(prompt, self.fallback_model, system, options)

        # Regla C4 (CynCo S5): Interceptar bucles infinitos de inferencia
        if response and governor.check_doom_loop(response):
            log.warning("[S5 Governor] Doom loop detectado en generate. Interrumpiendo repetición.")
            response = "Reiteración detectada por el gobernador cibernético. Por favor replantea la consulta."

        return response

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_context: str = "",
        model: str = None,
        temperature: float = None,
    ) -> Iterator[str]:
        """Genera tokens progresivos via streaming (generador)."""
        chosen_model = model or self.default_model
        full_messages = self._build_messages(messages, system_context)
        options = dict(self._options)
        if temperature is not None:
            options["temperature"] = temperature

        payload = json.dumps({
            "model": chosen_model,
            "messages": full_messages,
            "stream": True,
            "options": options,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.chat_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                for raw_line in res:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.error(f"Error en stream_chat ({chosen_model}): {e}")
            yield f"[Error de stream: {e}]"

    def list_models(self) -> List[str]:
        """Retorna los modelos instalados en Ollama."""
        try:
            req = urllib.request.Request(self.tags_url)
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            log.warning(f"No se pudo listar modelos Ollama: {e}")
            return []

    def is_online(self) -> bool:
        """Verifica si Ollama está respondiendo."""
        try:
            with urllib.request.urlopen(self.tags_url, timeout=3):
                return True
        except Exception:
            return False

    # ─── Métodos internos ────────────────────────────────────────────────────

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
        system_context: str,
    ) -> List[Dict[str, str]]:
        """Construye la lista de mensajes con el contexto de sistema al inicio."""
        full = []
        if system_context:
            full.append({"role": "system", "content": system_context})
        for m in messages:
            if m.get("role") != "system":
                full.append(m)
        return full

    def _do_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        options: dict,
    ) -> str:
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.chat_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                body = json.loads(res.read().decode("utf-8"))
                return body.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            log.error(f"Error de conexión con Ollama ({model}): {e}")
            return ""
        except Exception as e:
            log.error(f"Error inesperado en chat ({model}): {e}")
            return ""

    def _do_generate(
        self,
        prompt: str,
        model: str,
        system: str,
        options: dict,
    ) -> str:
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if system:
            payload["system"] = system
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.generate_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                result = json.loads(res.read().decode())
                return result.get("response", "").strip()
        except urllib.error.URLError as e:
            log.error(f"Error de conexión con Ollama generate ({model}): {e}")
            return ""
        except Exception as e:
            log.error(f"Error inesperado en generate ({model}): {e}")
            return ""


# ─── Instancia singleton ──────────────────────────────────────────────────────
engine = FrondaInferenceEngine()
