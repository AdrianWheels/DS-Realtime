import argparse
import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.traceback import install as rich_install

from audio.capture import MicCapture
from audio.vad import VADSegmenter
from audio.sink import AudioSink
from pipeline.translate import NLLBTranslator
from profiles import select_profile, build_profile
from utils.timing import StageTimer

console = Console()
rich_install(show_locals=False)


@dataclass
class Utterance:
    pcm: bytes
    es_text: str = ""
    en_text: str = ""
    timer: StageTimer = field(default_factory=StageTimer)


async def pipeline_cli(args):
    # Queues entre etapas
    frames_q = asyncio.Queue(maxsize=256)  # bytes PCM16 16kHz 20ms
    asr_q = asyncio.Queue(maxsize=16)      # Utterance listos para ASR
    mt_q = asyncio.Queue(maxsize=16)       # Utterance tras ASR
    tts_q = asyncio.Queue(maxsize=16)      # Utterance tras MT

    # 1) Captura + VAD
    mic = MicCapture(device_name=args.input, samplerate=16000, frame_ms=20, exclusive=args.exclusive)
    vad = VADSegmenter(sample_rate=16000, frame_ms=20, padding_ms=400, aggressiveness=2)

    # 2) ASR + MT + TTS + Sink
    profile = select_profile() if args.profile == "auto" else build_profile(args.profile)
    asr = profile.asr
    tts = profile.tts
    mt = NLLBTranslator(
        model_name="facebook/nllb-200-distilled-600M",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    sink = AudioSink(device_hint=args.output, samplerate=tts.sample_rate, channels=1, exclusive=args.exclusive)

    async def capture_task():
        async for frame in mic.frames():
            await frames_q.put(frame)

    async def vad_task():
        async for segment in vad.segments(frames_q):
            await asr_q.put(Utterance(pcm=segment))

    async def asr_worker():
        while True:
            utt = await asr_q.get()
            with utt.timer.stage("asr"):
                utt.es_text = await asr.transcribe(utt.pcm, language="es")
            console.log(f"[bold cyan]ES:[/bold cyan] {utt.es_text}")
            await mt_q.put(utt)
            asr_q.task_done()

    async def mt_worker():
        while True:
            utt = await mt_q.get()
            with utt.timer.stage("mt"):
                utt.en_text = await mt.translate(utt.es_text, src_lang="spa_Latn", tgt_lang="eng_Latn")
            console.log(f"[bold green]EN:[/bold green] {utt.en_text}")
            await tts_q.put(utt)
            mt_q.task_done()

    async def tts_worker():
        while True:
            pcm = await utterances_q.get()
            audio_sec = len(pcm) / (2 * 16000)
            with timer.stage("total"):
                with timer.stage("asr"):
                    es_text = await asr.transcribe(pcm, language="es")
                with timer.stage("mt"):
                    en_text = await mt.translate(es_text, src_lang="spa_Latn", tgt_lang="eng_Latn")
                console.log(f"[bold cyan]ES:[/bold cyan] {es_text}")
                console.log(f"[bold green]EN:[/bold green] {en_text}")
                with timer.stage("tts"):
                    # stream directo al sink para mínima latencia
                    for chunk in tts.synthesize_stream_raw(en_text):
                        sink.write(chunk)
            console.log(timer.summary(audio_sec))
            utterances_q.task_done()


    # Orquestación
    tasks = [
        asyncio.create_task(capture_task(), name="capture"),
        asyncio.create_task(vad_task(), name="vad"),
        asyncio.create_task(asr_worker(), name="asr"),
        asyncio.create_task(mt_worker(), name="mt"),
        asyncio.create_task(tts_worker(), name="tts"),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        mic.close()
        sink.close()


def build_arg_parser():
    p = argparse.ArgumentParser(description="LocalVoiceTranslate (offline ES→EN)")
    p.add_argument("--nogui", action="store_true", help="Ejecutar en modo CLI")
    p.add_argument("--input", default=None, help="Nombre/parcial del micrófono de entrada (WASAPI)")
    p.add_argument("--output", default="CABLE Input", help="Nombre/parcial del dispositivo de salida (VB-Cable)")
    p.add_argument("--exclusive", action="store_true", help="WASAPI exclusive mode (menor latencia)")
    p.add_argument("--profile", default="auto",
                   choices=["auto", "cpu-light", "gpu-medium", "gpu-high"],
                   help="Perfil de hardware/modelos")
    return p


def main():
    args = build_arg_parser().parse_args()

    if args.nogui:
        asyncio.run(pipeline_cli(args))
    else:
        # Lanzar GUI con qasync
        from PySide6.QtWidgets import QApplication
        from qasync import QEventLoop
        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        win = MainWindow(args)
        win.show()
        with loop:
            loop.run_forever()


if __name__ == "__main__":
    main()
