"""Tests for tradebot.advice() and tradebot.total_balance()."""

import json

import pytest

import tradebot
from tests.conftest import seed_market_files


class TestAdvice:
    def test_advice_computes_eighty_percent_per_market(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA", "ETH", "XRP"],
            config={
                "time": "",
                "budget": 0.0005,
                "balance": "0.00300000",
                "advice": 0.0,
                "exclude": [],
            },
        )

        result = tradebot.advice(show=False)

        assert result["markets"] == 3
        assert result["balance"] == 0.003
        assert result["advice"] == round(0.003 * 0.8 / 3, 6)
        assert result["budget"] == 0.0005

        saved = json.loads((tradebot_env / "config.json").read_text(encoding="utf-8"))
        assert saved["advice"] == result["advice"]

    def test_advice_uses_active_markets_only(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA", "ETH", "XRP", "DOGE"],
            config={
                "time": "",
                "budget": 0.0005,
                "balance": "0.00400000",
                "advice": 0.0,
                "exclude": ["DOGE", "XRP"],
            },
        )

        result = tradebot.advice(show=False)

        assert result["markets"] == 2
        assert result["markets_total"] == 4
        assert result["advice"] == round(0.004 * 0.8 / 2, 6)

    def test_advice_handles_empty_market_list(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=[],
            config={
                "time": "",
                "budget": 0.0001,
                "balance": "0.00100000",
                "advice": 0.0,
                "exclude": [],
            },
        )

        result = tradebot.advice(show=False)

        assert result["markets"] == 0
        assert result["markets_total"] == 0
        assert result["advice"] == round(0.001 * 0.8 / 1, 6)


class TestApplyDefaultMarketExcludes:
    def test_apply_default_market_excludes_unheld_pairs(self, tradebot_env):
        coins = [f"C{i:02d}" for i in range(45)] + ["ADA", "ETH"]
        balances = {"BTC": ["0.1"], "ADA": ["100.0"], "ETH": ["1.0"]}
        for coin in coins:
            balances.setdefault(coin, ["0"])
        tickers = {f"{coin}/BTC": {"last": "0.00001"} for coin in coins}
        seed_market_files(
            tradebot_env,
            coins=coins,
            balances=balances,
            tickers=tickers,
            config={
                "time": "",
                "budget": 0.0008,
                "balance": "0.1",
                "advice": 0.0,
                "exclude": [],
            },
        )

        tradebot.apply_default_market_excludes(coins, "BTC")

        saved = json.loads((tradebot_env / "config.json").read_text(encoding="utf-8"))
        assert len(saved["exclude"]) == 45
        assert "ADA_BTC" not in saved["exclude"]
        assert "ETH_BTC" not in saved["exclude"]


class TestTotalBalance:
    def test_total_balance_sums_btc_and_alt_holdings(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={
                "BTC": ["0.01000000"],
                "ADA": ["1000.0"],
            },
            tickers={"ADA/BTC": {"last": "0.00001000"}},
            config={
                "time": "",
                "budget": 0.0008,
                "balance": "0",
                "advice": 0.0,
                "exclude": [],
            },
        )

        tradebot.total_balance(show=False)

        saved = json.loads((tradebot_env / "config.json").read_text(encoding="utf-8"))
        # 0.01 BTC + 1000 * 0.00001 = 0.01 + 0.01 = 0.02
        assert float(saved["balance"]) == pytest.approx(0.02, rel=1e-6)

    def test_total_balance_btc_only_when_no_alts(self, tradebot_env):
        seed_market_files(
            tradebot_env,
            coins=["ADA"],
            balances={"BTC": ["0.00500000"]},
            tickers={"ADA/BTC": {"last": "0.00001000"}},
        )

        tradebot.total_balance(show=False)

        saved = json.loads((tradebot_env / "config.json").read_text(encoding="utf-8"))
        assert float(saved["balance"]) == pytest.approx(0.005, rel=1e-8)
