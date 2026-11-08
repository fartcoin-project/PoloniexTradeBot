"""Tests for llm_config normalization."""

from llm_config import llm_root_url, normalize_llm_config


def test_normalize_defaults():
    cfg = normalize_llm_config(None)
    assert cfg["base_url"] == "http://127.0.0.1:8000/v1"
    assert cfg["auto_place"] is False
    assert cfg["loop_enabled"] is False
    assert cfg["status_reports_enabled"] is True
    assert cfg["loop_interval_minutes"] == 60
    assert cfg["status_interval_minutes"] == 15
    assert cfg["colibri_autostart"] is False
    assert cfg["colibri_model"] == ""


def test_normalize_adds_v1_suffix():
    cfg = normalize_llm_config({"base_url": "http://127.0.0.1:8000"})
    assert cfg["base_url"] == "http://127.0.0.1:8000/v1"


def test_normalize_clamps_intervals():
    cfg = normalize_llm_config({"loop_interval_minutes": 0, "status_interval_minutes": -3})
    assert cfg["loop_interval_minutes"] == 1
    assert cfg["status_interval_minutes"] == 1


def test_llm_root_url():
    assert llm_root_url("http://127.0.0.1:8000/v1") == "http://127.0.0.1:8000"
