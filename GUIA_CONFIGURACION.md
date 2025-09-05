# 🔧 Guía de Configuración Avanzada - DSRealtime

## 📖 Introducción

DSRealtime es un traductor de voz en tiempo real que convierte audio en español a inglés. Este documento explica todas las opciones de configuración disponibles en `config.ini`.

## 🎵 Configuración de Audio

### Parámetros Básicos

- **`sample_rate`**: Frecuencia de muestreo (16000 Hz recomendado)
- **`frame_ms`**: Duración de frames de audio (20ms es óptimo)
- **`min_speech_duration_ms`**: Duración mínima para considerar como habla
- **`max_silence_duration_ms`**: Tiempo máximo de silencio antes de procesar

### Umbrales de Detección

- **`voice_threshold_db`**: Nivel mínimo de voz (-30 dB recomendado)
  - Valores más altos: más restrictivo, menos ruido de fondo
  - Valores más bajos: más permisivo, puede captar más ruido

- **`noise_gate_db`**: Puerta de ruido (-45 dB recomendado)
  - Audio por debajo de este nivel se ignora completamente

## 🎤 Detector de Actividad de Voz (VAD)

### Configuración Principal

- **`aggressiveness`**: Sensibilidad del VAD (0-3)
  - 0: Muy permisivo, detecta hasta susurros
  - 1: Permisivo, para ambientes silenciosos
  - 2: Moderado, para uso general
  - 3: Estricto, solo voz clara y fuerte

- **`padding_ms`**: Tiempo de padding alrededor de segmentos detectados
- **`voice_ratio_threshold`**: Proporción de frames con voz para activar

## 🔄 Prevención de Bucles

Evita que el sistema traduzca su propia salida:

- **`enable_feedback_detection`**: Activar/desactivar prevención
- **`max_consecutive_translations`**: Máximo traducciones seguidas
- **`cooldown_after_translation_ms`**: Pausa tras cada traducción
- **`similarity_threshold`**: Umbral para detectar repeticiones

## 🔊 Supresión de Ruido

### Filtros Espectrales

- **`enable_spectral_subtraction`**: Sustracción espectral de ruido
- **`noise_reduction_factor`**: Intensidad de reducción (0.0-1.0)
- **`smoothing_factor`**: Suavizado espectral

### Filtros de Frecuencia

- **`high_pass_cutoff_hz`**: Elimina frecuencias bajas (80 Hz)
- **`low_pass_cutoff_hz`**: Elimina frecuencias altas (8000 Hz)
- **`adaptive_gain_control`**: Control automático de volumen

## 🚀 Optimización de Rendimiento

### Perfiles de Hardware

El sistema detecta automáticamente el hardware y selecciona el perfil óptimo:

- **`cpu-light`**: Para PCs básicas
- **`cpu-medium`**: Para PCs con buen procesador
- **`gpu-medium`**: Para PCs con GPU dedicada (6+ GB VRAM)
- **`gpu-high`**: Para PCs gaming/workstation (16+ GB VRAM)

### Configuración Manual

```ini
[performance]
use_gpu = auto          # auto, true, false
max_workers = 4         # Número de workers
chunk_size = 1024       # Tamaño de chunks
```

## 🐛 Depuración y Logs

### Opciones de Debug

- **`log_audio_levels`**: Registra niveles de audio
- **`log_vad_decisions`**: Registra decisiones del VAD
- **`save_audio_clips`**: Guarda clips para análisis

### Archivos de Log

- `ui_debug.log`: Logs de la interfaz
- Console: Logs en tiempo real

## 🎯 Configuraciones Recomendadas

### Para Ambientes Silenciosos
```ini
[vad]
aggressiveness = 1
[audio]
voice_threshold_db = -40
noise_gate_db = -50
```

### Para Ambientes Ruidosos
```ini
[vad]
aggressiveness = 3
[audio]
voice_threshold_db = -20
noise_gate_db = -35
```

### Para Prevenir Eco en Discord
```ini
[feedback_prevention]
enable_feedback_detection = true
max_consecutive_translations = 2
cooldown_after_translation_ms = 750
```

## 🔧 Solución de Problemas

### Problema: No detecta mi voz
**Solución**: Reducir `voice_threshold_db` y `aggressiveness`

### Problema: Detecta demasiado ruido
**Solución**: Aumentar `voice_threshold_db` y `noise_gate_db`

### Problema: Corta palabras
**Solución**: Aumentar `padding_ms` y reducir `max_silence_duration_ms`

### Problema: Bucles de audio
**Solución**: Activar `feedback_prevention` y ajustar `cooldown_after_translation_ms`

## 📧 Soporte

Para reportar problemas o sugerir mejoras, revisa los logs en `ui_debug.log` e incluye tu configuración actual.
