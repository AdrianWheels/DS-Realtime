import asyncio
import sounddevice as sd
from typing import AsyncGenerator, Optional


class MicCapture:
    """Captura audio mono PCM16 a 16 kHz en frames de N ms.

    Entrega frames de tamaño fijo (p.ej. 20 ms) como bytes `int16`.
    """

    def __init__(self, device_name: Optional[str], samplerate: int = 16000, frame_ms: int = 20, exclusive: bool = False):
        self.samplerate = samplerate
        self.frame_ms = frame_ms
        self.blocksize = int(samplerate * frame_ms / 1000)
        self.bytes_per_frame = self.blocksize * 2  # int16
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=256)
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # Fallback for contexts without a running loop
            self._loop = asyncio.get_event_loop()

        # Resolve device index first (if a hint was provided)
        device = None
        if device_name:
            device = self._find_device(device_name)

        # Only create WasapiSettings when the device's host API is WASAPI
        extra = None
        try:
            if device is not None:
                dev_info = sd.query_devices(device)
                hostapi_idx = dev_info.get("hostapi")
                if hostapi_idx is not None:
                    hostapi_name = sd.query_hostapis()[hostapi_idx].get("name", "").lower()
                    if "wasapi" in hostapi_name:
                        try:
                            extra = sd.WasapiSettings(exclusive=exclusive)
                        except Exception:
                            extra = None
        except Exception:
            # Fall back to no extra settings if any query fails
            extra = None

        # Try opening stream with extra_settings if available; on failure retry
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                channels=1,
                dtype="int16",
                device=device,
                extra_settings=extra,
                callback=self._callback,
            )
        except Exception:
            # If opening with extra_settings failed, retry without it
            self.stream = sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                channels=1,
                dtype="int16",
                device=device,
                callback=self._callback,
            )

        self.stream.start()

    def _find_device(self, hint: str):
        """Busca por subcadenas case-insensitive en la lista de dispositivos."""
        hint_low = hint.lower()
        for idx, dev in enumerate(sd.query_devices()):
            name = dev.get("name", "").lower()
            if hint_low in name:
                return idx
        return None

    def _callback(self, indata, frames, time, status):
        if status:
            # No levantar excepciones desde el hilo de PortAudio
            pass
        data = bytes(indata[: frames * 2])  # ya es int16 raw
        # Use call_soon_threadsafe to enqueue; if the queue is full, drop frame
        def _put():
            try:
                self._queue.put_nowait(data)
            except Exception:
                # QueueFull or other error: drop frame silently
                pass

        try:
            self._loop.call_soon_threadsafe(_put)
        except RuntimeError:
            # Event loop cerrado
            pass

    async def frames(self) -> AsyncGenerator[bytes, None]:
        while True:
            chunk = await self._queue.get()
            yield chunk

    def close(self):
        try:
            self.stream.stop(); self.stream.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
