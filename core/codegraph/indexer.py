"""
Indexador y Coordinador del Grafo de Código.
Escanea el proyecto, extrae símbolos mediante AST, vectoriza y construye el grafo en Kùzu.
"""

import os
from typing import Dict, List, Optional, Set
from core.codegraph.ast_parser import ASTParser, ParsedModule
from core.codegraph.embedder import CodeEmbedder
from core.codegraph.graph_db import CodeGraphDB


class CodeGraphIndexer:
    IGNORE_DIRS = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
        ".kuzu_codegraph",
        "node_modules",
        "scratch",
        ".agents",
        "logs",
    }

    def __init__(
        self,
        repo_root: str,
        db_path: str = ".kuzu_codegraph",
        embedder: Optional[CodeEmbedder] = None,
    ):
        self.repo_root = os.path.abspath(repo_root)
        self.db = CodeGraphDB(db_path=os.path.join(self.repo_root, db_path))
        self.embedder = embedder or CodeEmbedder()
        self.vector_index: Dict[str, List[float]] = {}
        self.symbol_metadata: Dict[str, Dict] = {}

    def index_all(self, reset: bool = True) -> Dict[str, int]:
        """Indexa completamente el repositorio y construye el grafo."""
        if reset:
            self.db.reset_database()
            self.vector_index.clear()
            self.symbol_metadata.clear()

        # 1. Descubrir todos los archivos .py
        py_files = []
        for root, dirs, files in os.walk(self.repo_root):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

        # 2. Parsear todos los módulos sintácticamente
        parsed_modules: Dict[str, ParsedModule] = {}
        func_name_map: Dict[str, List[str]] = {}  # name -> list of function IDs

        for file_path in py_files:
            parsed = ASTParser.parse_file(file_path, self.repo_root)
            if parsed:
                parsed_modules[parsed.path] = parsed
                for f_id, f_sym in parsed.functions.items():
                    func_name_map.setdefault(f_sym.name, []).append(f_id)

        # 3. Insertar Nodos en Kùzu
        for mod_path, mod in parsed_modules.items():
            self.db.insert_module(mod.path, mod.name)

            for c_id, cls in mod.classes.items():
                self.db.insert_class(
                    class_id=cls.id,
                    name=cls.name,
                    file_path=cls.file_path,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                    docstring=cls.docstring,
                )
                self.db.create_relation("DEFINES_CLASS", mod_path, c_id)

            for f_id, func in mod.functions.items():
                self.db.insert_function(
                    func_id=func.id,
                    name=func.name,
                    file_path=func.file_path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    docstring=func.docstring,
                    signature=func.signature,
                )
                if func.parent_class:
                    parent_cls_id = f"{func.file_path}::{func.parent_class}"
                    self.db.create_relation("CONTAINS_METHOD", parent_cls_id, f_id)
                else:
                    self.db.create_relation("DEFINES_FUNC", mod_path, f_id)

                # Generar embedding semántico del símbolo (docstring + firma)
                sem_text = f"Function {func.name} signature {func.signature}. {func.docstring}"
                try:
                    vec = self.embedder.embed_text(sem_text)
                    self.vector_index[f_id] = vec
                    self.symbol_metadata[f_id] = {
                        "name": func.name,
                        "file_path": func.file_path,
                        "signature": func.signature,
                        "line": func.line_start,
                    }
                except Exception:
                    pass

        # 4. Resolver Relaciones de Llamadas e Imports
        for mod_path, mod in parsed_modules.items():
            # Relaciones de IMPORTS
            for imp in mod.imports:
                # Buscar si el import corresponde a un módulo local
                for candidate_path, target_mod in parsed_modules.items():
                    if (
                        target_mod.name == imp
                        or candidate_path.replace(".py", "").replace("/", ".") == imp
                    ):
                        self.db.create_relation("IMPORTS", mod_path, candidate_path)

            # Relaciones de CALLS
            for f_id, func in mod.functions.items():
                for called_name in func.calls:
                    target_ids = func_name_map.get(called_name, [])
                    if not target_ids:
                        continue

                    # Priorizar si está en el mismo archivo
                    same_file = [tid for tid in target_ids if tid.startswith(f"{func.file_path}::")]
                    if same_file:
                        for tid in same_file:
                            self.db.create_relation("CALLS", f_id, tid)
                    else:
                        # O conectar a candidatos relevantes
                        for tid in target_ids[:2]:
                            self.db.create_relation("CALLS", f_id, tid)

        stats = self.db.get_stats()
        stats["py_files_scanned"] = len(py_files)
        return stats

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Búsqueda semántica vectorial de funciones y componentes por intención en lenguaje natural."""
        if not self.vector_index:
            return self.db.search_symbols(query, limit=top_k)

        query_vec = self.embedder.embed_text(query)
        scores = []
        for f_id, vec in self.vector_index.items():
            sim = self.embedder.cosine_similarity(query_vec, vec)
            meta = self.symbol_metadata.get(f_id, {})
            # Boost si el nombre de la función coincide con términos de la consulta
            if meta.get("name", "").lower() in query.lower():
                sim += 0.3
            scores.append((sim, f_id, meta))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, f_id, meta in scores[:top_k]:
            results.append(
                {
                    "id": f_id,
                    "similarity": round(float(sim), 4),
                    "name": meta.get("name", ""),
                    "file_path": meta.get("file_path", ""),
                    "signature": meta.get("signature", ""),
                    "line": meta.get("line", 1),
                }
            )
        return results
