@echo off
title Fronda 1.0 - Interfaz de Voz Neural
color 0a

cd /d "%~dp0"

echo =======================================================
echo         FRONDA 1.0 - CLON DIGITAL DE DAVID GALLEGUILLOS
echo         Voz: es-ES-AlvaroNeural
echo         Puerto: http://127.0.0.1:5176
echo =======================================================
echo.

:: Limpiar puerto 5176 si estuviera ocupado
echo [INFO] Verificando puerto 5176...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5176 " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: Iniciar servidor Fronda en WSL
echo [INFO] Iniciando servidor de Fronda 1.0 en WSL Ubuntu...
start "Fronda 1.0 WSL Engine" wsl.exe -d Ubuntu -e bash -c "cd /mnt/c/Users/Frondabrick/Desktop/dvd/Fronda/Fronda1.0 && python3 -u fronda_voice_server.py"

:: Esperar a que el servidor arranque
timeout /t 2 /nobreak >nul

:: Abrir la interfaz web
echo [INFO] Abriendo interfaz en http://127.0.0.1:5176
start "" "http://127.0.0.1:5176"

echo.
echo [OK] Fronda 1.0 activo. Cierra esta ventana para apagar.
pause
