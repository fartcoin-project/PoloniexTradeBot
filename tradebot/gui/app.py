import os

import queue

import sys



from PySide6.QtCore import Qt, QTimer

from PySide6.QtGui import QFont, QTextCursor

from PySide6.QtWidgets import (

    QApplication,

    QCheckBox,

    QComboBox,

    QDialog,

    QDialogButtonBox,

    QFrame,

    QGridLayout,

    QHBoxLayout,

    QLabel,

    QLineEdit,

    QMainWindow,

    QMessageBox,

    QPlainTextEdit,

    QProgressBar,

    QPushButton,

    QScrollArea,

    QSizePolicy,

    QSplitter,

    QTabWidget,

    QTextEdit,

    QVBoxLayout,

    QWidget,

)



from gui.data_store import build_wallet_from_cache

from gui.panels import (
    BudgetPanel,
    HistoryPanel,
    MarketsPanel,
    OptionsPanel,
    TradingSettingsPanel,
    WalletPanel,
)

from gui.paths import app_dir

from gui.log_stream import SessionFileLogger

from gui.service import BotService

from gui.theme import ACCENT, DANGER, STYLESHEET, SUCCESS, TEXT_MUTED

from gui.widgets import (
    CollapsibleSection,
    Panel,
    SessionLogSidebar,
    StatCard,
    StatusPill,
    WorkflowStepList,
)

from quote_config import (
    format_markets_label,
    format_quote_value,
    market_section_title,
    markets_from_config,
    min_order_for_markets,
    min_order_for_quote,
    normalize_quote,
    pairs_filename,
    primary_quote_from_config,
    quote_from_config,
)

from gui.window_settings import (
    MIN_HEIGHT,
    MIN_LOG_WIDTH,
    MIN_WIDTH,
    MAX_LOG_WIDTH,
    load_session_log_width,
    load_window_geometry,
    save_session_log_width,
    save_window_geometry,
)

from runtime_paths import PLACEHOLDER_API_KEY


STARTUP_UPDATE_DELAY_SEC = 5





MENU_GROUPS = [

    ("market", [

        ("Update Markets", "update_markets", None),

        ("Total Balance", "total_balance", None),

        ("Refresh Advice", "refresh_advice", None),

    ]),

    ("Orders", [

        ("Build Orders", "collect_orders", None),

        ("Preview Orders", "preview_orders", None),

        ("Place Orders", "place_orders", "dangerBtn"),

        ("Open Orders", "open_orders", None),

    ]),

]

WORKFLOW_COMPLETES = {
    "update_markets": ("update_markets", "refresh_advice"),
    "refresh_advice": ("refresh_advice",),
    "total_balance": ("total_balance",),
    "collect_orders": ("collect_orders",),
    "preview_orders": ("preview_orders",),
    "place_orders": ("place_orders",),
    "open_orders": ("open_orders",),
    "start_bot": ("update_markets", "refresh_advice", "collect_orders", "place_orders"),
}

WORKFLOW_RESETS = {
    "update_markets": ("collect_orders", "preview_orders", "place_orders"),
    "collect_orders": ("preview_orders", "place_orders"),
}


def market_group_title(markets):
    return market_section_title(markets)


class HelpDialog(QDialog):

    def __init__(self, text, parent=None):

        super().__init__(parent)

        self.setWindowTitle("TradeBot Help")

        self.resize(600, 520)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 16, 16, 16)

        viewer = QPlainTextEdit()

        viewer.setReadOnly(True)

        viewer.setPlainText(text)

        viewer.setFont(QFont("Consolas", 10))

        layout.addWidget(viewer)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        buttons.rejected.connect(self.reject)

        buttons.accepted.connect(self.accept)

        layout.addWidget(buttons)





class TradeBotWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("TradeBot — Poloniex")

        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        self._restore_window_geometry()



        self.log_queue = queue.Queue()

        self.service = BotService(self.log_queue)

        self._busy = False

        self._action_buttons = []

        self._workflow_steps = {}

        self._auto_scroll_log = True



        self._build_ui()

        self._load_config_fields()

        self._check_api_config()

        self._load_saved_data()

        self._append_log("Ready — market data loads automatically when API keys are saved.")

        self._append_log(f"Session log: {self.service.log_file_path()}")

        self._append_log(f"Saved data: {self.service.data_dir()}")

        self._refresh_stats_from_config()



        self._poll_timer = QTimer(self)

        self._poll_timer.timeout.connect(self._poll_queue)

        self._poll_timer.start(100)



    def _restore_window_geometry(self):

        geo = load_window_geometry()

        self._pending_maximize = bool(geo.get("maximized"))

        width = max(int(geo.get("width", 1320)), MIN_WIDTH)

        height = max(int(geo.get("height", 900)), MIN_HEIGHT)

        self.resize(width, height)

        x, y = geo.get("x"), geo.get("y")

        if x is not None and y is not None:

            self.move(int(x), int(y))



    def showEvent(self, event):

        super().showEvent(event)

        if getattr(self, "_pending_maximize", False):

            self._pending_maximize = False

            QTimer.singleShot(0, self.showMaximized)

        if not getattr(self, "_panels_loaded", False):

            self._panels_loaded = True

            QTimer.singleShot(0, self._load_market_panels)

        if not getattr(self, "_startup_refresh_scheduled", False):

            self._startup_refresh_scheduled = True

            QTimer.singleShot(0, self._schedule_startup_refresh)

        if not getattr(self, "_session_log_splitter_ready", False):

            self._session_log_splitter_ready = True

            QTimer.singleShot(0, self._apply_session_log_splitter)



    def closeEvent(self, event):

        if self.session_log.is_expanded():

            save_session_log_width(self._session_log_width)

        save_window_geometry(self)

        super().closeEvent(event)



    def _schedule_startup_refresh(self):

        """Wait STARTUP_UPDATE_DELAY_SEC before auto update; show countdown in status bar."""

        if self._busy:

            return

        if not self.service.api_configured():

            self._append_log(

                "Save API keys to auto-fetch market data and advice on startup.",

                tag="status",

            )

            return

        self._startup_countdown = STARTUP_UPDATE_DELAY_SEC

        if not hasattr(self, "_startup_countdown_timer"):

            self._startup_countdown_timer = QTimer(self)

            self._startup_countdown_timer.timeout.connect(self._on_startup_countdown_tick)

        self._update_startup_countdown_ui()

        self._append_log(

            f"Auto market update in {STARTUP_UPDATE_DELAY_SEC} seconds…",

            tag="status",

        )

        self._startup_countdown_timer.start(1000)



    def _on_startup_countdown_tick(self):

        self._startup_countdown -= 1

        if self._startup_countdown <= 0:

            self._cancel_startup_countdown()

            self._auto_refresh_on_startup()

            return

        self._update_startup_countdown_ui()



    def _update_startup_countdown_ui(self):

        remaining = getattr(self, "_startup_countdown", 0)

        message = f"Market update in {remaining}s…"

        self.status_label.setText(message)

        self.status_pill.set_state("ready", message)



    def _cancel_startup_countdown(self):

        timer = getattr(self, "_startup_countdown_timer", None)

        if timer is not None and timer.isActive():

            timer.stop()



    def _auto_refresh_on_startup(self):

        """Fetch markets, balances, and advice on launch (same as CLI startup)."""

        if self._busy:

            return

        if not self.service.api_configured():

            self._append_log(

                "Save API keys to auto-fetch market data and advice on startup.",

                tag="status",

            )

            return

        if not self._save_config(silent=True):

            return

        self._append_log("Startup: fetching market data and computing advice…", tag="status")

        self.status_label.setText("Updating markets…")

        self.progress.setValue(0)

        self.service.run_async("update_markets")



    def _build_ui(self):

        root = QWidget(objectName="root")

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)



        sidebar = QFrame(objectName="sidebar")

        sidebar.setFixedWidth(232)

        side_layout = QVBoxLayout(sidebar)

        side_layout.setContentsMargins(12, 16, 12, 12)

        side_layout.setSpacing(4)



        title = QLabel("TradeBot", objectName="title")

        subtitle = QLabel("Poloniex Rebalancer", objectName="subtitle")

        side_layout.addWidget(title)

        side_layout.addWidget(subtitle)

        side_layout.addSpacing(10)



        self.status_pill = StatusPill()

        side_layout.addWidget(self.status_pill)

        side_layout.addSpacing(12)



        self.run_all_btn = QPushButton("Run All")

        self.run_all_btn.setObjectName("primaryBtn")

        self.run_all_btn.setToolTip("Update markets, build orders, and place trades")

        self.run_all_btn.clicked.connect(lambda: self._run_action("start_bot"))

        side_layout.addWidget(self.run_all_btn)

        self._action_buttons.append(self.run_all_btn)

        run_hint = QLabel("Markets · Build · Trade")

        run_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; padding: 0 4px 6px 4px;")

        side_layout.addWidget(run_hint)

        side_layout.addSpacing(8)



        self.trading_settings = TradingSettingsPanel()

        self.budget_lbl = self.trading_settings.budget_lbl

        self.budget_edit = self.trading_settings.budget_edit

        self.use_advice_btn = self.trading_settings.use_advice_btn

        self.btc_market_check = self.trading_settings.btc_check

        self.usdt_market_check = self.trading_settings.usdt_check

        self.buy_mode_check = self.trading_settings.buy_check

        self.sell_mode_check = self.trading_settings.sell_check

        self.save_btn = self.trading_settings.save_btn

        self.budget_edit.editingFinished.connect(self._sync_budget_to_panel)

        self.use_advice_btn.clicked.connect(self._use_advice_budget)

        self.btc_market_check.toggled.connect(self._on_markets_changed)

        self.usdt_market_check.toggled.connect(self._on_markets_changed)

        self.buy_mode_check.toggled.connect(self._on_modes_changed)

        self.sell_mode_check.toggled.connect(self._on_modes_changed)

        self.save_btn.clicked.connect(self._save_config)

        side_layout.addWidget(self.trading_settings)

        side_layout.addSpacing(8)



        step_num = 1

        initial_markets = markets_from_config(self.service.load_config())

        for group_name, actions in MENU_GROUPS:

            title = market_group_title(initial_markets) if group_name == "market" else group_name

            group = WorkflowStepList(title)

            if group_name == "market":

                self._market_workflow_group = group

            for label, action, style in actions:

                btn = group.add_step(

                    step_num,

                    label,

                    action,

                    lambda checked=False, a=action: self._run_action(a),

                    style=style,

                )

                step_num += 1

                self._action_buttons.append(btn)

            for action_id in group.action_ids():

                self._workflow_steps[action_id] = group

            side_layout.addWidget(group)



        side_layout.addStretch()



        self.stop_btn = QPushButton("EMERGENCY STOP")

        self.stop_btn.setObjectName("stopBtn")

        self.stop_btn.setEnabled(False)

        self.stop_btn.clicked.connect(self._emergency_stop)

        side_layout.addWidget(self.stop_btn)



        self.tabs = QTabWidget()

        bot_tab = QWidget()

        bot_layout = QVBoxLayout(bot_tab)

        bot_layout.setContentsMargins(8, 10, 8, 8)

        bot_layout.setSpacing(14)



        self.budget_panel = BudgetPanel()

        self.budget_panel.budget_changed = self._on_budget_panel_default_changed

        self.budget_panel.on_coins_loaded = self._on_budgets_loaded



        dashboard_host = QWidget()

        dashboard_layout = QVBoxLayout(dashboard_host)

        dashboard_layout.setContentsMargins(0, 0, 0, 0)

        dashboard_layout.setSpacing(10)



        stats_row = QHBoxLayout()

        stats_row.setSpacing(10)

        market_label = format_markets_label(initial_markets)

        self.markets_card = StatCard(f"{market_label} markets", "—")

        self.balance_card = StatCard(f"{market_label} available", "—")

        self.advice_card = StatCard("Advice (80%)", "—")

        self.budget_card = StatCard("Per-coin budget", "—")

        for card in (self.markets_card, self.balance_card, self.advice_card, self.budget_card):

            stats_row.addWidget(card, stretch=1)

        dashboard_layout.addLayout(stats_row)



        self.markets_panel = MarketsPanel()

        self.markets_panel.selection_changed = self._on_markets_selection_changed

        self.markets_section = CollapsibleSection(market_group_title(initial_markets), expanded=False)

        self.markets_section.set_content(self.markets_panel)

        dashboard_layout.addWidget(self.markets_section)



        self.budgets_section = CollapsibleSection("Per-coin budgets", expanded=False)

        self.budgets_section.set_content(self.budget_panel)

        dashboard_layout.addWidget(self.budgets_section)



        dashboard_scroll = QScrollArea()

        dashboard_scroll.setWidgetResizable(True)

        dashboard_scroll.setFrameShape(QFrame.Shape.NoFrame)

        dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        dashboard_scroll.setWidget(dashboard_host)

        self.dashboard_scroll = dashboard_scroll



        progress_footer = QFrame()

        progress_footer.setObjectName("panel")

        footer_layout = QVBoxLayout(progress_footer)

        footer_layout.setContentsMargins(12, 8, 12, 10)

        footer_layout.setSpacing(6)

        self.status_label = QLabel("Ready")

        self.status_label.setStyleSheet("font-weight: 600;")

        footer_layout.addWidget(self.status_label)

        self.progress = QProgressBar()

        self.progress.setRange(0, 100)

        self.progress.setValue(0)

        self.progress.setTextVisible(True)

        self.progress.setFormat("%p%")

        self.progress.setFixedHeight(18)

        footer_layout.addWidget(self.progress)



        bot_layout.addWidget(dashboard_scroll, stretch=1)

        bot_layout.addWidget(progress_footer)



        self.wallet_panel = WalletPanel()

        self.wallet_panel.refresh_requested = self._refresh_wallet



        self.history_panel = HistoryPanel()



        self.options_panel = OptionsPanel()

        self.options_panel.save_requested = lambda: self._save_config(silent=False)

        self.options_panel.help_requested = self._show_help

        self.options_panel.set_paths(

            self.service.log_file_path(),

            self.service.data_dir(),

        )

        self.options_panel.refresh_log(errors_only=True)



        self.tabs.addTab(bot_tab, "Dashboard")

        self.tabs.addTab(self.wallet_panel, "Wallet")

        self.tabs.addTab(self.history_panel, "History")

        self.tabs.addTab(self.options_panel, "Options")

        self.tabs.currentChanged.connect(self._on_tab_changed)



        self.session_log = SessionLogSidebar()

        self.session_log.setMinimumWidth(MIN_LOG_WIDTH)

        self._session_log_width = load_session_log_width()

        self.log_text = self.session_log.log_text

        self.auto_scroll_check = self.session_log.auto_scroll_check

        self.auto_scroll_check.toggled.connect(self._set_auto_scroll)



        tabs_host = QWidget()

        tabs_host_layout = QGridLayout(tabs_host)

        tabs_host_layout.setContentsMargins(0, 0, 0, 0)

        tabs_host_layout.setSpacing(0)

        tabs_host_layout.addWidget(self.tabs, 0, 0)



        self.log_toggle_btn = QPushButton(">_")

        self.log_toggle_btn.setObjectName("logToggleBtn")

        self.log_toggle_btn.setCheckable(True)

        self.log_toggle_btn.setFixedSize(32, 26)

        self.log_toggle_btn.setToolTip("Session log")

        self.log_toggle_btn.clicked.connect(self._toggle_session_log)

        self.tabs.setCornerWidget(self.log_toggle_btn, Qt.Corner.TopRightCorner)



        center = QWidget()

        center_layout = QHBoxLayout(center)

        center_layout.setContentsMargins(20, 18, 20, 18)

        center_layout.setSpacing(0)

        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.center_splitter.setObjectName("centerSplitter")

        self.center_splitter.setChildrenCollapsible(False)

        self.center_splitter.setHandleWidth(6)

        tabs_host.setMinimumWidth(360)

        self.center_splitter.addWidget(tabs_host)

        self.center_splitter.addWidget(self.session_log)

        self.center_splitter.setStretchFactor(0, 1)

        self.center_splitter.setStretchFactor(1, 0)

        self.center_splitter.splitterMoved.connect(self._on_center_splitter_moved)

        center_layout.addWidget(self.center_splitter)



        layout.addWidget(sidebar)

        layout.addWidget(center, stretch=1)



    def _on_tab_changed(self, index):

        if self.tabs.widget(index) is self.options_panel:

            self.options_panel.refresh_log()



    def _clear_log(self):

        self.session_log.clear()



    def _toggle_session_log(self):

        expanded = self.log_toggle_btn.isChecked()

        self.session_log.set_expanded(expanded)

        self._apply_session_log_splitter(expanded)



    def _apply_session_log_splitter(self, expanded=None):

        if not hasattr(self, "center_splitter"):

            return

        if expanded is None:

            expanded = self.session_log.is_expanded()

        if not expanded:

            self.session_log.hide()

            return

        self.session_log.show()

        log_w = max(MIN_LOG_WIDTH, min(MAX_LOG_WIDTH, self._session_log_width))

        total = max(self.center_splitter.width(), sum(self.center_splitter.sizes()), 400)

        self.center_splitter.setSizes([max(total - log_w, 360), log_w])



    def _on_center_splitter_moved(self, _pos, _index):

        if not self.session_log.is_expanded():

            return

        sizes = self.center_splitter.sizes()

        if len(sizes) < 2:

            return

        self._session_log_width = max(

            MIN_LOG_WIDTH,

            min(MAX_LOG_WIDTH, sizes[1]),

        )



    def _set_auto_scroll(self, enabled):

        self._auto_scroll_log = enabled



    def _apply_wallet_to_panels(self, wallet):

        self.wallet_panel.set_wallet(wallet)

        self.budget_panel.set_wallet(wallet)



    def _load_saved_data(self):

        self._apply_wallet_to_panels(self.service.load_persisted_wallet())

        self.history_panel.set_action_history(self.service.get_action_history())

        self.history_panel.set_order_runs(self.service.get_order_runs())

        self._sync_workflow_from_history()



    def _set_workflow_done(self, action_id, done):

        group = self._workflow_steps.get(action_id)

        if group is not None:

            group.set_done(action_id, done)



    def _completed_actions_from_history(self, history):

        latest = {}

        for entry in history:

            action = entry.get("action")

            if action and action not in latest:

                latest[action] = bool(entry.get("ok"))

        completed = set()

        for action, ok in latest.items():

            if ok:

                completed.update(WORKFLOW_COMPLETES.get(action, (action,)))

        return completed



    def _sync_workflow_from_history(self, history=None):

        history = history if history is not None else self.service.get_action_history()

        completed = self._completed_actions_from_history(history)

        for action_id in self._workflow_steps:

            self._set_workflow_done(action_id, action_id in completed)



    def _on_workflow_step_done(self, action, ok):

        if ok:

            for step_id in WORKFLOW_COMPLETES.get(action, (action,)):

                self._set_workflow_done(step_id, True)

            for step_id in WORKFLOW_RESETS.get(action, ()):

                self._set_workflow_done(step_id, False)

        else:

            for step_id in WORKFLOW_COMPLETES.get(action, (action,)):

                self._set_workflow_done(step_id, False)



    def _refresh_wallet(self):

        if self._busy:

            return

        if not self.service.api_configured():

            wallet = build_wallet_from_cache(app_dir())

            self._apply_wallet_to_panels(wallet)

            return

        self._run_action("total_balance")



    def _refresh_history_ui(self, payload):

        if payload.get("actions") is not None:

            self.history_panel.set_action_history(payload["actions"])

        if payload.get("orders") is not None:

            self.history_panel.set_order_runs(payload["orders"])

        if payload.get("actions") is not None:

            self._sync_workflow_from_history(payload["actions"])



    def _update_api_status(self):

        configured = self.service.api_configured()

        self.options_panel.set_api_status(configured)

        if not self._busy:

            if configured:

                self.status_pill.set_state("ready", "Connected")

            else:

                self.status_pill.set_state("warn", "API not configured")



    def _check_api_config(self):

        self._update_api_status()

        if not self.service.api_configured():

            self._append_log("Enter your Poloniex API key and secret in Options, then save.")



    def _load_market_panels(self):

        cfg = self.service.load_config()

        self.markets_panel.load_from_config(cfg)

        self.budget_panel.load_from_config(cfg)

        self._refresh_stats_from_config(cfg)



    def _load_config_fields(self):

        cfg = self.service.load_config()

        markets = markets_from_config(cfg)

        primary = primary_quote_from_config(cfg)

        self.trading_settings.set_selected_markets(markets)

        self.trading_settings.set_trade_mode(cfg.get("trade_mode", "both"))

        self.trading_settings.set_schedule(cfg.get("schedule", {}))

        from gui.schedule import get_windows_task_state

        self.trading_settings.update_schedule_status(

            cfg.get("schedule", {}),

            task_state=get_windows_task_state(),

        )

        self._apply_markets_ui(markets)

        self.budget_edit.setText(str(cfg.get("budget", min_order_for_quote(primary))))

        verbose = bool(cfg.get("verbose_log", True))

        self.options_panel.verbose_check.setChecked(verbose)

        self.service.set_verbose_log(verbose)

        api_key, _api_secret = self.service.load_api_credentials()

        self.options_panel.load_api_fields(

            api_key if api_key != PLACEHOLDER_API_KEY else "",

        )

        self._update_api_status()



    def _apply_markets_ui(self, markets):

        if not markets:

            markets = ["BTC"]

        primary = markets[0]

        market_label = format_markets_label(markets)

        if len(markets) == 1:

            self.budget_lbl.setText(f"Budget ({primary})")

        else:

            self.budget_lbl.setText(f"Budget ({market_label})")

        title = market_group_title(markets)

        if hasattr(self, "_market_workflow_group"):

            self._market_workflow_group.set_title(title)

        if hasattr(self, "markets_section"):

            self.markets_section.set_title(title)

        if hasattr(self, "markets_card"):

            self.markets_card.set_label(f"{market_label} markets")

        if hasattr(self, "balance_card"):

            self.balance_card.set_label(f"{market_label} available")

        min_ord = min_order_for_markets(markets)

        try:

            current = float(self.budget_edit.text())

        except ValueError:

            current = min_ord

        if current < min_ord:

            self.budget_edit.setText(str(min_ord))



    def _on_markets_changed(self, _checked=False):

        markets = self.trading_settings.get_selected_markets()

        if not markets:

            self._append_log("Select at least one market (BTC or USDT).", tag="error")

            sender = self.sender()

            if sender is self.btc_market_check:

                self.btc_market_check.blockSignals(True)

                self.btc_market_check.setChecked(True)

                self.btc_market_check.blockSignals(False)

            elif sender is self.usdt_market_check:

                self.usdt_market_check.blockSignals(True)

                self.usdt_market_check.setChecked(True)

                self.usdt_market_check.blockSignals(False)

            markets = self.trading_settings.get_selected_markets()

        self._apply_markets_ui(markets)

        cfg = self.service.load_config()

        cfg["markets"] = markets

        cfg["quote_currency"] = markets[0]

        self.markets_panel.load_from_config(cfg)



    def _on_modes_changed(self, _checked=False):

        if not (
            self.buy_mode_check.isChecked() or self.sell_mode_check.isChecked()
        ):

            self._append_log("Select at least one mode (Buy or Sell).", tag="error")

            sender = self.sender()

            if sender is self.buy_mode_check:

                self.buy_mode_check.blockSignals(True)

                self.buy_mode_check.setChecked(True)

                self.buy_mode_check.blockSignals(False)

            elif sender is self.sell_mode_check:

                self.sell_mode_check.blockSignals(True)

                self.sell_mode_check.setChecked(True)

                self.sell_mode_check.blockSignals(False)



    def _on_budgets_loaded(self):

        """Expand budgets section after market update populates coin sliders."""

        if getattr(self, "_budgets_section_opened", False):

            return

        self._budgets_section_opened = True

        self.tabs.setCurrentIndex(0)

        QTimer.singleShot(150, self._expand_budgets_section)



    def _expand_budgets_section(self):

        if hasattr(self, "budgets_section"):

            self.budgets_section.set_expanded(True)

            self.budget_panel._schedule_layout_sync()

            if hasattr(self, "dashboard_scroll"):

                QTimer.singleShot(50, self._scroll_to_budgets)



    def _scroll_to_budgets(self):

        if hasattr(self, "dashboard_scroll") and hasattr(self, "budgets_section"):

            self.dashboard_scroll.ensureWidgetVisible(self.budgets_section, 0, 24)



    def _on_markets_selection_changed(self):

        stats = self.markets_panel.get_stats()

        if stats["total"]:

            self.markets_card.set_value(f"{stats['active']} / {stats['total']} active")

        else:

            self.markets_card.set_value("—")



    def _refresh_stats_from_config(self, cfg=None):

        if cfg is None:

            cfg = self.service.load_config()

        selected = markets_from_config(cfg)

        primary = primary_quote_from_config(cfg)

        pair_count = cfg.get("markets_total")

        if not isinstance(pair_count, int):

            pair_count = 0

            for q in selected:

                pairs_file = os.path.join(app_dir(), "json", pairs_filename(q))

                if os.path.exists(pairs_file):

                    with open(pairs_file, encoding="utf-8") as handle:

                        pair_count += sum(1 for line in handle if line.strip())

        balance = float(cfg.get("balance", 0) or 0)

        advice = float(cfg.get("advice", 0) or 0)

        budget = float(cfg.get("budget", 0) or 0)

        market_balances = cfg.get("market_balances") or {}



        if hasattr(self, "markets_panel") and self.markets_panel.get_stats()["total"]:

            stats = self.markets_panel.get_stats()

            self.markets_card.set_value(f"{stats['active']} / {stats['total']} active")

        elif pair_count:

            excluded = len(cfg.get("exclude", []))

            self.markets_card.set_value(f"{max(0, pair_count - excluded)} / {pair_count} active")

        else:

            self.markets_card.set_value("—")

        if len(selected) > 1 and market_balances:

            parts = []

            for q in selected:

                try:

                    parts.append(format_quote_value(q, float(market_balances.get(q, 0))))

                except (TypeError, ValueError):

                    pass

            self.balance_card.set_value(" · ".join(parts) if parts else format_quote_value(primary, balance))

        else:

            self.balance_card.set_value(format_quote_value(primary, balance))

        advice_color = SUCCESS if budget <= advice else DANGER

        self.advice_card.set_value(
            f'<span style="color:{advice_color}">{format_quote_value(primary, advice)}</span>'
        )

        self.budget_card.set_value(format_quote_value(primary, budget))

        self._last_advice = advice

        self._last_quote = primary

        self._last_markets = selected



    def _sync_budget_to_panel(self):

        try:

            value = float(self.budget_edit.text())

        except ValueError:

            return

        markets = self.trading_settings.get_selected_markets()

        if not markets:

            return

        if value >= min_order_for_markets(markets):

            self.budget_panel.set_default_budget(value)



    def _on_budget_panel_default_changed(self, text):

        self.budget_edit.setText(text)



    def _use_advice_budget(self):

        advice = getattr(self, "_last_advice", 0)

        quote = getattr(self, "_last_quote", primary_quote_from_config(self.service.load_config()))

        markets = getattr(self, "_last_markets", markets_from_config(self.service.load_config()))

        min_ord = min_order_for_markets(markets)

        if advice >= min_ord:

            prec = 2 if quote in ("USDT", "USDC") else 6

            self.budget_edit.setText(f"{advice:.{prec}f}")

            self.budget_panel.apply_advice(advice)

            label = format_markets_label(markets) if len(markets) > 1 else quote

            self.status_label.setText(f"Budget set to advice ({label}): {format_quote_value(quote, advice)}")

        else:

            QMessageBox.information(

                self,

                "No advice yet",

                "Run Update Markets or Total Balance first to compute advice.",

            )



    def _save_config(self, silent=False):

        try:

            budget = float(self.budget_edit.text())

        except ValueError:

            if not silent:

                QMessageBox.critical(self, "Invalid budget", "Budget must be a number.")

            return False

        markets = self.trading_settings.get_selected_markets()

        if not markets:

            if not silent:

                QMessageBox.critical(self, "Invalid config", "Select at least one market (BTC or USDT).")

            return False

        self.budget_panel.set_default_budget(budget, update_sliders=False)

        schedule = self.trading_settings.get_schedule()

        if schedule["enabled"] and self.trading_settings.schedule_budget_check.isChecked():

            if schedule["budget"] is None:

                if not silent:

                    QMessageBox.critical(

                        self,

                        "Invalid schedule",

                        "Fixed schedule budget must be a number.",

                    )

                return False

            min_ord = min_order_for_markets(markets)

            if schedule["budget"] < min_ord:

                if not silent:

                    QMessageBox.critical(

                        self,

                        "Invalid schedule",

                        f"Schedule budget must be at least {min_ord}.",

                    )

                return False

        try:

            schedule_result = self.service.save_config(

                budget=budget,

                exclude=self.markets_panel.get_excluded(),

                sell_mode=self.trading_settings.get_trade_mode(),

                verbose_log=self.options_panel.verbose_check.isChecked(),

                api_key=self.options_panel.api_key_edit.text(),

                api_secret=self.options_panel.api_secret_edit.text(),

                coin_budgets=self.budget_panel.get_coin_budgets(),

                coin_budget_custom=self.budget_panel.get_custom_coins(),

                markets=markets,

                schedule=schedule,

            )

        except ValueError as exc:

            if not silent:

                QMessageBox.critical(self, "Invalid config", str(exc))

            return False

        self.options_panel.api_secret_edit.clear()

        self._update_api_status()

        self.options_panel.refresh_log()

        self._refresh_stats_from_config()

        self.trading_settings.update_schedule_status(

            schedule,

            task_state=schedule_result.task_state,

        )

        if not silent:

            self._append_log("Settings saved.", tag="status")

            self._append_log(schedule_result.message, tag="status")

            self.status_label.setText(schedule_result.message if schedule["enabled"] else "Settings saved")

            SessionFileLogger.get().write_line("config", "Settings saved")

            if not schedule_result.ok:

                QMessageBox.warning(self, "Schedule", schedule_result.message)

        return True



    def _reveal_log(self):

        if hasattr(self, "session_log") and not self.session_log.is_expanded():

            self.session_log.set_expanded(True)

            self.log_toggle_btn.setChecked(True)

            self._apply_session_log_splitter(True)



    def _append_log(self, line, tag=None):

        color = "#c9d1d9"

        prefix = ""

        if tag == "error":

            color = DANGER

            prefix = "[ERROR] "

        elif tag == "status":

            color = SUCCESS

            prefix = "[*] "

        elif " Buy =" in line or " Buy=" in line:

            color = DANGER

        elif "Sell =" in line or "Sell=" in line:

            color = SUCCESS

        elif "Exclude" in line or "Order too Small" in line:

            color = "#4fc3f7"

        elif line.strip().startswith("  Updating:") or line.strip().startswith("  Build orders:"):

            color = TEXT_MUTED

        elif "saved" in line.lower():

            color = ACCENT

        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        self.log_text.append(f'<span style="color:{color}">{prefix}{safe}</span>')

        self._reveal_log()

        if self._auto_scroll_log:

            cursor = self.log_text.textCursor()

            cursor.movePosition(QTextCursor.MoveOperation.End)

            self.log_text.setTextCursor(cursor)



    def _set_busy(self, busy):

        self._busy = busy

        enabled = not busy

        for btn in self._action_buttons:

            btn.setEnabled(enabled)

        self.save_btn.setEnabled(enabled)

        self.options_panel.save_api_btn.setEnabled(enabled)

        self.use_advice_btn.setEnabled(enabled)

        self.stop_btn.setEnabled(busy)

        if busy:

            self.status_pill.set_state("busy", "Running…")

        elif self.service.api_configured():

            self.status_pill.set_state("ready", "Connected")

        else:

            self.status_pill.set_state("warn", "API not configured")



    def _emergency_stop(self):

        if not self._busy:

            return

        if self.service.request_cancel():

            self._append_log("Emergency stop requested — stopping between steps…", tag="error")

            self.status_label.setText("Emergency stop…")

            self.status_pill.set_state("error", "Stopping…")

            self.stop_btn.setEnabled(False)



    def _confirm_place(self, action):

        if action in ("place_orders", "start_bot"):

            reply = QMessageBox.question(

                self,

                "Confirm live trading",

                "TradeBot will place real BUY and SELL orders on Poloniex.\n\n"

                "Are you sure you want to continue?",

                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,

            )

            return reply == QMessageBox.StandardButton.Yes

        return True



    def _show_help(self):

        try:

            text = self.service.help_text()

        except Exception as exc:

            text = f"Could not load help: {exc}"

        HelpDialog(text, self).exec()



    def _run_action(self, action):

        self._cancel_startup_countdown()

        if self._busy:

            return

        if not self._save_config(silent=True):

            return

        if not self.service.api_configured():

            QMessageBox.warning(

                self,

                "API keys required",

                "Save your Poloniex API key and secret in the Options tab before running bot actions.",

            )

            return

        if not self._confirm_place(action):

            return

        self.progress.setValue(0)

        self.service.run_async(action)



    def _poll_queue(self):

        try:

            while True:

                tag, payload = self.log_queue.get_nowait()

                if tag == "log":

                    self._append_log(payload)

                elif tag == "error":

                    self._append_log(payload, tag="error")

                    if hasattr(self, "options_panel"):

                        self.options_panel.refresh_log(errors_only=True)

                elif tag == "status":

                    self.status_label.setText(payload)

                    self._append_log(payload, tag="status")

                elif tag == "progress":

                    self.progress.setValue(int(round(float(payload))))

                elif tag == "busy":

                    self._set_busy(payload)

                elif tag == "config":

                    self.markets_panel.load_from_config(payload)

                    self.budget_panel.load_from_config(payload)

                    self._refresh_stats_from_config(payload)

                elif tag == "wallet":

                    self._apply_wallet_to_panels(payload)

                elif tag == "history":

                    self._refresh_history_ui(payload)

                elif tag == "action_done":

                    self._on_workflow_step_done(payload["action"], payload["ok"])

                elif tag == "done":

                    if self._busy:

                        self.progress.setValue(100)

                    if hasattr(self, "options_panel"):

                        self.options_panel.refresh_log()

        except queue.Empty:

            pass





def main():

    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    app.setStyleSheet(STYLESHEET)

    window = TradeBotWindow()

    window.show()

    sys.exit(app.exec())





if __name__ == "__main__":

    main()

