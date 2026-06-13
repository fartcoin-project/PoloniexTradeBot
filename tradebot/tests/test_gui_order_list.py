"""order_list must run once in GUI mode (preview, buy, and sell API calls)."""

import queue
import types

from gui.service import BotService


def _make_fake_tradebot(*, interactive=True):
    state = {"interactive": interactive}
    tb = types.SimpleNamespace()
    loop_count = {"n": 0}

    def set_interactive_menu(enabled):
        state["interactive"] = bool(enabled)

    def orig_order_list(place=False):
        while True:
            loop_count["n"] += 1
            if loop_count["n"] > 5:
                raise AssertionError("order_list loop did not stop")
            if place:
                tb.completed()
            else:
                tb.menu()
            if not state["interactive"]:
                break

    tb.order_list = orig_order_list
    tb.set_interactive_menu = set_interactive_menu
    tb.set_cancel_check = lambda fn: None
    tb.completed = lambda: None
    tb.menu = lambda: None
    tb.advice = lambda show=False: None
    return tb, loop_count, state


def test_gui_patch_disables_interactive_menu():
    service = BotService(queue.Queue())
    tb, loop_count, state = _make_fake_tradebot()
    service._patch_for_gui(tb)

    assert state["interactive"] is False


def test_gui_order_list_preview_runs_once():
    service = BotService(queue.Queue())
    tb, loop_count, _state = _make_fake_tradebot()
    service._patch_for_gui(tb)

    tb.order_list(place=False)

    assert loop_count["n"] == 1


def test_gui_order_list_place_runs_once():
    service = BotService(queue.Queue())
    tb, loop_count, _state = _make_fake_tradebot()
    service._tb = tb
    service._patch_for_gui(tb)

    tb.order_list(place=True)

    assert loop_count["n"] == 1


def test_non_interactive_place_does_not_repeat_after_completed():
    tb, loop_count, state = _make_fake_tradebot(interactive=False)

    tb.order_list(place=True)

    assert loop_count["n"] == 1
