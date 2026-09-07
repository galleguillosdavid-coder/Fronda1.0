"""
Fronda 1.0 - Motor de Investigación Multi-Fuente (Inspirado en CynCo)
Permite a Fronda realizar búsquedas en tiempo real en múltiples fuentes abiertas:
- DuckDuckGo (web general y noticias)
- Wikipedia (resúmenes enciclopédicos directos vía REST API)
- GitHub (repositorios, proyectos y tecnologías vía API pública)
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any, Optional

from fronda_logger import get_logger

log = get_logger("fronda.skills.research")

_USER_AGENT = "FrondaAssistant/1.0 (Cybernetic AI Assistant; contact: user@fronda.local)"


def search_duckduckgo(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Busca en DuckDuckGo usando la librería duckduckgo_search.
    Retorna lista de diccionarios con 'title', 'snippet' y 'url'.
    """
    results: List[Dict[str, str]] = []
    if not query or not query.strip():
        return results

    clean_query = query.strip()
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(clean_query, max_results=max_results))
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", item.get("snippet", "")),
                    "url": item.get("href", item.get("link", ""))
                })
        log.info(f"DuckDuckGo: {len(results)} resultados para '{clean_query}'")
    except Exception as e:
        log.warning(f"Error consultando DuckDuckGo: {e}")
        # Fallback HTTP mínimo a API DuckDuckGo Instant Answer
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                abstract = data.get("AbstractText", "")
                heading = data.get("Heading", "")
                if abstract:
                    results.append({
                        "title": heading or clean_query,
                        "snippet": abstract,
                        "url": data.get("AbstractURL", "")
                    })
        except Exception as e_fallback:
            log.warning(f"Fallback DuckDuckGo falló: {e_fallback}")

    return results


def search_wikipedia(query: str, lang: str = "es") -> Optional[Dict[str, str]]:
    """
    Consulta la REST API de Wikipedia para obtener el extracto introductorio de un término.
    Retorna diccionario con 'title', 'extract', 'url' o None si no se encuentra.
    """
    if not query or not query.strip():
        return None

    clean_query = query.strip()
    endpoint = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_query)}"
    req = urllib.request.Request(endpoint, headers={"User-Agent": _USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                extract = data.get("extract", "")
                title = data.get("title", clean_query)
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                if extract:
                    log.info(f"Wikipedia ({lang}): Encontrado artículo '{title}'")
                    return {
                        "title": title,
                        "extract": extract,
                        "url": page_url
                    }
    except urllib.error.HTTPError as he:
        if he.code == 404:
            log.info(f"Wikipedia: '{clean_query}' no encontrado (404)")
        else:
            log.warning(f"Wikipedia HTTP {he.code} para '{clean_query}'")
    except Exception as e:
        log.warning(f"Error consultando Wikipedia: {e}")

    return None


def search_github(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Busca repositorios públicos en GitHub ordenados por estrellas.
    Retorna lista de diccionarios con 'name', 'description', 'stars', 'url'.
    """
    results: List[Dict[str, str]] = []
    if not query or not query.strip():
        return results

    clean_query = query.strip()
    endpoint = f"https://api.github.com/search/repositories?q={urllib.parse.quote(clean_query)}&sort=stars&per_page={max_results}"
    req = urllib.request.Request(endpoint, headers={
        "User-Agent": _USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    })

    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                for it in items[:max_results]:
                    results.append({
                        "name": it.get("full_name", ""),
                        "description": it.get("description", "") or "Sin descripción",
                        "stars": str(it.get("stargazers_count", 0)),
                        "url": it.get("html_url", "")
                    })
                log.info(f"GitHub: {len(results)} repos encontrados para '{clean_query}'")
    except Exception as e:
        log.warning(f"Error consultando GitHub API: {e}")

    return results


def synthesize_research(query: str, preferred_source: str = "auto") -> str:
    """
    Orquesta la investigación multi-fuente y entrega un resumen conciso
    diseñado para ser leído por voz (TTS) o mostrado en la interfaz.
    """
    if not query or not query.strip():
        return "Por favor indica qué deseas que investigue."

    clean_query = query.strip()

    # 1. Búsqueda específica en GitHub si se pide explícitamente
    if preferred_source == "github" or "github" in clean_query.lower() or "repositorio" in clean_query.lower():
        gh_query = clean_query.lower().replace("github", "").replace("repositorios", "").replace("repositorio", "").strip()
        gh_results = search_github(gh_query or clean_query, max_results=3)
        if gh_results:
            lines = [f"Encontré {len(gh_results)} proyectos destacados en GitHub:"]
            for r in gh_results:
                lines.append(f"• {r['name']} (⭐ {r['stars']}): {r['description']}")
            return "\n".join(lines)
        return f"No encontré repositorios públicos en GitHub para '{clean_query}'."

    # 2. Búsqueda en Wikipedia para definiciones / personalidades / historia
    if preferred_source in ("wiki", "wikipedia") or preferred_source == "auto":
        wiki = search_wikipedia(clean_query)
        if wiki:
            summary = wiki["extract"]
            sentences = summary.split(". ")
            short_summary = ". ".join(sentences[:3])
            if not short_summary.endswith("."):
                short_summary += "."
            return f"Según Wikipedia: {short_summary}"

    # 3. Búsqueda web en DuckDuckGo (para noticias, cosas recientes o si Wikipedia falló)
    ddg_results = search_duckduckgo(clean_query, max_results=3)
    if ddg_results:
        snippets = []
        for res in ddg_results:
            if res.get("snippet"):
                snippets.append(f"• {res['title']}: {res['snippet']}")
        if snippets:
            return "Información encontrada en la web:\n" + "\n".join(snippets)

    return f"No encontré información relevante sobre '{clean_query}' en las fuentes consultadas."
