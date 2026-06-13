"""Additional quote_config tests for file I/O and portfolio paths."""

import pytest

from tests.conftest import write_json


class TestLoadPairCoins:
    def test_load_pair_coins_reads_file(self, tmp_path):
        from quote_config import load_pair_coins

        (tmp_path / "json").mkdir(parents=True)
        (tmp_path / "json" / "poloniex_btc_pairs.txt").write_text(
            "ADA\nETH\n", encoding="utf-8"
        )
        assert load_pair_coins(tmp_path, "BTC") == ["ADA", "ETH"]

    def test_load_pair_coins_usdt_filename(self, tmp_path):
        from quote_config import load_pair_coins

        (tmp_path / "json").mkdir(parents=True)
        (tmp_path / "json" / "poloniex_usdt_pairs.txt").write_text("DOGE\n", encoding="utf-8")
        assert load_pair_coins(tmp_path, "USDT") == ["DOGE"]

    def test_load_pair_coins_missing_returns_empty(self, tmp_path):
        from quote_config import load_pair_coins

        assert load_pair_coins(tmp_path, "BTC") == []


class TestLoadQuoteAvailable:
    def test_reads_quote_balance(self, tmp_path):
        from quote_config import load_quote_available

        write_json(
            tmp_path / "json" / "poloniex_balances.json",
            {"BTC": ["0.015"], "USDT": ["42.5"]},
        )
        path = str(tmp_path / "json" / "poloniex_balances.json")
        assert load_quote_available(path, "BTC") == pytest.approx(0.015)
        assert load_quote_available(path, "USDT") == pytest.approx(42.5)

    def test_missing_file_returns_zero(self, tmp_path):
        from quote_config import load_quote_available

        path = str(tmp_path / "json" / "missing.json")
        assert load_quote_available(path, "BTC") == 0.0


class TestPortfolioInQuote:
    def test_includes_btc_holdings_when_quote_is_usdt(self):
        from quote_config import portfolio_in_quote

        balances = {"USDT": ["10"], "BTC": ["0.01"], "ADA": ["0"]}
        tickers = {"BTC/USDT": {"last": "50000"}, "ADA/USDT": {"last": "0.5"}}
        total = portfolio_in_quote(balances, tickers, ["ADA"], "USDT")
        assert total == pytest.approx(10 + 0.01 * 50000)


class TestActivePairCoins:
    def test_active_pair_coins_respects_exclude(self, tmp_path):
        from quote_config import active_pair_coins

        (tmp_path / "json").mkdir(parents=True)
        (tmp_path / "json" / "poloniex_btc_pairs.txt").write_text(
            "ADA\nETH\nDOGE\n", encoding="utf-8"
        )
        assert active_pair_coins(tmp_path, "BTC", exclude=["DOGE"]) == ["ADA", "ETH"]


class TestSuggestExcludes:
    def test_suggest_excludes_for_unheld(self):
        from quote_config import suggest_excludes_for_unheld

        coins = ["ADA", "ETH", "DOGE"]
        balances = {"BTC": ["0.1"], "ADA": ["100"], "ETH": ["0"], "DOGE": ["0"]}
        tickers = {
            "ADA/BTC": {"last": "0.00001"},
            "ETH/BTC": {"last": "0.05"},
            "DOGE/BTC": {"last": "0.000001"},
        }
        assert suggest_excludes_for_unheld(coins, balances, tickers, "BTC") == ["DOGE", "ETH"]
