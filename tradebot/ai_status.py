"""Persist AI chat/status messages and debounce autonomous reports."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional

STATUS_MAX = 100
CHAT_MAX = 200
DEFAULT_DEBOUNCE_SEC = 60.0


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class AiMessageStore:
    def __init__(self, root: str):
        self.root = root
        self.data_dir = os.path.join(root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.status_path = os.path.join(self.data_dir, "ai_status.json")
        self.chat_path = os.path.join(self.data_dir, "ai_chat.json")
        self._lock = threading.Lock()
        self._last_status_at = 0.0

    def _load(self, path, default):
        if not os.path.exists(path):
            return default
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return default

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def append_chat(self, role: str, content: str, msg_type: str = "chat") -> dict:
        entry = {
            "time": _now_iso(),
            "role": role,
            "type": msg_type,
            "content": content,
        }
        with self._lock:
            history = self._load(self.chat_path, [])
            if not isinstance(history, list):
                history = []
            history.append(entry)
            self._save(self.chat_path, history[-CHAT_MAX:])
            if msg_type == "status":
                status = self._load(self.status_path, [])
                if not isinstance(status, list):
                    status = []
                status.append(entry)
                self._save(self.status_path, status[-STATUS_MAX:])
                self._last_status_at = time.monotonic()
        return entry

    def load_chat(self) -> list:
        with self._lock:
            data = self._load(self.chat_path, [])
            return data if isinstance(data, list) else []

    def load_status(self) -> list:
        with self._lock:
            data = self._load(self.status_path, [])
            return data if isinstance(data, list) else []

    def should_emit_status(self, debounce_sec: float = DEFAULT_DEBOUNCE_SEC) -> bool:
        with self._lock:
            return (time.monotonic() - self._last_status_at) >= float(debounce_sec)

    def mark_status_emitted(self):
        with self._lock:
            self._last_status_at = time.monotonic()
