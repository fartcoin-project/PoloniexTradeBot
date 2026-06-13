"""Schedule settings stored in config.json."""

from __future__ import annotations

import re

DEFAULT_SCHEDULE = {
    "enabled": False,
    "time": "18:00",
    "budget": None,
    "start_after_missed": True,
}

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{1,2})$")


def normalize_schedule(raw):
    """Return a validated schedule dict."""
    data = raw if isinstance(raw, dict) else {}
    enabled = bool(data.get("enabled", DEFAULT_SCHEDULE["enabled"]))

    time_text = str(data.get("time") or DEFAULT_SCHEDULE["time"]).strip()
    match = _TIME_RE.match(time_text)
    if match:
        hour = max(0, min(23, int(match.group(1))))
        minute = max(0, min(59, int(match.group(2))))
        time_text = f"{hour:02d}:{minute:02d}"
    else:
        time_text = DEFAULT_SCHEDULE["time"]

    budget = data.get("budget", DEFAULT_SCHEDULE["budget"])
    if budget is not None and budget != "":
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            budget = None
    else:
        budget = None

    start_after_missed = data.get(
        "start_after_missed",
        DEFAULT_SCHEDULE["start_after_missed"],
    )
    if start_after_missed is None:
        start_after_missed = DEFAULT_SCHEDULE["start_after_missed"]

    return {
        "enabled": enabled,
        "time": time_text,
        "budget": budget,
        "start_after_missed": bool(start_after_missed),
    }


def schedule_budget_from_config(cfg):
    """Budget for a scheduled run: schedule override or main config budget."""
    schedule = normalize_schedule(cfg.get("schedule"))
    if schedule["budget"] is not None:
        return float(schedule["budget"])
    return float(cfg.get("budget", 0))


def schedule_summary(schedule):
    """Short label for the sidebar status line."""
    schedule = normalize_schedule(schedule)
    if not schedule["enabled"]:
        return "Off"
    missed = " · start if missed" if schedule["start_after_missed"] else ""
    budget = (
        f" · budget {schedule['budget']}"
        if schedule["budget"] is not None
        else ""
    )
    return f"Daily {schedule['time']}{budget}{missed}"
