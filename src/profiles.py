from dataclasses import dataclass
from pathlib import Path
import os

import torch

from .pipeline.asr import FasterWhisperASR
from .pipeline.tts import PiperTTS
from .utils.error_handling import DSRealtimeLogger, validate_file_paths


logger = DSRealtimeLogger("Profiles")


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
        try:
            from .pipeline.tts import XTTSTTS
            asr = FasterWhisperASR(model_size="medium", device="cuda", 
                                   compute_type="float16")
            tts = XTTSTTS()
        except Exception as e:
            print(f"[PROFILE] Error cargando perfil gpu-high: {e}")
            print("[PROFILE] Fallback a gpu-medium")
            # Fallback a gpu-medium si falla XTTS
            asr = FasterWhisperASR(model_size="small", device="cuda", 
                                   compute_type="float16")
            from pathlib import Path
            base_dir = Path(__file__).parent.parent.parent
            piper_model = base_dir / "models" / "piper" / "en_US-lessac-medium.onnx"
            tts = PiperTTS(model_path=str(piper_model), use_cuda=False)
    elif name == "gpu-medium":
        asr = FasterWhisperASR(model_size="small", device="cuda", compute_type="float16")
        tts = PiperTTS(model_path="models/piper/en_US-lessac-medium.onnx", use_cuda=False)
    elif name == "cpu-medium":
        # CPU-only profile with Piper TTS for reliable audio
        asr = FasterWhisperASR(model_size="small", device="cpu", compute_type="float32")
        tts = PiperTTS(model_path="models/piper/en_US-lessac-medium.onnx", use_cuda=False)
    else:
        # Prefer a local Vosk model on CPU, but gracefully fall back to a
        # CPU-based FasterWhisper ASR if the Vosk model folder isn't present
        # or Vosk fails to initialize. This avoids crashing the app when the
        # `models/` directory is not yet populated.
        try:
            from .pipeline.asr import VoskASR
            asr = VoskASR(model_path="models/vosk-model-small-es-0.42")
        except Exception:
            # Fallback to Whisper-based ASR running on CPU (no external model dir required,
            # faster-whisper will download model artifacts on first use).
            asr = FasterWhisperASR(model_size="small", device="cpu", compute_type="float32")

        # Prefer Piper local model if present; otherwise fall back to a NoopTTS
        # to avoid heavy downloads at startup (Coqui TTS attempts to fetch models
        # automatically which can fail or block). Users can later enable Coqui
        # or add Piper models in `models/`.
        from pathlib import Path
        import os
        
        # Usar rutas absolutas para evitar errores de ruta
        base_dir = Path(__file__).parent.parent.parent
        piper_model = base_dir / "models" / "piper" / "en_US-lessac-medium.onnx"
        piper_config = base_dir / "models" / "piper" / \
            "en_US-lessac-medium.onnx.json"
        
        try:
            if piper_model.exists() and piper_config.exists():
                tts = PiperTTS(model_path=str(piper_model), use_cuda=False)
            else:
                print(f"[PROFILE] Archivos Piper no encontrados:")
                print(f"  Model: {piper_model}")
                print(f"  Config: {piper_config}")
                from .pipeline.tts import NoopTTS
                tts = NoopTTS()
        except Exception as e:
            print(f"[PROFILE] Error cargando Piper TTS: {e}")
            from .pipeline.tts import NoopTTS
            tts = NoopTTS()
    return Profile(name=name, asr=asr, tts=tts)


def select_profile() -> Profile:
    return build_profile(detect_profile())

