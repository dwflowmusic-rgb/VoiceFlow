@echo off
title VoiceFlow DEBUG
cd /d "%~dp0"

echo [DEBUG] Iniciando com python.exe (Console Ativo)...
echo.
.\venv\Scripts\python.exe voiceflow.py

echo.
echo ========================================================
echo O programa encerrou. Veja o erro acima.
echo ========================================================
pause
