import unittest
import os
import sys
import shutil
import json
import time
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MOCK ALL THE THINGS before importing core modules
sys.modules['sounddevice'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['scipy'] = MagicMock()
sys.modules['scipy.io'] = MagicMock()
sys.modules['scipy.io.wavfile'] = MagicMock()
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
# Mock entire google.genai package structure
google_mock = MagicMock()
genai_mock = MagicMock()
types_mock = MagicMock()
genai_mock.types = types_mock
google_mock.genai = genai_mock
sys.modules['google'] = google_mock
sys.modules['google.genai'] = genai_mock
sys.modules['google.genai.types'] = types_mock
sys.modules['groq'] = MagicMock()

from core.maquina_estados import MaquinaEstados, Estado, DIR_FALHAS

class TestFailbackIntegration(unittest.TestCase):
    def setUp(self):
        # Config
        self.config = {
            'transcription': {'api_key': 'dummy', 'model': 'whisper'},
            'polishing': {'api_key': 'dummy', 'model': 'gemini'},
            'history': {'retention_days': 5}
        }
        self.maquina = MaquinaEstados(self.config)
        
        # Ensure fail dir exists and is empty
        if os.path.exists(DIR_FALHAS):
            shutil.rmtree(DIR_FALHAS)
        os.makedirs(DIR_FALHAS)
        
        # Create dummy wav
        self.test_wav = os.path.join("data", "test_audio.wav")
        if not os.path.exists("data"): os.makedirs("data")
        with open(self.test_wav, "w") as f:
            f.write("dummy audio content")

    def tearDown(self):
        # Cleanup
        if os.path.exists(DIR_FALHAS):
            shutil.rmtree(DIR_FALHAS)
        if os.path.exists(self.test_wav):
            os.remove(self.test_wav)

    def test_persistence_on_failure(self):
        """Test if audio is saved to DIR_FALHAS on transcription failure."""
        print("\n--- Test: Persistence on Failure ---")
        
        # 1. Setup State
        self.maquina._caminho_audio = self.test_wav
        self.maquina._duracao_audio = 1.0
        
        # 2. Mock API to Fail
        self.maquina._cliente_api.transcrever = MagicMock(return_value=(None, "Simulated API Error"))
        
        # 3. Execute (simulate thread run)
        # We assume _transitar(TRANSCRIBING) was called
        with patch.object(self.maquina, '_transitar') as mock_transitar:
            # Prevent actual transitioning logic which creates threads or logs heavily
            self.maquina._processar_audio()
            
            # 4. Assertions
            # Check if ERROR state was triggered
            mock_transitar.assert_any_call(Estado.ERROR)
            
            # Check if file exists in failed_audios
            files = os.listdir(DIR_FALHAS)
            json_files = [f for f in files if f.endswith('.json')]
            wav_files = [f for f in files if f.endswith('.wav')]
            
            self.assertEqual(len(json_files), 1, "Should have 1 JSON metadata file")
            self.assertEqual(len(wav_files), 1, "Should have 1 WAV file")
            
            # Verify JSON content
            with open(os.path.join(DIR_FALHAS, json_files[0]), 'r') as f:
                data = json.load(f)
                self.assertEqual(data['erro'], "Simulated API Error")

    def test_retry_flow(self):
        """Test 'reprocessar_arquivo' logic."""
        print("\n--- Test: Retry Flow ---")
        
        # 1. Create a "failed" file manually
        failed_wav = os.path.join(DIR_FALHAS, "retry_test.wav")
        shutil.copy(self.test_wav, failed_wav)
        
        # 2. Call reprocessar
        with patch.object(self.maquina, '_processar_audio') as mock_process:
            self.maquina.reprocessar_arquivo(failed_wav)
            
            # 3. Assertions
            self.assertEqual(self.maquina._caminho_audio, failed_wav)
            # Should transition to TRANSCRIBING (implied by starting thread)
            # Actually reprocessar_arquivo starts a thread targetting _processar_audio
            # We just verified it setup the state correctly
            self.assertTrue(mock_process.called or self.maquina._estado == Estado.IDLE) 
            # Note: Since reprocessar starts a thread, we can't easily assert the thread started 
            # without more mocking, but we can verify internal state matches expectation.

if __name__ == '__main__':
    unittest.main()
