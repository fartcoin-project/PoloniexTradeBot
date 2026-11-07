"""Shared colors and Qt stylesheet for TradeBot GUI."""

ACCENT = "#F7931A"
ACCENT_DIM = "#c97714"
BG_DARK = "#1a1a2e"
BG_PANEL = "#16213e"
BG_INPUT = "#0f3460"
BG_LOG = "#0d1117"
BORDER = "#1a508b"
TEXT = "#e0e0e0"
TEXT_MUTED = "#888888"
TEXT_DIM = "#c9d1d9"
SUCCESS = "#66bb6a"
DANGER = "#ef5350"
BUY = "#66bb6a"
SELL = "#ef5350"

STYLESHEET = f"""
QMainWindow, QWidget#root {{
    background-color: {BG_DARK};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}
QFrame#sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BG_INPUT};
}}
QFrame#sidebarSettings {{
    border-top: 1px solid {BG_INPUT};
    margin-top: 6px;
    padding-top: 4px;
}}
QScrollArea#sidebarScroll {{
    background: transparent;
    border: none;
}}
QScrollArea#sidebarScroll > QWidget > QWidget {{
    background: transparent;
}}
QFrame#sidebarSettings QLineEdit,
QFrame#sidebarSettings QComboBox {{
    min-height: 22px;
    font-size: 11px;
    padding: 2px 6px;
}}
QFrame#sidebarSettings QPushButton#ghostBtn {{
    text-align: center;
    padding: 3px 8px;
    font-size: 11px;
}}
QFrame#sidebarSettings QPushButton#saveBtn {{
    text-align: center;
    margin-top: 6px;
    padding: 4px 8px;
}}
QFrame#sidebarSettings QCheckBox {{
    min-height: 22px;
    padding: 2px 0;
}}
QFrame#panel {{
    background-color: {BG_PANEL};
    border: 1px solid {BG_INPUT};
    border-radius: 8px;
}}
QFrame#logSidebar {{
    background-color: {BG_LOG};
    border-left: 1px solid {BORDER};
}}
QFrame#logSidebarHeader {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}
QSplitter#centerSplitter::handle {{
    background-color: {BORDER};
}}
QSplitter#centerSplitter::handle:hover {{
    background-color: {ACCENT};
}}
QSplitter#centerSplitter::handle:horizontal {{
    width: 6px;
    margin: 0 1px;
}}
QPushButton#logToggleBtn {{
    background-color: #0a0a0a;
    color: #ffffff;
    border: 2px solid #3d3d3d;
    border-radius: 4px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    font-weight: bold;
    padding: 0;
    margin: 0 4px 0 8px;
    min-height: 0;
}}
QPushButton#logToggleBtn:hover {{
    background-color: #171717;
    border-color: #525252;
    color: #ffffff;
}}
QPushButton#logToggleBtn:checked {{
    background-color: #000000;
    color: #ffffff;
    border-color: #666666;
}}
QFrame#statCard {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#emptyState {{
    background-color: {BG_LOG};
    border: 1px dashed {BORDER};
    border-radius: 8px;
}}
QLabel#title {{
    color: {ACCENT};
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}
QLabel#subtitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#sectionTitle {{
    color: {TEXT_MUTED};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.2px;
    padding: 4px 0;
}}
QLabel#panelHeading {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 600;
}}
QLabel#statLabel {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 0.5px;
}}
QLabel#statValue {{
    color: {ACCENT};
    font-size: 15px;
    font-weight: bold;
}}
QLabel#statusReady {{
    color: {SUCCESS};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#statusBusy {{
    color: {ACCENT};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#statusError {{
    color: {DANGER};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#emptyHint {{
    color: {TEXT_MUTED};
    font-size: 12px;
    padding: 24px;
}}
QPushButton {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
    min-height: 22px;
    text-align: left;
}}
QPushButton:hover {{
    background-color: {BORDER};
    border-color: {ACCENT_DIM};
}}
QPushButton:pressed {{ background-color: #0a2848; }}
QPushButton:disabled {{
    background-color: #2a2a40;
    color: #555;
    border-color: transparent;
}}
QPushButton#sidebarBtn {{
    padding: 3px 6px 3px 8px;
    font-size: 11px;
    min-height: 24px;
    text-align: left;
}}
QCheckBox#stepDone {{
    spacing: 0;
}}
QCheckBox#stepDone::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid {BORDER};
    background: {BG_INPUT};
}}
QCheckBox#stepDone::indicator:checked {{
    background: {SUCCESS};
    border-color: {SUCCESS};
}}
QCheckBox#stepDone:disabled {{
    color: {TEXT_MUTED};
}}
QPushButton#collapseHeader {{
    background-color: transparent;
    color: {TEXT_MUTED};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 3px 6px;
    min-height: 20px;
    border: none;
}}
QPushButton#collapseHeader:hover {{
    color: {TEXT};
    background-color: {BG_INPUT};
}}
QPushButton#collapseHeader:checked {{
    color: {TEXT};
}}
QPushButton#primaryBtn {{
    background-color: {ACCENT};
    color: #111111;
    font-weight: bold;
    border-color: {ACCENT_DIM};
    padding: 5px 8px;
}}
QPushButton#primaryBtn:hover {{ background-color: {ACCENT_DIM}; }}
QPushButton#dangerBtn {{
    background-color: #8b2635;
    color: #ffe0e0;
    font-weight: bold;
    border-color: #a83244;
    padding: 4px 8px;
    font-size: 11px;
}}
QPushButton#dangerBtn:hover {{ background-color: #a83244; }}
QPushButton#ghostBtn {{
    background-color: transparent;
    border: 1px solid {BORDER};
    text-align: center;
    padding: 3px 8px;
    font-size: 11px;
    min-height: 22px;
}}
QPushButton#ghostBtn:hover {{
    background-color: {BG_INPUT};
    border-color: {ACCENT};
}}
QPushButton#stopBtn {{
    background-color: #b71c1c;
    color: #ffffff;
    font-weight: bold;
    text-align: center;
    padding: 6px 8px;
    font-size: 11px;
    min-height: 26px;
    border-radius: 6px;
    border: 2px solid #d32f2f;
}}
QPushButton#stopBtn:hover {{ background-color: #d32f2f; }}
QPushButton#stopBtn:disabled {{
    background-color: #4a2020;
    color: #666;
    border-color: #3a1818;
}}
QPushButton#saveBtn {{
    background-color: {BORDER};
    color: {TEXT};
    font-weight: bold;
    text-align: center;
    min-width: 0;
    padding: 4px 10px;
    font-size: 11px;
    min-height: 24px;
}}
QPushButton#saveBtn:hover {{ background-color: #2569ad; }}
QLineEdit, QComboBox {{
    background-color: {BG_LOG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
    min-height: 22px;
    selection-background-color: {BORDER};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
    subcontrol-origin: padding;
    subcontrol-position: top right;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT};
    selection-background-color: {BORDER};
    border: 1px solid {BORDER};
    padding: 2px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    min-height: 20px;
    padding: 2px 6px;
}}
QPlainTextEdit, QTextEdit#logView {{
    background-color: {BG_LOG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-radius: 8px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}}
QProgressBar {{
    background-color: {BG_INPUT};
    border: none;
    border-radius: 4px;
    height: 6px;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DIM}, stop:1 {ACCENT});
    border-radius: 4px;
}}
QCheckBox {{
    spacing: 8px;
    color: {TEXT_DIM};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background: {BG_LOG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT_DIM};
}}
QSlider::groove:horizontal {{
    background: {BG_INPUT};
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 2px solid {ACCENT_DIM};
}}
QSlider::handle:horizontal:hover {{ background: #ffb347; }}
QSlider::sub-page:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QTabWidget::pane {{
    border: 1px solid {BG_INPUT};
    background-color: {BG_DARK};
    border-radius: 0 8px 8px 8px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_MUTED};
    padding: 6px 14px;
    margin-right: 2px;
    font-size: 12px;
    min-height: 22px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid transparent;
    border-bottom: none;
}}
QTabBar::tab:hover {{
    color: {TEXT};
    background-color: {BG_INPUT};
}}
QTabBar::tab:selected {{
    background-color: {BG_DARK};
    color: {ACCENT};
    font-weight: bold;
    border-color: {BG_INPUT};
}}
QTableWidget {{
    background-color: {BG_LOG};
    color: {TEXT_DIM};
    gridline-color: #21262d;
    border: 1px solid {BORDER};
    border-radius: 8px;
    alternate-background-color: #131920;
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QTableWidget::item:selected {{
    background-color: {BORDER};
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_MUTED};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 11px;
}}
QDialog {{
    background-color: {BG_PANEL};
    color: {TEXT};
}}
"""
