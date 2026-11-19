"""Tests for api_compat helpers used by tradebot."""

import json

import pytest

from api_compat import (
    MIN_ORDER_BTC,
    OperationCancelled,
    auth_error_help,
    balances_dict_from_ccxt,
    currency_is_tradable,
    is_insufficient_balance_error,
    is_ip_whitelist_error,
    is_valid_trading_symbol,
    load_btc_available,
    order_side_for_ccxt,
    order_type_for_ccxt,
    parse_poloniex_error,
)


class TestBalancesDict:
    def test_balances_dict_from_ccxt_extracts_free_amounts(self):
        raw = {
            "BTC": {"free": 0.5, "used": 0.1, "total": 0.6},
            "ETH": {"free": 1.25, "used": 0, "total": 1.25},
            "info": {},
            "free": {},
        }
        result = balances_dict_from_ccxt(raw)
        assert result["BTC"] == ["0.5"]
        assert result["ETH"] == ["1.25"]
        assert "info" not in result


class TestSymbolValidation:
    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("ADA", True),
            ("ETH", True),
            ("BTC123", True),
            ("bad/coin", False),
            ("", False),
            ("COIN WITH SPACE", False),
        ],
    )
    def test_is_valid_trading_symbol(self, symbol, expected):
        assert is_valid_trading_symbol(symbol) is expected


class TestCurrencyTradable:
    def test_currency_is_tradable_active_coin(self):
        assert currency_is_tradable({"active": True, "info": {"tradeEnable": True}}) is True

    def test_currency_is_tradable_delisted(self):
        assert currency_is_tradable({"active": True, "info": {"delisted": True}}) is False

    def test_currency_is_tradable_trade_disabled(self):
        assert currency_is_tradable({"active": True, "info": {"tradeEnable": False}}) is False


class TestOrderMapping:
    def test_order_side_for_ccxt_lowercases(self):
        assert order_side_for_ccxt("BUY") == "buy"
        assert order_side_for_ccxt("SELL") == "sell"

    def test_order_type_for_ccxt_lowercases(self):
        assert order_type_for_ccxt("LIMIT") == "limit"


class TestPoloniexErrors:
    def test_parse_poloniex_error_extracts_json(self):
        exc = Exception('poloniex {"code": 21721, "message": "Insufficient balance."}')
        body = parse_poloniex_error(exc)
        assert body["code"] == 21721

    def test_is_insufficient_balance_error_by_code(self):
        exc = Exception('{"code": 21721, "message": "Insufficient balance."}')
        assert is_insufficient_balance_error(exc) is True

    def test_is_ip_whitelist_error(self):
        exc = Exception('{"code": 401, "message": "Illegal of ip"}')
        assert is_ip_whitelist_error(exc) is True

    def test_auth_error_help_mentions_ip_whitelist(self):
        exc = Exception('{"code": 401, "message": "Illegal of ip"}')
        help_text = auth_error_help(exc)
        assert "401" in help_text or "whitelist" in help_text.lower()


class TestLoadBtcAvailable:
    def test_load_btc_available_reads_json(self, tmp_path):
        path = tmp_path / "balances.json"
        path.write_text(json.dumps({"BTC": ["0.01234567"]}), encoding="utf-8")
        assert load_btc_available(str(path)) == pytest.approx(0.01234567)

    def test_load_btc_available_missing_file_returns_zero(self, tmp_path):
        assert load_btc_available(str(tmp_path / "missing.json")) == 0.0


class TestOperationCancelled:
    def test_operation_cancelled_is_exception(self):
        with pytest.raises(OperationCancelled):
            raise OperationCancelled("stop")

    def test_min_order_btc_constant(self):
        assert MIN_ORDER_BTC == 0.0001
