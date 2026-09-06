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

## 📁 ESTRUCTURA DEL REPOSITORIO

- `iniciar_fronda.bat` - Lanzador portable en 1 clic (libera puerto, levanta servidor y abre navegador).
- `fronda_voice_server.py` - Servidor HTTP backend (puerto 5176) que orquesta Ollama, skills, memoria y Edge-TTS.
- `fronda_voice_gui.html` - Interfaz web bio-digital interactiva (Chat, Telemetría, Micrófono y Panel de Memoria).
- `fronda_memory.py` - Gestor de persistencia, inyección de contexto RAG y extractor de recuerdos en segundo plano.
- `fronda_memory.json` - Base de datos viva con la biografía, proyectos, preferencias y aprendizajes sobre David.
- `fronda_skills.py` - Dispatcher de herramientas del sistema operativo, web y diagnóstico.
- `Modelfile.fronda` - Definición del modelo, directivas de identidad y parámetros de inferencia para Ollama.
- `test_skills.py` - Script de validación de dependencias del entorno.

---

## 🚀 REQUISITOS E INSTALACIÓN

### Requisitos previos:
- Windows 10 / 11
- Python 3.10+
- Ollama instalado localmente ([ollama.com](https://ollama.com))

### Dependencias de Python instaladas:
```bash
pip install edge-tts pygame-ce psutil pycaw comtypes pyautogui screen-brightness-control duckduckgo-search beautifulsoup4 playwright aiohttp Pillow mss pytesseract opencv-python
```

---

## ⚙️ INICIO RÁPIDO

1. **Crear o actualizar el modelo en Ollama:**
   ```cmd
   ollama create fronda -f Modelfile.fronda
   ```

2. **Iniciar Fronda 1.0:**
   Ejecutar haciendo doble clic en `iniciar_fronda.bat` o desde la consola:
   ```cmd
   iniciar_fronda.bat
   ```
   Se abrirá automáticamente la interfaz web en: `http://127.0.0.1:5176/`.
