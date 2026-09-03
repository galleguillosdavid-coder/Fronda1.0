# Jarvis - RESUMEN DE OPTIMIZACIÓN Y ESTADO DEL SISTEMA
**Última actualización:** Septiembre 2026 | v3.1 - Protocol "Self-Aware Core & Neural Voice"

---

## ESTADO GENERAL DEL SISTEMA

| Componente | Estado | Versión / Detalle |
|---|---|---|
| Identidad de IA | Jarvis (sin acrónimos) | Configurado en Modelfile y RAG |
| Windows Defender | ACTIVO + Auto-actualización programada | Definiciones actualizadas |
| Ollama | Online en localhost:11434 | Modelo `jarvis` compilado |
| GUI / HUD Holográfico | Activo en localhost:5173 | Three.js + Controles de Emergencia |
| Life Core Daemon | Daemon proactivo en localhost:5174 | Telemetría + TTS Neural + Control de Sistema |
| Voice Engine | Voz Neural Edge-TTS (`es-ES-AlvaroNeural`) | Integrada en Backend y HUD |

---

## HARDWARE DEL SISTEMA

| Componente | Especificación |
|---|---|
| CPU | Intel Core i5-1030NG7 (4 núcleos físicos, 8 hilos) |
| RAM | 16 GB DDR4 |
| Almacenamiento | SSD 293 GB / 173 GB libres |
| GPU | Intel Iris Plus Graphics (integrada) |
| Sistema Operativo | Windows 11 |

---

## ARQUITECTURA DE JARVIS

### Flujo de Comunicación Actualizado

```
      Usuario (Voz / Texto / Botones HUD)
                       |
        jarvis_gui.html (HUD en localhost:5173)
        [Controles: INICIO | REINICIO | APAGADO]
         |                                |
         | (RAG Context)                  | (TTS / Telemetría / Control)
         v                                v
   Ollama API (localhost:11434)     jarvis_life_core.py (localhost:5174)
         |                                +-- Telemetría de hardware (psutil)
   Modelo jarvis                          +-- Memoria persistente (jarvis_memory.json)
   (llama3.2:3b + Modelfile.jarvis)       +-- Motor TTS Neural (edge-tts /api/tts)
         |                                +-- Control sistema (/api/system/shutdown, restart)
         v                                +-- Dispatcher de apps Windows
   Respuesta streaming                    +-- Métricas de rendimiento y pensamientos
         |
         v
   Audio Neural MP3 (AlvaroNeural) reproducido en HUD
```

---

## MÓDULOS DEL SISTEMA

| Archivo | Descripción |
|---|---|
| `jarvis_gui.html` | HUD holográfico táctico con Three.js, visualizador de ondas neón y mandos de emergencia/inicio/reinicio. |
| `Modelfile.jarvis` | Definición de personalidad, instrucciones de identidad (Jarvis) e inferencia en Ollama. |
| `jarvis_life_core.py` | Servidor backend daemon con telemetría, endpoint TTS neural (`/api/tts`) y control de sistema. |
| `jarvis_voice_engine.py` | Motor de voz independiente en consola con `edge-tts` y `speech_recognition`. |
| `jarvis_memory.json` | Base de conocimiento persistente y perfil de David. |
| `iniciar_jarvis.bat` | Lanzador maestro que arranca Ollama, Life Core y el servidor HUD en 1 clic. |

---

## MANDOS DE CONTROL Y PARADA DE EMERGENCIA

1. **▶️ INICIO**: Reconecta subsistemas, reanuda telemetría y desbloquea los campos de entrada.
2. **🔄 REINICIO**: Purga las métricas en memoria del daemon, reinicia el ciclo de telemetría y re-sincroniza el modelo.
3. **🚨 APAGADO DE EMERGENCIA**:
   - Detiene inmediatamente la síntesis de audio y el micrófono.
   - Pone la interfaz en estado de alerta visual roja.
   - Bloquea los campos de entrada de forma segura hasta que se reactive con el botón de inicio.

---

## SÍNTESIS DE VOZ NEURAL (EDGE TTS)

- La voz oficial configurada es **`es-ES-AlvaroNeural`**, proporcionando una pronunciación natural, masculina y sin cortes robóticos.
- La generación se ejecuta de forma asíncrona en el daemon de Life Core y se transmite en MP3 directamente al navegador.
