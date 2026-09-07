@echo off
echo ========================================
echo    FRONDA 1.0 - Suite de Tests
echo ========================================
cd /d "%~dp0"
python -m pytest tests/ -v --tb=short
pause
