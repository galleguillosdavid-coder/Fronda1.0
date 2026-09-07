"""
Orquestador Topológico Multi-Subagente para Antigravity.
Utiliza el Grafo de Código Vectorial (Kùzu) y el puente con WSL2/Fronda Brick
para particionar tareas complejas en subagentes paralelos sin conflictos.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.codegraph.graph_db import CodeGraphDB
from core.codegraph.indexer import CodeGraphIndexer
from fronda_bridge import FrondaBridge


@dataclass
class SubagentWorkPackage:
    agent_id: str
    role: str
    target_files: List[str]
    read_only_files: List[str]
    surgical_context: Dict[str, Any]
    objective: str
    verification_command: str


class TopologicalOrchestrator:
    def __init__(self, repo_root: str = "."):
        self.repo_root = os.path.abspath(repo_root)
        self.indexer = CodeGraphIndexer(repo_root=self.repo_root)
        self.db = self.indexer.db
        self.bridge = FrondaBridge()

    def plan_parallel_subagents(
        self,
        objective: str,
        target_symbol_or_query: str,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """
        Particiona una tarea de megaproyecto en paquetes de trabajo desacoplados
        para subagentes de Antigravity basándose en la topología de Kùzu.
        """
        # 1. Búsqueda topológica y semántica del objetivo
        matches = self.indexer.semantic_search(target_symbol_or_query, top_k=3)
        primary_symbol = target_symbol_or_query
        if matches:
            primary_symbol = matches[0]["name"]

        # 2. Obtener el subgrafo quirúrgico del símbolo principal
        subgraph = self.db.get_symbol_subgraph(primary_symbol)

        # 3. Calcular Blast Radius (radio de impacto de dependencias)
        blast = self.db.calculate_blast_radius(primary_symbol, max_hops=max_hops)

        # 4. Asignación de fronteras por subagente
        # Subagente 1: Core Developer (Modifica el archivo raíz del componente)
        primary_file = (
            subgraph.get("details", {}).get("file_path")
            or (matches[0]["file_path"] if matches else "unknown")
        )
        core_files = [primary_file] if primary_file != "unknown" else []

        # Subagente 2: Adapter / Caller Agent (Modifica archivos dependientes de producción)
        dependent_files = [
            f for f in blast["affected_files"]
            if f not in core_files and not f.startswith("tests/")
        ]

        # Subagente 3: QA & Verification Agent (Ejecuta y adapta los tests afectados en WSL2)
        test_files = [
            f for f in blast["affected_files"]
            if f.startswith("tests/")
        ]
        if not test_files and os.path.exists(os.path.join(self.repo_root, "tests")):
            test_files = ["tests/test_codegraph.py"]

        # 5. Estructurar paquetes de trabajo
        packages = []

        # Agente Core
        packages.append(
            SubagentWorkPackage(
                agent_id="subagent_core_dev",
                role="Desarrollador Núcleo",
                target_files=core_files,
                read_only_files=dependent_files,
                surgical_context={
                    "symbol": primary_symbol,
                    "subgraph": subgraph,
                },
                objective=f"Implementar {objective} en {core_files}, manteniendo la compatibilidad con llamadores.",
                verification_command=f"python -m py_compile {' '.join(core_files)}",
            )
        )

        # Agente Adaptador (si hay dependientes de producción)
        if dependent_files:
            packages.append(
                SubagentWorkPackage(
                    agent_id="subagent_integration_adapter",
                    role="Adaptador de Integración",
                    target_files=dependent_files,
                    read_only_files=core_files,
                    surgical_context={
                        "incoming_callers": blast["direct_and_indirect_callers"],
                        "risk_level": blast["risk_level"],
                    },
                    objective=f"Actualizar las llamadas y contratos en {dependent_files} para reflejar los cambios en {primary_symbol}.",
                    verification_command=f"python -m py_compile {' '.join(dependent_files)}",
                )
            )

        # Agente QA
        packages.append(
            SubagentWorkPackage(
                agent_id="subagent_qa_wsl",
                role="Verificación QA en WSL2",
                target_files=test_files,
                read_only_files=core_files + dependent_files,
                surgical_context={
                    "impacted_tests": test_files,
                },
                objective=f"Ejecutar y actualizar las suites de prueba {test_files} en el entorno Linux de WSL2.",
                verification_command=f"wsl.exe -d Ubuntu -e bash -c 'pytest {' '.join(test_files)}'",
            )
        )

        # 6. Validación arquitectónica con el clon cognitivo de David (Capa 3)
        opinion_clon = "Sin conexión con Capa 3"
        try:
            health = self.bridge.check_health()
            if health.get("status") == "online":
                models = health.get("models", [])
                model_to_use = None
                for m in ["frondabrick", "fronda", "llama3.2:3b"]:
                    if any(m in tag for tag in models):
                        model_to_use = m
                        break
                if model_to_use:
                    self.bridge.model = model_to_use
                consulta = (
                    f"Como arquitecto David Galleguillos de Fronda: "
                    f"¿Qué precauciones recomiendas al modificar '{primary_symbol}' "
                    f"cuyo radio de impacto afecta a: {blast['affected_files']}?"
                )
                opinion_clon = self.bridge.ask_clone(consulta, num_ctx=1024)
        except Exception:
            pass

        return {
            "objective": objective,
            "target_symbol": primary_symbol,
            "blast_radius_summary": {
                "risk_level": blast["risk_level"],
                "total_dependents": blast["total_dependents"],
                "affected_files": blast["affected_files"],
            },
            "subagent_packages": [
                {
                    "agent_id": pkg.agent_id,
                    "role": pkg.role,
                    "target_files": pkg.target_files,
                    "read_only_files": pkg.read_only_files,
                    "objective": pkg.objective,
                    "verification_command": pkg.verification_command,
                }
                for pkg in packages
            ],
            "cognitive_clone_guidance": opinion_clon,
        }
