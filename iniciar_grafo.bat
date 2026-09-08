@echo off
title Fronda 1.0 — Kuzu Graph Explorer
color 0b

cd /d "%~dp0"

echo =======================================================
echo    FRONDA 1.0 — VISUALIZADOR DE GRAFO KUZU (Vis.js)
echo    Base de Datos : .kuzu_codegraph (Read-Only)
echo    Explorador Web: http://127.0.0.1:5050
echo =======================================================
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe visualizar_kuzu.py --port 5050
) else (
    python visualizar_kuzu.py --port 5050
)

pause
