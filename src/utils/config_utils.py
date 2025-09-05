"""
Utilidades para manejo de configuración con comentarios en línea.
"""
import configparser
from pathlib import Path
from typing import Any, Union


class CommentedConfigParser(configparser.ConfigParser):
    """ConfigParser que maneja comentarios en línea correctamente."""
    
    def get(self, section: str, option: str, **kwargs) -> str:
        """Override get para remover comentarios en línea."""
        value = super().get(section, option, **kwargs)
        # Remover comentarios después de #
        if '#' in value:
            value = value.split('#')[0]
        return value.strip()
    
    def getint(self, section: str, option: str, **kwargs) -> int:
        """Override getint para manejar comentarios."""
        value = self.get(section, option, **kwargs)
        return int(value)
    
    def getfloat(self, section: str, option: str, **kwargs) -> float:
        """Override getfloat para manejar comentarios."""
        value = self.get(section, option, **kwargs)
        return float(value)
    
    def getboolean(self, section: str, option: str, **kwargs) -> bool:
        """Override getboolean para manejar comentarios."""
        value = self.get(section, option, **kwargs)
        return value.lower() in ('true', 'yes', '1', 'on')


def load_config(config_file: Union[str, Path] = "config.ini") -> CommentedConfigParser:
    """Carga configuración con manejo de comentarios."""
    config = CommentedConfigParser()
    config_path = Path(config_file)
    
    if config_path.exists():
        try:
            config.read(config_path, encoding='utf-8')
        except Exception as e:
            print(f"[CONFIG] Error leyendo {config_file}: {e}")
            # Cargar valores por defecto
            load_default_config(config)
    else:
        print(f"[CONFIG] {config_file} no encontrado, usando valores por defecto")
        load_default_config(config)
    
    return config


def load_default_config(config: CommentedConfigParser):
    """Carga configuración por defecto."""
    config.read_dict({
        'audio': {
            'sample_rate': '16000',
            'frame_ms': '20',
            'min_speech_duration_ms': '200',
            'max_silence_duration_ms': '300',
            'voice_threshold_db': '-30',
            'noise_gate_db': '-45'
        },
        'vad': {
            'aggressiveness': '3',
            'padding_ms': '600',
            'voice_ratio_threshold': '0.8'
        },
        'feedback_prevention': {
            'enable_feedback_detection': 'true',
            'feedback_detection_window_ms': '1000',
            'max_consecutive_translations': '3',
            'cooldown_after_translation_ms': '500',
            'similarity_threshold': '0.8'
        },
        'noise_suppression': {
            'enable_spectral_subtraction': 'true',
            'noise_reduction_factor': '0.5',
            'smoothing_factor': '0.8'
        },
        'advanced_filters': {
            'high_pass_cutoff_hz': '80',
            'low_pass_cutoff_hz': '8000',
            'adaptive_gain_control': 'true',
            'enable_noise_suppression': 'true',
            'spectral_floor_db': '-41',
            'noise_reduction_factor': '0.5'
        },
        'debug': {
            'log_audio_levels': 'true',
            'log_vad_decisions': 'true',
            'save_audio_clips': 'false'
        },
        'models': {
            'asr_model_size': 'small',
            'tts_voice': 'en_US-lessac-medium',
            'translation_model': 'facebook/nllb-200-distilled-600M'
        },
        'performance': {
            'use_gpu': 'auto',
            'max_workers': '4',
            'chunk_size': '1024'
        }
    })


def save_config_value(config_file: Union[str, Path], section: str, 
                     option: str, value: Any):
    """Guarda un valor específico en el config manteniendo comentarios."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        return
    
    # Leer archivo línea por línea para preservar comentarios
    lines = []
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar la línea a modificar
    current_section = None
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Detectar secciones
        if line_stripped.startswith('[') and line_stripped.endswith(']'):
            current_section = line_stripped[1:-1]
            continue
        
        # Modificar valor en la sección correcta
        if current_section == section and '=' in line:
            key = line.split('=')[0].strip()
            if key == option:
                # Preservar comentario si existe
                comment = ""
                if '#' in line:
                    comment = " " + line.split('#', 1)[1].rstrip()
                
                # Actualizar línea
                lines[i] = f"{option} = {value}{comment}\n"
                break
    
    # Escribir archivo actualizado
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
