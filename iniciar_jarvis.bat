@echo off
title JARVIS AI - Autonomous Life Core Launcher
color 0b

echo =======================================================
echo     INICIANDO J.A.R.V.I.S. (NUCLEO DE VIDA AUTONOMO)
echo =======================================================
echo.

set "TARGET_DIR=C:\Users\Frondabrick\Desktop\dvd\11"
set "OLLAMA_ORIGINS=*"

:: 1. Verificar si Ollama esta corriendo
tasklist /fi "imagename eq ollama.exe" 2>NUL | find /i /n "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Motor Ollama en ejecucion.
) else (
    echo [INFO] Iniciando motor Ollama...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)

:: 2. Iniciar Servidor Web GUI (Puerto 5173) si no esta activo
powershell -NoProfile -Command "if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 5173 -InformationLevel Quiet)) { Start-Process 'python' -ArgumentList '-m', 'http.server', '5173', '--bind', '127.0.0.1', '--directory', 'C:\Users\Frondabrick\Desktop\dvd\11' -WindowStyle Hidden; Start-Sleep -Seconds 1 }"

:: 3. Iniciar Demonio de Consciencia y Telemetria (Puerto 5174) si no esta activo
powershell -NoProfile -Command "if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 5174 -InformationLevel Quiet)) { Start-Process 'python' -ArgumentList 'jarvis_life_core.py' -WorkingDirectory 'C:\Users\Frondabrick\Desktop\dvd\11' -WindowStyle Hidden; Start-Sleep -Seconds 1 }"

:: 4. Abrir la interfaz web conectada
echo [INFO] Abriendo HUD Tactico en http://127.0.0.1:5173/jarvis_gui.html ...
start "" "http://127.0.0.1:5173/jarvis_gui.html"

echo.
echo =======================================================
echo  [EXITO] Jarvis esta vivo y sincronizado con tu PC.
echo =======================================================
timeout /t 3 >nul
exit
