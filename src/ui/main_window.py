import asyncio
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox
from qasync import asyncSlot
import sounddevice as sd


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

        lay.addWidget(QLabel("Micrófono de entrada (WASAPI):"))
        lay.addWidget(self.combo_in)
        lay.addWidget(self.btn_start)
        lay.addWidget(self.btn_stop)
        lay.addWidget(self.latency_label)
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
        self._task = asyncio.create_task(main_mod.pipeline_cli(a))

    @asyncSlot()
    async def stop(self):
        if self._task:
            self._task.cancel()
