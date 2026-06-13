"""Tests for BotService.run_async() threading, output, and cancel."""

import queue
import time

import pytest

from gui.service import BotService
from tests.conftest import seed_market_files


def _drain(log_queue, timeout=5.0):
    deadline = time.time() + timeout
    messages = []
    while time.time() < deadline:
        try:
            messages.append(log_queue.get(timeout=0.05))
        except queue.Empty:
            if any(tag == "done" for tag, _ in messages):
                break
    return messages


class TestRunAsync:
    def test_run_async_success_emits_lifecycle_events(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        seed_market_files(tradebot_env, coins=["ADA"])
        log_queue = queue.Queue()
        svc = BotService(log_queue)
        svc._ensure_loaded()
        monkeypatch.setattr(svc._tb, "advice", lambda show=False: None)

        thread = svc.run_async("refresh_advice")
        thread.join(timeout=10)

        messages = _drain(log_queue)
        tags = [tag for tag, _ in messages]
        assert ("status", "Running: refresh_advice...") in messages
        assert ("status", "Finished: refresh_advice") in messages
        assert tags.count("busy") >= 2
        assert True in [payload for tag, payload in messages if tag == "busy"]
        assert False in [payload for tag, payload in messages if tag == "busy"]
        assert "done" in tags

    def test_run_async_captures_print_output(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        seed_market_files(tradebot_env, coins=["ADA"])
        log_queue = queue.Queue()
        svc = BotService(log_queue)

        def noisy_advice(show=False):
            print("pipeline-test-output-line")

        svc._ensure_loaded()
        monkeypatch.setattr(svc._tb, "advice", noisy_advice)

        thread = svc.run_async("refresh_advice")
        thread.join(timeout=10)

        logs = [payload for tag, payload in _drain(log_queue) if tag == "log"]
        assert any("pipeline-test-output-line" in line for line in logs)

    def test_run_async_cancel_mid_run(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        seed_market_files(tradebot_env, coins=["ADA"])
        log_queue = queue.Queue()
        svc = BotService(log_queue)

        def slow_advice(show=False):
            import tradebot as tb

            for _ in range(40):
                tb.abort_if_cancelled()
                time.sleep(0.05)

        svc._ensure_loaded()
        monkeypatch.setattr(svc._tb, "advice", slow_advice)

        thread = svc.run_async("refresh_advice")
        time.sleep(0.15)
        assert svc.request_cancel() is True
        thread.join(timeout=10)

        messages = _drain(log_queue)
        errors = [payload for tag, payload in messages if tag == "error"]
        assert any("Emergency stop" in err for err in errors)
        assert not svc.is_busy()

    def test_request_cancel_when_idle_returns_false(self):
        svc = BotService(queue.Queue())
        assert svc.request_cancel() is False

    def test_run_async_unknown_action_raises(self):
        svc = BotService(queue.Queue())
        with pytest.raises(ValueError, match="Unknown action"):
            svc.run_async("not_a_real_action")
