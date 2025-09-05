import asyncio
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QFrame,
)
from PySide6.QtCore import QTimer, QThread, Signal
from datetime import datetime
from qasync import asyncSlot
import sounddevice as sd
import torch

from .config_window import ConfigWindow


class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        # simple textual debug helper that also appends to ui_debug.log
        def _dbg(msg: str):
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[UI DEBUG] {ts} - {msg}"
            try:
                print(line)
            except Exception:
                pass
            try:
                with open('ui_debug.log', 'a', encoding='utf-8') as f:
                    f.write(line + "\n")
            except Exception:
                pass

        self._debug = _dbg

        self.setWindowTitle("LocalVoiceTranslate (ES→EN)")
        self.setMinimumSize(900, 420)
        self.args = args

        root = QWidget(self)
        lay = QVBoxLayout(root)

        # Top: two large rounded cards (ES left, EN right)
        cards = QHBoxLayout()
        cards.setSpacing(18)

        def make_card():
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setStyleSheet("background: transparent;")
            card_l = QVBoxLayout(card)
            label = QLabel("—")
            label.setWordWrap(True)
            label.setStyleSheet(
                "background:#ecd8ff; padding:18px; border-radius:14px; font-size:16px;"
            )
            label.setMinimumHeight(120)
            # small spacer and indicator placeholder
            indicator = QFrame()
            indicator.setFixedSize(10, 10)
            indicator.setStyleSheet("background: gray; border-radius:5px;")
            # layout for label + indicator
            card_l.addWidget(label)
            # place indicator at left below the card
            ind_row = QHBoxLayout()
            ind_row.addSpacing(6)
            ind_row.addWidget(indicator)
            ind_row.addStretch()
            card_l.addLayout(ind_row)
            return card, label, indicator

        left_card, self.es_label, self.mic_indicator = make_card()
        right_card, self.en_label, self.spk_indicator = make_card()

        cards.addWidget(left_card, 1)
        cards.addWidget(right_card, 1)

        lay.addLayout(cards)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 12, 0, 0)
        left = QVBoxLayout()
        left.setSpacing(8)
        right = QVBoxLayout()
        right.setSpacing(6)

        # Input / Output selectors
        self.combo_in = QComboBox()
        left.addWidget(QLabel("Micrófono de entrada (WASAPI):"))
        left.addWidget(self.combo_in)

        self.combo_out = QComboBox()
        left.addWidget(QLabel("Dispositivo de salida (hint):"))
        left.addWidget(self.combo_out)

        # Start / Stop buttons
        self.btn_start = QPushButton('Start')
        self.btn_start.setFixedHeight(36)
        self.btn_start.setFixedWidth(140)
        self.btn_stop = QPushButton('Stop')
        self.btn_stop.setFixedHeight(36)
        self.btn_stop.setFixedWidth(140)
        # Stop disabled by default until pipeline is running
        self.btn_stop.setEnabled(False)
        
        # Botón de configuración
        self.btn_config = QPushButton('⚙️ Config')
        self.btn_config.setFixedHeight(36)
        self.btn_config.setFixedWidth(100)
        self.btn_config.clicked.connect(self.open_config_window)
        
        # center buttons horizontally
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.btn_start)
        btn_row.addSpacing(8)
        btn_row.addWidget(self.btn_stop)
        btn_row.addSpacing(8)
        btn_row.addWidget(self.btn_config)
        btn_row.addStretch()
        left.addLayout(btn_row)

        # Metrics on the right column
        self.latency_label = QLabel("latencia: —")
        self.partial_label = QLabel("parcial: —")
        self.final_label = QLabel("final: —")
        self.fps_label = QLabel("FPS: —")
        self.rtf_label = QLabel("RTF: —")
        self.gpu_label = QLabel("GPU: —")
        self.vram_label = QLabel("VRAM: —")
        right.addWidget(self.latency_label)
        right.addWidget(self.partial_label)
        right.addWidget(self.final_label)
        right.addSpacing(6)
        right.addWidget(self.fps_label)
        right.addWidget(self.rtf_label)
        right.addSpacing(6)
        right.addWidget(self.gpu_label)
        right.addWidget(self.vram_label)
        right.addStretch()

        # status label
        self.status_label = QLabel("stopped")
        right.addWidget(self.status_label)

        controls.addLayout(left)
        controls.addLayout(right)
        lay.addLayout(controls)

        self.setCentralWidget(root)

        # Timers to reset indicators to gray after activity
        self._mic_timer = QTimer(self)
        self._mic_timer.setSingleShot(True)
        self._mic_timer.timeout.connect(lambda: self.mic_indicator.setStyleSheet("background: gray; border-radius:5px;"))
        self._spk_timer = QTimer(self)
        self._spk_timer.setSingleShot(True)
        self._spk_timer.timeout.connect(lambda: self.spk_indicator.setStyleSheet("background: gray; border-radius:5px;"))

        self._task = None
        self._running = False
        self.config_window = None  # Para la ventana de configuración
        self.vad_instance = None   # Instancia del VAD para recarga de config
        self._populate_inputs()
        # log initial device list for diagnostics
        try:
            self._debug("MainWindow initialized; available hostapis and devices:")
            hostapis = sd.query_hostapis()
            self._debug(f"hostapis: {len(hostapis)} entries")
            for i, h in enumerate(hostapis):
                self._debug(f"  hostapi[{i}] name={h.get('name')}")
            devs = sd.query_devices()
            self._debug(f"devices: {len(devs)} entries")
            for i, d in enumerate(devs):
                self._debug(f"  device[{i}] name={d.get('name')} index={d.get('index')} in={d.get('max_input_channels')} out={d.get('max_output_channels')}")
        except Exception as e:
            self._debug(f"error querying devices: {e}")
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)

        # log when UI is shown
        self._debug('MainWindow constructed (init complete)')

    def _populate_inputs(self):
        self.combo_in.clear()
        self.combo_out.clear()
        try:
            devs = sd.query_devices()
            for idx, d in enumerate(devs):
                name = d.get("name", "")
                max_in = int(d.get("max_input_channels", 0) or 0)
                max_out = int(d.get("max_output_channels", 0) or 0)
                self._debug(f"populate: device[{idx}] name={name!r} in={max_in} out={max_out}")
                if max_in:
                    self.combo_in.addItem(name)
                if max_out:
                    self.combo_out.addItem(name)
        except Exception as e:
            self._debug(f"_populate_inputs failed: {e}")
        
        # Configurar dispositivos por defecto para Discord
        try:
            # Buscar dispositivo de entrada: Logitech G535 (NO CABLE Output)
            for i in range(self.combo_in.count()):
                item_text = self.combo_in.itemText(i)
                if ('Logitech G535' in item_text and 
                    'micrófono' in item_text.lower()):
                    self.combo_in.setCurrentIndex(i)
                    self._debug(f'Auto-selected input: {item_text}')
                    break
            
            # Buscar dispositivo de salida: CABLE Input - device 6
            for i in range(self.combo_out.count()):
                item_text = self.combo_out.itemText(i)
                if item_text == 'CABLE Input (VB-Audio Virtual C':
                    self.combo_out.setCurrentIndex(i)
                    self._debug(f'Auto-selected output: {item_text}')
                    break
                # Fallback: CABLE In 16ch como alternativa
                elif 'CABLE In 16ch (VB-Audio Virtual' in item_text:
                    self.combo_out.setCurrentIndex(i)
                    self._debug(f'Fallback output selected: {item_text}')
                    # No break, seguir buscando el principal
        except Exception as e:
            self._debug(f'auto-selection failed: {e}')
        
        # log selected defaults
        try:
            in_count = self.combo_in.count()
            out_count = self.combo_out.count()
            self._debug(f"combo_in items={in_count} combo_out items={out_count}")
        except Exception:
            pass
        # connect selection change logging
        self.combo_in.currentTextChanged.connect(
            lambda t: self._debug(f"combo_in selected: {t}")
        )
        self.combo_out.currentTextChanged.connect(
            lambda t: self._debug(f"combo_out selected: {t}")
        )

    def showEvent(self, event):
        # window is shown on screen
        try:
            self._debug('MainWindow.showEvent -> window shown')
        except Exception:
            pass
        super().showEvent(event)

    @asyncSlot()
    async def start(self):
        # prevent re-entrancy using explicit running flag
        if self._running:
            return
        self._debug("Start pressed")
        self._running = True
        # Re-lanzar main CLI pipeline reusando args
        import src.main as main_mod  # evitar import circular
        a = self.args
        a.input = self.combo_in.currentText()
        a.output = self.combo_out.currentText()
        # disable Start to avoid repeated clicks; enable Stop
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("running")
        self._debug(
            f"state changed -> running (input={self.combo_in.currentText()} output={self.combo_out.currentText()})"
        )
        self._task = asyncio.create_task(
            main_mod.pipeline_cli(a, ui_callback=self.update_debug)
        )
        # attach done-callback to restore UI state and show errors
        self._task.add_done_callback(self._on_task_done)

    @asyncSlot()
    async def stop(self):
        self._debug("Stop pressed")
        if self._task:
            self._task.cancel()
        # reflect UI immediately
        self.btn_stop.setEnabled(False)
        self.btn_start.setEnabled(True)
        self._running = False
        self.status_label.setText("stopped")
        self._debug("state changed -> stopped")

    def _on_task_done(self, fut):
        # This callback is invoked when the asyncio Task finishes (success/exception/cancel)
        def _restore():
            # restore button state
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self._running = False
            self.status_label.setText("stopped")
            # show exception if any
            try:
                exc = fut.exception()
            except asyncio.CancelledError:
                exc = None
            if exc:
                # display short error message in final_label for visibility
                self.final_label.setText(f"error: {type(exc).__name__}: {str(exc)}")
        # Use QTimer.singleShot to run UI updates on the Qt main thread
        QTimer.singleShot(0, _restore)
        # clear task reference
        try:
            # avoid keeping reference cycles
            if self._task is fut:
                self._task = None
        except Exception:
            self._task = None
        # log completion
        try:
            exc = fut.exception()
            if exc:
                self._debug(f"pipeline task finished with exception: {type(exc).__name__}: {exc}")
            else:
                self._debug("pipeline task finished successfully")
        except asyncio.CancelledError:
            self._debug("pipeline task was cancelled")
        except Exception:
            pass

    def closeEvent(self, event):
        # log window close
        try:
            self._debug("MainWindow.closeEvent -> application closing")
        except Exception:
            print("[UI DEBUG] closing")
        super().closeEvent(event)

    def update_debug(self, partial=None, final=None, metrics=None, speaker_active=False):
        # Update displayed texts
        if partial is not None:
            self.partial_label.setText(f"parcial: {partial}")
            self.es_label.setText(partial)
            # mic active: turn green briefly
            self.mic_indicator.setStyleSheet("background: #4caf50; border-radius:5px;")
            self._mic_timer.start(700)
            try:
                self._debug(f"update_debug: partial received: {partial}")
            except Exception:
                pass
        if final is not None:
            self.final_label.setText(f"final: {final}")
            self.en_label.setText(final)
            # speaker active: turn green briefly
            self.spk_indicator.setStyleSheet("background: #4caf50; border-radius:5px;")
            self._spk_timer.start(700)
            try:
                self._debug(f"update_debug: final received: {final} (output device: {self.combo_out.currentText()})")
            except Exception:
                pass
        # explicit speaker_active callback (from sink writes)
        if speaker_active:
            try:
                self._debug(f"update_debug: speaker_active event (device: {self.combo_out.currentText()})")
            except Exception:
                pass
            self.spk_indicator.setStyleSheet('background: #4caf50; border-radius:5px;')
            self._spk_timer.start(700)
        if metrics:
            fps = 1.0 / metrics.get("t_final", 0.0) if metrics.get("t_final", 0.0) else 0.0
            self.fps_label.setText(f"FPS: {fps:.2f}")
            self.rtf_label.setText(f"RTF: {metrics.get('rtf', 0.0):.2f}")
            util = mem_alloc = mem_total = 0
            if torch.cuda.is_available():
                dev = torch.cuda.current_device()
                try:
                    util = torch.cuda.utilization(dev)
                except Exception:
                    util = 0
                mem_alloc = torch.cuda.memory_allocated(dev) / (1024 ** 2)
                mem_total = torch.cuda.get_device_properties(dev).total_memory / (1024 ** 2)
            self.gpu_label.setText(f"GPU: {util:.0f}%")
            self.vram_label.setText(f"VRAM: {mem_alloc/1024:.1f}/{mem_total/1024:.1f} GB")

    def open_config_window(self):
        """Abrir ventana de configuración"""
        if not hasattr(self, 'config_window') or self.config_window is None:
            self.config_window = ConfigWindow(parent=self)
            self.config_window.config_changed.connect(self.on_config_changed)
        
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()

    def on_config_changed(self, config_dict):
        """Manejar cambios de configuración en tiempo real"""
        try:
            # Recargar configuración del VAD si está disponible
            if (self.vad_instance and 
                hasattr(self.vad_instance, 'reload_config')):
                self.vad_instance.reload_config()
                self._debug('VAD configuración recargada en tiempo real')
                
                # Agregar info específica del VAD al log
                if hasattr(self, 'config_window') and self.config_window:
                    vad_config = config_dict.get('vad', {})
                    aggressiveness = vad_config.get('aggressiveness', '?')
                    threshold = config_dict.get('audio', {}).get('voice_threshold_db', '?')
                    self.config_window.add_log_entry(
                        f'VAD actualizado: agresividad={aggressiveness}, ' +
                        f'umbral={threshold}dB'
                    )
            
            self._debug(f'Config cambiado: {len(config_dict)} secciones actualizadas')
            
            # Agregar logs al monitor de la ventana de config si está abierta
            if hasattr(self, 'config_window') and self.config_window:
                self.config_window.add_log_entry('✅ Configuración aplicada')
                
        except Exception as e:
            self._debug(f'Error aplicando configuración: {e}')
            if hasattr(self, 'config_window') and self.config_window:
                self.config_window.add_log_entry(f'❌ Error: {e}')
