"""Tests for GUI data persistence and wallet cache."""

import pytest

from gui.data_store import DataStore, build_wallet_from_cache
from tests.conftest import write_json


class TestBuildWalletFromCache:
    def test_builds_holdings_from_balances_and_tickers(self, tmp_path):
        write_json(
            tmp_path / "json" / "poloniex_balances.json",
            {"BTC": ["0.01"], "ADA": ["1000"], "ETH": ["0"]},
        )
        write_json(
            tmp_path / "json" / "poloniex_tickers.json",
            {
                "ADA/BTC": {"last": "0.00001000"},
                "BTC/USDT": {"last": "50000"},
            },
        )

        wallet = build_wallet_from_cache(tmp_path)

        assert wallet["total_btc"] == pytest.approx(0.01 + 1000 * 0.00001)
        assert len(wallet["holdings"]) == 2
        coins = {h["coin"] for h in wallet["holdings"]}
        assert coins == {"ADA", "BTC"}

    def test_missing_balances_returns_empty_wallet(self, tmp_path):
        wallet = build_wallet_from_cache(tmp_path)
        assert wallet["holdings"] == []
        assert wallet["total_btc"] == 0.0


class TestDataStore:
    def test_record_action_caps_history(self, tmp_path):
        store = DataStore(tmp_path)
        for i in range(505):
            store.record_action(f"action_{i}", ok=True)
        history = store.get_action_history()
        assert len(history) == 500
        assert history[0]["action"] == "action_504"

    def test_record_order_run(self, tmp_path):
        store = DataStore(tmp_path)
        orders = [{"side": "SELL", "alt": "ADA"}]
        entry = store.record_order_run(orders, "preview_orders", placed=False)
        assert entry["count"] == 1
        assert entry["placed"] is False
        runs = store.get_order_runs()
        assert runs[0]["action"] == "preview_orders"
