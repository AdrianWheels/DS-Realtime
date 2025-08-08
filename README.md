# LocalVoiceTranslate

Traductor de voz local ES→EN, 100 % offline.

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

