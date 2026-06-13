"""Tests for GUI window geometry persistence."""

import json

from gui.window_settings import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    load_window_geometry,
)


def test_load_window_geometry_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr("gui.window_settings.app_dir", lambda: str(tmp_path))
    geo = load_window_geometry()
    assert geo["width"] == DEFAULT_WIDTH
    assert geo["height"] == DEFAULT_HEIGHT
    assert geo["maximized"] is False


def test_load_window_geometry_from_file(tmp_path, monkeypatch):
    monkeypatch.setattr("gui.window_settings.app_dir", lambda: str(tmp_path))
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "gui_settings.json").write_text(
        json.dumps({
            "window": {"width": 1600, "height": 1000, "x": 40, "y": 30, "maximized": True},
            "session_log_width": 420,
        }),
        encoding="utf-8",
    )
    geo = load_window_geometry()
    assert geo["width"] == 1600
    assert geo["height"] == 1000
    assert geo["x"] == 40
    assert geo["maximized"] is True


def test_session_log_width_round_trip(tmp_path, monkeypatch):
    from gui.window_settings import (
        DEFAULT_LOG_WIDTH,
        load_session_log_width,
        save_session_log_width,
    )

    monkeypatch.setattr("gui.window_settings.app_dir", lambda: str(tmp_path))
    assert load_session_log_width() == DEFAULT_LOG_WIDTH
    save_session_log_width(480)
    assert load_session_log_width() == 480
    save_session_log_width(50)
    assert load_session_log_width() == 200
