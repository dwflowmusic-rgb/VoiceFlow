
import sys
import threading
import time
import os
import unittest
from unittest.mock import MagicMock, patch

# Inject windll into ctypes to satisfy Windows-specific imports
import ctypes
if not hasattr(ctypes, 'windll'):
    ctypes.windll = MagicMock()
    ctypes.windll.user32.GetForegroundWindow.return_value = 12345
    ctypes.windll.kernel32 = MagicMock()

# Mock sounddevice to avoid PortAudio requirement
mock_sd = MagicMock()
sys.modules['sounddevice'] = mock_sd

# Now we can safely import core modules
sys.path.append(os.getcwd())

from core.maquina_estados import MaquinaEstados, Estado

# Mock config
MOCK_CONFIG = {
    "transcription": {"api_key": "dummy", "model": "dummy"},
    "polishing": {"api_key": "dummy", "model": "dummy"}
}

class TestEscRaceCondition(unittest.TestCase):
    def setUp(self):
        # Patch dependencies
        self.patcher_captura = patch('core.maquina_estados.CapturadorAudio')
        self.MockCaptura = self.patcher_captura.start()

        self.patcher_api = patch('core.maquina_estados.ClienteAPI')
        self.MockAPI = self.patcher_api.start()

        self.patcher_historico = patch('core.maquina_estados.GerenciadorHistorico')
        self.MockHistorico = self.patcher_historico.start()

        # Patch detector internal function to avoid any ctypes usage if it leaked
        self.patcher_detector = patch('core.maquina_estados.obter_janela_ativa', return_value=12345)
        self.MockDetector = self.patcher_detector.start()

        # Setup MaquinaEstados
        self.maquina = MaquinaEstados(MOCK_CONFIG)

        # Create a dummy file for the "audio"
        self.test_file = "test_audio.wav"
        with open(self.test_file, "w") as f:
            f.write("dummy audio data")

    def tearDown(self):
        self.patcher_captura.stop()
        self.patcher_api.stop()
        self.patcher_historico.stop()
        self.patcher_detector.stop()
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except OSError:
                pass

    def test_cancel_during_transcription(self):
        print("\n--- Testing Cancel During Transcription ---")

        # Setup mocks
        # Capturador returns our dummy file
        self.maquina._capturador.iniciar_gravacao.return_value = True
        self.maquina._capturador.parar_gravacao.return_value = (self.test_file, 1.0)

        # API transcrever simulates delay
        def slow_transcribe(*args, **kwargs):
            print("API: Transcribing... (sleeping)")
            # Verify file exists BEFORE processing starts (sanity check)
            if not os.path.exists(args[0]):
                 print("API: File missing at start!")
                 raise FileNotFoundError(args[0])

            time.sleep(2) # Sleep to allow cancel to happen

            print("API: Transcribing done. Checking file...")
            # Try to read the file to simulate what real API client might do
            try:
                with open(args[0], 'rb') as f:
                    pass
                print("API: File access SUCCESS")
                return "Transcribed Text", None
            except FileNotFoundError:
                print("API: CRITICAL ERROR - File not found!")
                raise

        self.maquina._cliente_api.transcrever.side_effect = slow_transcribe

        # 1. Start Recording
        print("Main: Starting recording")
        self.maquina.iniciar_gravacao()
        self.assertEqual(self.maquina.estado, Estado.RECORDING)

        # 2. Stop Recording (starts thread)
        print("Main: Stopping recording (starts thread)")
        self.maquina.parar_gravacao()
        self.assertEqual(self.maquina.estado, Estado.TRANSCRIBING)

        # Wait a bit to ensure thread enters 'transcrever'
        time.sleep(0.5)

        # 3. Cancel (The Bug Trigger)
        print("Main: User hits ESC (calling cancelar)")
        self.maquina.cancelar()

        # Verify state immediately changed to IDLE
        self.assertEqual(self.maquina.estado, Estado.IDLE)
        print("Main: State is IDLE")

        # Wait for thread to finish (it will wake up after sleep)
        time.sleep(2.5)

        # Verification:
        # The thread should have finished gracefully.
        # The file should be gone NOW (cleaned up by thread), but NO crash should have occurred.

        self.assertFalse(os.path.exists(self.test_file), "File should be cleaned up by thread eventually")
        print("Test finished successfully (no crash observed)")

if __name__ == '__main__':
    unittest.main()
