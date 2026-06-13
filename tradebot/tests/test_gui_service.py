"""Tests for BotService orchestration (no Qt)."""

import io
import queue

import pytest

import tradebot
from gui.service import BotService
from tests.conftest import write_json


class TestBotService:
    def test_preview_orders_requires_orderlist(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        svc = BotService(queue.Queue())
        actions = svc._actions()
        with pytest.raises(FileNotFoundError, match="Build Orders"):
            actions["preview_orders"]()

    def test_save_config_rejects_budget_below_minimum(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        svc = BotService(queue.Queue())
        with pytest.raises(ValueError, match="Budget must be at least"):
            svc.save_config(budget=0.00001, exclude=[])

    def test_save_config_persists_quote_and_exclude(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        svc = BotService(queue.Queue())
        svc.save_config(
            budget=5.0,
            exclude=[" ada ", ""],
            markets=["USDT"],
            sell_mode="sell",
        )
        cfg = svc.load_config()
        assert cfg["quote_currency"] == "USDT"
        assert cfg["markets"] == ["USDT"]
        assert cfg["exclude"] == ["ADA"]
        assert cfg["trade_mode"] == "sell"
        assert svc._tb.args.sell is True

    def test_run_sync_start_bot(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        monkeypatch.chdir(tradebot_env)
        from tests.conftest import seed_market_files

        seed_market_files(tradebot_env, coins=["ADA"])
        log_queue = queue.Queue()
        svc = BotService(log_queue)
        svc._ensure_loaded()
        svc._tb.get_update = lambda show=False: None
        svc._tb.market_list = lambda: None
        svc._tb.collect_orders = lambda show=False: None
        svc._tb.order_list = lambda place=False: None
        assert svc.run_sync("start_bot") is True

    def test_safe_advice_stats_uses_quote_pair_file(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        monkeypatch.chdir(tradebot_env)
        write_json(
            tradebot_env / "config.json",
            {
                "quote_currency": "USDT",
                "budget": 5.0,
                "balance": "100.0",
                "advice": 0.0,
                "exclude": [],
            },
        )
        (tradebot_env / "json" / "poloniex_usdt_pairs.txt").write_text("DOGE\n", encoding="utf-8")
        write_json(
            tradebot_env / "json" / "poloniex_balances.json",
            {"USDT": ["100"], "DOGE": ["0"]},
        )
        write_json(
            tradebot_env / "json" / "poloniex_tickers.json",
            {"DOGE/USDT": {"last": "0.1"}},
        )

        svc = BotService(queue.Queue())
        svc._ensure_loaded()
        monkeypatch.chdir(tradebot_env)
        svc._tb.args.log = False
        stats = svc._safe_advice_stats()

        assert stats is not None
        assert stats["quote_currency"] == "USDT"
        assert stats["markets"] == 1

    def test_safe_advice_stats_none_without_quote_pairs_file(self, tradebot_env, monkeypatch):
        monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
        monkeypatch.chdir(tradebot_env)
        write_json(
            tradebot_env / "config.json",
            {
                "quote_currency": "USDT",
                "budget": 5.0,
                "balance": "100.0",
                "advice": 0.0,
                "exclude": [],
            },
        )
        (tradebot_env / "json" / "poloniex_btc_pairs.txt").write_text("ADA\n", encoding="utf-8")

        svc = BotService(queue.Queue())
        svc._ensure_loaded()
        monkeypatch.chdir(tradebot_env)
        svc._tb.args.log = False

        assert svc._safe_advice_stats() is None


class TestGuiProgressBar:
    def test_subclass_call_without_extra_self(self):
        out = io.StringIO()

        class GuiProgressBar(tradebot.ProgressBar):
            def __call__(self):
                super().__call__()
                print("extra", file=out)

        bar = GuiProgressBar(10, output=out)
        bar.current = 4
        bar()  # must not raise TypeError
        assert "extra" in out.getvalue()
        assert "40%" in out.getvalue()
