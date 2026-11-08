import json
import os
import sys
import threading
import time
from contextlib import contextmanager

from ai_orders import orders_from_ai_text
from ai_status import AiMessageStore
from api_compat import OperationCancelled
import colibri_manager
from gui.cancel import CancelController
from gui.data_store import DataStore, build_wallet_from_cache, load_orderlist
from gui.log_stream import ProgressCapture, QueueLogWriter, SessionFileLogger
from gui.paths import app_dir, setup_runtime
from gui.schedule import apply_windows_schedule, ScheduleApplyResult
from gui.schedule_config import normalize_schedule
from llm_client import (
    LlmError,
    build_portfolio_context,
    chat_completions,
    health_check,
    messages_for_analyze,
    messages_for_chat,
    messages_for_propose,
    messages_for_status,
)
from llm_config import normalize_llm_config
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
    read_hf_token,
    save_api_credentials,
    save_hf_token,
)

BOT_DIR = app_dir()

ACTION_LABELS = {
    "update_markets": "update markets",
    "collect_orders": "build orders",
    "preview_orders": "preview orders",
    "place_orders": "place orders",
    "start_bot": "start bot",
    "total_balance": "total balance",
    "refresh_advice": "budget advice",
    "open_orders": "open orders",
    "ai_analyze": "AI analyze",
    "ai_propose_orders": "AI propose orders",
    "ai_rebalance_cycle": "AI rebalance cycle",
    "ai_status_report": "AI status report",
    "ai_chat": "AI chat",
    "colibri_list_models": "Colibri list models",
    "colibri_download": "Colibri download model",
    "colibri_start": "Colibri start",
    "colibri_stop": "Colibri stop",
    "colibri_status": "Colibri status",
}


def action_label(action_name):
    return ACTION_LABELS.get(action_name, action_name.replace("_", " "))


class BotService:
    """Thread-safe wrapper around tradebot.py for GUI use."""

    def __init__(self, log_queue):
        self.log_queue = log_queue
        self._tb = None
        self._lock = threading.RLock()
        self._file_log = SessionFileLogger.get()
        self._verbose_log = True
        self._store = DataStore(BOT_DIR)
        self._ai_store = AiMessageStore(BOT_DIR)
        self._cancel = CancelController()
        self._current_action = None
        self._last_cycle = {}
        self._colibri_was_down = False
        self._pending_chat = None
        self._pending_colibri_model = None
        self._loop_stop = threading.Event()
        self._loop_thread = None
        self._status_stop = threading.Event()
        self._status_thread = None

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
            "ai_propose_orders", "ai_rebalance_cycle",
        ):
            wallet = build_wallet_from_cache(BOT_DIR)
            if wallet.get("holdings"):
                self._store.save_wallet_snapshot(wallet)
        if ok and action_name in (
            "collect_orders", "place_orders", "preview_orders", "start_bot",
            "ai_propose_orders", "ai_rebalance_cycle",
        ):
            placed = action_name in ("place_orders", "start_bot") or (
                action_name == "ai_rebalance_cycle"
                and bool((self._last_cycle or {}).get("placed"))
            )
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
            cfg = {
                "budget": 0.0,
                "balance": 0.0,
                "advice": "0.0005",
                "exclude": [],
                "markets": 0,
            }
        else:
            with open(path, "r", encoding="utf-8") as handle:
                cfg = json.load(handle)
        cfg["llm"] = normalize_llm_config(cfg.get("llm"))
        return cfg

    def get_llm_config(self):
        return normalize_llm_config(self.load_config().get("llm"))

    def get_ai_chat_history(self):
        return self._ai_store.load_chat()

    def get_ai_status_history(self):
        return self._ai_store.load_status()

    def save_hf_token_if_provided(self, token):
        """Save HF token when non-empty; blank keeps existing."""
        value = (token or "").strip()
        if value:
            save_hf_token(value)
        return bool(read_hf_token())

    def colibri_runtime_info(self):
        return colibri_manager.runtime_info()

    def _colibri_line(self, line):
        self.log_queue.put(("colibri_log", line))
        # Heuristic progress from coli install-state / percent lines
        state = colibri_manager.read_install_state()
        done = state.get("done")
        total = state.get("total")
        pct = None
        if isinstance(done, (int, float)) and isinstance(total, (int, float)) and total:
            pct = int(100 * float(done) / float(total))
        self.log_queue.put(("colibri_progress", {"percent": pct, "line": line, "state": state}))

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
            existing_key, existing_secret = read_api_credentials()
            if existing_secret and existing_secret != PLACEHOLDER_API_SECRET:
                secret = existing_secret
            else:
                raise ValueError("API secret is required")
        else:
            existing_key, existing_secret = read_api_credentials()
            if key == existing_key and secret == existing_secret:
                return
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
        llm=None,
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
        old_schedule = normalize_schedule(cfg.get("schedule", {}))
        old_llm = normalize_llm_config(cfg.get("llm"))
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
        if llm is not None:
            cfg["llm"] = normalize_llm_config(llm)
        else:
            cfg["llm"] = old_llm
        schedule_changed = cfg["schedule"] != old_schedule
        path = os.path.join(BOT_DIR, "config.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(cfg, handle, indent=4)

        self._tb.exclude_list = cfg["exclude"]
        self.set_verbose_log(verbose_log)
        self._apply_sell_mode(self._tb, sell_mode)
        self._emit_config()
        if schedule_changed:
            return apply_windows_schedule(cfg["schedule"])
        return ScheduleApplyResult(ok=True, message="", task_state=None)

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

    def _snapshot_for_llm(self, extra=None):
        cfg = self.load_config()
        wallet = build_wallet_from_cache(BOT_DIR)
        orders = load_orderlist(BOT_DIR)
        return build_portfolio_context(
            config=cfg,
            wallet=wallet,
            orderlist=orders,
            last_cycle=self._last_cycle,
            extra=extra,
        )

    def _llm_call(self, messages, *, enable_thinking=False, reasoning_effort=None, max_tokens=2048):
        llm = self.get_llm_config()
        if not llm["enabled"]:
            raise LlmError("LLM is disabled in config")
        return chat_completions(
            messages,
            base_url=llm["base_url"],
            api_key=llm["api_key"],
            model=llm["model"],
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )

    def _emit_chat(self, role, content, msg_type="chat"):
        entry = self._ai_store.append_chat(role, content, msg_type=msg_type)
        self.log_queue.put(("chat", entry))
        return entry

    def check_colibri_health(self):
        llm = self.get_llm_config()
        result = health_check(llm["base_url"], llm["api_key"])
        was_down = self._colibri_was_down
        self._colibri_was_down = not result.get("ok")
        self.log_queue.put(("llm_status", {
            "ok": result.get("ok"),
            "detail": result.get("detail"),
            "models": result.get("models") or [],
            "llm": llm,
        }))
        if was_down and result.get("ok") and llm.get("status_reports_enabled"):
            self._maybe_status_report(trigger="colibri_up", force=True)
        return result

    def run_chat_async(self, user_text, callback=None):
        text = (user_text or "").strip()
        if not text:
            raise ValueError("Empty chat message")

        def worker():
            with self._lock:
                self._pending_chat = text
                ok = self._execute_action("ai_chat")
                if callback:
                    callback()
            return ok

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def _write_orderlist(self, orders):
        path = os.path.join(BOT_DIR, "json", "orderlist.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(orders, handle, indent=4)
        print(f"  AI wrote {len(orders)} order(s) → json/orderlist.json")

    def _ai_analyze_impl(self):
        snapshot = self._snapshot_for_llm()
        result = self._llm_call(
            messages_for_analyze(snapshot),
            enable_thinking=True,
            reasoning_effort="medium",
        )
        if result.get("thinking"):
            self._file_log.write_line("ai_thinking", result["thinking"][:4000])
        content = result.get("content") or "(geen analyse)"
        print(content)
        self._emit_chat("assistant", content, msg_type="analyze")
        return content

    def _ai_propose_impl(self):
        cfg = self.load_config()
        snapshot = self._snapshot_for_llm()
        result = self._llm_call(
            messages_for_propose(snapshot),
            enable_thinking=True,
            max_tokens=3000,
        )
        if result.get("thinking"):
            self._file_log.write_line("ai_thinking", result["thinking"][:4000])
        try:
            quote_bal = float(str(cfg.get("balance") or 0).replace(",", ""))
        except ValueError:
            quote_bal = 0.0
        try:
            budget = float(cfg.get("budget") or 0)
        except (TypeError, ValueError):
            budget = 0.0
        cap = budget if budget > 0 else quote_bal
        if quote_bal > 0 and budget > 0:
            cap = min(quote_bal, budget)
        orders, warnings = orders_from_ai_text(
            result.get("content") or "",
            cfg,
            available_quote=cap,
        )
        for warn in warnings:
            print(f"  ! {warn}")
        self._write_orderlist(orders)
        summary = f"AI proposed {len(orders)} order(s)" + (
            f" ({len(warnings)} skipped)" if warnings else ""
        )
        self._emit_chat("assistant", summary, msg_type="propose")
        self._last_cycle = {
            "action": "ai_propose_orders",
            "orders": len(orders),
            "warnings": len(warnings),
            "placed": False,
        }
        return orders

    def _ai_rebalance_impl(self):
        p = self._progress_capture
        tb = self._tb
        llm = self.get_llm_config()
        p.set_phase(0, 35)
        tb.get_update(show=False)
        p.set_phase(35, 45)
        tb.market_list()
        p.set_phase(45, 55)
        try:
            tb.advice(show=False)
        except Exception:
            pass
        p.set_phase(55, 75)
        analysis = self._ai_analyze_impl()
        p.set_phase(75, 90)
        orders = self._ai_propose_impl()
        placed = False
        place_error = ""
        if llm.get("auto_place"):
            if orders:
                p.set_phase(90, 100)
                print("  auto_place enabled — placing AI orders via order_list")
                try:
                    tb.order_list(place=True)
                    placed = True
                except Exception as exc:
                    place_error = str(exc)
                    print(f"  auto_place failed: {exc}")
                    raise
            else:
                print("  auto_place on but no orders to place")
                p.set_phase(100, 100)
        else:
            print("  auto_place off — orders proposed only (use Place Orders to execute)")
            p.set_phase(100, 100)
        self._last_cycle = {
            "action": "ai_rebalance_cycle",
            "orders": len(orders or []),
            "placed": placed,
            "analysis_preview": (analysis or "")[:240],
            "place_error": place_error,
        }
        self._maybe_status_report(trigger="rebalance_done", force=True)

    def _ai_status_impl(self, trigger="heartbeat"):
        llm = self.get_llm_config()
        if not llm.get("enabled") or not llm.get("status_reports_enabled"):
            print("  status reports disabled")
            return None
        health = health_check(llm["base_url"], llm["api_key"], timeout=2.0)
        if not health.get("ok"):
            self._colibri_was_down = True
            print(f"  status skipped — Colibri offline: {health.get('detail')}")
            self._emit_chat(
                "system",
                f"Colibri offline ({health.get('detail')})",
                msg_type="status",
            )
            return None
        snapshot = self._snapshot_for_llm(extra={"trigger": trigger})
        result = chat_completions(
            messages_for_status(snapshot, trigger=trigger),
            base_url=llm["base_url"],
            api_key=llm["api_key"],
            model=llm["model"],
            enable_thinking=True,
            reasoning_effort="medium",
            max_tokens=1024,
            timeout=60.0,
        )
        if result.get("thinking"):
            self._file_log.write_line("ai_thinking", result["thinking"][:4000])
        content = result.get("content") or ""
        if not content:
            print("  empty status from Colibri")
            return None
        print(f"[status:{trigger}] {content}")
        self._emit_chat("assistant", content, msg_type="status")
        self._ai_store.mark_status_emitted()
        return content

    def _maybe_status_report(self, trigger="heartbeat", force=False):
        llm = self.get_llm_config()
        if not llm.get("enabled") or not llm.get("status_reports_enabled"):
            return
        if not force and not self._ai_store.should_emit_status(60.0):
            return
        try:
            if self._current_action:
                # Already inside an action (RLock held) — inline status
                self._ai_status_impl(trigger=trigger)
            else:
                with self._lock:
                    self._ai_status_impl(trigger=trigger)
        except Exception as exc:
            self._file_log.write_line("error", f"status report failed: {exc}")
            print(f"  status report skipped: {exc}")

    def _ai_chat_impl(self):
        text = self._pending_chat or ""
        self._pending_chat = None
        self._emit_chat("user", text, msg_type="chat")
        snapshot = self._snapshot_for_llm()
        result = self._llm_call(
            messages_for_chat(text, snapshot),
            enable_thinking=True,
            reasoning_effort="medium",
        )
        if result.get("thinking"):
            self._file_log.write_line("ai_thinking", result["thinking"][:4000])
        content = result.get("content") or "(geen antwoord)"
        print(content)
        self._emit_chat("assistant", content, msg_type="chat")

    def _sync_background_workers(self, llm=None):
        llm = normalize_llm_config(llm or self.get_llm_config())
        if llm.get("loop_enabled") and llm.get("enabled"):
            self.start_background_loop()
        else:
            self.stop_background_loop()
        if llm.get("status_reports_enabled") and llm.get("enabled"):
            self.start_status_heartbeat()
        else:
            self.stop_status_heartbeat()

    def start_background_loop(self):
        if self._loop_thread and self._loop_thread.is_alive():
            return
        self._loop_stop.clear()

        def worker():
            self.log_queue.put(("log", "Background AI loop started"))
            self._emit_chat("system", "Background loop gestart", msg_type="status")
            while not self._loop_stop.is_set():
                llm = self.get_llm_config()
                if not llm.get("loop_enabled") or not llm.get("enabled"):
                    break
                interval = max(1, int(llm.get("loop_interval_minutes") or 60)) * 60
                action = "ai_rebalance_cycle" if llm.get("enabled") else "start_bot"
                try:
                    health = health_check(llm["base_url"], llm["api_key"])
                    if not health.get("ok"):
                        self._colibri_was_down = True
                        self.log_queue.put(("log", f"Loop skip — Colibri down: {health.get('detail')}"))
                    else:
                        self.run_sync(action)
                except Exception as exc:
                    self.log_queue.put(("error", f"Loop cycle error: {exc}"))
                # Sleep in chunks so stop is responsive
                for _ in range(interval):
                    if self._loop_stop.wait(1.0):
                        break
            self.log_queue.put(("log", "Background AI loop stopped"))
            self._emit_chat("system", "Background loop gestopt", msg_type="status")

        self._loop_thread = threading.Thread(target=worker, daemon=True, name="tradebot-ai-loop")
        self._loop_thread.start()

    def stop_background_loop(self):
        self._loop_stop.set()

    def start_status_heartbeat(self):
        if self._status_thread and self._status_thread.is_alive():
            return
        self._status_stop.clear()

        def worker():
            while not self._status_stop.is_set():
                llm = self.get_llm_config()
                if not llm.get("status_reports_enabled") or not llm.get("enabled"):
                    break
                interval = max(1, int(llm.get("status_interval_minutes") or 15)) * 60
                try:
                    if not self.is_busy():
                        self.check_colibri_health()
                        self._maybe_status_report(trigger="heartbeat", force=False)
                except Exception as exc:
                    self.log_queue.put(("log", f"Status heartbeat skipped: {exc}"))
                for _ in range(interval):
                    if self._status_stop.wait(1.0):
                        break

        self._status_thread = threading.Thread(
            target=worker, daemon=True, name="tradebot-ai-status"
        )
        self._status_thread.start()

    def stop_status_heartbeat(self):
        self._status_stop.set()

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
            self._last_cycle = {
                "action": "place_orders",
                "placed": True,
                "orders": len(load_orderlist(BOT_DIR) or []),
            }
            self._maybe_status_report(trigger="place_done", force=True)

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

        def ai_analyze():
            p = prog()
            p.set_phase(0, 100)
            self._ai_analyze_impl()

        def ai_propose_orders():
            p = prog()
            p.set_phase(0, 100)
            self._ai_propose_impl()

        def ai_rebalance_cycle():
            self._ai_rebalance_impl()

        def ai_status_report():
            p = prog()
            p.set_phase(0, 100)
            trigger = "manual"
            if isinstance(self._last_cycle, dict) and self._last_cycle.get("_status_trigger"):
                trigger = self._last_cycle.pop("_status_trigger", "manual")
            self._ai_status_impl(trigger=trigger)

        def ai_chat():
            p = prog()
            p.set_phase(0, 100)
            self._ai_chat_impl()

        def colibri_list_models():
            p = prog()
            p.set_phase(0, 100)
            models = colibri_manager.list_models(on_line=self._colibri_line)
            self.log_queue.put(("colibri_models", models))
            print(f"  {len(models)} Colibri model(s) listed")

        def colibri_download():
            p = prog()
            p.set_phase(0, 100)
            model_id = self._pending_colibri_model or self.get_llm_config().get("colibri_model")
            self._pending_colibri_model = None
            if not model_id:
                raise ValueError("Select a Colibri model to download")
            print(f"  Downloading Colibri model {model_id}…")
            colibri_manager.download_model(model_id, on_line=self._colibri_line)
            cfg = self.load_config()
            llm = normalize_llm_config(cfg.get("llm"))
            llm["colibri_model"] = model_id
            cfg["llm"] = llm
            path = os.path.join(BOT_DIR, "config.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(cfg, handle, indent=4)
            self._emit_config()
            print(f"  Download/setup finished for {model_id}")

        def colibri_start():
            p = prog()
            p.set_phase(0, 100)
            print("  Starting Colibri…")
            colibri_manager.start_server(on_line=self._colibri_line)
            self.check_colibri_health()
            print("  Colibri start requested")

        def colibri_stop():
            p = prog()
            p.set_phase(0, 100)
            print("  Stopping Colibri…")
            colibri_manager.stop_server(on_line=self._colibri_line)
            print("  Colibri stop requested")

        def colibri_status():
            p = prog()
            p.set_phase(0, 100)
            info = colibri_manager.runtime_info()
            status = colibri_manager.status_json(on_line=self._colibri_line)
            self.log_queue.put(("colibri_status", {"info": info, "status": status}))
            print(json.dumps({"info": info, "status": status}, indent=2)[:2000])

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
            # Colibri AI
            "ai_analyze": ai_analyze,
            "ai_propose_orders": ai_propose_orders,
            "ai_rebalance_cycle": ai_rebalance_cycle,
            "ai_status_report": ai_status_report,
            "ai_chat": ai_chat,
            # Bundled Colibri lifecycle
            "colibri_list_models": colibri_list_models,
            "colibri_download": colibri_download,
            "colibri_start": colibri_start,
            "colibri_stop": colibri_stop,
            "colibri_status": colibri_status,
        }

    def run_colibri_download_async(self, model_id, callback=None):
        self._pending_colibri_model = (model_id or "").strip()
        return self.run_async("colibri_download", callback=callback)