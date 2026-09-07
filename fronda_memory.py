"""
Fronda 1.0 - Motor de Memoria Persistente y Aprendizaje Incremental
Gestiona los recuerdos, la historia del usuario y el aprendizaje continuo.
- Caché con invalidación por mtime del archivo
- deepcopy correcto del template por defecto
- Hardware detectado dinámicamente al arrancar
"""
import os
import copy
import json
import re
import uuid
import datetime
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any

import config
from fronda_logger import get_logger

log = get_logger("fronda.memory")

MEMORY_FILE = config.memory_file()
_lock = threading.Lock()

# ─── Perfil por defecto (usado solo si no existe fronda_memory.json) ──────────
_DEFAULT_MEMORY = {
    "profile": {
        "name": "",
        "nickname": "",
        "role": "Creador e Ingeniero - Original de Fronda 1.0",
        "voice_preferred": "es-ES-AlvaroNeural",
        "mindset": [],
        "specialties": [],
        "hardware_specs": {}
    },
    "learned_history": [],
    "acquired_skills": [],
    "stats": {
        "total_interactions": 0,
        "total_memories": 0,
        "last_interaction": ""
    }
}

# ─── Algoritmo BM25 para Recuperación Semántica Híbrida (Inspirado en CynCo) ─
_SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "más", "pero", "sus",
    "le", "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin",
    "sobre", "tambien", "también", "me", "hasta", "hay", "donde", "quien", "desde",
    "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese",
    "eso", "ante", "ellos", "e", "esto", "mi", "mis", "tu", "tus", "te", "ti"
}


def _tokenize(text: str) -> List[str]:
    """Tokeniza y normaliza texto en español eliminando signos y stopwords."""
    if not text:
        return []
    words = re.findall(r"\b\w+\b", text.lower())
    return [w for w in words if len(w) > 2 and w not in _SPANISH_STOPWORDS]


class BM25Scorer:
    """Calculador BM25 puro en Python para ranking probabilístico de recuerdos."""

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_tokens = [_tokenize(doc) for doc in corpus]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avg_dl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 1.0

        # Calcular frecuencia de documentos (DF)
        self.df: Dict[str, int] = {}
        for tokens in self.doc_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1

    def score(self, query: str) -> List[float]:
        import math
        query_tokens = _tokenize(query)
        scores = [0.0] * self.corpus_size
        if not query_tokens or self.corpus_size == 0:
            return scores

        for term in query_tokens:
            df_val = self.df.get(term, 0)
            if df_val == 0:
                continue
            # Fórmula Robertson-Spärck Jones IDF
            idf = math.log((self.corpus_size - df_val + 0.5) / (df_val + 0.5) + 1.0)
            if idf < 0:
                idf = 0.01

            for idx, tokens in enumerate(self.doc_tokens):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_dl))
                scores[idx] += idf * (numerator / denominator)

        return scores


class FrondaMemoryManager:
    def __init__(self, filepath: Path = None):
        self.filepath = Path(filepath or MEMORY_FILE)
        self._cache = None
        self._cache_mtime: float = 0.0
        self._ensure_file()
        # Auto-detectar y actualizar hardware specs al iniciar
        self._sync_hardware_specs()

    # ─── Ciclo de vida del archivo ────────────────────────────────────────────

    def _ensure_file(self):
        """Crea el archivo de memoria con valores del config si no existe."""
        if self.filepath.exists():
            return
        cfg = config.get()
        default = copy.deepcopy(_DEFAULT_MEMORY)
        default["profile"]["name"]     = cfg.user.name
        default["profile"]["nickname"] = cfg.user.nickname
        default["profile"]["voice_preferred"] = cfg.audio.voice
        self._save(default)

    def _load(self) -> dict:
        """Carga la memoria con invalidación por mtime del archivo."""
        try:
            current_mtime = os.path.getmtime(self.filepath)
        except OSError:
            current_mtime = 0.0

        if self._cache is not None and current_mtime == self._cache_mtime:
            return self._cache

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                self._cache_mtime = current_mtime
                return self._cache
        except Exception as e:
            log.error(f"Error al cargar memoria desde {self.filepath}: {e}")
            self._cache = copy.deepcopy(_DEFAULT_MEMORY)  # deepcopy correcto
            self._cache_mtime = 0.0
            return self._cache

    def _save(self, data: dict):
        """Guarda la memoria de forma atómica vía archivo temporal."""
        self._cache = data
        try:
            temp_path = self.filepath.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.filepath)
            # Actualizar mtime para evitar recarga innecesaria
            self._cache_mtime = os.path.getmtime(self.filepath)
        except Exception as e:
            log.error(f"Error al guardar memoria: {e}")

    def _sync_hardware_specs(self):
        """Detecta el hardware real y actualiza el perfil guardado."""
        try:
            from skills.system_engine import detect_hardware_specs
            specs = detect_hardware_specs()
            with _lock:
                data = self._load()
                profile = data.setdefault("profile", {})
                hw = profile.setdefault("hardware_specs", {})
                hw.update(specs)
                self._save(data)
        except Exception as e:
            log.warning(f"No se pudo sincronizar hardware specs: {e}")

    # ─── API pública ──────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        with _lock:
            return copy.deepcopy(self._load())

    def get_profile(self) -> dict:
        return self.get_data().get("profile", {})

    def add_memory(self, content: str, category: str = "experiencia", importance: int = 3) -> dict:
        """Agrega un nuevo recuerdo a la memoria a largo plazo."""
        clean_content = content.strip()
        if not clean_content:
            return {}

        with _lock:
            data = self._load()
            history = data.setdefault("learned_history", [])

            # Evitar duplicados exactos
            for item in history:
                if item.get("content", "").lower() == clean_content.lower():
                    return item

            nickname = data.get("profile", {}).get("nickname", "el usuario")
            new_item = {
                "id":         f"mem_{uuid.uuid4().hex[:6]}",
                "timestamp":  datetime.datetime.now().isoformat(timespec="seconds"),
                "category":   category,
                "content":    clean_content,
                "importance": importance
            }
            history.append(new_item)

            stats = data.setdefault("stats", {})
            stats["total_memories"]   = len(history)
            stats["last_interaction"] = datetime.datetime.now().isoformat(timespec="seconds")
            self._save(data)
            log.info(f"[Memoria Viva] Nuevo recuerdo asimilado sobre {nickname}: {clean_content[:80]}")
            return new_item

    def record_interaction(self):
        with _lock:
            data = self._load()
            stats = data.setdefault("stats", {})
            stats["total_interactions"] = stats.get("total_interactions", 0) + 1
            stats["last_interaction"]   = datetime.datetime.now().isoformat(timespec="seconds")
            self._save(data)

    def invalidate_cache(self):
        """Fuerza recarga en el próximo acceso."""
        with _lock:
            self._cache = None
            self._cache_mtime = 0.0

    def search_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca y clasifica recuerdos según BM25 e importancia acumulada."""
        with _lock:
            data = self._load()
            history = data.get("learned_history", [])

        if not history:
            return []

        if not query or not query.strip():
            # Si no hay query, retornar los recuerdos con mayor importancia
            sorted_history = sorted(history, key=lambda x: x.get("importance", 1), reverse=True)
            return sorted_history[:top_k]

        docs = [item.get("content", "") for item in history]
        scorer = BM25Scorer(docs)
        bm25_scores = scorer.score(query)

        scored_items = []
        for idx, item in enumerate(history):
            bm_score = bm25_scores[idx]
            importance = float(item.get("importance", 1))
            # Combinación lineal: relevancia léxica BM25 + peso de importancia
            total_score = (bm_score * 2.5) + (importance * 0.5)
            scored_items.append((total_score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def get_relevant_memories(self, query: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        """Alias para search_memories con límite configurable."""
        return self.search_memories(query, top_k=limit)

    def get_system_context(self, user_query: str = "") -> str:
        """Genera el bloque de contexto inyectable en el prompt del sistema usando BM25."""
        with _lock:
            data = self._load()

        profile  = data.get("profile", {})
        skills   = data.get("acquired_skills", [])
        nickname = profile.get("nickname", "el usuario")
        hw       = profile.get("hardware_specs", {})

        # Ranking BM25 de recuerdos más relevantes a la consulta
        relevant_memories = self.search_memories(user_query, top_k=8)
        top_mems = [m.get("content", "") for m in relevant_memories if m.get("content")]

        # Construir CPU/RAM dinámico
        cpu_str = hw.get("cpu_name", "CPU desconocido")
        ram_str = f"{hw.get('ram_total_gb', '?')} GB RAM"
        specialties = profile.get("specialties", [])

        context = [
            f"=== DIRECTIVA DE IDENTIDAD Y MEMORIA VIVA DE {nickname.upper()} ===",
            f"IDENTIDAD: Eres Fronda 1.0, el CLON DIGITAL cognitivo de {profile.get('name', nickname)}.",
            f"RELACIÓN: Estás hablando directamente con tu creador e igual: {nickname}.",
            f"MENTALIDAD: Compartes su mentalidad de ingeniería pragmática, resolutiva y sin rodeos.",
            f"ESPECIALIDADES: {', '.join(specialties) if specialties else 'Ingeniería y programación avanzada'}",
            f"HARDWARE LOCAL: {cpu_str}, {ram_str}",
            f"\n--- HISTORIA Y HECHOS VIVOS QUE CONOCES DE {nickname.upper()} ---"
        ]

        if top_mems:
            for mem_text in top_mems:
                context.append(f"• {mem_text}")
        else:
            context.append("• Aprendizaje inicial activo.")

        if skills:
            context.append(f"\n--- HABILIDADES Y SKILLS ADQUIRIDOS ---")
            for sk in skills[:5]:
                context.append(f"• {sk}")

        context.append("=================================================================")
        return "\n".join(context)

    def extract_memories_async(self, user_text: str, assistant_response: str):
        """Analiza en segundo plano el texto para extraer hechos del usuario."""
        threading.Thread(
            target=self._analyze_text,
            args=(user_text, assistant_response),
            daemon=True
        ).start()

    def _analyze_text(self, user_text: str, assistant_response: str):
        text  = user_text.strip()
        nickname = self.get_profile().get("nickname", "el usuario")
        name_first = nickname.split()[0] if nickname else "El usuario"

        patterns = [
            (r"(?:yo\s+)?nací\s+en\s+([^.,;\n]+)",          "biografia",   f"{name_first} nació en {{0}}."),
            (r"(?:tengo|cumplí)\s+(\d{{1,2}}\s+años)",        "biografia",   f"{name_first} tiene {{0}} de edad."),
            (r"(?:mi\s+lenguaje\s+favorito|prefiero\s+programar\s+en)\s+(?:es\s+)?([^.,;\n]+)",
             "preferencia", f"El lenguaje preferido de {name_first} es {{0}}."),
            (r"(?:estoy\s+trabajando\s+en|mi\s+proyecto\s+actual\s+es|estoy\s+desarrollando)\s+([^.,;\n]+)",
             "proyectos",   f"Proyecto activo de {name_first}: {{0}}."),
            (r"(?:recuerdo\s+que|hace\s+tiempo|cuando\s+estudiaba|cuando\s+trabajé)\s+([^.,;\n]+)",
             "experiencia", f"Experiencia pasada de {name_first}: {{0}}."),
            (r"(?:mi\s+meta|mi\s+sueño|mi\s+objetivo)\s+es\s+([^.,;\n]+)",
             "vision",      f"Meta u objetivo de {name_first}: {{0}}."),
            (r"(?:me\s+gusta|me\s+apasiona|prefiero)\s+([^.,;\n]+)",
             "preferencia", f"A {name_first} le interesa/apasiona: {{0}}."),
            (r"(?:construí|diseñé|calculé)\s+([^.,;\n]+)",
             "proyectos",   f"Logro técnico de {name_first}: {{0}}."),
        ]

        regex_matched = False
        for regex, cat, template in patterns:
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) > 3 and not extracted.startswith("que "):
                    formatted = template.format(extracted)
                    self.add_memory(formatted, category=cat, importance=4)
                    regex_matched = True
                    return

        # ── Enriquecimiento NLP con spaCy si no capturó el regex (C17) ────────
        if not regex_matched:
            try:
                from fronda_nlp import enrich_memory_extraction
                enrich_memory_extraction(text, nickname, self)
            except Exception:
                pass  # spaCy no disponible o error — silencioso


# ─── Instancia singleton ──────────────────────────────────────────────────────
memory_manager = FrondaMemoryManager()
