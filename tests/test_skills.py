"""
Tests del dispatcher de skills — Fronda 1.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
import fronda_skills


# ─── Hora y Fecha ─────────────────────────────────────────────────────────────
def test_skill_time_date():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("qué hora es")
    assert has_skill
    assert name == "time_date"
    assert ":" in result  # formato HH:MM


def test_skill_date():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("qué fecha es")
    assert has_skill
    assert name == "time_date"
    assert "/" in result


# ─── Telemetría ───────────────────────────────────────────────────────────────
def test_skill_telemetry():
    mock_data = {
        "cpu_percent": 25.5, "ram_used_gb": 4.2, "ram_total_gb": 16.0,
        "ram_percent": 26.0, "disk_free_gb": 200.0, "disk_percent": 50.0
    }
    with patch("fronda_skills.get_system_telemetry", return_value=mock_data):
        has_skill, name, result = fronda_skills.dispatch_skill_intent("diagnóstico del sistema")
        assert has_skill
        assert name == "telemetry"
        assert "25.5" in result


# ─── OS Info ──────────────────────────────────────────────────────────────────
def test_skill_os_info():
    with patch("fronda_skills.get_os_info", return_value="Sistema: Windows 11"):
        has_skill, name, result = fronda_skills.dispatch_skill_intent("qué sistema operativo tengo")
        assert has_skill
        assert name == "os_info"


# ─── Cálculos Matemáticos ─────────────────────────────────────────────────────
def test_skill_math_simple():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("cuánto es 2 + 2")
    assert has_skill
    assert name == "math_calc"
    assert "4" in result


def test_skill_math_cbrt():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("raíz cúbica de 8")
    assert has_skill
    assert name == "math_calc"
    assert "2" in result


def test_skill_math_trig():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("calcula sin(0)")
    assert has_skill
    assert name == "math_calc"
    assert "0" in result


# ─── Volumen ──────────────────────────────────────────────────────────────────
def test_skill_volume():
    with patch("fronda_skills.set_system_volume", return_value="Volumen ajustado al 50%."):
        has_skill, name, result = fronda_skills.dispatch_skill_intent("pon el volumen al 50")
        assert has_skill
        assert name == "volume"
        assert "50" in result


def test_skill_mute():
    with patch("fronda_skills.mute_system_volume", return_value="Audio silenciado."):
        has_skill, name, result = fronda_skills.dispatch_skill_intent("silencia el audio")
        assert has_skill
        assert name == "mute"


def test_skill_unmute():
    with patch("fronda_skills.mute_system_volume", return_value="Audio reactivado."):
        has_skill, name, result = fronda_skills.dispatch_skill_intent("reactiva el audio del sistema")
        assert has_skill
        assert name == "unmute"


# ─── Skills Summary ───────────────────────────────────────────────────────────
def test_skill_capabilities():
    has_skill, name, result = fronda_skills.dispatch_skill_intent("qué puedes hacer")
    assert has_skill
    assert name == "skills_summary"
    assert len(result) > 50


# ─── Sin match ────────────────────────────────────────────────────────────────
def test_no_skill_match():
    has_skill, name, result = fronda_skills.dispatch_skill_intent(
        "cuéntame sobre la arquitectura de microservicios en Rust"
    )
    assert not has_skill
    assert name == ""
    assert result == ""


# ─── Tickets de limitación ───────────────────────────────────────────────────
def test_check_limitation_detected():
    ticket = fronda_skills.check_for_skill_limitation(
        "leer PDF", "No sé cómo leer archivos PDF."
    )
    assert ticket is not None
    assert ticket.get("categoria") == "procesamiento_archivos"


def test_check_no_limitation():
    ticket = fronda_skills.check_for_skill_limitation(
        "hola", "¡Hola! ¿En qué puedo ayudarte hoy?"
    )
    assert ticket is None
