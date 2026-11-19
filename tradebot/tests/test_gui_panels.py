"""Lightweight Qt widget tests for panel logic (no full app window)."""

import pytest

pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication

from gui.panels import BudgetPanel, MarketsPanel, TradingSettingsPanel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestMarketsPanel:
    def test_load_from_config_marks_excluded_unchecked(self, qapp):
        panel = MarketsPanel()
        panel.show()
        qapp.processEvents()
        panel.load_from_config(
            {"quote_currency": "BTC", "exclude": ["ETH"]},
            coins=["ADA", "ETH", "DOGE"],
        )

        stats = panel.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 2
        assert stats["excluded"] == 1
        assert panel.get_excluded() == ["ETH_BTC"]

    def test_select_none_excludes_all_visible(self, qapp):
        panel = MarketsPanel()
        panel.show()
        qapp.processEvents()
        panel.load_from_config({"quote_currency": "BTC", "exclude": []}, coins=["ADA", "ETH"])
        qapp.processEvents()

        panel._select_none()
        qapp.processEvents()

        assert panel.get_excluded() == ["ADA_BTC", "ETH_BTC"]
        assert panel.get_stats()["active"] == 0

    def test_filter_hides_non_matching_checkboxes(self, qapp):
        panel = MarketsPanel()
        panel.show()
        qapp.processEvents()
        panel.load_from_config({"quote_currency": "BTC", "exclude": []}, coins=["ADA", "ETH", "DOGE"])
        qapp.processEvents()

        panel._on_filter_changed("DO")
        qapp.processEvents()

        assert panel._checkboxes["DOGE_BTC"].isVisible()
        assert not panel._checkboxes["ADA_BTC"].isVisible()
        assert not panel._checkboxes["ETH_BTC"].isVisible()


class TestBudgetPanel:
    def test_coin_grid_uses_three_columns_when_wide(self, qapp):
        panel = BudgetPanel()
        panel.resize(1000, 500)
        panel.show()
        qapp.processEvents()
        panel._sync_column_count()
        panel.load_from_config(
            {"quote_currency": "BTC", "budget": 0.0001, "advice": 0.0001},
            coins=["ADA", "ETH", "DOGE", "XRP", "LTC", "DOT"],
        )
        qapp.processEvents()

        assert panel._column_count == 3
        assert panel.coins_layout.itemAtPosition(0, 0) is not None
        assert panel.coins_layout.itemAtPosition(0, 2) is not None
        assert panel.coins_layout.itemAtPosition(1, 0) is not None
        assert panel.coins_layout.columnStretch(2) == 1
        assert panel._rows["ADA_BTC"]["widget"].height() == 72
        assert panel.coins_host.height() >= 72

    def test_two_columns_clears_third_column_stretch(self, qapp):
        panel = BudgetPanel()
        panel.resize(500, 400)
        panel.show()
        qapp.processEvents()
        panel._sync_column_count()
        panel.load_from_config(
            {"quote_currency": "BTC", "budget": 0.0001, "advice": 0.0001},
            coins=["ADA", "ETH", "DOGE", "XRP"],
        )
        qapp.processEvents()

        assert panel._column_count == 2
        assert panel.coins_layout.itemAtPosition(0, 2) is None
        assert panel.coins_layout.columnStretch(2) == 0

    def test_filter_reflows_coin_grid(self, qapp):
        panel = BudgetPanel()
        panel.resize(900, 400)
        panel.show()
        qapp.processEvents()
        panel.load_from_config(
            {"quote_currency": "BTC", "budget": 0.0001, "advice": 0.0001},
            coins=["ADA", "ETH", "DOGE"],
        )
        qapp.processEvents()

        panel._on_filter_changed("DO")
        qapp.processEvents()

        assert panel.coins_layout.count() == 1
        assert panel.coins_layout.itemAtPosition(0, 0) is not None
        assert not panel._rows["ADA_BTC"]["widget"].isVisible()


class TestTradingSettingsPanel:
    def test_trade_mode_both_when_buy_and_sell_checked(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_trade_mode("both")
        assert panel.get_trade_mode() == "both"

    def test_trade_mode_sell_only(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_trade_mode("sell")
        assert panel.get_trade_mode() == "sell"
        assert not panel.buy_check.isChecked()
        assert panel.sell_check.isChecked()

    def test_trade_mode_buy_only(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_trade_mode("buy")
        assert panel.get_trade_mode() == "buy"
        assert panel.buy_check.isChecked()
        assert not panel.sell_check.isChecked()

    def test_trade_mode_test_when_neither_checked(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_trade_mode("test")
        assert panel.get_trade_mode() == "test"
        assert not panel.buy_check.isChecked()
        assert not panel.sell_check.isChecked()
        assert TradingSettingsPanel.trade_mode_from_checks(False, False) == "test"

    def test_selected_markets_xor(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_selected_markets(["USDT"])
        assert panel.get_selected_markets() == ["USDT"]
        assert panel.budget_lbl.text() == "Budget (USDT)"
        panel.set_selected_markets(["BTC", "USDT"])
        assert panel.get_selected_markets() == ["BTC"]
        assert panel.budget_lbl.text() == "Budget (BTC)"

    def test_market_xor_toggle(self, qapp):
        panel = TradingSettingsPanel()
        panel.btc_check.setChecked(True)
        panel.usdt_check.setChecked(True)
        assert panel.get_selected_markets() == ["USDT"]
        assert not panel.btc_check.isChecked()
        panel.usdt_check.setChecked(False)
        assert panel.get_selected_markets() == ["USDT"]
        assert panel.usdt_check.isChecked()

    def test_schedule_round_trip(self, qapp):
        panel = TradingSettingsPanel()
        panel.set_schedule({
            "enabled": True,
            "time": "18:30",
            "budget": 5.0,
            "start_after_missed": True,
        })
        sched = panel.get_schedule()
        assert sched["enabled"] is True
        assert sched["time"] == "18:30"
        assert sched["budget"] == 5.0
        assert sched["start_after_missed"] is True
