"""Tests for structured logging."""

import json
import logging

import pytest

from infrastructure.logging.setup import StructuredFormatter, log_auth_event


def test_structured_formatter_outputs_json() -> None:
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="reps.auth",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="User logged in",
        args=(),
        exc_info=None,
    )
    record.event = "login"
    record.success = True
    record.user_id = "user-1"
    record.role = "coach"

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "User logged in"
    assert payload["event"] == "login"
    assert payload["success"] is True
    assert payload["user_id"] == "user-1"
    assert payload["role"] == "coach"


def test_log_auth_event_uses_warning_on_failure(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("reps.test.auth")

    with caplog.at_level(logging.WARNING, logger="reps.test.auth"):
        log_auth_event(
            logger,
            event="login",
            success=False,
            message="Login failed",
        )

    assert any(record.message == "Login failed" for record in caplog.records)
