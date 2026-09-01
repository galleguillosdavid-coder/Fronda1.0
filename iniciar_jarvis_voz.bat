@echo off
title JARVIS Voice Assistant - Neural Engine
color 0a

echo =======================================================
echo     INICIANDO ASISTENTE DE VOZ NEURAL (J.A.R.V.I.S.)
echo =======================================================
echo.

cd /d "C:\Users\Frondabrick\Desktop\dvd\11"

:: 1. Verificar Ollama
tasklist /fi "imagename eq ollama.exe" 2>NUL | find /i /n "ollama.exe">NUL
if not "%ERRORLEVEL%"=="0" (
    echo [INFO] Iniciando Ollama...
    start "" ollama serve
    timeout /t 2 /nobreak >nul
)

:: 2. Ejecutar motor de voz en Python
python jarvis_voice_engine.py
pause
