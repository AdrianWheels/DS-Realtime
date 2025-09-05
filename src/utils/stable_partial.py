import time


class StablePartial:
    def __init__(self, min_chars: int = 20, stable_ms: int = 400):
        self.min_chars = min_chars
        self.stable_ms = stable_ms / 1000.0
        self._last_text = ""
        self._last_change = 0.0
        self._last_emit = ""

    def consider(self, text: str, now: float | None = None) -> str | None:
        now = now if now is not None else time.monotonic()
        if text != self._last_text:
            self._last_text = text
            self._last_change = now
            return None
        if now - self._last_change < self.stable_ms:
            return None
        if len(text) < self.min_chars and not text.endswith((" ", ",", ".", ";", ":", "?", "!")):
            return None
        if text == self._last_emit:
            return None
        self._last_emit = text
        return text
