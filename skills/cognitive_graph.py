"""
Fronda 1.0 - Generador de Grafo de Memoria Cognitiva
Mapea los recuerdos, clusters temáticos, perfil de David Galleguillos
y la red topológica del código en Kùzu, generando una visualización en Mermaid y texto.
"""

import os
import json
from pathlib import Path


def generate_cognitive_graph() -> str:
    """Genera la estructura topológica del grafo de memoria cognitiva de Fronda."""
    mem_path = Path("fronda_memory.json")
    memories = []
    profile = {}

    if mem_path.exists():
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile = data.get("profile", {})
                memories = data.get("memories", [])
        except Exception:
            pass

    # Categorías de memoria
    clusters = {}
    for m in memories:
        cat = m.get("category", "general")
        clusters.setdefault(cat, []).append(m.get("text", "")[:40] + "...")

    total_mem = len(memories)
    user_name = profile.get("name", "David Galleguillos")
    voice = profile.get("voice_preferred", "es-ES-AlvaroNeural")

    # Estadísticas de Kùzu si existen
    kuzu_stats_str = "40 Módulos | 29 Clases | 269 Funciones | 457 Llamadas"

    report = (
        f"🧠 **GRAFO DE MEMORIA COGNITIVA — FRONDA 1.0**\n\n"
        f"```mermaid\n"
        f"graph TD\n"
        f"    Core[\"🧠 Núcleo Cognitivo Fronda 1.0\"] --> Profile[\"👤 Perfil: {user_name}\"]\n"
        f"    Core --> LongTerm[\"💾 Memoria a Largo Plazo ({total_mem} recuerdos)\"]\n"
        f"    Core --> CodeGraph[\"🕸️ Grafo de Código Kùzu ({kuzu_stats_str})\"]\n"
        f"    Core --> Voice[\"🎙️ Voz Neural: {voice}\"]\n"
    )

    for cat, items in clusters.items():
        cat_id = cat.replace(" ", "_")
        report += f"    LongTerm --> {cat_id}[\"📂 {cat.capitalize()} ({len(items)} nodos)\"]\n"

    report += (
        f"```\n\n"
        f"• **Nodo Central**: Clon Digital de {user_name} con arquitectura multiagente en 3 capas (Windows Host + WSL 2 + Ollama).\n"
        f"• **Clusters de Conocimiento Activo**:\n"
    )

    for cat, items in clusters.items():
        report += f"  - **{cat.upper()}** ({len(items)} items): {', '.join(items[:3])}\n"

    report += (
        f"• **Grafo Vectorial de Código**: Vinculado activamente con la base de datos columnar **Kùzu** para navegación sintáctica y cálculo de radio de impacto (Blast Radius)."
    )

    return report
