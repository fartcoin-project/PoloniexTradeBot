"""Tests for llm_config normalization."""

import os

import llm_config
from llm_config import llm_root_url, normalize_llm_config


def test_normalize_defaults(monkeypatch, tmp_path):
    def fake_expanduser(path):
        if path == "~":
            return str(tmp_path)
        if isinstance(path, str) and path.startswith("~/"):
            return os.path.join(str(tmp_path), path[2:].replace("/", os.sep))
        return path

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    monkeypatch.setattr(llm_config, "colibri_models_dir", lambda: str(tmp_path / "missing-appdata"))
    cfg = normalize_llm_config(None)
    assert cfg["base_url"] == "http://127.0.0.1:8000/v1"
    assert cfg["auto_place"] is False
    assert cfg["loop_enabled"] is False
    assert cfg["status_reports_enabled"] is True
    assert cfg["loop_interval_minutes"] == 60
    assert cfg["status_interval_minutes"] == 15
    assert cfg["colibri_autostart"] is False
    assert cfg["colibri_model"] == ""
    assert cfg["coli_vk_device"] == ""
    assert cfg["models_dir"] == ""


def test_normalize_models_dir_prefers_appdata(monkeypatch, tmp_path):
    appdata = tmp_path / "appdata-colibri-models"
    home = tmp_path / "colibri-models"
    appdata.mkdir()
    home.mkdir()

    def fake_expanduser(path):
        if path == "~":
            return str(tmp_path)
        if isinstance(path, str) and path.startswith("~/"):
            return os.path.join(str(tmp_path), path[2:].replace("/", os.sep))
        return path

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    monkeypatch.setattr(llm_config, "colibri_models_dir", lambda: str(appdata))
    cfg = normalize_llm_config({})
    assert cfg["models_dir"] == str(appdata)

    cfg2 = normalize_llm_config({"models_dir": r"D:\models"})
    assert cfg2["models_dir"] == r"D:\models"


def test_normalize_models_dir_falls_back_to_home(monkeypatch, tmp_path):
    home = tmp_path / "colibri-models"
    home.mkdir()

    def fake_expanduser(path):
        if path == "~":
            return str(tmp_path)
        if isinstance(path, str) and path.startswith("~/"):
            return os.path.join(str(tmp_path), path[2:].replace("/", os.sep))
        return path

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    monkeypatch.setattr(
        llm_config, "colibri_models_dir", lambda: str(tmp_path / "missing-appdata")
    )
    cfg = normalize_llm_config({})
    assert cfg["models_dir"] == str(home)


def test_normalize_coli_vk_device():
    cfg = normalize_llm_config({"coli_vk_device": "  Arc A770  "})
    assert cfg["coli_vk_device"] == "Arc A770"


def test_normalize_adds_v1_suffix():
    cfg = normalize_llm_config({"base_url": "http://127.0.0.1:8000"})
    assert cfg["base_url"] == "http://127.0.0.1:8000/v1"


def test_normalize_clamps_intervals():
    cfg = normalize_llm_config({"loop_interval_minutes": 0, "status_interval_minutes": -3})
    assert cfg["loop_interval_minutes"] == 1
    assert cfg["status_interval_minutes"] == 1


def test_llm_root_url():
    assert llm_root_url("http://127.0.0.1:8000/v1") == "http://127.0.0.1:8000"
