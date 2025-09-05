#!/usr/bin/env python3
"""
Script de validación del sistema DSRealtime.
Verifica que todos los componentes estén correctamente configurados.
"""
import sys
import os
import configparser
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_python_environment():
    """Verifica el entorno Python."""
    console.print("\n[bold blue]🐍 Verificando Entorno Python[/bold blue]")
    
    # Versión de Python
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        console.print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        console.print(f"❌ Python {version.major}.{version.minor}.{version.micro} "
                     "(Requerido: Python 3.8+)")
        return False
    
    # Dependencias críticas
    critical_deps = [
        'torch', 'sounddevice', 'PySide6', 'qasync', 'rich',
        'numpy', 'webrtcvad', 'faster_whisper', 'piper'
    ]
    
    missing_deps = []
    for dep in critical_deps:
        try:
            __import__(dep)
            console.print(f"✅ {dep}")
        except ImportError:
            console.print(f"❌ {dep} (faltante)")
            missing_deps.append(dep)
    
    if missing_deps:
        console.print(f"\n[red]Dependencias faltantes: {', '.join(missing_deps)}[/red]")
        return False
    
    return True


def check_model_files():
    """Verifica archivos de modelos."""
    console.print("\n[bold blue]🤖 Verificando Modelos[/bold blue]")
    
    project_root = Path(__file__).parent
    models_dir = project_root / "models"
    
    # Modelo Piper
    piper_model = models_dir / "piper" / "en_US-lessac-medium.onnx"
    piper_config = models_dir / "piper" / "en_US-lessac-medium.onnx.json"
    
    if piper_model.exists() and piper_config.exists():
        size_mb = piper_model.stat().st_size / (1024 * 1024)
        console.print(f"✅ Piper TTS: {piper_model.name} ({size_mb:.1f} MB)")
    else:
        console.print(f"❌ Piper TTS: Archivos faltantes")
        console.print(f"   Esperado: {piper_model}")
        console.print(f"   Esperado: {piper_config}")
    
    # Modelo Vosk (opcional)
    vosk_model = models_dir / "vosk-model-small-es-0.42"
    if vosk_model.exists():
        console.print(f"✅ Vosk ASR: {vosk_model.name}")
    else:
        console.print(f"⚠️  Vosk ASR: No encontrado (opcional)")
    
    return True


def check_configuration():
    """Verifica archivo de configuración."""
    console.print("\n[bold blue]⚙️  Verificando Configuración[/bold blue]")
    
    config_file = Path(__file__).parent / "config.ini"
    if not config_file.exists():
        console.print("❌ config.ini no encontrado")
        return False
    
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
    except Exception as e:
        console.print(f"❌ Error leyendo config.ini: {e}")
        return False
    
    # Secciones requeridas
    required_sections = [
        'audio', 'vad', 'feedback_prevention', 
        'noise_suppression', 'advanced_filters', 'debug'
    ]
    
    for section in required_sections:
        if section in config:
            console.print(f"✅ Sección [{section}]")
        else:
            console.print(f"❌ Sección faltante: [{section}]")
    
    # Valores críticos
    try:
        # Obtener valor sin comentarios
        sample_rate_str = config.get('audio', 'sample_rate').split('#')[0].strip()
        sample_rate = int(sample_rate_str)
        if sample_rate == 16000:
            console.print(f"✅ Sample rate: {sample_rate} Hz")
        else:
            console.print(f"⚠️  Sample rate: {sample_rate} Hz (recomendado: 16000)")
        
        aggressiveness_str = config.get('vad', 'aggressiveness').split('#')[0].strip()
        aggressiveness = int(aggressiveness_str)
        if 0 <= aggressiveness <= 3:
            console.print(f"✅ VAD aggressiveness: {aggressiveness}")
        else:
            console.print(f"❌ VAD aggressiveness inválido: {aggressiveness}")
    
    except Exception as e:
        console.print(f"❌ Error validando parámetros: {e}")
    
    return True


def check_audio_devices():
    """Verifica dispositivos de audio."""
    console.print("\n[bold blue]🔊 Verificando Dispositivos de Audio[/bold blue]")
    
    try:
        import sounddevice as sd
        
        # Dispositivos de entrada
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        output_devices = [d for d in devices if d['max_output_channels'] > 0]
        
        console.print(f"✅ Dispositivos de entrada: {len(input_devices)}")
        console.print(f"✅ Dispositivos de salida: {len(output_devices)}")
        
        # VB-Cable check
        vb_cable = any("CABLE" in d['name'] for d in output_devices)
        if vb_cable:
            console.print("✅ VB-Cable detectado")
        else:
            console.print("⚠️  VB-Cable no detectado (recomendado para Discord)")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Error verificando audio: {e}")
        return False


def check_gpu_support():
    """Verifica soporte GPU."""
    console.print("\n[bold blue]🎮 Verificando Soporte GPU[/bold blue]")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            memory = torch.cuda.get_device_properties(0).total_memory
            memory_gb = memory / (1024**3)
            
            console.print(f"✅ GPU disponible: {gpu_name}")
            console.print(f"✅ VRAM: {memory_gb:.1f} GB")
            
            if memory_gb >= 6:
                console.print("✅ Suficiente VRAM para perfiles GPU")
            else:
                console.print("⚠️  VRAM limitada, usar perfiles CPU")
        else:
            console.print("⚠️  No hay GPU CUDA disponible")
            console.print("ℹ️  Se usarán perfiles CPU")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Error verificando GPU: {e}")
        return False


def generate_report():
    """Genera reporte completo del sistema."""
    console.print(Panel.fit(
        "[bold green]🚀 VALIDACIÓN DEL SISTEMA DSREALTIME[/bold green]",
        border_style="green"
    ))
    
    checks = [
        ("Entorno Python", check_python_environment),
        ("Archivos de Modelos", check_model_files),
        ("Configuración", check_configuration),
        ("Dispositivos de Audio", check_audio_devices),
        ("Soporte GPU", check_gpu_support),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, "✅ Correcto" if result else "❌ Error"))
        except Exception as e:
            results.append((name, f"❌ Excepción: {e}"))
    
    # Tabla resumen
    table = Table(title="Resumen de Validación")
    table.add_column("Componente", style="cyan")
    table.add_column("Estado", style="bold")
    
    for name, status in results:
        table.add_row(name, status)
    
    console.print("\n")
    console.print(table)
    
    # Recomendaciones
    all_passed = all("✅" in status for _, status in results)
    
    if all_passed:
        console.print("\n[bold green]🎉 ¡Sistema completamente funcional![/bold green]")
        console.print("Puedes ejecutar el traductor con:")
        console.print("  [cyan]python -m src.main[/cyan]")
    else:
        console.print("\n[bold yellow]⚠️  Se encontraron algunos problemas[/bold yellow]")
        console.print("Consulta la documentación o instala las dependencias faltantes.")


if __name__ == "__main__":
    generate_report()
