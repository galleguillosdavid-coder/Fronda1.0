#!/usr/bin/env python3
"""
🌿 FRONDA 1.0 — Visualizador Interactivo de Grafo Kùzu (Vis.js)
Permite explorar gráficamente el grafo de código de Kùzu DB (.kuzu_codegraph),
ejecutar consultas Cypher interactivas en vivo, inspeccionar firmas/docstrings
y exportar a Mermaid o PNG sin requerir Docker.
"""

import os
import sys
import json
import argparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from typing import Dict, Any, List, Tuple

import kuzu

DEFAULT_DB_PATH = ".kuzu_codegraph"
DEFAULT_PORT = 5050


class KuzuGraphExtractor:
    """Extrae subgrafos y ejecuta consultas Cypher transformándolas a nodos y aristas para Vis.js."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"No se encontró la base de datos de Kùzu en: {db_path}")
        # Conexión en modo solo lectura para permitir concurrencia segura
        self.db = kuzu.Database(db_path, read_only=True)
        self.conn = kuzu.Connection(self.db)

    def execute_cypher(self, query: str) -> Dict[str, Any]:
        """Ejecuta una consulta Cypher y extrae nodos y aristas de forma determinista."""
        clean_query = query.strip()
        if not clean_query:
            return {"error": "Consulta Cypher vacía"}

        try:
            result = self.conn.execute(clean_query)
        except Exception as e:
            return {"error": f"Error de sintaxis o ejecución Cypher: {str(e)}"}

        nodes_dict: Dict[str, Dict[str, Any]] = {}
        edges_dict: Dict[str, Dict[str, Any]] = {}
        raw_rows: List[List[Any]] = []

        COLOR_MAP = {
            "Module":   {"bg": "rgba(30, 58, 138, 0.85)", "border": "#3b82f6", "text": "#ffffff", "shape": "box"},
            "Class":    {"bg": "rgba(88, 28, 135, 0.85)", "border": "#a855f7", "text": "#ffffff", "shape": "diamond"},
            "Function": {"bg": "rgba(6, 78, 59, 0.85)",   "border": "#00ffaa", "text": "#ffffff", "shape": "dot"},
        }

        EDGE_COLOR_MAP = {
            "CALLS":           {"color": "#00e5ff", "highlight": "#38bdf8"},
            "DEFINES_FUNC":    {"color": "#00ffaa", "highlight": "#4ade80"},
            "DEFINES_CLASS":   {"color": "#c084fc", "highlight": "#e879f9"},
            "CONTAINS_METHOD": {"color": "#f59e0b", "highlight": "#fbbf24"},
            "IMPORTS":         {"color": "#94a3b8", "highlight": "#cbd5e1"},
            "INHERITS":        {"color": "#ec4899", "highlight": "#f472b6"},
        }

        def _make_node_id(obj: Dict[str, Any]) -> str:
            if isinstance(obj, dict) and "_id" in obj:
                return f"{obj['_id']['table']}_{obj['_id']['offset']}"
            return str(obj.get("id") or obj.get("path") or obj.get("name") or id(obj))

        def _process_node(node: Dict[str, Any]):
            nid = _make_node_id(node)
            if nid in nodes_dict:
                return nid

            lbl = node.get("_label", "Node")
            name = node.get("name") or node.get("path") or "unnamed"
            cfg = COLOR_MAP.get(lbl, {"bg": "#334155", "border": "#64748b", "text": "#fff", "shape": "ellipse"})

            # Crear tooltip detallado
            lines = f"L{node.get('line_start', '?')}-{node.get('line_end', '?')}" if node.get('line_start') else ""
            tooltip = f"<b>{lbl}</b>: {name}<br>📁 {node.get('file_path') or node.get('path') or ''} {lines}"
            if node.get("signature"):
                tooltip += f"<br><code>{node['signature']}</code>"

            nodes_dict[nid] = {
                "id": nid,
                "label": f"{name}",
                "group": lbl,
                "shape": cfg["shape"],
                "color": {
                    "background": cfg["bg"],
                    "border": cfg["border"],
                    "highlight": {"background": "#1e293b", "border": "#ffffff"},
                    "hover": {"border": "#ffffff"}
                },
                "font": {"color": cfg["text"], "face": "Rajdhani, Segoe UI, sans-serif", "size": 13},
                "title": tooltip,
                "properties": {
                    "label": lbl,
                    "name": name,
                    "id": node.get("id") or "",
                    "file_path": node.get("file_path") or node.get("path") or "",
                    "line_start": node.get("line_start"),
                    "line_end": node.get("line_end"),
                    "signature": node.get("signature") or "",
                    "docstring": node.get("docstring") or ""
                }
            }
            return nid

        def _process_edge(rel: Dict[str, Any], src_id: str, dst_id: str):
            lbl = rel.get("_label", "REL")
            edge_key = f"{src_id}->{dst_id}:{lbl}"
            if edge_key in edges_dict:
                return

            c_info = EDGE_COLOR_MAP.get(lbl, {"color": "#64748b", "highlight": "#94a3b8"})
            edges_dict[edge_key] = {
                "from": src_id,
                "to": dst_id,
                "label": lbl,
                "arrows": "to",
                "font": {"size": 9, "color": c_info["color"], "align": "middle"},
                "color": {
                    "color": c_info["color"],
                    "highlight": c_info["highlight"],
                    "hover": "#ffffff"
                },
                "width": 1.5,
                "smooth": {"type": "curvedCW", "roundness": 0.15}
            }

        while result.has_next():
            row = result.get_next()
            row_repr = []
            found_nodes: List[Tuple[str, Dict[str, Any]]] = []
            found_edges: List[Dict[str, Any]] = []

            for col in row:
                if isinstance(col, dict) and "_label" in col and "_id" in col:
                    if "_src" in col and "_dst" in col:
                        # Es una arista
                        found_edges.append(col)
                        row_repr.append(f"[:{col['_label']}]")
                    else:
                        # Es un nodo
                        nid = _process_node(col)
                        found_nodes.append((nid, col))
                        row_repr.append(f"({col['_label']}:{col.get('name', '')})")
                else:
                    row_repr.append(str(col))

            raw_rows.append(row_repr)

            # Si hay aristas explícitas devueltas
            for rel in found_edges:
                src_nid = f"{rel['_src']['table']}_{rel['_src']['offset']}"
                dst_nid = f"{rel['_dst']['table']}_{rel['_dst']['offset']}"
                _process_edge(rel, src_nid, dst_nid)

            # Si la consulta devuelve dos nodos sin arista explícita (e.g. RETURN a, b)
            if len(found_nodes) >= 2 and not found_edges:
                # Si son 2 nodos contiguos, conectarlos genéricamente
                for i in range(len(found_nodes) - 1):
                    _process_edge({"_label": "RELATES_TO"}, found_nodes[i][0], found_nodes[i+1][0])

        return {
            "query": clean_query,
            "nodes": list(nodes_dict.values()),
            "edges": list(edges_dict.values()),
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges_dict),
            "rows_count": len(raw_rows)
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtiene métricas generales de nodos y aristas en la base de datos."""
        stats = {}
        for label in ["Module", "Class", "Function"]:
            try:
                res = self.conn.execute(f"MATCH (n:{label}) RETURN count(n);")
                stats[label] = res.get_next()[0] if res.has_next() else 0
            except Exception:
                stats[label] = 0

        for edge in ["CALLS", "DEFINES_FUNC", "DEFINES_CLASS", "CONTAINS_METHOD", "IMPORTS"]:
            try:
                res = self.conn.execute(f"MATCH ()-[r:{edge}]->() RETURN count(r);")
                stats[edge] = res.get_next()[0] if res.has_next() else 0
            except Exception:
                stats[edge] = 0

        return stats


def generate_html_template(initial_data_json: str, initial_stats_json: str) -> str:
    """Genera el código HTML completo con la interfaz gráfica Vis.js y consola Cypher."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FRONDA 1.0 — Explorador de Grafo Kùzu</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #050811;
      --bg-panel: rgba(9, 17, 30, 0.92);
      --border: rgba(0, 255, 170, 0.22);
      --border-glow: rgba(0, 255, 170, 0.5);
      --emerald: #00ffaa;
      --cyan: #00e5ff;
      --violet: #a855f7;
      --amber: #f59e0b;
      --text: #e2e8f5;
      --muted: #94a3b8;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Rajdhani', sans-serif;
      overflow: hidden;
      display: grid;
      grid-template-rows: 60px auto 1fr;
      height: 100vh;
    }}

    /* ── Header ── */
    header {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 24px;
      backdrop-filter: blur(10px);
      z-index: 10;
    }}
    .logo-box {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .logo-ring {{
      width: 36px; height: 36px; border-radius: 50%;
      border: 2px solid var(--emerald);
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 15px rgba(0, 255, 170, 0.4);
      font-family: 'Orbitron', sans-serif; font-weight: 900;
      color: var(--emerald); font-size: 14px;
    }}
    .logo-title h1 {{
      font-family: 'Orbitron', sans-serif; font-size: 16px;
      letter-spacing: 1.5px; color: #fff;
    }}
    .logo-title p {{
      font-size: 11px; color: var(--muted); font-family: 'Fira Code', monospace;
    }}

    .stats-bar {{
      display: flex; gap: 12px; font-family: 'Fira Code', monospace; font-size: 11px;
    }}
    .stat-badge {{
      padding: 4px 10px; border-radius: 6px; background: rgba(0,0,0,0.4);
      border: 1px solid var(--border); display: flex; gap: 6px; align-items: center;
    }}
    .stat-badge b {{ color: var(--emerald); }}

    /* ── Barra de Consultas Cypher ── */
    #query-panel {{
      background: rgba(4, 9, 18, 0.95);
      border-bottom: 1px solid var(--border);
      padding: 10px 24px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 10;
    }}
    .query-input-row {{
      display: flex; gap: 10px; align-items: center;
    }}
    #cypher-input {{
      flex: 1;
      background: rgba(0, 0, 0, 0.6);
      border: 1px solid rgba(0, 229, 255, 0.35);
      border-radius: 8px;
      padding: 10px 14px;
      color: #00ffaa;
      font-family: 'Fira Code', monospace;
      font-size: 13px;
      outline: none;
      transition: all 0.25s;
    }}
    #cypher-input:focus {{
      border-color: var(--cyan);
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.3);
    }}
    .btn {{
      padding: 9px 16px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(0, 255, 170, 0.12);
      color: var(--emerald);
      font-family: 'Orbitron', sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      cursor: pointer;
      display: flex; align-items: center; gap: 6px;
      transition: all 0.25s;
    }}
    .btn:hover {{
      background: rgba(0, 255, 170, 0.25);
      box-shadow: 0 0 15px rgba(0, 255, 170, 0.4);
      transform: translateY(-1px);
    }}
    .btn.secondary {{
      background: rgba(168, 85, 247, 0.12);
      border-color: rgba(168, 85, 247, 0.4);
      color: #c084fc;
    }}
    .btn.secondary:hover {{
      background: rgba(168, 85, 247, 0.25);
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
    }}

    .presets-row {{
      display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
      font-size: 11px; color: var(--muted);
    }}
    .chip {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      padding: 3px 10px; border-radius: 12px;
      cursor: pointer; font-family: 'Fira Code', monospace;
      transition: all 0.2s;
    }}
    .chip:hover {{
      border-color: var(--emerald); color: var(--emerald);
      background: rgba(0,255,170,0.08);
    }}

    /* ── Main Canvas & Inspector ── */
    #main-content {{
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    #network {{
      width: 100%; height: 100%;
      background: radial-gradient(circle at center, #070e1c 0%, #03060c 100%);
    }}

    /* Floating Inspector Drawer */
    #inspector {{
      position: absolute;
      top: 16px; right: -420px;
      width: 400px; max-height: calc(100% - 32px);
      background: rgba(6, 12, 22, 0.94);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: -10px 0 35px rgba(0,0,0,0.8);
      backdrop-filter: blur(14px);
      padding: 18px;
      display: flex; flex-direction: column; gap: 14px;
      z-index: 20;
      transition: right 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      overflow-y: auto;
    }}
    #inspector.open {{ right: 16px; }}

    .inspector-header {{
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid var(--border); padding-bottom: 10px;
    }}
    .inspector-header h3 {{
      font-family: 'Orbitron', sans-serif; font-size: 14px;
      color: var(--emerald); letter-spacing: 1px;
    }}
    .btn-close {{
      background: none; border: none; color: var(--muted);
      cursor: pointer; font-size: 16px; font-weight: bold;
    }}
    .btn-close:hover {{ color: #fff; }}

    .field-label {{
      font-family: 'Fira Code', monospace; font-size: 10px;
      text-transform: uppercase; color: var(--cyan); margin-bottom: 3px;
    }}
    .field-value {{
      font-family: 'Fira Code', monospace; font-size: 12px;
      word-break: break-all; color: var(--text);
    }}
    .code-box {{
      background: rgba(0,0,0,0.5);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px; padding: 8px 10px;
      font-family: 'Fira Code', monospace; font-size: 11px;
      max-height: 180px; overflow-y: auto; white-space: pre-wrap;
    }}

    /* Control Toolbar Over Canvas */
    #toolbar {{
      position: absolute; bottom: 20px; left: 24px;
      background: rgba(9, 17, 30, 0.88);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 14px;
      display: flex; gap: 12px; align-items: center;
      backdrop-filter: blur(8px);
      z-index: 10;
    }}
    #search-box {{
      background: rgba(0,0,0,0.5);
      border: 1px solid var(--border);
      border-radius: 6px; padding: 5px 10px;
      color: #fff; font-family: 'Fira Code', monospace;
      font-size: 12px; outline: none; width: 160px;
    }}
    #search-box:focus {{ border-color: var(--emerald); width: 220px; }}

    .legend {{
      display: flex; gap: 8px; font-size: 11px; font-family: 'Fira Code', monospace;
    }}
    .legend-tag {{
      display: flex; align-items: center; gap: 4px;
    }}
    .dot {{ width: 9px; height: 9px; border-radius: 50%; }}
  </style>
</head>
<body>

  <!-- ── Header ── -->
  <header>
    <div class="logo-box">
      <div class="logo-ring">K</div>
      <div class="logo-title">
        <h1>FRONDA 1.0 — KÙZU GRAPH EXPLORER</h1>
        <p>Topología de Código Vectorial &bull; .kuzu_codegraph &bull; Motor Nativo</p>
      </div>
    </div>
    <div class="stats-bar" id="stats-container">
      <!-- Inyectado dinámicamente -->
    </div>
  </header>

  <!-- ── Cypher Query Panel ── -->
  <div id="query-panel">
    <div class="query-input-row">
      <input type="text" id="cypher-input" value="MATCH (a)-[r:CALLS]->(b) RETURN a, r, b LIMIT 120;" placeholder="Escribe tu consulta Cypher (ej. MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 50)...">
      <button class="btn" id="btn-run" onclick="runCypher()">▶ EJECUTAR</button>
      <button class="btn secondary" id="btn-freeze" onclick="togglePhysics()">⏸ PAUSAR FÍSICA</button>
      <button class="btn secondary" id="btn-mermaid" onclick="exportMermaid()">📋 MERMAID</button>
    </div>
    <div class="presets-row">
      <span>Consultas Rápidas:</span>
      <span class="chip" onclick="setPreset(1)">⚡ Todas las Llamadas (CALLS)</span>
      <span class="chip" onclick="setPreset(2)">🏛️ Clases y Métodos</span>
      <span class="chip" onclick="setPreset(3)">📦 Módulos e Imports</span>
      <span class="chip" onclick="setPreset(4)">🎯 Radio: search_memories</span>
      <span class="chip" onclick="setPreset(5)">🧠 Gobernador & Voice Server</span>
      <span class="chip" onclick="setPreset(6)">🌐 Grafo General (Top 250)</span>
    </div>
  </div>

  <!-- ── Main Canvas ── -->
  <div id="main-content">
    <div id="network"></div>

    <!-- Floating Canvas Toolbar -->
    <div id="toolbar">
      <input type="text" id="search-box" placeholder="🔍 Buscar nodo..." oninput="searchNode(this.value)">
      <div class="legend">
        <div class="legend-tag"><div class="dot" style="background:#3b82f6;"></div> Módulo</div>
        <div class="legend-tag"><div class="dot" style="background:#a855f7;"></div> Clase</div>
        <div class="legend-tag"><div class="dot" style="background:#00ffaa;"></div> Función</div>
      </div>
      <span id="graph-counts" style="font-family:'Fira Code'; font-size:11px; color:var(--cyan); margin-left:8px;">0 nodos | 0 aristas</span>
    </div>

    <!-- Inspector Drawer -->
    <div id="inspector">
      <div class="inspector-header">
        <h3 id="insp-title">INSPECTOR DE NODO</h3>
        <button class="btn-close" onclick="closeInspector()">✕</button>
      </div>
      <div id="inspector-body">
        <p style="color:var(--muted); font-size:12px;">Haz clic en cualquier nodo o relación para ver sus atributos en vivo.</p>
      </div>
    </div>
  </div>

  <script>
    let network = null;
    let nodesDataSet = new vis.DataSet([]);
    let edgesDataSet = new vis.DataSet([]);
    let physicsActive = true;

    const PRESETS = {{
      1: "MATCH (a)-[r:CALLS]->(b) RETURN a, r, b LIMIT 150;",
      2: "MATCH (c:Class)-[r:CONTAINS_METHOD]->(f:Function) RETURN c, r, f LIMIT 100;",
      3: "MATCH (m:Module)-[r:IMPORTS]->(b) RETURN m, r, b LIMIT 120;",
      4: "MATCH (a)-[r:CALLS]->(b:Function) WHERE b.name = 'search_memories' OR a.name = 'search_memories' RETURN a, r, b;",
      5: "MATCH (a)-[r]->(b) WHERE a.file_path CONTAINS 'governor' OR a.file_path CONTAINS 'voice_server' RETURN a, r, b LIMIT 100;",
      6: "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 250;"
    }};

    function setPreset(num) {{
      const q = PRESETS[num];
      if (q) {{
        document.getElementById('cypher-input').value = q;
        runCypher();
      }}
    }}

    function initNetwork(nodes, edges) {{
      const container = document.getElementById('network');
      nodesDataSet = new vis.DataSet(nodes);
      edgesDataSet = new vis.DataSet(edges);

      const data = {{ nodes: nodesDataSet, edges: edgesDataSet }};
      const options = {{
        physics: {{
          solver: 'barnesHut',
          barnesHut: {{
            gravitationalConstant: -3800,
            centralGravity: 0.28,
            springLength: 95,
            springConstant: 0.045,
            damping: 0.09,
            avoidOverlap: 0.2
          }},
          stabilization: {{ iterations: 120 }}
        }},
        interaction: {{
          hover: true,
          tooltipDelay: 150,
          hideEdgesOnDrag: false,
          navigationButtons: true,
          keyboard: true
        }}
      }};

      network = new vis.Network(container, data, options);

      // Eventos de selección
      network.on('click', function(params) {{
        if (params.nodes.length > 0) {{
          const nodeId = params.nodes[0];
          const nodeData = nodesDataSet.get(nodeId);
          showNodeInspector(nodeData);
        }} else if (params.edges.length > 0) {{
          const edgeId = params.edges[0];
          const edgeData = edgesDataSet.get(edgeId);
          showEdgeInspector(edgeData);
        }}
      }});

      updateCounts();
    }}

    function updateCounts() {{
      const n = nodesDataSet.length;
      const e = edgesDataSet.length;
      document.getElementById('graph-counts').textContent = `${{n}} nodos | ${{e}} aristas`;
    }}

    async function runCypher() {{
      const query = document.getElementById('cypher-input').value.trim();
      if (!query) return;

      const btn = document.getElementById('btn-run');
      btn.textContent = "⏳ CONSULTANDO...";
      btn.disabled = true;

      try {{
        const res = await fetch('/api/cypher', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ query }})
        }});
        const data = await res.json();
        if (data.error) {{
          alert(`Error Cypher: ${{data.error}}`);
        }} else {{
          nodesDataSet.clear();
          edgesDataSet.clear();
          nodesDataSet.add(data.nodes);
          edgesDataSet.add(data.edges);
          updateCounts();
          if (network) network.fit({{ animation: true }});
        }}
      }} catch (err) {{
        alert(`Error al contactar API Kùzu: ${{err.message}}`);
      }} finally {{
        btn.textContent = "▶ EJECUTAR";
        btn.disabled = false;
      }}
    }}

    function showNodeInspector(node) {{
      if (!node) return;
      const p = node.properties || {{}};
      const drawer = document.getElementById('inspector');
      const body = document.getElementById('inspector-body');

      document.getElementById('insp-title').textContent = `${{p.label || 'NODO'}}: ${{node.label}}`;

      let html = `
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>
            <div class="field-label">Nombre &bull; ID</div>
            <div class="field-value">${{p.name}}</div>
            <div style="font-size:10px; color:var(--muted); font-family:'Fira Code';">${{p.id || node.id}}</div>
          </div>
          <div>
            <div class="field-label">Archivo &bull; Líneas</div>
            <div class="field-value">${{p.file_path || '(Sin archivo)'}} ${{p.line_start ? `[L${{p.line_start}}-L${{p.line_end}}]` : ''}}</div>
          </div>
      `;

      if (p.signature) {{
        html += `
          <div>
            <div class="field-label">Firma de Función</div>
            <div class="code-box" style="color:#00ffaa;">${{p.signature}}</div>
          </div>
        `;
      }}

      if (p.docstring) {{
        html += `
          <div>
            <div class="field-label">Docstring / Documentación</div>
            <div class="code-box" style="color:#ddd6fe;">${{p.docstring}}</div>
          </div>
        `;
      }}

      // Conexiones entrantes y salientes
      const connectedEdges = network.getConnectedEdges(node.id);
      const connectedNodes = network.getConnectedNodes(node.id);

      html += `
        <div>
          <div class="field-label">Conexiones Activas (${{connectedNodes.length}})</div>
          <div style="font-size:11px; font-family:'Fira Code'; color:var(--muted); margin-top:4px;">
            ${{connectedEdges.length}} relaciones vinculadas en el subgrafo actual.
          </div>
        </div>
        <button class="btn" style="width:100%; justify-content:center; margin-top:6px;" onclick="focusOnNode('${{node.id}}')">🎯 Centrar Cámara</button>
      </div>`;

      body.innerHTML = html;
      drawer.classList.add('open');
    }}

    function showEdgeInspector(edge) {{
      const drawer = document.getElementById('inspector');
      const body = document.getElementById('inspector-body');
      document.getElementById('insp-title').textContent = `RELACIÓN: ${{edge.label || 'LINK'}}`;

      const src = nodesDataSet.get(edge.from);
      const dst = nodesDataSet.get(edge.to);

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:12px;">
          <div>
            <div class="field-label">Tipo de Arista</div>
            <div class="field-value" style="color:var(--cyan); font-weight:bold;">${{edge.label}}</div>
          </div>
          <div>
            <div class="field-label">Origen (From)</div>
            <div class="field-value">${{src ? src.label : edge.from}}</div>
          </div>
          <div>
            <div class="field-label">Destino (To)</div>
            <div class="field-value">${{dst ? dst.label : edge.to}}</div>
          </div>
        </div>
      `;
      drawer.classList.add('open');
    }}

    function closeInspector() {{
      document.getElementById('inspector').classList.remove('open');
    }}

    function focusOnNode(nodeId) {{
      if (!network) return;
      network.focus(nodeId, {{
        scale: 1.25,
        animation: {{ duration: 800, easingFunction: 'easeInOutQuad' }}
      }});
    }}

    function searchNode(term) {{
      term = term.trim().toLowerCase();
      if (!term) return;
      const allNodes = nodesDataSet.get();
      const match = allNodes.find(n => n.label.toLowerCase().includes(term));
      if (match) {{
        focusOnNode(match.id);
        network.selectNodes([match.id]);
        showNodeInspector(match);
      }}
    }}

    function togglePhysics() {{
      physicsActive = !physicsActive;
      network.setOptions({{ physics: {{ enabled: physicsActive }} }});
      const btn = document.getElementById('btn-freeze');
      btn.textContent = physicsActive ? "⏸ PAUSAR FÍSICA" : "▶ REANUDAR FÍSICA";
      btn.style.color = physicsActive ? "#c084fc" : "#00ffaa";
    }}

    function exportMermaid() {{
      const edges = edgesDataSet.get();
      if (edges.length === 0) {{
        alert("No hay aristas cargadas para exportar a Mermaid.");
        return;
      }}
      let m = "```mermaid\\ngraph LR\\n";
      edges.slice(0, 45).forEach(e => {{
        const s = nodesDataSet.get(e.from)?.label || e.from;
        const d = nodesDataSet.get(e.to)?.label || e.to;
        const cleanS = s.replace(/[^a-zA-Z0-9_]/g, '_');
        const cleanD = d.replace(/[^a-zA-Z0-9_]/g, '_');
        m += `    ${{cleanS}}["${{s}}"] -->|${{e.label}}| ${{cleanD}}["${{d}}"]\\n`;
      }});
      m += "```";
      navigator.clipboard.writeText(m).then(() => {{
        alert("¡Diagrama Mermaid copiado al portapapeles! Puedes pegarlo directamente en cualquier Markdown.");
      }});
    }}

    // Atajo de teclado: Ctrl+Enter para ejecutar consulta
    document.getElementById('cypher-input').addEventListener('keydown', (e) => {{
      if (e.key === 'Enter' && (e.ctrlKey || !e.shiftKey)) {{
        e.preventDefault();
        runCypher();
      }}
    }});

    // Cargar estadísticas
    const initialStats = {initial_stats_json};
    const statsContainer = document.getElementById('stats-container');
    statsContainer.innerHTML = `
      <div class="stat-badge">Módulos: <b>${{initialStats.Module || 0}}</b></div>
      <div class="stat-badge">Clases: <b>${{initialStats.Class || 0}}</b></div>
      <div class="stat-badge">Funciones: <b>${{initialStats.Function || 0}}</b></div>
      <div class="stat-badge">CALLS: <b>${{initialStats.CALLS || 0}}</b></div>
    `;

    // Cargar datos iniciales
    const initialData = {initial_data_json};
    initNetwork(initialData.nodes || [], initialData.edges || []);
  </script>
</body>
</html>"""


class KuzuVisualizerHandler(BaseHTTPRequestHandler):
    """Servidor HTTP embebido que sirve la GUI y ejecuta consultas Cypher en tiempo real."""

    extractor: KuzuGraphExtractor = None
    cached_html: str = ""

    def log_message(self, format, *args):
        # Silenciar logs ruidosos en terminal
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html", "/graph"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.cached_html.encode("utf-8"))
        elif parsed.path == "/api/stats":
            stats = self.extractor.get_summary_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/cypher":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(body)
                query = payload.get("query", "")
                result = self.extractor.execute_cypher(query)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Visualizador de Grafo Kùzu con Vis.js para Fronda 1.0")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Ruta a la base de datos Kùzu")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Puerto del servidor local (default: 5050)")
    parser.add_argument("--query", default="MATCH (a)-[r:CALLS]->(b) RETURN a, r, b LIMIT 120;", help="Consulta inicial")
    parser.add_argument("--export", help="Guarda el HTML en la ruta indicada y finaliza sin iniciar servidor")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" [FRONDA 1.0] VISUALIZADOR INTERACTIVO DE GRAFO KUZU (Vis.js)")
    print("=" * 65)

    extractor = KuzuGraphExtractor(args.db)
    print(f"[*] Conectado a Kuzu DB en: {os.path.abspath(args.db)} (Read-Only)")

    stats = extractor.get_summary_stats()
    print(f"[*] Estadisticas: {stats.get('Module', 0)} Modulos | {stats.get('Class', 0)} Clases | {stats.get('Function', 0)} Funciones | {stats.get('CALLS', 0)} Llamadas")

    print(f"[*] Ejecutando consulta inicial: {args.query}")
    initial_data = extractor.execute_cypher(args.query)
    print(f"[OK] Subgrafo extraído: {initial_data.get('total_nodes', 0)} nodos y {initial_data.get('total_edges', 0)} aristas.")

    html_content = generate_html_template(
        initial_data_json=json.dumps(initial_data, ensure_ascii=False),
        initial_stats_json=json.dumps(stats, ensure_ascii=False)
    )

    # Modo exportación estática
    if args.export:
        out_path = os.path.abspath(args.export)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n[OK - EXITO] Archivo HTML exportado en: {out_path}")
        if not args.no_browser:
            webbrowser.open(f"file:///{out_path}")
        return

    # Guardar también copia estática local kuzu_graph.html
    local_html = os.path.abspath("kuzu_graph.html")
    with open(local_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[*] Archivo local actualizado: {local_html}")

    # Iniciar servidor local interactivo con API Cypher en vivo
    KuzuVisualizerHandler.extractor = extractor
    KuzuVisualizerHandler.cached_html = html_content

    server_address = ("127.0.0.1", args.port)
    try:
        httpd = HTTPServer(server_address, KuzuVisualizerHandler)
    except OSError:
        # Si el puerto está ocupado, buscar puerto alternativo
        server_address = ("127.0.0.1", args.port + 1)
        httpd = HTTPServer(server_address, KuzuVisualizerHandler)

    url = f"http://127.0.0.1:{server_address[1]}/"
    print(f"\n[OK - SERVIDOR LISTO] Navega a: {url}")
    print("[*] Presiona Ctrl+C en esta consola para detener el visualizador.\n")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Visualizador detenido por el usuario.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
