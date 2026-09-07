"""
Tests unitarios para la recuperación de memoria con BM25 en Fronda.
"""
from fronda_memory import BM25Scorer, _tokenize, FrondaMemoryManager
from pathlib import Path
import json


def test_tokenize_stopwords_removed():
    tokens = _tokenize("El creador de la inteligencia artificial en Chile")
    assert "el" not in tokens
    assert "de" not in tokens
    assert "la" not in tokens
    assert "en" not in tokens
    assert "creador" in tokens
    assert "inteligencia" in tokens
    assert "artificial" in tokens
    assert "chile" in tokens


def test_bm25_scorer_ranking():
    corpus = [
        "David trabaja como ingeniero de software en Python y Linux.",
        "Le gusta el café expreso por las mañanas.",
        "Tiene experiencia en diseño de sistemas distribuidos y ciberseguridad.",
        "Desarrolla el asistente inteligente Fronda con arquitectura modular."
    ]
    scorer = BM25Scorer(corpus)
    scores = scorer.score("asistente inteligente fronda")

    # El documento 3 ("Desarrolla el asistente inteligente Fronda...") debe tener el score más alto
    max_idx = scores.index(max(scores))
    assert max_idx == 3
    assert scores[3] > 0.5


def test_memory_manager_search_memories(tmp_path: Path):
    test_file = tmp_path / "test_memory.json"
    data = {
        "profile": {"name": "David", "nickname": "David"},
        "learned_history": [
            {"id": "1", "content": "Le apasiona la robótica y la visión computacional.", "importance": 3},
            {"id": "2", "content": "Su comida favorita son los tallarines con salsa bolognesa.", "importance": 2},
            {"id": "3", "content": "Configuró un servidor WSL2 con Ubuntu en Windows 11.", "importance": 4}
        ],
        "acquired_skills": [],
        "stats": {}
    }
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    manager = FrondaMemoryManager(filepath=test_file)
    results = manager.search_memories("servidor ubuntu wsl2", top_k=2)

    assert len(results) >= 1
    assert "WSL2" in results[0]["content"]
