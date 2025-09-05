# Changelog

Todas las mejoras notables de LocalVoiceTranslate están documentadas en este archivo.

## [2.0.0] - 2025-09-05

### 🎛️ Agregado

#### Ventana de Configuración Avanzada
- **Nueva interfaz de configuración** con 5 pestañas organizadas:
  - 🎤 **Audio**: Configuración básica (sample rate, umbrales, duraciones)
  - 🗣️ **VAD**: Parámetros WebRTC VAD (agresividad, padding, ratios)
  - 🔄 **Anti-bucles**: Prevención feedback (cooldowns, límites, detección)
  - 🔧 **Filtros**: Procesamiento avanzado (pasa-alto/bajo, supresión espectral)
  - 🐛 **Debug**: Logging y monitor en tiempo real

#### Recarga en Tiempo Real
- **Aplicación inmediata** de cambios sin reiniciar la aplicación
- **Auto-guardado** de configuración tras 1 segundo de inactividad
- **Comunicación dinámica** entre interfaz y pipeline de audio

#### Sistema Anti-Feedback Mejorado
- **Detección inteligente** de bucles de retroalimentación
- **Cooldowns configurables** después de cada traducción
- **Límites de traducciones consecutivas** para prevenir spam
- **Análisis de similitud** de texto para detectar bucles

#### Monitor en Tiempo Real
- **Log visual** en la pestaña Debug mostrando:
  - Estado de configuración aplicada
  - Decisiones del VAD en tiempo real
  - Niveles de audio y umbrales
  - Detección de feedback y cooldowns

### 🔧 Mejorado

#### Interfaz de Usuario
- **Botón "⚙️ Config"** agregado a la ventana principal
- **Auto-selección mejorada** de dispositivos para Discord:
  - Entrada: Logitech G535 Gaming Headset (automático)
  - Salida: CABLE Input device 6 (corregido del 40)
- **Feedback visual** mejorado para indicadores de audio

#### VAD Avanzado (`AdvancedVADSegmenter`)
- **Método `reload_config()`** para recarga dinámica
- **Supresión espectral** de ruido de fondo
- **Umbrales configurables** para voz y puerta de ruido
- **Logging detallado** para debugging

#### Configuración Persistente
- **Archivo `config.ini`** organizado en secciones temáticas
- **Valores por defecto** optimizados para Discord
- **Validación de tipos** para prevenir errores de configuración

### 🛠️ Técnico

#### Arquitectura
- **Comunicación UI-Pipeline** mejorada para cambios en tiempo real
- **Separación de responsabilidades** entre configuración y procesamiento
- **Gestión de estado** más robusta para el VAD

#### Archivos Nuevos
- `src/ui/config_window.py` - Interfaz de configuración avanzada
- `CONFIGURACION_AVANZADA.md` - Documentación de usuario
- `CHANGELOG.md` - Este archivo

#### Archivos Modificados
- `src/ui/main_window.py` - Integración botón Config y recarga
- `src/main.py` - Comunicación con VAD para recarga dinámica
- `src/audio/advanced_vad.py` - Método reload_config()
- `README.md` - Documentación actualizada con nuevas características
- `config.ini` - Estructura mejorada y valores optimizados

### 🎯 Configuraciones Optimizadas

#### Para Discord (Anti-feedback)
```ini
voice_threshold_db = -30
noise_gate_db = -5
aggressiveness = 3
cooldown_after_translation_ms = 500
max_consecutive_translations = 3
```

#### Para Máxima Calidad
```ini
aggressiveness = 2
padding_ms = 600
enable_spectral_subtraction = true
high_pass_cutoff_hz = 80
adaptive_gain_control = true
```

---

## [1.0.0] - 2025-08-XX

### Agregado
- Pipeline de traducción offline ES→EN
- WebRTC VAD básico para segmentación de voz
- Interfaz gráfica con PySide6
- Soporte CUDA para GPU acceleration
- Integración con VB-Audio CABLE para Discord
- Modelos: FasterWhisper + NLLB + PiperTTS
