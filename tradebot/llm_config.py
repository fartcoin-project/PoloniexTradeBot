"""Normalize and default Colibri / OpenAI-compatible LLM settings."""

from __future__ import annotations

DEFAULT_LLM = {
    "enabled": True,
    "base_url": "http://127.0.0.1:8000/v1",
    "api_key": "local",
    "model": "",
    "auto_place": False,
    "loop_enabled": False,
    "loop_interval_minutes": 60,
    "status_reports_enabled": True,
    "status_interval_minutes": 15,
    "colibri_autostart": False,
    "colibri_model": "",
}


def normalize_llm_config(raw=None):
    """Return a complete llm config dict with typed defaults."""
    src = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULT_LLM)
    out["enabled"] = bool(src.get("enabled", out["enabled"]))
    base = str(src.get("base_url") or out["base_url"]).strip().rstrip("/")
    if not base.endswith("/v1"):
        # Accept root URL like http://127.0.0.1:8000
        if base.endswith("/"):
            base = base[:-1]
        if not base.endswith("/v1"):
            base = f"{base}/v1"
    out["base_url"] = base
    out["api_key"] = str(src.get("api_key") if src.get("api_key") is not None else out["api_key"]).strip() or "local"
    out["model"] = str(src.get("model") or "").strip()
    out["auto_place"] = bool(src.get("auto_place", False))
    out["loop_enabled"] = bool(src.get("loop_enabled", False))
    try:
        loop_mins = int(src.get("loop_interval_minutes", out["loop_interval_minutes"]))
    except (TypeError, ValueError):
        loop_mins = out["loop_interval_minutes"]
    out["loop_interval_minutes"] = max(1, loop_mins)
    out["status_reports_enabled"] = bool(
        src.get("status_reports_enabled", out["status_reports_enabled"])
    )
    try:
        status_mins = int(src.get("status_interval_minutes", out["status_interval_minutes"]))
    except (TypeError, ValueError):
        status_mins = out["status_interval_minutes"]
    out["status_interval_minutes"] = max(1, status_mins)
    out["colibri_autostart"] = bool(src.get("colibri_autostart", False))
    out["colibri_model"] = str(src.get("colibri_model") or "").strip()
    return out


def llm_root_url(base_url):
    """Strip trailing /v1 for health endpoint."""
    url = (base_url or "").rstrip("/")
    if url.endswith("/v1"):
        return url[:-3] or "http://127.0.0.1:8000"
    return url or "http://127.0.0.1:8000"
