# 🌿 Fronda 1.0 — Clon Digital Aumentado de David Galleguillos

Sistema de Inteligencia Artificial Local con arquitectura multi-hilo no bloqueante, síntesis de voz neural de alta fidelidad (`edge-tts`), memoria persistente con aprendizaje incremental continuo y suite de skills automatizados para control de Windows y navegación web en tiempo real.

Repositorio oficial: [https://github.com/galleguillosdavid-coder/Fronda1.0](https://github.com/galleguillosdavid-coder/Fronda1.0)

---

## ⚡ CARACTERÍSTICAS PRINCIPALES

- **Identidad: Clon Digital de David Galleguillos**: Fronda 1.0 no es un asistente genérico ni robótico. Es la manifestación digital de David: comparte su mentalidad de ingeniería pragmática, su visión resolutiva, sus áreas técnicas de especialización y su forma directa de comunicarse.
- **Aprendizaje Incremental de Memoria Viva (`fronda_memory.py`)**: 
  - En cada interacción, un extractor asíncrono analiza las conversaciones y guarda nuevos hechos, anécdotas, proyectos y preferencias sobre la vida de David en `fronda_memory.json`.
  - Inyección dinámica de memoria RAG relevante en el contexto de inferencia del LLM.
- **Motor LLM Local con Ollama**:
  - Modelo `fronda` basado en `llama3.2:3b` adaptado a través de `Modelfile.fronda`.
  - Optimizado para CPU Intel Core i5 con 4 hilos físicos, ventana de contexto ampliada de 4096 tokens y baja latencia.
- **Suite de Skills Asíncronos (`fronda_skills.py`)**:
  - **Control de Sistema**: Volumen y mute con `pycaw`, ajuste de brillo con `screen-brightness-control`, capturas de pantalla de alta velocidad con `mss` y `PIL`.
  - **Mundo Exterior**: Búsqueda web en tiempo real sin límites ni API keys con DuckDuckGo.
  - **Telemetría en Vivo**: Diagnóstico de CPU, memoria RAM, estado de almacenamiento y batería en tiempo real.
  - **Lanzador de Apps**: Ejecución instantánea de PowerShell, Calculadora, Bloc de notas, Administrador de tareas, etc.
- **HUD Bio-Digital Futurista (`fronda_voice_gui.html`)**:
  - Interfaz web moderna con paleta esmeralda cuántica (`#00ffaa`), cian y obsidiana profunda.
  - Panel deslizante lateral de **Memoria Viva** para visualizar y agregar recuerdos en tiempo real.
  - Soporte de reconocimiento de voz por micrófono (Web Speech API) y voz neural masculina (`es-ES-AlvaroNeural`).
- **Arquitectura Asíncrona y Multi-hilo**:
  - Servidor `ThreadingHTTPServer` que maneja peticiones concurrentes para que las consultas de telemetría y memoria sigan respondiendo mientras Ollama procesa inferencias complejas.
  - Hilos dedicados independientes para reproducción de voz neural (`edge-tts`) y extracción de memoria en segundo plano sin congelar la interfaz.

---

## 🏛️ ARQUITECTURA MULTI-AGENTE (WSL 2 + WINDOWS HOST)

Implementación de la arquitectura de 3 capas descrita en `Arquitectura_Sistema_Multiagente_FrondaBrick_WSL.pdf`:

```
┌─────────────────────────────────────────────────────────────┐
│             CAPA 1: Orquestador Windows (Antigravity)       │
│  - Planificación estratégica, gestión de Git y UI/Voz       │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               │ HTTP Localhost (11434)       │ wsl.exe CLI
               ▼                              ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│     CAPA 3: Clon Cognitivo    │ │  CAPA 2: Entorno Linux    │
│       Fronda Brick v0.01      │ │      (Ubuntu WSL 2)       │
│ - Ollama en WSL 2             │ │ - Shell bash, Git, tests  │
│ - qwen2.5-coder optimizado    │ │ - Compilación nativa      │
│ - temperature 0.3, ctx 2048   │ │ - Aislamiento de tareas   │
└───────────────────────────────┘ └───────────────────────────┘
```

- **`fronda_bridge.py`**: Conector universal que enlaza Windows (Capa 1) con WSL (Capa 2) y el modelo local (Capa 3).
- **`demo_multiagente.py`**: Prueba end-to-end de verificación cruzada entre el host, la CLI de Linux y el razonamiento del clon cognitivo.
- **`Modelfile.frondabrick`**: Definición de la personalidad pragmática, rigor en ingeniería y especialidades técnicas de David Galleguillos.

---

## 📁 ESTRUCTURA DEL REPOSITORIO

- `iniciar_fronda.bat` - Lanzador portable en 1 clic (libera puerto, levanta servidor y abre navegador).
- `fronda_voice_server.py` - Servidor HTTP backend (puerto 5176) que orquesta Ollama, skills, memoria y Edge-TTS.
- `fronda_voice_gui.html` - Interfaz web bio-digital interactiva (Chat, Telemetría, Micrófono y Panel de Memoria).
- `fronda_bridge.py` - Puente inter-agente Windows Host ↔ WSL 2 ↔ Ollama.
- `demo_multiagente.py` - Script demostrativo de validación de la arquitectura multi-agente de 3 capas.
- `fronda_memory.py` - Gestor de persistencia, inyección de contexto RAG y extractor de recuerdos en segundo plano.
- `fronda_memory.json` - Base de datos viva con la biografía, proyectos, preferencias y aprendizajes sobre David.
- `fronda_skills.py` - Dispatcher de herramientas del sistema operativo, web y diagnóstico.
- `Modelfile.frondabrick` - Definición del clon cognitivo Fronda Brick v0.01 en WSL 2.
- `Modelfile.fronda` - Definición del modelo tradicional de asistencia para Ollama.
- `test_skills.py` - Script de validación de dependencias del entorno.

---

## 🚀 REQUISITOS E INSTALACIÓN

### Requisitos previos:
- Windows 10 / 11 con WSL 2 habilitado
- Ubuntu en WSL 2 con Ollama instalado
- Python 3.10+
- Repositorio sincronizado en `c:\Users\Frondabrick\Desktop\dvd\Fronda\Fronda1.0`

### Dependencias de Python instaladas:
```bash
pip install edge-tts pygame-ce psutil pycaw comtypes pyautogui screen-brightness-control duckduckgo-search beautifulsoup4 playwright aiohttp Pillow mss pytesseract opencv-python
```

---

## ⚙️ INICIO RÁPIDO

1. **Verificar el puente multi-agente:**
   ```powershell
   python demo_multiagente.py
   ```

2. **Iniciar Fronda 1.0:**
   Ejecutar haciendo doble clic en `iniciar_fronda.bat` o desde la consola:
   ```cmd
   iniciar_fronda.bat
   ```
   Se abrirá automáticamente la interfaz web en: `http://127.0.0.1:5176/`.

