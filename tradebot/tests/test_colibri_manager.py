"""Unit tests for ColibriManager (no real Colibri / HF network)."""

import json
import os

import pytest

import colibri_manager as cm
import runtime_paths


def test_build_coli_cmd(monkeypatch, tmp_path):
    coli = tmp_path / "colibri" / "c"
    coli.mkdir(parents=True)
    (coli / "coli").write_text("#", encoding="utf-8")
    py = tmp_path / "python.exe"
    py.write_text("", encoding="utf-8")

    monkeypatch.setattr(cm, "resolve_python_exe", lambda: str(py))
    monkeypatch.setattr(cm, "resolve_coli_script", lambda: str(coli / "coli"))
    cmd = cm.build_coli_cmd("setup", "--list", "--json")
    assert cmd[0] == str(py)
    assert cmd[-3:] == ["setup", "--list", "--json"]


def test_child_env_injects_hf_token(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_paths, "app_dir", lambda: str(tmp_path))
    runtime_paths.save_hf_token("hf_test_secret")
    monkeypatch.setattr(cm, "colibri_state_dir", lambda: str(tmp_path / "state"))
    env = cm.child_env()
    assert env["HF_TOKEN"] == "hf_test_secret"
    assert env["HUGGING_FACE_HUB_TOKEN"] == "hf_test_secret"
    assert env["COLI_SETUP_HOME"] == str(tmp_path / "state")


def test_hf_token_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_paths, "app_dir", lambda: str(tmp_path))
    assert runtime_paths.read_hf_token() == ""
    runtime_paths.save_hf_token("abc123")
    assert runtime_paths.read_hf_token() == "abc123"
    runtime_paths.save_hf_token("")
    assert runtime_paths.read_hf_token() == ""
    assert os.path.isfile(runtime_paths.secrets_path())


def test_parse_json_output_trailing_noise():
    text = "hello\n{\"models\": [{\"id\": \"m1\"}]}\n"
    data = cm._parse_json_output(text)
    assert data["models"][0]["id"] == "m1"


def test_list_models_parses_array(monkeypatch):
    payload = [{"id": "a", "download_gb": 22, "recommended": True}]

    def fake_run(args, timeout=None, on_line=None):
        return 0, json.dumps(payload)

    monkeypatch.setattr(cm, "run_coli", fake_run)
    models = cm.list_models()
    assert models[0]["id"] == "a"


def test_resolve_colibri_root_dev(monkeypatch, tmp_path):
    root = tmp_path / "colibri"
    (root / "c").mkdir(parents=True)
    (root / "c" / "coli").write_text("x", encoding="utf-8")
    monkeypatch.setattr(cm, "_workspace_colibri_candidates", lambda: [str(root)])
    assert cm.resolve_colibri_root() == str(root)


def test_runtime_info_missing(monkeypatch):
    monkeypatch.setattr(
        cm,
        "resolve_colibri_root",
        lambda: (_ for _ in ()).throw(cm.ColibriManagerError("missing")),
    )
    info = cm.runtime_info()
    assert info["available"] is False
    assert "missing" in info["error"]
