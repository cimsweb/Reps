"""Structured application logging."""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if hasattr(record, "success"):
            payload["success"] = record.success
        if hasattr(record, "user_id"):
            payload["user_id"] = record.user_id
        if hasattr(record, "role"):
            payload["role"] = record.role
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


def log_auth_event(
    logger: logging.Logger,
    event: str,
    *,
    success: bool,
    user_id: str | None = None,
    role: str | None = None,
    message: str,
) -> None:
    """Log authentication-related events in a uniform format."""
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        message,
        extra={"event": event, "success": success, "user_id": user_id, "role": role},
    )


def log_authorization_check(
    logger: logging.Logger,
    *,
    success: bool,
    user_id: str | None,
    role: str | None,
    route: str,
) -> None:
    """Log role checks on protected routes."""
    log_auth_event(
        logger,
        event="authorization_check",
        success=success,
        user_id=user_id,
        role=role,
        message=f"Authorization check for route '{route}'",
    )
