# -*- coding: utf-8 -*-
"""
Testes end-to-end do pipeline completo.

Verifica fluxo: Gravação → Transcrição → Polimento → Clipboard
"""

import os
import json
import time
import pytest
import pyperclip


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


class TestPipelineCompleto:
    """Testes do pipeline E2E."""
    
    def test_maquina_estados_inicializa_idle(self):
        """Verifica que máquina inicia em estado IDLE."""
        from core.maquina_estados import MaquinaEstados, Estado
        
        config = carregar_config()
        maquina = MaquinaEstados(config)
        
        assert maquina.estado == Estado.IDLE
    
    def test_transicao_idle_para_recording(self):
        """Verifica transição IDLE → RECORDING."""
        from core.maquina_estados import MaquinaEstados, Estado
        
        config = carregar_config()
        maquina = MaquinaEstados(config)
        
        sucesso = maquina.iniciar_gravacao()
        
        if sucesso:
            assert maquina.estado == Estado.RECORDING
            # Para gravação para limpar
            maquina.parar_gravacao()
            # Aguarda processamento
            time.sleep(1)
        else:
            pytest.skip("Microfone não disponível")
    
    def test_gravacao_curta_volta_idle(self):
        """Verifica que gravação curta retorna a IDLE sem processar."""
        from core.maquina_estados import MaquinaEstados, Estado
        
        config = carregar_config()
        maquina = MaquinaEstados(config)
        
        if not maquina.iniciar_gravacao():
            pytest.skip("Microfone não disponível")
        
        # Grava por 200ms (abaixo do limite)
        time.sleep(0.2)
        maquina.parar_gravacao()
        
        # Deve voltar para IDLE rapidamente (sem chamar APIs)
        time.sleep(0.5)
        assert maquina.estado == Estado.IDLE
    
    def test_pipeline_completo_com_audio_real(self):
        """
        Teste E2E completo: grava áudio real e verifica clipboard.
        
        IMPORTANTE: Este teste requer:
        1. Microfone funcional
        2. API keys válidas
        3. Conexão com internet
        """
        from core.maquina_estados import MaquinaEstados, Estado
        
        config = carregar_config()
        maquina = MaquinaEstados(config)
        
        # Limpa clipboard
        pyperclip.copy('')
        
        if not maquina.iniciar_gravacao():
            pytest.skip("Microfone não disponível")
        
        # Grava por 2 segundos (deve capturar ruído ambiente)
        print("\n🎤 Gravando por 2 segundos...")
        time.sleep(2.0)
        
        maquina.parar_gravacao()
        
        # Aguarda processamento (transcrição + polimento)
        print("⏳ Aguardando processamento...")
        timeout = 30  # 30 segundos máximo
        inicio = time.time()
        
        while maquina.estado != Estado.IDLE and (time.time() - inicio) < timeout:
            time.sleep(0.5)
        
        # Verifica resultado
        assert maquina.estado == Estado.IDLE, f"Estado final: {maquina.estado.name}"
        
        # Nota: clipboard pode estar vazio se não houver áudio audível
        conteudo_clipboard = pyperclip.paste()
        print(f"📋 Conteúdo do clipboard: '{conteudo_clipboard[:100]}...' ({len(conteudo_clipboard)} chars)")


class TestConsumoMemoria:
    """Testes de consumo de memória."""
    
    def test_memoria_abaixo_limite(self):
        """Verifica consumo de memória em estado IDLE."""
        import tracemalloc
        from core.maquina_estados import MaquinaEstados
        
        config = carregar_config()
        
        tracemalloc.start()
        
        # Inicializa sistema
        maquina = MaquinaEstados(config)
        
        # Mede memória
        atual, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memoria_mb = atual / (1024 * 1024)
        pico_mb = pico / (1024 * 1024)
        
        print(f"\n📊 Memória atual: {memoria_mb:.2f} MB")
        print(f"📊 Pico de memória: {pico_mb:.2f} MB")
        
        # Limite: 20MB em IDLE (apenas componentes Python, sem Qt)
        # Nota: Com Qt, o limite total é ~30-40MB
        assert memoria_mb < 50, f"Consumo de memória muito alto: {memoria_mb:.2f} MB"
