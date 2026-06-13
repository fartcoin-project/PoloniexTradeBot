"""Tests for tradebot.order_list() preview and live placement."""

import json
from datetime import datetime, timedelta

import ccxt
import pytest

import tradebot
from tests.conftest import seed_market_files, write_json


def _seed_orderlist(root, orders):
    write_json(root / "json" / "orderlist.json", orders)


def _sample_order(*, side="SELL", alt="ADA", total=0.001, time=None):
    return {
        "symbol": f"{alt}/BTC",
        "type": "LIMIT",
        "side": side,
        "alt_amount": 100.0,
        "quantity": 100.0,
        "price": 0.00001,
        "total": total,
        "alt": alt,
        "time": time or tradebot.get_time(time_list=True),
    }


def _stale_time():
    return (datetime.now() - timedelta(seconds=400)).strftime("%Y %m %d %H %M %S")


@pytest.fixture
def order_list_env(tradebot_env, monkeypatch):
    tradebot.set_interactive_menu(False)
    monkeypatch.setattr(tradebot, "menu", lambda: None)
    monkeypatch.setattr(tradebot, "completed", lambda: None)
    seed_market_files(
        tradebot_env,
        coins=["ADA"],
        balances={"BTC": ["0.01000000"], "ADA": ["200000.0"]},
    )
    return tradebot_env


class TestOrderList:
    def test_preview_does_not_call_exchange(self, order_list_env, mock_polo):
        _seed_orderlist(order_list_env, [_sample_order(side="SELL")])

        tradebot.order_list(place=False)

        mock_polo.create_order.assert_not_called()

    def test_place_sell_calls_create_order_once(self, order_list_env, mock_polo):
        _seed_orderlist(order_list_env, [_sample_order(side="SELL")])

        tradebot.order_list(place=True)

        mock_polo.create_order.assert_called_once()
        args = mock_polo.create_order.call_args[0]
        assert args[0] == "ADA/BTC"
        assert args[2] == "sell"

    def test_place_buy_places_order_when_quote_available(self, order_list_env, mock_polo):
        _seed_orderlist(
            order_list_env,
            [_sample_order(side="BUY", alt="ETH", total=0.001)],
        )

        tradebot.order_list(place=True)

        mock_polo.create_order.assert_called_once()
        args = mock_polo.create_order.call_args[0]
        assert args[2] == "buy"

    def test_place_buy_skips_when_insufficient_quote(self, order_list_env, mock_polo):
        write_json(
            order_list_env / "json" / "poloniex_balances.json",
            {"BTC": ["0.001"], "ADA": ["0"]},
        )
        _seed_orderlist(
            order_list_env,
            [_sample_order(side="BUY", alt="ETH", total=0.005)],
        )

        tradebot.order_list(place=True)

        mock_polo.create_order.assert_not_called()
        incomplete = json.loads(
            (order_list_env / "json" / "orderlist_incomplete.json").read_text(encoding="utf-8")
        )
        assert len(incomplete) == 1
        assert incomplete[0]["side"] == "BUY"

    def test_stale_order_list_skips_api_calls(self, order_list_env, mock_polo):
        _seed_orderlist(
            order_list_env,
            [_sample_order(side="SELL", time=_stale_time())],
        )

        tradebot.order_list(place=True)

        mock_polo.create_order.assert_not_called()

    def test_network_error_on_create_order_records_incomplete(self, order_list_env, mock_polo):
        mock_polo.create_order.side_effect = ccxt.NetworkError("timeout")
        _seed_orderlist(order_list_env, [_sample_order(side="SELL")])

        tradebot.order_list(place=True)

        incomplete = json.loads(
            (order_list_env / "json" / "orderlist_incomplete.json").read_text(encoding="utf-8")
        )
        assert len(incomplete) == 1

    def test_non_interactive_runs_single_pass(self, order_list_env, mock_polo):
        _seed_orderlist(order_list_env, [_sample_order(side="SELL")])

        tradebot.order_list(place=True)

        assert mock_polo.create_order.call_count == 1

    def test_empty_orderlist_does_not_crash(self, order_list_env, capsys):
        _seed_orderlist(order_list_env, [])

        tradebot.order_list(place=False)

        out = capsys.readouterr().out
        assert "Order list is empty" in out

