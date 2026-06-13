import json
import os
import sys
import threading
import time
from contextlib import contextmanager

from api_compat import OperationCancelled
from gui.cancel import CancelController
from gui.data_store import DataStore, build_wallet_from_cache, load_orderlist
from gui.log_stream import ProgressCapture, QueueLogWriter, SessionFileLogger
from gui.paths import app_dir, setup_runtime
from gui.schedule import apply_windows_schedule
from gui.schedule_config import normalize_schedule
from quote_config import (
    format_quote_value,
    markets_from_config,
    min_order_for_markets,
    min_order_for_quote,
    normalize_quote,
    pairs_filename,
)
from runtime_paths import (
    PLACEHOLDER_API_KEY,
    PLACEHOLDER_API_SECRET,
    api_config_ready,
    read_api_credentials,
    save_api_credentials,
)

BOT_DIR = app_dir()

ACTION_LABELS = {
    "update_markets": "update markets",
    "collect_orders": "build orders",
    "preview_orders": "preview orders",
    "place_orders": "place orders",
    "start_bot": "start bot",
    "total_balance": "total balance",
    "refresh_advice": "refresh advice",
    "open_orders": "open orders",
}


def action_label(action_name):
    return ACTION_LABELS.get(action_name, action_name.replace("_", " "))


class BotService:
    """Thread-safe wrapper around tradebot.py for GUI use."""

    def __init__(self, log_queue):
        self.log_queue = log_queue
        self._tb = None
        self._lock = threading.Lock()
        self._file_log = SessionFileLogger.get()
        self._verbose_log = True
        self._store = DataStore(BOT_DIR)
        self._cancel = CancelController()
        self._current_action = None

    def is_busy(self):
        return self._current_action is not None

    def request_cancel(self):
        if not self.is_busy():
            return False
        self._cancel.request()
        self.log_queue.put(("status", "Emergency stop requested…"))
        self._file_log.write_line("cancel", f"Emergency stop during {self._current_action}")
        return True

    def data_dir(self):
        return self._store.data_dir

    def get_wallet(self):
        snapshot = build_wallet_from_cache(BOT_DIR)
        if snapshot.get("holdings"):
            self._store.save_wallet_snapshot(snapshot)
        return snapshot

    def get_action_history(self):
        return self._store.get_action_history()

    def get_order_runs(self):
        return self._store.get_order_runs()

    def load_persisted_wallet(self):
        return self._store.latest_wallet() or build_wallet_from_cache(BOT_DIR)

    def _persist_session(self, action_name, ok, detail=""):
        self._store.record_action(action_name, ok, detail)
        wallet = None
        if ok and action_name in (
            "update_markets", "total_balance", "start_bot", "collect_orders",
            "place_orders", "preview_orders",
        ):
            wallet = build_wallet_from_cache(BOT_DIR)
            if wallet.get("holdings"):
                self._store.save_wallet_snapshot(wallet)
        if ok and action_name in ("collect_orders", "place_orders", "preview_orders", "start_bot"):
            placed = action_name in ("place_orders", "start_bot")
            orders = load_orderlist(BOT_DIR)
            if orders:
                self._store.record_order_run(orders, action_name, placed=placed)
        self.log_queue.put(("history", {
            "actions": self._store.get_action_history(),
            "orders": self._store.get_order_runs(),
        }))
        if wallet is not None:
            self.log_queue.put(("wallet", wallet))
        elif ok and action_name == "total_balance":
            self.log_queue.put(("wallet", self.load_persisted_wallet()))

    def log_file_path(self):
        return self._file_log.log_path

    def _ensure_loaded(self):
        if self._tb is not None:
            return
        setup_runtime()
        if BOT_DIR not in sys.path:
            sys.path.insert(0, BOT_DIR)
        import tradebot as tb

        self._patch_for_gui(tb)
        self._tb = tb
        cfg = self.load_config()
        self._verbose_log = bool(cfg.get("verbose_log", True))
        self._tb.args.log = self._verbose_log
        self._sync_config()

    def set_verbose_log(self, enabled):
        self._verbose_log = bool(enabled)
        if self._tb is not None:
            self._tb.args.log = self._verbose_log

    def _patch_for_gui(self, tb):
        tb.menu = lambda: None
        tb.set_interactive_menu(False)

        def completed():
            self.log_queue.put(("status", "Trading run finished successfully."))
            self._emit_config()
            self.log_queue.put(("done", None))

        tb.completed = completed

        def exit_tradebot(good_exit=False):
            if good_exit:
                self.log_queue.put(("status", "Done."))
            else:
                self.log_queue.put(("error", "Operation failed."))
            self.log_queue.put(("done", None))

        tb.exit_tradebot = exit_tradebot
        tb.set_cancel_check(lambda: self._cancel.is_set())

    def _install_interruptible_sleep(self, tb):
        sleeper = self._cancel.interruptible_sleep
        self._orig_time_sleep = time.sleep
        self._orig_tb_sleep = tb.sleep
        tb.sleep = sleeper
        time.sleep = sleeper

    def _restore_sleep(self):
        if hasattr(self, "_orig_time_sleep"):
            time.sleep = self._orig_time_sleep
        if self._tb is not None and hasattr(self, "_orig_tb_sleep"):
            self._tb.sleep = self._orig_tb_sleep

    @staticmethod
    def _apply_sell_mode(tradebot, sell_mode):
        if sell_mode == "sell":
            tradebot.args.sell = True
        elif sell_mode == "buy":
            tradebot.args.sell = False
        else:
            tradebot.args.sell = None

    def _sync_config(self):
        cfg = self.load_config()
        self._tb.exclude_list = cfg.get("exclude", [])
        self._apply_sell_mode(self._tb, cfg.get("trade_mode", "both"))

    def _emit_config(self):
        cfg = self.load_config()
        stats = self._safe_advice_stats()
        if stats:
            cfg.update({
                "markets": stats["markets"],
                "balance": stats["balance"],
                "advice": stats["advice"],
                "budget": stats.get("budget", cfg.get("budget")),
            })
        self.log_queue.put(("config", cfg))

    def _safe_advice_stats(self):
        cfg = self.load_config()
        selected = markets_from_config(cfg)
        if not any(
            os.path.exists(os.path.join(BOT_DIR, "json", pairs_filename(q)))
            for q in selected
        ):
            return None
        try:
            return self._tb.advice(show=False)
        except (OSError, ValueError, json.JSONDecodeError, KeyError):
            return None

    def load_config(self):
        path = os.path.join(BOT_DIR, "config.json")
        if not os.path.exists(path):
            return {
                "budget": 0.0,
                "balance": 0.0,
                "advice": "0.0005",
                "exclude": [],
                "markets": 0,
            }
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def load_api_credentials(self):
        setup_runtime()
        return read_api_credentials()

    def api_configured(self):
        setup_runtime()
        return api_config_ready()

    def save_api_credentials(self, api_key, api_secret):
        key = (api_key or "").strip()
        secret = (api_secret or "").strip()
        if not key:
            raise ValueError("API key is required")
        if not secret:
            _, existing_secret = read_api_credentials()
            if existing_secret and existing_secret != PLACEHOLDER_API_SECRET:
                secret = existing_secret
            else:
                raise ValueError("API secret is required")
        save_api_credentials(key, secret)
        if self._tb is not None:
            self._tb.reload_exchange()

    def save_config(
        self,
        budget,
        exclude,
        sell_mode="both",
        verbose_log=False,
        api_key=None,
        api_secret=None,
        coin_budgets=None,
        coin_budget_custom=None,
        markets=None,
        quote_currency=None,
        schedule=None,
    ):
        setup_runtime()
        key = (api_key or "").strip() if api_key is not None else ""
        secret = (api_secret or "").strip() if api_secret is not None else ""
        if key or secret:
            self.save_api_credentials(key, secret)
        self._ensure_loaded()
        if markets is None:
            markets = [normalize_quote(quote_currency or "BTC")]
        selected = markets_from_config({"markets": markets})
        if not selected:
            raise ValueError("Select at least one market (BTC or USDT).")
        min_ord = min_order_for_markets(selected)
        primary = selected[0]
        if budget < min_ord:
            raise ValueError(
                f"Budget must be at least {format_quote_value(primary, min_ord)}"
            )
        cfg = self.load_config()
        cfg["budget"] = float(budget)
        cfg["markets"] = selected
        cfg["quote_currency"] = primary
        cfg["exclude"] = [coin.strip().upper() for coin in exclude if coin.strip()]
        custom = set(coin_budget_custom or [])
        if coin_budgets:
            cfg["coin_budgets"] = {
                coin: float(val)
                for coin, val in coin_budgets.items()
                if coin in custom
            }
        else:
            cfg["coin_budgets"] = {}
        cfg["coin_budget_custom"] = sorted(custom)
        cfg["verbose_log"] = bool(verbose_log)
        cfg["trade_mode"] = sell_mode
        if schedule is not None:
            cfg["schedule"] = normalize_schedule(schedule)
        elif "schedule" not in cfg:
            cfg["schedule"] = normalize_schedule({})
        path = os.path.join(BOT_DIR, "config.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(cfg, handle, indent=4)

        self._tb.exclude_list = cfg["exclude"]
        self.set_verbose_log(verbose_log)
        self._apply_sell_mode(self._tb, sell_mode)
        self._emit_config()
        return apply_windows_schedule(cfg["schedule"])

    def help_text(self):
        self._ensure_loaded()
        return self._tb.help_text()

    @contextmanager
    def _capture_output(self):
        self._ensure_loaded()
        writer = QueueLogWriter(self.log_queue, file_logger=self._file_log)
        progress = ProgressCapture(self.log_queue, file_logger=self._file_log)
        self._progress_capture = progress
        progress.reset()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_progress = self._tb.update_progress
        old_progress_bar = self._tb.ProgressBar
        log_queue = self.log_queue
        file_logger = self._file_log
        tb = self._tb

        class GuiProgressBar(old_progress_bar):
            def __call__(self):
                super().__call__()
                if self.total > 0:
                    line = f"  Build orders: {self.current}/{self.total}"
                    log_queue.put(("log", line))
                    if file_logger is not None:
                        file_logger.write_line("log", line)

        sys.stdout = writer
        sys.stderr = writer
        self._tb.update_progress = progress
        tb.ProgressBar = GuiProgressBar
        self._install_interruptible_sleep(self._tb)
        try:
            yield
        finally:
            writer.flush()
            self._restore_sleep()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self._tb.update_progress = old_progress
            tb.ProgressBar = old_progress_bar

    def _execute_action(self, action_name):
        if action_name not in self._actions():
            raise ValueError(f"Unknown action: {action_name}")

        ok = True
        detail = ""
        self._cancel.reset()
        self._current_action = action_name
        try:
            self._file_log.session_start(action_name)
            self.log_queue.put(("status", f"Running: {action_label(action_name)}..."))
            self.log_queue.put(("log", f"--- {action_label(action_name)} ---"))
            self.log_queue.put(("busy", True))
            with self._capture_output():
                self._actions()[action_name]()
            if self._cancel.is_set():
                raise OperationCancelled("Emergency stop — cancelled by user")
            self._emit_config()
            self.log_queue.put(("status", f"Finished: {action_label(action_name)}"))
        except OperationCancelled as exc:
            ok = False
            detail = str(exc)
            self.log_queue.put(("error", detail))
            self._file_log.write_line("cancel", detail)
        except Exception as exc:
            ok = False
            detail = str(exc)
            self.log_queue.put(("error", detail))
            self._file_log.log_exception(action_name, exc)
        finally:
            self._current_action = None
            self._cancel.reset()
            self._file_log.session_end(action_name, ok=ok)
            self._persist_session(action_name, ok, detail if not ok else "")
            self.log_queue.put(("action_done", {"action": action_name, "ok": ok}))
            self.log_queue.put(("busy", False))
            self.log_queue.put(("done", None))
        return ok

    def run_sync(self, action_name):
        """Run one action on the calling thread (headless / Task Scheduler)."""
        self._ensure_loaded()
        with self._lock:
            return self._execute_action(action_name)

    def run_async(self, action_name, callback=None):
        if action_name not in self._actions():
            raise ValueError(f"Unknown action: {action_name}")

        def worker():
            with self._lock:
                ok = self._execute_action(action_name)
                if callback:
                    callback()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def _actions(self):
        tb = self._tb
        prog = lambda: self._progress_capture

        def update_markets():
            p = prog()
            p.set_phase(0, 75)
            tb.get_update(show=False)
            p.set_phase(75, 95)
            tb.market_list()
            p.set_phase(95, 100)
            tb.advice(show=False)

        def total_balance():
            p = prog()
            p.set_phase(0, 85)
            tb.total_balance(show=False)
            p.set_phase(85, 100)
            tb.advice(show=False)

        def collect_orders():
            p = prog()
            p.set_phase(0, 100)
            tb.collect_orders(show=False)

        def _require_orderlist():
            path = os.path.join(BOT_DIR, "json", "orderlist.json")
            if not os.path.isfile(path):
                raise FileNotFoundError(
                    "No order list — run Build Orders first (missing json/orderlist.json)"
                )

        def preview_orders():
            _require_orderlist()
            p = prog()
            p.set_phase(0, 100)
            tb.order_list(place=False)

        def place_orders():
            _require_orderlist()
            p = prog()
            p.set_phase(0, 100)
            tb.order_list(place=True)

        def start_bot():
            p = prog()
            p.set_phase(0, 45)
            tb.get_update(show=False)
            p.set_phase(45, 60)
            tb.market_list()
            p.set_phase(60, 85)
            tb.collect_orders(show=False)
            p.set_phase(85, 100)
            tb.order_list(place=True)

        return {
            # CLI menu 1–6
            "start_bot": start_bot,
            "update_markets": update_markets,
            "total_balance": total_balance,
            "collect_orders": collect_orders,
            "preview_orders": preview_orders,
            "place_orders": place_orders,
            # CLI menu 9 / options
            "open_orders": lambda: tb.get_open_orders(show=False),
            "refresh_advice": lambda: tb.advice(show=False),
        }