@echo off
title Jarvis - Interfaz de Voz Neural
color 0b

cd /d "C:\Users\Frondabrick\Desktop\dvd\11"

echo =======================================================
echo         JARVIS - INTERFAZ DE VOZ NEURAL
echo         Voz: es-ES-AlvaroNeural
echo         Puerto: http://127.0.0.1:5176
echo =======================================================
echo.

:: Matar instancia anterior si existe
echo [INFO] Limpiando puerto 5176...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5176 " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: Iniciar servidor de voz en segundo plano
echo [INFO] Iniciando servidor de voz...
start "Jarvis Voice Server" python jarvis_voice_server.py

:: Esperar a que el servidor arranque
timeout /t 3 /nobreak >nul

:: Abrir la interfaz web
echo [INFO] Abriendo interfaz en http://127.0.0.1:5176
start "" "http://127.0.0.1:5176"

echo.
echo [OK] Jarvis activo. Cierra esta ventana para apagar.
pause
