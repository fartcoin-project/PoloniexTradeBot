"""Quote currency (BTC / USDT / USDC) helpers for Poloniex spot markets."""

import os
SUPPORTED_QUOTES = ("BTC", "USDT", "USDC")
GUI_MARKETS = ("BTC", "USDT")

MIN_ORDER_BY_QUOTE = {
    "BTC": 0.0001,
    "USDT": 1.0,
    "USDC": 1.0,
}


def normalize_quote(quote):
    q = (quote or "BTC").strip().upper()
    if q == "USD":
        return "USDT"
    if q not in SUPPORTED_QUOTES:
        return "BTC"
    return q


def quote_from_config(config):
    return primary_quote_from_config(config)


def markets_from_config(config):
    """Selected GUI markets (BTC / USDT), both allowed."""
    raw = (config or {}).get("markets")
    if isinstance(raw, list) and raw:
        selected = []
        for item in raw:
            q = normalize_quote(item)
            if q == "USDC":
                q = "USDT"
            if q in GUI_MARKETS and q not in selected:
                selected.append(q)
        if selected:
            return sorted(selected, key=lambda m: GUI_MARKETS.index(m))
    q = normalize_quote((config or {}).get("quote_currency") or "BTC")
    if q == "USDC":
        q = "USDT"
    return [q] if q in GUI_MARKETS else ["BTC"]


def primary_quote_from_config(config):
    markets = markets_from_config(config)
    return markets[0]


def market_section_title(markets):
    labels = [normalize_quote(m) for m in (markets or ["BTC"])]
    if len(labels) == 1:
        return f"Market · {labels[0]}"
    return "Market · " + " + ".join(labels)


def format_markets_label(markets):
    return " + ".join(normalize_quote(m) for m in markets)


def is_pair_excluded(coin, quote, exclude):
    excluded = {str(item).upper() for item in (exclude or [])}
    pair_key = market_id(coin, quote).upper()
    return coin.upper() in excluded or pair_key in excluded


def min_order_for_markets(markets):
    if not markets:
        return MIN_ORDER_BY_QUOTE["BTC"]
    return max(min_order_for_quote(q) for q in markets)


def market_balance_from_config(config, quote):
    q = normalize_quote(quote)
    balances = (config or {}).get("market_balances") or {}
    if q in balances:
        try:
            return float(balances[q])
        except (TypeError, ValueError):
            return 0.0
    if q == primary_quote_from_config(config):
        try:
            return float((config or {}).get("balance") or 0)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def min_order_for_quote(quote):
    return MIN_ORDER_BY_QUOTE.get(normalize_quote(quote), MIN_ORDER_BY_QUOTE["BTC"])


def ccxt_symbol(coin, quote):
    return f"{coin}/{normalize_quote(quote)}"


def market_id(coin, quote):
    return f"{coin}_{normalize_quote(quote)}"


def market_suffix(quote):
    return f"_{normalize_quote(quote)}"


def pairs_filename(quote):
    q = normalize_quote(quote).lower()
    if q == "btc":
        return "poloniex_btc_pairs.txt"
    return f"poloniex_{q}_pairs.txt"


def markets_filename(quote):
    q = normalize_quote(quote)
    if q == "BTC":
        return "poloniex_Btc_Markets.txt"
    return f"poloniex_{q}_Markets.txt"


def pairs_path(root, quote):
    base = root if root is not None else os.getcwd()
    return os.path.join(base, "json", pairs_filename(quote))


def load_pair_coins(root=None, quote="BTC"):
    path = pairs_path(root, quote)
    if not os.path.exists(path) and normalize_quote(quote) == "BTC":
        legacy = os.path.join(root or os.getcwd(), "json", "poloniex_btc_pairs.txt")
        path = legacy
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def active_pair_coins(root=None, quote="BTC", exclude=None, config=None):
    """Tradable pair coins minus the configured exclude list."""
    coins = load_pair_coins(root, quote)
    if exclude is None and config is not None:
        exclude = (config or {}).get("exclude") or []
    return [coin for coin in coins if not is_pair_excluded(coin, quote, exclude)]


def active_pairs_all_markets(root=None, config=None):
    """Active (coin, quote) pairs across all selected markets."""
    config = config or {}
    pairs = []
    for quote in markets_from_config(config):
        for coin in active_pair_coins(root, quote, config=config):
            if coin == quote:
                continue
            pairs.append((coin, quote))
    return pairs


def suggest_excludes_for_unheld(pair_coins, balances, tickers, quote, *, min_hold_value=None):
    """Coins to exclude when the account has no meaningful balance in that alt."""
    q = normalize_quote(quote)
    if min_hold_value is None:
        min_hold_value = min_order_for_quote(q) * 0.05
    exclude = []
    for coin in pair_coins:
        if coin == q:
            continue
        amount = float((balances.get(coin) or ["0"])[0])
        if amount <= 0:
            exclude.append(coin)
            continue
        pair = ccxt_symbol(coin, q)
        if pair not in tickers:
            exclude.append(coin)
            continue
        value = amount * float(tickers[pair].get("last") or 0)
        if value < min_hold_value:
            exclude.append(coin)
    return sorted(set(exclude))


def load_quote_available(balances_path="json/poloniex_balances.json", quote="BTC"):
    import json

    from api_compat import open_text

    q = normalize_quote(quote)
    try:
        with open_text(balances_path, "r") as handle:
            balances = json.load(handle)
        return float((balances.get(q) or ["0"])[0])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0


def format_quote_value(quote, value):
    q = normalize_quote(quote)
    if q == "BTC":
        return f"₿ {value:.8f}"
    if q in ("USDT", "USDC"):
        return f"{value:.2f} {q}"
    return f"{value:.4f} {q}"


def portfolio_in_quote(balances, tickers, pair_coins, quote):
    """Total portfolio value denominated in the trading quote currency."""
    q = normalize_quote(quote)
    total = float((balances.get(q) or ["0"])[0])

    for coin in pair_coins:
        if coin == q:
            continue
        if coin not in balances:
            continue
        pair = ccxt_symbol(coin, q)
        if pair not in tickers:
            continue
        amount = float((balances.get(coin) or ["0"])[0])
        if amount <= 0:
            continue
        total += amount * float(tickers[pair].get("last") or 0)

    if q != "BTC":
        btc_amt = float((balances.get("BTC") or ["0"])[0])
        if btc_amt > 0:
            btc_pair = ccxt_symbol("BTC", q)
            if btc_pair in tickers:
                total += btc_amt * float(tickers[btc_pair].get("last") or 0)

    return total


def filter_live_markets(live_market, quote):
    suffix = market_suffix(quote)
    return sorted(x for x in live_market if x.endswith(suffix))
