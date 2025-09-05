"""
Ventana de configuración de audio con prueba de micrófono en tiempo real.
"""
import asyncio
import numpy as np
import sounddevice as sd
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QSlider, QComboBox, QPushButton, QProgressBar, QFrame,
    QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QPalette, QColor

from ..utils.config_utils import load_config, save_config_value


class AudioLevelMonitor(QThread):
    """Monitor de niveles de audio en tiempo real."""
    level_updated = Signal(float)  # Señal con nivel en dB
    
    def __init__(self, device_name=None):
        super().__init__()
        self.device_name = device_name
        self.running = False
        self.sample_rate = 16000
        
    def run(self):
        """Ejecutar monitoreo de audio."""
        self.running = True
        
        def audio_callback(indata, frames, time, status):
            if self.running and len(indata) > 0:
                # Calcular RMS y convertir a dB
                rms = np.sqrt(np.mean(indata**2))
                if rms > 0:
                    db_level = 20 * np.log10(rms)
                else:
                    db_level = -100
                
                self.level_updated.emit(db_level)
        
        try:
            # Encontrar dispositivo
            devices = sd.query_devices()
            device_id = None
            
            if self.device_name:
                for i, device in enumerate(devices):
                    if self.device_name.lower() in device['name'].lower():
                        device_id = i
                        break
            
            # Iniciar stream de audio
            with sd.InputStream(
                device=device_id,
                samplerate=self.sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=1024
            ):
                while self.running:
                    self.msleep(50)  # 50ms de actualización
                    
        except Exception as e:
            print(f"[AUDIO] Error en monitor: {e}")
    
    def stop(self):
        """Detener monitoreo."""
        self.running = False
        self.wait()


class AudioTestWindow(QDialog):
    """Ventana de prueba y configuración de audio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Audio - DSRealtime")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Variables
        self.config = load_config()
        self.audio_monitor = None
        self.current_input_device = None
        self.current_output_device = None
        
        self.setup_ui()
        self.load_devices()
        self.load_settings()
        
        # Timer para actualizar UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)  # 100ms
    
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # === DISPOSITIVOS ===
        devices_group = QGroupBox("Dispositivos de Audio")
        devices_layout = QGridLayout(devices_group)
        
        # Dispositivo de entrada
        devices_layout.addWidget(QLabel("Dispositivo de entrada:"), 0, 0)
        self.input_combo = QComboBox()
        self.input_combo.currentTextChanged.connect(self.on_input_device_changed)
        devices_layout.addWidget(self.input_combo, 0, 1)
        
        # Dispositivo de salida
        devices_layout.addWidget(QLabel("Dispositivo de salida:"), 1, 0)
        self.output_combo = QComboBox()
        self.output_combo.currentTextChanged.connect(self.on_output_device_changed)
        devices_layout.addWidget(self.output_combo, 1, 1)
        
        layout.addWidget(devices_group)
        
        # === VOLUMEN ===
        volume_group = QGroupBox("Niveles de Audio")
        volume_layout = QVBoxLayout(volume_group)
        
        # Volumen de entrada
        input_vol_layout = QHBoxLayout()
        input_vol_layout.addWidget(QLabel("Volumen de entrada:"))
        self.input_volume_bar = QProgressBar()
        self.input_volume_bar.setRange(-60, 0)
        self.input_volume_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                background-color: #2b2b2b;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00ff00, stop: 0.7 #ffff00, stop: 1.0 #ff0000);
                border-radius: 3px;
            }
        """)
        input_vol_layout.addWidget(self.input_volume_bar)
        self.input_db_label = QLabel("-∞ dB")
        self.input_db_label.setMinimumWidth(60)
        input_vol_layout.addWidget(self.input_db_label)
        volume_layout.addLayout(input_vol_layout)
        
        # Volumen de salida
        output_vol_layout = QHBoxLayout()
        output_vol_layout.addWidget(QLabel("Volumen de salida:"))
        self.output_volume_slider = QSlider(Qt.Horizontal)
        self.output_volume_slider.setRange(0, 100)
        self.output_volume_slider.setValue(80)
        output_vol_layout.addWidget(self.output_volume_slider)
        self.output_vol_label = QLabel("80%")
        self.output_vol_label.setMinimumWidth(40)
        output_vol_layout.addWidget(self.output_vol_label)
        volume_layout.addLayout(output_vol_layout)
        
        layout.addWidget(volume_group)
        
        # === PRUEBA DE MICRÓFONO ===
        test_group = QGroupBox("Prueba de micrófono")
        test_layout = QVBoxLayout(test_group)
        
        test_info = QLabel("¿Tienes problemas con el micrófono? Empieza una prueba y di algo gracioso. Reproduciremos tu voz.")
        test_info.setWordWrap(True)
        test_info.setStyleSheet("color: #888; font-size: 12px;")
        test_layout.addWidget(test_info)
        
        # Botón de prueba y barra de progreso
        test_controls = QHBoxLayout()
        self.test_button = QPushButton("Detener prueba")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        self.test_button.clicked.connect(self.toggle_audio_test)
        test_controls.addWidget(self.test_button)
        
        # Barra de actividad del micrófono
        self.mic_activity_bar = QProgressBar()
        self.mic_activity_bar.setRange(0, 100)
        self.mic_activity_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2b2b2b;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                border-radius: 2px;
            }
        """)
        test_controls.addWidget(self.mic_activity_bar)
        test_layout.addLayout(test_controls)
        
        # Mensaje de estado
        self.status_label = QLabel("Discord no detecta ninguna entrada de voz de tu micrófono. Comprueba que hayas seleccionado el dispositivo de entrada correcto.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding: 8px;")
        test_layout.addWidget(self.status_label)
        
        layout.addWidget(test_group)
        
        # === CONFIGURACIÓN DE SENSIBILIDAD ===
        sensitivity_group = QGroupBox("Configuración de Sensibilidad")
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        
        # Umbral de voz
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Umbral de voz:"))
        self.voice_threshold_slider = QSlider(Qt.Horizontal)
        self.voice_threshold_slider.setRange(-60, 0)
        self.voice_threshold_slider.setValue(-30)
        self.voice_threshold_slider.valueChanged.connect(self.on_voice_threshold_changed)
        voice_layout.addWidget(self.voice_threshold_slider)
        self.voice_threshold_label = QLabel("-30 dB")
        self.voice_threshold_label.setMinimumWidth(60)
        voice_layout.addWidget(self.voice_threshold_label)
        sensitivity_layout.addLayout(voice_layout)
        
        # Puerta de ruido
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Puerta de ruido:"))
        self.noise_gate_slider = QSlider(Qt.Horizontal)
        self.noise_gate_slider.setRange(-70, -10)
        self.noise_gate_slider.setValue(-45)
        self.noise_gate_slider.valueChanged.connect(self.on_noise_gate_changed)
        noise_layout.addWidget(self.noise_gate_slider)
        self.noise_gate_label = QLabel("-45 dB")
        self.noise_gate_label.setMinimumWidth(60)
        noise_layout.addWidget(self.noise_gate_label)
        sensitivity_layout.addLayout(noise_layout)
        
        # Agresividad VAD
        vad_layout = QHBoxLayout()
        vad_layout.addWidget(QLabel("Agresividad VAD:"))
        self.vad_slider = QSlider(Qt.Horizontal)
        self.vad_slider.setRange(0, 3)
        self.vad_slider.setValue(2)
        self.vad_slider.valueChanged.connect(self.on_vad_changed)
        vad_layout.addWidget(self.vad_slider)
        vad_labels = ["Muy permisivo", "Permisivo", "Moderado", "Estricto"]
        self.vad_label = QLabel(vad_labels[2])
        self.vad_label.setMinimumWidth(100)
        vad_layout.addWidget(self.vad_label)
        sensitivity_layout.addLayout(vad_layout)
        
        layout.addWidget(sensitivity_group)
        
        # === OPCIONES AVANZADAS ===
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.feedback_check = QCheckBox("Prevención de bucles (anti-eco)")
        self.feedback_check.setChecked(True)
        self.feedback_check.stateChanged.connect(self.on_feedback_changed)
        advanced_layout.addWidget(self.feedback_check)
        
        self.noise_suppression_check = QCheckBox("Supresión de ruido espectral")
        self.noise_suppression_check.setChecked(False)
        self.noise_suppression_check.stateChanged.connect(self.on_noise_suppression_changed)
        advanced_layout.addWidget(self.noise_suppression_check)
        
        layout.addWidget(advanced_group)
        
        # === BOTONES ===
        buttons_layout = QHBoxLayout()
        
        reset_button = QPushButton("Restablecer")
        reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_button)
        
        buttons_layout.addStretch()
        
        ok_button = QPushButton("Aceptar")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def load_devices(self):
        """Cargar dispositivos de audio disponibles."""
        try:
            devices = sd.query_devices()
            
            # Cargar dispositivos por defecto desde config
            default_input_device = None
            default_output_device = None
            
            try:
                if self.config.has_section('devices'):
                    default_input_device = self.config.getint('devices', 'default_input_device', fallback=None)
                    default_output_device = self.config.getint('devices', 'default_output_device', fallback=None)
                    print(f"[AUDIO] Config defaults: input={default_input_device}, output={default_output_device}")
            except Exception as e:
                print(f"[AUDIO] Failed to load config defaults: {e}")
            
            # Dispositivos de entrada
            self.input_combo.clear()
            selected_input_index = 0
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    self.input_combo.addItem(f"{device['name']}", i)
                    # Auto-seleccionar si coincide con el dispositivo por defecto
                    if default_input_device is not None and i == default_input_device:
                        selected_input_index = self.input_combo.count() - 1
                        print(f"[AUDIO] Auto-selected input: {device['name']} (device {i})")
            
            # Dispositivos de salida  
            self.output_combo.clear()
            selected_output_index = 0
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    self.output_combo.addItem(f"{device['name']}", i)
                    # Auto-seleccionar si coincide con el dispositivo por defecto
                    if default_output_device is not None and i == default_output_device:
                        selected_output_index = self.output_combo.count() - 1
                        print(f"[AUDIO] Auto-selected output: {device['name']} (device {i})")
            
            # Aplicar selecciones automáticas
            if self.input_combo.count() > 0:
                self.input_combo.setCurrentIndex(selected_input_index)
            if self.output_combo.count() > 0:
                self.output_combo.setCurrentIndex(selected_output_index)
                    
        except Exception as e:
            print(f"[AUDIO] Error cargando dispositivos: {e}")
    
    def load_settings(self):
        """Cargar configuración actual."""
        # Cargar valores del config
        voice_threshold = self.config.getfloat('audio', 'voice_threshold_db', fallback=-30)
        noise_gate = self.config.getfloat('audio', 'noise_gate_db', fallback=-45)
        vad_aggressiveness = self.config.getint('vad', 'aggressiveness', fallback=2)
        feedback_enabled = self.config.getboolean('feedback_prevention', 'enable_feedback_detection', fallback=True)
        noise_suppression = self.config.getboolean('noise_suppression', 'enable_spectral_subtraction', fallback=False)
        
        # Aplicar a la UI
        self.voice_threshold_slider.setValue(int(voice_threshold))
        self.noise_gate_slider.setValue(int(noise_gate))
        self.vad_slider.setValue(vad_aggressiveness)
        self.feedback_check.setChecked(feedback_enabled)
        self.noise_suppression_check.setChecked(noise_suppression)
        
        # Actualizar labels
        self.on_voice_threshold_changed(int(voice_threshold))
        self.on_noise_gate_changed(int(noise_gate))
        self.on_vad_changed(vad_aggressiveness)
    
    def on_input_device_changed(self, device_name):
        """Cambio de dispositivo de entrada."""
        self.current_input_device = device_name
        
        # Reiniciar monitor si está activo
        if self.audio_monitor and self.audio_monitor.running:
            self.stop_audio_test()
            self.start_audio_test()
    
    def on_output_device_changed(self, device_name):
        """Cambio de dispositivo de salida."""
        self.current_output_device = device_name
    
    def toggle_audio_test(self):
        """Alternar prueba de audio."""
        if self.audio_monitor and self.audio_monitor.running:
            self.stop_audio_test()
        else:
            self.start_audio_test()
    
    def start_audio_test(self):
        """Iniciar prueba de audio."""
        self.audio_monitor = AudioLevelMonitor(self.current_input_device)
        self.audio_monitor.level_updated.connect(self.update_audio_level)
        self.audio_monitor.start()
        
        self.test_button.setText("Detener prueba")
        self.status_label.setText("Monitoreando entrada de micrófono...")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 11px; padding: 8px;")
    
    def stop_audio_test(self):
        """Detener prueba de audio."""
        if self.audio_monitor:
            self.audio_monitor.stop()
            self.audio_monitor = None
        
        self.test_button.setText("Iniciar prueba")
        self.status_label.setText("Prueba detenida. Haz clic en 'Iniciar prueba' para probar tu micrófono.")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding: 8px;")
        
        # Resetear barras
        self.input_volume_bar.setValue(-60)
        self.mic_activity_bar.setValue(0)
        self.input_db_label.setText("-∞ dB")
    
    def update_audio_level(self, db_level):
        """Actualizar nivel de audio."""
        # Limitar rango
        db_level = max(-60, min(0, db_level))
        
        # Actualizar barra de volumen
        self.input_volume_bar.setValue(int(db_level))
        self.input_db_label.setText(f"{db_level:.1f} dB")
        
        # Actualizar barra de actividad (0-100%)
        activity = max(0, min(100, (db_level + 60) * 100 / 60))
        self.mic_activity_bar.setValue(int(activity))
        
        # Actualizar estado basado en umbrales
        voice_threshold = self.voice_threshold_slider.value()
        noise_gate = self.noise_gate_slider.value()
        
        if db_level > voice_threshold:
            self.status_label.setText("✅ ¡Voz detectada! El nivel es suficiente para traducción.")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 11px; padding: 8px;")
        elif db_level > noise_gate:
            self.status_label.setText("⚠️ Audio detectado pero por debajo del umbral de voz.")
            self.status_label.setStyleSheet("color: #ffaa00; font-size: 11px; padding: 8px;")
        else:
            self.status_label.setText("🔇 Nivel muy bajo. Comprueba el micrófono o reduce la puerta de ruido.")
            self.status_label.setStyleSheet("color: #ff6666; font-size: 11px; padding: 8px;")
    
    def on_voice_threshold_changed(self, value):
        """Cambio en umbral de voz."""
        self.voice_threshold_label.setText(f"{value} dB")
        save_config_value('config.ini', 'audio', 'voice_threshold_db', value)
    
    def on_noise_gate_changed(self, value):
        """Cambio en puerta de ruido."""
        self.noise_gate_label.setText(f"{value} dB")
        save_config_value('config.ini', 'audio', 'noise_gate_db', value)
    
    def on_vad_changed(self, value):
        """Cambio en agresividad VAD."""
        labels = ["Muy permisivo", "Permisivo", "Moderado", "Estricto"]
        self.vad_label.setText(labels[value])
        save_config_value('config.ini', 'vad', 'aggressiveness', value)
    
    def on_feedback_changed(self, state):
        """Cambio en prevención de bucles."""
        enabled = state == Qt.Checked
        save_config_value('config.ini', 'feedback_prevention', 'enable_feedback_detection', str(enabled).lower())
    
    def on_noise_suppression_changed(self, state):
        """Cambio en supresión de ruido."""
        enabled = state == Qt.Checked
        save_config_value('config.ini', 'noise_suppression', 'enable_spectral_subtraction', str(enabled).lower())
    
    def reset_settings(self):
        """Restablecer configuración por defecto."""
        self.voice_threshold_slider.setValue(-30)
        self.noise_gate_slider.setValue(-45)
        self.vad_slider.setValue(2)
        self.feedback_check.setChecked(True)
        self.noise_suppression_check.setChecked(False)
    
    def update_ui(self):
        """Actualizar elementos de UI."""
        # Actualizar volumen de salida
        vol = self.output_volume_slider.value()
        self.output_vol_label.setText(f"{vol}%")
    
    def closeEvent(self, event):
        """Cerrar ventana."""
        self.stop_audio_test()
        event.accept()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = AudioTestWindow()
    window.show()
    sys.exit(app.exec())
