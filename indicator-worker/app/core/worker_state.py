"""In-memory worker readiness and queue tracking."""

import threading

_lock = threading.Lock()
_queue_size = 0
_ready = False


def mark_ready() -> None:
    global _ready
    with _lock:
        _ready = True


def mark_not_ready() -> None:
    global _ready
    with _lock:
        _ready = False


def is_ready() -> bool:
    with _lock:
        return _ready


def queue_size() -> int:
    with _lock:
        return _queue_size


class task_slot:
    """Context manager that tracks in-flight calculation tasks."""

    def __enter__(self):
        global _queue_size
        with _lock:
            _queue_size += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _queue_size
        with _lock:
            _queue_size -= 1
        return False
