# -*- coding: utf-8 -*-
"""
Widget de Status Flutuante (OSD) do VoiceFlow - Versão Minimalista.

Layout vertical compacto:
┌─────────┐
│   ●     │  ← Esfera colorida (vermelho/amarelo/verde)
│  00:00  │  ← Cronômetro
└─────────┘

Cores:
- Vermelho: Gravando
- Amarelo: Processando
- Verde: Pronto (some após 2s)

Autor: VoiceFlow Team
Data: 2026-01-03
"""

from typing import Optional
from enum import Enum, auto

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen

from core.logger import obter_logger

logger = obter_logger('status_widget')


class StatusType(Enum):
    """Tipos de status exibíveis no widget."""
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()
    SUCCESS = auto()
    CANCELLED = auto()
    ERROR = auto()


class StatusWidget(QWidget):
    """
    Widget minimalista flutuante para exibição de status.
    
    Exibe apenas uma esfera colorida + cronômetro.
    """
    
    # Cores para cada estado (esfera)
    CORES = {
        StatusType.IDLE: QColor(100, 100, 100),      # Cinza
        StatusType.RECORDING: QColor(255, 60, 60),   # Vermelho
        StatusType.PROCESSING: QColor(255, 200, 0),  # Amarelo
        StatusType.SUCCESS: QColor(60, 255, 60),     # Verde
        StatusType.CANCELLED: QColor(255, 140, 0),   # Laranja
        StatusType.ERROR: QColor(255, 0, 0),         # Vermelho forte
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._status_atual = StatusType.IDLE
        self._tempo_gravacao_ms = 0
        self._timer_gravacao: Optional[QTimer] = None
        self._timer_auto_hide: Optional[QTimer] = None
        
        # Configuração da janela
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Tamanho fixo compacto
        self.setFixedSize(60, 70)
        
        # Layout
        self._setup_ui()
        
        # Timer para cronômetro
        self._timer_gravacao = QTimer(self)
        self._timer_gravacao.timeout.connect(self._atualizar_cronometro)
        
        # Timer para auto-hide
        self._timer_auto_hide = QTimer(self)
        self._timer_auto_hide.setSingleShot(True)
        self._timer_auto_hide.timeout.connect(self._esconder)
        
        # Posição inicial (canto inferior direito)
        self._mover_para_canto()
        
        # Arrastar
        self._arrasto_pos: Optional[QPoint] = None
        
        logger.info("StatusWidget minimalista inicializado")
    
    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(2)
        
        # Cronômetro
        self._label_tempo = QLabel("00:00")
        self._label_tempo.setFont(QFont("Consolas", 10, QFont.Bold))
        self._label_tempo.setStyleSheet("color: white;")
        self._label_tempo.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(self._label_tempo)
    
    def _mover_para_canto(self) -> None:
        """Move widget para canto inferior direito."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.width() - 5
            y = geo.bottom() - self.height() - 5
            self.move(x, y)
            logger.debug(f"Widget posicionado em ({x}, {y})")
    
    def paintEvent(self, event) -> None:
        """Desenha o widget com esfera colorida."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fundo arredondado semi-transparente
        painter.setBrush(QBrush(QColor(20, 20, 20, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Esfera colorida no topo
        cor = self.CORES.get(self._status_atual, QColor(100, 100, 100))
        painter.setBrush(QBrush(cor))
        painter.setPen(QPen(cor.darker(120), 2))
        
        # Centro horizontal, topo
        esfera_x = self.width() // 2 - 12
        esfera_y = 10
        painter.drawEllipse(esfera_x, esfera_y, 24, 24)
    
    # =========================================================================
    # CONTROLE DE ESTADOS
    # =========================================================================
    
    @Slot(StatusType)
    def definir_status(self, status: StatusType) -> None:
        """Define o status atual."""
        # Ignora transição para IDLE se ainda estamos mostrando SUCCESS
        # (deixa o timer de auto-hide fazer o trabalho)
        if status == StatusType.IDLE and self._status_atual == StatusType.SUCCESS:
            logger.debug("Ignorando IDLE - ainda mostrando SUCCESS")
            return
        
        self._status_atual = status
        self.update()  # Redesenha esfera
        
        if status == StatusType.IDLE:
            self._timer_gravacao.stop()
            # Não esconde aqui - deixa o timer de SUCCESS fazer
            
        elif status == StatusType.RECORDING:
            self._tempo_gravacao_ms = 0
            self._label_tempo.setText("00:00")
            self._timer_gravacao.start(100)
            self.show()
            self.raise_()
            self._mover_para_canto()  # Garante posição
            
        elif status == StatusType.PROCESSING:
            # Pausa cronômetro, mantém tempo exibido
            self._timer_gravacao.stop()
            self.show()
            
        elif status == StatusType.SUCCESS:
            self._timer_gravacao.stop()
            self._timer_auto_hide.stop()
            self.show()
            self._timer_auto_hide.start(1500)  # Some após 1.5s
            logger.info("Timer auto-hide iniciado")
            
        elif status == StatusType.CANCELLED:
            self._timer_gravacao.stop()
            self._label_tempo.setText("--:--")
            self.show()
            self._timer_auto_hide.start(1000)
            
        elif status == StatusType.ERROR:
            self._timer_gravacao.stop()
            self._label_tempo.setText("ERRO")
            self.show()
            self._timer_auto_hide.start(2000)
        
        logger.debug(f"Status: {status.name}")
    
    def _atualizar_cronometro(self) -> None:
        """Atualiza cronômetro."""
        self._tempo_gravacao_ms += 100
        segundos = self._tempo_gravacao_ms // 1000
        minutos = segundos // 60
        segundos = segundos % 60
        self._label_tempo.setText(f"{minutos:02d}:{segundos:02d}")
    
    def _esconder(self) -> None:
        """Esconde o widget após timeout."""
        logger.info(">>> _esconder() chamado - executando hide()")
        self._status_atual = StatusType.IDLE  # Reset estado interno
        self.hide()
        self.update()
        logger.info(f">>> Widget escondido. isVisible={self.isVisible()}")
    
    # =========================================================================
    # ARRASTAR
    # =========================================================================
    
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._arrasto_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event) -> None:
        if self._arrasto_pos is not None:
            self.move(event.globalPosition().toPoint() - self._arrasto_pos)
    
    def mouseReleaseEvent(self, event) -> None:
        self._arrasto_pos = None
