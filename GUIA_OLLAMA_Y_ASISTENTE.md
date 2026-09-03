# Jarvis - GUIA COMPLETA DEL ASISTENTE LOCAL CON OLLAMA
**Versión:** 3.1 - Protocol "Self-Aware Core & Neural Voice" | Actualizado: Septiembre 2026

---

## 1. IDENTIDAD Y NOMBRE DEL ASISTENTE

El asistente se llama oficialmente **Jarvis**. Se ha configurado en su `Modelfile.jarvis` y en el contexto de memoria RAG para que reconozca su nombre de forma natural y directa como **Jarvis** (sin acrónimos, puntos ni siglas).

---

## 2. MODELOS RECOMENDADOS (Intel Core i5 + 16 GB RAM)

| Modelo | Descarga | RAM | Especialidad | Comando |
|---|---|---|---|---|
| **jarvis (ACTIVO)** | 2.0 GB | 2.5 GB | Español, personalidad Jarvis, optimizado para i5 | `ollama run jarvis` |
| llama3.2:3b | 2.0 GB | 2.5 GB | Modelo base en español, rápido, buen razonamiento | `ollama run llama3.2:3b` |
| qwen2.5:3b | 1.9 GB | 2.4 GB | Código y matemáticas | `ollama run qwen2.5:3b` |
| llama3.2:1b | 1.3 GB | 1.5 GB | Ultra-ligero para bajo consumo | `ollama run llama3.2:1b` |

---

## 3. INICIO RÁPIDO - 1 CLIC

1. Doble clic en `iniciar_voz_gui.bat`.
2. Esperar que los servicios inicien:
   - **Ollama** (puerto 11434)
   - **Servidor de Voz GUI** (puerto 5176)
3. El navegador abrirá automáticamente `http://127.0.0.1:5176`.

---

## 4. MANDOS DE CONTROL Y EMERGENCIA EN LA INTERFAZ

La interfaz incluye un botón **⏹** para detener la generación de audio al instante, así como un botón de **Micrófono (🎤)** para hablar directamente usando la tecnología Web Speech.

---

## 5. SUITE DE VOZ NEURAL (EDGE TTS)

La aplicación utiliza por defecto el motor de voz neural de alta definición **Edge TTS** forzado a la voz `es-ES-AlvaroNeural`:
- El servidor `jarvis_voice_server.py` sintetiza y reproduce en segundo plano las respuestas en audio MP3 de alta fidelidad directamente en el servidor.
- La interfaz de chat indicará visualmente cuando el servidor esté procesando la respuesta de Ollama o hablando.

---

## 6. COMANDOS DE VOZ Y ACCIONES RÁPIDAS

| Lo que dices | Lo que hace Jarvis |
|---|---|
| "Hola, ¿cómo te llamas?" | Jarvis responderá que su nombre es Jarvis |
| "abre Chrome" / "inicia Edge" | Lanza el navegador correspondiente |
| "inicia PowerShell" / "abre terminal" | Abre la consola PowerShell |
| "abre el explorador" | Abre el Explorador de archivos de Windows |
| "lanza la calculadora" | Abre la Calculadora |
| "abre el administrador de tareas" | Abre Task Manager (`taskmgr.exe`) |
| "evalúa tus sistemas" | Jarvis se auto-evalúa y propone optimizaciones |
| Consultas técnicas | Responde considerando tu hardware (i5, 16 GB RAM, Intel Iris Plus) |

---

## 7. GESTIÓN DE MEMORIA PERSISTENTE

### A través del HUD:
Hacer clic en el botón **"MEMORIA"** en el panel lateral -> Ingresar nuevo dato o proyecto -> **GUARDAR**.

### Vía edición directa:
Editar `jarvis_memory.json` y agregar datos en los campos:
- `learned_memories`: lista de hechos y preferencias aprendidas.
- `user_profile`: datos del usuario David.

---

## 8. ACTUALIZAR O RECOMPILAR EL MODELO

Si editas las directivas en `Modelfile.jarvis`, compila el modelo en Ollama ejecutando:
```bash
ollama create jarvis -f Modelfile.jarvis
```

---

## 9. SOLUCIÓN DE PROBLEMAS

| Problema | Solución |
|---|---|
| El HUD no conecta con Ollama | Verificar que Ollama esté en ejecución (`ollama serve`). |
| Jarvis no habla con voz neural | Verificar que `jarvis_life_core.py` esté activo en el puerto 5174. |
| El micrófono no detecta audio | Conceder permisos de micrófono en el navegador (Chrome o Edge). |
| Interfaz bloqueada por emergencia | Presionar el botón verde **[▶️ INICIO]** en la barra superior. |
