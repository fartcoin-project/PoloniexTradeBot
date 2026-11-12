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


def test_runtime_info_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cm,
        "resolve_colibri_root",
        lambda: (_ for _ in ()).throw(cm.ColibriManagerError("missing")),
    )
    info = cm.runtime_info(str(tmp_path / "models"))
    assert info["available"] is False
    assert "missing" in info["error"]
    assert info["models_dir"] == str((tmp_path / "models").resolve())
    assert os.path.isdir(info["models_dir"])


def test_list_local_and_model_present(tmp_path):
    root = tmp_path / "models"
    empty = root / "empty"
    empty.mkdir(parents=True)
    good = root / "qwen"
    good.mkdir()
    (good / "config.json").write_text("{}", encoding="utf-8")
    models = cm.list_local_models(str(root))
    assert models == [{"id": "qwen", "local": True, "status": "local"}]
    assert cm.model_present(str(root), "qwen") is True
    assert cm.model_present(str(root), "empty") is False
    assert cm.model_present(str(root), "missing") is False


def test_list_models_merged(monkeypatch, tmp_path):
    root = tmp_path / "models"
    local = root / "local-m"
    local.mkdir(parents=True)
    (local / "f.bin").write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        cm,
        "list_models",
        lambda on_line=None: [
            {"id": "local-m", "download_gb": 1},
            {"id": "remote-m", "download_gb": 2, "recommended": True},
        ],
    )
    merged = cm.list_models_merged(str(root))
    assert merged[0]["id"] == "local-m"
    assert merged[0]["local"] is True
    assert merged[1]["id"] == "remote-m"
    assert merged[1]["local"] is False


def test_resolve_models_dir_creates(tmp_path):
    target = tmp_path / "new-models"
    path = cm.resolve_models_dir(str(target))
    assert path == str(target.resolve())
    assert os.path.isdir(path)


def test_download_model_skips_when_local(tmp_path, monkeypatch):
    root = tmp_path / "models"
    model = root / "qwen36-35b"
    model.mkdir(parents=True)
    (model / "weights.bin").write_text("x", encoding="utf-8")
    called = {"n": 0}

    def fake_run(*a, **k):
        called["n"] += 1
        return 0, "ok"

    monkeypatch.setattr(cm, "run_coli", fake_run)
    monkeypatch.setattr(cm, "ensure_setup_vk_device", lambda preferred_name=None: {})
    out = cm.download_model("qwen36-35b", models_dir=str(root))
    assert "Using local" in out
    assert called["n"] == 0


_SAMPLE_VULKANINFO = """
GPU0:
	vendorID           = 0x10de
	deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
	deviceName         = NVIDIA GeForce GTX 1060 6GB
GPU1:
	vendorID           = 0x10de
	deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
	deviceName         = Microsoft Direct3D12 (NVIDIA GeForce GTX 1060 6GB)
GPU2:
	vendorID           = 0x8086
	deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
	deviceName         = Intel(R) UHD Graphics 770
GPU4:
	vendorID           = 0x8086
	deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
	deviceName         = Intel(R) Arc(TM) A770 Graphics
GPU5:
	vendorID           = 0x8086
	deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
	deviceName         = Microsoft Direct3D12 (Intel(R) Arc(TM) A770 Graphics)
"""


def test_parse_vulkaninfo_summary_skips_wrappers_via_list_filter():
    devices = cm.parse_vulkaninfo_summary(_SAMPLE_VULKANINFO)
    assert len(devices) == 5
    names = [d["name"] for d in devices]
    assert "Intel(R) Arc(TM) A770 Graphics" in names
    assert any(cm.is_d3d12_wrapper_device(n) for n in names)


def test_pick_vulkan_device_prefers_arc_over_gtx():
    devices = cm.parse_vulkaninfo_summary(_SAMPLE_VULKANINFO)
    chosen = cm.pick_vulkan_device(devices)
    assert chosen is not None
    assert chosen["index"] == 4
    assert "Arc" in chosen["name"]
    assert not cm.is_d3d12_wrapper_device(chosen["name"])


def test_pick_vulkan_device_preferred_name():
    devices = cm.parse_vulkaninfo_summary(_SAMPLE_VULKANINFO)
    chosen = cm.pick_vulkan_device(devices, preferred_name="GTX 1060")
    assert chosen["index"] == 0
    chosen_arc = cm.pick_vulkan_device(devices, preferred_name="A770")
    assert chosen_arc["index"] == 4


def test_ensure_setup_vk_device_writes_coli_vk_dev(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    setup = {
        "status": "ready",
        "backend": "vulkan",
        "gpu": "NVIDIA GeForce GTX 1060 6GB",
        "env": {"COLI_VULKAN": "1"},
    }
    (state / "setup.json").write_text(json.dumps(setup), encoding="utf-8")
    monkeypatch.setattr(cm, "colibri_state_dir", lambda: str(state))
    monkeypatch.setattr(
        cm,
        "list_vulkan_devices",
        lambda include_wrappers=False: [
            d
            for d in cm.parse_vulkaninfo_summary(_SAMPLE_VULKANINFO)
            if not cm.is_d3d12_wrapper_device(d["name"])
        ],
    )
    result = cm.ensure_setup_vk_device()
    assert result["changed"] is True
    assert result["index"] == 4
    data = json.loads((state / "setup.json").read_text(encoding="utf-8"))
    assert data["env"]["COLI_VK_DEV"] == "4"
    assert "Arc" in data["gpu"]


def test_gpu_selection_warning_when_gtx_active():
    devices = [
        d
        for d in cm.parse_vulkaninfo_summary(_SAMPLE_VULKANINFO)
        if not cm.is_d3d12_wrapper_device(d["name"])
    ]
    warn = cm.gpu_selection_warning("NVIDIA GeForce GTX 1060 6GB", devices)
    assert "Arc" in warn
    assert cm.gpu_selection_warning("Intel(R) Arc(TM) A770 Graphics", devices) == ""


def test_read_install_state_stale_build_idle(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    (state / "setup.json").write_text(
        json.dumps({"status": "ready", "backend": "vulkan"}),
        encoding="utf-8",
    )
    (state / "install-state.json").write_text(
        json.dumps({"phase": "build", "pid": 99999999, "engine": "qwen36"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cm, "colibri_state_dir", lambda: str(state))
    monkeypatch.setattr(cm, "_pid_alive", lambda pid: False)
    assert cm.read_install_state() == {}
    raw = cm.read_install_state(raw=True)
    assert raw["phase"] == "build"


def test_clear_stale_install_state(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    path = state / "install-state.json"
    path.write_text(
        json.dumps({"phase": "build", "pid": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cm, "colibri_state_dir", lambda: str(state))
    monkeypatch.setattr(cm, "_pid_alive", lambda pid: False)
    assert cm.clear_stale_install_state() is True
    assert not path.exists()


def test_default_models_dir_prefers_appdata(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata-models"
    appdata.mkdir()
    (tmp_path / "colibri-models").mkdir()
    monkeypatch.setattr(cm, "colibri_models_dir", lambda: str(appdata))
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: str(tmp_path) if p == "~" else p,
    )
    assert cm.default_models_dir() == str(appdata)
