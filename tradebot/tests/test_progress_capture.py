"""Tests for GUI progress capture and log streaming."""

import queue

from gui.log_stream import ProgressCapture, QueueLogWriter


def test_progress_capture_maps_unit_interval_to_percent():
    log_queue = queue.Queue()
    cap = ProgressCapture(log_queue)
    cap(0.5)
    log_tag, log_line = log_queue.get_nowait()
    assert log_tag == "log"
    assert "Updating:" in log_line
    assert "50%" in log_line
    tag, value = log_queue.get_nowait()
    assert tag == "progress"
    assert value == 50.0


def test_progress_capture_phase_scaling():
    log_queue = queue.Queue()
    cap = ProgressCapture(log_queue)
    cap.set_phase(60, 85)
    cap(0.5)
    log_queue.get_nowait()  # log line
    tag, value = log_queue.get_nowait()
    assert tag == "progress"
    assert value == 72.5


def test_queue_log_writer_carriage_return():
    log_queue = queue.Queue()
    writer = QueueLogWriter(log_queue)
    writer.write("\r  Build orders: 4/18")
    writer.flush()
    tag, line = log_queue.get_nowait()
    assert tag == "log"
    assert "4/18" in line
