# -*- coding: utf-8 -*-
"""
Testes de integração com API Groq Whisper.

Requer API key válida em config.json para executar testes reais.
"""

import os
import json
import pytest

# Caminho do config
CAMINHO_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    'config.json'
)


def carregar_config():
    """Carrega configurações para testes."""
    if not os.path.exists(CAMINHO_CONFIG):
        pytest.skip("config.json não encontrado")
    
    with open(CAMINHO_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestClienteAPIGroq:
    """Testes para integração com Groq Whisper."""
    
    def test_transcrever_audio_valido(self):
        """Testa transcrição de áudio de amostra."""
        from core.cliente_api import ClienteAPI
        
        config = carregar_config()
        cliente = ClienteAPI(config)
        
        # Verifica se existe arquivo de teste
        caminho_teste = os.path.join(
            os.path.dirname(__file__), 
            'samples', 
            'teste_audio.wav'
        )
        
        if not os.path.exists(caminho_teste):
            pytest.skip("Arquivo de teste não encontrado: samples/teste_audio.wav")
        
        texto, erro = cliente.transcrever(caminho_teste)
        
        assert erro is None, f"Erro na transcrição: {erro}"
        assert texto is not None, "Texto não retornado"
        assert len(texto) > 0, "Texto vazio"
    
    def test_erro_arquivo_inexistente(self):
        """Testa comportamento com arquivo inexistente."""
        from core.cliente_api import ClienteAPI
        
        config = carregar_config()
        cliente = ClienteAPI(config)
        
        texto, erro = cliente.transcrever('/arquivo/inexistente.wav')
        
        assert texto is None
        assert erro is not None


class TestClienteAPIGemini:
    """Testes para integração com Google Gemini."""
    
    def test_polir_texto_simples(self):
        """Testa polimento de texto simples."""
        from core.cliente_api import ClienteAPI
        
        config = carregar_config()
        cliente = ClienteAPI(config)
        
        texto_bruto = "então tipo assim eu queria falar sobre sobre programação né"
        
        texto_polido, foi_polido = cliente.polir(texto_bruto)
        
        assert texto_polido is not None
        assert len(texto_polido) > 0
        # Aceita tanto polimento bem-sucedido quanto fallback
        assert isinstance(foi_polido, bool)
    
    def test_polir_mantem_conteudo(self):
        """Verifica que polimento mantém conteúdo original."""
        from core.cliente_api import ClienteAPI
        
        config = carregar_config()
        cliente = ClienteAPI(config)
        
        texto_bruto = "Python é uma linguagem de programação muito versátil."
        
        texto_polido, _ = cliente.polir(texto_bruto)
        
        # Verifica que palavras-chave estão presentes
        assert "Python" in texto_polido or "python" in texto_polido.lower()
        assert "programação" in texto_polido.lower()
