"""Tests for budget_helpers used by collect_orders."""

import json

import pytest

from api_compat import MIN_ORDER_BTC
from budget_helpers import (
    SLIDER_SCALE,
    btc_to_slider,
    coin_budget_from_config,
    format_budget_multiplier,
    multiplier_step_to_value,
    normalize_coin_budgets,
    slider_to_btc,
    value_to_multiplier_step,
)
from tests.conftest import write_json


class TestCoinBudgetFromConfig:
    def test_uses_global_budget_by_default(self):
        config = {"budget": 0.0008}
        assert coin_budget_from_config(config, "ADA") == 0.0008

    def test_uses_override_when_present(self):
        config = {"budget": 0.0008, "coin_budgets": {"ETH": 0.0012}}
        assert coin_budget_from_config(config, "ETH") == 0.0012

    def test_allows_zero_budget(self):
        config = {"budget": 0}
        assert coin_budget_from_config(config, "ADA") == 0.0

    def test_allows_budget_below_exchange_minimum(self):
        config = {"budget": 0.00001}
        assert coin_budget_from_config(config, "ADA") == 0.00001

    def test_missing_budget_falls_back_to_min_order(self):
        assert coin_budget_from_config({}, "ADA") == MIN_ORDER_BTC


class TestNormalizeCoinBudgets:
    def test_non_custom_coins_follow_global(self):
        config = {"budget": 0.0008, "coin_budgets": {"ETH": 0.002}, "coin_budget_custom": ["ETH"]}
        result = normalize_coin_budgets(config, coins=["ADA", "ETH"])
        assert result["ADA"] == 0.0008
        assert result["ETH"] == 0.002

    def test_custom_without_override_still_uses_global(self):
        config = {"budget": 0.0008, "coin_budgets": {}, "coin_budget_custom": ["ETH"]}
        result = normalize_coin_budgets(config, coins=["ETH"])
        assert result["ETH"] == 0.0008


class TestMultiplierSteps:
    def test_step_to_value_uses_base(self):
        assert multiplier_step_to_value(2, 0.001, 0.0001) == pytest.approx(0.001)

    def test_value_to_nearest_step(self):
        assert value_to_multiplier_step(0.002, 0.001, 0.0001) == 4  # ×2

    def test_format_multiplier(self):
        assert format_budget_multiplier(0) == "×0.3"
        assert format_budget_multiplier(2) == "×1"


class TestSliderConversion:
    def test_slider_round_trip(self):
        value = 0.00081234
        assert slider_to_btc(btc_to_slider(value)) == pytest.approx(value, rel=1e-6)

    def test_slider_scale(self):
        assert SLIDER_SCALE == 100_000_000
