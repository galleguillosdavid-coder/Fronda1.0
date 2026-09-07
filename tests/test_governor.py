"""
Tests unitarios para el gobernador cibernético S5 de Fronda.
"""
import time
from core.governor import CyberneticGovernor


def test_governor_initial_tool_allowed():
    gov = CyberneticGovernor(failure_threshold=3, cooldown_seconds=1.0)
    assert gov.is_tool_allowed("wsl_command") is True


def test_governor_trips_after_threshold():
    gov = CyberneticGovernor(failure_threshold=3, cooldown_seconds=0.2)
    gov.record_tool_result("wsl_command", success=False, error_msg="WSL not responding")
    assert gov.is_tool_allowed("wsl_command") is True

    gov.record_tool_result("wsl_command", success=False, error_msg="WSL not responding")
    assert gov.is_tool_allowed("wsl_command") is True

    # Tercer fallo consecutivo activa C2
    gov.record_tool_result("wsl_command", success=False, error_msg="WSL timeout")
    assert gov.is_tool_allowed("wsl_command") is False


def test_governor_cooldown_recovers():
    gov = CyberneticGovernor(failure_threshold=2, cooldown_seconds=0.1)
    gov.record_tool_result("audio_device", success=False, error_msg="Locked")
    gov.record_tool_result("audio_device", success=False, error_msg="Locked")
    assert gov.is_tool_allowed("audio_device") is False

    # Esperar que expire el cooldown
    time.sleep(0.15)
    assert gov.is_tool_allowed("audio_device") is True


def test_governor_success_resets_failures():
    gov = CyberneticGovernor(failure_threshold=3)
    gov.record_tool_result("ddg_search", success=False, error_msg="Rate limit")
    gov.record_tool_result("ddg_search", success=False, error_msg="Rate limit")
    # Éxito intermedio
    gov.record_tool_result("ddg_search", success=True)
    state = gov.get_tool_state("ddg_search")
    assert state.consecutive_failures == 0
    assert gov.is_tool_allowed("ddg_search") is True


def test_governor_doom_loop_detection():
    gov = CyberneticGovernor()
    assert gov.check_doom_loop("Hola, ¿en qué puedo ayudarte?") is False
    assert gov.check_doom_loop("Hola, ¿en qué puedo ayudarte?") is False
    # Tercera salida idéntica activa C4
    assert gov.check_doom_loop("Hola, ¿en qué puedo ayudarte?") is True


def test_governor_cpu_headroom_guard():
    gov = CyberneticGovernor()
    info = gov.get_cpu_headroom()
    assert "cpu_headroom_percent" in info
    assert "cpu_percent" in info
    assert "target_headroom_percent" in info
    assert 0 <= info["cpu_headroom_percent"] <= 100

    # Verificar que apply_low_priority_guard no arroja excepciones
    res = gov.apply_low_priority_guard()
    assert isinstance(res, bool)

