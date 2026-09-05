# 🧠 PLAN DE EXPANSIÓN: SKILLS Y HERRAMIENTAS PARA JARVIS

> **⚠️ AVISO PARA LA IA ASIGNADA A ESTA TAREA:**
> Este documento contiene la hoja de ruta para expandir las capacidades de Jarvis (basado en Ollama + Python). 
> **Tu objetivo exclusivo es INSTALAR, CONFIGURAR Y PROBAR las dependencias** enumeradas aquí para asegurar que coexistan en armonía sin romper el ecosistema actual (Windows, Python 3.14, Edge-TTS, pygame). No reescribas el `jarvis_voice_server.py` base todavía, enfócate en dejar el terreno preparado con scripts de prueba (`test_skill.py`) para cada módulo.

---

## 📋 CONTEXTO DEL ENTORNO (Para la IA)
- **OS:** Windows 10/11
- **Motor LLM:** Ollama local (modelo `jarvis`)
- **Interfaz actual:** Servidor HTTP en Python (`jarvis_voice_server.py`) en puerto 5176 que se comunica por API con un frontend Web (HTML/JS) y reproduce audio TTS localmente vía `pygame` y `edge-tts`.
- **Regla de oro:** Todas las herramientas instaladas deben ser asíncronas (`asyncio`) o no bloqueantes, para no congelar el servidor de voz ni la reproducción del TTS.

---

## 🛠️ FASE 1: AUTOMATIZACIÓN Y CONTROL DEL SISTEMA (WINDOWS)
*Habilidad para controlar el PC, volumen, brillo y simular pulsaciones.*

- [x] **Control de Volumen y Audio (`pycaw`, `comtypes`)**
  - **Objetivo:** Permitir a Jarvis mutear, subir o bajar el volumen del sistema.
  - **Instalación:** `pip install pycaw comtypes`
- [x] **Automatización de Teclado/Ratón (`pyautogui`)**
  - **Objetivo:** Abrir menús, simular atajos de teclado (ej. Win+D para escritorio).
  - **Instalación:** `pip install pyautogui`
- [x] **Control de brillo de pantalla (`screen-brightness-control`)**
  - **Objetivo:** Ajustar el brillo ("Jarvis, baja el brillo al 30%").
  - **Instalación:** `pip install screen-brightness-control`

## 🌐 FASE 2: CONEXIÓN AL MUNDO EXTERIOR (BÚSQUEDA Y EXTRACCIÓN)
*Habilidad para que Jarvis busque datos en tiempo real cuando Ollama no los sepa.*

- [x] **Búsqueda web sin API Keys (`duckduckgo-search`)**
  - **Objetivo:** Buscar noticias, clima o datos rápidos en la web de forma anónima y gratuita.
  - **Instalación:** `pip install duckduckgo-search`
- [x] **Navegación y Extracción de webs dinámicas (`playwright`, `beautifulsoup4`)**
  - **Objetivo:** Leer el contenido de un link para resumirlo.
  - **Instalación:** `pip install beautifulsoup4 playwright` y ejecutar `playwright install chromium`
- [x] **Peticiones HTTP eficientes (`aiohttp`)**
  - **Objetivo:** Reemplazar `urllib` o `requests` bloqueantes por peticiones asíncronas rápidas a APIs externas (clima, bolsa, etc.).
  - **Instalación:** `pip install aiohttp`

## 👁️ FASE 3: VISIÓN COMPUTACIONAL Y OCR
*Habilidad para que Jarvis vea la pantalla o lea documentos.*

- [x] **Captura de Pantalla nativa (`Pillow`, `mss`)**
  - **Objetivo:** Tomar capturas ultrarrápidas de lo que el usuario está viendo.
  - **Instalación:** `pip install Pillow mss`
- [ ] **Reconocimiento Óptico de Caracteres (`pytesseract`)**
  - **Objetivo:** Extraer texto de la captura de pantalla o de imágenes.
  - **Requisito externo:** Instalar [Tesseract OCR para Windows](https://github.com/UB-Mannheim/tesseract/wiki) y añadirlo al PATH.
  - **Instalación:** `pip install pytesseract`
- [x] **Visión Avanzada (`opencv-python`)**
  - **Objetivo:** Detección facial o de movimiento usando la webcam.
  - **Instalación:** `pip install opencv-python`

## 🎵 FASE 4: MULTIMEDIA Y DOMÓTICA
*Integración con servicios de terceros y dispositivos inteligentes.*

- [x] **Control de Spotify (`spotipy`)**
  - **Objetivo:** Reproducir música, pausar, saltar canciones.
  - **Instalación:** `pip install spotipy`
  - **Nota:** Requiere crear una app en Spotify Developer Dashboard para obtener Client ID y Secret.
- [x] **Control Domótico (`homeassistant-api` / genérico MQTT)**
  - **Objetivo:** Apagar/encender luces inteligentes o enchufes si el usuario tiene Home Assistant, Alexa o Google Home.
  - **Instalación:** `pip install paho-mqtt` (si usa MQTT local) o simple `aiohttp` para Webhooks.

---

## 🚀 INSTRUCCIONES DE EJECUCIÓN (Checklist Operativo)

Para la IA que continuará el trabajo:
1. Revisa qué paquetes ya están instalados usando `pip list`.
2. Instala las librerías fase por fase en la terminal.
3. **Manejo de dependencias cruzadas:** Asegúrate de que las versiones instaladas no creen conflictos con `edge-tts` o `pygame`.
4. Crea un script llamado `test_skills.py` donde importes cada librería recién instalada e imprimas su versión para confirmar que el entorno está sano.
5. Si un paquete (como `playwright` o `tesseract`) requiere instalación de binarios externos, describe claramente el comando o script PowerShell necesario para automatizar su descarga.
6. Al terminar, marca las casillas de este checklist reemplazando `[ ]` por `[x]` y genera un reporte.
