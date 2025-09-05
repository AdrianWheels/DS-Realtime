import sounddevice as sd
from array import array


class AudioSink:
    """Salida raw a VB-Cable (u otro) en PCM16.

    Escribe bytes `int16` al dispositivo de salida.
    """

    def __init__(self, device_hint: str = "CABLE Input", samplerate: int = 22050, channels: int = 1, exclusive: bool = False, on_playback=None):
        self.samplerate = samplerate
        self.channels = channels
        self._on_playback = on_playback
        # Resolve device index first
        device = self._find_device(device_hint) if device_hint else None

        # Prepare WasapiSettings only if applicable
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
            extra = None

        # Query device capabilities
        dev_info = None
        max_out = 0
        try:
            if device is not None:
                dev_info = sd.query_devices(device)
                max_out = int(dev_info.get("max_output_channels", 0) or 0)
        except Exception:
            dev_info = None
            max_out = 0

        # Build candidate opened channel counts (prefer minimal changes)
        candidates = []
        # desired logical channels first
        candidates.append(self.channels)
        # if logical is mono, try stereo
        if self.channels == 1 and max_out >= 2:
            candidates.append(2)
        # try device max if available
        if max_out and max_out not in candidates:
            candidates.append(max_out)
        # finally try 1 if not present
        if 1 not in candidates:
            candidates.append(1)

        last_exc = None
        self.stream = None
        opened_channels = None

        # Try candidates with extra settings first, then without
        for ch in candidates:
            if ch <= 0:
                continue
            # skip attempts that exceed device capacity
            if max_out and ch > max_out:
                continue
            for use_extra in (True, False):
                try:
                    settings = extra if (use_extra and extra is not None) else None
                    self.stream = sd.RawOutputStream(
                        samplerate=self.samplerate,
                        channels=ch,
                        dtype="int16",
                        device=device,
                        extra_settings=settings,
                    )
                    opened_channels = ch
                    break
                except Exception as e:
                    last_exc = e
                    # try next option
                    continue
            if self.stream is not None:
                break

        if self.stream is None:
            # Build helpful diagnostics
            try:
                hosts = sd.query_hostapis()
            except Exception:
                hosts = None
            msg = (
                f"Could not open output stream for device_hint={device_hint!r} (device_index={device!r})."
                f" last_error={last_exc!r}. device_info={dev_info!r} hostapis={hosts!r}"
            )
            raise RuntimeError(msg)

        # success
        self.stream.start()
        self.underruns = 0
        self._opened_channels = opened_channels or getattr(self.stream, "channels", self.channels)

    def _find_device(self, hint: str):
        hint_low = hint.lower()
        candidates = []
        for idx, dev in enumerate(sd.query_devices()):
            name = dev.get("name", "").lower()
            max_out = int(dev.get("max_output_channels", 0) or 0)
            if hint_low in name:
                # prefer devices that actually have output channels
                if max_out:
                    return idx
                candidates.append(idx)
        if candidates:
            return candidates[0]
        # fallback to default output device
        try:
            default_out = sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else sd.default.device
            return default_out
        except Exception:
            return None

    def write(self, audio_bytes: bytes):
        if not audio_bytes:
            return
        out_bytes = audio_bytes
        # If we opened the stream with more channels than the logical ones,
        # duplicate mono samples across channels (simple interleave).
        try:
            if getattr(self, "_opened_channels", self.channels) > self.channels:
                arr = array('h')
                arr.frombytes(audio_bytes)
                if len(arr) and len(arr) * 2 == len(audio_bytes):
                    new = array('h')
                    for s in arr:
                        for _ in range(self._opened_channels):
                            new.append(s)
                    out_bytes = new.tobytes()
        except Exception:
            out_bytes = audio_bytes

        self.stream.write(out_bytes)
        try:
            status = self.stream.get_status()
            if status.output_underflow:
                self.underruns += 1
        except Exception:
            pass
        # Notify playback to any listener (UI) - keep non-blocking
        try:
            if self._on_playback:
                try:
                    self._on_playback(out_bytes)
                except Exception:
                    # swallow callback errors
                    pass
        except Exception:
            pass

    def close(self):
        try:
            self.stream.stop(); self.stream.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
