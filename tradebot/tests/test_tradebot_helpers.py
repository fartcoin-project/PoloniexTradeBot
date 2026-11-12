"""Tests for pure helpers in tradebot.py."""

import io
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from api_compat import MIN_ORDER_BTC, OperationCancelled
import tradebot


class TestCancelAndSleep:
    def setup_method(self):
        tradebot.set_cancel_check(None)
        tradebot.set_interactive_menu(True)

    def test_set_interactive_menu_controls_order_list_mode(self):
        tradebot.set_interactive_menu(False)
        assert tradebot._interactive_menu is False
        tradebot.set_interactive_menu(True)
        assert tradebot._interactive_menu is True

    def test_abort_if_cancelled_raises_when_check_returns_true(self):
        tradebot.set_cancel_check(lambda: True)
        with pytest.raises(OperationCancelled, match="Emergency stop"):
            tradebot.abort_if_cancelled()

    def test_abort_if_cancelled_no_op_when_not_set(self):
        tradebot.set_cancel_check(None)
        tradebot.abort_if_cancelled()

    def test_abort_if_cancelled_no_op_when_check_false(self):
        tradebot.set_cancel_check(lambda: False)
        tradebot.abort_if_cancelled()

    def test_gui_sleep_respects_cancel(self):
        tradebot.set_cancel_check(lambda: True)
        with pytest.raises(OperationCancelled):
            tradebot.gui_sleep(1.0)

    def test_gui_sleep_completes_when_not_cancelled(self):
        tradebot.set_cancel_check(None)
        start = time.time()
        tradebot.gui_sleep(0.05)
        assert time.time() - start >= 0.04


class TestProgressBar:
    def test_progress_bar_format_at_half(self):
        out = io.StringIO()
        bar = tradebot.ProgressBar(10, width=10, fmt=tradebot.ProgressBar.FULL, output=out)
        bar.current = 5
        bar()
        line = out.getvalue()
        assert "5/10" in line
        assert "=" in line

    def test_progress_bar_done_prints_newline(self):
        out = io.StringIO()
        bar = tradebot.ProgressBar(4, output=out)
        bar.done()
        assert out.getvalue().endswith("\n")


class TestUpdateProgress:
    def test_clamps_progress_to_unit_interval(self, capsys):
        tradebot.update_progress(-5)
        captured = capsys.readouterr().out
        assert "0.0%" in captured or "0%" in captured

        tradebot.update_progress(2.0)
        captured = capsys.readouterr().out
        assert "100" in captured


class TestStringAndTimeHelpers:
    def test_string2list_splits_on_spaces(self):
        assert tradebot.string2list("DOGE ETH BTC") == ["DOGE", "ETH", "BTC"]

    def test_get_time_default_format(self):
        with patch.object(tradebot, "datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 13, 15, 30, 45)
            assert tradebot.get_time() == "2026/06/13 15:30:45"

    def test_get_time_list_format(self):
        with patch.object(tradebot, "datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 13, 15, 30, 45)
            assert tradebot.get_time(time_list=True) == "2026 06 13 15 30 45"


class TestTestMode:
    def test_is_test_mode_requires_buy_and_sell_false(self, tradebot_env):
        tradebot.args.buy = None
        tradebot.args.sell = False
        assert tradebot.is_test_mode() is False
        tradebot.args.buy = False
        tradebot.args.sell = False
        assert tradebot.is_test_mode() is True
        tradebot.args.buy = True
        tradebot.args.sell = False
        assert tradebot.is_test_mode() is False


class TestHelpText:
    def test_help_text_documents_cli_and_menu(self):
        text = tradebot.help_text()
        assert "--budget" in text
        assert "Build orders" in text
        assert "Place orders" in text


class TestReloadExchange:
    def test_reload_exchange_returns_polo_instance(self, mock_polo):
        result = tradebot.reload_exchange()
        assert result is mock_polo
