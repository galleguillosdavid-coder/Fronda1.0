"""
Pruebas unitarias para las nuevas habilidades instaladas:
- hardware_analysis (analiza mi computador)
- weather (clima en tiempo real)
- cognitive_graph (grafo de memoria cognitiva)
- pdf_reader (lector de PDFs)
- media_convert (conversor de formatos)
"""

import os
import sys
sys.path.insert(0, ".")
import pytest
from fronda_skills import dispatch_skill_intent


def test_hardware_analysis_dispatch():
    ok, name, res = dispatch_skill_intent("analiza mi computador")
    assert ok is True
    assert name == "hardware_analysis"
    assert "ANÁLISIS COMPLETO DE TU COMPUTADOR" in res
    assert "Procesador (CPU)" in res
    assert "Memoria RAM" in res
    assert "Tarjeta Gráfica (GPU)" in res


def test_weather_dispatch():
    ok, name, res = dispatch_skill_intent("cómo va estar el clima hoy")
    assert ok is True
    assert name == "weather"
    assert "CLIMA ACTUAL" in res or "No se pudo obtener" in res


def test_cognitive_graph_dispatch():
    ok, name, res = dispatch_skill_intent("hazme un grafo de tu memoria cognitiva")
    assert ok is True
    assert name == "cognitive_graph"
    assert "GRAFO DE MEMORIA COGNITIVA" in res
    assert "mermaid" in res


def test_pdf_reader_dispatch():
    ok, name, res = dispatch_skill_intent("leer pdf Arquitectura_Sistema_Multiagente_FrondaBrick_WSL.pdf")
    assert ok is True
    assert name == "pdf_reader"
    assert "DOCUMENTO PDF LEÍDO EXITOSAMENTE" in res
    assert "Arquitectura Multi-Agente" in res


def test_september_18_dispatch():
    ok, name, res = dispatch_skill_intent("18 de septiembre")
    assert ok is True
    assert name == "september_18"
    assert "18 DE SEPTIEMBRE — FIESTAS PATRIAS DE CHILE" in res
    assert "Primera Junta Nacional de Gobierno" in res


def test_holidays_dispatch():
    ok, name, res = dispatch_skill_intent("cuándo es el próximo feriado")
    assert ok is True
    assert name == "holidays"
    assert "PRÓXIMO FERIADO OFICIAL" in res


def test_screen_vision_dispatch():
    ok, name, res = dispatch_skill_intent("mira mi pantalla y lee este error")
    assert ok is True
    assert name == "screen_vision"
    assert "ANÁLISIS DE VISIÓN MULTIMODAL" in res or "capturas/" in res or "No se pudo" in res or "Error" in res


def test_nlp_extraction():
    from fronda_nlp import extract_entities, is_available
    assert is_available() is True
    entities = extract_entities("David Galleguillos vive en Santiago de Chile")
    assert any(ent[0] == "David Galleguillos" or "David" in ent[0] for ent in entities)

