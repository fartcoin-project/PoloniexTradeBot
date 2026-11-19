"""Tests for schedule config and Windows task integration."""

import pytest

from gui.schedule import TASK_NAME, apply_windows_schedule
from gui.schedule_config import (
    DEFAULT_SCHEDULE,
    normalize_schedule,
    schedule_budget_from_config,
    schedule_summary,
)


class TestScheduleConfig:
    def test_normalize_defaults(self):
        assert normalize_schedule({}) == DEFAULT_SCHEDULE

    def test_normalize_time_and_flags(self):
        sched = normalize_schedule({
            "enabled": True,
            "time": "9:5",
            "budget": "2.5",
            "start_after_missed": False,
        })
        assert sched["enabled"] is True
        assert sched["time"] == "09:05"
        assert sched["budget"] == 2.5
        assert sched["start_after_missed"] is False

    def test_schedule_budget_prefers_override(self):
        cfg = {"budget": 1.0, "schedule": {"budget": 3.5}}
        assert schedule_budget_from_config(cfg) == 3.5

    def test_schedule_budget_falls_back_to_main(self):
        cfg = {"budget": 1.25, "schedule": {"budget": None}}
        assert schedule_budget_from_config(cfg) == 1.25

    def test_schedule_summary_includes_missed_flag(self):
        text = schedule_summary({
            "enabled": True,
            "time": "18:00",
            "budget": None,
            "start_after_missed": True,
        })
        assert "18:00" in text
        assert "start if missed" in text


class TestApplyWindowsSchedule:
    def test_non_windows_returns_error(self, monkeypatch):
        monkeypatch.setattr("gui.schedule.sys.platform", "linux")
        result = apply_windows_schedule({"enabled": True, "time": "18:00"})
        assert result.ok is False
        assert "Windows" in result.message

    def test_disabled_unregisters_task(self, monkeypatch):
        monkeypatch.setattr("gui.schedule.sys.platform", "win32")
        calls = []

        def fake_run(script):
            calls.append(script)

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            return Result()

        monkeypatch.setattr("gui.schedule._run_powershell", fake_run)
        result = apply_windows_schedule({"enabled": False})
        assert result.ok is True
        assert TASK_NAME in calls[0]
        assert "Unregister-ScheduledTask" in calls[0]

    def test_enabled_uses_start_when_available_flag(self, monkeypatch):
        monkeypatch.setattr("gui.schedule.sys.platform", "win32")
        scripts = []

        def fake_run(script):
            scripts.append(script)

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            return Result()

        monkeypatch.setattr("gui.schedule._run_powershell", fake_run)
        monkeypatch.setattr("gui.schedule.get_windows_task_state", lambda: "Ready")

        result = apply_windows_schedule({
            "enabled": True,
            "time": "18:00",
            "start_after_missed": True,
        })
        assert result.ok is True
        assert "-StartWhenAvailable:$true" in scripts[0]

        result = apply_windows_schedule({
            "enabled": True,
            "time": "18:00",
            "start_after_missed": False,
        })
        assert result.ok is True
        assert "-StartWhenAvailable:$false" in scripts[1]
