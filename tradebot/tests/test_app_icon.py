"""Tests for GUI app icon path resolution."""

import os

from gui.app import resolve_app_icon_path


def test_resolve_app_icon_path_finds_project_icon(monkeypatch, tmp_path):
    icon = tmp_path / "icon.png"
    icon.write_bytes(b"\x89PNG\r\n\x1a\n")
    package = tmp_path / "tradebot"
    package.mkdir()
    monkeypatch.setattr("gui.app.bundle_dir", lambda: str(package))
    monkeypatch.setattr("gui.app.install_dir", lambda: str(package))
    assert resolve_app_icon_path() == str(icon)


def test_resolve_app_icon_path_prefers_bundle(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    install = tmp_path / "install"
    install.mkdir()
    bundled = bundle / "icon.png"
    bundled.write_bytes(b"png")
    (install / "icon.png").write_bytes(b"other")
    monkeypatch.setattr("gui.app.bundle_dir", lambda: str(bundle))
    monkeypatch.setattr("gui.app.install_dir", lambda: str(install))
    assert resolve_app_icon_path() == str(bundled)


def test_resolve_app_icon_path_missing(monkeypatch, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr("gui.app.bundle_dir", lambda: str(empty))
    monkeypatch.setattr("gui.app.install_dir", lambda: str(empty))
    assert resolve_app_icon_path() is None
