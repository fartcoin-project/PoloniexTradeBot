"""Colibri chat + autonomous status feed panel."""

from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.theme import DANGER, SUCCESS, TEXT_MUTED
from gui.widgets import Panel


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.send_requested = None
        self.analyze_requested = None
        self.status_requested = None
        self.propose_requested = None
        self.cycle_requested = None
        self.health_requested = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(12)

        status_panel = Panel("Colibri")
        self.status_label = QLabel("Colibri: unknown")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        self.status_label.setWordWrap(True)
        status_panel.layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.health_btn = QPushButton("Check")
        self.health_btn.setObjectName("ghostBtn")
        self.health_btn.clicked.connect(self._on_health)
        btn_row.addWidget(self.health_btn)
        self.analyze_btn = QPushButton("Analyseer portfolio")
        self.analyze_btn.setObjectName("ghostBtn")
        self.analyze_btn.clicked.connect(self._on_analyze)
        btn_row.addWidget(self.analyze_btn)
        self.propose_btn = QPushButton("AI voorstellen")
        self.propose_btn.setObjectName("ghostBtn")
        self.propose_btn.clicked.connect(self._on_propose)
        btn_row.addWidget(self.propose_btn)
        self.cycle_btn = QPushButton("AI cycle")
        self.cycle_btn.setObjectName("ghostBtn")
        self.cycle_btn.clicked.connect(self._on_cycle)
        btn_row.addWidget(self.cycle_btn)
        self.status_btn = QPushButton("Status nu")
        self.status_btn.setObjectName("ghostBtn")
        self.status_btn.clicked.connect(self._on_status)
        btn_row.addWidget(self.status_btn)
        btn_row.addStretch()
        status_panel.layout.addLayout(btn_row)
        layout.addWidget(status_panel)

        chat_panel = Panel("Chat")
        self.transcript = QPlainTextEdit()
        self.transcript.setObjectName("logView")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText(
            "Praat met Colibri over je portfolio. Autonome statusberichten verschijnen hier ook."
        )
        chat_panel.layout.addWidget(self.transcript, stretch=1)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Vraag Colibri iets…")
        self.input_edit.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_edit, stretch=1)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("saveBtn")
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)
        chat_panel.layout.addLayout(input_row)
        layout.addWidget(chat_panel, stretch=1)

    def set_busy(self, busy: bool):
        for w in (
            self.send_btn,
            self.input_edit,
            self.analyze_btn,
            self.propose_btn,
            self.cycle_btn,
            self.status_btn,
            self.health_btn,
        ):
            w.setEnabled(not busy)

    def set_llm_status(self, payload: dict):
        ok = bool((payload or {}).get("ok"))
        detail = (payload or {}).get("detail") or ""
        llm = (payload or {}).get("llm") or {}
        model = llm.get("model") or (
            ((payload or {}).get("models") or [""])[0] if (payload or {}).get("models") else ""
        )
        auto = "aan" if llm.get("auto_place") else "uit"
        loop = "aan" if llm.get("loop_enabled") else "uit"
        status_on = "aan" if llm.get("status_reports_enabled") else "uit"
        color = SUCCESS if ok else DANGER
        text = (
            f"Colibri {'online' if ok else 'offline'}"
            f" · model {model or '—'}"
            f" · auto-place {auto}"
            f" · loop {loop}"
            f" · status {status_on}"
        )
        if detail and not ok:
            text += f" · {detail}"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")

    def load_history(self, entries):
        self.transcript.clear()
        for entry in entries or []:
            self.append_entry(entry, scroll=False)
        self._scroll_end()

    def append_entry(self, entry: dict, scroll=True):
        role = (entry or {}).get("role") or "assistant"
        msg_type = (entry or {}).get("type") or "chat"
        content = (entry or {}).get("content") or ""
        when = (entry or {}).get("time") or ""
        if msg_type == "status" or role == "system":
            prefix = f"[{when}] STATUS"
            line = f"{prefix}\n{content}\n"
        elif role == "user":
            line = f"[{when}] Jij\n{content}\n"
        else:
            label = "Colibri" if msg_type == "chat" else f"Colibri ({msg_type})"
            line = f"[{when}] {label}\n{content}\n"
        self.transcript.appendPlainText(line)
        if scroll:
            self._scroll_end()

    def _scroll_end(self):
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcript.setTextCursor(cursor)

    def _on_send(self):
        text = self.input_edit.text().strip()
        if not text:
            return
        self.input_edit.clear()
        if callable(self.send_requested):
            self.send_requested(text)

    def _on_analyze(self):
        if callable(self.analyze_requested):
            self.analyze_requested()

    def _on_propose(self):
        if callable(self.propose_requested):
            self.propose_requested()

    def _on_cycle(self):
        if callable(self.cycle_requested):
            self.cycle_requested()

    def _on_status(self):
        if callable(self.status_requested):
            self.status_requested()

    def _on_health(self):
        if callable(self.health_requested):
            self.health_requested()
