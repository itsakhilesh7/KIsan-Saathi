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
import re
import sys
import uuid
from contextvars import ContextVar
from typing import Any

# Context variable for tracing request IDs across async boundaries
_REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")

# Sensitive key substrings that must NEVER be logged
REDACTED_KEYS = {"key", "secret", "token", "auth", "password", "credential"}

# Pattern for Telegram Bot API tokens in URLs (/bot<token>/)
TELEGRAM_TOKEN_REGEX = re.compile(r"/bot[0-9]+:[A-Za-z0-9_-]+", re.IGNORECASE)
# Pattern for API keys in URL query parameters or headers (api-key=..., apikey=...)
API_KEY_PARAM_REGEX = re.compile(r"(?i)(api[-_]?key)=([a-zA-Z0-9_\-]+)")


def _sanitize_string(text: str) -> str:
    """Sanitizes text by stripping bot tokens and API keys."""
    if not isinstance(text, str):
        return text
    s = TELEGRAM_TOKEN_REGEX.sub("/bot[REDACTED]", text)
    return API_KEY_PARAM_REGEX.sub(r"\1=[REDACTED]", s)


class TelegramTokenRedactionFilter(logging.Filter):
    """Redacts Telegram Bot tokens and API keys from log records to prevent secret leakage."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _sanitize_string(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (_sanitize_string(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    (_sanitize_string(a) if isinstance(a, str) else a)
                    for a in record.args
                )
        return True


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
        raw_msg = record.getMessage()
        sanitized_msg = _sanitize_string(raw_msg)

        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_msg,
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
                    elif isinstance(v, str):
                        log_entry[k] = _sanitize_string(v)
                    else:
                        log_entry[k] = v

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """Initializes the structured JSON logger with security filters."""
    redaction_filter = TelegramTokenRedactionFilter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(redaction_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    root_logger.addFilter(redaction_filter)

    # Silence verbose HTTP client loggers that log request URLs with tokens
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Alias for backward compatibility
configure_logging = setup_logging
