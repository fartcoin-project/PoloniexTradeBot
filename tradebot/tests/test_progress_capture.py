"""Tests for GUI progress capture and log streaming."""

import queue

from gui.log_stream import (
    LOG_ORDER_BUY,
    LOG_ORDER_SELL,
    LOG_ORDER_TEST,
    ProgressCapture,
    QueueLogWriter,
    format_order_log_html,
    strip_ansi,
)


def test_progress_capture_maps_unit_interval_to_percent():
    log_queue = queue.Queue()
    cap = ProgressCapture(log_queue)
    cap(0.5)
    tag, value = log_queue.get_nowait()
    assert tag == "progress"
    assert value == 50.0
    assert log_queue.empty()


def test_progress_capture_phase_scaling():
    log_queue = queue.Queue()
    cap = ProgressCapture(log_queue)
    cap.set_phase(60, 85)
    cap(0.5)
    tag, value = log_queue.get_nowait()
    assert tag == "progress"
    assert value == 72.5
    assert log_queue.empty()


def test_queue_log_writer_carriage_return():
    log_queue = queue.Queue()
    writer = QueueLogWriter(log_queue)
    writer.write("\r  Build orders: 4/18")
    writer.flush()
    tag, line = log_queue.get_nowait()
    assert tag == "log"
    assert "4/18" in line


def test_format_order_log_html_colors_buy_and_total():
    line = "          BUY      100.00000000 ADA       0.00001000     ₿ 0.**1*0000     Preview"
    html = format_order_log_html(line)
    assert html is not None
    assert LOG_ORDER_BUY in html
    assert ">BUY<" in html or ">BUY</span>" in html
    assert "₿ 0.**1*0000" in html


def test_format_order_log_html_colors_sell():
    line = "         SELL        0.50000000 ETH       0.05000000     ₿ 0.*25*0000     Preview"
    html = format_order_log_html(line)
    assert html is not None
    assert LOG_ORDER_SELL in html
    assert "SELL" in html


def test_format_order_log_html_colors_test_mode():
    line = "         TEST      100.00000000 ADA       0.00001000     ₿ 0.**1*0000      Test"
    html = format_order_log_html(line)
    assert html is not None
    assert LOG_ORDER_TEST in html
    assert "TEST" in html


def test_format_order_log_html_total_cost_test():
    line = "  Total cost (test): ₿ 0.02600000"
    html = format_order_log_html(line)
    assert html is not None
    assert LOG_ORDER_TEST in html
    assert "₿ 0.02600000" in html


def test_format_order_log_html_ignores_unrelated_lines():
    assert format_order_log_html("orders: 2 list created 0 seconds ago") is None
    assert format_order_log_html(strip_ansi("\x1b[1;31mhello\x1b[0;0m")) is None
