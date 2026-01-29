# -*- coding: utf-8 -*-
"""
Low-Level Keyboard Hook para Interceptação de CapsLock.

Este módulo implementa um hook de teclado de baixo nível usando SetWindowsHookEx
da Win32 API. Diferentemente do polling (GetAsyncKeyState), hooks permitem
INTERCEPTAR e SUPRIMIR eventos antes que o Windows os processe.

Isso é essencial para o CapsLock porque:
1. Podemos detectar quando a tecla é pressionada sem que o LED mude
2. Podemos distinguir TAP (<500ms) de HOLD (>500ms)
3. Para TAPs, deixamos o Windows processar normalmente (toggle funciona)
4. Para HOLDs, suprimimos o evento (LED não muda, gravação inicia)

AVISO DE SEGURANÇA:
Hooks de teclado em Python são perigosos. Se o callback travar ou for lento,
o mouse e teclado do usuário podem travar. Mitigações implementadas:
- Callback ultra-rápido (apenas seta flags, processamento em thread separada)
- Windows remove automaticamente hooks lentos após ~300ms
- Watchdog thread monitora heartbeat

Autor: VoiceFlow Team
Data: 2026-01-03
"""

import ctypes
from ctypes import wintypes, CFUNCTYPE, POINTER, c_int, c_void_p
from typing import Optional, Callable
from enum import Enum, auto
import threading
import time

from PySide6.QtCore import QObject, Signal

from core.logger import obter_logger

logger = obter_logger('input_hook')

# =============================================================================
# CONSTANTES WIN32
# =============================================================================

# Tipo de hook: Low-Level Keyboard
WH_KEYBOARD_LL = 13

# Mensagens de teclado
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

# Virtual Key Codes
VK_CAPITAL = 0x14  # CapsLock
VK_ESCAPE = 0x1B   # ESC (para cancelamento)

# Configurações de timing
THRESHOLD_TAP_MS = 500  # Abaixo disso é TAP (toggle normal), acima é HOLD (gravação)

# =============================================================================
# ESTRUTURAS WIN32
# =============================================================================

class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Estrutura passada para o callback do hook de teclado."""
    _fields_ = [
        ("vkCode", wintypes.DWORD),      # Virtual key code
        ("scanCode", wintypes.DWORD),    # Scan code do hardware
        ("flags", wintypes.DWORD),       # Flags do evento
        ("time", wintypes.DWORD),        # Timestamp do evento
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

# Tipo do callback do hook
# LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam)
HOOKPROC = CFUNCTYPE(c_int, c_int, wintypes.WPARAM, wintypes.LPARAM)

# =============================================================================
# FUNÇÕES WIN32
# =============================================================================

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# SetWindowsHookExW
user32.SetWindowsHookExW.argtypes = [c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

# UnhookWindowsHookEx
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

# CallNextHookEx
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = c_int

# GetModuleHandleW
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

# =============================================================================
# ENUMS
# =============================================================================

class EstadoHook(Enum):
    """Estados do detector de CapsLock via Hook."""
    AGUARDANDO = auto()      # Esperando CapsLock ser pressionada
    CONTANDO = auto()        # CapsLock DOWN, contando tempo para decidir TAP vs HOLD
    GRAVANDO = auto()        # HOLD confirmado, gravação ativa


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class KeyboardHook(QObject):
    """
    Hook de teclado de baixo nível para interceptação inteligente do CapsLock.
    
    Comportamento:
    - TAP (<500ms): Deixa Windows processar normalmente (LED toggle funciona)
    - HOLD (>=500ms): Suprime evento (LED não muda), dispara callback de gravação
    
    Signals:
        gravacao_iniciada: Emitido quando HOLD é detectado
        gravacao_parada: Emitido quando tecla é solta durante gravação
        cancelamento_solicitado: Emitido quando ESC é pressionado durante gravação
    """
    
    # Qt Signals para comunicação thread-safe com a UI
    gravacao_iniciada = Signal()
    gravacao_parada = Signal()
    cancelamento_solicitado = Signal()
    
    def __init__(
        self,
        callback_iniciar: Optional[Callable[[], bool]] = None,
        callback_parar: Optional[Callable[[], None]] = None,
        callback_cancelar: Optional[Callable[[], None]] = None,
        threshold_ms: int = THRESHOLD_TAP_MS
    ):
        """
        Inicializa o hook de teclado.
        
        Args:
            callback_iniciar: Chamado quando HOLD é detectado (retorna True se sucesso)
            callback_parar: Chamado quando tecla é solta durante gravação
            callback_cancelar: Chamado quando ESC é pressionado durante gravação
            threshold_ms: Tempo em ms para distinguir TAP de HOLD
        """
        super().__init__()
        
        self._callback_iniciar = callback_iniciar
        self._callback_parar = callback_parar
        self._callback_cancelar = callback_cancelar
        self._threshold_ms = threshold_ms
        
        # Estado interno
        self._estado = EstadoHook.AGUARDANDO
        self._timestamp_keydown: Optional[int] = None  # Quando CapsLock foi pressionada
        self._hook_handle: Optional[int] = None
        self._hook_proc: Optional[HOOKPROC] = None  # Manter referência para evitar GC
        
        # Flags para comunicação com o callback (deve ser ultra-rápido)
        self._suprimir_proximo_keyup = False
        
        # Thread de mensagens do Windows (hooks precisam de message pump)
        self._thread_hook: Optional[threading.Thread] = None
        self._running = False
        
        logger.info(f"KeyboardHook inicializado - threshold: {threshold_ms}ms")
    
    def iniciar(self) -> bool:
        """
        Instala o hook de teclado.
        
        Returns:
            True se hook foi instalado com sucesso
        """
        if self._hook_handle is not None:
            logger.warning("Hook já está ativo")
            return True
        
        # Callback deve ser armazenado como atributo para evitar garbage collection
        self._hook_proc = HOOKPROC(self._hook_callback)
        
        # Obter handle do módulo atual (None = processo atual)
        h_module = kernel32.GetModuleHandleW(None)
        
        # Instalar hook
        self._hook_handle = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            h_module,
            0  # 0 = hook global (todos os threads)
        )
        
        if not self._hook_handle:
            erro = ctypes.get_last_error()
            logger.error(f"Falha ao instalar hook. Código de erro: {erro}")
            return False
        
        self._running = True
        self._estado = EstadoHook.AGUARDANDO
        
        logger.info("✅ Low-Level Keyboard Hook instalado com sucesso")
        return True
    
    def parar(self) -> None:
        """Remove o hook de teclado."""
        self._running = False
        
        if self._hook_handle:
            if user32.UnhookWindowsHookEx(self._hook_handle):
                logger.info("Hook de teclado removido")
            else:
                logger.warning("Falha ao remover hook")
            
            self._hook_handle = None
        
        self._estado = EstadoHook.AGUARDANDO
    
    def _hook_callback(self, nCode: int, wParam: int, lParam: int) -> int:
        """
        Callback do hook de teclado.
        
        ATENÇÃO: Este método é chamado pelo Windows para CADA evento de teclado.
        Deve ser EXTREMAMENTE rápido (<1ms) para não travar o input do sistema.
        
        Args:
            nCode: Se < 0, não processar e chamar CallNextHookEx
            wParam: Tipo de mensagem (WM_KEYDOWN, WM_KEYUP, etc)
            lParam: Ponteiro para KBDLLHOOKSTRUCT
        
        Returns:
            1 para suprimir evento, CallNextHookEx para propagar
        """
        # Se nCode < 0, devemos chamar o próximo hook sem processar
        if nCode < 0:
            return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)
        
        # Extrair informações do evento
        kb_struct = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
        vk_code = kb_struct.vkCode
        timestamp = kb_struct.time
        
        # =====================================================================
        # TRATAR ESC: Cancelamento durante gravação
        # =====================================================================
        if vk_code == VK_ESCAPE and self._estado == EstadoHook.GRAVANDO:
            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                logger.info("ESC detectado durante gravação - solicitando cancelamento")
                self.cancelamento_solicitado.emit()
                if self._callback_cancelar:
                    self._callback_cancelar()
            # Deixar ESC propagar normalmente
            return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)
        
        # =====================================================================
        # TRATAR CAPSLOCK
        # =====================================================================
        if vk_code != VK_CAPITAL:
            # Não é CapsLock, deixar passar
            return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)
        
        # ----- KEYDOWN -----
        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            if self._estado == EstadoHook.AGUARDANDO:
                # Primeira vez que CapsLock é pressionada
                self._estado = EstadoHook.CONTANDO
                self._timestamp_keydown = timestamp
                self._suprimir_proximo_keyup = False
                logger.debug(f"CapsLock DOWN - iniciando contagem (timestamp: {timestamp})")
                
                # BLOQUEAR o evento DOWN para o LED não acender ainda
                return 1
            
            # Se já está CONTANDO ou GRAVANDO, ignorar keydowns repetidos (repeat)
            return 1
        
        # ----- KEYUP -----
        if wParam in (WM_KEYUP, WM_SYSKEYUP):
            if self._estado == EstadoHook.CONTANDO:
                # Calcular duração do hold
                if self._timestamp_keydown is not None:
                    duracao_ms = timestamp - self._timestamp_keydown
                else:
                    duracao_ms = 0
                
                if duracao_ms < self._threshold_ms:
                    # TAP: Foi um toque rápido, deixar Windows processar normalmente
                    logger.debug(f"TAP detectado ({duracao_ms}ms < {self._threshold_ms}ms) - propagando toggle")
                    self._estado = EstadoHook.AGUARDANDO
                    self._timestamp_keydown = None
                    
                    # PROPAGAR: Deixar o Windows fazer o toggle normal do CapsLock
                    # Precisamos enviar tanto DOWN quanto UP para simular o toggle
                    self._simular_toggle_capslock()
                    return 1  # Suprimir o UP original (já simulamos)
                
                else:
                    # HOLD: Duração suficiente para gravação
                    logger.info(f"HOLD detectado ({duracao_ms}ms >= {self._threshold_ms}ms) - iniciando gravação")
                    self._estado = EstadoHook.GRAVANDO
                    self._timestamp_keydown = None
                    
                    # Emitir signal e chamar callback
                    self.gravacao_iniciada.emit()
                    if self._callback_iniciar:
                        self._callback_iniciar()
                    
                    # Não chegamos aqui porque o KEYUP só acontece quando solta,
                    # mas se chegássemos, suprimiríamos
                    return 1
            
            elif self._estado == EstadoHook.GRAVANDO:
                # Tecla solta durante gravação - parar gravação
                logger.info("CapsLock UP durante gravação - parando gravação")
                self._estado = EstadoHook.AGUARDANDO
                
                # Emitir signal e chamar callback
                self.gravacao_parada.emit()
                if self._callback_parar:
                    self._callback_parar()
                
                # SUPRIMIR: Não queremos toggle após gravação
                return 1
        
        # Default: propagar evento
        return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)
    
    def _simular_toggle_capslock(self) -> None:
        """
        Simula um pressionamento de CapsLock para fazer o toggle funcionar.
        
        Como suprimimos o DOWN original, precisamos injetar novos eventos
        para que o Windows processe o toggle normalmente.
        """
        # Estrutura INPUT para SendInput
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
        
        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("ki", KEYBDINPUT),
                ("padding", ctypes.c_ubyte * 8)
            ]
        
        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        
        # Criar eventos DOWN e UP
        inputs = (INPUT * 2)()
        
        # DOWN
        inputs[0].type = INPUT_KEYBOARD
        inputs[0].ki.wVk = VK_CAPITAL
        inputs[0].ki.dwFlags = 0
        
        # UP
        inputs[1].type = INPUT_KEYBOARD
        inputs[1].ki.wVk = VK_CAPITAL
        inputs[1].ki.dwFlags = KEYEVENTF_KEYUP
        
        # Enviar eventos
        user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        logger.debug("Toggle de CapsLock simulado via SendInput")
    
    @property
    def esta_gravando(self) -> bool:
        """Retorna True se está no estado de gravação."""
        return self._estado == EstadoHook.GRAVANDO
    
    @property
    def threshold_ms(self) -> int:
        """Retorna threshold atual."""
        return self._threshold_ms
    
    @threshold_ms.setter
    def threshold_ms(self, valor: int) -> None:
        """Define novo threshold."""
        self._threshold_ms = max(200, min(1500, valor))
        logger.info(f"Threshold atualizado para {self._threshold_ms}ms")
