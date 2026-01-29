# -*- coding: utf-8 -*-
"""
Gerenciador de Inicialização Automática (Windows).

Permite registrar a aplicação para iniciar junto com o Windows
modificando a chave de registro HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
"""

import sys
import os
import winreg
from core.logger import obter_logger

logger = obter_logger('autostart')

CHAVE_REGISTRO = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOME_APP = "VoiceFlow"

def obter_comando_inicializacao() -> str:
    """
    Retorna o comando correto para iniciar a aplicação.
    Suporta tanto modo script (dev) quanto executável congelado (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # Executável compilado (PyInstaller)
        caminho_exe = sys.executable
        return f'"{caminho_exe}"'
    else:
        # Script Python (Dev)
        python_exe = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        # Usa pythonw.exe se disponível para não abrir console
        if "python.exe" in python_exe:
            python_exe = python_exe.replace("python.exe", "pythonw.exe")
        return f'"{python_exe}" "{script_path}"'

def verificar_autostart() -> bool:
    """Verifica se o autostart está ativado no registro."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHAVE_REGISTRO, 0, winreg.KEY_READ)
        valor, _ = winreg.QueryValueEx(key, NOME_APP)
        winreg.CloseKey(key)
        
        comando_atual = obter_comando_inicializacao()
        
        # Verifica se o comando salvo é o mesmo do app atual
        if valor == comando_atual:
            return True
        else:
            logger.warning(f"Autostart configurado mas caminho difere: {valor} != {comando_atual}")
            return False
            
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar autostart: {e}")
        return False

def definir_autostart(ativar: bool) -> bool:
    """Define ou remove o autostart no registro."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHAVE_REGISTRO, 0, winreg.KEY_WRITE)
        
        if ativar:
            comando = obter_comando_inicializacao()
            winreg.SetValueEx(key, NOME_APP, 0, winreg.REG_SZ, comando)
            logger.info(f"Autostart ativado: {comando}")
        else:
            try:
                winreg.DeleteValue(key, NOME_APP)
                logger.info("Autostart removido")
            except FileNotFoundError:
                pass # Já não existia
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        logger.error(f"Erro ao definir autostart ({ativar}): {e}")
        return False
