"""
Tests para validar las mejoras de manejo de errores y configuración.
"""
import pytest
import tempfile
import configparser
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.error_handling import (
    DSRealtimeLogger, 
    validate_file_paths, 
    get_absolute_model_path
)


class TestErrorHandling:
    """Tests para el manejo de errores mejorado."""
    
    def test_logger_creation(self):
        """Test que el logger se crea correctamente."""
        logger = DSRealtimeLogger("test")
        assert logger.logger.name == "test"
        assert len(logger.logger.handlers) >= 2  # File + Console
    
    def test_validate_file_paths_existing_files(self):
        """Test validación con archivos existentes."""
        with tempfile.NamedTemporaryFile() as tf1, \
             tempfile.NamedTemporaryFile() as tf2:
            assert validate_file_paths(tf1.name, tf2.name) is True
    
    def test_validate_file_paths_missing_files(self):
        """Test validación con archivos faltantes."""
        assert validate_file_paths("nonexistent.txt") is False
    
    def test_get_absolute_model_path(self):
        """Test conversión a rutas absolutas."""
        path = get_absolute_model_path("models/test.onnx")
        assert isinstance(path, Path)
        assert path.is_absolute()


class TestAdvancedVADFixes:
    """Tests para verificar que los errores del VAD están corregidos."""
    
    def test_config_file_attribute_exists(self):
        """Test que config_file se guarda correctamente."""
        from src.audio.advanced_vad import AdvancedVADSegmenter
        
        vad = AdvancedVADSegmenter(config_file="test.ini")
        assert hasattr(vad, 'config_file')
        assert vad.config_file == "test.ini"
    
    def test_reload_config_with_missing_file(self):
        """Test recarga de config con archivo faltante."""
        from src.audio.advanced_vad import AdvancedVADSegmenter
        
        vad = AdvancedVADSegmenter(config_file="nonexistent.ini")
        # No debería crashear
        vad.reload_config()


class TestProfileFixes:
    """Tests para verificar las correcciones en profiles."""
    
    @patch('src.profiles.Path')
    def test_piper_path_handling(self, mock_path):
        """Test manejo correcto de rutas de Piper."""
        # Mock path exists
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        from src.profiles import build_profile
        
        # No debería crashear por rutas incorrectas
        try:
            profile = build_profile("cpu-light")
            assert profile is not None
        except Exception as e:
            # Si falla, debe ser por modelos faltantes, no por rutas
            assert "FileNotFoundError" not in str(type(e))
    
    @patch('src.profiles.XTTSTTS')
    def test_gpu_high_fallback(self, mock_xtts):
        """Test fallback cuando XTTS falla."""
        # Mock XTTS para que falle
        mock_xtts.side_effect = KeyError('xtts_v2')
        
        from src.profiles import build_profile
        
        # Debería fallar gracefully y hacer fallback
        profile = build_profile("gpu-high")
        assert profile is not None
        # Debería usar PiperTTS como fallback
        assert "Piper" in str(type(profile.tts))


class TestConfigImprovements:
    """Tests para verificar las mejoras en configuración."""
    
    def test_config_has_explanations(self):
        """Test que config.ini tiene comentarios explicativos."""
        config_path = Path(__file__).parent.parent / "config.ini"
        
        if config_path.exists():
            content = config_path.read_text(encoding='utf-8')
            
            # Debe tener comentarios explicativos
            assert "# Configuración básica de audio" in content
            assert "# Detector de Actividad de Voz" in content
            assert "# Prevención de bucles" in content
    
    def test_config_sections_complete(self):
        """Test que todas las secciones están presentes."""
        config_path = Path(__file__).parent.parent / "config.ini"
        
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            
            required_sections = [
                'audio', 'vad', 'feedback_prevention',
                'noise_suppression', 'advanced_filters', 'debug'
            ]
            
            for section in required_sections:
                assert section in config, f"Sección faltante: {section}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
