from __future__ import annotations

import logging

import app


def test_http_transport_loggers_do_not_emit_info_request_urls():
    """OAuth-bearing provider URLs must not become ordinary INFO runtime logs."""
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING


def test_transport_log_guard_survives_verbose_root_logging():
    root = logging.getLogger()
    previous = root.level
    try:
        root.setLevel(logging.DEBUG)
        assert logging.getLogger("httpx").isEnabledFor(logging.INFO) is False
        assert logging.getLogger("httpcore").isEnabledFor(logging.INFO) is False
    finally:
        root.setLevel(previous)
