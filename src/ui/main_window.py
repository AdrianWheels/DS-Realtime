import asyncio
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox
from qasync import asyncSlot
import sounddevice as sd
import torch


class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("LocalVoiceTranslate (ES→EN)")
        self.args = args

        root = QWidget(self)
        lay = QVBoxLayout(root)
        self.combo_in = QComboBox()
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.latency_label = QLabel("latencia: —")
        self.partial_label = QLabel("parcial: —")
        self.final_label = QLabel("final: —")
        self.fps_label = QLabel("FPS: —")
        self.rtf_label = QLabel("RTF: —")
        self.gpu_label = QLabel("GPU: —")
        self.vram_label = QLabel("VRAM: —")

        lay.addWidget(QLabel("Micrófono de entrada (WASAPI):"))
        lay.addWidget(self.combo_in)
        lay.addWidget(self.btn_start)
        lay.addWidget(self.btn_stop)
        lay.addWidget(self.latency_label)
        lay.addWidget(self.partial_label)
        lay.addWidget(self.final_label)
        lay.addWidget(self.fps_label)
        lay.addWidget(self.rtf_label)
        lay.addWidget(self.gpu_label)
        lay.addWidget(self.vram_label)
        self.setCentralWidget(root)

        self._populate_inputs()
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)

        self._task = None

    def _populate_inputs(self):
        self.combo_in.clear()
        for d in sd.query_devices():
            name = d.get("name", "")
            self.combo_in.addItem(name)

    @asyncSlot()
    async def start(self):
        if self._task and not self._task.done():
            return
        # Re-lanzar main CLI pipeline reusando args
        import src.main as main_mod  # evitar import circular
        a = self.args
        a.input = self.combo_in.currentText()
        self._task = asyncio.create_task(main_mod.pipeline_cli(a, ui_callback=self.update_debug))

    @asyncSlot()
    async def stop(self):
        if self._task:
            self._task.cancel()

    def update_debug(self, partial=None, final=None, metrics=None):
        if partial is not None:
            self.partial_label.setText(f"parcial: {partial}")
        if final is not None:
            self.final_label.setText(f"final: {final}")
        if metrics:
            fps = 1.0 / metrics["t_final"] if metrics["t_final"] else 0.0
            self.fps_label.setText(f"FPS: {fps:.2f}")
            self.rtf_label.setText(f"RTF: {metrics['rtf']:.2f}")
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
