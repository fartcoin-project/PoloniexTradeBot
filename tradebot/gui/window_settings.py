"""Persist main window size/position between sessions."""

import json
import os

from runtime_paths import app_dir

DEFAULT_WIDTH = 1320
DEFAULT_HEIGHT = 900
MIN_WIDTH = 900
MIN_HEIGHT = 640
DEFAULT_LOG_WIDTH = 340
MIN_LOG_WIDTH = 200
MAX_LOG_WIDTH = 900


def _path():
    return os.path.join(app_dir(), "data", "gui_settings.json")


def _load_settings_file():
    path = _path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}


def _write_settings_file(data):
    path = _path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_session_log_width():
    saved = _load_settings_file().get("session_log_width", DEFAULT_LOG_WIDTH)
    try:
        width = int(saved)
    except (TypeError, ValueError):
        width = DEFAULT_LOG_WIDTH
    return max(MIN_LOG_WIDTH, min(MAX_LOG_WIDTH, width))


def save_session_log_width(width):
    width = max(MIN_LOG_WIDTH, min(MAX_LOG_WIDTH, int(width)))
    data = _load_settings_file()
    data["session_log_width"] = width
    _write_settings_file(data)
    return width


def load_window_geometry():
    defaults = {
        "width": DEFAULT_WIDTH,
        "height": DEFAULT_HEIGHT,
        "x": None,
        "y": None,
        "maximized": False,
    }
    saved = _load_settings_file().get("window") or {}
    return {**defaults, **saved}


def save_window_geometry(window):
    from PySide6.QtCore import Qt

    maximized = bool(window.windowState() & Qt.WindowState.WindowMaximized)
    if maximized:
        normal = window.normalGeometry()
        payload = {
            "width": normal.width(),
            "height": normal.height(),
            "x": normal.x(),
            "y": normal.y(),
            "maximized": True,
        }
    else:
        geo = window.geometry()
        payload = {
            "width": geo.width(),
            "height": geo.height(),
            "x": geo.x(),
            "y": geo.y(),
            "maximized": False,
        }
    payload["width"] = max(MIN_WIDTH, int(payload["width"]))
    payload["height"] = max(MIN_HEIGHT, int(payload["height"]))
    data = _load_settings_file()
    data["window"] = payload
    _write_settings_file(data)
