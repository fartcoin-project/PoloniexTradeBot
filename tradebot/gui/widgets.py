"""Reusable UI building blocks."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.theme import TEXT_MUTED


class ScrollNeutralSlider(QSlider):
    """Slider that ignores the mouse wheel so parent scroll areas keep scrolling."""

    def wheelEvent(self, event):
        event.ignore()


class SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self.setObjectName("sectionTitle")


class PanelHeading(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("panelHeading")


class StatCard(QFrame):
    def __init__(self, label, value="—", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        self.label = QLabel(label)
        self.label.setObjectName("statLabel")
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        self.value.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.label)
        layout.addWidget(self.value)

    def set_value(self, text):
        self.value.setText(text)

    def set_label(self, text):
        self.label.setText(text)


class EmptyState(QFrame):
    def __init__(self, title, hint="", parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 14px; font-weight: 600; color: #c9d1d9;")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        if hint:
            sub = QLabel(hint)
            sub.setObjectName("emptyHint")
            sub.setWordWrap(True)
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(sub)


class Panel(QFrame):
    """Card container with optional heading."""

    def __init__(self, heading=None, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(10)
        if heading:
            self.layout.addWidget(PanelHeading(heading))


class StatusPill(QWidget):
    _COLORS = {
        "ready": "#66bb6a",
        "busy": "#F7931A",
        "error": "#ef5350",
        "warn": "#ffb74d",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.dot = QLabel("●")
        self.dot.setFixedWidth(14)
        self.text = QLabel("Ready")
        row.addWidget(self.dot)
        row.addWidget(self.text, stretch=1)
        self.set_state("ready", "Ready")

    def set_state(self, state, message):
        color = self._COLORS.get(state, self._COLORS["ready"])
        self.text.setText(message)
        self.text.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 600;"
        )
        self.dot.setStyleSheet(f"color: {color}; font-size: 10px;")


class CollapsibleGroup(QFrame):
    """Sidebar section that expands/collapses to show action buttons."""

    def __init__(self, title, *, expanded=False, parent=None):
        super().__init__(parent)
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._header = QPushButton()
        self._header.setObjectName("collapseHeader")
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._toggle)
        self._refresh_header()

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(4)
        self._body.setVisible(expanded)

        layout.addWidget(self._header)
        layout.addWidget(self._body)

    def _refresh_header(self):
        arrow = "▼" if self._header.isChecked() else "▶"
        self._header.setText(f"{arrow}  {self._title}")

    def _toggle(self):
        open_section = self._header.isChecked()
        self._body.setVisible(open_section)
        self._refresh_header()

    def add_action(self, label, callback, *, style=None):
        btn = QPushButton(label)
        btn.setObjectName(style or "sidebarBtn")
        btn.clicked.connect(callback)
        self._body_layout.addWidget(btn)
        return btn


class WorkflowStepList(QFrame):
    """Flat sidebar workflow: section title + step rows with done checkbox and action button."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setSpacing(6)

        heading = QLabel(title.upper())
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        self._heading = heading
        self._steps = {}

    def add_step(self, step_num, label, action_id, callback, *, style=None):
        row = QHBoxLayout()
        row.setSpacing(4)
        row.setContentsMargins(0, 0, 0, 0)

        check = QCheckBox()
        check.setObjectName("stepDone")
        check.setEnabled(False)
        check.setFixedWidth(20)
        check.setToolTip("Step completed")

        btn = QPushButton(f"Step {step_num} — {label}")
        btn.setObjectName(style or "sidebarBtn")
        btn.clicked.connect(callback)

        row.addWidget(check, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(btn, stretch=1)

        wrapper = QWidget()
        wrapper.setLayout(row)
        self.layout().addWidget(wrapper)

        self._steps[action_id] = check
        return btn

    def set_done(self, action_id, done):
        check = self._steps.get(action_id)
        if check is not None:
            check.setChecked(done)

    def set_title(self, title):
        self._heading.setText(title.upper())

    def action_ids(self):
        return list(self._steps.keys())


class CollapsibleSection(QFrame):
    """Dashboard section with expand/collapse header (replaces scroll areas)."""

    def __init__(self, title, *, expanded=False, parent=None):
        super().__init__(parent)
        self._title = title
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self._header = QPushButton()
        self._header.setObjectName("collapseHeader")
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._toggle)
        self._refresh_header()
        header_row.addWidget(self._header, stretch=1)

        self._header_extra = QHBoxLayout()
        self._header_extra.setSpacing(6)
        header_row.addLayout(self._header_extra)

        layout.addLayout(header_row)

        self._body = QWidget()
        self._body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(8)
        self._body.setVisible(expanded)
        layout.addWidget(self._body, 0, Qt.AlignmentFlag.AlignTop)

    def add_header_widget(self, widget):
        self._header_extra.addWidget(widget)

    def set_content(self, widget, *, stretch=0):
        self._body_layout.addWidget(widget, stretch)

    def set_expanded(self, expanded):
        if self._header.isChecked() != expanded:
            self._header.setChecked(expanded)
            self._toggle()

    def is_expanded(self):
        return self._header.isChecked()

    def set_title(self, title):
        self._title = title
        self._refresh_header()

    def _refresh_header(self):
        arrow = "▼" if self._header.isChecked() else "▶"
        self._header.setText(f"{arrow}  {self._title.upper()}")

    def _toggle(self):
        open_section = self._header.isChecked()
        self._body.setVisible(open_section)
        self._refresh_header()
        if open_section:
            self._body.updateGeometry()
            self.updateGeometry()


class SessionLogSidebar(QFrame):
    """Right-hand session log panel; collapsed by default."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logSidebar")
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("logSidebarHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 10, 10)
        header_layout.setSpacing(8)

        title = QLabel("SESSION LOG")
        title.setObjectName("sectionTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ghostBtn")
        clear_btn.setFixedWidth(56)
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)

        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        header_layout.addWidget(self.auto_scroll_check)

        layout.addWidget(header)

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.log_text, stretch=1)

        self.set_expanded(False)

    def clear(self):
        self.log_text.clear()

    def set_expanded(self, expanded):
        self._expanded = bool(expanded)
        if self._expanded:
            self.show()
        else:
            self.hide()

    def is_expanded(self):
        return self._expanded
