import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self):
        self._stamps = {}
        self._last = None

    @contextmanager
    def stage(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self._stamps[name] = self._stamps.get(name, 0.0) + (end - start)

    def summary(self) -> str:
        parts = [f"{k}={v*1000:.0f} ms" for k, v in self._stamps.items()]
        self._stamps.clear()
        return " | ".join(parts)
