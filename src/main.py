from pathlib import Path
import asyncio
import sys
import time
import argparse

import torch
import sounddevice as sd

from .profiles import select_profile, build_profile
from .pipeline.translate import NLLBTranslator
from .audio.capture import MicCapture
from .audio.sink import AudioSink

# Usar VAD avanzado si está disponible, sino el original
try:
    from .audio.advanced_vad import AdvancedVADSegmenter as VADSegmenter
    VAD_ADVANCED = True
except ImportError:
    from .audio.vad import VADSegmenter
    VAD_ADVANCED = False
from .utils.timing import StageTimer

from rich.console import Console
from rich.traceback import install as rich_install

try:
    from PySide6.QtWidgets import QApplication
    from qasync import QEventLoop
    from .ui.main_window import MainWindow
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False












console = Console()
rich_install(show_locals=False)






class Utterance:
    def __init__(self, pcm: bytes):
        self.pcm = pcm
        self.es_text: str = ''
        self.en_text: str = ''
        self.timer = StageTimer()



async def pipeline_cli(args, ui_callback=None):
    """Ejecuta el pipeline completo de traducción de voz.
    
    Args:
        args: Argumentos de línea de comandos
        ui_callback: Callback opcional para actualizar interfaz de usuario
                    Acepta también config_reload_signal para recargar config
    """
    print(f"[PIPELINE] starting pipeline with input={args.input!r} "
          f"output={args.output!r} exclusive={args.exclusive}")
    try:
        hosts = sd.query_hostapis()
        print(f"[PIPELINE] hostapis: {len(hosts)}")
        for i, h in enumerate(hosts):
            print(f"[PIPELINE]   hostapi[{i}] name={h.get('name')}")
        devs = sd.query_devices()
        print(f"[PIPELINE] devices: {len(devs)}")
        for i, d in enumerate(devs):
            print(f"[PIPELINE]   device[{i}] name={d.get('name')} "
                  f"idx={d.get('index')} in={d.get('max_input_channels')} "
                  f"out={d.get('max_output_channels')}")
    except Exception as e:
        print(f"[PIPELINE] device enumeration error: {e}")

    # Queues entre etapas
    frames_q = asyncio.Queue(maxsize=256)  # bytes PCM16 16kHz 20ms
    asr_q = asyncio.Queue(maxsize=16)      # Utterance listos para ASR
    mt_q = asyncio.Queue(maxsize=16)       # Utterance tras ASR
    tts_q = asyncio.Queue(maxsize=16)      # Utterance tras MT

    # 1) Captura + VAD
    mic = MicCapture(device_name=args.input, samplerate=16000, frame_ms=20, 
                     exclusive=args.exclusive)
    
    # Usar VAD avanzado con configuración anti-bucle
    if VAD_ADVANCED:
        vad = VADSegmenter(sample_rate=16000, frame_ms=20, config_file='config.ini')
        console.log('[bold green]VAD Avanzado activado[/bold green] - ' +
                   'Prevención de bucles habilitada')
        # Compartir instancia VAD con callback UI para recarga de config
        if ui_callback and hasattr(ui_callback, '__self__'):
            ui_callback.__self__.vad_instance = vad
    else:
        vad = VADSegmenter(sample_rate=16000, frame_ms=20, padding_ms=600, 
                           aggressiveness=3)
        console.log('[yellow]VAD Básico[/yellow] - ' +
                   'Instalar advanced_vad para mejor rendimiento')

    # 2) ASR + MT + TTS + Sink
    profile = (select_profile() if args.profile == 'auto' 
               else build_profile(args.profile))
    asr = profile.asr
    tts = profile.tts
    mt = NLLBTranslator(
        model_name='facebook/nllb-200-distilled-600M',
        device='cuda' if torch.cuda.is_available() else 'cpu',
    )
    # prepare a small on_playback callback to notify UI when audio is written

    def _on_playback(_bytes):
        if ui_callback:
            try:
                ui_callback(speaker_active=True)
            except Exception:
                pass

    try:
        sink = AudioSink(device_hint=args.output, samplerate=tts.sample_rate, 
                         channels=1, exclusive=args.exclusive, 
                         on_playback=_on_playback)
    except Exception as e:
        console.log(f"PortAudioError/AudioSink error: {e}")
        # try fallback to default output device (no hint)
        try:
            sink = AudioSink(device_hint=None, samplerate=tts.sample_rate, 
                             channels=1, exclusive=args.exclusive, 
                             on_playback=_on_playback)
            console.log("AudioSink: fallback to default output device succeeded")
            if ui_callback:
                try:
                    ui_callback(final="warning: used default output device")
                except Exception:
                    pass
        except Exception:
            # notify UI if present and abort
            if ui_callback:
                try:
                    ui_callback(final=f"error: {type(e).__name__}: {str(e)}")
                except Exception:
                    pass
            raise

    # Mensaje de inicio para CLI
    if ui_callback is None:  # Solo en modo CLI
        console.log("[bold green]🎤 TRADUCTOR INICIADO[/bold green]")
        console.log("[cyan]Configuración:[/cyan]")
        console.log(f"  • Entrada: {args.input}")
        console.log(f"  • Salida: {args.output}")
        console.log(f"  • Perfil: {args.profile}")
        console.log('')
        console.log('[yellow]💬 HABLA EN ESPAÑOL - Se traducirá al inglés[/yellow]')
        console.log('[dim]Presiona Ctrl+C para detener[/dim]')
        console.log('')

    async def capture_task():
        async for frame in mic.frames():
            await frames_q.put(frame)

    async def vad_task():
        async for segment in vad.segments(frames_q):
            await asr_q.put(Utterance(pcm=segment))

    async def asr_worker():
        while True:
            utt = await asr_q.get()
            with utt.timer.stage('asr'):
                utt.es_text = await asr.transcribe(utt.pcm, language='es')
            console.log(f"[bold cyan]ES:[/bold cyan] {utt.es_text}")
            await mt_q.put(utt)
            asr_q.task_done()

    async def mt_worker():
        while True:
            utt = await mt_q.get()
            with utt.timer.stage('mt'):
                utt.en_text = await mt.translate(utt.es_text, src_lang='spa_Latn', 
                                                 tgt_lang='eng_Latn')
            console.log(f"[bold green]EN:[/bold green] {utt.en_text}")
            await tts_q.put(utt)
            mt_q.task_done()

    async def tts_worker():
        while True:
            utt: Utterance = await tts_q.get()

            start = time.perf_counter()

            # Assume ASR and MT stages already ran (asr_worker and mt_worker),
            # so use existing texts on the utterance. If not present, compute them.
            try:
                t_first_partial = 0.0
                with utt.timer.stage('total'):
                    if not getattr(utt, 'es_text', None):
                        with utt.timer.stage('asr'):
                            utt.es_text = await asr.transcribe(utt.pcm, language='es')
                    t_first_partial = time.perf_counter() - start
                    if ui_callback:
                        ui_callback(partial=utt.es_text)
                    if not getattr(utt, 'en_text', None):
                        with utt.timer.stage('mt'):
                            utt.en_text = await mt.translate(utt.es_text, 
                                                             src_lang='spa_Latn', 
                                                             tgt_lang='eng_Latn')
                    t_final = time.perf_counter() - start
                    if ui_callback:
                        ui_callback(final=utt.en_text)
                    console.log(f"[bold cyan]ES:[/bold cyan] {utt.es_text}")
                    console.log(f"[bold green]EN:[/bold green] {utt.en_text}")

                    t_tts_start = None
                    with utt.timer.stage('tts'):
                        for chunk in tts.synthesize_stream_raw(utt.en_text):
                            if t_tts_start is None:
                                t_tts_start = time.perf_counter() - start
                            sink.write(chunk)

                    # Marcar traducción completada para prevención de bucles
                    if VAD_ADVANCED and hasattr(vad, 'mark_translation_completed'):
                        vad.mark_translation_completed()

                total_time = time.perf_counter() - start
                duration = len(utt.pcm) / (2 * 16000)
                rtf = total_time / duration if duration else 0.0
                metrics = {
                    "t_first_partial": t_first_partial,
                    "t_final": t_final,
                    "t_tts_start": t_tts_start if t_tts_start is 
                        not None else total_time,
                    "underruns": sink.underruns,
                    "rtf": rtf,
                }
                if ui_callback:
                    ui_callback(metrics=metrics)
                console.log(
                    f"metrics: first_partial={t_first_partial*1000:.0f} ms | "
                    f"final={t_final*1000:.0f} ms | "
                    f"tts_start={t_tts_start*1000:.0f} ms | "
                    f"underruns={sink.underruns} | RTF={rtf:.2f}"
                )
                console.log(utt.timer.summary())

            except Exception as e:
                console.log(f"tts_worker error: {e}")

            tts_q.task_done()


    # Orquestación
    tasks = [
        asyncio.create_task(capture_task(), name='capture'),
        asyncio.create_task(vad_task(), name='vad'),
        asyncio.create_task(asr_worker(), name='asr'),
        asyncio.create_task(mt_worker(), name='mt'),
        asyncio.create_task(tts_worker(), name='tts'),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        mic.close()
        sink.close()
    print("[PIPELINE] pipeline exiting, resources closed")




def build_arg_parser():
    p = argparse.ArgumentParser(description="LocalVoiceTranslate (offline ES→EN)")
    p.add_argument('--nogui', action='store_true', help="Ejecutar en modo CLI")
    p.add_argument('--input', default=None, 
        help="Nombre/parcial del micrófono de entrada (WASAPI)")
    p.add_argument('--output', default="CABLE Input", 
        help="Nombre/parcial del dispositivo de salida (VB-Cable)")
    p.add_argument('--exclusive', action='store_true', 
        help="WASAPI exclusive mode (menor latencia)")
    p.add_argument('--profile', default='auto',
                   choices=['auto', 'cpu-light', 'cpu-medium', 'gpu-medium', 'gpu-high'],
                   help="Perfil de hardware/modelos")
    return p




def main():
    args = build_arg_parser().parse_args()

    if args.nogui:
        asyncio.run(pipeline_cli(args))
    else:
        # Lanzar GUI con qasync
        if not GUI_AVAILABLE:
            print("Error: GUI dependencies not available. "
                  "Install PySide6 and qasync.")
            sys.exit(1)
            
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        win = MainWindow(args)
        # log app start to console and ui_debug.log via print
        print(f"[APP] starting MainWindow with input={args.input} "
              f"output={args.output} exclusive={args.exclusive}")
        win.show()
        with loop:
            loop.run_forever()
        print("[APP] event loop finished; application exiting")


if __name__ == "__main__":
    main()
