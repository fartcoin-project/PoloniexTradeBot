"""Parse and validate AI-proposed orders into TradeBot orderlist schema."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

from quote_config import markets_from_config, normalize_quote


def _now_str():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def extract_json_object(text: str) -> Any:
    """Pull JSON object/array from model text (raw or fenced)."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty AI response — no JSON orders")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start_obj = raw.find("{")
        start_arr = raw.find("[")
        starts = [i for i in (start_obj, start_arr) if i >= 0]
        if not starts:
            raise ValueError("AI response contains no JSON")
        start = min(starts)
        blob = raw[start:]
        # Try progressive trim from the end
        for end in range(len(blob), 0, -1):
            try:
                return json.loads(blob[:end])
            except json.JSONDecodeError:
                continue
        raise ValueError("Could not parse JSON from AI response")


def _symbol_parts(symbol: str) -> tuple[str, str]:
    sym = (symbol or "").strip().upper().replace("_", "/")
    if "/" not in sym:
        raise ValueError(f"Invalid symbol: {symbol}")
    base, quote = sym.split("/", 1)
    return base.strip(), normalize_quote(quote.strip())


def _excluded(base: str, quote: str, exclude: list) -> bool:
    excl = {str(x).strip().upper() for x in (exclude or [])}
    return (
        base in excl
        or f"{base}_{quote}" in excl
        or f"{base}/{quote}" in excl
    )


def validate_and_normalize_orders(
    payload: Any,
    config: dict,
    *,
    available_quote: Optional[float] = None,
) -> tuple[list[dict], list[str]]:
    """
    Convert AI payload to orderlist items.
    Returns (orders, warnings).
    """
    if isinstance(payload, dict):
        items = payload.get("orders")
        if items is None and "symbol" in payload:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("AI orders payload must be a list or {orders: [...]}")

    if not isinstance(items, list):
        raise ValueError("orders must be a list")

    selected = set(markets_from_config(config))
    trade_mode = str(config.get("trade_mode") or "both").lower()
    exclude = config.get("exclude") or []
    try:
        budget = float(config.get("budget") or 0)
    except (TypeError, ValueError):
        budget = 0.0
    quote_cap = available_quote if available_quote is not None else budget
    try:
        quote_cap = float(quote_cap)
    except (TypeError, ValueError):
        quote_cap = budget

    orders: list[dict] = []
    warnings: list[str] = []
    buy_spent = 0.0

    for raw in items:
        if not isinstance(raw, dict):
            warnings.append("Skipped non-object order entry")
            continue
        try:
            base, quote = _symbol_parts(str(raw.get("symbol") or ""))
        except ValueError as exc:
            warnings.append(str(exc))
            continue
        if selected and quote not in selected:
            warnings.append(f"Dropped {base}/{quote}: quote not in markets {sorted(selected)}")
            continue
        if _excluded(base, quote, exclude):
            warnings.append(f"Dropped {base}/{quote}: excluded")
            continue
        side = str(raw.get("side") or "").upper()
        if side not in ("BUY", "SELL"):
            warnings.append(f"Dropped {base}/{quote}: invalid side {side!r}")
            continue
        if trade_mode == "buy" and side != "BUY":
            warnings.append(f"Dropped {base}/{quote}: trade_mode=buy")
            continue
        if trade_mode == "sell" and side != "SELL":
            warnings.append(f"Dropped {base}/{quote}: trade_mode=sell")
            continue
        try:
            qty = float(raw.get("quantity", raw.get("alt_amount", 0)))
            price = float(raw.get("price", 0))
        except (TypeError, ValueError):
            warnings.append(f"Dropped {base}/{quote}: bad quantity/price")
            continue
        if qty <= 0 or price <= 0:
            warnings.append(f"Dropped {base}/{quote}: non-positive qty/price")
            continue
        total = qty * price
        if side == "BUY":
            if quote_cap > 0 and buy_spent + total > quote_cap * 1.001:
                warnings.append(
                    f"Dropped BUY {base}/{quote}: would exceed quote budget "
                    f"({buy_spent + total:.8f} > {quote_cap:.8f})"
                )
                continue
            buy_spent += total
        order_type = str(raw.get("type") or "LIMIT").upper()
        if order_type not in ("LIMIT", "MARKET"):
            order_type = "LIMIT"
        orders.append({
            "symbol": f"{base}/{quote}",
            "type": order_type,
            "side": side,
            "alt_amount": qty,
            "quantity": qty,
            "price": price,
            "total": total,
            "alt": str(raw.get("alt") or base).upper(),
            "time": _now_str(),
        })

    return orders, warnings


def orders_from_ai_text(text: str, config: dict, *, available_quote=None):
    payload = extract_json_object(text)
    return validate_and_normalize_orders(payload, config, available_quote=available_quote)
