"""
Fronda 1.0 - Motor de Procesamiento y Conversión Multimedia
Utiliza ffmpeg para convertir formatos de audio y video (ej. MKV a MP4).
"""

import os
import shutil
import subprocess
from pathlib import Path


def _find_ffmpeg() -> str:
    """Localiza el binario de ffmpeg en Windows o Linux."""
    # Buscar en PATH
    ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if ff:
        return ff

    # Rutas comunes en Windows
    winget_link = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe")
    if os.path.exists(winget_link):
        return winget_link

    return ""


def convert_media_file(input_path: str, target_format: str = "mp4") -> str:
    """Convierte un archivo de video o audio al formato deseado usando ffmpeg."""
    clean_in = input_path.strip().strip('"').strip("'")
    if not os.path.exists(clean_in):
        return f"El archivo origen '{clean_in}' no existe en el sistema."

    ffmpeg_bin = _find_ffmpeg()
    if not ffmpeg_bin:
        return "ffmpeg no se encuentra instalado o disponible en el PATH del sistema."

    in_file = Path(clean_in)
    out_file = in_file.with_suffix(f".{target_format.lower().lstrip('.')}")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(in_file),
        "-c:v", "copy",
        "-c:a", "aac",
        str(out_file)
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and out_file.exists():
            size_mb = round(out_file.stat().st_size / (1024 * 1024), 2)
            return (
                f"🎬 **CONVERSIÓN MULTIMEDIA EXITOSA**\n"
                f"• **Origen**: `{in_file.name}`\n"
                f"• **Destino**: `{out_file.name}` ({size_mb} MB)\n"
                f"• **Ruta**: `{out_file.resolve()}`"
            )
        else:
            return f"Error en la conversión con ffmpeg: {res.stderr[:300]}"
    except subprocess.TimeoutExpired:
        return "La conversión tardó demasiado tiempo y fue interrumpida."
    except Exception as e:
        return f"Error al ejecutar conversión: {e}"
