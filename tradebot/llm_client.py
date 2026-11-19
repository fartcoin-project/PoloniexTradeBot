"""OpenAI-compatible HTTP client for Colibri (and similar local servers)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import httpx

from llm_config import llm_root_url, normalize_llm_config

logger = logging.getLogger(__name__)


class LlmError(RuntimeError):
    """Raised when the LLM HTTP API fails."""


def _headers(api_key: str) -> dict:
    key = (api_key or "local").strip() or "local"
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def health_check(base_url: str, api_key: str = "local", timeout: float = 5.0) -> dict:
    """Return {ok, detail, models?} after probing Colibri."""
    cfg = normalize_llm_config({"base_url": base_url, "api_key": api_key})
    root = llm_root_url(cfg["base_url"])
    try:
        with httpx.Client(timeout=timeout) as client:
            health = client.get(f"{root}/health", headers=_headers(cfg["api_key"]))
            if health.status_code < 500:
                models = list_models(cfg["base_url"], cfg["api_key"], timeout=timeout)
                return {"ok": True, "detail": "reachable", "models": models}
            return {"ok": False, "detail": f"health HTTP {health.status_code}", "models": []}
    except httpx.HTTPError as exc:
        # Fall back to /v1/models only
        try:
            models = list_models(cfg["base_url"], cfg["api_key"], timeout=timeout)
            return {"ok": True, "detail": f"models ok ({exc.__class__.__name__})", "models": models}
        except LlmError as models_exc:
            return {"ok": False, "detail": str(models_exc) or str(exc), "models": []}


def list_models(base_url: str, api_key: str = "local", timeout: float = 10.0) -> list[str]:
    cfg = normalize_llm_config({"base_url": base_url, "api_key": api_key})
    url = f"{cfg['base_url']}/models"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers=_headers(cfg["api_key"]))
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise LlmError(f"Cannot list models at {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LlmError(f"Invalid models JSON from {url}") from exc

    items = data.get("data") if isinstance(data, dict) else data
    models = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                models.append(str(item["id"]))
            elif isinstance(item, str):
                models.append(item)
    return models


def resolve_model(cfg: dict, timeout: float = 10.0) -> str:
    """Use configured model or first available from /v1/models."""
    llm = normalize_llm_config(cfg)
    if llm["model"]:
        return llm["model"]
    models = list_models(llm["base_url"], llm["api_key"], timeout=timeout)
    if not models:
        raise LlmError("No model configured and /v1/models returned empty")
    return models[0]


def _delta_text(delta: dict, *keys: str) -> str:
    for key in keys:
        val = delta.get(key)
        if isinstance(val, str) and val:
            return val
        if isinstance(val, list):
            return "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in val
            )
    return ""


def _consume_chat_stream(resp: httpx.Response, *, deadline: float, t0: float) -> dict[str, Any]:
    """Accumulate OpenAI-style SSE chat chunks into content/thinking."""
    content_parts: list[str] = []
    thinking_parts: list[str] = []
    chunk_count = 0
    first_token_s: Optional[float] = None
    for line in resp.iter_lines():
        if time.monotonic() > deadline:
            raise httpx.ReadTimeout("overall deadline exceeded", request=resp.request)
        if not line:
            continue
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        chunk_count += 1
        choices = chunk.get("choices") if isinstance(chunk, dict) else None
        if not isinstance(choices, list) or not choices:
            continue
        delta = choices[0].get("delta") or {}
        if not isinstance(delta, dict):
            continue
        content_bit = _delta_text(delta, "content")
        thinking_bit = _delta_text(delta, "reasoning_content", "thinking", "reasoning")
        if (content_bit or thinking_bit) and first_token_s is None:
            first_token_s = round(time.monotonic() - t0, 3)
        if content_bit:
            content_parts.append(content_bit)
        if thinking_bit:
            thinking_parts.append(thinking_bit)
    content = "".join(content_parts)
    thinking = "".join(thinking_parts)
    return {
        "content": content,
        "thinking": thinking,
        "first_token_s": first_token_s,
        "chunk_count": chunk_count,
        "raw": {
            "stream": True,
            "chunk_count": chunk_count,
            "choices": [
                {
                    "message": {
                        "content": content,
                        "reasoning_content": thinking,
                    }
                }
            ],
        },
    }


def chat_completions(
    messages: list[dict],
    *,
    base_url: str,
    api_key: str = "local",
    model: str = "",
    timeout: float = 300.0,
    temperature: float = 0.4,
    max_tokens: int = 2048,
    enable_thinking: bool = False,
    reasoning_effort: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict[str, Any]:
    """POST /v1/chat/completions (SSE stream). Returns {content, thinking, raw}."""
    llm = normalize_llm_config({
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    })
    use_model = llm["model"] or resolve_model(llm, timeout=min(timeout, 15.0))
    body: dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if enable_thinking:
        body["enable_thinking"] = True
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    if extra:
        body.update(extra)

    url = f"{llm['base_url']}/chat/completions"
    # Read timeout covers slow prefill / gaps between SSE chunks; overall deadline caps total.
    timeout_cfg = httpx.Timeout(connect=10.0, read=float(timeout), write=30.0, pool=10.0)
    t0 = time.monotonic()
    deadline = t0 + float(timeout)
    content = ""
    thinking = ""
    data: dict[str, Any] = {}
    try:
        with httpx.Client(timeout=timeout_cfg) as client:
            with client.stream(
                "POST", url, headers=_headers(llm["api_key"]), json=body
            ) as resp:
                resp.raise_for_status()
                parsed = _consume_chat_stream(resp, deadline=deadline, t0=t0)
                content = parsed.get("content") or ""
                thinking = parsed.get("thinking") or ""
                data = parsed.get("raw") or {}
    except httpx.HTTPError as exc:
        raise LlmError(f"chat/completions failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LlmError("Invalid chat/completions JSON") from exc

    return {
        "content": content.strip() if isinstance(content, str) else str(content),
        "thinking": thinking.strip() if isinstance(thinking, str) else str(thinking),
        "model": use_model,
        "raw": data,
    }


def build_portfolio_context(
    *,
    config: dict,
    wallet: Optional[dict] = None,
    orderlist: Optional[list] = None,
    last_cycle: Optional[dict] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Compact JSON-serializable snapshot for prompts."""
    llm = normalize_llm_config(config.get("llm"))
    holdings = []
    if wallet:
        for row in (wallet.get("holdings") or [])[:40]:
            holdings.append({
                "coin": row.get("coin"),
                "amount": row.get("amount"),
                "usd_value": row.get("usd_value"),
                "btc_value": row.get("btc_value"),
            })
    orders = []
    for item in (orderlist or [])[:50]:
        orders.append({
            "symbol": item.get("symbol"),
            "side": item.get("side"),
            "type": item.get("type"),
            "quantity": item.get("quantity", item.get("alt_amount")),
            "price": item.get("price"),
            "total": item.get("total"),
        })
    snapshot = {
        "budget": config.get("budget"),
        "balance": config.get("balance"),
        "advice": config.get("advice"),
        "trade_mode": config.get("trade_mode", "both"),
        "markets": config.get("markets"),
        "quote_currency": config.get("quote_currency"),
        "exclude_count": len(config.get("exclude") or []),
        "exclude_sample": (config.get("exclude") or [])[:20],
        "wallet_total_usd": (wallet or {}).get("total_usd"),
        "wallet_total_btc": (wallet or {}).get("total_btc"),
        "holdings": holdings,
        "proposed_orders": orders,
        "llm": {
            "auto_place": llm["auto_place"],
            "loop_enabled": llm["loop_enabled"],
            "status_reports_enabled": llm["status_reports_enabled"],
        },
        "last_cycle": last_cycle or {},
    }
    if extra:
        snapshot.update(extra)
    return snapshot


CHAT_SYSTEM_PROMPT = """Je bent Colibri, de lokale AI-assistent van TradeBot (Poloniex rebalancer).
Gebruik ALLEEN de meegeleverde portfolio-snapshot. Verzin geen balances of orders.
Antwoord in het Nederlands, kort en concreet. Help met analyse, excludes, budget en buy/sell-ideeën.
Je plaatst zelf geen orders; de bot doet dat via de bestaande pipeline."""


STATUS_SYSTEM_PROMPT = """Je bent Colibri, de autonome status-assistent van TradeBot.
Denk eerst na over de snapshot (risico, idle capital, open voorstellen, loop/auto-place).
Schrijf daarna een korte status in het Nederlands (max ~8 zinnen) voor de gebruiker.
Geen JSON. Geen verzonnen cijfers — alleen de snapshot."""


PROPOSE_SYSTEM_PROMPT = """Je bent Colibri voor TradeBot. Stel LIMIT orders voor op basis van de snapshot.
Antwoord ALLEEN met JSON: {"orders":[{"symbol":"COIN/QUOTE","side":"BUY"|"SELL","type":"LIMIT","quantity":number,"price":number,"alt":"COIN"}]}
Respecteer trade_mode, markets en exclude. Geen markdown, geen uitleg buiten JSON."""


def messages_for_chat(user_text: str, snapshot: dict) -> list[dict]:
    return [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Portfolio snapshot (JSON):\n"
                f"{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n\n"
                f"Vraag:\n{user_text}"
            ),
        },
    ]


def messages_for_status(snapshot: dict, trigger: str = "heartbeat") -> list[dict]:
    return [
        {"role": "system", "content": STATUS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Trigger: {trigger}\n"
                "Denk eerst na, geef daarna alleen het statusbericht.\n"
                f"Snapshot:\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def messages_for_propose(snapshot: dict) -> list[dict]:
    return [
        {"role": "system", "content": PROPOSE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Maak een orderlijst voor rebalance.\n"
                f"Snapshot:\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def messages_for_analyze(snapshot: dict) -> list[dict]:
    return [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Analyseer deze portfolio-snapshot. Wat valt op? "
                "Welke buys/sells of excludes zou je overwegen?\n"
                f"{json.dumps(snapshot, ensure_ascii=False, indent=2)}"
            ),
        },
    ]
