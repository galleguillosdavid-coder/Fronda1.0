"""
Fronda 1.0 - Cross-Platform System Telemetry & OS Engine
Proporciona diagnóstico de hardware y entorno de ejecución en Windows y Linux WSL 2.
Detecta el OS real en tiempo de ejecución; no usa strings hardcodeados.
"""
import os
import sys
import platform
import subprocess
from typing import Dict, Any

from fronda_logger import get_logger

log = get_logger("fronda.system")


def _detect_disk_path() -> str:
    """Detecta el path de disco principal según el entorno."""
    try:
        import config
        cfg_path = config.get().paths
        # Si hay un path de disco personalizado en config lo usamos
    except Exception:
        pass

    if sys.platform == "win32":
        return "C:\\"
    if os.path.exists("/mnt/c"):
        return "/mnt/c"
    return "/"


def _detect_wsl_version() -> str:
    """Detecta la versión de kernel WSL si está disponible."""
    try:
        result = subprocess.run(
            ["uname", "-r"],
            capture_output=True, text=True, timeout=3
        )
        kernel = result.stdout.strip()
        if "microsoft" in kernel.lower():
            return kernel
    except Exception:
        pass
    return ""


def _detect_linux_distro() -> str:
    """Detecta la distribución Linux real (si estamos en WSL o Linux nativo)."""
    try:
        result = subprocess.run(
            ["lsb_release", "-d", "-s"],
            capture_output=True, text=True, timeout=3
        )
        distro = result.stdout.strip().strip('"')
        if distro:
            return distro
    except Exception:
        pass
    # Fallback leyendo /etc/os-release
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "Linux"


def get_system_telemetry() -> Dict[str, Any]:
    """Retorna métricas de CPU, RAM y almacenamiento en tiempo real."""
    try:
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory()  # ← definida correctamente
        disk_path = _detect_disk_path()
        disk = psutil.disk_usage(disk_path)

        telemetry = {
            "cpu_percent":  cpu_usage,
            "cpu_cores":    psutil.cpu_count(logical=True),
            "ram_percent":  ram.percent,
            "ram_used_gb":  round(ram.used / (1024 ** 3), 1),
            "ram_total_gb": round(ram.total / (1024 ** 3), 1),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "disk_path":    disk_path,
            "os_environment": _build_os_description(),
            "platform":     sys.platform,
        }

        # Batería si es laptop
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                telemetry["battery_percent"] = battery.percent
                telemetry["power_plugged"]   = battery.power_plugged

        return telemetry

    except Exception as e:
        log.error(f"Error en telemetría de sistema: {e}")
        return {"error": str(e)}


def _build_os_description() -> str:
    """Construye la descripción del OS detectando el entorno real."""
    if sys.platform == "win32":
        win_ver = platform.version()
        win_name = platform.system()
        return f"{win_name} {win_ver}"

    wsl_kernel = _detect_wsl_version()
    if wsl_kernel or os.path.exists("/mnt/c"):
        distro = _detect_linux_distro()
        # Intentar detectar versión de Windows desde el host
        try:
            res = subprocess.run(
                ["cmd.exe", "/c", "ver"],
                capture_output=True, text=True, timeout=3
            )
            win_ver_str = res.stdout.strip().split("\n")[0].strip()
        except Exception:
            win_ver_str = "Windows Host"
        return f"WSL 2 ({distro}) + {win_ver_str}"

    return f"Linux ({_detect_linux_distro()})"


def get_os_info() -> str:
    """Retorna descripción formal del sistema detectado en tiempo real."""
    if sys.platform == "win32":
        return (
            f"Sistema operativo: {platform.system()} {platform.version()}\n"
            f"• Procesador: {platform.processor()}\n"
            f"• Python: {sys.version.split()[0]}"
        )

    wsl_kernel = _detect_wsl_version()
    distro = _detect_linux_distro()

    if wsl_kernel or os.path.exists("/mnt/c"):
        try:
            import config
            nickname = config.get().user.nickname
        except Exception:
            nickname = "David"

        # Detectar versión de Windows Host
        try:
            res = subprocess.run(
                ["cmd.exe", "/c", "ver"],
                capture_output=True, text=True, timeout=3
            )
            win_ver = res.stdout.strip().split("\n")[0].strip()
        except Exception:
            win_ver = "Windows Host"

        # Detectar versión de Python
        py_ver = f"Python {sys.version.split()[0]}"

        return (
            f"Tu entorno activo es una arquitectura híbrida multi-agente:\n"
            f"• Sistema Anfitrión: {win_ver} (C: accesible en /mnt/c)\n"
            f"• Subsistema Nativo: {distro} en WSL 2"
            + (f" (Kernel: {wsl_kernel})" if wsl_kernel else "") + "\n"
            f"• Agente: Fronda 1.0 operando con {py_ver} en Linux"
        )

    return (
        f"Sistema: Linux — {distro}\n"
        f"• Kernel: {platform.release()}\n"
        f"• Python: {sys.version.split()[0]}"
    )


def detect_hardware_specs() -> dict:
    """Detecta las especificaciones de hardware del sistema en tiempo real."""
    specs = {}
    try:
        import psutil
        specs["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        specs["cpu_cores_logical"] = psutil.cpu_count(logical=True)
        specs["cpu_cores_physical"] = psutil.cpu_count(logical=False)
    except Exception:
        pass

    specs["cpu_name"] = platform.processor() or "Desconocido"
    specs["os"] = platform.system()
    specs["os_version"] = platform.version()
    specs["python_version"] = sys.version.split()[0]

    return specs
