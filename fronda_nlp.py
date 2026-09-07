"""
Fronda 1.0 - Extractor NLP con spaCy (C17)
Mejora el extractor de memorias usando NLP real para detectar entidades nombradas.
Requiere: pip install spacy && python -m spacy download es_core_news_sm

Uso:
    from fronda_nlp import extract_entities, categorize_memory_with_nlp
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from fronda_logger import get_logger

log = get_logger("fronda.nlp")

# ─── Carga lazy del modelo spaCy ─────────────────────────────────────────────
_nlp = None
_NLP_MODEL = "es_core_news_sm"
_SPACY_AVAILABLE = False


def _get_nlp():
    """Carga el modelo spaCy de forma lazy al primer uso."""
    global _nlp, _SPACY_AVAILABLE
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        _nlp = spacy.load(_NLP_MODEL)
        _SPACY_AVAILABLE = True
        log.info(f"spaCy cargado: modelo '{_NLP_MODEL}'")
    except ImportError:
        log.warning("spaCy no está instalado. Instalar con: pip install spacy")
    except OSError:
        log.warning(
            f"Modelo spaCy '{_NLP_MODEL}' no encontrado. "
            f"Instalar con: python -m spacy download {_NLP_MODEL}"
        )
    return _nlp


def is_available() -> bool:
    """Retorna True si spaCy y el modelo están disponibles."""
    return _get_nlp() is not None


# ─── Mapeo de tipos de entidad spaCy → categoría Fronda ─────────────────────
_ENTITY_CATEGORY_MAP = {
    "PER":  "persona",       # Personas nombradas
    "LOC":  "lugar",         # Lugares, ciudades, países
    "ORG":  "organizacion",  # Organizaciones, empresas
    "MISC": "general",       # Misceláneos (tecnologías, eventos)
    "DATE": "fecha",         # Fechas y expresiones temporales
    "TIME": "tiempo",        # Expresiones de tiempo
    "MONEY": "economia",     # Cantidades monetarias
    "PERCENT": "estadistica",# Porcentajes
    "GPE":  "lugar",         # Entidades geopolíticas (si el modelo lo usa)
    "PRODUCT": "tecnologia", # Productos/software
}


def extract_entities(text: str) -> List[Tuple[str, str, str]]:
    """
    Extrae entidades nombradas del texto usando spaCy.
    
    Retorna lista de tuplas: (texto_entidad, tipo_spacy, categoria_fronda)
    Retorna lista vacía si spaCy no está disponible.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []
    
    try:
        doc = nlp(text)
        entities = []
        for ent in doc.ents:
            categoria = _ENTITY_CATEGORY_MAP.get(ent.label_, "general")
            entities.append((ent.text, ent.label_, categoria))
        return entities
    except Exception as e:
        log.error(f"Error al extraer entidades NLP: {e}")
        return []


def categorize_memory_with_nlp(text: str) -> Optional[str]:
    """
    Sugiere una categoría de memoria basada en las entidades detectadas.
    Retorna la categoría más relevante, o None si no se detectó nada.
    
    Prioridad: persona > lugar > tecnologia > organizacion > fecha > general
    """
    entities = extract_entities(text)
    if not entities:
        return None

    priority = ["persona", "lugar", "tecnologia", "organizacion", "fecha", "general"]
    cats_found = {cat for _, _, cat in entities}
    
    for cat in priority:
        if cat in cats_found:
            return cat
    return "general"


def extract_memory_from_text_nlp(
    text: str,
    nickname: str = "el usuario"
) -> Optional[Tuple[str, str, int]]:
    """
    Intenta extraer un recuerdo relevante del texto usando NLP.
    Retorna (contenido, categoria, importancia) o None.
    
    Complementa (no reemplaza) el extractor regex de fronda_memory.py.
    """
    entities = extract_entities(text)
    if not entities:
        return None

    # Seleccionar entidades más relevantes (max 3)
    top_entities = entities[:3]
    ent_descriptions = [f"{ent[0]} ({ent[2]})" for ent in top_entities]
    
    categoria = categorize_memory_with_nlp(text) or "general"
    importancia = 3

    # Ajustar importancia según el tipo de entidad
    cats = {cat for _, _, cat in top_entities}
    if "persona" in cats or "lugar" in cats:
        importancia = 4
    if "tecnologia" in cats:
        importancia = 4

    contenido = (
        f"Entidades detectadas en mensaje de {nickname}: "
        f"{', '.join(ent_descriptions)}. "
        f"Contexto: '{text[:120].strip()}'"
    )
    return contenido, categoria, importancia


def enrich_memory_extraction(
    user_text: str,
    nickname: str,
    memory_manager
) -> None:
    """
    Enriquece la extracción de memorias con NLP.
    Llama a memory_manager.add_memory() si se detectan entidades relevantes.
    Se usa como complemento del sistema regex existente.
    """
    if not is_available():
        return
    
    result = extract_memory_from_text_nlp(user_text, nickname)
    if result:
        contenido, categoria, importancia = result
        # Solo agregar si es suficientemente largo y relevante
        if len(contenido) > 30:
            memory_manager.add_memory(contenido, category=categoria, importance=importancia)
            log.debug(f"[NLP] Memoria enriquecida extraída: {contenido[:60]}...")
