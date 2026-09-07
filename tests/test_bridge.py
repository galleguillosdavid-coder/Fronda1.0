"""
Tests del FrondaBridge — Fronda 1.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
import json


def _make_bridge():
    with patch("fronda_bridge._detect_wsl_distro", return_value="Ubuntu"), \
         patch.object(__import__("fronda_bridge").FrondaBridge, "_resolve_ollama_url", return_value="http://127.0.0.1:11434"):
        from fronda_bridge import FrondaBridge
        return FrondaBridge()


def test_check_health_online():
    mock_response = MagicMock()
    mock_response.status  = 200
    mock_response.read.return_value = json.dumps({
        "models": [{"name": "frondabrick"}, {"name": "qwen2.5-coder:1.5b"}]
    }).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__  = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        from fronda_bridge import FrondaBridge
        bridge = FrondaBridge.__new__(FrondaBridge)
        bridge.model       = "frondabrick"
        bridge.ollama_url  = "http://127.0.0.1:11434"
        bridge._wsl_distro = "Ubuntu"
        health = bridge.check_health()

    assert health["status"] == "online"
    assert "frondabrick" in health.get("models", [])
    assert health["target_model_ready"] is True


def test_check_health_offline():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        from fronda_bridge import FrondaBridge
        bridge = FrondaBridge.__new__(FrondaBridge)
        bridge.model       = "frondabrick"
        bridge.ollama_url  = "http://127.0.0.1:11434"
        bridge._wsl_distro = "Ubuntu"
        health = bridge.check_health()

    assert health["status"] == "offline"
    assert "error" in health


def test_run_wsl_command_safe():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout     = "Linux 5.15.153.1-microsoft-standard-WSL2"
    mock_result.stderr     = ""

    with patch("subprocess.run", return_value=mock_result):
        from fronda_bridge import FrondaBridge
        bridge = FrondaBridge.__new__(FrondaBridge)
        bridge._wsl_distro = "Ubuntu"
        res = bridge.run_wsl_command("uname -r")

    assert res["exit_code"] == 0
    assert "Linux" in res["stdout"]


def test_run_wsl_command_blocked():
    from fronda_bridge import FrondaBridge
    bridge = FrondaBridge.__new__(FrondaBridge)
    bridge._wsl_distro = "Ubuntu"
    # Intentar un comando peligroso
    res = bridge.run_wsl_command("rm -rf /tmp/test && echo done")
    assert res["exit_code"] == -2  # rechazado por validación
    assert "rechazado" in res["stderr"].lower() or "seguridad" in res["stderr"].lower()


def test_detect_wsl_distro_fallback():
    """Si wsl.exe falla, debe retornar Ubuntu como fallback."""
    with patch("subprocess.run", side_effect=Exception("wsl not found")):
        from fronda_bridge import _detect_wsl_distro
        distro = _detect_wsl_distro()
    assert distro == "Ubuntu"


def test_run_windows_command_and_admin():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Windows Command OK"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        from fronda_bridge import FrondaBridge
        bridge = FrondaBridge.__new__(FrondaBridge)
        bridge._wsl_distro = "Ubuntu"

        res = bridge.run_windows_command("Get-Process")
        assert res["exit_code"] == 0
        assert res["stdout"] == "Windows Command OK"
        assert res["as_admin"] is False

        # Test con flag de administrador
        res_admin = bridge.run_windows_command("Get-Process", as_admin=True)
        assert res_admin["exit_code"] == 0
        assert res_admin["as_admin"] is True


def test_run_wsl_command_as_root():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "root"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        from fronda_bridge import FrondaBridge
        bridge = FrondaBridge.__new__(FrondaBridge)
        bridge._wsl_distro = "Ubuntu"

        res = bridge.run_wsl_command("whoami", as_root=True)
        assert res["exit_code"] == 0
        assert res["as_root"] is True

