"""
Fronda 1.0 - Cross-Platform System Telemetry & OS Engine
Proporciona diagnóstico de hardware y entorno de ejecución en Windows y Linux WSL 2.
"""
import os
import sys
import psutil
from typing import Dict, Any

def get_system_telemetry() -> Dict[str, Any]:
    """Retorna métricas de CPU, RAM y almacenamiento."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.2)
        disk_path = '/'
        if sys.platform == 'win32':
            disk_path = 'C:\\'
        elif os.path.exists('/mnt/c'):
            disk_path = '/mnt/c'
        disk = psutil.disk_usage(disk_path)
        ram = psutil.virtual_memory()

        telemetry = {
            "cpu_percent": cpu_usage,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 1),
            "os_environment": "WSL 2 (Ubuntu 26.04) + Windows 11 Host" if os.path.exists('/mnt/c') else sys.platform
        }

        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                telemetry["battery_percent"] = battery.percent
                telemetry["power_plugged"] = battery.power_plugged

        return telemetry
    except Exception as e:
        return {"error": str(e)}

def get_os_info() -> str:
    """Retorna descripción formal del sistema híbrido."""
    return ("Tu entorno activo es una arquitectura híbrida multi-agente:\n"
            "• Sistema Anfitrión: Windows 11 (C: accesible en /mnt/c)\n"
            "• Subsistema Nativo: Linux Ubuntu 26.04 LTS en WSL 2 (con Ollama y Python 3.14 integrados)\n"
            "• Agente: Fronda 1.0 operando con comunicación directa en Linux y renderizado en Windows.")
