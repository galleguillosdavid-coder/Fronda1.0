@echo off
title Fronda 1.0 - Clon Digital de David Galleguillos
color 0a

cd /d "%~dp0"

echo =======================================================
echo         FRONDA 1.0 - CLON DIGITAL DE DAVID GALLEGUILLOS
echo         Motor: Ollama (Modelo fronda)
echo         Voz: es-ES-AlvaroNeural (Multi-hilo)
echo         Interfaz Web: http://127.0.0.1:5176
echo =======================================================
echo.

:: Liberar puerto 5176 si estuviera ocupado
echo [INFO] Verificando puerto 5176...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5176 " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: Iniciar servidor Fronda en segundo plano
echo [INFO] Inicializando servidor de Fronda 1.0...
start "Fronda 1.0 Voice Server" python fronda_voice_server.py

:: Esperar a que el servidor arranque
timeout /t 2 /nobreak >nul

:: Abrir la interfaz web
echo [INFO] Abriendo HUD en http://127.0.0.1:5176
start "" "http://127.0.0.1:5176"

echo.
echo [OK] Fronda 1.0 activo y escuchando. Cierra esta ventana para finalizar la sesion.
pause
