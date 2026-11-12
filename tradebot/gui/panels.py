from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from gui.schedule_config import normalize_schedule, schedule_summary

import os

from budget_helpers import (
    budget_multiplier_count,
    format_budget_multiplier,
    load_pair_coins,
    multiplier_step_to_value,
    normalize_coin_budgets,
    value_to_multiplier_step,
)
from gui.data_store import holdings_map_for_quote
from gui.log_stream import read_session_log
from gui.paths import app_dir
from quote_config import (
    active_pairs_all_markets,
    format_markets_label,
    format_quote_value,
    is_pair_excluded,
    load_pair_coins,
    market_id,
    markets_from_config,
    min_order_for_quote,
    primary_quote_from_config,
    quote_from_config,
)
from gui.theme import ACCENT, BUY, DANGER, SELL, SUCCESS, TEXT_MUTED
from gui.widgets import (
    CollapsibleSection,
    EmptyState,
    Panel,
    PanelHeading,
    ScrollNeutralSlider,
    SectionLabel,
)


def _pair_label(coin_key):
    if "_" in coin_key:
        base, quote = coin_key.rsplit("_", 1)
        return f"{base}/{quote}"
    return coin_key


def _base_coin(coin_key):
    if "_" in coin_key:
        return coin_key.rsplit("_", 1)[0]
    return coin_key


def _fmt_btc(value):
    if value is None:
        return "—"
    return f"₿ {value:.8f}"


def _fmt_usd(value):
    if value is None:
        return "—"
    return f"$ {value:,.2f}"


def _fmt_amount(amount):
    if amount is None:
        return "—"
    amount = float(amount)
    if amount >= 1000:
        return f"{amount:,.2f}"
    if amount >= 1:
        return f"{amount:.4f}"
    return f"{amount:.8f}".rstrip("0").rstrip(".") or "0"


def _fmt_pct(value, total):
    if value is None or not total:
        return "—"
    return f"{100.0 * float(value) / float(total):.1f}%"


class WalletPanel(QWidget):
    refresh_requested = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wallet = None
        self._currency = "BTC"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(12)

        top = QHBoxLayout()
        summary = Panel()
        summary.layout.setContentsMargins(16, 12, 16, 12)
        sum_inner = QVBoxLayout()
        sum_inner.setSpacing(6)
        self.total_label = QLabel("—")
        self.total_label.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {ACCENT};"
        )
        self.subtotal_label = QLabel("")
        self.subtotal_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.updated_label = QLabel("")
        self.updated_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        sum_inner.addWidget(QLabel("Portfolio total"))
        sum_inner.addWidget(self.total_label)
        sum_inner.addWidget(self.subtotal_label)
        sum_inner.addWidget(self.updated_label)
        summary.layout.addLayout(sum_inner)
        top.addWidget(summary, stretch=1)

        controls = Panel()
        controls.layout.setContentsMargins(16, 12, 16, 12)
        ctrl_inner = QVBoxLayout()
        ctrl_inner.setSpacing(8)
        ctrl_inner.addWidget(PanelHeading("Display currency"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["BTC", "USD"])
        self.currency_combo.setFixedWidth(120)
        self.currency_combo.currentTextChanged.connect(self._on_currency_changed)
        ctrl_inner.addWidget(self.currency_combo)
        self.refresh_btn = QPushButton("Refresh wallet")
        self.refresh_btn.setObjectName("ghostBtn")
        self.refresh_btn.clicked.connect(self._on_refresh)
        ctrl_inner.addWidget(self.refresh_btn)
        controls.layout.addLayout(ctrl_inner)
        top.addWidget(controls)
        layout.addLayout(top)

        self.stack = QStackedWidget()
        self.empty_state = EmptyState(
            "No wallet data yet",
            "Run Update Markets or Total Balance to load holdings.",
        )
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Coin", "Amount", "Value", "Allocation"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.stack.addWidget(self.empty_state)
        self.stack.addWidget(self.table)
        layout.addWidget(self.stack, stretch=1)

    def _on_refresh(self):
        if callable(self.refresh_requested):
            self.refresh_requested()

    def _on_currency_changed(self, currency):
        self._currency = currency
        self._render_wallet()

    def _value_header(self):
        return "USD value" if self._currency == "USD" else "BTC value"

    def _fmt_value(self, item):
        if self._currency == "USD":
            return _fmt_usd(item.get("usd_value"))
        return _fmt_btc(item.get("btc_value"))

    def _portfolio_total(self, wallet):
        if self._currency == "USD":
            total = wallet.get("total_usd")
            if total is not None:
                return _fmt_usd(float(total)), _fmt_btc(float(wallet.get("total_btc") or 0))
            btc = float(wallet.get("total_btc") or 0)
            rate = wallet.get("btc_usd")
            if rate:
                return _fmt_usd(btc * float(rate)), _fmt_btc(btc)
            return "—", _fmt_btc(btc) if btc else ""
        total_btc = float(wallet.get("total_btc") or 0)
        sub = ""
        rate = wallet.get("btc_usd")
        if rate and total_btc:
            sub = _fmt_usd(total_btc * float(rate))
        return _fmt_btc(total_btc), sub

    def _render_wallet(self):
        wallet = self._wallet
        if not wallet:
            return

        primary, secondary = self._portfolio_total(wallet)
        self.total_label.setText(primary)
        self.subtotal_label.setText(secondary if secondary else "")
        self.subtotal_label.setVisible(bool(secondary))

        holdings = wallet.get("holdings") or []
        if not holdings:
            self.stack.setCurrentWidget(self.empty_state)
            return

        self.stack.setCurrentWidget(self.table)
        self.table.setHorizontalHeaderLabels(["Coin", "Amount", self._value_header(), "Allocation"])

        total_btc = float(wallet.get("total_btc") or 0)
        total_usd = wallet.get("total_usd")
        if total_usd is None and total_btc > 0 and wallet.get("btc_usd"):
            total_usd = total_btc * float(wallet["btc_usd"])

        self.table.setRowCount(len(holdings))
        for row, item in enumerate(holdings):
            coin_name = str(item.get("coin", ""))
            coin = QTableWidgetItem(coin_name)
            coin.setFont(coin.font())
            f = coin.font()
            f.setBold(True)
            coin.setFont(f)

            amount = QTableWidgetItem(f"{float(item.get('amount') or 0):.8f}")
            value = QTableWidgetItem(self._fmt_value(item))

            if self._currency == "USD":
                val = item.get("usd_value")
                total = float(total_usd) if total_usd else 0
            else:
                val = item.get("btc_value")
                total = total_btc

            pct_text = _fmt_pct(val, total)
            pct = QTableWidgetItem(pct_text)
            if val is not None and total > 0:
                pct_val = 100.0 * float(val) / total
                if pct_val >= 20:
                    pct.setForeground(QColor(BUY))

            if val is not None and total > 0:
                tip = f"{pct_text} of portfolio"
                if self._currency == "BTC" and item.get("usd_value") is not None:
                    tip += f"\n{_fmt_usd(item['usd_value'])}"
                elif self._currency == "USD" and item.get("btc_value") is not None:
                    tip += f"\n{_fmt_btc(item['btc_value'])}"
                value.setToolTip(tip)

            for col, cell in enumerate((coin, amount, value, pct)):
                align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                if col in (2, 3):
                    align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
                cell.setTextAlignment(align)
                self.table.setItem(row, col, cell)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, max(self.table.columnWidth(1), 120))

    def set_wallet(self, wallet):
        self._wallet = wallet
        if not wallet:
            self.total_label.setText("—")
            self.subtotal_label.clear()
            self.updated_label.setText("Run Update Markets to load data")
            self.stack.setCurrentWidget(self.empty_state)
            return

        updated = wallet.get("time", "")
        self.updated_label.setText(f"Last updated {updated}" if updated else "")
        holdings = wallet.get("holdings") or []
        if not holdings:
            self.stack.setCurrentWidget(self.empty_state)
            return
        self._render_wallet()


class BudgetPanel(QWidget):
    """Per-coin budget sliders; default follows global budget unless overridden."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom = set()
        self._rows = {}
        self._quote = "BTC"
        self._min_order = min_order_for_quote("BTC")
        self._default = self._min_order
        self._global_base = self._min_order
        self._block = False
        self._filter = ""
        self._wallet = None
        self._holdings = {}
        self.on_coins_loaded = None
        self._refreshing_geometry = False
        self._layout_timer = QTimer(self)
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._deferred_layout_sync)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter coins…")
        self.search_edit.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.search_edit, stretch=1)
        self.reset_btn = QPushButton("Reset overrides")
        self.reset_btn.setObjectName("ghostBtn")
        self.reset_btn.clicked.connect(self.reset_all_custom)
        toolbar.addWidget(self.reset_btn)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        toolbar.addWidget(self.count_label)
        layout.addLayout(toolbar)

        self.coins_container = QWidget()
        self.coins_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        coins_container_layout = QVBoxLayout(self.coins_container)
        coins_container_layout.setContentsMargins(0, 0, 0, 0)
        coins_container_layout.setSpacing(0)
        self.empty_state = EmptyState(
            "No budgets yet",
            "Run Update Markets to load per-coin budget sliders.",
        )
        self.coins_host = QWidget()
        self.coins_host.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.coins_layout = QGridLayout(self.coins_host)
        self.coins_layout.setSpacing(6)
        self.coins_layout.setContentsMargins(0, 0, 4, 0)
        self.coins_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._column_count = 3
        coins_container_layout.addWidget(self.empty_state)
        coins_container_layout.addWidget(
            self.coins_host, 0, Qt.AlignmentFlag.AlignTop
        )
        self.coins_host.setVisible(False)
        layout.addWidget(self.coins_container)

        self.empty_filter = EmptyState("No coins match your filter")
        self.empty_filter.setVisible(False)
        layout.addWidget(self.empty_filter)

        default_frame = Panel("Global budget")
        default_row = QHBoxLayout()
        self.default_slider = ScrollNeutralSlider(Qt.Orientation.Horizontal)
        self._configure_multiplier_slider(self.default_slider)
        self.default_slider.valueChanged.connect(self._on_default_slider)
        default_row.addWidget(self.default_slider, stretch=1)
        self.default_label = QLabel(format_budget_multiplier(2))
        self.default_label.setFixedWidth(130)
        self.default_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        default_row.addWidget(self.default_label)
        default_frame.layout.addLayout(default_row)
        hint = QLabel(
            "Steps ×0.3 … ×10 relative to advice. "
            "Applies to all coins without a custom override above."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        default_frame.layout.addWidget(hint)
        self.wallet_summary_label = QLabel("")
        self.wallet_summary_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        default_frame.layout.addWidget(self.wallet_summary_label)
        layout.addWidget(default_frame)

        self.budget_changed = None

    _MAX_COIN_COLUMNS = 3
    _MIN_COIN_COL_WIDTH = 200
    _COIN_CARD_MIN_HEIGHT = 72

    def showEvent(self, event):
        super().showEvent(event)
        self._schedule_layout_sync()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_layout_sync()

    def _schedule_layout_sync(self):
        self._layout_timer.start(0)

    def _deferred_layout_sync(self):
        self._sync_column_count()
        self._refresh_coins_layout_geometry()

    def _grid_available_width(self):
        for widget in (self.coins_container, self):
            width = widget.width()
            if width > 0:
                return width
        width = self.coins_host.width()
        if width > 0:
            return width
        return 0

    def _sync_column_count(self):
        width = self._grid_available_width()
        if width <= 0:
            return
        cols = max(1, min(self._MAX_COIN_COLUMNS, width // self._MIN_COIN_COL_WIDTH))
        if cols != self._column_count:
            self._column_count = cols
            if self._rows:
                self._relayout_coin_grid()

    def _relayout_coin_grid(self):
        while self.coins_layout.count():
            self.coins_layout.takeAt(0)
        visible = [
            coin
            for coin in sorted(self._rows.keys())
            if not self._filter or self._filter in coin.upper()
        ]
        cols = max(1, self._column_count)
        for col in range(self._MAX_COIN_COLUMNS):
            self.coins_layout.setColumnStretch(col, 1 if col < cols else 0)
        for index, coin in enumerate(visible):
            widget = self._rows[coin]["widget"]
            widget.setVisible(True)
            self.coins_layout.addWidget(
                widget,
                index // cols,
                index % cols,
                Qt.AlignmentFlag.AlignTop,
            )
        for coin, row in self._rows.items():
            if coin not in visible:
                row["widget"].setVisible(False)
        self._refresh_coins_layout_geometry()

    def _refresh_coins_layout_geometry(self):
        if self._refreshing_geometry:
            return
        self._refreshing_geometry = True
        try:
            if not self.coins_host.isVisible():
                self.coins_host.setFixedHeight(0)
                return
            visible_count = len(
                [
                    coin
                    for coin in self._rows
                    if not self._filter or self._filter in coin.upper()
                ]
            )
            cols = max(1, self._column_count)
            rows = (visible_count + cols - 1) // cols if visible_count else 0
            for row in range(64):
                self.coins_layout.setRowStretch(row, 0)
                self.coins_layout.setRowMinimumHeight(row, 0)
            for row in range(rows):
                self.coins_layout.setRowMinimumHeight(row, self._COIN_CARD_MIN_HEIGHT)
            spacing = self.coins_layout.spacing()
            margins = self.coins_layout.contentsMargins()
            height = (
                rows * self._COIN_CARD_MIN_HEIGHT
                + max(0, rows - 1) * spacing
                + margins.top()
                + margins.bottom()
            )
            self.coins_host.setFixedHeight(max(height, 0))
            self.coins_container.updateGeometry()
            self.updateGeometry()
        finally:
            self._refreshing_geometry = False

    def set_wallet(self, wallet):
        self._wallet = wallet
        self._holdings = holdings_map_for_quote(wallet, self._quote)
        self._refresh_wallet_summary()
        for coin in self._rows:
            self._update_row_wallet(coin)

    def _refresh_wallet_summary(self):
        if not self._wallet:
            self.wallet_summary_label.setText("Wallet: run Update Markets to load balances")
            return
        free = self._holdings.get(self._quote, {}).get("amount")
        if free is not None:
            self.wallet_summary_label.setText(
                f"Wallet · free {self._quote}: {format_quote_value(self._quote, free)}"
            )
        else:
            self.wallet_summary_label.setText("Wallet · holdings loaded")

    def _update_row_wallet(self, coin):
        row = self._rows.get(coin)
        if not row:
            return
        base = _base_coin(coin)
        hold = self._holdings.get(base)
        budget_val = self._step_to_value(row["slider"].value(), self._coin_base_value())
        if not hold:
            row["amount_label"].setText("0")
            row["hold_label"].setText("—")
            row["hold_label"].setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
            row["widget"].setToolTip("")
            return
        amount = hold.get("amount") or 0
        quote_val = hold.get("quote_value")
        row["amount_label"].setText(_fmt_amount(amount))
        if quote_val is not None:
            row["hold_label"].setText(format_quote_value(self._quote, quote_val))
        else:
            row["hold_label"].setText("—")
        if quote_val is not None and budget_val > 0:
            if quote_val > budget_val * 1.05:
                color = SELL
                hint = "above target — likely sell"
            elif quote_val < budget_val * 0.95:
                color = BUY
                hint = "below target — likely buy"
            else:
                color = TEXT_MUTED
                hint = "near target"
            row["hold_label"].setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 600;")
            row["widget"].setToolTip(
                f"{coin}: { _fmt_amount(amount) } ≈ {format_quote_value(self._quote, quote_val)} ({hint})"
            )
        else:
            row["hold_label"].setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
            row["widget"].setToolTip(f"{coin}: {_fmt_amount(amount)}")

    def has_coins(self):
        return bool(self._rows)

    def _update_coins_view(self):
        had_coins = self.coins_host.isVisible()
        has_coins = self.has_coins()
        self.empty_state.setVisible(not has_coins)
        self.coins_host.setVisible(has_coins)
        if has_coins:
            self._refresh_coins_layout_geometry()
        else:
            self.coins_host.setFixedHeight(0)
        if has_coins and not had_coins and callable(self.on_coins_loaded):
            self.on_coins_loaded()

    def _on_filter_changed(self, text):
        self._filter = text.strip().upper()
        visible = sum(
            1
            for coin in self._rows
            if not self._filter or self._filter in coin.upper()
        )
        self.empty_filter.setVisible(bool(self._filter) and visible == 0 and bool(self._rows))
        self._relayout_coin_grid()

    def _configure_multiplier_slider(self, slider):
        slider.setMinimum(0)
        slider.setMaximum(max(0, budget_multiplier_count() - 1))
        slider.setSingleStep(1)
        slider.setPageStep(1)

    def _configure_all_sliders(self):
        self._configure_multiplier_slider(self.default_slider)
        for row in self._rows.values():
            self._configure_multiplier_slider(row["slider"])

    def _fmt_step_label(self, step, value):
        return f"{format_budget_multiplier(step)} · {format_quote_value(self._quote, value)}"

    def _global_base_value(self):
        return max(self._global_base, self._min_order)

    def _coin_base_value(self):
        return max(self._default, self._min_order)

    def _step_to_value(self, step, base):
        return multiplier_step_to_value(step, base, self._min_order)

    def _value_to_step(self, value, base):
        return value_to_multiplier_step(value, base, self._min_order)

    def _set_quote(self, quote):
        self._quote = quote
        self._min_order = min_order_for_quote(quote)
        self.default_slider.setMinimum(0)
        if self._wallet:
            self._holdings = holdings_map_for_quote(self._wallet, self._quote)
            self._refresh_wallet_summary()
            for coin in self._rows:
                self._update_row_wallet(coin)

    def _update_count_label(self):
        n = len(self._custom)
        total = len(self._rows)
        if n:
            self.count_label.setText(f"{n} of {total} customized")
        else:
            self.count_label.setText(f"{total} coins · all use global")

    def load_from_config(self, config, coins=None):
        self._set_quote(primary_quote_from_config(config))
        self._custom = set(config.get("coin_budget_custom") or [])
        if "budget" in config and config.get("budget") is not None:
            self._default = max(float(config["budget"]), 0.0)
        else:
            self._default = self._min_order
        advice = float(config.get("advice") or 0)
        if advice >= self._min_order:
            self._global_base = advice
        else:
            self._global_base = self._default
        if coins is None:
            pairs = active_pairs_all_markets(None, config)
            coin_keys = [market_id(coin, quote) for coin, quote in pairs]
        else:
            coin_keys = []
            quote = primary_quote_from_config(config)
            for item in coins:
                if isinstance(item, (tuple, list)) and len(item) >= 2:
                    coin_keys.append(market_id(item[0], item[1]))
                else:
                    coin_keys.append(market_id(str(item), quote))
        budgets = normalize_coin_budgets(config, coin_keys)

        existing = set(self._rows.keys())
        target = set(budgets.keys())
        for coin in existing - target:
            row = self._rows.pop(coin)
            row["widget"].deleteLater()
        for coin in sorted(budgets.keys()):
            if coin not in self._rows:
                self._add_coin_row(coin)
            self._set_coin_value(coin, budgets[coin], mark_custom=False)
            self._update_row_wallet(coin)

        self._configure_all_sliders()
        self._block = True
        global_step = self._value_to_step(self._default, self._global_base_value())
        self._default = self._step_to_value(global_step, self._global_base_value())
        self.default_slider.setValue(global_step)
        self.default_label.setText(self._fmt_step_label(global_step, self._default))
        self._block = False
        self._update_count_label()
        self._on_filter_changed(self.search_edit.text())
        self._update_coins_view()
        self._relayout_coin_grid()
        self._schedule_layout_sync()

    def _add_coin_row(self, coin):
        widget = QFrame()
        widget.setObjectName("panel")
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        widget.setFixedHeight(self._COIN_CARD_MIN_HEIGHT)
        card = QVBoxLayout(widget)
        card.setContentsMargins(8, 6, 8, 6)
        card.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)
        name = QLabel(_pair_label(coin))
        name.setStyleSheet("font-weight: bold; font-size: 12px;")
        top.addWidget(name)

        custom_mark = QLabel("custom")
        custom_mark.setToolTip("This coin uses a custom budget")
        custom_mark.setStyleSheet(f"color: {ACCENT}; font-size: 9px; font-weight: 600;")
        custom_mark.setVisible(False)
        top.addWidget(custom_mark)
        top.addStretch()

        value_label = QLabel(format_budget_multiplier(2))
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value_label.setStyleSheet(
            "color: #c9d1d9; font-family: Consolas, monospace; font-size: 10px;"
        )
        top.addWidget(value_label)
        card.addLayout(top)

        hold_row = QHBoxLayout()
        hold_row.setSpacing(4)
        amount_label = QLabel("—")
        amount_label.setStyleSheet(
            "color: #c9d1d9; font-family: Consolas, monospace; font-size: 10px;"
        )
        hold_label = QLabel("—")
        hold_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        hold_row.addWidget(amount_label)
        hold_row.addWidget(hold_label)
        hold_row.addStretch()
        card.addLayout(hold_row)

        slider = ScrollNeutralSlider(Qt.Orientation.Horizontal)
        slider.setMinimumHeight(20)
        slider.setMaximumWidth(16777215)
        self._configure_multiplier_slider(slider)
        slider.valueChanged.connect(lambda value, c=coin: self._on_coin_slider(c, value))
        card.addWidget(slider)

        self._rows[coin] = {
            "widget": widget,
            "slider": slider,
            "label": value_label,
            "amount_label": amount_label,
            "hold_label": hold_label,
            "custom": custom_mark,
        }
        self._update_row_wallet(coin)

    def _set_coin_value(self, coin, value, mark_custom=None):
        row = self._rows.get(coin)
        if not row:
            return
        self._block = True
        value = max(float(value), 0.0)
        if value == 0:
            step = 0
        else:
            base = self._coin_base_value()
            step = self._value_to_step(value, base)
            value = self._step_to_value(step, base)
        row["slider"].setValue(step)
        if value == 0:
            row["label"].setText(format_quote_value(self._quote, 0.0))
            row["label"].setToolTip("0 — sell down holdings")
        else:
            row["label"].setText(self._fmt_step_label(step, value))
            row["label"].setToolTip(format_quote_value(self._quote, value))
        if mark_custom is True:
            self._custom.add(coin)
            row["custom"].setVisible(True)
            row["widget"].setStyleSheet(f"QFrame#panel {{ border-color: {ACCENT}; }}")
        elif mark_custom is False and coin not in self._custom:
            row["custom"].setVisible(False)
            row["widget"].setStyleSheet("")
        self._block = False
        self._update_row_wallet(coin)

    def _on_default_slider(self, step):
        if self._block:
            return
        self._default = self._step_to_value(step, self._global_base_value())
        self.default_label.setText(self._fmt_step_label(step, self._default))
        self.default_label.setToolTip(format_quote_value(self._quote, self._default))
        for coin in self._rows:
            if coin not in self._custom:
                self._set_coin_value(coin, self._default, mark_custom=False)
        self._update_count_label()
        if callable(self.budget_changed):
            prec = 2 if self._quote in ("USDT", "USDC") else 8
            self.budget_changed(f"{self._default:.{prec}f}")

    def _on_coin_slider(self, coin, step):
        if self._block:
            return
        base = self._coin_base_value()
        value = self._step_to_value(step, base)
        row = self._rows[coin]
        row["label"].setText(self._fmt_step_label(step, value))
        row["label"].setToolTip(format_quote_value(self._quote, value))
        self._custom.add(coin)
        row["custom"].setVisible(True)
        row["widget"].setStyleSheet(f"QFrame#panel {{ border-color: {ACCENT}; }}")
        self._update_count_label()
        self._update_row_wallet(coin)

    def set_default_budget(self, value, update_sliders=True):
        value = max(float(value), 0.0)
        if value == 0:
            # Exact zero target (sell-down); skip multiplier snap which floors at min order.
            self._default = 0.0
            self._block = True
            self.default_slider.setValue(0)
            self.default_label.setText(format_quote_value(self._quote, 0.0))
            self.default_label.setToolTip("0 — sell down holdings")
            self._block = False
        else:
            base = self._global_base_value()
            step = self._value_to_step(value, base)
            self._default = self._step_to_value(step, base)
            self._block = True
            self.default_slider.setValue(step)
            self.default_label.setText(self._fmt_step_label(step, self._default))
            self.default_label.setToolTip(format_quote_value(self._quote, self._default))
            self._block = False
        if update_sliders:
            for coin in self._rows:
                if coin not in self._custom:
                    self._set_coin_value(coin, self._default, mark_custom=False)

    def apply_advice(self, advice):
        if advice >= self._min_order:
            self._global_base = advice
            self.set_default_budget(advice)

    def reset_all_custom(self):
        self._custom.clear()
        for coin in self._rows:
            self._set_coin_value(coin, self._default, mark_custom=False)
        self._update_count_label()

    def get_default_budget(self):
        return self._default

    def get_coin_budgets(self):
        result = {}
        base = self._coin_base_value()
        for coin, row in self._rows.items():
            if coin not in self._custom and self._default == 0:
                result[coin] = 0.0
            else:
                result[coin] = self._step_to_value(row["slider"].value(), base)
        return result

    def get_custom_coins(self):
        return set(self._custom)


class MarketsPanel(QWidget):
    """Checkbox grid of tradable markets; unchecked coins are excluded from the bot."""

    COLUMNS = 6

    def __init__(self, parent=None, *, max_grid_height=None):
        super().__init__(parent)
        self._quote = "BTC"
        self._selected_markets = ["BTC"]
        self._checkboxes = {}
        self._pair_entries = {}
        self._block = False
        self._filter = ""
        self.selection_changed = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self.summary_label = QLabel("No markets loaded")
        self.summary_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        toolbar.addWidget(self.summary_label, stretch=1)

        self.select_all_btn = QPushButton("All on")
        self.select_all_btn.setObjectName("ghostBtn")
        self.select_all_btn.setFixedWidth(56)
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("All off")
        self.select_none_btn.setObjectName("ghostBtn")
        self.select_none_btn.setFixedWidth(56)
        self.select_none_btn.clicked.connect(self._select_none)
        toolbar.addWidget(self.select_none_btn)
        layout.addLayout(toolbar)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter markets…")
        self.search_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.search_edit)

        self.stack = QStackedWidget()
        self.empty_state = EmptyState(
            "No markets yet",
            "Run Update Markets to load pairs for your selected markets.",
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        if max_grid_height:
            scroll.setMaximumHeight(max_grid_height)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        scroll.setWidget(self.grid_host)
        self.stack.addWidget(self.empty_state)
        self.stack.addWidget(scroll)
        layout.addWidget(self.stack)

    def _notify(self):
        self._update_summary()
        if callable(self.selection_changed):
            self.selection_changed()

    def get_stats(self):
        total = len(self._checkboxes)
        active = sum(1 for cb in self._checkboxes.values() if cb.isChecked())
        return {"total": total, "active": active, "excluded": total - active}

    def _update_summary(self):
        stats = self.get_stats()
        market_label = format_markets_label(self._selected_markets)
        if stats["total"] == 0:
            self.summary_label.setText(f"No {market_label} markets loaded")
            return
        self.summary_label.setText(
            f"{stats['total']} {market_label} pairs · "
            f"{stats['active']} active · {stats['excluded']} excluded"
        )

    def load_from_config(self, config, coins=None):
        self._selected_markets = markets_from_config(config)
        self._quote = primary_quote_from_config(config)
        exclude = config.get("exclude") or []
        if coins is None:
            entries = []
            for quote in self._selected_markets:
                for coin in load_pair_coins(None, quote):
                    pair_id = market_id(coin, quote)
                    entries.append((pair_id, coin, quote))
        else:
            entries = []
            for item in coins:
                if isinstance(item, (tuple, list)) and len(item) >= 3:
                    entries.append((item[0], item[1], item[2]))
                elif isinstance(item, (tuple, list)) and len(item) == 2:
                    coin, quote = item[0], item[1]
                    entries.append((market_id(coin, quote), coin, quote))
                else:
                    coin = str(item)
                    quote = self._quote
                    entries.append((market_id(coin, quote), coin, quote))
        self._rebuild(entries, exclude)

    def _rebuild(self, entries, exclude):
        self._block = True
        for cb in self._checkboxes.values():
            self.grid_layout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()
        self._pair_entries = {}

        if not entries:
            self.stack.setCurrentWidget(self.empty_state)
            self._block = False
            self._update_summary()
            return

        self.stack.setCurrentIndex(1)
        for idx, (pair_id, coin, quote) in enumerate(entries):
            cb = QCheckBox(_pair_label(pair_id))
            cb.setChecked(not is_pair_excluded(coin, quote, exclude))
            cb.setToolTip(f"Trade {coin}/{quote}")
            cb.toggled.connect(self._on_toggle)
            row, col = divmod(idx, self.COLUMNS)
            self.grid_layout.addWidget(cb, row, col)
            self._checkboxes[pair_id] = cb
            self._pair_entries[pair_id] = (coin, quote)

        self._block = False
        self._on_filter_changed(self.search_edit.text())
        self._update_summary()

    def _on_toggle(self, _checked):
        if self._block:
            return
        self._notify()

    def _on_filter_changed(self, text):
        self._filter = text.strip().upper()
        for pair_id, cb in self._checkboxes.items():
            show = not self._filter or self._filter in pair_id.upper()
            cb.setVisible(show)

    def _select_all(self):
        self._block = True
        for cb in self._checkboxes.values():
            if cb.isVisible():
                cb.setChecked(True)
        self._block = False
        self._notify()

    def _select_none(self):
        self._block = True
        for cb in self._checkboxes.values():
            if cb.isVisible():
                cb.setChecked(False)
        self._block = False
        self._notify()

    def get_excluded(self):
        return sorted(
            pair_id for pair_id, cb in self._checkboxes.items() if not cb.isChecked()
        )


class TradingSettingsPanel(QFrame):
    """Compact budget / market / mode controls for the left sidebar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarSettings")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        layout.addWidget(SectionLabel("Trading"))

        self.budget_lbl = QLabel("Budget (BTC)")
        self.budget_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.budget_lbl)

        self.budget_edit = QLineEdit("0.0001")
        layout.addWidget(self.budget_edit)

        self.use_advice_btn = QPushButton("Budget advice")
        self.use_advice_btn.setObjectName("ghostBtn")
        layout.addWidget(self.use_advice_btn)

        layout.addSpacing(4)

        self.market_lbl = QLabel("Markets")
        self.market_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.market_lbl)

        market_row = QHBoxLayout()
        market_row.setSpacing(16)
        self.btc_check = QCheckBox("BTC")
        self.btc_check.setChecked(True)
        self.usdt_check = QCheckBox("USDT")
        market_row.addWidget(self.btc_check)
        market_row.addWidget(self.usdt_check)
        layout.addLayout(market_row)
        self.btc_check.toggled.connect(self._on_btc_market_toggled)
        self.usdt_check.toggled.connect(self._on_usdt_market_toggled)

        self.mode_lbl = QLabel("Mode")
        self.mode_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.mode_lbl)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(16)
        self.buy_check = QCheckBox("Buy")
        self.buy_check.setChecked(True)
        self.sell_check = QCheckBox("Sell")
        self.sell_check.setChecked(True)
        mode_row.addWidget(self.buy_check)
        mode_row.addWidget(self.sell_check)
        layout.addLayout(mode_row)

        layout.addSpacing(4)

        layout.addWidget(SectionLabel("Schedule"))

        self.schedule_enable = QCheckBox("Daily run")
        layout.addWidget(self.schedule_enable)

        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        time_lbl = QLabel("Time")
        time_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        time_lbl.setFixedWidth(36)
        time_row.addWidget(time_lbl)
        self.schedule_time = QTimeEdit()
        self.schedule_time.setDisplayFormat("HH:mm")
        self.schedule_time.setTime(QTime(18, 0))
        self.schedule_time.setFixedWidth(72)
        time_row.addWidget(self.schedule_time)
        time_row.addStretch()
        layout.addLayout(time_row)

        self.schedule_budget_check = QCheckBox("Fixed budget")
        layout.addWidget(self.schedule_budget_check)

        self.schedule_budget_edit = QLineEdit()
        self.schedule_budget_edit.setPlaceholderText("Same as budget above")
        self.schedule_budget_edit.setEnabled(False)
        layout.addWidget(self.schedule_budget_edit)

        self.start_after_missed_check = QCheckBox("Start if missed")
        self.start_after_missed_check.setChecked(True)
        self.start_after_missed_check.setToolTip(
            "Run as soon as possible after a missed scheduled time (PC was off/asleep)."
        )
        layout.addWidget(self.start_after_missed_check)

        self.schedule_status = QLabel("Schedule: off")
        self.schedule_status.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        self.schedule_status.setWordWrap(True)
        layout.addWidget(self.schedule_status)

        self.schedule_budget_check.toggled.connect(self._on_schedule_budget_toggled)

        self.save_btn = QPushButton("Save settings")
        self.save_btn.setObjectName("saveBtn")
        layout.addWidget(self.save_btn)

    def get_selected_markets(self):
        markets = []
        if self.btc_check.isChecked():
            markets.append("BTC")
        if self.usdt_check.isChecked():
            markets.append("USDT")
        return markets

    def set_selected_markets(self, markets):
        ordered = [str(m).upper() for m in (markets or []) if str(m).strip()]
        pick = ordered[0] if ordered else "BTC"
        if pick not in ("BTC", "USDT"):
            pick = "BTC"
        self.btc_check.blockSignals(True)
        self.usdt_check.blockSignals(True)
        self.btc_check.setChecked(pick == "BTC")
        self.usdt_check.setChecked(pick == "USDT")
        self.btc_check.blockSignals(False)
        self.usdt_check.blockSignals(False)
        self._update_budget_market_label()

    def _on_btc_market_toggled(self, checked):
        if checked:
            self.usdt_check.blockSignals(True)
            self.usdt_check.setChecked(False)
            self.usdt_check.blockSignals(False)
            self._update_budget_market_label()
            return
        if not self.usdt_check.isChecked():
            self.btc_check.blockSignals(True)
            self.btc_check.setChecked(True)
            self.btc_check.blockSignals(False)

    def _on_usdt_market_toggled(self, checked):
        if checked:
            self.btc_check.blockSignals(True)
            self.btc_check.setChecked(False)
            self.btc_check.blockSignals(False)
            self._update_budget_market_label()
            return
        if not self.btc_check.isChecked():
            self.usdt_check.blockSignals(True)
            self.usdt_check.setChecked(True)
            self.usdt_check.blockSignals(False)

    def _update_budget_market_label(self):
        quote = "USDT" if self.usdt_check.isChecked() else "BTC"
        self.budget_lbl.setText(f"Budget ({quote})")

    @staticmethod
    def trade_mode_from_checks(buy, sell):
        if buy and sell:
            return "both"
        if sell:
            return "sell"
        if buy:
            return "buy"
        return "test"

    def get_trade_mode(self):
        return self.trade_mode_from_checks(
            self.buy_check.isChecked(),
            self.sell_check.isChecked(),
        )

    def set_trade_mode(self, mode):
        mode = (mode or "both").lower()
        self.buy_check.blockSignals(True)
        self.sell_check.blockSignals(True)
        if mode == "sell":
            self.buy_check.setChecked(False)
            self.sell_check.setChecked(True)
        elif mode == "buy":
            self.buy_check.setChecked(True)
            self.sell_check.setChecked(False)
        elif mode == "test":
            self.buy_check.setChecked(False)
            self.sell_check.setChecked(False)
        else:
            self.buy_check.setChecked(True)
            self.sell_check.setChecked(True)
        self.buy_check.blockSignals(False)
        self.sell_check.blockSignals(False)

    def _on_schedule_budget_toggled(self, checked):
        self.schedule_budget_edit.setEnabled(checked)
        if not checked:
            self.schedule_budget_edit.clear()

    def get_schedule(self):
        budget = None
        if self.schedule_budget_check.isChecked():
            text = self.schedule_budget_edit.text().strip()
            if text:
                try:
                    budget = float(text)
                except ValueError:
                    budget = None
        return normalize_schedule({
            "enabled": self.schedule_enable.isChecked(),
            "time": self.schedule_time.time().toString("HH:mm"),
            "budget": budget,
            "start_after_missed": self.start_after_missed_check.isChecked(),
        })

    def set_schedule(self, schedule):
        schedule = normalize_schedule(schedule)
        self.schedule_enable.blockSignals(True)
        self.schedule_budget_check.blockSignals(True)
        self.start_after_missed_check.blockSignals(True)

        self.schedule_enable.setChecked(schedule["enabled"])
        hour, minute = (int(part) for part in schedule["time"].split(":", 1))
        self.schedule_time.setTime(QTime(hour, minute))

        if schedule["budget"] is not None:
            self.schedule_budget_check.setChecked(True)
            self.schedule_budget_edit.setEnabled(True)
            self.schedule_budget_edit.setText(str(schedule["budget"]))
        else:
            self.schedule_budget_check.setChecked(False)
            self.schedule_budget_edit.setEnabled(False)
            self.schedule_budget_edit.clear()

        self.start_after_missed_check.setChecked(schedule["start_after_missed"])

        self.schedule_enable.blockSignals(False)
        self.schedule_budget_check.blockSignals(False)
        self.start_after_missed_check.blockSignals(False)
        self.update_schedule_status(schedule)

    def update_schedule_status(self, schedule=None, task_state=None, extra=""):
        schedule = normalize_schedule(schedule or self.get_schedule())
        parts = [f"Schedule: {schedule_summary(schedule)}"]
        if schedule["enabled"] and task_state:
            parts.append(f"task {task_state.lower()}")
        if extra:
            parts.append(extra)
        self.schedule_status.setText(" · ".join(parts))


class OptionsPanel(QWidget):
    """API keys, app preferences, and session/error log viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.save_requested = None
        self.help_requested = None
        self._log_errors_only = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(10)

        api_body = QWidget()
        api_layout = QVBoxLayout(api_body)
        api_layout.setContentsMargins(0, 0, 0, 0)
        api_layout.setSpacing(8)
        api_row1 = QHBoxLayout()
        key_lbl = QLabel("API Key")
        key_lbl.setFixedWidth(80)
        key_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        api_row1.addWidget(key_lbl)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Your Poloniex API key")
        api_row1.addWidget(self.api_key_edit, stretch=1)
        api_layout.addLayout(api_row1)

        api_row2 = QHBoxLayout()
        sec_lbl = QLabel("Secret")
        sec_lbl.setFixedWidth(80)
        sec_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        api_row2.addWidget(sec_lbl)
        self.api_secret_edit = QLineEdit()
        self.api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_secret_edit.setPlaceholderText("Leave blank to keep saved secret")
        api_row2.addWidget(self.api_secret_edit, stretch=1)
        self.show_secret_check = QCheckBox("Show")
        self.show_secret_check.toggled.connect(self._toggle_secret_visibility)
        api_row2.addWidget(self.show_secret_check)
        api_layout.addLayout(api_row2)

        self.api_status_label = QLabel("")
        self.api_status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        api_layout.addWidget(self.api_status_label)

        api_actions = QHBoxLayout()
        api_actions.addStretch()
        self.save_api_btn = QPushButton("Save API & options")
        self.save_api_btn.setObjectName("saveBtn")
        self.save_api_btn.clicked.connect(self._on_save)
        api_actions.addWidget(self.save_api_btn)
        api_layout.addLayout(api_actions)
        self.api_section = CollapsibleSection("API credentials", expanded=False)
        self.api_section.set_content(api_body)
        layout.addWidget(self.api_section)

        prefs_body = QWidget()
        prefs_layout = QVBoxLayout(prefs_body)
        prefs_layout.setContentsMargins(0, 0, 0, 0)
        prefs_row = QHBoxLayout()
        self.verbose_check = QCheckBox("Verbose log (extra bot output in session log)")
        self.verbose_check.setChecked(True)
        prefs_row.addWidget(self.verbose_check)
        prefs_row.addStretch()
        self.help_btn = QPushButton("Help")
        self.help_btn.setObjectName("ghostBtn")
        self.help_btn.clicked.connect(self._on_help)
        prefs_row.addWidget(self.help_btn)
        prefs_layout.addLayout(prefs_row)
        self.prefs_section = CollapsibleSection("Preferences", expanded=False)
        self.prefs_section.set_content(prefs_body)
        layout.addWidget(self.prefs_section)

        self.colibri_list_requested = None
        self.colibri_download_requested = None
        self.colibri_start_requested = None
        self.colibri_stop_requested = None
        self.colibri_status_requested = None
        self._colibri_model_ids = []
        self._colibri_model_local = []

        def _field_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            return lbl

        def _compact_field(label, editor, *, trailing=None, max_width=200):
            cell = QWidget()
            cell.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(2)
            cell_layout.addWidget(_field_label(label))
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            editor.setMaximumWidth(max_width)
            row.addWidget(editor)
            if trailing is not None:
                row.addWidget(trailing)
            row.addStretch()
            cell_layout.addLayout(row)
            return cell

        # Pinned above (always visible): enable
        llm_pinned_above = QWidget()
        llm_pinned_above.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        pinned_above_layout = QVBoxLayout(llm_pinned_above)
        pinned_above_layout.setContentsMargins(0, 0, 0, 0)
        pinned_above_layout.setSpacing(4)
        self.llm_enabled_check = QCheckBox("Enable Colibri integration")
        self.llm_enabled_check.setChecked(True)
        pinned_above_layout.addWidget(self.llm_enabled_check)

        # Collapsible body (red): compact input rows + automation
        llm_body = QWidget()
        llm_layout = QVBoxLayout(llm_body)
        llm_layout.setContentsMargins(0, 0, 0, 0)
        llm_layout.setSpacing(6)

        self.llm_models_dir_edit = QLineEdit()
        self.llm_models_dir_edit.setPlaceholderText("Empty = AppData models")
        self.llm_models_dir_browse_btn = QPushButton("Browse…")
        self.llm_models_dir_browse_btn.setObjectName("ghostBtn")
        self.llm_models_dir_browse_btn.clicked.connect(self._browse_models_dir)

        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token_edit.setPlaceholderText("HF token (blank = keep)")
        self.show_hf_check = QCheckBox("Show")
        self.show_hf_check.toggled.connect(self._toggle_hf_visibility)

        self.colibri_model_combo = QComboBox()
        self.colibri_model_combo.setEditable(True)
        self.colibri_model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.colibri_model_combo.setPlaceholderText("Model id")
        self.colibri_model_combo.currentIndexChanged.connect(self._on_colibri_model_index_changed)
        self.colibri_refresh_btn = QPushButton("Refresh")
        self.colibri_refresh_btn.setObjectName("ghostBtn")
        self.colibri_refresh_btn.clicked.connect(self._on_colibri_list)

        inputs_row1 = QHBoxLayout()
        inputs_row1.setSpacing(8)
        inputs_row1.addWidget(
            _compact_field(
                "Models folder",
                self.llm_models_dir_edit,
                trailing=self.llm_models_dir_browse_btn,
                max_width=200,
            )
        )
        inputs_row1.addWidget(
            _compact_field(
                "HF token",
                self.hf_token_edit,
                trailing=self.show_hf_check,
                max_width=200,
            )
        )
        inputs_row1.addWidget(
            _compact_field(
                "Model",
                self.colibri_model_combo,
                trailing=self.colibri_refresh_btn,
                max_width=220,
            )
        )
        inputs_row1.addStretch()
        llm_layout.addLayout(inputs_row1)

        self.llm_base_url_edit = QLineEdit()
        self.llm_base_url_edit.setPlaceholderText("http://127.0.0.1:8000/v1")
        self.llm_base_url_edit.setText("http://127.0.0.1:8000/v1")
        self.llm_api_key_edit = QLineEdit()
        self.llm_api_key_edit.setPlaceholderText("local (or COLI_API_KEY)")
        self.llm_api_key_edit.setText("local")
        self.llm_model_edit = QLineEdit()
        self.llm_model_edit.setPlaceholderText("Empty = first from /v1/models")
        self.llm_coli_vk_device_edit = QLineEdit()
        self.llm_coli_vk_device_edit.setPlaceholderText("Empty = prefer Intel Arc")

        inputs_row2 = QHBoxLayout()
        inputs_row2.setSpacing(8)
        inputs_row2.addWidget(_compact_field("Base URL", self.llm_base_url_edit, max_width=200))
        inputs_row2.addWidget(_compact_field("API key", self.llm_api_key_edit, max_width=200))
        inputs_row2.addWidget(_compact_field("Serve model", self.llm_model_edit, max_width=200))
        inputs_row2.addWidget(
            _compact_field("Vulkan GPU", self.llm_coli_vk_device_edit, max_width=200)
        )
        inputs_row2.addStretch()
        llm_layout.addLayout(inputs_row2)

        self.colibri_gpu_label = QLabel("")
        self.colibri_gpu_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.colibri_gpu_label.setWordWrap(True)
        llm_layout.addWidget(self.colibri_gpu_label)

        self.llm_auto_place_check = QCheckBox(
            "Auto-place AI orders (default off — uses existing place pipeline)"
        )
        self.llm_auto_place_check.setChecked(False)
        llm_layout.addWidget(self.llm_auto_place_check)

        self.llm_loop_check = QCheckBox("Background AI loop (service-like)")
        self.llm_loop_check.setChecked(False)
        llm_layout.addWidget(self.llm_loop_check)

        loop_row = QHBoxLayout()
        loop_lbl = QLabel("Loop interval (min)")
        loop_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        loop_row.addWidget(loop_lbl)
        self.llm_loop_interval_edit = QLineEdit("60")
        self.llm_loop_interval_edit.setFixedWidth(80)
        loop_row.addWidget(self.llm_loop_interval_edit)
        loop_row.addStretch()
        llm_layout.addLayout(loop_row)

        self.llm_status_check = QCheckBox("Autonomous Colibri status reports")
        self.llm_status_check.setChecked(True)
        llm_layout.addWidget(self.llm_status_check)

        status_row = QHBoxLayout()
        status_lbl = QLabel("Status interval (min)")
        status_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        status_row.addWidget(status_lbl)
        self.llm_status_interval_edit = QLineEdit("15")
        self.llm_status_interval_edit.setFixedWidth(80)
        status_row.addWidget(self.llm_status_interval_edit)
        status_row.addStretch()
        llm_layout.addLayout(status_row)

        # Pinned below (always visible): actions + log + autostart
        llm_pinned_below = QWidget()
        llm_pinned_below.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        pinned_below_layout = QVBoxLayout(llm_pinned_below)
        pinned_below_layout.setContentsMargins(0, 0, 0, 0)
        pinned_below_layout.setSpacing(4)

        coli_btn_row = QHBoxLayout()
        self.colibri_download_btn = QPushButton("Download / setup model")
        self.colibri_download_btn.setObjectName("ghostBtn")
        self.colibri_download_btn.clicked.connect(self._on_colibri_download)
        coli_btn_row.addWidget(self.colibri_download_btn)
        self.colibri_start_btn = QPushButton("Start Colibri")
        self.colibri_start_btn.setObjectName("ghostBtn")
        self.colibri_start_btn.clicked.connect(self._on_colibri_start)
        coli_btn_row.addWidget(self.colibri_start_btn)
        self.colibri_stop_btn = QPushButton("Stop")
        self.colibri_stop_btn.setObjectName("ghostBtn")
        self.colibri_stop_btn.clicked.connect(self._on_colibri_stop)
        coli_btn_row.addWidget(self.colibri_stop_btn)
        self.colibri_status_btn = QPushButton("Status")
        self.colibri_status_btn.setObjectName("ghostBtn")
        self.colibri_status_btn.clicked.connect(self._on_colibri_status)
        coli_btn_row.addWidget(self.colibri_status_btn)
        coli_btn_row.addStretch()
        pinned_below_layout.addLayout(coli_btn_row)

        self.colibri_progress = QProgressBar()
        self.colibri_progress.setRange(0, 100)
        self.colibri_progress.setValue(0)
        self.colibri_progress.setTextVisible(True)
        pinned_below_layout.addWidget(self.colibri_progress)

        self.colibri_log = QPlainTextEdit()
        self.colibri_log.setObjectName("logView")
        self.colibri_log.setReadOnly(True)
        self.colibri_log.setMinimumHeight(220)
        self.colibri_log.setPlaceholderText("Colibri setup / download output…")
        pinned_below_layout.addWidget(self.colibri_log)

        self.llm_autostart_check = QCheckBox("Auto-start Colibri when TradeBot opens")
        self.llm_autostart_check.setChecked(False)
        pinned_below_layout.addWidget(self.llm_autostart_check)

        self.llm_section = CollapsibleSection("Colibri / local LLM", expanded=False)
        self.llm_section.set_pinned_above(llm_pinned_above)
        self.llm_section.set_content(llm_body)
        self.llm_section.set_pinned_below(llm_pinned_below)
        layout.addWidget(self.llm_section)

        paths_body = QWidget()
        paths_layout = QVBoxLayout(paths_body)
        paths_layout.setContentsMargins(0, 0, 0, 0)
        paths_layout.setSpacing(4)
        self.log_path_label = QLabel("")
        self.log_path_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.log_path_label.setWordWrap(True)
        self.data_path_label = QLabel("")
        self.data_path_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.data_path_label.setWordWrap(True)
        paths_layout.addWidget(QLabel("Session log"))
        paths_layout.addWidget(self.log_path_label)
        paths_layout.addWidget(QLabel("Saved data"))
        paths_layout.addWidget(self.data_path_label)
        self.paths_section = CollapsibleSection("Paths", expanded=False)
        self.paths_section.set_content(paths_body)
        layout.addWidget(self.paths_section)

        log_body = QWidget()
        log_layout = QVBoxLayout(log_body)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        log_toolbar = QHBoxLayout()
        self.log_mode_label = QLabel("Showing errors only")
        self.log_mode_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        log_toolbar.addWidget(self.log_mode_label)
        log_toolbar.addStretch()
        self.errors_btn = QPushButton("Errors")
        self.errors_btn.setObjectName("ghostBtn")
        self.errors_btn.setCheckable(True)
        self.errors_btn.setChecked(True)
        self.errors_btn.clicked.connect(lambda: self.refresh_log(errors_only=True))
        log_toolbar.addWidget(self.errors_btn)
        self.full_log_btn = QPushButton("Full log")
        self.full_log_btn.setObjectName("ghostBtn")
        self.full_log_btn.setCheckable(True)
        self.full_log_btn.clicked.connect(lambda: self.refresh_log(errors_only=False))
        log_toolbar.addWidget(self.full_log_btn)
        self.refresh_log_btn = QPushButton("Refresh")
        self.refresh_log_btn.setObjectName("ghostBtn")
        self.refresh_log_btn.clicked.connect(lambda: self.refresh_log())
        log_toolbar.addWidget(self.refresh_log_btn)
        self.open_log_btn = QPushButton("Open folder")
        self.open_log_btn.setObjectName("ghostBtn")
        self.open_log_btn.clicked.connect(self.open_logs_folder)
        log_toolbar.addWidget(self.open_log_btn)
        log_layout.addLayout(log_toolbar)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_view.setPlaceholderText("Error and session lines from logs/tradebot.log")
        log_layout.addWidget(self.log_view, stretch=1)
        self.log_section = CollapsibleSection("Error log", expanded=False)
        self.log_section.set_content(log_body, stretch=1)
        layout.addWidget(self.log_section, stretch=1)

    def set_paths(self, log_path, data_dir):
        self.log_path_label.setText(log_path)
        self.data_path_label.setText(data_dir)

    def set_api_status(self, configured):
        if configured:
            self.api_status_label.setText("Credentials saved — ready to trade")
            self.api_status_label.setStyleSheet(f"color: {SUCCESS}; font-size: 11px;")
        else:
            self.api_status_label.setText("Enter API key and secret, then save")
            self.api_status_label.setStyleSheet(f"color: {DANGER}; font-size: 11px;")

    def load_api_fields(self, api_key):
        self.api_key_edit.setText(api_key)
        self.api_secret_edit.clear()

    def load_llm_fields(self, llm):
        from llm_config import default_models_dir_candidate

        llm = llm or {}
        self.llm_enabled_check.setChecked(bool(llm.get("enabled", True)))
        models_dir = str(llm.get("models_dir") or "").strip()
        if not models_dir:
            models_dir = default_models_dir_candidate() or ""
        self.llm_models_dir_edit.setText(models_dir)
        self.llm_base_url_edit.setText(str(llm.get("base_url") or "http://127.0.0.1:8000/v1"))
        self.llm_api_key_edit.setText(str(llm.get("api_key") or "local"))
        self.llm_model_edit.setText(str(llm.get("model") or ""))
        self.llm_auto_place_check.setChecked(bool(llm.get("auto_place", False)))
        self.llm_loop_check.setChecked(bool(llm.get("loop_enabled", False)))
        self.llm_loop_interval_edit.setText(str(llm.get("loop_interval_minutes") or 60))
        self.llm_status_check.setChecked(bool(llm.get("status_reports_enabled", True)))
        self.llm_status_interval_edit.setText(str(llm.get("status_interval_minutes") or 15))
        self.llm_autostart_check.setChecked(bool(llm.get("colibri_autostart", False)))
        self.llm_coli_vk_device_edit.setText(str(llm.get("coli_vk_device") or ""))
        colibri_model = str(llm.get("colibri_model") or "").strip()
        if colibri_model:
            idx = self.colibri_model_combo.findText(colibri_model)
            if idx < 0:
                self.colibri_model_combo.addItem(colibri_model)
                idx = self.colibri_model_combo.findText(colibri_model)
            if idx >= 0:
                self.colibri_model_combo.setCurrentIndex(idx)
            else:
                self.colibri_model_combo.setEditText(colibri_model)

    def get_llm_fields(self):
        try:
            loop_mins = int(self.llm_loop_interval_edit.text().strip() or "60")
        except ValueError:
            loop_mins = 60
        try:
            status_mins = int(self.llm_status_interval_edit.text().strip() or "15")
        except ValueError:
            status_mins = 15
        return {
            "enabled": self.llm_enabled_check.isChecked(),
            "models_dir": self.llm_models_dir_edit.text().strip(),
            "base_url": self.llm_base_url_edit.text().strip(),
            "api_key": self.llm_api_key_edit.text().strip() or "local",
            "model": self.llm_model_edit.text().strip(),
            "auto_place": self.llm_auto_place_check.isChecked(),
            "loop_enabled": self.llm_loop_check.isChecked(),
            "loop_interval_minutes": loop_mins,
            "status_reports_enabled": self.llm_status_check.isChecked(),
            "status_interval_minutes": status_mins,
            "colibri_autostart": self.llm_autostart_check.isChecked(),
            "colibri_model": self.get_selected_colibri_model(),
            "coli_vk_device": self.llm_coli_vk_device_edit.text().strip(),
        }

    def get_hf_token_input(self):
        return self.hf_token_edit.text().strip()

    def clear_hf_token_input(self):
        self.hf_token_edit.clear()

    def get_selected_colibri_model(self):
        text = self.colibri_model_combo.currentText().strip()
        # Combo display may include "id — 22 GB (good)"
        if " — " in text:
            text = text.split(" — ", 1)[0].strip()
        if self._colibri_model_ids and self.colibri_model_combo.currentIndex() >= 0:
            idx = self.colibri_model_combo.currentIndex()
            if idx < len(self._colibri_model_ids):
                return self._colibri_model_ids[idx]
        return text

    def set_colibri_models(self, models):
        current = self.get_selected_colibri_model()
        self.colibri_model_combo.clear()
        self._colibri_model_ids = []
        self._colibri_model_local = []
        for item in models or []:
            mid = str(item.get("id") or "").strip()
            if not mid:
                continue
            local = bool(item.get("local"))
            if local:
                label = f"{mid} — local"
            else:
                gb = item.get("download_gb")
                status = item.get("status") or ""
                rec = " ★" if item.get("recommended") else ""
                label = (
                    f"{mid} — {gb} GB ({status}){rec}"
                    if gb is not None
                    else f"{mid} ({status}){rec}"
                )
            self._colibri_model_ids.append(mid)
            self._colibri_model_local.append(local)
            self.colibri_model_combo.addItem(label)
        if current:
            for i, mid in enumerate(self._colibri_model_ids):
                if mid == current:
                    self.colibri_model_combo.setCurrentIndex(i)
                    break
            else:
                self.colibri_model_combo.setEditText(current)
        self._on_colibri_model_index_changed(self.colibri_model_combo.currentIndex())

    def set_download_button_for_model(self, local: bool):
        self.colibri_download_btn.setText(
            "Use local model" if local else "Download / setup model"
        )

    def _on_colibri_model_index_changed(self, index):
        local = False
        if 0 <= index < len(self._colibri_model_local):
            local = bool(self._colibri_model_local[index])
        self.set_download_button_for_model(local)

    def _browse_models_dir(self):
        from colibri_manager import default_models_dir

        start = self.llm_models_dir_edit.text().strip() or default_models_dir() or ""
        chosen = QFileDialog.getExistingDirectory(self, "Select Colibri models folder", start)
        if chosen:
            self.llm_models_dir_edit.setText(chosen)
            if callable(self.colibri_list_requested):
                self.colibri_list_requested()

    def append_colibri_log(self, line):
        self.colibri_log.appendPlainText(str(line))

    def set_colibri_progress(self, percent, text=None):
        try:
            value = int(percent)
        except (TypeError, ValueError):
            value = 0
        self.colibri_progress.setValue(max(0, min(100, value)))
        if text:
            self.colibri_progress.setFormat(str(text))
        else:
            self.colibri_progress.setFormat("%p%")

    def set_colibri_gpu_status(self, gpu_name=None, warning=None, coli_vk_dev=None):
        parts = []
        name = (gpu_name or "").strip()
        if name:
            idx = str(coli_vk_dev or "").strip()
            parts.append(
                f"Active GPU: {name}" + (f" (COLI_VK_DEV={idx})" if idx else "")
            )
        warn = (warning or "").strip()
        if warn:
            parts.append(warn)
        self.colibri_gpu_label.setText("\n".join(parts))
        if warn:
            self.colibri_gpu_label.setStyleSheet(f"color: {DANGER}; font-size: 11px;")
        else:
            self.colibri_gpu_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

    def _toggle_secret_visibility(self, show):
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.api_secret_edit.setEchoMode(mode)

    def _toggle_hf_visibility(self, show):
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.hf_token_edit.setEchoMode(mode)

    def _on_colibri_list(self):
        if callable(self.colibri_list_requested):
            self.colibri_list_requested()

    def _on_colibri_download(self):
        if callable(self.colibri_download_requested):
            self.colibri_download_requested()

    def _on_colibri_start(self):
        if callable(self.colibri_start_requested):
            self.colibri_start_requested()

    def _on_colibri_stop(self):
        if callable(self.colibri_stop_requested):
            self.colibri_stop_requested()

    def _on_colibri_status(self):
        if callable(self.colibri_status_requested):
            self.colibri_status_requested()

    def _on_save(self):
        if callable(self.save_requested):
            self.save_requested()

    def _on_help(self):
        if callable(self.help_requested):
            self.help_requested()

    def refresh_log(self, errors_only=None):
        if errors_only is None:
            errors_only = self._log_errors_only
        else:
            self._log_errors_only = errors_only
        self.errors_btn.setChecked(errors_only)
        self.full_log_btn.setChecked(not errors_only)
        self.log_mode_label.setText(
            "Showing errors only" if errors_only else "Showing full session log"
        )
        text, line_count, _path = read_session_log(errors_only=errors_only)
        self.log_view.setPlainText(text)
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        self.log_mode_label.setText(
            f"{'Errors' if errors_only else 'Full log'} · {line_count} line(s)"
        )

    def open_logs_folder(self):
        import subprocess
        import sys

        folder = os.path.join(app_dir(), "logs")
        os.makedirs(folder, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)


class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(12)

        actions_panel = Panel("Recent actions")
        self.actions_table = QTableWidget(0, 4)
        self.actions_table.setHorizontalHeaderLabels(["Time", "Action", "Status", "Detail"])
        self.actions_table.horizontalHeader().setStretchLastSection(True)
        self.actions_table.setAlternatingRowColors(True)
        self.actions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.actions_table.setShowGrid(False)
        self.actions_table.verticalHeader().setVisible(False)
        self.actions_empty = EmptyState("No actions yet", "Bot runs will appear here.")
        self.actions_stack = QStackedWidget()
        self.actions_stack.addWidget(self.actions_empty)
        self.actions_stack.addWidget(self.actions_table)
        actions_panel.layout.addWidget(self.actions_stack)
        layout.addWidget(actions_panel, stretch=1)

        orders_panel = Panel("Order history")
        self.orders_table = QTableWidget(0, 6)
        self.orders_table.setHorizontalHeaderLabels(
            ["Time", "Run", "Side", "Coin", "Amount", "Total BTC"]
        )
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.orders_table.setShowGrid(False)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_empty = EmptyState("No orders yet", "Build or place orders to see them here.")
        self.orders_stack = QStackedWidget()
        self.orders_stack.addWidget(self.orders_empty)
        self.orders_stack.addWidget(self.orders_table)
        orders_panel.layout.addWidget(self.orders_stack)
        layout.addWidget(orders_panel, stretch=2)

    def set_action_history(self, history):
        if not history:
            self.actions_stack.setCurrentWidget(self.actions_empty)
            return
        self.actions_stack.setCurrentWidget(self.actions_table)
        self.actions_table.setRowCount(len(history))
        for row, entry in enumerate(history):
            ok = entry.get("ok", True)
            status = "OK" if ok else "FAILED"
            cells = [
                str(entry.get("time", "")),
                str(entry.get("action", "")),
                status,
                str(entry.get("detail", "")),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 2:
                    item.setForeground(QColor(BUY if ok else SELL))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.actions_table.setItem(row, col, item)
        self.actions_table.resizeColumnsToContents()

    def set_order_runs(self, runs):
        rows = []
        for run in runs:
            for order in run.get("orders") or []:
                rows.append({
                    "time": run.get("time", ""),
                    "run": run.get("action", ""),
                    "side": order.get("side", ""),
                    "coin": order.get("alt", order.get("symbol", "")),
                    "amount": order.get("alt_amount", order.get("quantity", 0)),
                    "total": order.get("total", 0),
                })
        if not rows:
            self.orders_stack.setCurrentWidget(self.orders_empty)
            return
        self.orders_stack.setCurrentWidget(self.orders_table)
        self.orders_table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            side = str(item["side"]).upper()
            values = [
                str(item["time"]),
                str(item["run"]),
                side,
                str(item["coin"]),
                f"{float(item['amount']):.8f}",
                _fmt_btc(float(item["total"]) if item["total"] else 0),
            ]
            for col, text in enumerate(values):
                cell = QTableWidgetItem(text)
                if col == 2:
                    if side == "BUY":
                        cell.setForeground(QColor(BUY))
                    elif side == "SELL":
                        cell.setForeground(QColor(SELL))
                    f = cell.font()
                    f.setBold(True)
                    cell.setFont(f)
                self.orders_table.setItem(row, col, cell)
        self.orders_table.resizeColumnsToContents()
