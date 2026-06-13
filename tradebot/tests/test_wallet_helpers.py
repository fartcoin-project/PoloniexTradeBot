"""Tests for wallet helpers used in budget rows."""

from gui.data_store import holding_value_in_quote, holdings_map_for_quote


def test_holding_value_in_quote_btc():
    holding = {"coin": "ADA", "amount": 100.0, "btc_value": 0.001, "usd_value": 50.0}
    assert holding_value_in_quote(holding, "BTC") == 0.001


def test_holding_value_in_quote_usdt_stablecoin():
    holding = {"coin": "USDT", "amount": 25.5, "btc_value": 0.0, "usd_value": 25.5}
    assert holding_value_in_quote(holding, "USDT") == 25.5


def test_holdings_map_for_quote():
    wallet = {
        "holdings": [
            {"coin": "BTC", "amount": 0.01, "btc_value": 0.01, "usd_value": 600.0},
            {"coin": "ADA", "amount": 100.0, "btc_value": 0.001, "usd_value": 50.0},
        ]
    }
    mapped = holdings_map_for_quote(wallet, "BTC")
    assert mapped["ADA"]["amount"] == 100.0
    assert mapped["ADA"]["quote_value"] == 0.001
