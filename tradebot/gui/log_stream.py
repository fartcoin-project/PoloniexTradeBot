import os
import re
import sys
import threading
import traceback
from datetime import datetime

from runtime_paths import app_dir

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return ANSI_ESCAPE.sub("", text)


def read_session_log(path=None, *, errors_only=False, max_lines=2000):
    """Read tail of tradebot.log; optionally filter ERROR / FAILED lines."""
    log_path = path or SessionFileLogger.get().log_path
    if not os.path.exists(log_path):
        return "No log file yet.\n", 0, log_path
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()
    if errors_only:
        lines = [
            line
            for line in lines
            if "[ERROR]" in line.upper() or " FAILED " in line.upper()
        ]
    if max_lines and len(lines) > max_lines:
        lines = lines[-max_lines:]
    text = "".join(lines) if lines else (
        "No errors logged yet.\n" if errors_only else "Log file is empty.\n"
    )
    return text, len(lines), log_path


class SessionFileLogger:
    """Append-only session log beside the app (logs/tradebot.log)."""

    _instance = None
    _init_lock = threading.Lock()

    def __init__(self, path):
        self.path = path
        self._write_lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    @classmethod
    def get(cls):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    log_path = os.path.join(app_dir(), "logs", "tradebot.log")
                    cls._instance = cls(log_path)
        return cls._instance

    @property
    def log_path(self):
        return self.path

    def write_line(self, tag, line):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._write_lock:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(f"{ts} [{tag.upper()}] {line}\n")

    def session_start(self, action):
        self.write_line("session", f"===== {action} =====")

    def session_end(self, action, ok=True):
        status = "OK" if ok else "FAILED"
        self.write_line("session", f"----- {action} {status} -----")

    def log_exception(self, action, exc):
        self.write_line("error", f"{action}: {exc}")
        self.write_line("error", traceback.format_exc())


class QueueLogWriter:
    """Redirect stdout/stderr into a thread-safe queue for the GUI log panel."""

    def __init__(self, log_queue, tag="log", file_logger=None):
        self.log_queue = log_queue
        self.tag = tag
        self.file_logger = file_logger
        self._buffer = ""

    def _emit(self, cleaned):
        if not cleaned:
            return
        self.log_queue.put((self.tag, cleaned))
        if self.file_logger is not None:
            self.file_logger.write_line(self.tag, cleaned)

    def _emit_complete_lines(self):
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            cleaned = strip_ansi(line).rstrip("\r")
            self._emit(cleaned)

    def write(self, text):
        if not text:
            return
        if "\r" in text:
            parts = text.split("\r")
            for part in parts[:-1]:
                cleaned = strip_ansi(part).strip()
                if cleaned:
                    self._emit(cleaned)
            self._buffer = parts[-1]
            self._emit_complete_lines()
            return
        self._buffer += text
        self._emit_complete_lines()

    def flush(self):
        if self._buffer.strip():
            cleaned = strip_ansi(self._buffer).rstrip("\r")
            self._emit(cleaned)
            self._buffer = ""


class ProgressCapture:
    """Map tradebot update_progress() 0–1 calls to GUI progress bar percentage."""

    def __init__(self, log_queue, file_logger=None):
        self.log_queue = log_queue
        self.file_logger = file_logger
        self._phase_start = 0.0
        self._phase_span = 100.0
        self._last_logged_pct = -1.0

    def reset(self):
        self._phase_start = 0.0
        self._phase_span = 100.0
        self._last_logged_pct = -1.0
        self._emit(0.0)

    def set_phase(self, start_pct, end_pct):
        self._phase_start = float(start_pct)
        self._phase_span = float(end_pct) - float(start_pct)
        self._last_logged_pct = -1.0

    def _log_progress_line(self, pct):
        shown = max(0.0, min(100.0, pct))
        if abs(shown - self._last_logged_pct) < 1.0 and shown not in (0.0, 100.0):
            return
        self._last_logged_pct = shown
        block = int(round(33 * (shown / 100.0)))
        bar = "#" * block + "-" * (33 - block)
        line = f"  Updating: [{bar}] {shown:.0f}%"
        self.log_queue.put(("log", line))
        if self.file_logger is not None:
            self.file_logger.write_line("log", line)

    def _emit(self, pct):
        pct = max(0.0, min(100.0, pct))
        self.log_queue.put(("progress", pct))
        if self.file_logger is not None:
            self.file_logger.write_line("progress", f"{pct:.1f}%")

    def __call__(self, progress):
        local = max(0.0, min(1.0, float(progress)))
        pct = self._phase_start + local * self._phase_span
        self._log_progress_line(pct)
        self._emit(pct)
