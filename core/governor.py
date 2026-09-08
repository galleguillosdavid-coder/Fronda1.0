"""
Fronda 1.0 - Gobernanza Cibernética y Circuit Breaker (Inspirado en el S5 de CynCo / Cybersyn)
Protege la estabilidad de Fronda evitando que herramientas defectuosas o bucles de
inferencia congelen el sistema.
- C1 / C2: Tool Circuit Breaker (excluye temporalmente un skill que falle 3 veces consecutivas)
- C4: Doom Loop Breaker (detecta respuestas repetitivas o bucles idénticos)
"""
import time
import threading
from typing import Dict, Any, List, Optional
from fronda_logger import get_logger

log = get_logger("fronda.governor")


class ToolState:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.consecutive_failures: int = 0
        self.total_failures: int = 0
        self.total_successes: int = 0
        self.is_tripped: bool = False
        self.tripped_at: float = 0.0
        self.last_error: str = ""
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds


class CyberneticGovernor:
    """
    Controlador de políticas cibernéticas y estabilidad homeostática para Fronda.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self._lock = threading.Lock()
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._tools: Dict[str, ToolState] = {}
        self._recent_outputs: List[str] = []
        self._max_recent_history: int = 10
        self.cpu_guard_active: bool = False

    def get_tool_state(self, tool_name: str) -> ToolState:
        with self._lock:
            if tool_name not in self._tools:
                self._tools[tool_name] = ToolState(
                    failure_threshold=self.failure_threshold,
                    cooldown_seconds=self.cooldown_seconds
                )
            return self._tools[tool_name]

    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        Verifica si una herramienta o skill tiene permiso de ejecución
        o si ha sido aislada temporalmente por la regla C2.
        """
        with self._lock:
            if tool_name not in self._tools:
                return True

            state = self._tools[tool_name]
            if not state.is_tripped:
                return True

            # Verificar si el cooldown ya expiró (auto-recuperación)
            now = time.time()
            if (now - state.tripped_at) >= state.cooldown_seconds:
                state.is_tripped = False
                state.consecutive_failures = 0
                log.info(f"[S5 Governor] Cooldown expirado para tool '{tool_name}'. Circuito restablecido.")
                return True

            return False

    def record_tool_result(self, tool_name: str, success: bool, error_msg: str = ""):
        """Registra el resultado de una ejecución y aplica reglas C1/C2."""
        with self._lock:
            if tool_name not in self._tools:
                self._tools[tool_name] = ToolState(
                    failure_threshold=self.failure_threshold,
                    cooldown_seconds=self.cooldown_seconds
                )

            state = self._tools[tool_name]
            if success:
                state.total_successes += 1
                state.consecutive_failures = 0
                state.is_tripped = False
                state.last_error = ""
            else:
                state.total_failures += 1
                state.consecutive_failures += 1
                state.last_error = error_msg
                log.warning(f"[S5 Governor] Tool '{tool_name}' falló ({state.consecutive_failures}/{state.failure_threshold}): {error_msg}")

                if state.consecutive_failures >= state.failure_threshold and not state.is_tripped:
                    state.is_tripped = True
                    state.tripped_at = time.time()
                    log.error(f"[S5 Governor] REGLA C2 ACTIVADA: Tool '{tool_name}' aislada por {state.cooldown_seconds}s tras {state.consecutive_failures} fallos continuos.")

    def check_doom_loop(self, current_output: str) -> bool:
        """
        REGLA C4: Detecta si la salida actual es idéntica a las últimas 2 salidas
        (bucle de inferencia infinito).
        """
        if not current_output or len(current_output.strip()) < 5:
            return False

        clean_current = current_output.strip()
        with self._lock:
            self._recent_outputs.append(clean_current)
            if len(self._recent_outputs) > self._max_recent_history:
                self._recent_outputs.pop(0)

            if len(self._recent_outputs) >= 3:
                last_3 = self._recent_outputs[-3:]
                if last_3[0] == last_3[1] == last_3[2]:
                    log.error(f"[S5 Governor] REGLA C4 ACTIVADA: Doom loop detectado en inferencia (3 salidas idénticas).")
                    return True

        return False

    # ── Regla C5: CPU Thermal & Headroom Guard ──────────────────────────────
    def get_cpu_headroom(self) -> dict:
        """Retorna el porcentaje de CPU disponible (libre) en el sistema y meta de headroom."""
        try:
            import psutil
            usage = psutil.cpu_percent(interval=None)
            free = max(0.0, 100.0 - usage)
            target = getattr(config.get().resources, "cpu_headroom_target_percent", 15)
            return {
                "cpu_percent": usage,
                "cpu_headroom_percent": free,
                "target_headroom_percent": target
            }
        except Exception:
            return {
                "cpu_percent": 50.0,
                "cpu_headroom_percent": 50.0,
                "target_headroom_percent": 15
            }

    def apply_low_priority_guard(self):
        """
        Ajusta la prioridad del proceso a 'Below Normal' para evitar que la
        inferencia sature el 100% y congele otras aplicaciones o Windows.
        """
        try:
            import psutil
            p = psutil.Process()
            if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            else:
                # Linux / WSL
                import os
                try:
                    os.nice(5)
                except Exception:
                    pass
            log.info("[S5 Governor] Regla C5 aplicada: Prioridad de CPU moderada para proteger la estabilidad térmica.")
            self.cpu_guard_active = True
            return True
        except Exception as e:
            log.debug(f"[S5 Governor] No se pudo ajustar nice/prioridad: {e}")
            self.cpu_guard_active = False
            return False

    def reset(self):
        """Reinicia todos los contadores de gobernanza."""
        with self._lock:
            self._tools.clear()
            self._recent_outputs.clear()

    def get_status_report(self) -> Dict[str, Any]:
        """Genera un reporte de salud del sistema y sus herramientas."""
        with self._lock:
            report = {}
            for name, state in self._tools.items():
                report[name] = {
                    "is_tripped": state.is_tripped,
                    "consecutive_failures": state.consecutive_failures,
                    "total_successes": state.total_successes,
                    "total_failures": state.total_failures,
                    "last_error": state.last_error
                }
            headroom_info = self.get_cpu_headroom()
            report["cpu_headroom_percent"] = round(headroom_info.get("cpu_headroom_percent", 50.0), 1)
            report["cpu_percent"] = round(headroom_info.get("cpu_percent", 50.0), 1)
            report["cpu_guard_active"] = self.cpu_guard_active
            return report


# Instancia singleton del Governor
governor = CyberneticGovernor()
# Aplicar protección de prioridad al importar
governor.apply_low_priority_guard()
