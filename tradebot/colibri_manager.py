"""Manage bundled Colibri as a subprocess (setup / download / start / stop)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
from typing import Callable, Optional

from runtime_paths import (
    colibri_models_dir,
    colibri_state_dir,
    install_dir,
    is_frozen,
    read_hf_token,
)

ProgressCallback = Optional[Callable[[str], None]]

_TERMINAL_INSTALL_PHASES = frozenset({
    "ready",
    "done",
    "idle",
    "complete",
    "completed",
    "finished",
    "error",
    "failed",
})


class ColibriManagerError(RuntimeError):
    pass


def setup_json_path() -> str:
    return os.path.join(colibri_state_dir(), "setup.json")


def read_setup_json() -> dict:
    path = setup_json_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_setup_json(data: dict) -> None:
    home = colibri_state_dir()
    os.makedirs(home, exist_ok=True)
    path = setup_json_path()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def _workspace_colibri_candidates():
    here = os.path.dirname(os.path.abspath(__file__))
    project = os.path.dirname(here)
    parent = os.path.dirname(project)
    return [
        os.path.join(install_dir(), "colibri"),
        os.path.join(project, "colibri"),
        os.path.join(parent, "colibri"),
        r"C:\workspace\projects\colibri",
    ]


def resolve_colibri_root() -> str:
    for candidate in _workspace_colibri_candidates():
        coli = os.path.join(candidate, "c", "coli")
        if os.path.isfile(coli):
            return candidate
    raise ColibriManagerError(
        "Colibri runtime not found. Rebuild the installer payload "
        "(installer/payload/colibri) or keep the sibling colibri repo."
    )


def resolve_python_exe() -> str:
    bundled = os.path.join(install_dir(), "runtime", "python", "python.exe")
    if os.path.isfile(bundled):
        return bundled
    # Dev / non-frozen: current interpreter
    return sys.executable


def resolve_coli_script() -> str:
    return os.path.join(resolve_colibri_root(), "c", "coli")


def default_models_dir() -> str:
    """Prefer TradeBot AppData models dir; fall back to ~/colibri-models."""
    appdata = colibri_models_dir()
    if os.path.isdir(appdata):
        return appdata
    preferred = os.path.join(os.path.expanduser("~"), "colibri-models")
    if os.path.isdir(preferred):
        return preferred
    return appdata


def resolve_models_dir(models_dir=None) -> str:
    path = str(models_dir or "").strip()
    if not path:
        path = default_models_dir()
    if not path:
        path = colibri_models_dir()
    path = os.path.abspath(os.path.expanduser(path))
    os.makedirs(path, exist_ok=True)
    return path


def ensure_data_dirs(models_dir=None):
    resolve_models_dir(models_dir)
    os.makedirs(colibri_state_dir(), exist_ok=True)


def parse_vulkaninfo_summary(text: str) -> list[dict]:
    """Parse `vulkaninfo --summary` GPU blocks into device dicts."""
    devices: list[dict] = []
    current: Optional[dict] = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        match = re.match(r"^GPU(\d+)\s*:", line, re.IGNORECASE)
        if match:
            if current is not None:
                devices.append(current)
            current = {
                "index": int(match.group(1)),
                "name": "",
                "vendor_id": "",
                "type": "other",
            }
            continue
        if current is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "devicename":
            current["name"] = value
        elif key == "vendorid":
            current["vendor_id"] = value.lower()
        elif key == "devicetype":
            kind = value.lower()
            if "discrete" in kind:
                current["type"] = "discrete"
            elif "integrated" in kind:
                current["type"] = "integrated"
            elif "virtual" in kind:
                current["type"] = "virtual"
            elif "cpu" in kind:
                current["type"] = "cpu"
            else:
                current["type"] = "other"
    if current is not None:
        devices.append(current)
    return devices


def is_d3d12_wrapper_device(name: str) -> bool:
    return "microsoft direct3d12" in (name or "").lower()


def list_vulkan_devices(*, include_wrappers: bool = False) -> list[dict]:
    """Enumerate Vulkan devices via vulkaninfo --summary."""
    exe = shutil.which("vulkaninfo") or (
        r"C:\Windows\System32\vulkaninfo.exe" if sys.platform == "win32" else None
    )
    if not exe or (sys.platform == "win32" and not os.path.isfile(exe)):
        return []
    try:
        result = subprocess.run(
            [exe, "--summary"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    text = (result.stdout or "") + "\n" + (result.stderr or "")
    devices = parse_vulkaninfo_summary(text)
    if include_wrappers:
        return devices
    return [d for d in devices if not is_d3d12_wrapper_device(str(d.get("name") or ""))]


def _device_match_score(device: dict, preferred_name: str) -> int:
    name = str(device.get("name") or "")
    needle = (preferred_name or "").strip()
    if not needle:
        return 0
    if name.lower() == needle.lower():
        return 300
    if needle.lower() in name.lower():
        return 200
    return 0


def _is_intel_arc(device: dict) -> bool:
    name = str(device.get("name") or "").lower()
    vendor = str(device.get("vendor_id") or "").lower()
    intel = vendor in {"0x8086", "8086"} or "intel" in name
    return intel and "arc" in name


def pick_vulkan_device(
    devices: list[dict],
    preferred_name: Optional[str] = None,
) -> Optional[dict]:
    """Choose a Vulkan device; prefer name match, else Intel Arc discrete."""
    usable = [
        d for d in (devices or [])
        if not is_d3d12_wrapper_device(str(d.get("name") or ""))
        and str(d.get("type") or "") != "cpu"
    ]
    if not usable:
        return None
    preferred = (preferred_name or "").strip()
    if preferred:
        scored = sorted(
            usable,
            key=lambda d: (
                -_device_match_score(d, preferred),
                0 if d.get("type") == "discrete" else 1,
                int(d.get("index") or 0),
            ),
        )
        if _device_match_score(scored[0], preferred) > 0:
            return scored[0]
    arc = [
        d for d in usable
        if _is_intel_arc(d) and d.get("type") == "discrete"
    ]
    if arc:
        return sorted(arc, key=lambda d: int(d.get("index") or 0))[0]
    discrete = [d for d in usable if d.get("type") == "discrete"]
    if discrete:
        return sorted(discrete, key=lambda d: int(d.get("index") or 0))[0]
    return sorted(usable, key=lambda d: int(d.get("index") or 0))[0]


def resolve_coli_vk_dev(
    preferred_name: Optional[str] = None,
    devices: Optional[list[dict]] = None,
) -> Optional[dict]:
    """
    Resolve preferred Vulkan device.
    Returns {index, name, ...} or None when enumeration fails / empty.
    """
    enumerated = devices if devices is not None else list_vulkan_devices()
    return pick_vulkan_device(enumerated, preferred_name=preferred_name)


def gpu_selection_warning(
    active_gpu: Optional[str],
    devices: Optional[list[dict]] = None,
) -> str:
    """Warn when setup still points at NVIDIA while an Arc card is present."""
    active = (active_gpu or "").strip()
    enumerated = devices if devices is not None else list_vulkan_devices()
    has_arc = any(_is_intel_arc(d) and d.get("type") == "discrete" for d in enumerated)
    if not has_arc or not active:
        return ""
    lower = active.lower()
    if "arc" in lower:
        return ""
    if "nvidia" in lower or "geforce" in lower or "gtx" in lower or "rtx" in lower:
        return (
            f"Colibri GPU is '{active}' but an Intel Arc card is available; "
            "set coli_vk_device / COLI_VK_DEV to prefer Arc."
        )
    return ""


def ensure_setup_vk_device(preferred_name: Optional[str] = None) -> dict:
    """
    Persist COLI_VK_DEV (+ gpu label) into setup.json when a preferred device
    can be resolved. Returns {changed, index, name, warning}.
    """
    result = {
        "changed": False,
        "index": None,
        "name": "",
        "warning": "",
        "devices": [],
    }
    devices = list_vulkan_devices()
    result["devices"] = devices
    chosen = resolve_coli_vk_dev(preferred_name=preferred_name, devices=devices)
    if not chosen:
        setup = read_setup_json()
        result["warning"] = gpu_selection_warning(str(setup.get("gpu") or ""), devices)
        return result

    index = int(chosen["index"])
    name = str(chosen.get("name") or "")
    result["index"] = index
    result["name"] = name

    setup = read_setup_json()
    if not setup:
        # No setup yet — nothing durable to patch until coli setup runs.
        result["warning"] = gpu_selection_warning(name if "arc" in name.lower() else "", devices)
        return result

    env = setup.get("env") if isinstance(setup.get("env"), dict) else {}
    env = dict(env)
    desired = str(index)
    changed = env.get("COLI_VK_DEV") != desired or str(setup.get("gpu") or "") != name
    if setup.get("backend") == "vulkan" or env.get("COLI_VULKAN") == "1":
        env["COLI_VULKAN"] = "1"
    env["COLI_VK_DEV"] = desired
    setup["env"] = env
    setup["gpu"] = name
    if changed:
        write_setup_json(setup)
        result["changed"] = True
    result["warning"] = gpu_selection_warning(str(setup.get("gpu") or ""), devices)
    return result


def clear_stale_install_state() -> bool:
    """Remove install-state.json when it looks stuck (dead pid / leftover build)."""
    path = os.path.join(colibri_state_dir(), "install-state.json")
    if not os.path.isfile(path):
        return False
    state = read_install_state(raw=True)
    if not state:
        return False
    if install_state_is_active(state):
        return False
    phase = str(state.get("phase") or "").strip().lower()
    if phase in _TERMINAL_INSTALL_PHASES:
        return False
    # Leftover non-terminal phase with no live pid → clear
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def _pid_alive(pid) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    if sys.platform == "win32":
        try:
            # Avoid importing psutil; OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, value)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(value, 0)
    except OSError:
        return False
    return True


def install_state_is_active(state: Optional[dict] = None) -> bool:
    data = state if isinstance(state, dict) else read_install_state(raw=True)
    if not data:
        return False
    phase = str(data.get("phase") or "").strip().lower()
    if phase in _TERMINAL_INSTALL_PHASES:
        return False
    if data.get("running") is True:
        return True
    return _pid_alive(data.get("pid"))


def _dir_looks_like_model(path: str) -> bool:
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    return True
                if entry.is_dir(follow_symlinks=False):
                    try:
                        with os.scandir(entry.path) as nested:
                            if any(nested):
                                return True
                    except OSError:
                        continue
    except OSError:
        return False
    return False


def list_local_models(models_dir) -> list[dict]:
    root = str(models_dir or "").strip()
    if not root:
        root = default_models_dir()
    if not root:
        return []
    root = os.path.abspath(os.path.expanduser(root))
    if not os.path.isdir(root):
        return []
    found: list[dict] = []
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    for name in names:
        if name.startswith("."):
            continue
        path = os.path.join(root, name)
        if not os.path.isdir(path):
            continue
        if not _dir_looks_like_model(path):
            continue
        found.append({"id": name, "local": True, "status": "local"})
    return found


def model_present(models_dir, model_id) -> bool:
    mid = str(model_id or "").strip()
    if not mid:
        return False
    root = str(models_dir or "").strip()
    if not root:
        root = default_models_dir()
    if not root:
        return False
    path = os.path.join(os.path.abspath(os.path.expanduser(root)), mid)
    return os.path.isdir(path) and _dir_looks_like_model(path)


def list_models_merged(models_dir, on_line: ProgressCallback = None) -> list[dict]:
    local = list_local_models(models_dir)
    local_ids = {str(m.get("id") or "") for m in local}
    merged = list(local)
    for item in list_models(on_line=on_line):
        mid = str(item.get("id") or "").strip()
        if not mid or mid in local_ids:
            continue
        entry = dict(item)
        entry["local"] = False
        merged.append(entry)
    return merged


# Back-compat aliases used by older service helpers
def scan_local_models(models_dir=None) -> list[dict]:
    return list_local_models(models_dir)


def merge_model_lists(local_models: list[dict], catalog: list[dict]) -> list[dict]:
    by_id = {}
    for item in local_models or []:
        mid = str(item.get("id") or "").strip()
        if mid:
            entry = dict(item)
            entry["local"] = True
            entry["status"] = item.get("status") or "local"
            by_id[mid] = entry
    for item in catalog or []:
        mid = str(item.get("id") or "").strip()
        if not mid or mid in by_id:
            continue
        entry = dict(item)
        entry["local"] = False
        by_id[mid] = entry
    locals_first = [v for v in by_id.values() if v.get("local")]
    rest = [v for v in by_id.values() if not v.get("local")]
    locals_first.sort(key=lambda m: str(m.get("id") or ""))
    rest.sort(key=lambda m: (not m.get("recommended"), str(m.get("id") or "")))
    return locals_first + rest


def child_env(extra=None) -> dict:
    env = os.environ.copy()
    token = read_hf_token()
    if token:
        env["HF_TOKEN"] = token
        env["HUGGING_FACE_HUB_TOKEN"] = token
    env["COLI_SETUP_HOME"] = colibri_state_dir()
    # Prefer UTF-8 logs
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if extra:
        env.update(extra)
    return env


def _popen_kwargs():
    kwargs = {
        "cwd": resolve_colibri_root(),
        "env": child_env(),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if sys.platform == "win32":
        # Avoid flashing console windows from GUI
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kwargs


def build_coli_cmd(*args: str) -> list[str]:
    return [resolve_python_exe(), resolve_coli_script(), *args]


def run_coli(
    args: list[str],
    *,
    timeout: Optional[float] = None,
    on_line: ProgressCallback = None,
) -> tuple[int, str]:
    ensure_data_dirs()
    cmd = build_coli_cmd(*args)
    kwargs = _popen_kwargs()
    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        raise ColibriManagerError(f"Failed to start Colibri: {exc}") from exc

    lines: list[str] = []
    assert proc.stdout is not None

    def reader():
        for line in proc.stdout:
            text = line.rstrip("\n")
            lines.append(text)
            if on_line:
                try:
                    on_line(text)
                except Exception:
                    pass

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        thread.join(timeout=2)
        raise ColibriManagerError(f"Colibri timed out: {' '.join(args)}") from exc
    thread.join(timeout=5)
    return int(code or 0), "\n".join(lines)


def _parse_json_output(text: str):
    text = (text or "").strip()
    if not text:
        raise ColibriManagerError("Empty JSON from Colibri")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Scan for the first JSON value (object or array) when logs precede it
    for i, ch in enumerate(text):
        if ch not in "{[":
            continue
        for end in range(len(text), i, -1):
            try:
                return json.loads(text[i:end])
            except json.JSONDecodeError:
                continue
    raise ColibriManagerError("Could not parse Colibri JSON")


def list_models(on_line: ProgressCallback = None) -> list[dict]:
    code, out = run_coli(
        ["setup", "--list", "--json"],
        timeout=180,
        on_line=on_line,
    )
    if code != 0:
        raise ColibriManagerError(f"coli setup --list failed ({code}): {out[-2000:]}")
    data = _parse_json_output(out)
    if isinstance(data, dict) and "models" in data:
        models = data["models"]
    elif isinstance(data, list):
        models = data
    else:
        models = []
    if not isinstance(models, list):
        raise ColibriManagerError("Unexpected --list --json shape")
    return [m for m in models if isinstance(m, dict)]


def download_model(
    model_id: str,
    models_dir=None,
    on_line: ProgressCallback = None,
    *,
    coli_vk_device: Optional[str] = None,
) -> str:
    model_id = (model_id or "").strip()
    if not model_id:
        raise ColibriManagerError("Model id is required")
    target = resolve_models_dir(models_dir)
    ensure_data_dirs(target)
    if model_present(target, model_id):
        msg = f"Using local model {model_id} in {os.path.join(target, model_id)}"
        if on_line:
            on_line(msg)
        ensure_setup_vk_device(coli_vk_device)
        return msg
    args = [
        "setup",
        "--yes",
        "--model",
        model_id,
        "--dir",
        target,
        "--no-start",
    ]
    code, out = run_coli(args, timeout=None, on_line=on_line)
    if code != 0:
        raise ColibriManagerError(f"coli setup download failed ({code}): {out[-3000:]}")
    ensure_setup_vk_device(coli_vk_device)
    clear_stale_install_state()
    return out


def start_server(
    models_dir=None,
    on_line: ProgressCallback = None,
    *,
    coli_vk_device: Optional[str] = None,
) -> str:
    # `coli start` has no documented --dir; setup state + COLI_SETUP_HOME carry the path.
    resolve_models_dir(models_dir)
    ensure_data_dirs(models_dir)
    clear_stale_install_state()
    pinned = ensure_setup_vk_device(coli_vk_device)
    if on_line and pinned.get("name"):
        idx = pinned.get("index")
        msg = f"Vulkan device: {pinned['name']}"
        if idx is not None:
            msg += f" (COLI_VK_DEV={idx})"
        on_line(msg)
        if pinned.get("warning"):
            on_line(pinned["warning"])
    code, out = run_coli(
        ["start", "--background", "--no-browser"],
        timeout=300,
        on_line=on_line,
    )
    if code != 0:
        # Some builds use different flag names — try without --no-browser
        code2, out2 = run_coli(
            ["start", "--background"],
            timeout=300,
            on_line=on_line,
        )
        if code2 != 0:
            raise ColibriManagerError(
                f"coli start failed ({code}/{code2}): {out[-1500:]}\n{out2[-1500:]}"
            )
        return out2
    return out


def stop_server(on_line: ProgressCallback = None) -> str:
    code, out = run_coli(["stop"], timeout=120, on_line=on_line)
    if code != 0:
        raise ColibriManagerError(f"coli stop failed ({code}): {out[-1500:]}")
    return out


def status_json(on_line: ProgressCallback = None) -> dict:
    code, out = run_coli(["status", "--json"], timeout=60, on_line=on_line)
    if code != 0:
        return {"ok": False, "raw": out, "exit_code": code}
    try:
        data = _parse_json_output(out)
        if isinstance(data, dict):
            data.setdefault("ok", True)
            return data
    except ColibriManagerError:
        pass
    return {"ok": code == 0, "raw": out, "exit_code": code}


def _load_install_state_file() -> dict:
    home = colibri_state_dir()
    for name in ("install-state.json", "state.json", "setup-state.json"):
        path = os.path.join(home, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            continue
    # Also search nested
    if os.path.isdir(home):
        for root, _dirs, files in os.walk(home):
            if "install-state.json" in files:
                path = os.path.join(root, "install-state.json")
                try:
                    with open(path, encoding="utf-8") as handle:
                        data = json.load(handle)
                    if isinstance(data, dict):
                        return data
                except (OSError, json.JSONDecodeError):
                    pass
                break
    return {}


def read_install_state(*, raw: bool = False) -> dict:
    """Best-effort progress from Colibri setup home.

    When raw is False, stale non-terminal install phases with a dead pid are
    treated as idle (empty dict) so the GUI does not look stuck on build.
    """
    data = _load_install_state_file()
    if raw or not data:
        return data
    if install_state_is_active(data):
        return data
    phase = str(data.get("phase") or "").strip().lower()
    if phase and phase not in _TERMINAL_INSTALL_PHASES:
        setup = read_setup_json()
        if str(setup.get("status") or "").strip().lower() == "ready":
            return {}
    return data


def runtime_info(models_dir=None) -> dict:
    info = {
        "python_exe": None,
        "coli_script": None,
        "colibri_root": None,
        "models_dir": resolve_models_dir(models_dir),
        "state_dir": colibri_state_dir(),
        "frozen": is_frozen(),
        "hf_token_set": bool(read_hf_token()),
    }
    setup = read_setup_json()
    if setup:
        info["setup_gpu"] = str(setup.get("gpu") or "")
        env = setup.get("env") if isinstance(setup.get("env"), dict) else {}
        info["coli_vk_dev"] = str(env.get("COLI_VK_DEV") or "")
    try:
        info["python_exe"] = resolve_python_exe()
        info["colibri_root"] = resolve_colibri_root()
        info["coli_script"] = resolve_coli_script()
        info["available"] = True
    except ColibriManagerError as exc:
        info["available"] = False
        info["error"] = str(exc)
    warning = gpu_selection_warning(str(info.get("setup_gpu") or ""))
    if warning:
        info["gpu_warning"] = warning
    return info
