"""Cooperative cancel for GUI emergency stop."""

import threading
import time

from api_compat import OperationCancelled

__all__ = ["OperationCancelled", "CancelController"]

# Real OS sleep — never replaced when GUI patches time.sleep for interruptible_sleep.
_REAL_SLEEP = time.sleep


class CancelController:
    def __init__(self):
        self._event = threading.Event()

    def reset(self):
        self._event.clear()

    def request(self):
        self._event.set()

    def is_set(self):
        return self._event.is_set()

    def wait_or_raise(self, seconds):
        if self._event.wait(timeout=float(seconds)):
            raise OperationCancelled("Emergency stop — cancelled by user")

    def interruptible_sleep(self, seconds):
        end = time.time() + float(seconds)
        while time.time() < end:
            if self._event.is_set():
                raise OperationCancelled("Emergency stop — cancelled by user")
            _REAL_SLEEP(min(0.05, end - time.time()))
