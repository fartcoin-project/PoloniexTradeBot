"""Tests for GUI cancel/sleep patching (no recursion when time.sleep is hooked)."""

import time
from unittest.mock import patch

from gui.cancel import CancelController


class TestInterruptibleSleep:
    def test_does_not_recurse_when_time_sleep_is_patched(self):
        cancel = CancelController()
        real_sleep = time.sleep
        time.sleep = cancel.interruptible_sleep
        try:
            cancel.interruptible_sleep(0.02)
        finally:
            time.sleep = real_sleep

    def test_raises_when_cancelled_during_sleep(self):
        from api_compat import OperationCancelled

        cancel = CancelController()
        cancel.request()
        real_sleep = time.sleep
        time.sleep = cancel.interruptible_sleep
        try:
            import pytest

            with pytest.raises(OperationCancelled):
                cancel.interruptible_sleep(1.0)
        finally:
            time.sleep = real_sleep
