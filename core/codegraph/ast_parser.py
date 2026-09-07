"""
Parser sintáctico basado en el árbol AST de Python.
Extrae de forma determinista:
- Nodos: Module, Class, Function / Method.
- Relaciones: IMPORTS, DEFINES, INHERITS, CALLS.
"""

import ast
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class FunctionSymbol:
    id: str
    name: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str
    signature: str
    parent_class: Optional[str] = None
    calls: Set[str] = field(default_factory=set)


@dataclass
class ClassSymbol:
    id: str
    name: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)


@dataclass
class ParsedModule:
    path: str
    name: str
    imports: Set[str] = field(default_factory=set)
    classes: Dict[str, ClassSymbol] = field(default_factory=dict)
    functions: Dict[str, FunctionSymbol] = field(default_factory=dict)


class CodeASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

        self.imports: Set[str] = set()
        self.classes: Dict[str, ClassSymbol] = {}
        self.functions: Dict[str, FunctionSymbol] = {}

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_id = f"{self.file_path}::{node.name}"
        docstring = ast.get_docstring(node) or ""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attr_name(base)}")

        cls_symbol = ClassSymbol(
            id=class_id,
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            docstring=docstring.strip(),
            bases=bases,
        )
        self.classes[class_id] = cls_symbol

        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)

    def _process_function(self, node):
        if self.current_class:
            func_id = f"{self.file_path}::{self.current_class}.{node.name}"
            class_id = f"{self.file_path}::{self.current_class}"
            if class_id in self.classes:
                self.classes[class_id].methods.append(func_id)
        else:
            func_id = f"{self.file_path}::{node.name}"

        docstring = ast.get_docstring(node) or ""
        args = [a.arg for a in node.args.args]
        signature = f"{node.name}({', '.join(args)})"

        func_symbol = FunctionSymbol(
            id=func_id,
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            docstring=docstring.strip(),
            signature=signature,
            parent_class=self.current_class,
        )
        self.functions[func_id] = func_symbol

        previous_func = self.current_function
        self.current_function = func_id
        self.generic_visit(node)
        self.current_function = previous_func

    def visit_Call(self, node: ast.Call):
        if self.current_function and self.current_function in self.functions:
            called_name = None
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr

            if called_name:
                self.functions[self.current_function].calls.add(called_name)
        self.generic_visit(node)

    def _get_attr_name(self, node: ast.Attribute) -> str:
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))


class ASTParser:
    @staticmethod
    def parse_file(file_path: str, repo_root: str) -> Optional[ParsedModule]:
        """Parsea un archivo Python y retorna la estructura del módulo."""
        try:
            rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/")
            module_name = os.path.splitext(os.path.basename(file_path))[0]

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            visitor = CodeASTVisitor(file_path=rel_path, module_name=module_name)
            visitor.visit(tree)

            return ParsedModule(
                path=rel_path,
                name=module_name,
                imports=visitor.imports,
                classes=visitor.classes,
                functions=visitor.functions,
            )
        except Exception as e:
            # En caso de sintaxis incompatible o archivo corrupto, omitir de forma segura
            return None
