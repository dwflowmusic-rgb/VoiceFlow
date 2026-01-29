# -*- coding: utf-8 -*-
"""
Módulo de Logging Estruturado do VoiceFlow Transcriber.

Implementa logging com RotatingFileHandler para diagnóstico de problemas.
Formato: [timestamp] [LEVEL] [module] mensagem
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Diretório de logs
DIRETORIO_LOGS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')

# Formato do log
FORMATO_LOG = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
FORMATO_DATA = '%Y-%m-%d %H:%M:%S'


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """
    Configura sistema de logging estruturado com rotação de arquivos.
    
    Args:
        nivel: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger configurado para a aplicação
    """
    # Cria diretório de logs se não existir
    os.makedirs(DIRETORIO_LOGS, exist_ok=True)
    
    # Caminho do arquivo de log
    caminho_log = os.path.join(DIRETORIO_LOGS, 'voiceflow.log')
    
    # Configura handler com rotação (5MB máx, 3 backups)
    handler_arquivo = RotatingFileHandler(
        caminho_log,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    handler_arquivo.setFormatter(logging.Formatter(FORMATO_LOG, FORMATO_DATA))
    
    # Handler para console (desenvolvimento)
    handler_console = logging.StreamHandler()
    handler_console.setFormatter(logging.Formatter(FORMATO_LOG, FORMATO_DATA))
    
    # Configura logger raiz
    logger = logging.getLogger('voiceflow')
    logger.setLevel(nivel)
    logger.addHandler(handler_arquivo)
    logger.addHandler(handler_console)
    
    # Evita duplicação de handlers
    logger.propagate = False
    
    logger.info(f"Sistema de logging iniciado - Arquivo: {caminho_log}")
    
    return logger


def obter_logger(nome_modulo: str) -> logging.Logger:
    """
    Obtém logger filho para módulo específico.
    
    Args:
        nome_modulo: Nome do módulo (ex: 'audio_capture', 'api_client')
        
    Returns:
        Logger configurado para o módulo
    """
    return logging.getLogger(f'voiceflow.{nome_modulo}')
