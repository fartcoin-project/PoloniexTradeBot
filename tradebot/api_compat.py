"""Helpers for the current Poloniex Spot API via ccxt.

Legacy private API (decommissioned Feb 2023) used info[0]['balances'].
See: https://api-docs.poloniex.com/spot
"""

import json
import re
import urllib.error
import urllib.request

import ccxt

SKIP_BALANCE_KEYS = frozenset(
    {"info", "free", "used", "total", "datetime", "timestamp"}
)

VALID_SYMBOL = re.compile(r"^[A-Z0-9]{1,20}$")
MIN_ORDER_BTC = 0.0001


class OperationCancelled(Exception):
    """Raised when GUI emergency stop is requested."""


def create_exchange(api_key, api_secret):
    return ccxt.poloniex(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"createMarketBuyOrderRequiresPrice": False},
        }
    )


def balances_dict_from_ccxt(fetch_bal):
    """Build {COIN: [available_str]} from ccxt fetch_balance() (Spot API)."""
    res = {}
    for currency, data in fetch_bal.items():
        if currency in SKIP_BALANCE_KEYS:
            continue
        if isinstance(data, dict) and "free" in data:
            res[currency] = [str(data.get("free") or 0)]
    return res


def currency_is_tradable(entry):
    """True if coin is listed and trading enabled on Poloniex Spot."""
    if entry.get("active") is False:
        return False
    info = entry.get("info")
    if isinstance(info, dict):
        if info.get("delisted") is True:
            return False
        if info.get("tradeEnable") is False:
            return False
        return True
    if isinstance(info, list) and info:
        nested = info[0]
        if isinstance(nested, dict):
            x_id = entry.get("id")
            inner = nested.get(x_id, nested) if x_id else nested
            if isinstance(inner, dict):
                if inner.get("delisted") is True:
                    return False
                if inner.get("tradeEnable") is False:
                    return False
                return True
    return entry.get("active", True)


def order_side_for_ccxt(side):
    return side.lower() if isinstance(side, str) else side


def order_type_for_ccxt(order_type):
    return order_type.lower() if isinstance(order_type, str) else order_type


def is_valid_trading_symbol(symbol):
    """Poloniex spot symbols are ASCII letters/digits (filters junk listed names)."""
    return bool(symbol and VALID_SYMBOL.match(str(symbol)))


def is_insufficient_balance_error(exc):
    body = parse_poloniex_error(exc)
    if body.get("code") == 21721:
        return True
    return "insufficient" in str(exc).lower()


def load_btc_available(balances_path="json/poloniex_balances.json"):
    try:
        with open_text(balances_path, "r") as handle:
            balances = json.load(handle)
        return float((balances.get("BTC") or ["0"])[0])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0


def open_text(path, mode="r", **kwargs):
    """Open text files as UTF-8 (fixes Windows cp1252 UnicodeEncodeError)."""
    if "b" in mode:
        return open(path, mode, **kwargs)
    kwargs.setdefault("encoding", "utf-8")
    return open(path, mode, **kwargs)


def fetch_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except (urllib.error.URLError, OSError, TimeoutError):
        return None


def parse_poloniex_error(exc):
    """Extract Poloniex JSON error body from ccxt exception text."""
    text = str(exc)
    start = text.find("{")
    if start >= 0:
        try:
            return json.loads(text[start:])
        except json.JSONDecodeError:
            pass
    return {}


def is_ip_whitelist_error(exc):
    body = parse_poloniex_error(exc)
    message = str(body.get("message", "")).lower()
    if "illegal of ip" in message or "illegal ip" in message:
        return True
    text = str(exc).lower()
    return "illegal of ip" in text or ("401" in text and "ip" in text)


def auth_error_help(exc):
    """Human-readable fix steps for 401 / IP / key errors."""
    lines = [
        "",
        "  Poloniex rejected the authenticated request (HTTP 401).",
        "  Public market data was saved; balance/trading needs API access.",
        "",
    ]
    if is_ip_whitelist_error(exc):
        ip = fetch_public_ip()
        lines.append("  Cause: API key IP whitelist — your IP is not allowed.")
        if ip:
            lines.append(f"  Whitelist this IP in Poloniex → API Management: {ip}")
        else:
            lines.append("  Whitelist your current public IP in Poloniex → API Management.")
        lines.append("  Or create a key with IP restriction disabled (less secure).")
    else:
        body = parse_poloniex_error(exc)
        if body.get("message"):
            lines.append(f"  Poloniex says: {body['message']}")
        lines.append("  Check: Spot API key, read + trade permissions, correct secret.")
    lines.extend([
        "  Docs: https://api-docs.poloniex.com/spot",
        "",
    ])
    return "\n".join(lines)
