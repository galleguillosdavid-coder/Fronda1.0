# J.A.R.V.I.S. - GUIA COMPLETA DEL ASISTENTE LOCAL CON OLLAMA
**Version:** 3.0 - Protocol "Self-Aware Core" | Actualizado: 1 Sep 2026

---

## 1. MODELOS ECONOMICOS RECOMENDADOS (Intel Core i5 + 16 GB RAM)

| Modelo | Descarga | RAM | Especialidad | Comando |
|---|---|---|---|---|
| llama3.2:3b (ACTIVO) | 2.0 GB | 2.5 GB | Espanol, rapido, razonamiento | ollama run llama3.2:3b |
| qwen2.5:3b | 1.9 GB | 2.4 GB | Codigo y matematicas | ollama run qwen2.5:3b |
| llama3.2:1b | 1.3 GB | 1.5 GB | Ultra-ligero | ollama run llama3.2:1b |
| phi3.5:mini | 2.2 GB | 2.8 GB | Logica, Microsoft | ollama run phi3.5:mini |

---

## 2. INICIO RAPIDO - 1 CLIC

  1. Doble clic en iniciar_jarvis.bat
  2. Esperar que los 3 servicios inicien (Ollama, Life Core, Servidor HUD)
  3. Abrir http://localhost:5173/jarvis_gui.html en Chrome o Edge

---

## 3. CAPACIDADES ACTUALES (v3.0)

### HUD Holografico (jarvis_gui.html)
- Interfaz Iron Man con Three.js: reactor de arco 3D, escanlines, efectos HUD
- Chat en streaming (texto aparece en tiempo real mientras el modelo piensa)
- Reconocimiento de voz (STT) en espanol
- Sintesis de voz (TTS) con voces del sistema o edge-tts
- Modo manos libres: escucha -> procesa -> responde -> vuelve a escuchar
- Efectos de audio procedurales via Web Audio API
- Panel de telemetria de hardware en tiempo real

### Life Core Daemon (jarvis_life_core.py - localhost:5174)
- Monitoreo continuo de CPU, RAM, disco y uptime
- Pensamientos autonomos proactivos (Jarvis genera iniciativas sin ser preguntado)
- Gestión de memoria persistente (jarvis_memory.json)
- Dispatcher de apps Windows (abre aplicaciones por comando de voz o texto)
- Metricas de rendimiento de Jarvis (tiempo de respuesta promedio, min, max)
- Mantenimiento automatico del sistema (purga de temporales y papelera)

### Las 4 Mejoras de Auto-Optimizacion (implementadas Sep 2026)
1. RAG Memory Injection: jarvis_memory.json inyectado como contexto en cada query
2. Personalizacion total: Modelfile con perfil de hardware y preferencias del usuario
3. Metricas de rendimiento: tiempo por query registrado y reportado
4. Windows Tool Dispatcher: comandos de voz que lanzan apps del sistema

---

## 4. COMANDOS DE VOZ DISPONIBLES

| Lo que dices | Lo que hace Jarvis |
|---|---|
| "abre Chrome" | Lanza Google Chrome |
| "inicia PowerShell" | Abre la terminal |
| "abre el explorador" | Abre el Explorador de archivos |
| "lanza la calculadora" | Abre la Calculadora |
| "evalua tus sistemas" | Jarvis se auto-evalua y propone mejoras |
| Cualquier pregunta tecnica | Responde con contexto de tu hardware |

---

## 5. PRESETS RAPIDOS EN EL HUD

| Chip | Funcion |
|---|---|
| ESTADO DE HARDWARE | Consulta telemetria en tiempo real |
| PURGA RAPIDA | Optimiza RAM y limpia temporales |
| CONSULTAR MEMORIA | Jarvis lista lo que recuerda de ti |
| SCRIPT POWERSHELL | Genera scripts listos para copiar |
| INFORME DE RENDIMIENTO | Muestra metricas del sistema y de Jarvis |
| AUTO-EVALUACION | Solicita propuestas de mejora propias |

---

## 6. ENSENARLE NUEVOS DATOS A JARVIS

### Via el HUD:
  Boton "MEMORIA" -> "Ensenar nuevo dato o proyecto" -> GUARDAR

### Via edicion directa:
  Editar jarvis_memory.json y agregar datos en los campos:
  - learned_facts: array de hechos
  - projects: array de proyectos activos
  - preferences: array de preferencias

---

## 7. PERSONALIZAR EL MODELO

### Editar personalidad:
  Modificar Modelfile.jarvis y reconstruir:
  
    ollama create jarvis -f Modelfile.jarvis

### Parametros del modelo:

| Parametro | Valor | Efecto |
|---|---|---|
| num_thread | 4 | Usa todos los nucleos del i5 |
| num_ctx | 4096 | Ventana de contexto para memoria |
| temperature | 0.72 | Creatividad balanceada |
| repeat_penalty | 1.1 | Evita repeticiones |

---

## 8. MANTENIMIENTO

### Actualizar definiciones del antivirus:
  powershell -Command "Update-MpSignature"

### Recompilar modelo Jarvis:
  ollama create jarvis -f Modelfile.jarvis

### Ver logs del Life Core:
  El daemon imprime sus "pensamientos" en la consola al iniciarse

### Agregar nuevas apps al dispatcher:
  Editar APP_MAP en jarvis_life_core.py:
  "nombre app": "ruta\a\la\app.exe"

---

## 9. SOLUCION DE PROBLEMAS

| Problema | Solucion |
|---|---|
| HUD no conecta a Ollama | Verificar que iniciar_jarvis.bat este corriendo |
| Voz no funciona | Permitir acceso al microfono en Chrome/Edge |
| Life Core no responde | Reiniciar iniciar_jarvis.bat |
| Jarvis no recuerda nada | Verificar que jarvis_life_core.py esta en el puerto 5174 |
| Respuestas lentas | Cerrar otras aplicaciones pesadas para liberar RAM |
