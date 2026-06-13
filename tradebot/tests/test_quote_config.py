"""Tests for quote currency helpers."""

from quote_config import (
    ccxt_symbol,
    filter_live_markets,
    format_quote_value,
    market_id,
    markets_from_config,
    min_order_for_quote,
    normalize_quote,
    pairs_filename,
    portfolio_in_quote,
    quote_from_config,
)


def test_normalize_quote():
    assert normalize_quote("btc") == "BTC"
    assert normalize_quote("USD") == "USDT"
    assert normalize_quote("usdc") == "USDC"
    assert normalize_quote("INVALID") == "BTC"


def test_min_order_for_quote():
    assert min_order_for_quote("BTC") == 0.0001
    assert min_order_for_quote("USDT") == 1.0
    assert min_order_for_quote("USDC") == 1.0


def test_symbols_and_files():
    assert ccxt_symbol("ADA", "USDT") == "ADA/USDT"
    assert market_id("ETH", "USDC") == "ETH_USDC"
    assert pairs_filename("BTC") == "poloniex_btc_pairs.txt"
    assert pairs_filename("USDT") == "poloniex_usdt_pairs.txt"


def test_format_quote_value():
    assert format_quote_value("BTC", 0.00012345).startswith("₿")
    assert "USDT" in format_quote_value("USDT", 12.5)


def test_quote_from_config():
    assert quote_from_config({"quote_currency": "USDT"}) == "USDT"
    assert markets_from_config({"markets": ["USDT", "BTC"]}) == ["BTC", "USDT"]
    assert markets_from_config({"quote_currency": "USDT"}) == ["USDT"]
    assert quote_from_config({}) == "BTC"


def test_filter_live_markets():
    live = ["ADA_BTC", "ETH_BTC", "ADA_USDT", "ETH_USDT"]
    assert filter_live_markets(live, "USDT") == ["ADA_USDT", "ETH_USDT"]


def test_portfolio_in_quote_usdt():
    balances = {"USDT": ["100"], "ADA": ["1000"], "BTC": ["0.01"]}
    tickers = {
        "ADA/USDT": {"last": "0.50"},
        "BTC/USDT": {"last": "60000"},
    }
    total = portfolio_in_quote(balances, tickers, ["ADA"], "USDT")
    assert total == 100 + 1000 * 0.50 + 0.01 * 60000
