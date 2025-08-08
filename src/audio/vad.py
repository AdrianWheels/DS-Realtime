import asyncio
import collections
import time
import webrtcvad


class VADSegmenter:
    """Corta en *utterances* usando WebRTC VAD.

    - Entrada: frames PCM16 (bytes) de `frame_ms` a `sample_rate`.
    - Salida: bytes concatenados (utterance completa).
    """

    def __init__(self, sample_rate=16000, frame_ms=20, padding_ms=400, aggressiveness=2):
        assert frame_ms in (10, 20, 30)
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.bytes_per_frame = int(sample_rate * frame_ms / 1000) * 2
        self.vad = webrtcvad.Vad(aggressiveness)
        self.num_pad = max(1, padding_ms // frame_ms)

    async def segments(self, frames_q: asyncio.Queue):
        ring = collections.deque(maxlen=self.num_pad)
        voiced_frames = bytearray()
        triggered = False
        silence_count = 0
        while True:
            frame: bytes = await frames_q.get()
            # Normalizar tamaño exacto de frame
            if len(frame) != self.bytes_per_frame:
                # Relleno/corte para VAD
                if len(frame) < self.bytes_per_frame:
                    frame = frame + b"\x00" * (self.bytes_per_frame - len(frame))
                else:
                    frame = frame[: self.bytes_per_frame]

            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring.append((frame, is_speech))
                num_voiced = sum(1 for _, s in ring if s)
                if num_voiced > 0.6 * ring.maxlen:
                    triggered = True
                    for f, _ in ring:
                        voiced_frames.extend(f)
                    ring.clear()
            else:
                voiced_frames.extend(frame)
                ring.append((frame, is_speech))
                if not is_speech:
                    silence_count += 1
                else:
                    silence_count = 0

                if silence_count >= self.num_pad:
                    # Fin de utterance
                    yield bytes(voiced_frames)
                    voiced_frames = bytearray()
                    ring.clear(); triggered = False; silence_count = 0
