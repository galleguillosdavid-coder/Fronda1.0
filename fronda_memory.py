"""
Fronda 1.0 - Motor de Memoria Persistente y Aprendizaje Incremental
Gestiona los recuerdos, la historia de David Galleguillos y el aprendizaje continuo.
"""
import os
import json
import re
import uuid
import datetime
import threading
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "fronda_memory.json"
_lock = threading.Lock()

DEFAULT_MEMORY = {
    "profile": {
        "name": "David Galleguillos",
        "nickname": "David",
        "role": "Creador e Ingeniero - Original de Fronda 1.0",
        "voice_preferred": "es-ES-AlvaroNeural",
        "mindset": [
            "Visión de ingeniería pragmática",
            "Soluciones técnicas directas sin rodeos",
            "Innovación continua y autosuficiencia",
            "Optimización obsesiva de rendimiento"
        ],
        "specialties": [
            "Construcción y obras de ingeniería técnica",
            "Programación de alto rendimiento en Rust",
            "Automatización e Inteligencia Artificial en Python",
            "Administración y scripts avanzados de PowerShell en Windows 11",
            "Arquitectura de telecomunicaciones y protocolos IPv7 / VPI7"
        ],
        "hardware_specs": {
            "cpu": "Intel Core i5-1030NG7 (4 núcleos)",
            "ram": "16 GB LPDDR4",
            "graphics": "Intel Iris Plus Graphics",
            "os": "Windows 11"
        }
    },
    "learned_history": [],
    "acquired_skills": [],
    "stats": {
        "total_interactions": 0,
        "total_memories": 0,
        "last_interaction": ""
    }
}

class FrondaMemoryManager:
    def __init__(self, filepath=MEMORY_FILE):
        self.filepath = Path(filepath)
        self._cache = None
        self._ensure_file()

    def _ensure_file(self):
        if not self.filepath.exists():
            self._save(DEFAULT_MEMORY)

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                return self._cache
        except Exception as e:
            print(f"[Memoria] Error al cargar {self.filepath}: {e}")
            self._cache = DEFAULT_MEMORY.copy()
            return self._cache

    def _save(self, data: dict):
        self._cache = data
        try:
            temp_path = self.filepath.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.filepath)
        except Exception as e:
            print(f"[Memoria] Error al guardar memoria: {e}")

    def get_data(self) -> dict:
        with _lock:
            return self._load()

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

            new_item = {
                "id": f"mem_{uuid.uuid4().hex[:6]}",
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "category": category,
                "content": clean_content,
                "importance": importance
            }
            history.append(new_item)

            stats = data.setdefault("stats", {})
            stats["total_memories"] = len(history)
            stats["last_interaction"] = datetime.datetime.now().isoformat(timespec="seconds")
            self._save(data)
            print(f"[Memoria Viva] Nuevo recuerdo asimilado sobre David: {clean_content}")
            return new_item

    def record_interaction(self):
        with _lock:
            data = self._load()
            stats = data.setdefault("stats", {})
            stats["total_interactions"] = stats.get("total_interactions", 0) + 1
            stats["last_interaction"] = datetime.datetime.now().isoformat(timespec="seconds")
            self._save(data)

    def get_system_context(self, user_query: str = "") -> str:
        """Genera el bloque de contexto inyectable en el prompt del sistema."""
        with _lock:
            data = self._load()

        profile = data.get("profile", {})
        history = data.get("learned_history", [])
        skills  = data.get("acquired_skills", [])

        # Filtrar o priorizar recuerdos relevantes a la consulta
        q_lower = user_query.lower()
        scored_mems = []
        for mem in history:
            text = mem.get("content", "").lower()
            score = mem.get("importance", 1)
            words = [w for w in q_lower.split() if len(w) > 3]
            for w in words:
                if w in text:
                    score += 3
            scored_mems.append((score, mem))

        scored_mems.sort(key=lambda x: x[0], reverse=True)
        top_mems = [m["content"] for _, m in scored_mems[:8]]

        context = [
            f"=== DIRECTIVA DE IDENTIDAD Y MEMORIA VIVA DE DAVID GALLEGUILLOS ===",
            f"IDENTIDAD: Eres Fronda Brick v0.01, el CLON DIGITAL cognitivo de David Galleguillos.",
            f"RELACIÓN CON EL USUARIO: Estás hablando directamente con tu creador e igual: David Galleguillos.",
            f"MENTALIDAD Y TRATO: Compartes su mentalidad de ingeniería pragmática, resolutiva y sin rodeos. NUNCA digas 'no tengo una identidad' ni hables como un robot impersonal; habla como el gemelo digital de David.",
            f"ESPECIALIDADES MAESTRAS: {', '.join(profile.get('specialties', []))}",
            f"HARDWARE LOCAL: {profile.get('hardware_specs', {}).get('cpu', 'Intel i5')}, {profile.get('hardware_specs', {}).get('ram', '16GB RAM')}",
            f"\n--- HISTORIA Y HECHOS VIVOS QUE CONOCES DE DAVID ---"
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
        """Analiza en segundo plano el texto del usuario para extraer hechos de la historia de David."""
        threading.Thread(
            target=self._analyze_text,
            args=(user_text, assistant_response),
            daemon=True
        ).start()

    def _analyze_text(self, user_text: str, assistant_response: str):
        text = user_text.strip()
        t_low = text.lower()

        # Patrones heurísticos de aprendizaje personal y profesional
        patterns = [
            (r"(?:yo\s+)?nací\s+en\s+([^.,;\n]+)", "biografia", "David nació en {0}."),
            (r"(?:tengo|cumplí)\s+(\d{1,2}\s+años)", "biografia", "David tiene {0} de edad."),
            (r"(?:mi\s+lenguaje\s+favorito|lo\s+que\s+más\s+programo|prefiero\s+programar\s+en)\s+(?:es\s+)?([^.,;\n]+)", "preferencia", "El lenguaje preferido o más programado por David es {0}."),
            (r"(?:estoy\s+trabajando\s+en|mi\s+proyecto\s+actual\s+es|estoy\s+desarrollando)\s+([^.,;\n]+)", "proyectos", "Proyecto activo de David: {0}."),
            (r"(?:recuerdo\s+que|hace\s+tiempo|en\s+el\s+pasado|cuando\s+estudiaba|cuando\s+trabajé)\s+([^.,;\n]+)", "experiencia", "Experiencia pasada de David: {0}."),
            (r"(?:mi\s+meta|mi\s+sueño|mi\s+objetivo)\s+es\s+([^.,;\n]+)", "vision", "Meta u objetivo de David: {0}."),
            (r"(?:me\s+gusta|me\s+apasiona|prefiero)\s+([^.,;\n]+)", "preferencia", "A David le interesa/apasiona: {0}."),
            (r"(?:construí|diseñé|diseñamos|calculé)\s+([^.,;\n]+)", "proyectos", "Logro o diseño técnico de David: {0}.")
        ]

        for regex, cat, template in patterns:
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) > 3 and not extracted.startswith("que "):
                    formatted = template.format(extracted)
                    self.add_memory(formatted, category=cat, importance=4)
                    return

# Instancia singleton accesible
memory_manager = FrondaMemoryManager()
