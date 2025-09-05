"""
Utilidades para manejo robusto de errores y logging mejorado.
"""
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class DSRealtimeLogger:
    """Logger centralizado para DSRealtime con manejo de errores mejorado."""
    
    def __init__(self, name: str = "DSRealtime"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers de logging."""
        # Handler para archivo
        log_file = Path("dsrealtime.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def error_with_context(self, message: str, error: Exception, 
                          context: Optional[dict] = None):
        """Log error with full context and traceback."""
        error_info = {
            'message': message,
            'error_type': type(error).__name__,
            'error_str': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        if context:
            error_info.update(context)
        
        self.logger.error(f"ERROR: {message}")
        self.logger.error(f"Type: {error_info['error_type']}")
        self.logger.error(f"Details: {error_info['error_str']}")
        self.logger.debug(f"Traceback:\n{error_info['traceback']}")
        
        if context:
            self.logger.debug(f"Context: {context}")
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


def safe_file_operation(operation, *args, **kwargs):
    """Wrapper para operaciones de archivo con manejo seguro de errores."""
    logger = DSRealtimeLogger()
    
    try:
        return operation(*args, **kwargs)
    except FileNotFoundError as e:
        logger.error_with_context(
            f"Archivo no encontrado en operación: {operation.__name__}",
            e,
            {'args': args, 'kwargs': kwargs}
        )
        raise
    except PermissionError as e:
        logger.error_with_context(
            f"Sin permisos para operación: {operation.__name__}",
            e,
            {'args': args, 'kwargs': kwargs}
        )
        raise
    except Exception as e:
        logger.error_with_context(
            f"Error inesperado en operación: {operation.__name__}",
            e,
            {'args': args, 'kwargs': kwargs}
        )
        raise


def validate_file_paths(*paths: str) -> bool:
    """Valida que todos los archivos existan."""
    logger = DSRealtimeLogger()
    
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Archivo no encontrado: {path.absolute()}")
            return False
        if not path.is_file():
            logger.warning(f"La ruta no es un archivo: {path.absolute()}")
            return False
    
    return True


def get_absolute_model_path(relative_path: str) -> Path:
    """Convierte rutas relativas de modelos a absolutas."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    return project_root / relative_path
