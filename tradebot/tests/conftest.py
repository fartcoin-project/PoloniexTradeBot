"""Shared fixtures for tradebot.py tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

TRADEBOT_ROOT = Path(__file__).resolve().parent.parent
if str(TRADEBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRADEBOT_ROOT))

_MOCK_CONFIG = type(
    "TradebotConfig",
    (),
    {"SECRET_API_KEY": "test-key", "SECRET_API_SECRET": "test-secret"},
)()
_MOCK_POLO = MagicMock(name="poloniex_exchange")


def _default_orderbook():
    return {
        "asks": [
            [0.00001000, 50000.0],
            [0.00001050, 40000.0],
            [0.00001100, 30000.0],
            [0.00001150, 20000.0],
            [0.00001200, 10000.0],
        ],
        "bids": [
            [0.00000950, 50000.0],
            [0.00000900, 40000.0],
            [0.00000850, 30000.0],
            [0.00000800, 20000.0],
            [0.00000750, 10000.0],
        ],
    }


_MOCK_POLO.fetch_order_book.return_value = _default_orderbook()

_patches = [
    patch("runtime_paths.load_tradebot_config", return_value=_MOCK_CONFIG),
    patch("api_compat.create_exchange", return_value=_MOCK_POLO),
]
for _patch in _patches:
    _patch.start()

import tradebot  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    for _patch in _patches:
        _patch.stop()


@pytest.fixture
def mock_polo():
    _MOCK_POLO.reset_mock()
    _MOCK_POLO.fetch_order_book.return_value = _default_orderbook()
    tradebot.polo = _MOCK_POLO
    return _MOCK_POLO


@pytest.fixture
def tradebot_env(tmp_path, monkeypatch, mock_polo):
    """Isolated cwd with json/config fixtures; resets tradebot globals."""
    monkeypatch.chdir(tmp_path)
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    (tmp_path / "orderbooks").mkdir()

    tradebot.exclude_list = []
    tradebot.args.log = False
    tradebot.args.sell = None
    tradebot.set_cancel_check(None)
    tradebot.set_interactive_menu(True)

    return tmp_path


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def seed_market_files(
    root: Path,
    *,
    coins=None,
    balances=None,
    tickers=None,
    config=None,
):
    if coins is None:
        coins = ["ADA", "ETH"]
    balances = balances or {"BTC": ["0.01000000"], "ADA": ["0"]}
    tickers = tickers or {
        "ADA/BTC": {"last": "0.00001000"},
        "ETH/BTC": {"last": "0.05000000"},
    }
    config = config or {
        "time": "",
        "budget": 0.0008,
        "balance": "0.01",
        "advice": 0.0,
        "exclude": [],
    }

    (root / "json" / "poloniex_btc_pairs.txt").write_text(
        ("\n".join(coins) + "\n") if coins else "",
        encoding="utf-8",
    )
    write_json(root / "json" / "poloniex_balances.json", balances)
    write_json(root / "json" / "poloniex_tickers.json", tickers)
    write_json(root / "config.json", config)


def seed_ccxt_fetch_mocks(mock_polo):
    """Standard ccxt responses for get_update() / market_list() pipeline tests."""
    mock_polo.fetch_markets.return_value = [
        {"id": "ADA_BTC", "active": True},
        {"id": "ETH_BTC", "active": True},
        {"id": "DOGE_BTC", "active": False},
        {"id": "ADA_USDT", "active": True},
    ]
    mock_polo.fetch_currencies.return_value = {
        "ADA": {"id": "ADA", "active": True, "info": {"tradeEnable": True}},
        "ETH": {"id": "ETH", "active": True, "info": {"tradeEnable": True}},
        "BTC": {"id": "BTC", "active": True, "info": {"tradeEnable": True}},
    }
    mock_polo.fetch_balance.return_value = {
        "BTC": {"free": 0.01, "used": 0.0, "total": 0.01},
        "ADA": {"free": 100.0, "used": 0.0, "total": 100.0},
        "info": {},
    }
    mock_polo.fetch_tickers.return_value = {
        "ADA/BTC": {"last": "0.00001000"},
        "ETH/BTC": {"last": "0.05000000"},
        "BTC/USDT": {"last": "50000.0"},
    }
