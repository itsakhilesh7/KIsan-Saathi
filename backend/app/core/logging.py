"""Structured logging and privacy protection for Kisan Saathi.

Strict rules enforced:
- Never log raw phone numbers: salted SHA-256 hash only.
- Never log secrets, authorization tokens, or API keys.
- Never log raw audio bytes.
- Request-ID tracking across all stages.
"""

import hashlib
import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

# Context variable for tracing request IDs across async boundaries
_REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")

# Sensitive key substrings that must NEVER be logged
REDACTED_KEYS = {"key", "secret", "token", "auth", "password", "credential"}


def get_request_id() -> str:
    """Returns the current request ID or generates a new one if unset."""
    req_id = _REQUEST_ID_CTX.get()
    if not req_id:
        req_id = str(uuid.uuid4())
        _REQUEST_ID_CTX.set(req_id)
    return req_id


def set_request_id(request_id: str) -> None:
    """Sets the request ID for the current context."""
    _REQUEST_ID_CTX.set(request_id)


def hash_phone(phone: str, salt: str) -> str:
    """Produces a secure salted SHA-256 hash of a phone number (16 hex chars).

    Raw phone numbers must NEVER be written to logs or disk.
    """
    if not phone:
        return "anonymous"
    salted = f"{salt}:{phone.strip()}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()[:16]


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON, scrubbing sensitive fields."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = _REQUEST_ID_CTX.get() or getattr(record, "request_id", "")
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": req_id,
        }

        # Include extra attributes, scrubbing any sensitive keys
        if hasattr(record, "__dict__"):
            for k, v in record.__dict__.items():
                if k not in (
                    "args", "asctime", "created", "exc_info", "exc_text", "filename",
                    "funcName", "id", "levelname", "levelno", "lineno", "module",
                    "msecs", "message", "msg", "name", "pathname", "process",
                    "processName", "relativeCreated", "stack_info", "thread",
                    "threadName", "request_id",
                ):
                    if any(secret in k.lower() for secret in REDACTED_KEYS):
                        log_entry[k] = "[REDACTED]"
                    elif isinstance(v, bytes):
                        log_entry[k] = f"<bytes: {len(v)} bytes>"
                    else:
                        log_entry[k] = v

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """Initializes the structured JSON logger."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers on re-init
    root_logger.handlers = [handler]
