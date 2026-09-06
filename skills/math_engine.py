"""
Fronda 1.0 - Mathematical and Scientific Safe AST Engine
Resuelve cálculos científicos y aritméticos en sub-milisegundos sin alucinaciones numéricas.
"""
import ast
import math
import re
from typing import Tuple

SAFE_MATH_OPERATORS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'sqrt': math.sqrt, 'isqrt': math.isqrt, 'cbrt': getattr(math, 'cbrt', lambda x: x ** (1/3)),
    'log': math.log, 'log10': math.log10, 'log2': math.log2, 'exp': math.exp,
    'pi': math.pi, 'e': math.e, 'tau': math.tau,
    'abs': abs, 'round': round, 'pow': pow, 'ceil': math.ceil, 'floor': math.floor
}

def evaluate_math_expression(expr_str: str) -> Tuple[bool, str]:
    """Evalúa de forma segura una expresión matemática compleja usando AST."""
    clean = (expr_str.replace('^', '**')
                     .replace('×', '*')
                     .replace('÷', '/')
                     .replace('x', '*')
                     .strip())
    
    clean = re.sub(r'sen\b', 'sin', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+c[uú]bica\s+de\s+', 'cbrt(', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+cuadrada\s+de\s+', 'sqrt(', clean, flags=re.IGNORECASE)
    clean = re.sub(r'ra[ií]z\s+', 'sqrt(', clean, flags=re.IGNORECASE)

    open_p = clean.count('(')
    close_p = clean.count(')')
    if open_p > close_p:
        clean += ')' * (open_p - close_p)

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.UnaryOp):
            val = _eval_node(node.operand)
            if isinstance(node.op, ast.UAdd): return +val
            if isinstance(node.op, ast.USub): return -val
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.Pow): return left ** right
            if isinstance(node.op, ast.Mod): return left % right
            if isinstance(node.op, ast.FloorDiv): return left // right
        elif isinstance(node, ast.Call):
            func_name = getattr(node.func, 'id', None)
            if func_name in SAFE_MATH_OPERATORS:
                args = [_eval_node(arg) for arg in node.args]
                return SAFE_MATH_OPERATORS[func_name](*args)
            raise ValueError(f"Función matemática no permitida: {func_name}")
        raise TypeError(f"Nodo no soportado: {type(node)}")

    try:
        tree = ast.parse(clean, mode='eval')
        result = _eval_node(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 5)
        return True, str(result)
    except Exception:
        return False, ""
