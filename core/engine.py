"""
Fronda 1.0 - Core Inference Engine
Gestiona la comunicación de alta velocidad con Ollama en Linux WSL 2,
aplicando optimizaciones de latencia y penalizaciones dinámicas contra bucles.
"""
import json
import urllib.request
from typing import List, Dict, Any

class FrondaInferenceEngine:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", default_model: str = "frondabrick"):
        self.base_url = base_url
        self.default_model = default_model
        self.chat_url = f"{base_url}/api/chat"
        self.generate_url = f"{base_url}/api/generate"

    def chat(self, messages: List[Dict[str, str]], system_context: str = "", model: str = None, temperature: float = 0.25) -> str:
        """Envía conversación estructurada a Ollama con inyección de contexto."""
        chosen_model = model or self.default_model
        full_messages = []
        if system_context:
            full_messages.append({"role": "system", "content": system_context})
        
        for m in messages:
            if m.get("role") != "system":
                full_messages.append(m)

        payload = {
            "model": chosen_model,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 2048,
                "num_predict": 512,
                "repeat_penalty": 1.15
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.chat_url, data=data, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                body = json.loads(res.read().decode("utf-8"))
                return body.get("message", {}).get("content", "")
        except Exception as e:
            return f"Error en inferencia de Fronda ({chosen_model}): {e}"

engine = FrondaInferenceEngine()
