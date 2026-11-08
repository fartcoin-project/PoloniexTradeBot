"""Tests for AI status message store and debounce."""

import time

from ai_status import AiMessageStore


def test_append_and_load_chat(tmp_path):
    store = AiMessageStore(str(tmp_path))
    store.append_chat("user", "Hallo", msg_type="chat")
    store.append_chat("assistant", "Status ok", msg_type="status")
    chat = store.load_chat()
    assert len(chat) == 2
    assert chat[0]["role"] == "user"
    status = store.load_status()
    assert len(status) == 1
    assert status[0]["type"] == "status"


def test_status_debounce(tmp_path):
    store = AiMessageStore(str(tmp_path))
    assert store.should_emit_status(debounce_sec=0.2) is True
    store.append_chat("assistant", "ping", msg_type="status")
    assert store.should_emit_status(debounce_sec=60) is False
    time.sleep(0.25)
    assert store.should_emit_status(debounce_sec=0.2) is True
