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

:: Asegurar entorno WSL y Ollama activo
echo [INFO] Inicializando motor Fronda Brick en WSL 2...
start /B "" wsl.exe -d Ubuntu -e bash -c "nohup /usr/local/bin/ollama serve > ~/.ollama/ollama.log 2>&1 & sleep 1; tail -f /dev/null" >nul 2>&1

timeout /t 2 /nobreak >nul

:: Iniciar servidor Fronda de forma nativa en Linux WSL 2
echo [INFO] Inicializando servidor de Fronda 1.0 en subsistema Linux Ubuntu WSL 2...
start "Fronda 1.0 WSL Engine" wsl.exe -d Ubuntu -e bash -c "cd /mnt/c/Users/Frondabrick/Desktop/dvd/Fronda/Fronda1.0 && python3 -u fronda_voice_server.py"

:: Esperar a que el servidor arranque
timeout /t 2 /nobreak >nul

:: Abrir la interfaz web
echo [INFO] Abriendo HUD en http://127.0.0.1:5176
start "" "http://127.0.0.1:5176"

echo.
echo [OK] Fronda 1.0 activo y escuchando. Cierra esta ventana para finalizar la sesion.
pause
