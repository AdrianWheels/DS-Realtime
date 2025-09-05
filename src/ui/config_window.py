import configparser
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QTabWidget, QWidget, QGridLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal


class ConfigWindow(QDialog):
    """Ventana de configuración avanzada en tiempo real"""
    config_changed = Signal(dict)  # Señal para notificar cambios
    
    def __init__(self, config_path='config.ini', parent=None):
        super().__init__(parent)
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.load_config()
        
        self.setWindowTitle('Configuración Avanzada - LocalVoiceTranslate')
        self.setMinimumSize(600, 700)
        self.resize(800, 800)
        
        # Timer para aplicar cambios automáticamente
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.save_and_apply_config)
        
        self.setup_ui()
        self.populate_values()
        
    def load_config(self):
        """Cargar configuración desde archivo"""
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            # Valores por defecto si no existe el archivo
            self.create_default_config()
    
    def create_default_config(self):
        """Crear configuración por defecto"""
        self.config['audio'] = {
            'sample_rate': '16000',
            'frame_ms': '20',
            'min_speech_duration_ms': '300',
            'max_silence_duration_ms': '800',
            'voice_threshold_db': '-30',
            'noise_gate_db': '-45'
        }
        self.config['vad'] = {
            'aggressiveness': '3',
            'padding_ms': '600',
            'voice_ratio_threshold': '0.8'
        }
        self.config['feedback_prevention'] = {
            'enable_feedback_detection': 'true',
            'feedback_detection_window_ms': '1000',
            'max_consecutive_translations': '3',
            'cooldown_after_translation_ms': '500',
            'similarity_threshold': '0.8'
        }
        self.config['noise_suppression'] = {
            'enable_spectral_subtraction': 'true',
            'noise_reduction_factor': '0.5',
            'smoothing_factor': '0.8'
        }
        self.config['advanced_filters'] = {
            'high_pass_cutoff_hz': '80',
            'low_pass_cutoff_hz': '8000',
            'adaptive_gain_control': 'true',
            'enable_noise_suppression': 'true',
            'spectral_floor_db': '-60'
        }
        self.config['debug'] = {
            'log_audio_levels': 'false',
            'log_vad_decisions': 'false',
            'save_audio_clips': 'false'
        }
        
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Crear pestañas
        tab_widget = QTabWidget()
        
        # Pestaña de Audio
        audio_tab = self.create_audio_tab()
        tab_widget.addTab(audio_tab, '🎤 Audio')
        
        # Pestaña de VAD
        vad_tab = self.create_vad_tab()
        tab_widget.addTab(vad_tab, '🗣️ VAD')
        
        # Pestaña de Anti-bucles
        feedback_tab = self.create_feedback_tab()
        tab_widget.addTab(feedback_tab, '🔄 Anti-bucles')
        
        # Pestaña de Filtros
        filters_tab = self.create_filters_tab()
        tab_widget.addTab(filters_tab, '🔧 Filtros')
        
        # Pestaña de Debug
        debug_tab = self.create_debug_tab()
        tab_widget.addTab(debug_tab, '🐛 Debug')
        
        layout.addWidget(tab_widget)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton('🔄 Restaurar Defecto')
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.save_btn = QPushButton('💾 Guardar')
        self.save_btn.clicked.connect(self.save_and_apply_config)
        
        self.apply_btn = QPushButton('✅ Aplicar')
        self.apply_btn.clicked.connect(self.apply_config)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel('Configuración cargada')
        self.status_label.setStyleSheet('color: green; font-size: 12px;')
        layout.addWidget(self.status_label)
        
    def create_audio_tab(self):
        """Crear pestaña de configuración de audio"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de configuración básica
        basic_group = QGroupBox('Configuración Básica de Audio')
        basic_layout = QGridLayout(basic_group)
        
        # Sample Rate
        basic_layout.addWidget(QLabel('Sample Rate (Hz):'), 0, 0)
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(8000, 48000)
        self.sample_rate_spin.setSingleStep(8000)
        self.sample_rate_spin.valueChanged.connect(self.on_value_changed)
        basic_layout.addWidget(self.sample_rate_spin, 0, 1)
        
        # Frame MS
        basic_layout.addWidget(QLabel('Frame Duration (ms):'), 1, 0)
        self.frame_ms_spin = QSpinBox()
        self.frame_ms_spin.setRange(10, 100)
        self.frame_ms_spin.setSingleStep(10)
        self.frame_ms_spin.valueChanged.connect(self.on_value_changed)
        basic_layout.addWidget(self.frame_ms_spin, 1, 1)
        
        layout.addWidget(basic_group)
        
        # Grupo de detección de voz
        voice_group = QGroupBox('Detección de Voz')
        voice_layout = QGridLayout(voice_group)
        
        # Voice Threshold
        voice_layout.addWidget(QLabel('Umbral de Voz (dB):'), 0, 0)
        self.voice_threshold_slider = QSlider(Qt.Horizontal)
        self.voice_threshold_slider.setRange(-60, 0)
        self.voice_threshold_slider.valueChanged.connect(self.on_slider_changed)
        self.voice_threshold_label = QLabel('-30')
        voice_layout.addWidget(self.voice_threshold_slider, 0, 1)
        voice_layout.addWidget(self.voice_threshold_label, 0, 2)
        
        # Noise Gate
        voice_layout.addWidget(QLabel('Puerta de Ruido (dB):'), 1, 0)
        self.noise_gate_slider = QSlider(Qt.Horizontal)
        self.noise_gate_slider.setRange(-80, -10)
        self.noise_gate_slider.valueChanged.connect(self.on_slider_changed)
        self.noise_gate_label = QLabel('-45')
        voice_layout.addWidget(self.noise_gate_slider, 1, 1)
        voice_layout.addWidget(self.noise_gate_label, 1, 2)
        
        # Min Speech Duration
        voice_layout.addWidget(QLabel('Duración Mínima de Voz (ms):'), 2, 0)
        self.min_speech_spin = QSpinBox()
        self.min_speech_spin.setRange(100, 2000)
        self.min_speech_spin.setSingleStep(50)
        self.min_speech_spin.valueChanged.connect(self.on_value_changed)
        voice_layout.addWidget(self.min_speech_spin, 2, 1)
        
        # Max Silence Duration
        voice_layout.addWidget(QLabel('Duración Máxima de Silencio (ms):'), 3, 0)
        self.max_silence_spin = QSpinBox()
        self.max_silence_spin.setRange(200, 3000)
        self.max_silence_spin.setSingleStep(100)
        self.max_silence_spin.valueChanged.connect(self.on_value_changed)
        voice_layout.addWidget(self.max_silence_spin, 3, 1)
        
        layout.addWidget(voice_group)
        layout.addStretch()
        
        return widget
        
    def create_vad_tab(self):
        """Crear pestaña de configuración VAD"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        vad_group = QGroupBox('WebRTC VAD Configuración')
        vad_layout = QGridLayout(vad_group)
        
        # Aggressiveness
        vad_layout.addWidget(QLabel('Agresividad (0-3):'), 0, 0)
        self.aggressiveness_slider = QSlider(Qt.Horizontal)
        self.aggressiveness_slider.setRange(0, 3)
        self.aggressiveness_slider.valueChanged.connect(self.on_slider_changed)
        self.aggressiveness_label = QLabel('3')
        vad_layout.addWidget(self.aggressiveness_slider, 0, 1)
        vad_layout.addWidget(self.aggressiveness_label, 0, 2)
        
        # Padding
        vad_layout.addWidget(QLabel('Padding (ms):'), 1, 0)
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(100, 2000)
        self.padding_spin.setSingleStep(100)
        self.padding_spin.valueChanged.connect(self.on_value_changed)
        vad_layout.addWidget(self.padding_spin, 1, 1)
        
        # Voice Ratio Threshold
        vad_layout.addWidget(QLabel('Umbral de Ratio de Voz:'), 2, 0)
        self.voice_ratio_spin = QDoubleSpinBox()
        self.voice_ratio_spin.setRange(0.1, 1.0)
        self.voice_ratio_spin.setSingleStep(0.1)
        self.voice_ratio_spin.setDecimals(1)
        self.voice_ratio_spin.valueChanged.connect(self.on_value_changed)
        vad_layout.addWidget(self.voice_ratio_spin, 2, 1)
        
        layout.addWidget(vad_group)
        layout.addStretch()
        
        return widget
        
    def create_feedback_tab(self):
        """Crear pestaña de prevención de bucles"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        feedback_group = QGroupBox('Prevención de Bucles de Retroalimentación')
        feedback_layout = QGridLayout(feedback_group)
        
        # Enable Feedback Detection
        self.feedback_detection_check = QCheckBox('Habilitar Detección de Bucles')
        self.feedback_detection_check.stateChanged.connect(self.on_checkbox_changed)
        feedback_layout.addWidget(self.feedback_detection_check, 0, 0, 1, 2)
        
        # Detection Window
        feedback_layout.addWidget(QLabel('Ventana de Detección (ms):'), 1, 0)
        self.detection_window_spin = QSpinBox()
        self.detection_window_spin.setRange(500, 5000)
        self.detection_window_spin.setSingleStep(250)
        self.detection_window_spin.valueChanged.connect(self.on_value_changed)
        feedback_layout.addWidget(self.detection_window_spin, 1, 1)
        
        # Max Consecutive Translations
        feedback_layout.addWidget(QLabel('Máx. Traducciones Consecutivas:'), 2, 0)
        self.max_consecutive_spin = QSpinBox()
        self.max_consecutive_spin.setRange(1, 10)
        self.max_consecutive_spin.valueChanged.connect(self.on_value_changed)
        feedback_layout.addWidget(self.max_consecutive_spin, 2, 1)
        
        # Cooldown
        feedback_layout.addWidget(QLabel('Cooldown (ms):'), 3, 0)
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(100, 2000)
        self.cooldown_spin.setSingleStep(100)
        self.cooldown_spin.valueChanged.connect(self.on_value_changed)
        feedback_layout.addWidget(self.cooldown_spin, 3, 1)
        
        # Similarity Threshold
        feedback_layout.addWidget(QLabel('Umbral de Similitud:'), 4, 0)
        self.similarity_spin = QDoubleSpinBox()
        self.similarity_spin.setRange(0.1, 1.0)
        self.similarity_spin.setSingleStep(0.1)
        self.similarity_spin.setDecimals(1)
        self.similarity_spin.valueChanged.connect(self.on_value_changed)
        feedback_layout.addWidget(self.similarity_spin, 4, 1)
        
        layout.addWidget(feedback_group)
        layout.addStretch()
        
        return widget
        
    def create_filters_tab(self):
        """Crear pestaña de filtros avanzados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Noise Suppression Group
        noise_group = QGroupBox('Supresión de Ruido')
        noise_layout = QGridLayout(noise_group)
        
        self.spectral_subtraction_check = QCheckBox('Habilitar Sustracción Espectral')
        self.spectral_subtraction_check.stateChanged.connect(self.on_checkbox_changed)
        noise_layout.addWidget(self.spectral_subtraction_check, 0, 0, 1, 2)
        
        noise_layout.addWidget(QLabel('Factor de Reducción de Ruido:'), 1, 0)
        self.noise_reduction_spin = QDoubleSpinBox()
        self.noise_reduction_spin.setRange(0.0, 1.0)
        self.noise_reduction_spin.setSingleStep(0.1)
        self.noise_reduction_spin.setDecimals(1)
        self.noise_reduction_spin.valueChanged.connect(self.on_value_changed)
        noise_layout.addWidget(self.noise_reduction_spin, 1, 1)
        
        noise_layout.addWidget(QLabel('Factor de Suavizado:'), 2, 0)
        self.smoothing_spin = QDoubleSpinBox()
        self.smoothing_spin.setRange(0.0, 1.0)
        self.smoothing_spin.setSingleStep(0.1)
        self.smoothing_spin.setDecimals(1)
        self.smoothing_spin.valueChanged.connect(self.on_value_changed)
        noise_layout.addWidget(self.smoothing_spin, 2, 1)
        
        layout.addWidget(noise_group)
        
        # Filters Group
        filters_group = QGroupBox('Filtros de Frecuencia')
        filters_layout = QGridLayout(filters_group)
        
        filters_layout.addWidget(QLabel('Filtro Pasa-alto (Hz):'), 0, 0)
        self.high_pass_spin = QSpinBox()
        self.high_pass_spin.setRange(20, 200)
        self.high_pass_spin.setSingleStep(10)
        self.high_pass_spin.valueChanged.connect(self.on_value_changed)
        filters_layout.addWidget(self.high_pass_spin, 0, 1)
        
        filters_layout.addWidget(QLabel('Filtro Pasa-bajo (Hz):'), 1, 0)
        self.low_pass_spin = QSpinBox()
        self.low_pass_spin.setRange(4000, 16000)
        self.low_pass_spin.setSingleStep(1000)
        self.low_pass_spin.valueChanged.connect(self.on_value_changed)
        filters_layout.addWidget(self.low_pass_spin, 1, 1)
        
        filters_layout.addWidget(QLabel('Piso Espectral (dB):'), 2, 0)
        self.spectral_floor_slider = QSlider(Qt.Horizontal)
        self.spectral_floor_slider.setRange(-80, -40)
        self.spectral_floor_slider.valueChanged.connect(self.on_slider_changed)
        self.spectral_floor_label = QLabel('-60')
        filters_layout.addWidget(self.spectral_floor_slider, 2, 1)
        filters_layout.addWidget(self.spectral_floor_label, 2, 2)
        
        self.adaptive_gain_check = QCheckBox('Control Automático de Ganancia')
        self.adaptive_gain_check.stateChanged.connect(self.on_checkbox_changed)
        filters_layout.addWidget(self.adaptive_gain_check, 3, 0, 1, 2)
        
        layout.addWidget(filters_group)
        layout.addStretch()
        
        return widget
        
    def create_debug_tab(self):
        """Crear pestaña de debug"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        debug_group = QGroupBox('Configuración de Debug')
        debug_layout = QVBoxLayout(debug_group)
        
        self.log_audio_check = QCheckBox('Registrar Niveles de Audio')
        self.log_audio_check.stateChanged.connect(self.on_checkbox_changed)
        debug_layout.addWidget(self.log_audio_check)
        
        self.log_vad_check = QCheckBox('Registrar Decisiones del VAD')
        self.log_vad_check.stateChanged.connect(self.on_checkbox_changed)
        debug_layout.addWidget(self.log_vad_check)
        
        self.save_clips_check = QCheckBox('Guardar Clips de Audio para Debug')
        self.save_clips_check.stateChanged.connect(self.on_checkbox_changed)
        debug_layout.addWidget(self.save_clips_check)
        
        layout.addWidget(debug_group)
        
        # Log viewer
        log_group = QGroupBox('Monitor de VAD en Tiempo Real')
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('''
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        ''')
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        return widget
        
    def populate_values(self):
        """Poblar los controles con valores del config"""
        # Audio
        self.sample_rate_spin.setValue(
            self.config.getint('audio', 'sample_rate', fallback=16000)
        )
        self.frame_ms_spin.setValue(
            self.config.getint('audio', 'frame_ms', fallback=20)
        )
        self.voice_threshold_slider.setValue(
            self.config.getint('audio', 'voice_threshold_db', fallback=-30)
        )
        self.noise_gate_slider.setValue(
            self.config.getint('audio', 'noise_gate_db', fallback=-45)
        )
        self.min_speech_spin.setValue(
            self.config.getint('audio', 'min_speech_duration_ms', fallback=300)
        )
        self.max_silence_spin.setValue(
            self.config.getint('audio', 'max_silence_duration_ms', fallback=800)
        )
        
        # VAD
        self.aggressiveness_slider.setValue(
            self.config.getint('vad', 'aggressiveness', fallback=3)
        )
        self.padding_spin.setValue(
            self.config.getint('vad', 'padding_ms', fallback=600)
        )
        self.voice_ratio_spin.setValue(
            self.config.getfloat('vad', 'voice_ratio_threshold', fallback=0.8)
        )
        
        # Feedback Prevention
        self.feedback_detection_check.setChecked(
            self.config.getboolean('feedback_prevention', 'enable_feedback_detection', fallback=True)
        )
        self.detection_window_spin.setValue(
            self.config.getint('feedback_prevention', 'feedback_detection_window_ms', fallback=1000)
        )
        self.max_consecutive_spin.setValue(
            self.config.getint('feedback_prevention', 'max_consecutive_translations', fallback=3)
        )
        self.cooldown_spin.setValue(
            self.config.getint('feedback_prevention', 'cooldown_after_translation_ms', fallback=500)
        )
        self.similarity_spin.setValue(
            self.config.getfloat('feedback_prevention', 'similarity_threshold', fallback=0.8)
        )
        
        # Noise Suppression
        self.spectral_subtraction_check.setChecked(
            self.config.getboolean('noise_suppression', 'enable_spectral_subtraction', fallback=True)
        )
        self.noise_reduction_spin.setValue(
            self.config.getfloat('noise_suppression', 'noise_reduction_factor', fallback=0.5)
        )
        self.smoothing_spin.setValue(
            self.config.getfloat('noise_suppression', 'smoothing_factor', fallback=0.8)
        )
        
        # Advanced Filters
        self.high_pass_spin.setValue(
            self.config.getint('advanced_filters', 'high_pass_cutoff_hz', fallback=80)
        )
        self.low_pass_spin.setValue(
            self.config.getint('advanced_filters', 'low_pass_cutoff_hz', fallback=8000)
        )
        self.spectral_floor_slider.setValue(
            self.config.getint('advanced_filters', 'spectral_floor_db', fallback=-60)
        )
        self.adaptive_gain_check.setChecked(
            self.config.getboolean('advanced_filters', 'adaptive_gain_control', fallback=True)
        )
        
        # Debug
        self.log_audio_check.setChecked(
            self.config.getboolean('debug', 'log_audio_levels', fallback=False)
        )
        self.log_vad_check.setChecked(
            self.config.getboolean('debug', 'log_vad_decisions', fallback=False)
        )
        self.save_clips_check.setChecked(
            self.config.getboolean('debug', 'save_audio_clips', fallback=False)
        )
        
        # Actualizar labels
        self.update_slider_labels()
        
    def update_slider_labels(self):
        """Actualizar etiquetas de sliders"""
        self.voice_threshold_label.setText(str(self.voice_threshold_slider.value()))
        self.noise_gate_label.setText(str(self.noise_gate_slider.value()))
        self.aggressiveness_label.setText(str(self.aggressiveness_slider.value()))
        self.spectral_floor_label.setText(str(self.spectral_floor_slider.value()))
        
    def on_slider_changed(self):
        """Manejar cambios en sliders"""
        self.update_slider_labels()
        self.on_value_changed()
        
    def on_value_changed(self):
        """Manejar cambios en valores"""
        self.status_label.setText('Configuración modificada - aplicando en 1s...')
        self.status_label.setStyleSheet('color: orange; font-size: 12px;')
        
        # Reiniciar timer para auto-aplicar
        self.auto_save_timer.start(1000)  # 1 segundo de delay
        
    def on_checkbox_changed(self):
        """Manejar cambios en checkboxes"""
        self.on_value_changed()
        
    def collect_config_values(self):
        """Recopilar valores de todos los controles"""
        config_dict = {}
        
        # Audio
        config_dict['audio'] = {
            'sample_rate': str(self.sample_rate_spin.value()),
            'frame_ms': str(self.frame_ms_spin.value()),
            'voice_threshold_db': str(self.voice_threshold_slider.value()),
            'noise_gate_db': str(self.noise_gate_slider.value()),
            'min_speech_duration_ms': str(self.min_speech_spin.value()),
            'max_silence_duration_ms': str(self.max_silence_spin.value())
        }
        
        # VAD
        config_dict['vad'] = {
            'aggressiveness': str(self.aggressiveness_slider.value()),
            'padding_ms': str(self.padding_spin.value()),
            'voice_ratio_threshold': str(self.voice_ratio_spin.value())
        }
        
        # Feedback Prevention
        config_dict['feedback_prevention'] = {
            'enable_feedback_detection': str(self.feedback_detection_check.isChecked()).lower(),
            'feedback_detection_window_ms': str(self.detection_window_spin.value()),
            'max_consecutive_translations': str(self.max_consecutive_spin.value()),
            'cooldown_after_translation_ms': str(self.cooldown_spin.value()),
            'similarity_threshold': str(self.similarity_spin.value())
        }
        
        # Noise Suppression
        config_dict['noise_suppression'] = {
            'enable_spectral_subtraction': str(self.spectral_subtraction_check.isChecked()).lower(),
            'noise_reduction_factor': str(self.noise_reduction_spin.value()),
            'smoothing_factor': str(self.smoothing_spin.value())
        }
        
        # Advanced Filters
        config_dict['advanced_filters'] = {
            'high_pass_cutoff_hz': str(self.high_pass_spin.value()),
            'low_pass_cutoff_hz': str(self.low_pass_spin.value()),
            'spectral_floor_db': str(self.spectral_floor_slider.value()),
            'adaptive_gain_control': str(self.adaptive_gain_check.isChecked()).lower(),
            'enable_noise_suppression': 'true',
            'noise_reduction_factor': str(self.noise_reduction_spin.value())
        }
        
        # Debug
        config_dict['debug'] = {
            'log_audio_levels': str(self.log_audio_check.isChecked()).lower(),
            'log_vad_decisions': str(self.log_vad_check.isChecked()).lower(),
            'save_audio_clips': str(self.save_clips_check.isChecked()).lower()
        }
        
        return config_dict
        
    def save_and_apply_config(self):
        """Guardar configuración y aplicar cambios"""
        config_dict = self.collect_config_values()
        
        # Actualizar el objeto config
        for section, values in config_dict.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in values.items():
                self.config.set(section, key, value)
        
        # Guardar a archivo
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
        
        # Emitir señal de cambio
        self.config_changed.emit(config_dict)
        
        self.status_label.setText('✅ Configuración aplicada')
        self.status_label.setStyleSheet('color: green; font-size: 12px;')
        
    def apply_config(self):
        """Aplicar configuración sin guardar"""
        config_dict = self.collect_config_values()
        self.config_changed.emit(config_dict)
        
        self.status_label.setText('✅ Configuración aplicada (no guardada)')
        self.status_label.setStyleSheet('color: blue; font-size: 12px;')
        
    def reset_to_defaults(self):
        """Restaurar valores por defecto"""
        self.create_default_config()
        self.populate_values()
        self.save_and_apply_config()
        
    def add_log_entry(self, message):
        """Agregar entrada al log de debug"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f'[{__import__("datetime").datetime.now().strftime("%H:%M:%S")}] {message}')
            
            # Mantener solo las últimas 50 líneas
            text = self.log_text.toPlainText()
            lines = text.split('\n')
            if len(lines) > 50:
                self.log_text.setPlainText('\n'.join(lines[-50:]))
