# -*- coding: utf-8 -*-
"""
Detector de Foco e Simulação de Teclado do VoiceFlow Transcriber.

Utiliza Win32 API para:
1. Detectar qual janela está ativa (GetForegroundWindow)
2. Simular atalho Ctrl+V (SendInput) para colagem automática

Isso permite a funcionalidade de "Colagem Inteligente":
Cola apenas se o usuário não mudou de janela durante a transcrição.
"""

import ctypes
from ctypes import wintypes
import time
from typing import Optional

from core.logger import obter_logger

logger = obter_logger('detector_foco')

# Carrega bibliotecas Win32
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Definições de estruturas para SendInput
# https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

VK_CONTROL = 0x11
VK_V = 0x56

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

# Configura tipos de argumentos e retorno
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


def obter_janela_ativa() -> int:
    """
    Retorna o handle (HWND) da janela que atualmente tem o foco.
    
    Returns:
        Handle da janela como inteiro.
    """
    try:
        hwnd = user32.GetForegroundWindow()
        return hwnd
    except Exception as e:
        logger.error(f"Erro ao obter janela ativa: {e}")
        return 0


def simular_ctrl_v() -> bool:
    """
    Simula o pressionamento de Ctrl+V (Colar) via SendInput.
    
    Returns:
        True se a simulação foi enviada com sucesso.
    """
    try:
        # Define sequência de inputs: Ctrl Down, V Down, V Up, Ctrl Up
        inputs = (INPUT * 4)()
        
        # 1. Ctrl Down
        inputs[0].type = INPUT_KEYBOARD
        inputs[0].union.ki.wVk = VK_CONTROL
        inputs[0].union.ki.dwFlags = 0
        
        # 2. V Down
        inputs[1].type = INPUT_KEYBOARD
        inputs[1].union.ki.wVk = VK_V
        inputs[1].union.ki.dwFlags = 0
        
        # 3. V Up
        inputs[2].type = INPUT_KEYBOARD
        inputs[2].union.ki.wVk = VK_V
        inputs[2].union.ki.dwFlags = KEYEVENTF_KEYUP
        
        # 4. Ctrl Up
        inputs[3].type = INPUT_KEYBOARD
        inputs[3].union.ki.wVk = VK_CONTROL
        inputs[3].union.ki.dwFlags = KEYEVENTF_KEYUP
        
        # Envia inputs
        enviados = user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
        
        if enviados == 4:
            logger.info("Simulação de Ctrl+V enviada com sucesso")
            return True
        else:
            logger.warning(f"Simulação de Ctrl+V incompleta: enviou {enviados}/4 eventos")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao simular Ctrl+V: {e}")
        return False


VK_RETURN = 0x0D  # Enter key


def simular_enter() -> bool:
    """
    Simula o pressionamento da tecla Enter via SendInput.
    
    Returns:
        True se a simulação foi enviada com sucesso.
    """
    try:
        # Define sequência de inputs: Enter Down, Enter Up
        inputs = (INPUT * 2)()
        
        # 1. Enter Down
        inputs[0].type = INPUT_KEYBOARD
        inputs[0].union.ki.wVk = VK_RETURN
        inputs[0].union.ki.dwFlags = 0
        
        # 2. Enter Up
        inputs[1].type = INPUT_KEYBOARD
        inputs[1].union.ki.wVk = VK_RETURN
        inputs[1].union.ki.dwFlags = KEYEVENTF_KEYUP
        
        # Envia inputs
        enviados = user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
        
        if enviados == 2:
            logger.info("Simulação de Enter enviada com sucesso")
            return True
        else:
            logger.warning(f"Simulação de Enter incompleta: enviou {enviados}/2 eventos")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao simular Enter: {e}")
        return False
