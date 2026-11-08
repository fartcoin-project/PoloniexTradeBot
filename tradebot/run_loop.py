#!/usr/bin/env python3
"""Headless background loop: periodic AI rebalance (or classic start_bot).

Uses config.json llm.loop_* settings. Colibri must already be running
(e.g. START-HERE.bat in the colibri folder).
"""

from __future__ import annotations

import argparse
import queue
import sys
import time

from gui.paths import setup_runtime

setup_runtime()

from gui.service import BotService  # noqa: E402
from llm_client import health_check  # noqa: E402
from llm_config import normalize_llm_config  # noqa: E402
from runtime_paths import api_config_ready  # noqa: E402


def _drain(log_queue):
    while True:
        try:
            kind, payload = log_queue.get_nowait()
        except queue.Empty:
            break
        if kind in ("log", "status", "chat"):
            if kind == "chat" and isinstance(payload, dict):
                print(f"[{payload.get('type')}] {payload.get('content', '')}")
            else:
                print(payload)
        elif kind == "error":
            print(payload, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TradeBot + Colibri background loop")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override loop interval minutes",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ai_rebalance_cycle (or start_bot) and exit",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Force classic start_bot instead of ai_rebalance_cycle",
    )
    args = parser.parse_args(argv)

    if not api_config_ready():
        print("API not configured — set Poloniex keys first.", file=sys.stderr)
        return 2

    log_queue = queue.Queue()
    svc = BotService(log_queue)
    cfg = svc.load_config()
    llm = normalize_llm_config(cfg.get("llm"))
    if args.interval is not None:
        llm["loop_interval_minutes"] = max(1, int(args.interval))

    action = "start_bot" if args.no_ai or not llm.get("enabled") else "ai_rebalance_cycle"

    def one_cycle():
        health = health_check(llm["base_url"], llm["api_key"])
        if action.startswith("ai") and not health.get("ok"):
            print(f"Colibri unreachable — skip: {health.get('detail')}", file=sys.stderr)
            _drain(log_queue)
            return False
        ok = svc.run_sync(action)
        _drain(log_queue)
        return ok

    if args.once:
        return 0 if one_cycle() else 1

    print(
        f"Loop started · action={action} · every {llm['loop_interval_minutes']} min "
        f"· auto_place={llm['auto_place']}"
    )
    print("Ctrl+C to stop.")
    try:
        while True:
            one_cycle()
            # Refresh llm settings each cycle
            llm = svc.get_llm_config()
            action = "start_bot" if args.no_ai or not llm.get("enabled") else "ai_rebalance_cycle"
            time.sleep(max(1, int(llm.get("loop_interval_minutes") or 60)) * 60)
    except KeyboardInterrupt:
        print("\nLoop stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
