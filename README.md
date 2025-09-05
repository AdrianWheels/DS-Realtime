# LocalVoiceTranslate

Traductor de voz local ES→EN, 100% offline con **configuración avanzada en tiempo real**.

## 🎯 Características

- ✅ **Traducción offline completa**: Sin servicios externos
- ✅ **Interfaz gráfica avanzada**: Con configuración en tiempo real
- ✅ **Anti-feedback inteligente**: Prevención de bucles de retroalimentación
- ✅ **VAD avanzado**: Detección de voz con supresión de ruido espectral
- ✅ **Optimizado para Discord**: Audio routing perfecto
- ✅ **GPU accelerated**: NVIDIA CUDA para máximo rendimiento

## Resumen

LocalVoiceTranslate captura audio del micrófono, detecta segmentos de voz,
transcribe al español, traduce al inglés y sintetiza el resultado en audio, todo
sin depender de servicios externos. 

### 🆕 Nuevas características v2.0:

- **Ventana de configuración avanzada** con 5 pestañas organizadas
- **Recarga de configuración en tiempo real** sin reiniciar
- **Monitor de VAD en vivo** para debugging y optimización
- **Sistema anti-bucles mejorado** con cooldowns y detección de similitud
- **Auto-selección de dispositivos** para DiscordeTranslate

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

### 🎛️ Interfaz Gráfica (Recomendado)

```bash
python -m src.main
```

**Nuevas características de la interfaz:**
- Botón **"⚙️ Config"** para acceder a configuración avanzada
- Auto-selección de dispositivos optimizada para Discord
- Monitor en tiempo real del VAD y procesamiento de audio

### 🔧 Ventana de Configuración Avanzada

La nueva ventana de configuración permite ajustar todos los parámetros en tiempo real:

- **🎤 Audio**: Sample rate, umbrales de voz, puerta de ruido
- **🗣️ VAD**: Agresividad, padding, ratio de voz
- **🔄 Anti-bucles**: Prevención de feedback, cooldowns, límites
- **🔧 Filtros**: Pasa-alto/bajo, supresión espectral
- **🐛 Debug**: Logging y monitor en tiempo real

### Modo CLI

```bash
python -m src.main --nogui --input "Micrófono de los auriculares con micrófono (Logitech G535 Gaming Headset)" --output "CABLE Input"
```

### 🎮 Configuración para Discord

1. **Dispositivos recomendados** (auto-seleccionados):
   - Entrada: `Logitech G535 Gaming Headset`
   - Salida: `CABLE Input (VB-Audio Virtual Cable)`

2. **En Discord**:
   - Entrada: Tu micrófono normal
   - Salida: `CABLE Output (VB-Audio Virtual Cable)`

3. **Configuración anti-bucles**:
   - Umbral de voz: -30dB
   - Cooldown: 500ms
   - Máx. traducciones consecutivas: 3

## Arquitectura

La pipeline se ejecuta de forma asíncrona en varias etapas:

1. **audio.capture.MicCapture** – captura frames PCM16 del micrófono.
2. **audio.advanced_vad.AdvancedVADSegmenter** – segmenta voz con anti-feedback y supresión de ruido.
3. **pipeline.asr.FasterWhisperASR** – transcribe texto en español.
4. **pipeline.translate.NLLBTranslator** – traduce el texto al inglés.
5. **pipeline.tts.PiperTTS** – sintetiza audio en inglés.
6. **audio.sink.AudioSink** – envía el audio generado al dispositivo de salida.

### 🧠 Sistema VAD Avanzado

- **WebRTC VAD base** con configuración dinámica
- **Supresión espectral de ruido** en tiempo real
- **Detección de bucles de feedback** con similitud de texto
- **Cooldowns inteligentes** para prevenir spam
- **Umbrales de nivel** configurables para diferentes entornos

### 🎛️ Configuración en Tiempo Real

- **Sin reinicio**: Los cambios se aplican inmediatamente
- **Persistencia**: Se guarda automáticamente en `config.ini`
- **Monitor visual**: Feedback en vivo del estado del sistema

`utils.StageTimer` registra tiempos por etapa y `ui.config_window` ofrece
configuración avanzada con PySide6.

## Desarrollo y pruebas

Las pruebas unitarias se ejecutan con:

```bash
pytest
```

Se recomienda ejecutarlas antes de enviar cambios para verificar el correcto
funcionamiento del pipeline.

## 📋 Archivos de configuración

- **`config.ini`**: Configuración principal del VAD y procesamiento
- **`CONFIGURACION_AVANZADA.md`**: Guía detallada de la interfaz de configuración

## 🔧 Solución de problemas

### Bucles de retroalimentación
Si experimentas bucles de audio:
1. Abre la ventana de configuración (⚙️ Config)
2. Ve a la pestaña "🔄 Anti-bucles"
3. Ajusta el cooldown a 1000ms
4. Reduce el máximo de traducciones consecutivas a 2

### Sensibilidad del VAD
Para ajustar la detección de voz:
1. Pestaña "🗣️ VAD" → Ajusta agresividad (0-3)
2. Pestaña "🎤 Audio" → Modifica umbral de voz (-40 a 0 dB)
3. Usa la pestaña "🐛 Debug" para monitorear en tiempo real

## 📚 Documentación adicional

- [Configuración Avanzada](CONFIGURACION_AVANZADA.md) - Guía completa de la interfaz
- [Scripts Discord](discord_mode.ps1) - Automatización para gaming
