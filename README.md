# 🤖 Jarvis - Autonomous Life Core & Mark 85 Holographic HUD

Sistema de Asistencia de Inteligencia Artificial Local con arquitectura proactiva, interfaz holográfica táctica en 3D (Three.js), suite de síntesis de voz neural (Edge TTS), reconocimiento de voz, controles de sistema/emergencia, monitoreo de hardware en tiempo real y memoria persistente a largo plazo.

---

## ⚡ CARACTERÍSTICAS PRINCIPALES

- **Nombre e Identidad: Jarvis**: Configurado a nivel de modelo Ollama y memoria para reconocerse y responder exclusivamente como **Jarvis**.
- **HUD Holográfico Mark 85**: Interfaz web inspirada en Iron Man desarrollada con **Three.js** (Reactor de Arco 3D dinámico), líneas de escaneo holográfico y audio procedural Web Audio API.
- **Suite de Voz Neural de Alta Definición**: Síntesis de voz neural integrada mediante **Edge TTS** (voz masculina en español `es-ES-AlvaroNeural`) en el servidor backend y HUD, junto con reconocimiento de voz continuo (STT) y modo manos libres.
- **Controles de Sistema y Mandos de Emergencia**:
  - `▶️ INICIO`: Inicialización y reconexión inmediata de subsistemas.
  - `🔄 REINICIO`: Purgado y reinicio del núcleo de vida y telemetría.
  - `🚨 APAGADO DE EMERGENCIA`: Detención inmediata de voz, escucha activa y suspensión segura del sistema.
- **Memoria Persistente RAG**: Inyección automática del contexto del usuario (`jarvis_memory.json`) en cada interacción con el modelo Ollama.
- **Dispatcher de Herramientas de Windows**: Apertura directa de aplicaciones del sistema (Chrome, PowerShell, Task Manager, Calculadora, etc.) por comando de voz o texto.
- **Métricas de Rendimiento en Tiempo Real**: Medición dinámica de latencia por consulta (ms), telemetría de CPU/RAM/Disco y auto-diagnóstico.
- **Panel Táctico Colapsable y Sliders**: Control deslizante de temperatura de IA, velocidad del reactor 3D y velocidad de voz, con barra lateral auto-deslizante.

---

## 📁 ESTRUCTURA DEL PROYECTO

- `jarvis_voice_gui.html` - Interfaz web premium de chat de voz (Micrófono Web Speech, estado del servidor).
- `jarvis_voice_server.py` - Servidor HTTP backend (puerto 5176) que enlaza Ollama, gestiona la interfaz y ejecuta `edge-tts` localmente.
- `jarvis_voice_engine.py` - Motor de voz neural independiente y core de generación TTS.
- `Modelfile.jarvis` - Configuración, directivas de identidad (Jarvis) y parámetros de inferencia para Ollama.
- `jarvis_memory.json` - Base de datos JSON de recuerdos, proyectos y perfil del usuario.
- `iniciar_voz_gui.bat` - Lanzador maestro en 1 clic para el servidor Web HUD.
- `iniciar_voz_alvaro.bat` - Lanzador simple en consola para el motor de voz neural.
- `GUIA_OLLAMA_Y_ASISTENTE.md` - Manual detallado de uso, comandos y configuración.
- `RESUMEN_OPTIMIZACION_SISTEMA.md` - Documentación técnica de arquitectura del sistema.

---

## 🚀 REQUISITOS E INSTALACIÓN

### Requisitos previos:
- Windows 11 / 10
- Python 3.10+
- Ollama instalado ([ollama.com](https://ollama.com))

### Instalación de dependencias de Python:
```bash
pip install ollama psutil edge-tts SpeechRecognition pygame-ce
```

---

## ⚙️ INICIO RÁPIDO

1. **Crear o actualizar el modelo en Ollama:**
   ```bash
   ollama create jarvis -f Modelfile.jarvis
   ```

2. **Ejecutar el asistente:**
   Hacer doble clic en `iniciar_voz_gui.bat` o ejecutar en terminal:
   ```cmd
   iniciar_voz_gui.bat
   ```
   Abrirá el HUD automáticamente en tu navegador: `http://127.0.0.1:5176/`.
