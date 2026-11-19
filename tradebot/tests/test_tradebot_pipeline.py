"""Tests for get_update(), market_list(), and start_bot() with mocked ccxt."""

import json

import ccxt
import pytest

import tradebot
from tests.conftest import seed_ccxt_fetch_mocks, seed_market_files, write_json


class TestGetUpdate:
    def test_get_update_writes_market_and_balance_files(self, tradebot_env, mock_polo):
        seed_ccxt_fetch_mocks(mock_polo)

        tradebot.get_update(show=False)

        assert (tradebot_env / "json" / "poloniex_markets.json").is_file()
        assert (tradebot_env / "json" / "poloniex_currencies.json").is_file()
        assert (tradebot_env / "json" / "poloniex_balances.json").is_file()
        assert (tradebot_env / "json" / "poloniex_tickers.json").is_file()
        mock_polo.fetch_markets.assert_called_once()
        mock_polo.fetch_balance.assert_called_once()

    def test_get_update_uses_cached_balances_on_auth_error(self, tradebot_env, mock_polo):
        seed_ccxt_fetch_mocks(mock_polo)
        write_json(
            tradebot_env / "json" / "poloniex_balances.json",
            {"BTC": ["0.005"], "ADA": ["10"]},
        )
        mock_polo.fetch_balance.side_effect = ccxt.AuthenticationError("401")

        tradebot.get_update(show=False)

        balances = json.loads(
            (tradebot_env / "json" / "poloniex_balances.json").read_text(encoding="utf-8")
        )
        assert balances["BTC"] == ["0.005"]


class TestMarketList:
    def test_market_list_builds_btc_pair_file(self, tradebot_env, mock_polo):
        seed_ccxt_fetch_mocks(mock_polo)
        tradebot.get_update(show=False)

        tradebot.market_list()

        pairs = (tradebot_env / "json" / "poloniex_btc_pairs.txt").read_text(encoding="utf-8")
        assert "ADA" in pairs.splitlines()
        assert "ETH" in pairs.splitlines()
        listed = (tradebot_env / "json" / "poloniex_ListedCoins.txt").read_text(encoding="utf-8")
        assert "ADA" in listed.splitlines()


class TestStartBot:
    def test_start_bot_runs_pipeline_in_order(self, tradebot_env, monkeypatch):
        calls = []

        monkeypatch.setattr(tradebot, "get_update", lambda show=False: calls.append("get_update"))
        monkeypatch.setattr(tradebot, "market_list", lambda: calls.append("market_list"))
        monkeypatch.setattr(
            tradebot, "collect_orders", lambda show=False: calls.append("collect_orders")
        )
        monkeypatch.setattr(tradebot, "order_list", lambda place=False: calls.append(("order_list", place)))

        tradebot.start_bot()

        assert calls == [
            "get_update",
            "market_list",
            "collect_orders",
            ("order_list", True),
        ]

    def test_start_bot_integration_with_mocks(self, tradebot_env, mock_polo, monkeypatch):
        seed_ccxt_fetch_mocks(mock_polo)
        seed_market_files(tradebot_env, coins=["ADA"])
        placed = {"n": 0}

        def fake_order_list(place=False):
            placed["n"] += 1
            assert place is True

        monkeypatch.setattr(tradebot, "order_list", fake_order_list)
        monkeypatch.setattr(tradebot, "collect_orders", lambda show=False: write_json(
            tradebot_env / "json" / "orderlist.json",
            [],
        ))

        tradebot.start_bot()

        assert placed["n"] == 1
        mock_polo.fetch_markets.assert_called()
