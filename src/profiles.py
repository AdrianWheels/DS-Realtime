from dataclasses import dataclass

import torch

from pipeline.asr import FasterWhisperASR
from pipeline.tts import PiperTTS


@dataclass
class Profile:
    name: str
    asr: object
    tts: object


def _available_vram() -> int:
    """Return available VRAM in MB for the first CUDA device."""
    try:
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return props.total_memory // (1024 ** 2)
    except Exception:
        pass
    return 0


def detect_profile() -> str:
    vram = _available_vram()
    if vram >= 16000:  # 16 GB or more
        return "gpu-high"
    if vram >= 6000:   # 6 GB or more
        return "gpu-medium"
    return "cpu-light"


def build_profile(name: str) -> Profile:
    if name == "gpu-high":
        from pipeline.tts import XTTSTTS
        asr = FasterWhisperASR(model_size="medium", device="cuda", compute_type="float16")
        tts = XTTSTTS()
    elif name == "gpu-medium":
        asr = FasterWhisperASR(model_size="small", device="cuda", compute_type="float16")
        tts = PiperTTS(model_path="models/piper/en_US-lessac-medium.onnx", use_cuda=True)
    else:
        from pipeline.asr import VoskASR
        asr = VoskASR(model_path="models/vosk-model-small-es-0.42")
        tts = PiperTTS(model_path="models/piper/en_US-lessac-medium.onnx", use_cuda=False)
    return Profile(name=name, asr=asr, tts=tts)


def select_profile() -> Profile:
    return build_profile(detect_profile())

