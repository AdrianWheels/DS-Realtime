import argparse
import asyncio
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.traceback import install as rich_install

from audio.capture import MicCapture
from audio.vad import VADSegmenter
from audio.sink import AudioSink
from pipeline.asr import FasterWhisperASR
from pipeline.translate import NLLBTranslator
from pipeline.tts import PiperTTS
from utils.timing import StageTimer

console = Console()
rich_install(show_locals=False)


async def pipeline_cli(args, ui_callback=None):
    # Queues entre etapas
    frames_q = asyncio.Queue(maxsize=256)        # bytes PCM16 16kHz 20ms
    utterances_q = asyncio.Queue(maxsize=16)     # bytes PCM16 concatenados

    # 1) Captura + VAD
    mic = MicCapture(device_name=args.input, samplerate=16000, frame_ms=20, exclusive=args.exclusive)
    vad = VADSegmenter(sample_rate=16000, frame_ms=20, padding_ms=400, aggressiveness=2)

    # 2) ASR + MT + TTS + Sink
    asr = FasterWhisperASR(model_size=args.whisper, device="cuda", compute_type="float16")
    mt = NLLBTranslator(model_name="facebook/nllb-200-distilled-600M", device="cuda")

    # Cargamos TTS y salida VB-Cable (samplerate de la voz)
    tts = PiperTTS(model_path=args.piper_model, use_cuda=True)
    sink = AudioSink(device_hint=args.output, samplerate=tts.sample_rate, channels=1, exclusive=args.exclusive)

    timer = StageTimer()

    async def capture_task():
        async for frame in mic.frames():
            await frames_q.put(frame)

    async def vad_task():
        async for segment in vad.segments(frames_q):
            await utterances_q.put(segment)

    async def nlp_task():
        while True:
            pcm = await utterances_q.get()
            start = time.perf_counter()
            with timer.stage("total"):
                with timer.stage("asr"):
                    es_text = await asr.transcribe(pcm, language="es")
                t_first_partial = time.perf_counter() - start
                if ui_callback:
                    ui_callback(partial=es_text)
                with timer.stage("mt"):
                    en_text = await mt.translate(es_text, src_lang="spa_Latn", tgt_lang="eng_Latn")
                t_final = time.perf_counter() - start
                if ui_callback:
                    ui_callback(final=en_text)
                console.log(f"[bold cyan]ES:[/bold cyan] {es_text}")
                console.log(f"[bold green]EN:[/bold green] {en_text}")
                t_tts_start = None
                with timer.stage("tts"):
                    # stream directo al sink para mínima latencia
                    for chunk in tts.synthesize_stream_raw(en_text):
                        if t_tts_start is None:
                            t_tts_start = time.perf_counter() - start
                        sink.write(chunk)
            total_time = time.perf_counter() - start
            duration = len(pcm) / (2 * 16000)
            rtf = total_time / duration if duration else 0.0
            metrics = {
                "t_first_partial": t_first_partial,
                "t_final": t_final,
                "t_tts_start": t_tts_start if t_tts_start is not None else total_time,
                "underruns": sink.underruns,
                "rtf": rtf,
            }
            if ui_callback:
                ui_callback(metrics=metrics)
            console.log(
                f"metrics: first_partial={t_first_partial*1000:.0f} ms | "
                f"final={t_final*1000:.0f} ms | tts_start={t_tts_start*1000:.0f} ms | "
                f"underruns={sink.underruns} | RTF={rtf:.2f}"
            )
            console.log(timer.summary())
            utterances_q.task_done()

    # Orquestación
    tasks = [
        asyncio.create_task(capture_task(), name="capture"),
        asyncio.create_task(vad_task(), name="vad"),
        asyncio.create_task(nlp_task(), name="nlp"),
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
    p.add_argument("--whisper", default="small", help="Tamaño modelo faster-whisper (small/medium/large-v3, etc.)")
    p.add_argument("--piper-model", default=str(Path(__file__).resolve().parents[1] / "models/piper/en_US-lessac-medium.onnx"),
                   help="Ruta al modelo Piper .onnx")
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
