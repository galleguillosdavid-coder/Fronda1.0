"""
Fronda 1.0 - Motor de Visión Multimodal por Computadora
Permite capturar la pantalla y analizar imágenes en tiempo real
usando el modelo multimodal ligero local 'moondream' en Ollama.
"""

import os
import sys
import io
import json
import base64
import urllib.request
from pathlib import Path
from typing import Optional

from fronda_logger import get_logger

log = get_logger("fronda.vision")


def _get_ollama_url() -> str:
    try:
        import config
        return config.get().ollama.url
    except Exception:
        return "http://127.0.0.1:11434"


def _encode_image_to_base64(image_path: str, max_size=(1024, 768)) -> Optional[str]:
    """Carga una imagen, la redimensiona para velocidad de inferencia y la pasa a Base64."""
    if not os.path.exists(image_path):
        return None
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        log.warning(f"PIL no disponible o error al redimensionar ({e}), leyendo bytes directos...")
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e2:
            log.error(f"Error al leer imagen directamente: {e2}")
            return None


def capture_screen_image(output_path: str = "capturas/screen_vision.png") -> Optional[str]:
    """Captura la pantalla actual y retorna la ruta del archivo generado."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Intento 1: MSS (si está en sesión gráfica interactiva)
    try:
        import mss
        mss_cls = getattr(mss, "MSS", getattr(mss, "mss", None))
        if mss_cls:
            with mss_cls() as sct:
                sct.shot(output=str(out))
                if out.exists() and out.stat().st_size > 0:
                    return str(out)
    except Exception:
        pass

    # Intento 2: Pillow ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(str(out))
        if out.exists() and out.stat().st_size > 0:
            return str(out)
    except Exception:
        pass

    # Intento 3: Buscar la captura más reciente en capturas/
    try:
        cap_dir = Path("capturas")
        if cap_dir.exists():
            files = sorted(
                [f for f in cap_dir.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            if files:
                return str(files[0])
    except Exception:
        pass

    return None


def analyze_screen_vision(prompt: str = "") -> str:
    """
    Captura la pantalla y consulta al modelo de visión 'moondream' en Ollama.
    """
    screen_path = capture_screen_image()
    if not screen_path or not os.path.exists(screen_path):
        return (
            "No se pudo capturar la pantalla automáticamente en este entorno. "
            "Asegúrate de tener una imagen en la carpeta 'capturas/' para que Fronda pueda analizarla."
        )

    b64_image = _encode_image_to_base64(screen_path)
    if not b64_image:
        return "Error al procesar los píxeles de la captura de pantalla."

    # Moondream 1.4B está optimizado para instrucciones de visión en inglés
    vision_prompt = (
        "Describe what you see on this screen in detail: identify open applications, "
        "windows, code, readable text, and any visible status or error messages."
    )
    if prompt and any(w in prompt.lower() for w in ["error", "fallo", "bug", "exception"]):
        vision_prompt = "Carefully identify and read any error messages, logs, or exceptions visible on this screen."
    elif prompt and any(w in prompt.lower() for w in ["texto", "lee", "código", "codigo", "read"]):
        vision_prompt = "Transcribe and summarize the readable text or code visible on this screen."

    ollama_url = _get_ollama_url().rstrip("/")
    payload = {
        "model": "moondream",
        "prompt": vision_prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 2048,
        }
    }

    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answer = data.get("response", "").strip()

            if not answer:
                answer = "El modelo de visión procesó la imagen pero no devolvió descripción."

            return (
                f"👁️ **ANÁLISIS DE VISIÓN MULTIMODAL (Moondream 1.4B)**\n"
                f"• **Captura analizada**: `{os.path.basename(screen_path)}`\n\n"
                f"{answer}"
            )
    except Exception as e:
        return f"Error en la inferencia multimodal de visión con Ollama: {e}"
