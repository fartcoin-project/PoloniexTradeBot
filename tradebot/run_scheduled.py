#!/usr/bin/env python3
"""Headless TradeBot run for Windows Task Scheduler (no GUI).

Uses config.json: budget, markets, exclude list, and trade_mode (buy/sell).
Logs to logs/tradebot.log beside the app.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys

from gui.paths import setup_runtime

setup_runtime()

from gui.service import BotService  # noqa: E402
from gui.schedule_config import schedule_budget_from_config
from quote_config import (  # noqa: E402
    format_markets_label,
    markets_from_config,
    min_order_for_markets,
    primary_quote_from_config,
)
from runtime_paths import api_config_ready, app_dir  # noqa: E402

SCHEDULED_ACTIONS = (
    "start_bot",
    "update_markets",
    "collect_orders",
    "place_orders",
)


def _drain_log_queue(log_queue):
    while True:
        try:
            kind, payload = log_queue.get_nowait()
        except queue.Empty:
            break
        if kind in ("log", "status"):
            print(payload)
        elif kind == "error":
            print(payload, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run TradeBot headless (Windows Task Scheduler)",
    )
    parser.add_argument(
        "--action",
        default="start_bot",
        choices=SCHEDULED_ACTIONS,
        help="Pipeline to run (default: full start_bot = update + build + place)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Override config.json budget for this run",
    )
    args = parser.parse_args(argv)

    if not api_config_ready():
        print(
            "API not configured — create tradebot_config.py with your Poloniex keys.",
            file=sys.stderr,
        )
        return 2

    log_queue = queue.Queue()
    svc = BotService(log_queue)
    cfg = svc.load_config()
    markets = markets_from_config(cfg)
    if not markets:
        print("No markets selected in config.json.", file=sys.stderr)
        return 2

    primary = primary_quote_from_config(cfg)
    budget = float(args.budget if args.budget is not None else schedule_budget_from_config(cfg))
    min_ord = min_order_for_markets(markets)
    if budget < min_ord:
        print(
            f"Budget {budget} is below minimum {min_ord} for selected markets.",
            file=sys.stderr,
        )
        return 2

    if args.budget is not None:
        cfg["budget"] = budget
        config_path = os.path.join(app_dir(), "config.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(cfg, handle, indent=4)

    market_label = format_markets_label(markets) if len(markets) > 1 else primary
    print(f"TradeBot scheduled run: {args.action}")
    print(f"  markets: {market_label}")
    print(f"  budget:  {budget}")
    print(f"  mode:    {cfg.get('trade_mode', 'both')}")

    ok = svc.run_sync(args.action)
    _drain_log_queue(log_queue)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
