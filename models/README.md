# Carpeta de Modelos - LocalVoiceTranslate

Esta carpeta contiene los modelos necesarios para el funcionamiento de LocalVoiceTranslate.

## 📁 Estructura de Directorios

### `/piper/`
Modelos de Piper TTS para síntesis de voz en inglés.

**Archivo requerido:**
- `en_US-lessac-medium.onnx` - Modelo principal de Piper TTS
- `en_US-lessac-medium.onnx.json` - Configuración del modelo

**Descarga:**
```bash
# Desde el repositorio oficial de Piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### `/vosk-model-small-es-0.42/`
Modelo de Vosk para reconocimiento de voz en español (opcional).

**Descarga:**
```bash
# Modelo pequeño de español para Vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
# Extraer en esta carpeta
```

## 📝 Notas

- Los modelos de **Piper TTS** son necesarios para los perfiles `gpu-medium` y `cpu-medium`
- El modelo de **Vosk** es opcional - el sistema puede usar FasterWhisper como alternativa
- Si no tienes los modelos locales, el sistema intentará usar alternativas online (menos eficiente)

## 🔧 Solución de Problemas

Si ves errores como:
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/piper/en_US-lessac-medium.onnx.json'
```

Significa que necesitas descargar los modelos de Piper TTS en esta carpeta.
