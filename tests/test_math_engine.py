"""
Tests del motor matemático AST — Fronda 1.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from skills.math_engine import evaluate_math_expression


# ─── Aritmética básica ────────────────────────────────────────────────────────
@pytest.mark.parametrize("expr, expected", [
    ("2 + 2",      "4"),
    ("10 - 3",     "7"),
    ("4 * 5",      "20"),
    ("10 / 4",     "2.5"),
    ("7 // 2",     "3"),
    ("10 % 3",     "1"),
    ("2 ** 10",    "1024"),
    ("2 ^ 10",     "1024"),        # alias para **
    ("-5 + 10",    "5"),
    ("(2 + 3) * 4","20"),
])
def test_arithmetic(expr, expected):
    ok, result = evaluate_math_expression(expr)
    assert ok, f"No se pudo evaluar: {expr}"
    assert result == expected, f"{expr} → {result!r}, esperado {expected!r}"


# ─── Trigonometría ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("expr, approx_val", [
    ("sin(0)",    0.0),
    ("cos(0)",    1.0),
    ("tan(0)",    0.0),
])
def test_trig(expr, approx_val):
    ok, result = evaluate_math_expression(expr)
    assert ok
    assert abs(float(result) - approx_val) < 1e-4


# ─── Funciones matemáticas ────────────────────────────────────────────────────
@pytest.mark.parametrize("expr, approx_val", [
    ("sqrt(4)",    2.0),
    ("sqrt(9)",    3.0),
    ("log10(100)", 2.0),
    ("log2(8)",    3.0),
    ("abs(-7)",    7.0),
    ("ceil(2.1)",  3.0),
    ("floor(2.9)", 2.0),
    ("round(2.567, 2)", 2.57),
])
def test_math_functions(expr, approx_val):
    ok, result = evaluate_math_expression(expr)
    assert ok, f"No se pudo evaluar: {expr}"
    assert abs(float(result) - approx_val) < 1e-4


# ─── Constantes ──────────────────────────────────────────────────────────────
def test_pi():
    ok, result = evaluate_math_expression("pi")
    assert ok
    assert abs(float(result) - 3.14159) < 0.0001


def test_euler():
    ok, result = evaluate_math_expression("e")
    assert ok
    assert abs(float(result) - 2.71828) < 0.0001


# ─── Alias en español ─────────────────────────────────────────────────────────
def test_spanish_sqrt():
    ok, result = evaluate_math_expression("raíz cuadrada de 16")
    assert ok
    assert result == "4"


def test_spanish_cbrt():
    ok, result = evaluate_math_expression("raíz cúbica de 27")
    assert ok
    assert abs(float(result) - 3.0) < 0.001


def test_spanish_sen():
    ok, result = evaluate_math_expression("sen(0)")
    assert ok
    assert float(result) == 0.0


# ─── Casos que deben fallar ───────────────────────────────────────────────────
@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo')",
    "eval('1+1')",
    "open('file.txt')",
    "print('hello')",
])
def test_unsafe_expressions_rejected(expr):
    ok, _ = evaluate_math_expression(expr)
    assert not ok, f"Expresión peligrosa no fue rechazada: {expr}"


# ─── División por cero ────────────────────────────────────────────────────────
def test_division_by_zero():
    ok, _ = evaluate_math_expression("1 / 0")
    assert not ok


# ─── Expresión vacía ─────────────────────────────────────────────────────────
def test_empty_expression():
    ok, result = evaluate_math_expression("")
    assert not ok or result == ""
