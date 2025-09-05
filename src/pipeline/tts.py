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
        for chunk in self.voice.synthesize_stream_raw(text):
            if chunk:
                yield chunk


class XTTSTTS:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/xtts_v2"):
        self.tts = CoquiTTS(model_name)
        self.sample_rate = self.tts.synthesizer.output_sample_rate

    def synthesize_stream_raw(self, text: str) -> Iterable[bytes]:
        wav = self.tts.tts(text)
        pcm = (np.array(wav) * 32767).astype(np.int16).tobytes()
        yield pcm
