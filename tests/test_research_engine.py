"""
Tests unitarios para el motor de investigación multi-fuente de Fronda.
"""
from unittest.mock import patch, MagicMock
from skills.research_engine import (
    search_duckduckgo,
    search_wikipedia,
    search_github,
    synthesize_research
)


def test_search_wikipedia_success():
    mock_payload = b'{"title": "Cybersyn", "extract": "El proyecto Synco o Cybersyn fue un sistema cibernetico chileno.", "content_urls": {"desktop": {"page": "https://es.wikipedia.org/wiki/Cybersyn"}}}'
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_wikipedia("Cybersyn")
        assert result is not None
        assert result["title"] == "Cybersyn"
        assert "chileno" in result["extract"]


def test_search_wikipedia_not_found():
    import urllib.error
    mock_error = urllib.error.HTTPError("url", 404, "Not Found", {}, None)

    with patch("urllib.request.urlopen", side_effect=mock_error):
        result = search_wikipedia("terminoinexistentexyz123")
        assert result is None


def test_search_github_mock():
    mock_payload = b'{"items": [{"full_name": "civersen222/CynCo", "description": "Cybernetic Collaborator", "stargazers_count": 120, "html_url": "https://github.com/civersen222/CynCo"}]}'
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = search_github("CynCo")
        assert len(results) == 1
        assert results[0]["name"] == "civersen222/CynCo"
        assert results[0]["stars"] == "120"


def test_synthesize_research_github():
    mock_items = [{"name": "fronda/repo", "description": "Asistente IA", "stars": "50", "url": "url"}]
    with patch("skills.research_engine.search_github", return_value=mock_items):
        summary = synthesize_research("busca repositorio de fronda", preferred_source="github")
        assert "GitHub" in summary
        assert "fronda/repo" in summary


def test_synthesize_research_wikipedia():
    with patch("skills.research_engine.search_wikipedia", return_value={"title": "Python", "extract": "Python es un lenguaje de programacion interpretado."}):
        summary = synthesize_research("qué es python")
        assert "Wikipedia" in summary
        assert "lenguaje de programacion" in summary


def test_synthesize_empty_query():
    summary = synthesize_research("")
    assert "indica qué deseas" in summary.lower()
