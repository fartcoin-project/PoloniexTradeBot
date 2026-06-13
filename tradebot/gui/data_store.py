"""Persist wallet snapshots, bot actions, and order runs for the GUI."""

import json
import os
from datetime import datetime, timezone

from runtime_paths import app_dir

HISTORY_MAX = 500
SNAPSHOT_MAX = 200
ORDER_RUNS_MAX = 100


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class DataStore:
    def __init__(self, root=None):
        self.root = root or app_dir()
        self.data_dir = os.path.join(self.root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.history_path = os.path.join(self.data_dir, "history.json")
        self.wallet_path = os.path.join(self.data_dir, "wallet_snapshots.json")
        self.orders_path = os.path.join(self.data_dir, "order_runs.json")

    def _load(self, path, default):
        if not os.path.exists(path):
            return default
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return default

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def record_action(self, action, ok, detail=None):
        entry = {
            "time": _now_iso(),
            "action": action,
            "ok": ok,
            "detail": detail or "",
        }
        history = self._load(self.history_path, [])
        history.insert(0, entry)
        self._save(self.history_path, history[:HISTORY_MAX])
        return entry

    def get_action_history(self):
        return self._load(self.history_path, [])

    def save_wallet_snapshot(self, snapshot):
        snapshot = dict(snapshot)
        snapshot.setdefault("time", _now_iso())
        snapshots = self._load(self.wallet_path, [])
        snapshots.insert(0, snapshot)
        self._save(self.wallet_path, snapshots[:SNAPSHOT_MAX])
        return snapshot

    def get_wallet_snapshots(self):
        return self._load(self.wallet_path, [])

    def latest_wallet(self):
        snapshots = self.get_wallet_snapshots()
        return snapshots[0] if snapshots else None

    def record_order_run(self, orders, action, placed=False):
        entry = {
            "time": _now_iso(),
            "action": action,
            "placed": placed,
            "count": len(orders) if orders else 0,
            "orders": orders or [],
        }
        runs = self._load(self.orders_path, [])
        runs.insert(0, entry)
        self._save(self.orders_path, runs[:ORDER_RUNS_MAX])
        return entry

    def get_order_runs(self):
        return self._load(self.orders_path, [])


def build_wallet_from_cache(root=None):
    """Build wallet view from cached poloniex json files."""
    root = root or app_dir()
    balances_path = os.path.join(root, "json", "poloniex_balances.json")
    tickers_path = os.path.join(root, "json", "poloniex_tickers.json")
    if not os.path.exists(balances_path):
        return {"time": _now_iso(), "total_btc": 0.0, "total_usd": 0.0, "holdings": []}

    with open(balances_path, encoding="utf-8") as handle:
        balances = json.load(handle)
    tickers = {}
    if os.path.exists(tickers_path):
        with open(tickers_path, encoding="utf-8") as handle:
            tickers = json.load(handle)

    holdings = []
    total_btc = 0.0
    total_usd = 0.0
    btc_usd = None
    if "BTC/USDT" in tickers:
        btc_usd = float(tickers["BTC/USDT"].get("last") or 0)
    elif "BTC/USDC" in tickers:
        btc_usd = float(tickers["BTC/USDC"].get("last") or 0)

    for coin in sorted(balances.keys()):
        amount = float((balances.get(coin) or ["0"])[0])
        if amount <= 0:
            continue
        if coin == "BTC":
            btc_value = amount
        else:
            pair = f"{coin}/BTC"
            if pair in tickers:
                btc_value = amount * float(tickers[pair].get("last") or 0)
            else:
                btc_value = None

        usd_value = None
        if coin in ("USDT", "USDC", "USDQ", "USDR"):
            usd_value = amount
        else:
            usdt_pair = f"{coin}/USDT"
            if usdt_pair in tickers:
                usd_value = amount * float(tickers[usdt_pair].get("last") or 0)
            elif btc_value is not None and btc_usd:
                usd_value = btc_value * btc_usd

        if btc_value is not None:
            total_btc += btc_value
        if usd_value is not None:
            total_usd += usd_value

        holdings.append({
            "coin": coin,
            "amount": amount,
            "btc_value": btc_value,
            "usd_value": usd_value,
        })

    if total_usd <= 0 and total_btc > 0 and btc_usd:
        total_usd = total_btc * btc_usd

    holdings.sort(
        key=lambda row: row["btc_value"] if row["btc_value"] is not None else -1,
        reverse=True,
    )
    return {
        "time": _now_iso(),
        "total_btc": total_btc,
        "total_usd": total_usd,
        "btc_usd": btc_usd,
        "holdings": holdings,
    }


def holding_value_in_quote(holding, quote):
    """Value of one wallet row in the trading quote currency."""
    from quote_config import normalize_quote

    q = normalize_quote(quote)
    coin = holding.get("coin")
    if coin == q:
        return float(holding.get("amount") or 0)
    if q == "BTC":
        val = holding.get("btc_value")
        return float(val) if val is not None else None
    if q in ("USDT", "USDC"):
        val = holding.get("usd_value")
        return float(val) if val is not None else None
    return None


def holdings_map_for_quote(wallet, quote):
    """Map coin symbol -> {amount, quote_value} for budget rows."""
    result = {}
    for item in (wallet or {}).get("holdings") or []:
        coin = item.get("coin")
        if not coin:
            continue
        result[coin] = {
            "amount": float(item.get("amount") or 0),
            "quote_value": holding_value_in_quote(item, quote),
        }
    return result


def load_orderlist(root=None):
    path = os.path.join(root or app_dir(), "json", "orderlist.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else [data]
    except (OSError, json.JSONDecodeError):
        return []
