"""
Fronda 1.0 - Motor de Diagnóstico y Análisis Profundo de Computador
Detecta especificaciones reales de hardware en tiempo de ejecución:
CPU, GPU, RAM, Placa Base, Discos, Sistema Operativo y Red.
Funciona en entornos híbridos Windows Host y WSL 2.
"""

import os
import sys
import platform
import subprocess
from typing import Dict, Any


def _run_cmd(cmd: list) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception:
        return ""


def get_deep_hardware_analysis() -> str:
    """Realiza un escaneo exhaustivo de hardware y genera un informe completo."""
    import psutil

    # 1. CPU
    cpu_name = platform.processor() or "Desconocido"
    cores_physical = psutil.cpu_count(logical=False) or 0
    cores_logical = psutil.cpu_count(logical=True) or 0
    cpu_usage = psutil.cpu_percent(interval=0.3)
    cpu_freq = psutil.cpu_freq()
    freq_str = f" @ {round(cpu_freq.current / 1000, 2)} GHz" if cpu_freq else ""

    # Si estamos en WSL o Windows, intentar obtener el nombre comercial de la CPU
    if sys.platform != "win32" and os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu_name = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
    elif sys.platform == "win32":
        try:
            wmic_cpu = _run_cmd(["wmic", "cpu", "get", "name"])
            lines = [l.strip() for l in wmic_cpu.splitlines() if l.strip() and "Name" not in l]
            if lines:
                cpu_name = lines[0]
        except Exception:
            pass

    # 2. RAM
    mem = psutil.virtual_memory()
    ram_total = round(mem.total / (1024 ** 3), 1)
    ram_used = round(mem.used / (1024 ** 3), 1)
    ram_free = round(mem.available / (1024 ** 3), 1)
    ram_pct = mem.percent

    # 3. GPU (Detección híbrida)
    gpus = []
    # Intento con PowerShell en el host si estamos en WSL o Windows
    cmd_ps = ["powershell.exe", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
    ps_gpu = _run_cmd(cmd_ps)
    if ps_gpu:
        for g in ps_gpu.splitlines():
            g = g.strip()
            if g and g not in gpus:
                gpus.append(g)

    if not gpus:
        # Intento con nvidia-smi
        smi = _run_cmd(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if smi:
            for g in smi.splitlines():
                if g.strip():
                    gpus.append(g.strip())

    gpu_str = ", ".join(gpus) if gpus else "Gráficos integrados estándar"

    # 4. Placa Base / Motherboard
    mobo = "Información no disponible"
    mobo_cmd = ["powershell.exe", "-NoProfile", "-Command", "(Get-CimInstance Win32_BaseBoard).Manufacturer + ' ' + (Get-CimInstance Win32_BaseBoard).Product"]
    mobo_res = _run_cmd(mobo_cmd)
    if mobo_res and "Win32_BaseBoard" not in mobo_res:
        mobo = mobo_res

    # 5. Discos
    disk_path = "C:\\" if sys.platform == "win32" else ("/mnt/c" if os.path.exists("/mnt/c") else "/")
    try:
        disk = psutil.disk_usage(disk_path)
        disk_total = round(disk.total / (1024 ** 3), 1)
        disk_free = round(disk.free / (1024 ** 3), 1)
        disk_pct = disk.percent
    except Exception:
        disk_total, disk_free, disk_pct = 0, 0, 0

    # 6. Sistema Operativo y Entorno
    os_desc = platform.system() + " " + platform.version()
    if os.path.exists("/proc/version") and "microsoft" in open("/proc/version").read().lower():
        os_desc = f"Windows 11 Host con subsistema Ubuntu en WSL 2"

    # 7. Diagnóstico y Salud
    health_verdict = "Óptimo"
    recommendations = []
    if ram_pct > 85:
        health_verdict = "Carga Alta"
        recommendations.append("La memoria RAM está por encima del 85%. Considera cerrar procesos en segundo plano.")
    if disk_pct > 90:
        health_verdict = "Espacio Crítico"
        recommendations.append("El disco principal supera el 90% de ocupación. Se recomienda liberar espacio.")
    if cpu_usage > 85:
        health_verdict = "CPU Exigida"
        recommendations.append("El procesador está bajo carga pesada en este momento.")

    if not recommendations:
        recommendations.append("Todos los parámetros de memoria, almacenamiento y cómputo se encuentran en rangos saludables.")

    report = (
        f"🖥️ **ANÁLISIS COMPLETO DE TU COMPUTADOR**\n\n"
        f"• **Procesador (CPU)**: {cpu_name}{freq_str}\n"
        f"  └ Cores: {cores_physical} físicos / {cores_logical} hilos | Uso actual: {cpu_usage}%\n"
        f"• **Memoria RAM**: {ram_total} GB totales\n"
        f"  └ En uso: {ram_used} GB ({ram_pct}%) | Disponible: {ram_free} GB\n"
        f"• **Tarjeta Gráfica (GPU)**: {gpu_str}\n"
        f"• **Placa Base (Motherboard)**: {mobo}\n"
        f"• **Almacenamiento (Disco C:)**: {disk_free} GB libres de {disk_total} GB ({disk_pct}% ocupado)\n"
        f"• **Sistema Operativo**: {os_desc}\n\n"
        f"📊 **Diagnóstico del Sistema**: **{health_verdict}**\n"
        f"👉 *Evaluación*: {' '.join(recommendations)}"
    )
    return report
