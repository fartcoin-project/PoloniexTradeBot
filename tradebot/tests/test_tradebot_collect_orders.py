"""Tests for tradebot.collect_orders() order-building logic."""

import json

import pytest

import tradebot
from api_compat import MIN_ORDER_BTC, OperationCancelled
from tests.conftest import seed_market_files


def _load_orderlist(root):
    return json.loads((root / "json" / "orderlist.json").read_text(encoding="utf-8"))


class TestCollectOrders:
    def test_collect_orders_places_buy_when_under_budget(self, tradebot_env, mock_polo):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["0"]},
            tickers={"ADA/BTC": {"last": "0.00001000"}},
            config={
                "time": "",
                "budget": 0.0008,
                "balance": "0.01",
                "advice": 0.0,
                "exclude": [],
            },
        )

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        order = orders[0]
        assert order["side"] == "BUY"
        assert order["alt"] == "ADA"
        assert order["symbol"] == "ADA/BTC"
        assert order["total"] >= MIN_ORDER_BTC
        mock_polo.fetch_order_book.assert_called()

    def test_collect_orders_places_sell_when_over_budget(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["200000.0"]},
            tickers={"ADA/BTC": {"last": "0.00001000"}},
            config={
                "time": "",
                "budget": 0.0008,
                "balance": "0.01",
                "advice": 0.0,
                "exclude": [],
            },
        )

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        assert orders[0]["side"] == "SELL"
        assert orders[0]["alt"] == "ADA"

    def test_collect_orders_skips_excluded_coins(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["0"]},
            config={
                "time": "",
                "budget": 0.0008,
                "balance": "0.01",
                "advice": 0.0,
                "exclude": ["ADA"],
            },
        )
        tradebot.exclude_list = ["ADA"]

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert orders == []

    def test_collect_orders_buy_only_marks_sells_as_exclude(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["200000.0"]},
            config={"time": "", "budget": 0.0008, "balance": "0.01", "advice": 0.0, "exclude": []},
        )
        tradebot.args.sell = False  # buy only

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        assert orders[0]["side"] == "exclude"

    def test_collect_orders_sell_only_marks_buys_as_exclude(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["0"]},
            config={"time": "", "budget": 0.0008, "balance": "0.01", "advice": 0.0, "exclude": []},
        )
        tradebot.args.sell = True  # sell only

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        assert orders[0]["side"] == "exclude"

    def test_collect_orders_uses_per_coin_budget_override(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["50000.0"]},
            tickers={"ADA/BTC": {"last": "0.00001000"}},
            config={
                "time": "",
                "budget": 0.0008,
                "coin_budgets": {"ADA": 0.0005},
                "coin_budget_custom": ["ADA"],
                "balance": "0.01",
                "advice": 0.0,
                "exclude": [],
            },
        )
        # alt worth = 50000 * 0.00001 = 0.5 BTC >> 0.0005 budget -> SELL

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        assert orders[0]["side"] == "SELL"

    def test_collect_orders_skips_invalid_symbols(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["BAD/COIN", "ADA"],
            balances={"BTC": ["0.01000000"], "ADA": ["0"]},
        )

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        assert len(orders) == 1
        assert orders[0]["alt"] == "ADA"

    def test_collect_orders_respects_cancel(self, tradebot_env):
        seed_market_files(tradebot_env, coins=["ADA", "ETH"])
        tradebot.set_cancel_check(lambda: True)

        with pytest.raises(OperationCancelled):
            tradebot.collect_orders(show=False)

    def test_collect_orders_caps_buy_to_available_btc(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.00020000"], "ADA": ["0"]},
            config={"time": "", "budget": 0.0008, "balance": "0.0002", "advice": 0.0, "exclude": []},
        )

        tradebot.collect_orders(show=False)

        orders = _load_orderlist(tradebot_env)
        if orders:
            # remaining buy budget = 0.0002 * 0.95 = 0.00019
            assert orders[0]["total"] <= 0.0002
