# Fronda 1.0 - API Reference

Especificación técnica de la API REST y streaming Server-Sent Events (SSE) del servidor backend [fronda_voice_server.py](fronda_voice_server.py) (puerto 5176).

## Base URL
```
http://127.0.0.1:5176
```
La interfaz web [fronda_voice_gui.html](fronda_voice_gui.html) resuelve automáticamente la URL base mediante `window.location.origin`.

---

## Autenticación (Opcional)
Si `config.json:server.auth_token` está configurado, cada solicitud HTTP debe incluir la cabecera:
```http
X-Fronda-Token: <tu_token>
```

---

## Endpoints

### `GET /`
Sirve la interfaz web interactiva `fronda_voice_gui.html`.

---

### `GET /api/status`
Reporta el estado en tiempo real del servidor, inferencia y entorno de ejecución.

**Response (200 OK):**
```json
{
  "speaking": false,
  "processing": false,
  "voice": "es-ES-AlvaroNeural",
  "model": "frondabrick",
  "ollama_online": true,
  "wsl_available": true
}
```

---

### `GET /api/config`
Configuración pública de Fronda 1.0 (sin exponer credenciales ni rutas sensibles).

**Response (200 OK):**
```json
{
  "default_model": "frondabrick",
  "fallback_model": "qwen2.5-coder:1.5b",
  "available_models": ["frondabrick", "qwen2.5-coder:1.5b", "moondream:latest"],
  "voice": "es-ES-AlvaroNeural",
  "port": 5176,
  "welcome_message": "Fronda 1.0 inicializado...",
  "user_nickname": "David"
}
```

---

### `GET /api/telemetry`
Métricas de hardware y telemetría recolectadas en tiempo real.

**Response (200 OK):**
```json
{
  "cpu_percent": 14.2,
  "cpu_cores": 4,
  "ram_percent": 41.5,
  "ram_used_gb": 6.5,
  "ram_total_gb": 15.7,
  "disk_percent": 54.8,
  "disk_free_gb": 182.4,
  "disk_path": "C:\\",
  "os_environment": "WSL 2 (Ubuntu) + Windows 11",
  "platform": "linux"
}
```

---

### `GET /api/memory`
Devuelve la base de datos completa de Memoria Viva del clon.

**Response (200 OK):**
```json
{
  "profile": {
    "name": "David Galleguillos",
    "nickname": "David",
    "role": "Creador e Ingeniero - Original de Fronda 1.0",
    "voice_preferred": "es-ES-AlvaroNeural",
    "hardware_specs": {
      "cpu": "Intel Core i5-1030NG7 (4 núcleos)",
      "ram": "16 GB LPDDR4",
      "graphics": "Intel Iris Plus Graphics"
    }
  },
  "learned_history": [...],
  "acquired_skills": [...],
  "stats": {
    "total_interactions": 85,
    "total_memories": 6,
    "last_interaction": "2026-09-07T15:41:10"
  }
}
```

---

### `POST /api/chat`
Envío síncrono de mensajes al clon digital con soporte de ejecución directa de skills y síntesis TTS.

**Request (JSON):**
```json
{
  "messages": [
    {"role": "user", "content": "mira mi pantalla"}
  ],
  "speak": true
}
```

**Response (200 OK):**
```json
{
  "response": "👁️ **ANÁLISIS DE VISIÓN MULTIMODAL (Moondream 1.4B)**\n• **Captura analizada**: `screen_vision.png`\n\nThe screen shows...",
  "audio_id": "aud_1788795689123",
  "voice": "es-ES-AlvaroNeural",
  "skill_executed": "screen_vision",
  "skill_request": null
}
```

---

### `POST /api/chat/stream`
Streaming de inferencia en tiempo real mediante **Server-Sent Events (SSE)**.
Emite tokens progresivos a medida que el LLM genera la respuesta, minimizando la latencia percibida.

**Request (JSON):**
```json
{
  "messages": [
    {"role": "user", "content": "¿Cómo estás Fronda?"}
  ]
}
```

**Response (SSE Stream - `text/event-stream`):**
```text
event: token
data: "¡"

event: token
data: "Hola"

event: token
data: " David"

event: token
data: "!"

event: done
data: {}
```

---

### `GET /api/audio?id={audio_id}`
Descarga el audio MP3 generado por `edge-tts` sincronizado con la respuesta del chat.
- El parámetro `id` garantiza que el navegador reciba con certeza el audio del turno actual (evitando reproducir el audio del turno anterior).
- Si el audio aún se está codificando, el servidor espera de forma no bloqueante hasta 10 segundos antes de enviar el buffer.

**Response:** `audio/mpeg` (binario)

---

### `GET /api/skills`
Catálogo de habilidades registradas y activas en el despachador de Fronda.

**Response (200 OK):**
```json
{
  "skills": [
    {"name": "screen_vision", "description": "Análisis multimodal de pantalla con Moondream 1.4B"},
    {"name": "hardware_analysis", "description": "Diagnóstico profundo de hardware en tiempo real"},
    {"name": "weather", "description": "Condiciones meteorológicas en vivo con wttr.in"},
    {"name": "cognitive_graph", "description": "Generación de diagramas de memoria cognitiva en Mermaid"},
    {"name": "pdf_reader", "description": "Extracción y resumen de documentos PDF con pypdf"},
    {"name": "media_convert", "description": "Conversión multimedia de video con ffmpeg"},
    {"name": "september_18", "description": "Efemérides de Fiestas Patrias chilenas y cuenta regresiva"},
    {"name": "holidays", "description": "Calendario oficial de feriados de Chile"},
    {"name": "time_date", "description": "Hora y fecha actual"},
    {"name": "telemetry", "description": "Métricas del sistema (CPU, RAM, disco)"},
    {"name": "os_info", "description": "Información del sistema operativo Windows 11 + WSL 2"},
    {"name": "volume", "description": "Ajuste de volumen del sistema"},
    {"name": "mute", "description": "Silenciar o reactivar el audio"},
    {"name": "brightness", "description": "Ajuste de brillo de la pantalla"},
    {"name": "screenshot", "description": "Captura de pantalla rápida"},
    {"name": "wsl_command", "description": "Ejecución de comandos en la terminal de Ubuntu"}
  ]
}
```

---

### `POST /api/model/switch`
Cambia dinámicamente el modelo activo en Ollama.

**Request:**
```json
{"model": "qwen2.5-coder:1.5b"}
```

**Response (200 OK):**
```json
{"ok": true, "model": "qwen2.5-coder:1.5b"}
```

---

### `POST /api/memory/add`
Inserta un nuevo recuerdo explícito en la base de datos de memoria persistente.

**Request:**
```json
{
  "content": "David completó la integración del grafo Kùzu para Antigravity.",
  "category": "proyectos"
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "memory": {
    "id": "mem_e4b1c2",
    "timestamp": "2026-09-07T16:45:00",
    "category": "proyectos",
    "content": "David completó la integración del grafo Kùzu para Antigravity.",
    "importance": 4
  }
}
```

---

### `GET /api/skills/requests`
Lista las solicitudes y tickets de habilidades registradas por limitaciones detectadas.

**Response:** Array de objetos JSON con `id`, `fecha`, `peticion_usuario`, `estado` (`PENDIENTE_DESARROLLO` o `INSTALADO`), `descripcion` y `notas`.

---

### `POST /api/stop`
Detiene de inmediato cualquier reproducción o emisión de audio activa.

**Response:** `{"stopped": true}`

---

## Códigos de Respuesta HTTP

| Código | Significado |
|---|---|
| `200 OK` | Operación exitosa. |
| `400 Bad Request` | Cuerpo JSON malformado o modelo no disponible. |
| `401 Unauthorized` | Cabecera `X-Fronda-Token` ausente o incorrecta. |
| `404 Not Found` | Endpoint no encontrado. |
| `429 Too Many Requests` | Límite de tasa por segundo excedido para la IP de origen. |
| `500 Internal Error` | Error no manejado en la ejecución del servidor. |
