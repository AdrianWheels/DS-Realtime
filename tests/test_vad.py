import asyncio
import pytest
from audio.vad import VADSegmenter


class FakeVAD:
    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        return frame[0] == 1


@pytest.mark.asyncio
async def test_vad_segmenter_segments_frames():
    seg = VADSegmenter(sample_rate=16000, frame_ms=20, padding_ms=40)
    seg.vad = FakeVAD()
    q = asyncio.Queue()
    speech = b'\x01' * seg.bytes_per_frame
    silence = b'\x00' * seg.bytes_per_frame
    for frame in [speech, speech, silence, silence]:
        await q.put(frame)
    gen = seg.segments(q)
    utterance = await asyncio.wait_for(gen.__anext__(), timeout=1)
    assert utterance == speech + speech + silence + silence
    await gen.aclose()
