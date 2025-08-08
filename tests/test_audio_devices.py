import sys
import types

# Provide a minimal stub for the sounddevice module used during imports
sd_stub = types.SimpleNamespace(
    query_devices=lambda: [],
    WasapiSettings=lambda *args, **kwargs: None,
    RawInputStream=object,
    RawOutputStream=object,
)
sys.modules.setdefault('sounddevice', sd_stub)

from audio.capture import MicCapture
from audio.sink import AudioSink
from unittest.mock import patch


def test_mic_capture_find_device():
    mc = MicCapture.__new__(MicCapture)
    devices = [{'name': 'Device A'}, {'name': 'My Mic'}, {'name': 'Other'}]
    with patch('audio.capture.sd.query_devices', return_value=devices):
        assert mc._find_device('my mic') == 1
        assert mc._find_device('unknown') is None


def test_audio_sink_find_device():
    sink = AudioSink.__new__(AudioSink)
    devices = [{'name': 'Alpha'}, {'name': 'Beta Device'}]
    with patch('audio.sink.sd.query_devices', return_value=devices):
        assert sink._find_device('beta') == 1
        assert sink._find_device('gamma') is None
