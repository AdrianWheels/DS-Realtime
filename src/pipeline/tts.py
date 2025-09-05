from typing import Iterable

import numpy as np
from piper.voice import PiperVoice
from TTS.api import TTS as CoquiTTS


class PiperTTS:
    def __init__(self, model_path: str, use_cuda: bool = True):
        # Piper busca el .json junto al .onnx automáticamente
        self.voice = PiperVoice.load(model_path, use_cuda=use_cuda)
        self.sample_rate = self.voice.config.sample_rate

    def synthesize_stream_raw(self, text: str) -> Iterable[bytes]:
        """Genera PCM16 (bytes) mientras se sintetiza (streaming)."""
        try:
            # voice.synthesize() retorna un Iterable[AudioChunk]
            audio_chunks = self.voice.synthesize(text)
            
            # Procesar cada AudioChunk del generador
            for chunk in audio_chunks:
                # AudioChunk tiene audio_int16_bytes property que retorna PCM16
                pcm16_bytes = chunk.audio_int16_bytes
                yield pcm16_bytes
                
        except Exception as e:
            # En caso de error, generar silencio breve
            duration_samples = int(self.sample_rate * 0.1)  # 100ms de silencio
            silence = np.zeros(duration_samples, dtype=np.int16).tobytes()
            yield silence


class XTTSTTS:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/xtts_v2"):
        self.tts = CoquiTTS(model_name)
        self.sample_rate = self.tts.synthesizer.output_sample_rate

    def synthesize_stream_raw(self, text: str) -> Iterable[bytes]:
        wav = self.tts.tts(text)
        pcm = (np.array(wav) * 32767).astype(np.int16).tobytes()
        yield pcm


class NoopTTS:
    """Fallback TTS that yields silence to allow the app to run when real TTS
    models are not present. Produces PCM16 mono at 16000 Hz.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def synthesize_stream_raw(self, text: str):
        # Yield a short silent frame (20 ms) to keep pipeline behavior.
        duration_ms = 20
        blocksize = int(self.sample_rate * duration_ms / 1000)
        silent_pcm = (np.zeros(blocksize, dtype=np.int16)).tobytes()
        yield silent_pcm
