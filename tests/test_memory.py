"""
Tests del motor de memoria — Fronda 1.0
"""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_manager(tmp_path=None):
    """Crea un FrondaMemoryManager con archivo temporal."""
    if tmp_path is None:
        tmp_path = Path(tempfile.mkdtemp()) / "test_memory.json"
    from fronda_memory import FrondaMemoryManager
    return FrondaMemoryManager(filepath=tmp_path)


def test_create_default_file(tmp_path):
    filepath = tmp_path / "mem.json"
    mgr = _make_manager(filepath)
    assert filepath.exists()
    data = mgr.get_data()
    assert "profile" in data
    assert "learned_history" in data


def test_add_memory(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    item = mgr.add_memory("David trabaja en Rust", category="tecnica", importance=5)
    assert item.get("id", "").startswith("mem_")
    assert item["content"] == "David trabaja en Rust"
    assert item["category"] == "tecnica"
    assert item["importance"] == 5


def test_no_duplicate_memory(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    mgr.add_memory("Hecho único de David")
    mgr.add_memory("Hecho único de David")  # duplicado
    data = mgr.get_data()
    count = sum(1 for m in data["learned_history"] if m["content"] == "Hecho único de David")
    assert count == 1


def test_record_interaction(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    before = mgr.get_data().get("stats", {}).get("total_interactions", 0)
    mgr.record_interaction()
    after = mgr.get_data().get("stats", {}).get("total_interactions", 0)
    assert after == before + 1


def test_get_system_context_returns_string(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    ctx = mgr.get_system_context("rust programacion")
    assert isinstance(ctx, str)
    assert len(ctx) > 50


def test_get_system_context_contains_identity(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    ctx = mgr.get_system_context("")
    assert "Fronda 1.0" in ctx or "IDENTIDAD" in ctx


def test_cache_invalidation(tmp_path):
    filepath = tmp_path / "mem.json"
    mgr = _make_manager(filepath)
    mgr.add_memory("Primera memoria")
    mgr.invalidate_cache()
    # Editar el archivo directamente
    data = json.loads(filepath.read_text(encoding="utf-8"))
    data["learned_history"].append({"id": "ext_001", "content": "Memoria externa", "category": "test", "importance": 1})
    filepath.write_text(json.dumps(data), encoding="utf-8")
    # Forzar recarga por mtime cambiado
    import time; time.sleep(0.05)
    Path(filepath).touch()
    mgr._cache_mtime = 0.0  # invalidar
    reloaded = mgr.get_data()
    contents = [m["content"] for m in reloaded["learned_history"]]
    assert "Memoria externa" in contents


def test_add_empty_memory_returns_empty(tmp_path):
    mgr = _make_manager(tmp_path / "mem.json")
    result = mgr.add_memory("   ")
    assert result == {}


def test_deepcopy_default_not_mutated(tmp_path):
    """Verifica que deepcopy previene mutación del template."""
    from fronda_memory import _DEFAULT_MEMORY
    import copy
    original_len = len(_DEFAULT_MEMORY["learned_history"])
    mgr = _make_manager(tmp_path / "mem.json")
    mgr.add_memory("test mutacion")
    assert len(_DEFAULT_MEMORY["learned_history"]) == original_len
