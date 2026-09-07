"""
Gestor de Base de Datos para el Grafo de Código en Kùzu.
Proporciona operaciones de inserción, consultas de topología, subgrafos compactos
y cálculo de radio de impacto (Blast Radius).
"""

import os
import shutil
from typing import Any, Dict, List, Optional
import kuzu

from core.codegraph.schema import initialize_schema


class CodeGraphDB:
    def __init__(self, db_path: str = ".kuzu_codegraph"):
        self.db_path = db_path
        self._db: Optional[kuzu.Database] = None
        self._conn: Optional[kuzu.Connection] = None
        self._connect()

    def _connect(self):
        """Inicializa la base de datos Kùzu y su conexión."""
        # Asegurarse de que el directorio padre exista si tiene subcarpetas
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        self._db = kuzu.Database(self.db_path)
        self._conn = kuzu.Connection(self._db)
        initialize_schema(self._conn)

    def close(self):
        """Cierra la conexión y libera los recursos de la base de datos."""
        self._conn = None
        self._db = None

    def reset_database(self):
        """Limpia y reinicia la base de datos desde cero."""
        self.close()
        if os.path.exists(self.db_path):
            if os.path.isdir(self.db_path):
                shutil.rmtree(self.db_path, ignore_errors=True)
            else:
                try:
                    os.remove(self.db_path)
                except OSError:
                    pass
        self._connect()

    def _escape_str(self, val: Any) -> str:
        if val is None:
            return ""
        s = str(val)
        return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")

    def insert_module(self, path: str, name: str):
        path_esc = self._escape_str(path)
        name_esc = self._escape_str(name)
        q = f"CREATE (m:Module {{path: '{path_esc}', name: '{name_esc}'}});"
        try:
            self._conn.execute(q)
        except Exception:
            pass

    def insert_class(
        self,
        class_id: str,
        name: str,
        file_path: str,
        line_start: int,
        line_end: int,
        docstring: str = "",
    ):
        q = (
            f"CREATE (c:Class {{"
            f"id: '{self._escape_str(class_id)}', "
            f"name: '{self._escape_str(name)}', "
            f"file_path: '{self._escape_str(file_path)}', "
            f"line_start: {int(line_start)}, "
            f"line_end: {int(line_end)}, "
            f"docstring: '{self._escape_str(docstring)}'"
            f"}});"
        )
        try:
            self._conn.execute(q)
        except Exception:
            pass

    def insert_function(
        self,
        func_id: str,
        name: str,
        file_path: str,
        line_start: int,
        line_end: int,
        docstring: str = "",
        signature: str = "",
    ):
        q = (
            f"CREATE (f:Function {{"
            f"id: '{self._escape_str(func_id)}', "
            f"name: '{self._escape_str(name)}', "
            f"file_path: '{self._escape_str(file_path)}', "
            f"line_start: {int(line_start)}, "
            f"line_end: {int(line_end)}, "
            f"docstring: '{self._escape_str(docstring)}', "
            f"signature: '{self._escape_str(signature)}'"
            f"}});"
        )
        try:
            self._conn.execute(q)
        except Exception:
            pass

    def create_relation(self, rel_type: str, from_id: str, to_id: str):
        from_esc = self._escape_str(from_id)
        to_esc = self._escape_str(to_id)

        if rel_type == "IMPORTS":
            q = (
                f"MATCH (a:Module), (b:Module) "
                f"WHERE a.path = '{from_esc}' AND b.path = '{to_esc}' "
                f"CREATE (a)-[:IMPORTS]->(b);"
            )
        elif rel_type == "CALLS":
            q = (
                f"MATCH (a:Function), (b:Function) "
                f"WHERE a.id = '{from_esc}' AND b.id = '{to_esc}' "
                f"CREATE (a)-[:CALLS]->(b);"
            )
        elif rel_type == "DEFINES_FUNC":
            q = (
                f"MATCH (a:Module), (b:Function) "
                f"WHERE a.path = '{from_esc}' AND b.id = '{to_esc}' "
                f"CREATE (a)-[:DEFINES_FUNC]->(b);"
            )
        elif rel_type == "DEFINES_CLASS":
            q = (
                f"MATCH (a:Module), (b:Class) "
                f"WHERE a.path = '{from_esc}' AND b.id = '{to_esc}' "
                f"CREATE (a)-[:DEFINES_CLASS]->(b);"
            )
        elif rel_type == "CONTAINS_METHOD":
            q = (
                f"MATCH (a:Class), (b:Function) "
                f"WHERE a.id = '{from_esc}' AND b.id = '{to_esc}' "
                f"CREATE (a)-[:CONTAINS_METHOD]->(b);"
            )
        elif rel_type == "INHERITS":
            q = (
                f"MATCH (a:Class), (b:Class) "
                f"WHERE a.id = '{from_esc}' AND b.id = '{to_esc}' "
                f"CREATE (a)-[:INHERITS]->(b);"
            )
        else:
            return

        try:
            self._conn.execute(q)
        except Exception:
            pass

    def calculate_blast_radius(self, symbol: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Calcula el radio de impacto transitivo de modificar una función, clase o módulo.
        Devuelve todos los llamadores a 1..max_hops saltos.
        """
        sym_esc = self._escape_str(symbol)
        max_hops = max(1, min(max_hops, 5))

        # 1. Buscar llamadores transitivos de la función
        q_calls = (
            f"MATCH (caller:Function)-[:CALLS*1..{max_hops}]->(target:Function) "
            f"WHERE target.id = '{sym_esc}' OR target.name = '{sym_esc}' "
            f"RETURN DISTINCT caller.id, caller.name, caller.file_path, caller.line_start, target.name;"
        )

        callers = []
        try:
            res = self._conn.execute(q_calls)
            while res.has_next():
                row = res.get_next()
                callers.append(
                    {
                        "caller_id": row[0],
                        "caller_name": row[1],
                        "file_path": row[2],
                        "line": row[3],
                        "target_name": row[4],
                    }
                )
        except Exception:
            pass

        # 2. Buscar clases que heredan de esta clase
        q_inherits = (
            f"MATCH (child:Class)-[:INHERITS*1..{max_hops}]->(parent:Class) "
            f"WHERE parent.id = '{sym_esc}' OR parent.name = '{sym_esc}' "
            f"RETURN DISTINCT child.id, child.name, child.file_path, child.line_start;"
        )

        inheritors = []
        try:
            res_inh = self._conn.execute(q_inherits)
            while res_inh.has_next():
                row = res_inh.get_next()
                inheritors.append(
                    {
                        "class_id": row[0],
                        "name": row[1],
                        "file_path": row[2],
                        "line": row[3],
                    }
                )
        except Exception:
            pass

        # 3. Módulos que importan este módulo
        q_imports = (
            f"MATCH (importer:Module)-[:IMPORTS]->(target:Module) "
            f"WHERE target.path = '{sym_esc}' OR target.name = '{sym_esc}' "
            f"RETURN DISTINCT importer.path, importer.name;"
        )

        dependent_modules = []
        try:
            res_imp = self._conn.execute(q_imports)
            while res_imp.has_next():
                row = res_imp.get_next()
                dependent_modules.append({"path": row[0], "name": row[1]})
        except Exception:
            pass

        files_affected = sorted(
            list(
                set(
                    [c["file_path"] for c in callers]
                    + [inh["file_path"] for inh in inheritors]
                    + [m["path"] for m in dependent_modules]
                )
            )
        )

        risk_level = "LOW"
        total_dependents = len(callers) + len(inheritors) + len(dependent_modules)
        if total_dependents > 15 or len(files_affected) > 5:
            risk_level = "CRITICAL"
        elif total_dependents > 5 or len(files_affected) > 2:
            risk_level = "HIGH"
        elif total_dependents > 0:
            risk_level = "MEDIUM"

        return {
            "symbol": symbol,
            "risk_level": risk_level,
            "total_dependents": total_dependents,
            "affected_files_count": len(files_affected),
            "affected_files": files_affected,
            "direct_and_indirect_callers": callers,
            "inheritors": inheritors,
            "dependent_modules": dependent_modules,
        }

    def get_symbol_subgraph(self, symbol: str) -> Dict[str, Any]:
        """
        Extrae el subgrafo compacto alrededor de un símbolo:
        - Definición (firma, docstring, ubicación)
        - Quien lo llama (Incoming)
        - A quién llama (Outgoing)
        - Clases o módulos que lo contienen
        """
        sym_esc = self._escape_str(symbol)

        # 1. Obtener detalles de la función
        q_func = (
            f"MATCH (f:Function) "
            f"WHERE f.id = '{sym_esc}' OR f.name = '{sym_esc}' "
            f"RETURN f.id, f.name, f.file_path, f.line_start, f.line_end, f.docstring, f.signature LIMIT 1;"
        )

        target_info = None
        try:
            res = self._conn.execute(q_func)
            if res.has_next():
                row = res.get_next()
                target_info = {
                    "type": "Function",
                    "id": row[0],
                    "name": row[1],
                    "file_path": row[2],
                    "line_start": row[3],
                    "line_end": row[4],
                    "docstring": row[5],
                    "signature": row[6],
                }
        except Exception:
            pass

        if not target_info:
            # Intentar buscar como Clase
            q_cls = (
                f"MATCH (c:Class) "
                f"WHERE c.id = '{sym_esc}' OR c.name = '{sym_esc}' "
                f"RETURN c.id, c.name, c.file_path, c.line_start, c.line_end, c.docstring LIMIT 1;"
            )
            try:
                res_cls = self._conn.execute(q_cls)
                if res_cls.has_next():
                    row = res_cls.get_next()
                    target_info = {
                        "type": "Class",
                        "id": row[0],
                        "name": row[1],
                        "file_path": row[2],
                        "line_start": row[3],
                        "line_end": row[4],
                        "docstring": row[5],
                    }
            except Exception:
                pass

        if not target_info:
            return {"symbol": symbol, "found": False, "message": "Symbol not found in graph"}

        target_id_esc = self._escape_str(target_info["id"])

        incoming_calls = []
        outgoing_calls = []

        if target_info["type"] == "Function":
            # Incoming CALLS
            q_in = (
                f"MATCH (caller:Function)-[:CALLS]->(target:Function) "
                f"WHERE target.id = '{target_id_esc}' "
                f"RETURN caller.id, caller.name, caller.file_path, caller.line_start LIMIT 20;"
            )
            try:
                res_in = self._conn.execute(q_in)
                while res_in.has_next():
                    row = res_in.get_next()
                    incoming_calls.append({"id": row[0], "name": row[1], "file_path": row[2], "line": row[3]})
            except Exception:
                pass

            # Outgoing CALLS
            q_out = (
                f"MATCH (target:Function)-[:CALLS]->(callee:Function) "
                f"WHERE target.id = '{target_id_esc}' "
                f"RETURN callee.id, callee.name, callee.file_path, callee.line_start LIMIT 20;"
            )
            try:
                res_out = self._conn.execute(q_out)
                while res_out.has_next():
                    row = res_out.get_next()
                    outgoing_calls.append({"id": row[0], "name": row[1], "file_path": row[2], "line": row[3]})
            except Exception:
                pass

        return {
            "symbol": symbol,
            "found": True,
            "details": target_info,
            "incoming_calls": incoming_calls,
            "outgoing_calls": outgoing_calls,
        }

    def search_symbols(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Busca símbolos por coincidencia parcial en nombre o archivo."""
        query_esc = self._escape_str(query)
        q = (
            f"MATCH (f:Function) "
            f"WHERE f.name CONTAINS '{query_esc}' OR f.file_path CONTAINS '{query_esc}' "
            f"RETURN f.id, f.name, f.file_path, f.line_start, f.signature LIMIT {limit};"
        )
        results = []
        try:
            res = self._conn.execute(q)
            while res.has_next():
                row = res.get_next()
                results.append(
                    {
                        "type": "Function",
                        "id": row[0],
                        "name": row[1],
                        "file_path": row[2],
                        "line": row[3],
                        "signature": row[4],
                    }
                )
        except Exception:
            pass

        # Buscar en clases
        q_cls = (
            f"MATCH (c:Class) "
            f"WHERE c.name CONTAINS '{query_esc}' "
            f"RETURN c.id, c.name, c.file_path, c.line_start LIMIT {limit};"
        )
        try:
            res_cls = self._conn.execute(q_cls)
            while res_cls.has_next():
                row = res_cls.get_next()
                results.append(
                    {
                        "type": "Class",
                        "id": row[0],
                        "name": row[1],
                        "file_path": row[2],
                        "line": row[3],
                    }
                )
        except Exception:
            pass

        return results[:limit]

    def get_stats(self) -> Dict[str, int]:
        """Obtiene métricas de volumen del grafo."""
        stats = {"modules": 0, "classes": 0, "functions": 0, "calls": 0}
        queries = {
            "modules": "MATCH (m:Module) RETURN count(m);",
            "classes": "MATCH (c:Class) RETURN count(c);",
            "functions": "MATCH (f:Function) RETURN count(f);",
            "calls": "MATCH ()-[r:CALLS]->() RETURN count(r);",
        }
        for k, q in queries.items():
            try:
                res = self._conn.execute(q)
                if res.has_next():
                    stats[k] = int(res.get_next()[0])
            except Exception:
                pass
        return stats
