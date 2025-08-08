import sounddevice as sd


class AudioSink:
    """Salida raw a VB-Cable (u otro) en PCM16.

    Escribe bytes `int16` al dispositivo de salida.
    """

    def __init__(self, device_hint: str = "CABLE Input", samplerate: int = 22050, channels: int = 1, exclusive: bool = False):
        self.samplerate = samplerate
        self.channels = channels
        extra = None
        try:
            extra = sd.WasapiSettings(exclusive=exclusive)
        except Exception:
            extra = None

        device = self._find_device(device_hint) if device_hint else None

        self.stream = sd.RawOutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="int16",
            device=device,
            extra_settings=extra,
        )
        self.stream.start()

    def _find_device(self, hint: str):
        hint_low = hint.lower()
        for idx, dev in enumerate(sd.query_devices()):
            name = dev.get("name", "").lower()
            if hint_low in name:
                return idx
        return None

    def write(self, audio_bytes: bytes):
        if not audio_bytes:
            return
        self.stream.write(audio_bytes)

    def close(self):
        try:
            self.stream.stop(); self.stream.close()
        except Exception:
            pass
