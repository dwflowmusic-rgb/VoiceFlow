# -*- coding: utf-8 -*-
"""
Janela de Recuperação de Falhas.

Permite visualizar e reprocessar áudios que falharam.
"""

import os
import json
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from core.logger import obter_logger
from core.maquina_estados import MaquinaEstados

DIR_FALHAS = os.path.join("data", "failed_audios")

class JanelaRetry(QDialog):
    def __init__(self, maquina_estados: MaquinaEstados, parent=None):
        super().__init__(parent)
        self._maquina = maquina_estados
        self._logger = obter_logger('janela_retry')
        self._setup_ui()
        self.atualizar_lista()

    def _setup_ui(self):
        self.setWindowTitle("VoiceFlow - Recuperação de Falhas")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self._lista = QListWidget()
        self._lista.itemSelectionChanged.connect(self._on_selecao)
        layout.addWidget(QLabel("Áudios que falharam no processamento:"))
        layout.addWidget(self._lista)
        
        btn_layout = QHBoxLayout()
        
        self._btn_reprocessar = QPushButton("♻️ Reprocessar")
        self._btn_reprocessar.clicked.connect(self._on_reprocessar)
        self._btn_reprocessar.setEnabled(False)
        
        self._btn_reproduzir = QPushButton("▶️ Reproduzir")
        self._btn_reproduzir.clicked.connect(self._on_reproduzir)
        self._btn_reproduzir.setEnabled(False)
        
        self._btn_excluir = QPushButton("🗑️ Excluir")
        self._btn_excluir.clicked.connect(self._on_excluir)
        self._btn_excluir.setStyleSheet("color: #c9302c;")
        self._btn_excluir.setEnabled(False)
        
        self._btn_atualizar = QPushButton("🔄 Atualizar")
        self._btn_atualizar.clicked.connect(self.atualizar_lista)
        
        btn_layout.addWidget(self._btn_reprocessar)
        btn_layout.addWidget(self._btn_reproduzir)
        btn_layout.addWidget(self._btn_excluir)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_atualizar)
        
        layout.addLayout(btn_layout)

    def atualizar_lista(self):
        self._lista.clear()
        if not os.path.exists(DIR_FALHAS):
            return
            
        arquivos = sorted(
            [f for f in os.listdir(DIR_FALHAS) if f.endswith('.json')],
            reverse=True
        )
        
        for arq in arquivos:
            try:
                full_path = os.path.join(DIR_FALHAS, arq)
                with open(full_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                # Formata timestamp para ficar mais legível (opcional)
                ts = dados.get('timestamp', 'N/A')
                erro = dados.get('erro', 'Desconhecido')
                duracao = dados.get('duracao', 0)
                
                item = QListWidgetItem(f"[{ts}] {duracao:.1f}s - {erro}")
                item.setData(Qt.UserRole, full_path) # path to json
                item.setData(Qt.UserRole + 1, dados.get('arquivo_audio')) # path to wav
                self._lista.addItem(item)
            except Exception as e:
                self._logger.error(f"Erro ao ler metadata {arq}: {e}")

    def _on_selecao(self):
        tem_selecao = len(self._lista.selectedItems()) > 0
        self._btn_reprocessar.setEnabled(tem_selecao)
        self._btn_reproduzir.setEnabled(tem_selecao)
        self._btn_excluir.setEnabled(tem_selecao)

    def _on_reprocessar(self):
        item = self._lista.currentItem()
        if not item: return
        
        wav_path = item.data(Qt.UserRole + 1)
        if wav_path and os.path.exists(wav_path):
            self._logger.info(f"Solicitando reprocessamento: {wav_path}")
            self._maquina.reprocessar_arquivo(wav_path)
            self.close()
        else:
            QMessageBox.warning(self, "Erro", "Arquivo de áudio não encontrado.")

    def _on_reproduzir(self):
        item = self._lista.currentItem()
        if not item: return
        
        wav_path = item.data(Qt.UserRole + 1)
        if wav_path and os.path.exists(wav_path):
            os.startfile(wav_path)
        else:
             QMessageBox.warning(self, "Erro", "Arquivo de áudio não encontrado.")

    def _on_excluir(self):
        item = self._lista.currentItem()
        if not item: return
        
        if QMessageBox.question(
            self, 
            "Confirmar Exclusão", 
            "Tem certeza que deseja apagar permanentemente este áudio falho?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            json_path = item.data(Qt.UserRole)
            wav_path = item.data(Qt.UserRole + 1)
            
            try:
                if os.path.exists(json_path): os.remove(json_path)
                if os.path.exists(wav_path): os.remove(wav_path)
                self.atualizar_lista()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir: {e}")
