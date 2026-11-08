"""Manage bundled Colibri as a subprocess (setup / download / start / stop)."""

from __future__ import annotations

import json
import os
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


class ColibriManagerError(RuntimeError):
    pass


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


def ensure_data_dirs():
    os.makedirs(colibri_models_dir(), exist_ok=True)
    os.makedirs(colibri_state_dir(), exist_ok=True)


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


def download_model(model_id: str, on_line: ProgressCallback = None) -> str:
    model_id = (model_id or "").strip()
    if not model_id:
        raise ColibriManagerError("Model id is required")
    ensure_data_dirs()
    args = [
        "setup",
        "--yes",
        "--model",
        model_id,
        "--dir",
        colibri_models_dir(),
        "--no-start",
    ]
    # Long-running; no hard timeout — caller can cancel via process kill later
    code, out = run_coli(args, timeout=None, on_line=on_line)
    if code != 0:
        raise ColibriManagerError(f"coli setup download failed ({code}): {out[-3000:]}")
    return out


def start_server(on_line: ProgressCallback = None) -> str:
    ensure_data_dirs()
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


def read_install_state() -> dict:
    """Best-effort progress from Colibri setup home."""
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


def runtime_info() -> dict:
    info = {
        "python_exe": None,
        "coli_script": None,
        "colibri_root": None,
        "models_dir": colibri_models_dir(),
        "state_dir": colibri_state_dir(),
        "frozen": is_frozen(),
        "hf_token_set": bool(read_hf_token()),
    }
    try:
        info["python_exe"] = resolve_python_exe()
        info["colibri_root"] = resolve_colibri_root()
        info["coli_script"] = resolve_coli_script()
        info["available"] = True
    except ColibriManagerError as exc:
        info["available"] = False
        info["error"] = str(exc)
    return info
