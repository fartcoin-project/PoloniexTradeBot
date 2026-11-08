"""Tests for Colibri OpenAI-compatible client (httpx mocked)."""

import json

import httpx
import pytest

import llm_client


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or json.dumps(self._payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "http://x"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, routes):
        self.routes = routes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, headers=None):
        for prefix, resp in self.routes:
            if url.startswith(prefix) or prefix in url:
                return resp
        return _FakeResponse(404, {"error": "missing"})

    def post(self, url, headers=None, json=None):
        for prefix, resp in self.routes:
            if url.startswith(prefix) or prefix in url:
                return resp
        return _FakeResponse(404, {"error": "missing"})


def test_list_models(monkeypatch):
    routes = [
        (
            "/models",
            _FakeResponse(200, {"data": [{"id": "glm-test"}, {"id": "other"}]}),
        )
    ]
    monkeypatch.setattr(llm_client.httpx, "Client", lambda timeout=None: _FakeClient(routes))
    models = llm_client.list_models("http://127.0.0.1:8000/v1", "local")
    assert models == ["glm-test", "other"]


def test_chat_completions_extracts_thinking(monkeypatch):
    routes = [
        (
            "/chat/completions",
            _FakeResponse(
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Alles rustig.",
                                "reasoning_content": "Denk…",
                            }
                        }
                    ]
                },
            ),
        )
    ]
    monkeypatch.setattr(llm_client.httpx, "Client", lambda timeout=None: _FakeClient(routes))
    out = llm_client.chat_completions(
        [{"role": "user", "content": "hi"}],
        base_url="http://127.0.0.1:8000/v1",
        model="glm-test",
        enable_thinking=True,
    )
    assert out["content"] == "Alles rustig."
    assert out["thinking"] == "Denk…"
    assert out["model"] == "glm-test"


def test_resolve_model_uses_first(monkeypatch):
    monkeypatch.setattr(llm_client, "list_models", lambda *a, **k: ["m1", "m2"])
    assert llm_client.resolve_model({"base_url": "http://x/v1", "model": ""}) == "m1"


def test_health_check_ok(monkeypatch):
    routes = [
        ("/health", _FakeResponse(200, {"ok": True})),
        ("/models", _FakeResponse(200, {"data": [{"id": "m1"}]})),
    ]
    monkeypatch.setattr(llm_client.httpx, "Client", lambda timeout=None: _FakeClient(routes))
    result = llm_client.health_check("http://127.0.0.1:8000/v1")
    assert result["ok"] is True
    assert result["models"] == ["m1"]


def test_build_portfolio_context_shapes():
    snap = llm_client.build_portfolio_context(
        config={
            "budget": 10,
            "balance": "100",
            "exclude": ["AAA"],
            "trade_mode": "both",
            "llm": {"auto_place": False},
        },
        wallet={"total_usd": 100, "holdings": [{"coin": "USDT", "amount": 100}]},
        orderlist=[{"symbol": "ADA/USDT", "side": "BUY", "quantity": 1, "price": 0.5}],
    )
    assert snap["budget"] == 10
    assert snap["holdings"][0]["coin"] == "USDT"
    assert snap["proposed_orders"][0]["symbol"] == "ADA/USDT"


def test_messages_for_status_include_thinking_instruction():
    msgs = llm_client.messages_for_status({"budget": 1}, trigger="heartbeat")
    assert msgs[0]["role"] == "system"
    assert "Denk" in msgs[1]["content"] or "denk" in msgs[1]["content"].lower()
