"""
Fronda 1.0 - Logger Estructurado
Configura handlers de consola y archivo con rotación diaria.
"""
import logging
import logging.handlers
from pathlib import Path

_initialized = False

def get_logger(name: str = "fronda") -> logging.Logger:
    """Retorna el logger configurado de Fronda."""
    global _initialized
    logger = logging.getLogger(name)

    if _initialized:
        return logger

    logger.setLevel(logging.DEBUG)

    # ─── Handler de consola (INFO+) ──────────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(console)

    # ─── Handler de archivo con rotación diaria (DEBUG+) ─────────────────────
    try:
        # Importar config aquí para evitar importaciones circulares
        from config import logs_dir
        log_path = logs_dir() / "fronda.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_path,
            when="midnight",
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"No se pudo configurar el log en archivo: {e}")

    _initialized = True
    return logger

# Logger raíz de Fronda
log = get_logger("fronda")
