# 🌿 Fronda 1.0 — Clon Digital Aumentado de David Galleguillos

Sistema de Inteligencia Artificial Local y Multi-Agente con arquitectura híbrida (Windows 11 + WSL 2), síntesis de voz neural de alta fidelidad (`edge-tts`), memoria viva continua (RAG híbrido BM25 + spaCy), **Grafo de Conocimiento Vectorial de Código (Kùzu DB + AST + MCP)** para Antigravity, y catálogo de habilidades multimodales y de ingeniería en tiempo real.

Repositorio oficial: [https://github.com/galleguillosdavid-coder/Fronda1.0](https://github.com/galleguillosdavid-coder/Fronda1.0)

---

## ⚡ CARACTERÍSTICAS PRINCIPALES

- **Identidad: Clon Digital de David Galleguillos**: Fronda 1.0 no es un asistente genérico ni robótico. Es la manifestación digital de David: comparte su mentalidad de ingeniería pragmática, su visión resolutiva, sus áreas técnicas de especialización (Rust, Python, PowerShell, redes IPv7/VPI7) y su forma directa de comunicarse sin rodeos.
- **Grafo de Conocimiento Vectorial de Código (Kùzu DB + MCP + AST)**:
  - Base de datos de grafos embebida en `.kuzu_codegraph/` con embeddings de Ollama (`nomic-embed-text`, 768 dims).
  - Mapeo determinista de 40 módulos, 29 clases, 269 funciones y 457 llamadas topológicas (`CALLS`).
  - Servidor MCP nativo (`core/codegraph/mcp_server.py`) conectado a Antigravity para cálculo de *Blast Radius* y subgrafos quirúrgicos.
- **Orquestador Multi-Agente Topológico (`orquestar_subagentes.py`)**:
  - Análisis de DAG de dependencias para calcular niveles de ejecución paralela segura y minimizar el riesgo de colisiones entre subagentes de Antigravity.
- **Memoria Viva con NLP Avanzado (`fronda_memory.py` + `fronda_nlp.py`)**:
  - Extracción automática de entidades nombradas en español mediante `spaCy` (`es_core_news_sm`).
  - Algoritmo de ranking semántico BM25 adaptado para español con filtrado de stopwords e inyección dinámica en contexto.
- **Visión por Computadora Multimodal (`skills/vision_engine.py`)**:
  - Análisis visual de pantalla en tiempo real mediante el modelo ligero local `moondream` (1.4B) en Ollama.
  - Reconocimiento y lectura de errores, código y ventanas activas con respuesta instantánea.
- **Suite de Habilidades y Herramientas Especializadas (`fronda_skills.py`)**:
  - **Diagnóstico Profundo de Hardware (`skills/hardware_analyzer.py`)**: Análisis en tiempo real de CPU, memoria RAM, tarjeta gráfica (Intel Iris Plus), discos, placa base y salud de batería.
  - **Clima Meteorológico en Vivo (`skills/weather_engine.py`)**: Condiciones climáticas y pronóstico en vivo sin API keys vía `wttr.in`.
  - **Grafo Cognitivo Visual (`skills/cognitive_graph.py`)**: Generación de diagramas de arquitectura de memoria y clusters de conocimiento en formato Mermaid.
  - **Lector de Documentos PDF (`skills/pdf_engine.py`)**: Extracción de texto y resumen estructurado de documentos PDF usando `pypdf`.
  - **Conversor Multimedia (`skills/media_engine.py`)**: Conversión de formatos de audio y video (ej. MKV a MP4) mediante `ffmpeg`.
  - **Efemérides y Feriados de Chile (`skills/calendar_engine.py`)**: Contador de Fiestas Patrias ("18 de Septiembre") y calendario oficial de feriados nacionales.
  - **Control de Sistema y Automatización**: Volumen y silencio con `pycaw`, ajuste de brillo con `screen-brightness-control`, capturas con `mss` y ejecución nativa en Ubuntu WSL 2.
- **HUD Bio-Digital Futurista y Streaming SSE (`fronda_voice_gui.html` + `fronda_voice_server.py`)**:
  - Transmisión en tiempo real token por token vía Server-Sent Events (`/api/chat/stream`).
  - Sincronización estricta por `audio_id` y caché con `threading.Event`, eliminando por completo cualquier desfase entre el audio neural reproducido y el texto en pantalla.
  - Voz neural en español (`es-ES-AlvaroNeural`).

---

## 🏛️ ARQUITECTURA MULTI-AGENTE (WINDOWS HOST ↔ WSL 2 ↔ GRAFO KÙZU)

```
┌─────────────────────────────────────────────────────────────────────────┐
│              CAPA 1: Antigravity IDE (Orquestador Host Windows)         │
│  - Subagentes en paralelo guiados por .agents/skills/code-graph-nav     │
│  - Servidor MCP conectado a .agents/mcp_config.json                     │
└────────────────┬───────────────────────────────────────┬────────────────┘
                 │                                       │
                 ▼                                       ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────┐
│     CAPA 2: Motor de Grafo (Kùzu)     │ │   CAPA 3: Subsistema Linux    │
│  - Base vectorial .kuzu_codegraph/    │ │         (Ubuntu WSL 2)        │
│  - Cálculo de Blast Radius y Subgrafos│ │ - fronda_voice_server.py:5176 │
│  - Ingesta AST con Ollama Embeddings  │ │ - Ollama (frondabrick 1.5B)   │
└───────────────────────────────────────┘ └───────────────────────────────┘
```

- **`core/codegraph/`**:
  - `schema.py`: Esquema relacional DDL de nodos (`Module`, `Class`, `Function`) y aristas (`CALLS`, `IMPORTS`, etc.).
  - `ast_parser.py`: Parser sintáctico AST determinista de Python.
  - `embedder.py`: Embeddings de código vectoriales (768 dims).
  - `graph_db.py`: Consultas Cypher para extracción de dependencias y radio de impacto.
  - `mcp_server.py`: Servidor de protocolo MCP sobre `stdio`.
- **`orquestar_subagentes.py`**: CLI de planificación topológica para subagentes en paralelo de Antigravity.
- **`fronda_bridge.py`**: Conector universal Windows Host ↔ WSL 2 ↔ Ollama.
- **`generate_modelfile.py`**: Generador automático y compilador de `Modelfile.fronda` en Ollama.

---

## 📁 ESTRUCTURA DEL REPOSITORIO

```text
Fronda1.0/
├── .agents/                      # Configuración de Antigravity (MCP, Skills, Reglas)
│   ├── mcp_config.json           # Registro del servidor MCP codegraph-memory
│   ├── rules/                    # Reglas de arquitectura "Graph-First"
│   └── skills/code-graph-nav/    # Directiva obligatoria de navegación por grafo
├── core/
│   ├── codegraph/                # Motor de grafo de código vectorial (Kùzu DB)
│   │   ├── schema.py, graph_db.py, ast_parser.py, embedder.py, indexer.py, mcp_server.py
│   ├── engine.py                 # Inferencia con Ollama y fallback automático
│   ├── governor.py               # Gobernador cibernético de seguridad y control
│   └── session_handoff.py        # Persistencia de contexto entre sesiones
├── skills/                       # Módulos especializados de habilidades
│   ├── vision_engine.py          # Visión multimodal de pantalla con Moondream 1.4B
│   ├── hardware_analyzer.py      # Telemetría y diagnóstico profundo de hardware
│   ├── weather_engine.py         # Consulta de clima en vivo vía wttr.in
│   ├── cognitive_graph.py        # Grafos cognitivos en formato Mermaid
│   ├── pdf_engine.py             # Extractor de documentos PDF con pypdf
│   ├── media_engine.py           # Conversor de formatos de video con ffmpeg
│   ├── calendar_engine.py        # Fiestas Patrias chilenas y feriados oficiales
│   ├── math_engine.py            # Motor de cálculo exacto seguro
│   ├── system_engine.py          # Métricas de CPU, RAM y sistema operativo
│   ├── research_engine.py        # Investigación web, Wikipedia y GitHub
│   └── dispatcher_keywords.json  # Diccionario multi-idioma de intents
├── tests/                        # Suite completa de pruebas automatizadas (110 tests)
├── fronda_voice_server.py        # Servidor backend principal HTTP / SSE (puerto 5176)
├── fronda_voice_gui.html         # HUD interactivo con reconocimiento y síntesis de voz
├── fronda_memory.py              # Memoria viva y ranking híbrido BM25
├── fronda_memory.json            # Base de datos JSON de biografía y recuerdos de David
├── fronda_nlp.py                 # Extractor de entidades nombradas con spaCy
├── fronda_skills.py              # Dispatcher dinámico de intents y solicitudes
├── generate_modelfile.py         # Generador y compilador de Modelfile.fronda
├── Modelfile.fronda              # Definición compilada del clon en Ollama
├── iniciar_fronda.bat            # Script de inicio en 1 clic para Windows
└── pytest.ini                    # Configuración de pruebas unitarias
```

---

## 🚀 REQUISITOS E INSTALACIÓN

### Requisitos previos:
- Windows 10 / 11 con WSL 2 habilitado
- Ubuntu en WSL 2 con Ollama instalado
- Python 3.10+ (tanto en Windows como en WSL 2)
- Modelos locales en Ollama:
  - `frondabrick` (o `qwen2.5-coder:1.5b` como base)
  - `moondream:latest` (para Visión Multimodal)
  - `nomic-embed-text:latest` (para Embeddings del Grafo de Código)

### Instalación de dependencias:
```bash
# En Windows (.venv):
uv pip install -r requirements.txt
uv pip install spacy https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl

# En Ubuntu WSL 2:
pip install --break-system-packages edge-tts pygame-ce psutil duckduckgo-search pillow mss pypdf kuzu
pip install --break-system-packages spacy https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl
```

---

## ⚙️ EJECUCIÓN Y OPERACIÓN

### 1. Iniciar Fronda 1.0 (Servidor y GUI)
Hacer doble clic en `iniciar_fronda.bat` o ejecutar:
```cmd
iniciar_fronda.bat
```
El servidor backend se levantará en WSL 2 en `http://127.0.0.1:5176` y se abrirá automáticamente el navegador con la interfaz de voz.

### 2. Ejecutar la Suite de Pruebas Automatizadas
Para verificar el 100% de los módulos y habilidades:
```cmd
.venv\Scripts\pytest tests/ -v
```
*(110 pruebas pasan exitosamente).*

### 3. Regenerar y Compilar el Modelo en Ollama
Cuando agregues nuevas memorias o habilidades:
```powershell
python generate_modelfile.py --build
```
Esto recompila inmediatamente `frondabrick:latest` en Ollama con el hardware real, catálogo de habilidades y directivas del clon digital.

### 4. Orquestar Subagentes en Paralelo con el Grafo de Código
Para analizar dependencias antes de refactorizar:
```powershell
python orquestar_subagentes.py fronda_memory.py fronda_skills.py core/engine.py
```
El orquestador devolverá los niveles topológicos seguros para ejecutar subagentes en paralelo sin colisiones.

### 5. Control Térmico, Siri Waveform HUD y Runner de Comandos Admin
- **Protección Térmica de CPU**: La inferencia está configurada con `PARAMETER num_thread 4` (dejando 4 hilos libres en procesadores Intel de 8 hilos) y un objetivo de `cpu_headroom_target_percent: 15`. El Gobernador cibernético (`core/governor.py`) aplica automáticamente prioridad de CPU moderada (`BELOW_NORMAL_PRIORITY_CLASS` en Windows y `nice 5` en Linux), impidiendo que el uso de CPU salte a 100% y congele otras aplicaciones.
- **Siri Waveform HUD**: Visualizador biométrico cuántico en `fronda_voice_gui.html` que vibra y modula en tiempo real según el estado (reposo, escucha por micrófono, procesamiento cognitivo o síntesis neural TTS).
- **Inspección de Pensamiento Interno**: Cada respuesta de Fronda incluye una sección desplegable `🧠 PENSAMIENTO INTERNO & TELEMETRÍA COGNITIVA` con la traza de razonamiento, las memorias consultadas con BM25, la intención y el porcentaje de CPU libre.
- **Runner de Comandos con Privilegios de Administrador**:
  - En la interfaz web, cualquier bloque de código devuelto por Fronda cuenta con botones interactivos `[▶ Ejecutar]` y `[🛡️ Admin]`.
  - La API `POST /api/command/run` permite ejecutar comandos tanto en **Windows** (con elevación de PowerShell RunAs / Bypass) como en **WSL 2** (como root mediante `sudo -n` o `wsl.exe -u root`), proyectando la salida en un mini terminal en pantalla.

