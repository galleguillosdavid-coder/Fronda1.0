# 🌿 Catálogo de Habilidades y Skills — Fronda 1.0

Estado y hoja de ruta técnica de las habilidades automatizadas, multimodales y cognitivas integradas en Fronda 1.0.

---

## 📊 Matriz de Habilidades Instaladas y Activas

| Módulo / Skill | Archivo Fuente | Dependencia / Motor | Estado | Keywords de Activación |
| :--- | :--- | :--- | :---: | :--- |
| **Visión Multimodal** | `skills/vision_engine.py` | `moondream:latest` (Ollama), `Pillow`, `mss` | **INSTALADO** | *"mira mi pantalla"*, *"qué hay en mi pantalla"*, *"lee este error"*, *"analiza lo que estoy viendo"* |
| **NLP Avanzado (Entidades)** | `fronda_nlp.py` | `spacy 3.8.16`, `es_core_news_sm` | **INSTALADO** | Extracción automática en background de personas, lugares y proyectos en cada mensaje. |
| **Diagnóstico de Hardware** | `skills/hardware_analyzer.py` | `psutil`, WMI, Linux `/proc/` | **INSTALADO** | *"analiza mi computador"*, *"especificaciones de mi pc"*, *"hardware de mi pc"* |
| **Clima Meteorológico** | `skills/weather_engine.py` | `wttr.in` (JSON/Texto) | **INSTALADO** | *"cómo va a estar el clima hoy"*, *"pronóstico del tiempo"*, *"qué clima hace en [ciudad]"* |
| **Grafo Cognitivo Visual** | `skills/cognitive_graph.py` | Mermaid Markdown, `fronda_memory.json` | **INSTALADO** | *"hazme un grafo de tu memoria cognitiva"*, *"mapa de tu memoria"*, *"grafo de memoria"* |
| **Lector de PDFs** | `skills/pdf_engine.py` | `pypdf` | **INSTALADO** | *"leer pdf [archivo]"*, *"lee este pdf"*, *"extraer pdf"* |
| **Conversor Multimedia** | `skills/media_engine.py` | `ffmpeg` | **INSTALADO** | *"convierte este archivo de video mkv a mp4"*, *"convertir video"* |
| **18 de Septiembre y Feriados**| `skills/calendar_engine.py` | Algoritmos de calendario oficial de Chile | **INSTALADO** | *"18 de septiembre"*, *"cuándo es el próximo feriado"*, *"cuánto falta para el 18"* |
| **Grafo de Código Vectorial** | `core/codegraph/` | `Kùzu DB`, AST Python, `nomic-embed-text` | **INSTALADO** | Servidor MCP nativo (`codegraph-memory`) y CLI `orquestar_subagentes.py` |
| **Cálculo Científico** | `skills/math_engine.py` | Parser matemático seguro AST | **INSTALADO** | *"cuánto es [expresión]"*, *"calcula [fórmula]"* |
| **Telemetría del Sistema** | `skills/system_engine.py` | `psutil` | **INSTALADO** | *"diagnóstico"*, *"estado del pc"*, *"uso de ram"*, *"rendimiento"* |
| **Sistema Operativo** | `skills/system_engine.py` | `platform`, `subprocess` | **INSTALADO** | *"sistema operativo"*, *"qué sistema tengo"*, *"kernel"* |
| **Control de Audio** | `fronda_skills.py` | `pycaw`, `comtypes` | **INSTALADO** | *"silencia"*, *"mutear"*, *"reactiva el audio"*, *"volumen"* |
| **Control de Brillo** | `fronda_skills.py` | `screen-brightness-control` | **INSTALADO** | *"brillo al [X]%"*, *"ajusta el brillo"* |
| **Comandos WSL 2** | `fronda_bridge.py` | `wsl.exe`, Ubuntu | **INSTALADO** | *"ejecuta en wsl: [comando]"*, *"corre en linux: [comando]"* |

---

## 🎯 Registro de Solicitudes y Tickets Resueltos

Todas las solicitudes históricas registradas en `solicitudes_habilidades.json` se encuentran resueltas y verificadas con pruebas automatizadas:

1. **`REQ-20260905-235228` (INSTALADO)**: Conversión de video MKV a MP4 con `ffmpeg`.
2. **`REQ-20260906-025816` (INSTALADO)**: Detección precisa de sistema operativo dual (Windows 11 + Ubuntu WSL 2).
3. **`REQ-20260906-031232` (INSTALADO)**: Consulta de condiciones meteorológicas y clima en tiempo real sin API keys.
4. **`REQ-20260906-093000` (INSTALADO)**: Extracción y lectura estructurada de documentos PDF con `pypdf`.
5. **`REQ-20260907-141611` (INSTALADO)**: Representación de arquitectura de memoria cognitiva en diagramas Mermaid.
6. **`REQ-20260907-142540` (INSTALADO)**: Escaneo profundo de hardware (CPU, GPU, RAM, Discos, Placa base).
7. **`REQ-20260907-145900` (INSTALADO)**: Efemérides patrias chilenas, historia del 18 de Septiembre y calendario oficial de feriados.
8. **`REQ-20260907-152000` (INSTALADO)**: Visión por Computadora Multimodal con modelo local Moondream 1.4B en Ollama.
9. **`REQ-20260907-152100` (INSTALADO)**: NLP Avanzado y extracción de entidades nombradas con `spaCy` (`es_core_news_sm`).

---

## 🧪 Verificación Continua

La suite de pruebas en `tests/` verifica automáticamente todos los módulos:
```bash
pytest tests/ -v
============================= 110 passed =============================
```
