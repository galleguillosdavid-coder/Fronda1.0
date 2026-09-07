"""
Servidor MCP (Model Context Protocol) nativo sobre stdio para Antigravity.
Expone herramientas de consulta topológica, búsqueda semántica y cálculo de blast radius
desde la base de conocimiento vectorial en Kùzu.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

from core.codegraph.embedder import CodeEmbedder
from core.codegraph.graph_db import CodeGraphDB
from core.codegraph.indexer import CodeGraphIndexer


class MCPServer:
    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.indexer = CodeGraphIndexer(repo_root=self.repo_root)
        self.db = self.indexer.db

    def run_stdio(self):
        """Bucle principal de escucha JSON-RPC sobre stdin/stdout."""
        # Asegurar UTF-8 en stdin/stdout
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue

                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    out = json.dumps(response, ensure_ascii=False) + "\n"
                    sys.stdout.write(out)
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)},
                }
                out = json.dumps(err_resp) + "\n"
                sys.stdout.write(out)
                sys.stdout.flush()

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Notificaciones sin id
        if req_id is None and method == "notifications/initialized":
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "antigravity-codegraph-mcp",
                        "version": "1.0.0",
                    },
                },
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self._get_tools_manifest()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            return self._call_tool(req_id, tool_name, tool_args)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }

    def _get_tools_manifest(self) -> list:
        return [
            {
                "name": "codegraph_query",
                "description": (
                    "Búsqueda semántica o por nombre en el grafo de conocimiento vectorial de código. "
                    "Devuelve funciones, clases, firmas y similitud para encontrar componentes exactos."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Consulta en lenguaje natural o nombre de símbolo a buscar.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Cantidad máxima de resultados.",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "codegraph_get_subgraph",
                "description": (
                    "Extrae quirúrgicamente el subgrafo alrededor de un símbolo (función o clase): "
                    "ubicación, firma, docstring, quién lo llama (incoming) y a quién llama (outgoing)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Nombre o ID del símbolo (ej. 'iniciar_servidor' o 'fronda_memory.py::FrondaMemory').",
                        }
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "codegraph_calculate_blast_radius",
                "description": (
                    "Calcula el radio de impacto transitivo (Blast Radius) antes de modificar o refactorizar código. "
                    "Identifica todos los llamadores y archivos dependientes para no generar breaking changes."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Nombre de la función, clase o módulo a analizar.",
                        },
                        "max_hops": {
                            "type": "integer",
                            "description": "Profundidad transitiva del grafo (1 a 5 saltos).",
                            "default": 3,
                        },
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "codegraph_reindex",
                "description": "Reindexa completamente el espacio de trabajo en la base de datos de grafos Kùzu.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reset": {
                            "type": "boolean",
                            "description": "Si es True, reinicia la base de datos antes de reindexar.",
                            "default": True,
                        }
                    },
                },
            },
        ]

    def _call_tool(self, req_id: Any, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "codegraph_query":
                query = args.get("query", "")
                top_k = args.get("top_k", 5)
                res = self.indexer.semantic_search(query, top_k=top_k)
                content_text = json.dumps(res, indent=2, ensure_ascii=False)

            elif name == "codegraph_get_subgraph":
                symbol = args.get("symbol", "")
                res = self.db.get_symbol_subgraph(symbol)
                content_text = json.dumps(res, indent=2, ensure_ascii=False)

            elif name == "codegraph_calculate_blast_radius":
                symbol = args.get("symbol", "")
                max_hops = args.get("max_hops", 3)
                res = self.db.calculate_blast_radius(symbol, max_hops=max_hops)
                content_text = json.dumps(res, indent=2, ensure_ascii=False)

            elif name == "codegraph_reindex":
                reset = args.get("reset", True)
                stats = self.indexer.index_all(reset=reset)
                content_text = json.dumps(stats, indent=2, ensure_ascii=False)

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not recognized: {name}"},
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": content_text}]
                },
            }
        except Exception as err:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Error ejecutando {name}: {str(err)}"}],
                },
            }


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    server = MCPServer(repo_root=repo)
    server.run_stdio()
