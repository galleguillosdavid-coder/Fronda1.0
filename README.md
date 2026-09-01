# 🤖 J.A.R.V.I.S. - Autonomous Life Core & Mark 85 Holographic HUD

Sistema de Asistencia de Inteligencia Artificial Local con arquitectura proactiva, interfaz holografica tactica en 3D (Three.js), suite de sintesis y reconocimiento de voz, monitoreo de hardware en tiempo real y memoria persistente a largo plazo.

---

## ⚡ CARACTERISTICAS PRINCIPALES

- **HUD Holografico Mark 85**: Interfaz web inspirada en Iron Man desarrollada con **Three.js** (Reactor de Arco 3D dinamico), lineas de escaneo holografico y audio procedimental Web Audio API.
- **Suite Dual de Voz**: Reconocimiento de voz continuo (STT) en espanol y sintesis vocal neural (TTS) manos libres.
- **Memoria Persistente RAG**: Inyeccion automatica del contexto del usuario (jarvis_memory.json) en cada interaccion con la IA.
- **Dispatcher de Herramientas de Windows**: Apertura directa de aplicaciones del sistema (Chrome, PowerShell, Task Manager, Calculadora, etc.) por comando de voz o texto.
- **Metricas de Rendimiento en Tiempo Real**: Medicion dinamica de latencia por consulta (ms), telemetria de CPU/RAM/Disco y auto-diagnostico.
- **Panel Tactico Colapsable y Sliders**: Control deslizante de temperatura de IA, velocidad del reactor 3D y velocidad de voz, con barra lateral autodeslizante.

---

## 📁 ESTRUCTURA DEL PROYECTO

- jarvis_gui.html - HUD Holografico principal (Three.js, Web Audio, CSS Grid/Flex)
- jarvis_life_core.py - Daemon de telemetria, pensamientos proactivos y despacho de herramientas
- jarvis_voice_engine.py - Motor de voz independiente con edge-tts y SpeechRecognition
- Modelfile.jarvis - Archivo de configuracion y personalidad del modelo Ollama
- jarvis_memory.json - Base de datos JSON de recuerdos y proyectos del usuario
- iniciar_jarvis.bat - Lanzador maestro en 1 clic para todos los servicios
- iniciar_jarvis_voz.bat - Lanzador en consola para el motor de voz
- GUIA_OLLAMA_Y_ASISTENTE.md - Manual detallado de uso y configuracion
- RESUMEN_OPTIMIZACION_SISTEMA.md - Documentacion tecnica de arquitectura v3.0

---

## 🚀 REQUISITOS E INSTALACION

### Requisitos previos:
- Windows 11 / 10
- Python 3.10+
- Ollama instalado (ollama.com)

### Instalacion de dependencias de Python:
`ash
pip install ollama psutil edge-tts SpeechRecognition pygame-ce
`

---

## ⚙️ INICIO RAPIDO

1. **Clonar el repositorio:**
   `ash
   git clone https://github.com/davidgruizut/Jarvis.git
   cd Jarvis
   `

2. **Crear el modelo de Ollama:**
   `ash
   ollama create jarvis -f Modelfile.jarvis
   `

3. **Ejecutar el asistente:**
   Hacer doble clic en iniciar_jarvis.bat o ejecutar en terminal:
   `cmd
   iniciar_jarvis.bat
   `
   Abrira el HUD automaticamente en tu navegador: http://localhost:5173/jarvis_gui.html.
