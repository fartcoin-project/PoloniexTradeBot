"""Windows Task Scheduler integration for daily headless runs."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass

from gui.schedule_config import normalize_schedule, schedule_summary
from runtime_paths import app_dir, is_frozen

TASK_NAME = "TradeBot Daily"


@dataclass
class ScheduleApplyResult:
    ok: bool
    message: str
    task_state: str | None = None


def _ps_escape(value):
    return str(value).replace("'", "''")


def _scheduled_command():
    """Return (executable, arguments, working_directory) for headless runs."""
    bot_dir = app_dir()
    project_root = os.path.dirname(bot_dir)
    exe_beside_root = os.path.join(project_root, "TradeBot.exe")

    if is_frozen():
        return sys.executable, "--scheduled --action start_bot", bot_dir
    if os.path.isfile(exe_beside_root):
        return exe_beside_root, "--scheduled --action start_bot", bot_dir
    script = os.path.join(bot_dir, "run_scheduled.py")
    return sys.executable, f'"{script}" --action start_bot', bot_dir


def _run_powershell(script):
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )


def get_windows_task_state():
    """Return Task Scheduler state string or None if missing / unsupported."""
    if sys.platform != "win32":
        return None
    script = (
        f"$t = Get-ScheduledTask -TaskName '{_ps_escape(TASK_NAME)}' "
        "-ErrorAction SilentlyContinue; "
        "if ($t) { $t.State }"
    )
    result = _run_powershell(script)
    state = (result.stdout or "").strip()
    return state or None


def apply_windows_schedule(schedule):
    """Register, update, or remove the daily Windows scheduled task."""
    schedule = normalize_schedule(schedule)
    if sys.platform != "win32":
        return ScheduleApplyResult(
            ok=False,
            message="Daily schedule requires Windows Task Scheduler.",
            task_state=None,
        )

    if not schedule["enabled"]:
        script = (
            f"Unregister-ScheduledTask -TaskName '{_ps_escape(TASK_NAME)}' "
            "-Confirm:$false -ErrorAction SilentlyContinue"
        )
        _run_powershell(script)
        return ScheduleApplyResult(ok=True, message="Schedule disabled.", task_state=None)

    execute, arguments, workdir = _scheduled_command()
    start_when = "$true" if schedule["start_after_missed"] else "$false"
    time_text = schedule["time"]
    script = f"""
$Action = New-ScheduledTaskAction -Execute '{_ps_escape(execute)}' -Argument '{_ps_escape(arguments)}' -WorkingDirectory '{_ps_escape(workdir)}'
$Trigger = New-ScheduledTaskTrigger -Daily -At '{_ps_escape(time_text)}'
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable:{start_when} -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$Principal = New-ScheduledTaskPrincipal -UserId 'CurrentUser' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName '{_ps_escape(TASK_NAME)}' -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
"""
    result = _run_powershell(script)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Unknown error").strip()
        return ScheduleApplyResult(
            ok=False,
            message=f"Could not register scheduled task: {detail}",
            task_state=None,
        )

    state = get_windows_task_state()
    summary = schedule_summary(schedule)
    missed = " (start if missed)" if schedule["start_after_missed"] else ""
    return ScheduleApplyResult(
        ok=True,
        message=f"Scheduled: {summary}{missed}",
        task_state=state,
    )
