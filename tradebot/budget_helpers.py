"""Per-coin budget helpers (config.json coin_budgets overrides)."""

import os

from quote_config import load_pair_coins, min_order_for_quote, quote_from_config
from runtime_paths import app_dir

SLIDER_SCALE = 100_000_000  # legacy linear sliders (unused in GUI)

# Discrete budget multipliers relative to advice / global default (×1).
BUDGET_MULTIPLIERS = (0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 10.0)


def budget_multiplier_count():
    return len(BUDGET_MULTIPLIERS)


def format_budget_multiplier(step_index):
    mult = BUDGET_MULTIPLIERS[int(step_index)]
    if mult == 1.0:
        return "×1"
    if float(mult).is_integer():
        return f"×{int(mult)}"
    return f"×{mult:g}"


def value_to_multiplier_step(value, base, min_order):
    """Nearest multiplier step for value relative to base."""
    base = max(float(base or 0), float(min_order))
    value = max(float(value or 0), float(min_order))
    ratio = value / base
    best = 0
    best_dist = float("inf")
    for idx, mult in enumerate(BUDGET_MULTIPLIERS):
        dist = abs(mult - ratio)
        if dist < best_dist:
            best_dist = dist
            best = idx
    return best


def multiplier_step_to_value(step_index, base, min_order):
    base = max(float(base or 0), float(min_order))
    idx = max(0, min(int(step_index), len(BUDGET_MULTIPLIERS) - 1))
    return max(base * BUDGET_MULTIPLIERS[idx], float(min_order))


def load_btc_pair_coins(root=None):
    """Backward-compatible alias — uses quote from config.json if present."""
    return load_pair_coins(root, _quote_from_root(root))


def _quote_from_root(root):
    import json

    cfg_path = os.path.join(root or os.getcwd(), "config.json")
    if not os.path.exists(cfg_path):
        return "BTC"
    try:
        with open(cfg_path, encoding="utf-8") as handle:
            return quote_from_config(json.load(handle))
    except (OSError, json.JSONDecodeError):
        return "BTC"


def coin_budget_from_config(config, coin):
    quote = quote_from_config(config)
    min_ord = min_order_for_quote(quote)
    default = float(config.get("budget") or min_ord)
    overrides = config.get("coin_budgets") or {}
    if coin in overrides:
        return max(float(overrides[coin]), min_ord)
    return max(default, min_ord)


def normalize_coin_budgets(config, coins=None):
    """Return full map coin -> budget for GUI sliders."""
    quote = quote_from_config(config)
    min_ord = min_order_for_quote(quote)
    default = max(float(config.get("budget") or min_ord), min_ord)
    overrides = config.get("coin_budgets") or {}
    custom = set(config.get("coin_budget_custom") or [])
    if coins is None:
        coins = load_pair_coins(None, quote)
    result = {}
    for coin in coins:
        if coin in custom and coin in overrides:
            result[coin] = max(float(overrides[coin]), min_ord)
        else:
            result[coin] = default
    return result


def slider_to_btc(value):
    return int(value) / SLIDER_SCALE


def btc_to_slider(value):
    return int(round(float(value) * SLIDER_SCALE))
