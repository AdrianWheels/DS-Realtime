# LocalVoiceTranslate

Traductor de voz local ES→EN, 100 % offline.

## Resumen

LocalVoiceTranslate captura audio del micrófono, detecta segmentos de voz,
transcribe al español, traduce al inglés y sintetiza el resultado en audio, todo
sin depender de servicios externos. La aplicación funciona en modo CLI o con
una interfaz gráfica básica y está diseñada para ejecutarse de forma local con
aceleración GPU.

## Requisitos

- Windows 11 x64
- Python 3.11
- NVIDIA RTX 4080 con CUDA 12.1 (drivers recientes)
- VB-Audio Virtual Cable instalado

## Instalación

1. **Crear venv** y actualizar pip:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -U pip wheel pip-tools
   ```

2. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

   Para `torch` y `onnxruntime` se recomienda utilizar los binarios con soporte
   CUDA 12.1.

## Uso

### Modo CLI

```bash
python -m src.main --nogui --input "Nombre del micrófono" --output "CABLE Input"
```

### Interfaz gráfica

```bash
python -m src.main
```

Al iniciar se puede seleccionar el dispositivo de entrada y la aplicación
procesará la voz en tiempo real.

## Arquitectura

La pipeline se ejecuta de forma asíncrona en varias etapas:

1. **audio.capture.MicCapture** – captura frames PCM16 del micrófono.
2. **audio.vad.VADSegmenter** – segmenta voz usando WebRTC VAD.
3. **pipeline.FasterWhisperASR** – transcribe texto en español.
4. **pipeline.NLLBTranslator** – traduce el texto al inglés.
5. **pipeline.PiperTTS** – sintetiza audio en inglés.
6. **audio.sink.AudioSink** – envía el audio generado al dispositivo de salida.

`utils.StageTimer` registra tiempos por etapa y `ui.main_window` ofrece una
interfaz mínima con PySide6.

## Desarrollo y pruebas

Las pruebas unitarias se ejecutan con:

```bash
pytest
```

Se recomienda ejecutarlas antes de enviar cambios para verificar el correcto
funcionamiento del pipeline.
