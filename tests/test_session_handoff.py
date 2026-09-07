"""
Tests unitarios para el gestor de relevo entre sesiones (Handoff) de Fronda.
"""
from pathlib import Path
from core.session_handoff import SessionHandoffManager


def test_session_handoff_initial_greeting(tmp_path: Path):
    handoff_file = tmp_path / "test_handoff.json"
    mgr = SessionHandoffManager(filepath=handoff_file)
    greeting = mgr.get_greeting_briefing("David")
    assert "¡Hola David!" in greeting
    assert "inicializados" in greeting


def test_session_handoff_record_and_briefing(tmp_path: Path):
    handoff_file = tmp_path / "test_handoff.json"
    mgr = SessionHandoffManager(filepath=handoff_file)

    mgr.record_turn(
        user_query="optimizar motor de búsqueda BM25",
        topic="Arquitectura BM25",
        decision="Adoptar fórmula Robertson-Spärck Jones"
    )

    data = mgr.get_handoff_summary()
    assert data["last_user_intent"] == "optimizar motor de búsqueda BM25"
    assert "Arquitectura BM25" in data["active_topics"]
    assert len(data["recent_decisions"]) == 1

    greeting = mgr.get_greeting_briefing("David")
    assert "Arquitectura BM25" in greeting
    assert "¿Deseas continuar con eso" in greeting
