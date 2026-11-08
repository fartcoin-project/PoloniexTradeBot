"""Smoke tests for ChatPanel."""

import pytest

pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication

from gui.chat_panel import ChatPanel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_chat_panel_append_and_status(qapp):
    panel = ChatPanel()
    panel.show()
    qapp.processEvents()
    panel.append_entry({
        "time": "2026-01-01T00:00:00",
        "role": "user",
        "type": "chat",
        "content": "Hallo",
    })
    panel.append_entry({
        "time": "2026-01-01T00:00:01",
        "role": "assistant",
        "type": "status",
        "content": "Alles ok",
    })
    text = panel.transcript.toPlainText()
    assert "Hallo" in text
    assert "STATUS" in text
    assert "Alles ok" in text
    panel.set_llm_status({
        "ok": True,
        "detail": "reachable",
        "models": ["m1"],
        "llm": {
            "model": "m1",
            "auto_place": False,
            "loop_enabled": True,
            "status_reports_enabled": True,
        },
    })
    assert "online" in panel.status_label.text()
    assert "loop aan" in panel.status_label.text()


def test_options_llm_fields_roundtrip(qapp):
    from gui.panels import OptionsPanel

    panel = OptionsPanel()
    panel.load_llm_fields({
        "enabled": True,
        "base_url": "http://127.0.0.1:8000/v1",
        "api_key": "local",
        "model": "glm",
        "auto_place": True,
        "loop_enabled": True,
        "loop_interval_minutes": 30,
        "status_reports_enabled": False,
        "status_interval_minutes": 5,
        "colibri_autostart": True,
        "colibri_model": "qwen36-35b",
    })
    fields = panel.get_llm_fields()
    assert fields["model"] == "glm"
    assert fields["auto_place"] is True
    assert fields["loop_interval_minutes"] == 30
    assert fields["status_reports_enabled"] is False
    assert fields["colibri_autostart"] is True
    assert fields["colibri_model"] == "qwen36-35b"
    panel.set_colibri_models([
        {"id": "qwen36-35b", "download_gb": 22, "status": "good", "recommended": True},
        {"id": "other", "download_gb": 40, "status": "tight"},
    ])
    assert panel.get_selected_colibri_model() == "qwen36-35b"
