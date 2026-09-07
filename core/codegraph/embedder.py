"""
Generador de embeddings para símbolos de código y consultas de lenguaje natural.
Soporta:
1. Ollama local (ej. nomic-embed-text, all-minilm).
2. Generador determinista de respaldo (TF-IDF / Hashing normalizado) si Ollama no está disponible.
"""

import hashlib
import math
import re
from typing import List, Optional
import requests


class CodeEmbedder:
    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model_name: str = "nomic-embed-text",
        fallback_dim: int = 128,
    ):
        self.ollama_url = ollama_url.rstrip("/")
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self._ollama_available: Optional[bool] = None

    def check_ollama(self) -> bool:
        """Comprueba si Ollama y el modelo de embeddings están disponibles."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                # Coincidencia con nombre base o etiqueta
                has_model = any(
                    m == self.model_name or m.startswith(f"{self.model_name}:")
                    for m in models
                )
                self._ollama_available = has_model
                return has_model
        except Exception:
            pass
        self._ollama_available = False
        return False

    def embed_text(self, text: str) -> List[float]:
        """Obtiene el vector de embedding para un texto dado."""
        if not text or not text.strip():
            return [0.0] * self.fallback_dim

        # Intentar Ollama si está disponible o no se ha verificado
        if self._ollama_available is not False:
            vec = self._embed_ollama(text)
            if vec is not None and len(vec) > 0:
                self._ollama_available = True
                return vec
            self._ollama_available = False

        # Fallback determinista
        return self._embed_fallback(text)

    def _embed_ollama(self, text: str) -> Optional[List[float]]:
        """Invoca la API de Ollama para obtener embeddings."""
        try:
            # Primero intentar el nuevo endpoint /api/embed
            resp = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.model_name, "input": text},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if embeddings and len(embeddings[0]) > 0:
                    return embeddings[0]

            # Intentar el endpoint clásico /api/embeddings
            resp_legacy = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=8,
            )
            if resp_legacy.status_code == 200:
                emb = resp_legacy.json().get("embedding", [])
                if emb:
                    return emb
        except Exception:
            pass
        return None

    def _embed_fallback(self, text: str) -> List[float]:
        """
        Generador de embedding sintáctico determinista basado en hashing de n-gramas de tokens.
        Garantiza similitud de coseno semántica básica sin dependencias externas pesadas.
        """
        tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        if not tokens:
            return [0.0] * self.fallback_dim

        vector = [0.0] * self.fallback_dim
        for token in tokens:
            # Calcular bucket con MD5
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(digest, 16) % self.fallback_dim
            # Peso según longitud del token
            weight = 1.0 + math.log(1.0 + len(token))
            vector[idx] += weight

        # Normalización L2
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calcula la similitud de coseno entre dos vectores."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 <= 0.0 or norm2 <= 0.0:
            return 0.0
        return dot / (norm1 * norm2)
