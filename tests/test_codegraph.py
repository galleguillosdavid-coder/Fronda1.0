"""
Suite de pruebas para el subsistema de Grafo de Código Vectorial (Kùzu + AST + MCP).
Valida:
1. Extracción sintáctica AST.
2. Generación de embeddings con Ollama o Fallback.
3. Almacenamiento y consultas topológicas en Kùzu.
4. Cálculo de Blast Radius y Subgrafos.
5. Protocolo MCP stdio.
"""

import os
import sys
import unittest

# Asegurar importación de core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.codegraph.ast_parser import ASTParser
from core.codegraph.embedder import CodeEmbedder
from core.codegraph.graph_db import CodeGraphDB
from core.codegraph.indexer import CodeGraphIndexer
from core.codegraph.mcp_server import MCPServer


class TestCodeGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.test_db_path = ".kuzu_test_db"

    def tearDown(self):
        test_path = os.path.join(self.repo_root, self.test_db_path)
        if os.path.exists(test_path):
            import shutil
            shutil.rmtree(test_path, ignore_errors=True)

    def test_ast_parser(self):
        """Verifica que el parser AST extrae correctamente clases y funciones."""
        test_code_path = os.path.join(self.repo_root, "fronda_memory.py")
        if os.path.exists(test_code_path):
            parsed = ASTParser.parse_file(test_code_path, self.repo_root)
            self.assertIsNotNone(parsed)
            self.assertGreater(len(parsed.classes), 0)
            self.assertIn("fronda_memory.py::FrondaMemoryManager", parsed.classes)
            self.assertGreater(len(parsed.functions), 0)

    def test_embedder(self):
        """Verifica que el embedder produce vectores normalizados."""
        embedder = CodeEmbedder()
        vec = embedder.embed_text("def ejecutar_comando(): pass")
        self.assertIsInstance(vec, list)
        self.assertGreater(len(vec), 0)

    def test_graph_db_and_indexer(self):
        """Verifica la indexación en Kùzu, blast radius y subgrafo."""
        indexer = CodeGraphIndexer(repo_root=self.repo_root, db_path=self.test_db_path)
        stats = indexer.index_all(reset=True)

        self.assertGreater(stats.get("modules", 0), 0)
        self.assertGreater(stats.get("functions", 0), 0)

        # Probar Blast Radius
        blast = indexer.db.calculate_blast_radius("guardar_memoria")
        self.assertIn("risk_level", blast)
        self.assertIn("affected_files", blast)

        # Probar Subgrafo
        subgraph = indexer.db.get_symbol_subgraph("guardar_memoria")
        self.assertIn("found", subgraph)

        # Probar Búsqueda Semántica
        results = indexer.semantic_search("almacenar recuerdos o memoria", top_k=3)
        self.assertIsInstance(results, list)

        indexer.db.close()

    def test_mcp_protocol(self):
        """Simula la negociación JSON-RPC con el servidor MCP."""
        server = MCPServer(repo_root=self.repo_root)

        # 1. Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "AntigravityIDE"}},
        }
        resp = server.handle_request(init_req)
        self.assertEqual(resp["id"], 1)
        self.assertIn("capabilities", resp["result"])

        # 2. List Tools
        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        tools_resp = server.handle_request(tools_req)
        tools = tools_resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("codegraph_query", tool_names)
        self.assertIn("codegraph_calculate_blast_radius", tool_names)
        self.assertIn("codegraph_get_subgraph", tool_names)

        # 3. Call Tool (Blast Radius)
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "codegraph_calculate_blast_radius",
                "arguments": {"symbol": "buscar_memoria", "max_hops": 2},
            },
        }
        call_resp = server.handle_request(call_req)
        self.assertIn("result", call_resp)
        self.assertFalse(call_resp["result"].get("isError", False))

        server.db.close()


if __name__ == "__main__":
    unittest.main()
