"""Telegram Webhook endpoint for inbound updates."""

import logging
import secrets
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request

from ...core.config import Settings, get_settings
from .poller import process_update

log = logging.getLogger("telegram.webhook")

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook/{webhook_path}")
async def receive_telegram_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Receives inbound Telegram update, verifies path and secret token, and dispatches in background."""
    # 1. Validate path
    expected_path = settings.TELEGRAM_WEBHOOK_PATH.strip()
    if not expected_path or not secrets.compare_digest(webhook_path, expected_path):
        log.warning("Telegram webhook received on unrecognized path: '%s'", webhook_path)
        raise HTTPException(status_code=404, detail="Webhook path not found")

    # 2. Validate secret token header if configured
    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET.strip()
    if expected_secret:
        if not x_telegram_bot_api_secret_token or not secrets.compare_digest(
            x_telegram_bot_api_secret_token, expected_secret
        ):
            log.warning("Telegram webhook received with invalid secret token")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    # 3. Parse JSON body
    try:
        body = await request.json()
    except Exception as e:
        log.warning("Invalid JSON received on Telegram webhook: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 4. Enqueue background processing so Telegram gets immediate 200 OK
    background_tasks.add_task(process_update, update=body, settings=settings)

    return {"ok": True}
