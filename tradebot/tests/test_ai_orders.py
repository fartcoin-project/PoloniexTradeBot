"""Tests for AI order JSON parsing and guards."""

import pytest

from ai_orders import extract_json_object, orders_from_ai_text, validate_and_normalize_orders


CFG = {
    "budget": 10.0,
    "balance": "50",
    "markets": ["USDT"],
    "quote_currency": "USDT",
    "trade_mode": "both",
    "exclude": ["SCAM", "SCAM_USDT"],
}


def test_extract_json_from_fence():
    text = 'Here:\n```json\n{"orders":[{"symbol":"ADA/USDT","side":"BUY"}]}\n```'
    data = extract_json_object(text)
    assert data["orders"][0]["symbol"] == "ADA/USDT"


def test_validate_drops_excluded_and_wrong_quote():
    payload = {
        "orders": [
            {"symbol": "ADA/USDT", "side": "BUY", "type": "LIMIT", "quantity": 10, "price": 0.5},
            {"symbol": "SCAM/USDT", "side": "BUY", "type": "LIMIT", "quantity": 1, "price": 1},
            {"symbol": "ADA/BTC", "side": "BUY", "type": "LIMIT", "quantity": 1, "price": 0.001},
        ]
    }
    orders, warnings = validate_and_normalize_orders(payload, CFG, available_quote=10)
    assert len(orders) == 1
    assert orders[0]["symbol"] == "ADA/USDT"
    assert orders[0]["side"] == "BUY"
    assert any("excluded" in w.lower() for w in warnings)
    assert any("quote" in w.lower() for w in warnings)


def test_validate_respects_trade_mode_buy_only():
    cfg = dict(CFG, trade_mode="buy")
    payload = {
        "orders": [
            {"symbol": "ADA/USDT", "side": "SELL", "quantity": 1, "price": 1},
            {"symbol": "DOGE/USDT", "side": "BUY", "quantity": 2, "price": 0.1},
        ]
    }
    orders, warnings = validate_and_normalize_orders(payload, cfg, available_quote=10)
    assert len(orders) == 1
    assert orders[0]["side"] == "BUY"
    assert any("trade_mode=buy" in w for w in warnings)


def test_validate_caps_buy_budget():
    payload = {
        "orders": [
            {"symbol": "ADA/USDT", "side": "BUY", "quantity": 100, "price": 1.0},
        ]
    }
    orders, warnings = validate_and_normalize_orders(payload, CFG, available_quote=10)
    assert orders == []
    assert any("exceed" in w.lower() for w in warnings)


def test_orders_from_ai_text_roundtrip():
    text = (
        '{"orders":[{"symbol":"ADA/USDT","side":"BUY","type":"LIMIT",'
        '"quantity":5,"price":0.4,"alt":"ADA"}]}'
    )
    orders, warnings = orders_from_ai_text(text, CFG, available_quote=10)
    assert len(orders) == 1
    assert orders[0]["quantity"] == 5
    assert orders[0]["total"] == pytest.approx(2.0)
    assert warnings == []
