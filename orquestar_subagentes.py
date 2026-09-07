"""
CLI de Orquestación Topológica para Megaproyectos en Antigravity.
Permite descomponer cualquier tarea en subagentes paralelos usando el grafo Kùzu.

Uso:
    python orquestar_subagentes.py "<objetivo>" "<símbolo_o_módulo>"
Ejemplo:
    python orquestar_subagentes.py "Refactorizar caché de memoria" search_memories
"""

import json
import sys
from core.codegraph.orchestrator import TopologicalOrchestrator


def main():
    if len(sys.argv) < 3:
        print("Uso: python orquestar_subagentes.py \"<objetivo>\" \"<símbolo_o_módulo>\"")
        print("Ejemplo: python orquestar_subagentes.py \"Optimizar búsqueda semántica\" search_memories")
        sys.exit(1)

    objective = sys.argv[1]
    symbol = sys.argv[2]

    print(f"[*] Analizando topología en Kùzu para objetivo: '{objective}'...")
    print(f"[*] Símbolo de anclaje: '{symbol}'\n")

    orchestrator = TopologicalOrchestrator()
    plan = orchestrator.plan_parallel_subagents(objective=objective, target_symbol_or_query=symbol)

    print("=" * 70)
    print("      PLAN TOPOLÓGICO DE PARTICIÓN MULTI-SUBAGENTE")
    print("=" * 70)
    print(f"Objetivo          : {plan['objective']}")
    print(f"Símbolo Primario  : {plan['target_symbol']}")
    blast = plan["blast_radius_summary"]
    print(f"Nivel de Riesgo   : {blast['risk_level']}")
    print(f"Dependientes      : {blast['total_dependents']}")
    print(f"Archivos en Riesgo: {', '.join(blast['affected_files']) if blast['affected_files'] else 'Ninguno'}")
    print("-" * 70)

    print("\n[PAQUETES DE TRABAJO PARA SUBAGENTES EN PARALELO]:\n")
    for i, pkg in enumerate(plan["subagent_packages"], 1):
        print(f"--- Subagente {i}: {pkg['role']} ({pkg['agent_id']}) ---")
        print(f"  * Archivos Asignados (Edición) : {pkg['target_files']}")
        print(f"  * Archivos Bloqueados (Lectura): {pkg['read_only_files']}")
        print(f"  * Misión                        : {pkg['objective']}")
        print(f"  * Comando de Verificación      : {pkg['verification_command']}")
        print()

    print("-" * 70)
    print("[GUÍA ARQUITECTÓNICA DE FRONDA BRICK (CAPA 3)]:")
    print(plan.get("cognitive_clone_guidance", "N/A"))
    print("=" * 70)


if __name__ == "__main__":
    main()
