
import sys
import threading
import time
import os
import unittest
from unittest.mock import MagicMock, patch

# Inject windll
import ctypes
if not hasattr(ctypes, 'windll'):
    ctypes.windll = MagicMock()
    ctypes.windll.user32.GetForegroundWindow.return_value = 12345
    ctypes.windll.kernel32 = MagicMock()

# Mock sounddevice
mock_sd = MagicMock()
sys.modules['sounddevice'] = mock_sd

sys.path.append(os.getcwd())
from core.maquina_estados import MaquinaEstados, Estado

MOCK_CONFIG = {
    "transcription": {"api_key": "dummy", "model": "dummy"},
    "polishing": {"api_key": "dummy", "model": "dummy"}
}

class TestZombieThread(unittest.TestCase):
    def setUp(self):
        self.patcher_captura = patch('core.maquina_estados.CapturadorAudio')
        self.MockCaptura = self.patcher_captura.start()

        self.patcher_api = patch('core.maquina_estados.ClienteAPI')
        self.MockAPI = self.patcher_api.start()

        self.patcher_historico = patch('core.maquina_estados.GerenciadorHistorico')
        self.MockHistorico = self.patcher_historico.start()

        self.patcher_detector = patch('core.maquina_estados.obter_janela_ativa', return_value=12345)
        self.MockDetector = self.patcher_detector.start()

        self.maquina = MaquinaEstados(MOCK_CONFIG)
        self.test_file_1 = "audio_1.wav"
        self.test_file_2 = "audio_2.wav"

        with open(self.test_file_1, "w") as f: f.write("audio1")
        with open(self.test_file_2, "w") as f: f.write("audio2")

    def tearDown(self):
        self.patcher_captura.stop()
        self.patcher_api.stop()
        self.patcher_historico.stop()
        self.patcher_detector.stop()
        if os.path.exists(self.test_file_1): os.remove(self.test_file_1)
        if os.path.exists(self.test_file_2): os.remove(self.test_file_2)

    def test_zombie_thread_ignored(self):
        print("\n--- Testing Zombie Thread Ignored ---")

        # Setup mocks
        self.MockCaptura.return_value.iniciar_gravacao.return_value = True
        # First stop returns file 1
        self.MockCaptura.return_value.parar_gravacao.side_effect = [
            (self.test_file_1, 1.0),
            (self.test_file_2, 1.0)
        ]

        # API transcrever simulates delay
        def slow_transcribe(*args, **kwargs):
            print(f"API: Transcribing {args[0]}... (sleeping)")
            time.sleep(2)
            print(f"API: Transcribing done for {args[0]}")
            return "Text", None

        self.maquina._cliente_api.transcrever.side_effect = slow_transcribe

        # 1. Start Recording 1
        self.maquina.iniciar_gravacao()
        print(f"ID Operacao: {self.maquina._id_operacao}")
        id1 = self.maquina._id_operacao

        # 2. Stop Recording 1 (Thread 1 starts)
        self.maquina.parar_gravacao()
        # Thread 1 is now sleeping in slow_transcribe

        # 3. Cancel (State -> IDLE)
        # Note: In real app, user might press ESC.
        # Here we verify that cancellation works and allows new recording.
        self.maquina.cancelar()
        self.assertEqual(self.maquina.estado, Estado.IDLE)
        print("Cancelled. State is IDLE.")

        # 4. Start Recording 2 (State -> RECORDING)
        # This increments ID
        self.maquina.iniciar_gravacao()
        print(f"ID Operacao: {self.maquina._id_operacao}")
        id2 = self.maquina._id_operacao
        self.assertNotEqual(id1, id2)
        self.assertEqual(self.maquina.estado, Estado.RECORDING)

        # 5. Wait for Thread 1 to finish
        print("Waiting for Thread 1 to wake up...")
        time.sleep(2.5)

        # 6. Verify State
        # If bug exists, Thread 1 would set state to IDLE.
        # If fixed, Thread 1 sees obsolete ID and does NOT touch state.
        print(f"Current State: {self.maquina.estado}")
        self.assertEqual(self.maquina.estado, Estado.RECORDING,
                         "State should remain RECORDING (Zombie thread must not reset it)")

        # Verify Thread 1 cleaned up its file
        self.assertFalse(os.path.exists(self.test_file_1), "Zombie thread should clean its file")

        # Verify Thread 2 (Recording) is still active (conceptually)
        # We didn't stop recording 2 yet.

if __name__ == '__main__':
    unittest.main()
