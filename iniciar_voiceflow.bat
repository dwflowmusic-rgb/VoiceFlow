@echo off
title VoiceFlow Launcher
cd /d "%~dp0"

echo ========================================================
echo [VoiceFlow Transcriber v1.0] Inicializando...
echo ========================================================

echo [1/2] Verificando ambiente...
if not exist ".\venv\Scripts\pythonw.exe" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute: python -m venv venv ^&^& pip install -r requirements.txt
    pause
    exit /b
)

echo [2/2] Iniciando em SEGUNDO PLANO...
start "" ".\venv\Scripts\pythonw.exe" voiceflow.py

echo.
echo ========================================================
echo [SUCESSO] VoiceFlow rodando na bandeja do sistema!
echo.
echo OPCOES DISPONIVEIS NO MENU (botao direito no icone):
echo   - Ver Historico
echo   - Iniciar com Windows
echo   - Auto-Enter apos Colar (NOVO!)
echo   - Sair
echo ========================================================
timeout /t 5
exit
