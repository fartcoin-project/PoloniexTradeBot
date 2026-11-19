"""GUI budget persistence helpers."""

from budget_helpers import (  # noqa: F401 — re-export for gui
    SLIDER_SCALE,
    btc_to_slider,
    coin_budget_from_config,
    load_btc_pair_coins,
    normalize_coin_budgets,
    slider_to_btc,
)


def merge_config_budgets(config, default_budget, coin_budgets, custom_coins):
    config = dict(config)
    config["budget"] = float(default_budget)
    config["coin_budgets"] = {
        coin: float(val)
        for coin, val in (coin_budgets or {}).items()
        if coin in custom_coins
    }
    config["coin_budget_custom"] = sorted(custom_coins)
    return config
