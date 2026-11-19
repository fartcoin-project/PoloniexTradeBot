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
        "models_dir": r"C:\models",
        "auto_place": True,
        "loop_enabled": True,
        "loop_interval_minutes": 30,
        "status_reports_enabled": False,
        "status_interval_minutes": 5,
        "colibri_autostart": True,
        "colibri_model": "qwen36-35b",
        "coli_vk_device": "Arc",
    })
    fields = panel.get_llm_fields()
    assert fields["model"] == "glm"
    assert fields["models_dir"] == r"C:\models"
    assert fields["auto_place"] is True
    assert fields["loop_interval_minutes"] == 30
    assert fields["status_reports_enabled"] is False
    assert fields["colibri_autostart"] is True
    assert fields["colibri_model"] == "qwen36-35b"
    assert fields["coli_vk_device"] == "Arc"
    panel.set_colibri_gpu_status("Intel Arc A770", coli_vk_dev="4")
    assert "Arc" in panel.colibri_gpu_label.text()
    panel.set_colibri_models([
        {"id": "qwen36-35b", "local": True, "status": "local"},
        {"id": "other", "download_gb": 40, "status": "tight", "local": False},
    ])
    assert panel.get_selected_colibri_model() == "qwen36-35b"
    assert "local" in panel.colibri_model_combo.currentText()
    assert panel.colibri_download_btn.text() == "Use local model"
    panel.set_download_button_for_model(False)
    assert panel.colibri_download_btn.text() == "Download / setup model"


def test_options_colibri_pinned_visible_when_collapsed(qapp):
    from gui.panels import OptionsPanel

    panel = OptionsPanel()
    panel.resize(1000, 800)
    panel.show()
    qapp.processEvents()

    panel.llm_section.set_expanded(False)
    qapp.processEvents()
    assert panel.colibri_log.isVisible()
    assert panel.llm_enabled_check.isVisible()
    assert panel.colibri_start_btn.isVisible()
    assert panel.colibri_stop_btn.isVisible()
    assert panel.colibri_status_btn.isVisible()
    assert panel.colibri_progress.isVisible()
    assert panel.llm_autostart_check.isVisible()
    assert not panel.llm_base_url_edit.isVisible()
    assert not panel.llm_models_dir_edit.isVisible()
    assert not panel.llm_auto_place_check.isVisible()

    panel.llm_section.set_expanded(True)
    qapp.processEvents()
    assert panel.colibri_log.isVisible()
    assert panel.llm_base_url_edit.isVisible()
    assert panel.llm_models_dir_edit.isVisible()
    assert panel.llm_auto_place_check.isVisible()
    assert panel.llm_base_url_edit.maximumWidth() >= 100000
    assert panel.llm_models_dir_edit.maximumWidth() >= 100000


def test_options_error_log_min_height_when_expanded(qapp):
    from gui.panels import OptionsPanel

    panel = OptionsPanel()
    panel.resize(900, 700)
    panel.show()
    qapp.processEvents()

    panel.log_section.set_expanded(False)
    qapp.processEvents()
    assert panel.log_section.minimumHeight() == 0

    panel.log_section.set_expanded(True)
    qapp.processEvents()
    expected = int(panel.height() * 0.30)
    assert panel.log_section.minimumHeight() >= expected


def test_collapsible_section_pinned_slots(qapp):
    from PySide6.QtWidgets import QLabel

    from gui.widgets import CollapsibleSection

    section = CollapsibleSection("Demo", expanded=False)
    above = QLabel("above")
    body = QLabel("body")
    below = QLabel("below")
    section.set_pinned_above(above)
    section.set_content(body)
    section.set_pinned_below(below)
    section.show()
    qapp.processEvents()

    assert above.isVisible()
    assert below.isVisible()
    assert not body.isVisible()

    section.set_expanded(True)
    qapp.processEvents()
    assert above.isVisible()
    assert below.isVisible()
    assert body.isVisible()
