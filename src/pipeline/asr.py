import asyncio
import json
import numpy as np
from faster_whisper import WhisperModel
from vosk import Model, KaldiRecognizer


class FasterWhisperASR:
    def __init__(self, model_size: str = "small", device: str = "cuda", compute_type: str = "float16"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    async def transcribe(self, pcm16_bytes: bytes, language: str = "es") -> str:
        """Transcribe PCM16 16k mono → texto.
        Usa un hilo del pool para no bloquear el event loop.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_transcribe, pcm16_bytes, language)

    def _sync_transcribe(self, pcm16_bytes: bytes, language: str) -> str:
        audio = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        text_parts = [seg.text for seg in segments]
        return " ".join(text_parts).strip()


class VoskASR:
    def __init__(self, model_path: str):
        self.model = Model(model_path)

    async def transcribe(self, pcm16_bytes: bytes, language: str = "es") -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_transcribe, pcm16_bytes)

    def _sync_transcribe(self, pcm16_bytes: bytes) -> str:
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.AcceptWaveform(pcm16_bytes)
        result = json.loads(recognizer.Result())
        return result.get("text", "").strip()
