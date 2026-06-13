"""Tests for runtime_paths credential and first-run setup."""

import json

import pytest

from runtime_paths import (
    PLACEHOLDER_API_KEY,
    PLACEHOLDER_API_SECRET,
    api_config_ready,
    read_api_credentials,
    save_api_credentials,
    setup_runtime,
)


class TestRuntimePaths:
    def test_setup_runtime_creates_folders_and_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("runtime_paths.app_dir", lambda: str(tmp_path))

        setup_runtime()

        for folder in ("json", "orderbooks", "data", "logs"):
            assert (tmp_path / folder).is_dir()
        assert (tmp_path / "config.json").is_file()
        cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert cfg["quote_currency"] == "BTC"

    def test_api_config_ready_rejects_placeholders(self, tmp_path, monkeypatch):
        monkeypatch.setattr("runtime_paths.app_dir", lambda: str(tmp_path))
        cfg = type(
            "Cfg",
            (),
            {"SECRET_API_KEY": PLACEHOLDER_API_KEY, "SECRET_API_SECRET": PLACEHOLDER_API_SECRET},
        )()
        monkeypatch.setattr("runtime_paths.load_tradebot_config", lambda: cfg)
        assert api_config_ready() is False

    def test_save_and_read_api_credentials(self, tmp_path, monkeypatch):
        monkeypatch.setattr("runtime_paths.app_dir", lambda: str(tmp_path))
        save_api_credentials("real-key", "real-secret")
        cfg = type(
            "Cfg",
            (),
            {"SECRET_API_KEY": "real-key", "SECRET_API_SECRET": "real-secret"},
        )()
        monkeypatch.setattr("runtime_paths.load_tradebot_config", lambda: cfg)
        key, secret = read_api_credentials()
        assert key == "real-key"
        assert secret == "real-secret"
        assert api_config_ready() is True

    def test_read_api_credentials_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("runtime_paths.app_dir", lambda: str(tmp_path))
        assert read_api_credentials() == ("", "")
