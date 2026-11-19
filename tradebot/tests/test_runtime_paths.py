"""Tests for runtime_paths credential and first-run setup."""

import json
import os
import sys

import runtime_paths as rp
from runtime_paths import (
    PLACEHOLDER_API_KEY,
    PLACEHOLDER_API_SECRET,
    api_config_ready,
    app_dir,
    data_dir,
    install_dir,
    read_api_credentials,
    save_api_credentials,
    setup_runtime,
    _migrate_legacy_data_if_needed,
)


class TestRuntimePaths:
    def test_setup_runtime_creates_folders_and_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("runtime_paths.app_dir", lambda: str(tmp_path))
        monkeypatch.setattr("runtime_paths.is_frozen", lambda: False)

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

    def test_data_dir_dev_uses_package_dir(self, monkeypatch):
        monkeypatch.setattr("runtime_paths.is_frozen", lambda: False)
        expected = os.path.dirname(os.path.abspath(rp.__file__))
        assert data_dir() == expected
        assert app_dir() == expected
        assert install_dir() == expected

    def test_data_dir_frozen_uses_local_appdata(self, tmp_path, monkeypatch):
        monkeypatch.setattr("runtime_paths.is_frozen", lambda: True)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
        monkeypatch.setattr(
            sys,
            "executable",
            str(tmp_path / "Programs" / "TradeBot" / "TradeBot.exe"),
        )
        assert data_dir() == str(tmp_path / "Local" / "TradeBot")
        assert app_dir() == data_dir()
        assert install_dir() == str(tmp_path / "Programs" / "TradeBot")

    def test_data_dir_frozen_fallback_without_localappdata(self, tmp_path, monkeypatch):
        monkeypatch.setattr("runtime_paths.is_frozen", lambda: True)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.setattr("os.path.expanduser", lambda _p: str(tmp_path / "home"))
        assert data_dir() == str(tmp_path / "home" / "AppData" / "Local" / "TradeBot")

    def test_migrate_copies_once_when_appdata_empty(self, tmp_path):
        source = tmp_path / "install"
        dest = tmp_path / "AppData" / "TradeBot"
        source.mkdir()
        (source / "config.json").write_text('{"budget": 1.5}', encoding="utf-8")
        (source / "tradebot_config.py").write_text("SECRET_API_KEY = 'k'\n", encoding="utf-8")
        (source / "json").mkdir()
        (source / "json" / "cache.json").write_text("{}", encoding="utf-8")
        (source / "logs").mkdir()
        (source / "logs" / "tradebot.log").write_text("hi\n", encoding="utf-8")

        _migrate_legacy_data_if_needed(str(source), str(dest))

        assert (dest / "config.json").read_text(encoding="utf-8") == '{"budget": 1.5}'
        assert (dest / "tradebot_config.py").is_file()
        assert (dest / "json" / "cache.json").is_file()
        assert (dest / "logs" / "tradebot.log").is_file()

    def test_migrate_does_not_overwrite_existing_appdata(self, tmp_path):
        source = tmp_path / "install"
        dest = tmp_path / "AppData" / "TradeBot"
        source.mkdir()
        dest.mkdir(parents=True)
        (source / "config.json").write_text('{"budget": 9}', encoding="utf-8")
        (dest / "config.json").write_text('{"budget": 1}', encoding="utf-8")

        _migrate_legacy_data_if_needed(str(source), str(dest))

        assert (dest / "config.json").read_text(encoding="utf-8") == '{"budget": 1}'

    def test_setup_runtime_frozen_migrates_then_seeds(self, tmp_path, monkeypatch):
        install = tmp_path / "Programs" / "TradeBot"
        data = tmp_path / "Local" / "TradeBot"
        install.mkdir(parents=True)
        (install / "config.json").write_text(
            '{\n    "time": "",\n    "quote_currency": "ETH",\n    "budget": 2.0,\n'
            '    "balance": 0.0,\n    "advice": "0.0005",\n    "exclude": []\n}\n',
            encoding="utf-8",
        )
        (install / "tradebot_config.py").write_text(
            "SECRET_API_KEY = 'migrated'\nSECRET_API_SECRET = 'secret'\n",
            encoding="utf-8",
        )

        monkeypatch.setattr("runtime_paths.is_frozen", lambda: True)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
        monkeypatch.setattr(sys, "executable", str(install / "TradeBot.exe"))
        monkeypatch.chdir(tmp_path)

        setup_runtime()

        assert data_dir() == str(data)
        assert (data / "config.json").is_file()
        cfg = json.loads((data / "config.json").read_text(encoding="utf-8"))
        assert cfg["quote_currency"] == "ETH"
        assert (data / "tradebot_config.py").is_file()
        for folder in ("json", "orderbooks", "data", "logs"):
            assert (data / folder).is_dir()
        assert os.getcwd() == str(data)
