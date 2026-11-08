"""BotService AI actions with mocked Colibri."""

import json
import queue

import pytest

from gui.service import BotService
from tests.conftest import write_json


def _patch_llm(monkeypatch, content, thinking="reason"):
    def fake_chat(*args, **kwargs):
        return {"content": content, "thinking": thinking, "model": "test", "raw": {}}

    monkeypatch.setattr("gui.service.chat_completions", fake_chat)
    monkeypatch.setattr(
        "gui.service.health_check",
        lambda *a, **k: {"ok": True, "detail": "ok", "models": ["test"]},
    )


def test_save_config_persists_llm(tradebot_env, monkeypatch):
    monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
    svc = BotService(queue.Queue())
    svc.save_config(
        budget=5.0,
        exclude=[],
        markets=["USDT"],
        llm={
            "enabled": True,
            "base_url": "http://127.0.0.1:8000",
            "auto_place": True,
            "loop_enabled": False,
            "status_reports_enabled": False,
            "model": "glm",
        },
    )
    cfg = svc.load_config()
    assert cfg["llm"]["base_url"].endswith("/v1")
    assert cfg["llm"]["auto_place"] is True
    assert cfg["llm"]["model"] == "glm"
    assert cfg["llm"]["status_reports_enabled"] is False


def test_ai_propose_orders_writes_orderlist(tradebot_env, monkeypatch):
    monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
    monkeypatch.chdir(tradebot_env)
    write_json(
        tradebot_env / "config.json",
        {
            "budget": 10.0,
            "balance": "100",
            "markets": ["USDT"],
            "quote_currency": "USDT",
            "trade_mode": "both",
            "exclude": [],
            "llm": {"enabled": True, "model": "test", "auto_place": False},
        },
    )
    payload = {
        "orders": [
            {
                "symbol": "ADA/USDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": 5,
                "price": 0.5,
                "alt": "ADA",
            }
        ]
    }
    _patch_llm(monkeypatch, json.dumps(payload))
    svc = BotService(queue.Queue())
    assert svc.run_sync("ai_propose_orders") is True
    orders = json.loads((tradebot_env / "json" / "orderlist.json").read_text(encoding="utf-8"))
    assert len(orders) == 1
    assert orders[0]["symbol"] == "ADA/USDT"


def test_ai_rebalance_respects_auto_place_off(tradebot_env, monkeypatch):
    monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
    monkeypatch.chdir(tradebot_env)
    write_json(
        tradebot_env / "config.json",
        {
            "budget": 10.0,
            "balance": "100",
            "markets": ["USDT"],
            "quote_currency": "USDT",
            "trade_mode": "both",
            "exclude": [],
            "llm": {"enabled": True, "model": "test", "auto_place": False},
        },
    )
    placed = {"n": 0}

    def fake_chat(messages, **kwargs):
        # propose path needs JSON; analyze gets prose
        user = messages[-1]["content"]
        if "JSON" in messages[0]["content"] or "orderlijst" in user.lower() or "Maak een orderlijst" in user:
            return {
                "content": json.dumps({
                    "orders": [{
                        "symbol": "ADA/USDT",
                        "side": "BUY",
                        "quantity": 1,
                        "price": 1.0,
                    }]
                }),
                "thinking": "",
                "model": "test",
                "raw": {},
            }
        return {"content": "Analyse ok", "thinking": "t", "model": "test", "raw": {}}

    monkeypatch.setattr("gui.service.chat_completions", fake_chat)
    svc = BotService(queue.Queue())
    svc._ensure_loaded()
    monkeypatch.setattr(svc._tb, "get_update", lambda show=False: None)
    monkeypatch.setattr(svc._tb, "market_list", lambda: None)
    monkeypatch.setattr(svc._tb, "advice", lambda show=False: None)

    def place(**kwargs):
        placed["n"] += 1

    monkeypatch.setattr(svc._tb, "order_list", place)
    assert svc.run_sync("ai_rebalance_cycle") is True
    assert placed["n"] == 0
    assert (tradebot_env / "json" / "orderlist.json").exists()


def test_ai_rebalance_auto_place_on(tradebot_env, monkeypatch):
    monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
    monkeypatch.chdir(tradebot_env)
    write_json(
        tradebot_env / "config.json",
        {
            "budget": 10.0,
            "balance": "100",
            "markets": ["USDT"],
            "quote_currency": "USDT",
            "trade_mode": "both",
            "exclude": [],
            "llm": {"enabled": True, "model": "test", "auto_place": True},
        },
    )
    placed = {"n": 0}

    def fake_chat(messages, **kwargs):
        sys_content = messages[0]["content"]
        if "JSON" in sys_content or "orders" in sys_content.lower():
            return {
                "content": json.dumps({
                    "orders": [{
                        "symbol": "ADA/USDT",
                        "side": "BUY",
                        "quantity": 1,
                        "price": 1.0,
                    }]
                }),
                "thinking": "",
                "model": "test",
                "raw": {},
            }
        return {"content": "Analyse", "thinking": "", "model": "test", "raw": {}}

    monkeypatch.setattr("gui.service.chat_completions", fake_chat)
    svc = BotService(queue.Queue())
    svc._ensure_loaded()
    monkeypatch.setattr(svc._tb, "get_update", lambda show=False: None)
    monkeypatch.setattr(svc._tb, "market_list", lambda: None)
    monkeypatch.setattr(svc._tb, "advice", lambda show=False: None)

    def place(place=False):
        if place:
            placed["n"] += 1

    monkeypatch.setattr(svc._tb, "order_list", place)
    assert svc.run_sync("ai_rebalance_cycle") is True
    assert placed["n"] == 1


def test_ai_status_report_emits_chat(tradebot_env, monkeypatch):
    monkeypatch.setattr("gui.service.BOT_DIR", str(tradebot_env))
    monkeypatch.chdir(tradebot_env)
    write_json(
        tradebot_env / "config.json",
        {
            "budget": 5.0,
            "markets": ["USDT"],
            "llm": {
                "enabled": True,
                "model": "test",
                "status_reports_enabled": True,
            },
        },
    )
    _patch_llm(monkeypatch, "Alles stabiel op Poloniex.")
    log_queue = queue.Queue()
    svc = BotService(log_queue)
    # Rebind AI store to env
    from ai_status import AiMessageStore

    svc._ai_store = AiMessageStore(str(tradebot_env))
    assert svc.run_sync("ai_status_report") is True
    found = False
    while not log_queue.empty():
        tag, payload = log_queue.get_nowait()
        if tag == "chat" and payload.get("type") == "status":
            found = True
            assert "stabiel" in payload["content"]
    assert found
