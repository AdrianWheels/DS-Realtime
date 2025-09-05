# Instrucciones para usar la nueva ventana de configuración

## 🎛️ Ventana de Configuración Avanzada en Tiempo Real

Se ha agregado una nueva interfaz de configuración que permite ajustar todos los parámetros del VAD y procesamiento de audio en tiempo real.

### ✨ Características:

1. **Botón de Configuración**: 
   - En la ventana principal, verás un nuevo botón "⚙️ Config" junto a Start/Stop
   - Al hacer clic se abre la ventana de configuración avanzada

2. **Pestañas Organizadas**:
   - 🎤 **Audio**: Configuración básica (sample rate, umbrales de voz, puerta de ruido)
   - 🗣️ **VAD**: Parámetros del WebRTC VAD (agresividad, padding, ratio de voz)
   - 🔄 **Anti-bucles**: Prevención de feedback loops (cooldowns, máximo traducciones consecutivas)
   - 🔧 **Filtros**: Filtros de frecuencia y supresión de ruido espectral
   - 🐛 **Debug**: Opciones de logging y monitor en tiempo real

3. **Recarga Automática**:
   - Los cambios se aplican automáticamente después de 1 segundo
   - No necesitas reiniciar la aplicación
   - El VAD se recarga dinámicamente con los nuevos valores

4. **Monitor en Tiempo Real**:
   - La pestaña Debug incluye un monitor que muestra la actividad del VAD
   - Logs de configuración aplicada y estado del sistema

### 🚀 Cómo usar:

1. **Inicia la aplicación**: `python -m src.main`
2. **Haz clic en "⚙️ Config"** para abrir la ventana de configuración
3. **Ajusta los parámetros** usando sliders y controles
4. **Observa el monitor** en la pestaña Debug para ver los efectos en tiempo real
5. **Los cambios se guardan automáticamente** en `config.ini`

### ⚡ Configuraciones Recomendadas:

**Para Discord (evitar bucles):**
- Umbral de Voz: -30dB
- Puerta de Ruido: -5dB
- Agresividad VAD: 3
- Cooldown: 500ms
- Máx. traducciones consecutivas: 3

**Para mejor calidad de voz:**
- Agresividad VAD: 2
- Padding: 600ms
- Filtro pasa-alto: 80Hz
- Supresión espectral: Habilitada

### 🔧 Parámetros Clave:

- **voice_threshold_db**: Nivel mínimo para considerar voz (-40 a 0 dB)
- **noise_gate_db**: Puerta de ruido para filtrar sonido de fondo (-80 a -10 dB)
- **aggressiveness**: Sensibilidad del VAD (0=menos sensible, 3=más sensible)
- **cooldown_after_translation_ms**: Pausa después de cada traducción
- **max_consecutive_translations**: Límite de traducciones seguidas antes de pausa

¡La configuración ahora es totalmente interactiva y en tiempo real! 🎉
