import threading
import time

from slappaper.config import AUTO_DEBOUNCE_SECONDS


class ExecutionState:
    def __init__(self, auto_debounce_seconds=AUTO_DEBOUNCE_SECONDS):
        self.auto_debounce_seconds = auto_debounce_seconds
        self._lock = threading.Lock()
        self._generation_in_progress = False
        self._last_auto_generation_at = None

    def begin_generation(self, source, now=None):
        if source not in {"auto", "manual"}:
            raise ValueError(f"Unsupported generation source: {source}")

        now = time.monotonic() if now is None else now
        with self._lock:
            if self._generation_in_progress:
                return False

            if (
                source == "auto"
                and self._last_auto_generation_at is not None
                and now - self._last_auto_generation_at < self.auto_debounce_seconds
            ):
                return False

            self._generation_in_progress = True
            if source == "auto":
                self._last_auto_generation_at = now
            return True

    def finish_generation(self):
        with self._lock:
            self._generation_in_progress = False
