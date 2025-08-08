from typing import Iterable
from piper.voice import PiperVoice


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
