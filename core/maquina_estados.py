# -*- coding: utf-8 -*-
"""
Máquina de Estados do VoiceFlow Transcriber.

Gerencia transições entre estados: IDLE → RECORDING → TRANSCRIBING → POLISHING → COMPLETE.
Cada transição é logada para diagnóstico.
"""

from enum import Enum, auto
from typing import Optional, Callable
import threading

from core.logger import obter_logger
from core.captura_audio import CapturadorAudio, limpar_arquivo_temporario
from core.cliente_api import ClienteAPI
from core.gerenciador_clipboard import (
    copiar_para_clipboard,
    notificar_sucesso,
    notificar_erro
)
from core.historico import GerenciadorHistorico
from core.detector_foco import obter_janela_ativa, simular_ctrl_v, simular_enter
import time
import os
import shutil
import json
from datetime import datetime

DIR_FALHAS = os.path.join("data", "failed_audios")

logger = obter_logger('maquina_estados')


class Estado(Enum):
    """Estados possíveis da máquina de estados."""
    IDLE = auto()           # Aguardando hotkey
    RECORDING = auto()      # Capturando áudio
    TRANSCRIBING = auto()   # Enviando para Groq
    POLISHING = auto()      # Enviando para Gemini
    COMPLETE = auto()       # Processamento concluído
    ERROR = auto()          # Erro no processamento


class MaquinaEstados:
    """
    Máquina de estados finitos para controle do fluxo de transcrição.
    
    Transições:
        IDLE → RECORDING (hotkey pressionado)
        RECORDING → TRANSCRIBING (hotkey solto)
        TRANSCRIBING → POLISHING (transcrição OK)
        TRANSCRIBING → ERROR (falha API)
        POLISHING → COMPLETE (texto polido ou fallback)
        COMPLETE → IDLE (após clipboard + notificação)
        ERROR → IDLE (após notificação de erro)
    """
    
    def __init__(self, config: dict):
        """
        Inicializa máquina de estados.
        
        Args:
            config: Configurações da aplicação
        """
        self._estado: Estado = Estado.IDLE
        self._config = config
        
        # Componentes
        self._capturador = CapturadorAudio()
        self._cliente_api = ClienteAPI(config)
        self._cliente_api = ClienteAPI(config)
        self._historico = GerenciadorHistorico()
        
        # Controle de foco (Fase 3)
        self._janela_inicio: int = 0
        
        # Dados da transcrição atual
        self._caminho_audio: Optional[str] = None
        self._duracao_audio: float = 0.0
        self._texto_bruto: Optional[str] = None
        self._texto_polido: Optional[str] = None
        
        # Callbacks para operações que devem rodar na thread principal
        self._callback_estado: Optional[Callable[[Estado], None]] = None
        self._callback_clipboard: Optional[Callable[[str], None]] = None
        self._callback_nova_transcricao: Optional[Callable[[], None]] = None
        
        # Flag de cancelamento (Fase 4)
        self._cancelado = False
        self._id_operacao = 0  # Identificador de geração para thread safety
        
        logger.info("Máquina de estados inicializada - Estado: IDLE")
    
    @property
    def estado(self) -> Estado:
        """Retorna estado atual."""
        return self._estado
    
    @property
    def esta_gravando(self) -> bool:
        """Retorna True se está gravando áudio."""
        return self._estado == Estado.RECORDING
    
    @property
    def duracao_gravacao(self) -> float:
        """Retorna duração da gravação atual em segundos."""
        return self._capturador.duracao_atual
    
    def registrar_callback_estado(self, callback: Callable[[Estado], None]) -> None:
        """
        Registra callback para notificação de mudança de estado.
        
        Args:
            callback: Função chamada com novo estado
        """
        self._callback_estado = callback
    
    def registrar_callback_clipboard(self, callback: Callable[[str], None]) -> None:
        """
        Registra callback para copiar texto para clipboard na thread principal.
        
        IMPORTANTE: Este callback DEVE ser executado na thread principal do Qt
        para evitar erros COM no Windows.
        
        Args:
            callback: Função que recebe texto e copia para clipboard
        """
        self._callback_clipboard = callback
        logger.info("Callback de clipboard registrado")
    
    def registrar_callback_nova_transcricao(self, callback: Callable[[], None]) -> None:
        """
        Registra callback notificar quando uma nova transcrição é salva.
        Útil para atualizar janelas de histórico automaticamente.
        """
        self._callback_nova_transcricao = callback
    
    def _transitar(self, novo_estado: Estado) -> None:
        """
        Executa transição de estado com logging.
        
        Args:
            novo_estado: Estado destino
        """
        estado_anterior = self._estado
        self._estado = novo_estado
        logger.info(f"Transição: {estado_anterior.name} → {novo_estado.name}")
        
        if self._callback_estado:
            try:
                self._callback_estado(novo_estado)
            except Exception as e:
                logger.warning(f"Erro no callback de estado: {e}")
    
    def iniciar_gravacao(self) -> bool:
        """
        Inicia gravação de áudio (IDLE → RECORDING).
        
        Returns:
            True se transição foi bem-sucedida
        """
        if self._estado != Estado.IDLE:
            logger.warning(f"Tentativa de iniciar gravação em estado inválido: {self._estado.name}")
            return False
        
        # Limpa dados anteriores e incrementa ID da operação
        self._id_operacao += 1
        self._cancelado = False

        self._caminho_audio = None
        self._duracao_audio = 0.0
        self._texto_bruto = None
        self._texto_bruto = None
        self._texto_polido = None
        
        # Captura janela ativa para colagem inteligente
        self._janela_inicio = obter_janela_ativa()
        logger.debug(f"Janela ativa no início: {self._janela_inicio}")
        
        # Tenta iniciar captura
        if self._capturador.iniciar_gravacao():
            self._transitar(Estado.RECORDING)
            return True
        else:
            notificar_erro("Microfone não disponível")
            return False
    
    def cancelar(self) -> None:
        """
        Cancela a operação atual.
        
        Se estiver gravando: para gravação, descarta áudio e limpa arquivo.
        Se estiver processando: seta flag e DEIXA A THREAD limpar o arquivo.
        """
        if self._estado == Estado.IDLE:
            logger.debug("Cancelamento ignorado - já em IDLE")
            return
        
        logger.info(f"🚫 Cancelamento solicitado em estado: {self._estado.name}")
        
        # Seta flag para abortar processamento (thread verifica isso)
        self._cancelado = True
        
        # Se estiver gravando, para a gravação e limpa IMEDIATAMENTE
        if self._estado == Estado.RECORDING:
            caminho_temp, _ = self._capturador.parar_gravacao()
            if caminho_temp:
                limpar_arquivo_temporario(caminho_temp)
            
            # Limpa referência se existir
            if self._caminho_audio:
                limpar_arquivo_temporario(self._caminho_audio)
                self._caminho_audio = None

            self._transitar(Estado.IDLE)
            logger.info("✅ Gravação cancelada e descartada")
        
        elif self._estado in (Estado.TRANSCRIBING, Estado.POLISHING):
            # Se estiver processando, NÃO limpamos o arquivo aqui para não quebrar a thread.
            # A thread vai ler a flag self._cancelado, abortar e limpar o arquivo.

            # Transitamos para IDLE para feedback visual imediato na UI
            self._transitar(Estado.IDLE)
            logger.info("✅ Processamento cancelado (aguardando thread finalizar limpeza)")
    
    def parar_gravacao(self) -> None:
        """
        Para gravação e inicia processamento (RECORDING → TRANSCRIBING).
        Processamento acontece em thread separada para não bloquear UI.
        """
        if self._estado != Estado.RECORDING:
            logger.warning(f"Tentativa de parar gravação em estado inválido: {self._estado.name}")
            return
        
        # Para captura e salva arquivo
        caminho, duracao = self._capturador.parar_gravacao()
        
        if caminho is None:
            # Gravação muito curta - volta para IDLE silenciosamente
            self._transitar(Estado.IDLE)
            return
        
        self._caminho_audio = caminho
        self._duracao_audio = duracao
        
        # Inicia processamento em thread separada, passando o caminho explicitamente
        self._transitar(Estado.TRANSCRIBING)

        # Captura ID atual para passar à thread
        op_id = self._id_operacao
        thread = threading.Thread(target=self._processar_audio, args=(caminho, op_id), daemon=True)
        thread.start()
    
    def _processar_audio(self, caminho_audio: str, id_operacao: int) -> None:
        """
        Processa áudio: transcrição + polimento.
        Executado em thread separada.

        Args:
            caminho_audio: Caminho do arquivo WAV a processar
            id_operacao: ID da operação para verificar obsolescência (zombie check)
        """
        # Verifica se thread é obsoleta (usuário iniciou nova operação)
        if self._id_operacao != id_operacao:
            logger.info(f"Thread obsoleta (ID {id_operacao} != {self._id_operacao}) - abortando silenciosamente")
            limpar_arquivo_temporario(caminho_audio)
            return

        try:
            # Verifica cancelamento ANTES de chamar API (economia de tokens)
            if self._cancelado:
                logger.info("🚫 Processamento abortado por cancelamento (inicio)")
                self._cancelado = False  # Reset flag
                self._finalizar(caminho_audio, id_operacao)
                return
            
            # TRANSCRIBING: Envia para Groq
            texto, erro = self._cliente_api.transcrever(caminho_audio)
            
            # Verifica cancelamento após transcrição (antes de polimento)
            if self._cancelado or self._id_operacao != id_operacao:
                logger.info("🚫 Transcrição concluída mas abortado por cancelamento ou obsolescência")
                if self._cancelado: self._cancelado = False
                self._finalizar(caminho_audio, id_operacao)
                return
            
            if texto is None:
                # Se foi cancelado durante a transcrição
                if self._cancelado or self._id_operacao != id_operacao:
                    logger.info("🚫 Erro na transcrição ignorado (cancelado/obsoleto)")
                    if self._cancelado: self._cancelado = False
                    self._finalizar(caminho_audio, id_operacao)
                    return

                logger.error(f"Transcrição falhou: {erro}")
                # Só salva falha se NÃO foi cancelado
                self._salvar_audio_falha(erro or "Falha na transcrição", caminho_audio)

                # Só muda estado se ID bater
                if self._id_operacao == id_operacao:
                    self._transitar(Estado.ERROR)
                    notificar_erro(erro or "Falha na transcrição")

                self._finalizar(caminho_audio, id_operacao)
                return
            
            self._texto_bruto = texto
            
            # POLISHING: Envia para Gemini
            if self._id_operacao == id_operacao:
                self._transitar(Estado.POLISHING)

            texto_polido, foi_polido = self._cliente_api.polir(texto)
            self._texto_polido = texto_polido
            
            # Verifica cancelamento após polimento
            if self._cancelado or self._id_operacao != id_operacao:
                logger.info("🚫 Polimento concluído mas abortado antes de salvar/colar")
                if self._cancelado: self._cancelado = False
                self._finalizar(caminho_audio, id_operacao)
                return

            if not foi_polido:
                logger.warning("Usando texto bruto (polimento falhou)")
            
            # PERSISTÊNCIA-PRIMEIRO (Write-Ahead Logging)
            # Salva no histórico ANTES de qualquer operação de clipboard
            # Se SQLite falhar, tenta salvar em arquivo de emergência
            persistencia_sucesso = False
            try:
                registro_id = self._historico.salvar(
                    texto_bruto=self._texto_bruto,
                    texto_polido=self._texto_polido,
                    duracao_segundos=self._duracao_audio
                )
                logger.info(f"✅ Transcrição persistida no histórico: ID {registro_id}")
                persistencia_sucesso = True
                
                # Notifica que há nova transcrição (para refresh do histórico)
                if self._callback_nova_transcricao:
                    try:
                        self._callback_nova_transcricao()
                    except Exception as e:
                        logger.error(f"Erro no callback de nova transcrição: {e}")
                        
            except Exception as e:
                logger.error(f"CRÍTICO: Falha ao salvar no histórico SQLite: {e}")
                # FAIL-SAFE: Tentar salvar em arquivo de emergência no Desktop
                try:
                    import os
                    from datetime import datetime
                    desktop = os.path.join(os.environ.get('USERPROFILE', '~'), 'Desktop')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    arquivo_emergencia = os.path.join(desktop, f"VoiceFlow_EMERGENCIA_{timestamp}.txt")
                    with open(arquivo_emergencia, 'w', encoding='utf-8') as f:
                        f.write(f"=== TRANSCRIÇÃO DE EMERGÊNCIA ===\n")
                        f.write(f"Data/Hora: {datetime.now().isoformat()}\n")
                        f.write(f"Duração: {self._duracao_audio:.1f}s\n\n")
                        f.write(f"--- TEXTO BRUTO ---\n{self._texto_bruto}\n\n")
                        f.write(f"--- TEXTO POLIDO ---\n{self._texto_polido}\n")
                    logger.warning(f"⚠️ Transcrição salva em arquivo de emergência: {arquivo_emergencia}")
                    notificar_erro(f"Erro no banco de dados! Texto salvo em: {arquivo_emergencia}")
                    persistencia_sucesso = True  # Conseguimos salvar de alguma forma
                except Exception as e2:
                    logger.critical(f"FALHA TOTAL: Não conseguiu salvar nem no SQLite nem em arquivo: {e2}")
                    notificar_erro("CRÍTICO: Impossível salvar transcrição!")
                    # Ainda assim, tentar entregar ao clipboard como última chance
            
            # COMPLETE: Copia para clipboard via callback bloqueante
            if self._id_operacao == id_operacao:
                self._transitar(Estado.COMPLETE)
            
            if self._callback_clipboard and self._id_operacao == id_operacao:
                # Callback é bloqueante - aguarda até clipboard ser atualizado
                logger.info(f"Copiando {len(self._texto_polido)} caracteres para clipboard")
                sucesso = self._callback_clipboard(self._texto_polido)
                
                if sucesso:
                    logger.info("Clipboard atualizado com sucesso")
                else:
                    logger.warning("Falha ao atualizar clipboard")
            else:
                # Fallback: tenta diretamente (pode falhar no Windows)
                logger.warning("Callback de clipboard não registrado - tentando diretamente")
                copiar_para_clipboard(self._texto_polido)
            
            # COLAGEM INTELIGENTE (Fase 3)
            # Verifica se usuário manteve foco na mesma janela
            janela_atual = obter_janela_ativa()
            
            if janela_atual == self._janela_inicio and self._janela_inicio != 0:
                logger.info("Foco preservado - Colando automaticamente")
                if simular_ctrl_v():
                    notificar_sucesso("Transcrição colada com sucesso!")
                    
                    # AUTO-ENTER: Se habilitado, aguarda 800ms e pressiona Enter
                    if self._config.get('auto_enter', False):
                        time.sleep(0.8)  # 800ms delay
                        if simular_enter():
                            logger.info("Auto-Enter executado com sucesso")
                        else:
                            logger.warning("Falha ao executar Auto-Enter")
                else:
                    notificar_sucesso("Transcrição no clipboard (falha ao colar)")
            else:
                logger.info(f"Foco mudou ou inválido ({self._janela_inicio} -> {janela_atual}) - Mantendo no clipboard")
                notificar_sucesso("Transcrição pronta no clipboard (foco alterado)")
            

            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}", exc_info=True)
            if not self._cancelado and self._id_operacao == id_operacao:
                self._salvar_audio_falha(f"Erro de processamento: {str(e)}", caminho_audio)
                self._transitar(Estado.ERROR)
                notificar_erro("Erro inesperado no processamento")
            else:
                logger.info("Erro suprimido (cancelado ou obsoleto)")
        
        finally:
            self._finalizar(caminho_audio, id_operacao)

    def _salvar_audio_falha(self, erro_msg: str, caminho_origem: Optional[str] = None) -> None:
        """Salva áudio falho para retry posterior."""
        caminho = caminho_origem or self._caminho_audio
        if not caminho or not os.path.exists(caminho):
            return

        try:
            if not os.path.exists(DIR_FALHAS):
                os.makedirs(DIR_FALHAS)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_base = f"falha_{timestamp}"
            caminho_destino = os.path.join(DIR_FALHAS, f"{nome_base}.wav")
            caminho_json = os.path.join(DIR_FALHAS, f"{nome_base}.json")

            # Copia arquivo (preserva original para _finalizar limpar se for temp)
            shutil.copy2(caminho, caminho_destino)

            # Salva metadados
            dados = {
                "timestamp": datetime.now().isoformat(),
                "erro": str(erro_msg),
                "arquivo_audio": caminho_destino,
                "duracao": self._duracao_audio
            }
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
                
            logger.info(f"💾 Áudio falho salvo em: {caminho_destino}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar áudio falho: {e}")

    def reprocessar_arquivo(self, caminho_wav: str) -> None:
        """
        Inicia processamento de um arquivo existente (Retry).
        
        Args:
            caminho_wav: Caminho absoluto do arquivo WAV
        """
        if self._estado != Estado.IDLE:
             logger.warning("Falha ao reprocessar: Máquina não está em IDLE")
             notificar_erro("Aguarde o processamento atual terminar")
             return
             
        if not os.path.exists(caminho_wav):
            logger.error(f"Arquivo não encontrado para reprocessamento: {caminho_wav}")
            notificar_erro("Arquivo de áudio não encontrado")
            return
            
        logger.info(f"♻️ Iniciando reprocessamento de: {caminho_wav}")
        
        # Incrementa ID e reseta cancelamento
        self._id_operacao += 1
        self._cancelado = False

        # Define estado
        self._caminho_audio = caminho_wav
        self._duracao_audio = 0.0 
        
        # Inicia processamento
        self._transitar(Estado.TRANSCRIBING)

        op_id = self._id_operacao
        thread = threading.Thread(target=self._processar_audio, args=(caminho_wav, op_id), daemon=True)
        thread.start()
    
    def _finalizar(self, caminho_audio: Optional[str], id_operacao: int) -> None:
        """
        Limpa recursos e retorna para IDLE.
        Verifica id_operacao para evitar race condition com novas operações.
        """
        # Remove arquivo temporário se passado como argumento (usado pela thread)
        if caminho_audio:
             limpar_arquivo_temporario(caminho_audio)

        # Só atualiza estado global se ID bater
        if self._id_operacao == id_operacao:
            # Se self._caminho_audio ainda apontar para o mesmo arquivo, limpa a referência
            if self._caminho_audio and caminho_audio and self._caminho_audio == caminho_audio:
                self._caminho_audio = None

            # Limpa arquivo temporário se sobrar em self._caminho_audio (fallback)
            if self._caminho_audio:
                limpar_arquivo_temporario(self._caminho_audio)
                self._caminho_audio = None

            # Retorna para IDLE (se já não estiver em IDLE devido a cancelamento)
            if self._estado != Estado.IDLE:
                self._transitar(Estado.IDLE)
        else:
            logger.info(f"Finalização ignorada para ID {id_operacao} (Atual: {self._id_operacao})")
