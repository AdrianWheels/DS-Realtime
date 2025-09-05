import time
from utils.timing import StageTimer


def test_stage_timer_accumulates_and_clears():
    timer = StageTimer()
    with timer.stage('phase'):
        time.sleep(0.001)
    with timer.stage('phase'):
        time.sleep(0.001)
    summary = timer.summary(audio_duration=0.01)
    assert 'phase=' in summary and 'RTF=' in summary
    assert timer._stamps == {}
    assert timer.summary() == ''
