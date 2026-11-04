"""Tests for Telegram logging redaction and runner module import (test-first)."""

import importlib
import io
import logging

from backend.app.core.logging import StructuredJsonFormatter, TelegramTokenRedactionFilter, setup_logging


def test_run_telegram_polling_import():
    """Verify backend/scripts/run_telegram_polling.py imports cleanly without ImportError."""
    mod = importlib.import_module("backend.scripts.run_telegram_polling")
    assert hasattr(mod, "main")
    assert callable(mod.main)


def test_setup_logging_quiets_httpx_and_httpcore():
    """setup_logging must quiet httpx and httpcore loggers to WARNING to avoid URL leak."""
    setup_logging()
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING


def test_telegram_token_redaction_filter():
    """Filter must redact /bot<token>/ patterns in log record message and args."""
    fake_token = "987654321:ABCdefGHIjklMNOpqrsTUV_wxyz123"
    raw_url = f"https://api.telegram.org/bot{fake_token}/getUpdates"

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="HTTP Request: GET %s",
        args=(raw_url,),
        exc_info=None,
    )

    filt = TelegramTokenRedactionFilter()
    filt.filter(record)

    formatted_msg = record.getMessage()
    assert fake_token not in formatted_msg
    assert "/bot[REDACTED]/getUpdates" in formatted_msg


def test_captured_log_never_emits_bot_token():
    """End-to-end log emission test verifying bot token is never in final output."""
    fake_token = "123456789:ABCdefGHIjklMNOpqrsTUV_wxyz123"

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(TelegramTokenRedactionFilter())

    logger = logging.getLogger("test_tg_redaction")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    logger.propagate = False

    logger.info("Connecting to https://api.telegram.org/bot%s/sendMessage?chat_id=123", fake_token)
    logger.info("Direct url: https://api.telegram.org/bot%s/getMe", fake_token)

    output = stream.getvalue()

    assert fake_token not in output
    assert "/bot[REDACTED]/sendMessage" in output
    assert "/bot[REDACTED]/getMe" in output
