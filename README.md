# 🎤 DSRealtime - Traductor de Voz en Tiempo Real

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**DSRealtime** es un traductor de voz en tiempo real que convierte audio en español a inglés usando IA local. Perfecto para gaming, streaming y comunicación internacional.

## ✨ Características Principales

- 🎯 **Traducción en Tiempo Real**: Español → Inglés con latencia mínima
- 🤖 **IA 100% Local**: Sin conexión a internet requerida
- 🎮 **Optimizado para Gaming**: Compatible con Discord, OBS, etc.
- 🔧 **Configuración Avanzada**: Control total sobre todos los parámetros
- 🛡️ **Prevención de Bucles**: Sistema inteligente anti-eco
- 💻 **Interfaz Gráfica**: UI moderna con PySide6
- ⚡ **Multi-perfil**: Soporte CPU y GPU automático

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio
```bash
git clone https://github.com/AdrianWheels/DSRealtime.git
cd DSRealtime
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Validar Sistema
```bash
python validate_system.py
```

### 4. ¡Ejecutar!

**Opción 1: Interfaz Gráfica (Recomendado)**
```bash
python -m src.main
```

**Opción 2: Script de Control Centralizado**
```bash
.\dsrealtime.ps1
```

**Opción 3: Línea de Comandos Directa**
```bash
python -m src.main --nogui --profile cpu-medium --input 8 --output 6
```

## � Uso Rápido

### Script Centralizado (Recomendado)
```bash
.\dsrealtime.ps1
```
Menú interactivo con todas las opciones:
- Configuraciones predefinidas para Discord
- Modo anti-bucles avanzado
- Validación del sistema
- Gestión de dispositivos

### Interfaz Gráfica
```bash
python -m src.main
```
- **Botón "⚙️ Config"** para configuración avanzada en tiempo real
- Auto-selección de dispositivos optimizada para Discord
- Monitor VAD en vivo para debugging

```ini
[audio]
voice_threshold_db = -30    # Sensibilidad del micrófono
noise_gate_db = -45        # Filtro de ruido de fondo

[vad]
aggressiveness = 3         # Detección de voz: 0=permisivo, 3=estricto

[feedback_prevention]
enable_feedback_detection = true    # Prevenir bucles de audio
cooldown_after_translation_ms = 500 # Pausa entre traducciones
```

### Configuración Avanzada

Para opciones avanzadas, consulta [GUIA_CONFIGURACION.md](GUIA_CONFIGURACION.md)

## 🎮 Uso con Discord

### Opción 1: VB-Cable (Recomendado)
1. Instala [VB-Audio Cable](https://vb-audio.com/Cable/)
2. Configura DSRealtime para enviar a "CABLE Input"
3. En Discord, selecciona "CABLE Output" como micrófono

### Opción 2: Modo Discord Directo
```bash
./discord_mode.ps1
```

## 📊 Perfiles de Rendimiento

| Perfil | Hardware | Latencia | Calidad |
|--------|----------|----------|---------|
| `cpu-light` | CPU básica | ~800ms | Buena |
| `cpu-medium` | CPU potente | ~500ms | Muy buena |
| `gpu-medium` | GPU 6+ GB | ~300ms | Excelente |
| `gpu-high` | GPU 16+ GB | ~200ms | Premium |

## 🔧 Solución de Problemas

### Errores Comunes

1. **"FileNotFoundError: models/piper/..."**
   ```bash
   # Descargar modelos faltantes
   python download_models.py
   ```

2. **"No detecta mi voz"**
   - Reducir `voice_threshold_db` en config.ini
   - Verificar micrófono con `python list_devices.py`

3. **"Bucles de audio en Discord"**
   - Activar `feedback_prevention` en config.ini
   - Usar `discord_anti_bucles.ps1`

### Validación del Sistema

Ejecuta el validador para diagnosticar problemas:

```bash
python validate_system.py
```

## 📁 Estructura del Proyecto

```
DSRealtime/
├── src/
│   ├── main.py              # Punto de entrada principal
│   ├── profiles.py          # Gestión de perfiles de hardware
│   ├── audio/               # Procesamiento de audio
│   │   ├── capture.py       # Captura de micrófono
│   │   ├── advanced_vad.py  # Detección de voz avanzada
│   │   └── sink.py          # Salida de audio
│   ├── pipeline/            # Pipeline de IA
│   │   ├── asr.py           # Reconocimiento de voz
│   │   ├── translate.py     # Traducción
│   │   └── tts.py           # Síntesis de voz
│   ├── ui/                  # Interfaz gráfica
│   └── utils/               # Utilidades
├── models/                  # Modelos de IA locales
├── tests/                   # Tests automatizados
├── config.ini              # Configuración principal
├── validate_system.py      # Validador del sistema
└── requirements.txt        # Dependencias Python
```

## 🧪 Testing

Ejecutar todos los tests:

```bash
python -m pytest tests/ -v
```

Tests específicos:

```bash
python -m pytest tests/test_improvements.py -v
```

## 📚 Documentación

- [📖 Guía de Configuración Avanzada](GUIA_CONFIGURACION.md)
- [🔧 Configuración Avanzada Original](CONFIGURACION_AVANZADA.md)
- [📝 Changelog](CHANGELOG.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [Piper TTS](https://github.com/rhasspy/piper) por la síntesis de voz
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) por el reconocimiento
- [NLLB](https://github.com/facebookresearch/fairseq/tree/nllb) por la traducción
- La comunidad de Python por las increíbles librerías

## 📬 Soporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/AdrianWheels/DSRealtime/issues)
- 💬 **Discusiones**: [GitHub Discussions](https://github.com/AdrianWheels/DSRealtime/discussions)
- 📧 **Email**: [tu-email@ejemplo.com](mailto:tu-email@ejemplo.com)

---

⭐ **¡Si te gusta el proyecto, dale una estrella en GitHub!** ⭐
