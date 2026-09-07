"""
Tests de verificación de dependencias instaladas (C18.3) — Fronda 1.0
Verifica que las dependencias requeridas estén instaladas y reporta cuáles faltan.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import importlib
import pytest


# ─── Dependencias requeridas ──────────────────────────────────────────────────
REQUIRED_DEPS = [
    ("psutil",              "psutil"),
    ("edge_tts",            "edge-tts"),
    ("duckduckgo_search",   "duckduckgo-search"),
]

# Dependencias opcionales — no fallan el test, solo reportan
OPTIONAL_DEPS = [
    ("pygame",                  "pygame-ce"),
    ("comtypes",                "comtypes"),
    ("pycaw",                   "pycaw"),
    ("mss",                     "mss"),
    ("screen_brightness_control", "screen-brightness-control"),
    ("spacy",                   "spacy"),
]


def _check_dep(import_name: str) -> bool:
    """Retorna True si el módulo puede importarse."""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


@pytest.mark.parametrize("import_name,pkg_name", REQUIRED_DEPS)
def test_required_dependency_installed(import_name, pkg_name):
    """Las dependencias requeridas deben estar instaladas."""
    assert _check_dep(import_name), (
        f"Dependencia requerida faltante: '{import_name}'. "
        f"Instalar con: pip install {pkg_name}"
    )


def test_optional_dependencies_report():
    """
    Informa qué dependencias opcionales están disponibles.
    Este test siempre pasa — solo genera un reporte informativo.
    """
    missing = []
    present = []
    for import_name, pkg_name in OPTIONAL_DEPS:
        if _check_dep(import_name):
            present.append(import_name)
        else:
            missing.append(pkg_name)

    print(f"\n[Deps Opcionales] Instaladas: {present}")
    if missing:
        print(f"[Deps Opcionales] Faltantes (no requeridas): {missing}")
        print(f"  → Instalar con: pip install {' '.join(missing)}")

    assert True  # siempre pasa


def test_config_loads_correctly():
    """Verifica que config.py carga sin errores."""
    import config
    cfg = config.get()
    assert cfg.ollama.url.startswith("http")
    assert cfg.server.port > 0
    assert cfg.user.nickname


def test_fronda_logger_initializes():
    """Verifica que el logger se inicializa correctamente."""
    from fronda_logger import get_logger
    log = get_logger("test.deps")
    assert log is not None


def test_math_engine_importable():
    """Verifica que el motor matemático es importable y funcional."""
    from skills.math_engine import evaluate_math_expression
    ok, result = evaluate_math_expression("2 + 2")
    assert ok
    assert result == "4"


def test_system_engine_importable():
    """Verifica que el motor de sistema es importable."""
    from skills.system_engine import get_system_telemetry, get_os_info
    assert callable(get_system_telemetry)
    assert callable(get_os_info)


def test_skill_registry_importable():
    """Verifica que el SkillRegistry es importable."""
    from fronda_skill_registry import SkillRegistry, Skill
    reg = SkillRegistry()
    assert len(reg) == 0


def test_nlp_module_importable():
    """Verifica que fronda_nlp se importa aunque spaCy no esté disponible."""
    import fronda_nlp
    # is_available() puede ser True o False — no importa
    # Lo importante es que no lanza excepción al importar
    assert hasattr(fronda_nlp, "is_available")
    assert hasattr(fronda_nlp, "extract_entities")
