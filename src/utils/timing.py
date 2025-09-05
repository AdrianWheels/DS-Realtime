import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self):
        self._stamps = {}
        # Inicio global para calcular el tiempo total del pipeline
        self._start = time.perf_counter()

    @contextmanager
    def stage(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self._stamps[name] = self._stamps.get(name, 0.0) + (end - start)

    def summary(self, audio_duration: float | None = None) -> str:
        # If a 'total' stage was recorded explicitly (for example via
        # `with timer.stage('total')`) it may not reflect the sum of
        # individual stages. Compute a canonical total as the sum of all
        # recorded stages excluding any previously-recorded 'total' and
        # override/add the 'total' entry with that value to produce
        # consistent summaries.
        total_excl = sum(v for k, v in self._stamps.items() if k != "total")
        if total_excl > 0:
            self._stamps["total"] = total_excl

        parts = [f"{k}={v*1000:.0f} ms" for k, v in self._stamps.items()]
        total = self._stamps.get("total", 0.0)
        if audio_duration:
            rtf = total / audio_duration if audio_duration > 0 else 0.0
            parts.append(f"RTF={rtf:.2f}")
        # Clear stamps after summarizing
        self._stamps.clear()
        return " | ".join(parts)

    def stop(self):
        """Registra el tiempo total desde la creación del temporizador."""
        self._stamps["total"] = time.perf_counter() - self._start
