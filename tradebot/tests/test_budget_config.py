"""Tests for GUI budget config merge helper."""

from gui.budget_config import merge_config_budgets


def test_merge_config_budgets_keeps_only_custom_coins():
    cfg = {"budget": 0.0001, "exclude": ["X"]}
    merged = merge_config_budgets(
        cfg,
        default_budget=0.0008,
        coin_budgets={"ADA": 0.001, "ETH": 0.002, "DOGE": 0.003},
        custom_coins={"ADA", "ETH"},
    )
    assert merged["budget"] == 0.0008
    assert merged["coin_budgets"] == {"ADA": 0.001, "ETH": 0.002}
    assert merged["coin_budget_custom"] == ["ADA", "ETH"]
