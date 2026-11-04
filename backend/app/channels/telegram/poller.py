"""Telegram Bot long-polling service for receiving and dispatching updates."""

import asyncio
import logging
from typing import Any

import httpx

from ...core.config import Settings, get_settings
from ...core.http_client import get_http_client
from ...repositories.deduplication import DeduplicationRepository, SQLiteDeduplicationRepository
from ...services.orchestrator import handle_incoming_message
from .client import TelegramChannelClient

log = logging.getLogger("telegram.poller")

_dedup_repo: DeduplicationRepository | None = None


def get_dedup_repo() -> DeduplicationRepository:
    """Returns the deduplication repository, lazily initialized."""
    global _dedup_repo
    if _dedup_repo is None:
        _dedup_repo = SQLiteDeduplicationRepository()
    return _dedup_repo


def parse_update(update: dict[str, Any]) -> dict[str, Any] | None:
    """Parses a raw Telegram Update into the normalized message structure."""
    update_id = update.get("update_id")
    if not update_id:
        return None

    message = update.get("message") or update.get("edited_message")
    if not message:
        return None

    sender = message.get("from") or {}
    user_id = str(sender.get("id") or "")
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id") or user_id)

    if not chat_id:
        return None

    # Check for native voice note
    voice = message.get("voice")
    if voice and voice.get("file_id"):
        return {
            "update_id": update_id,
            "from": chat_id,
            "user_id": user_id,
            "type": "audio",
            "media_id": voice["file_id"],
            "mime_type": voice.get("mime_type", "audio/ogg"),
            "duration": voice.get("duration"),
        }

    # Check for general audio file attachment
    audio = message.get("audio")
    if audio and audio.get("file_id"):
        return {
            "update_id": update_id,
            "from": chat_id,
            "user_id": user_id,
            "type": "audio",
            "media_id": audio["file_id"],
            "mime_type": audio.get("mime_type", "audio/ogg"),
            "duration": audio.get("duration"),
        }

    # Check for text message
    text = message.get("text")
    if text:
        return {
            "update_id": update_id,
            "from": chat_id,
            "user_id": user_id,
            "type": "text",
            "text": text,
        }

    # Non-text/audio (photos, documents, stickers, etc.)
    return {
        "update_id": update_id,
        "from": chat_id,
        "user_id": user_id,
        "type": "unsupported",
    }


async def process_update(
    update: dict[str, Any],
    settings: Settings,
    client: TelegramChannelClient | None = None,
    dedup_repo: DeduplicationRepository | None = None,
) -> bool:
    """Processes a single Telegram update with deduplication and pipeline dispatch."""
    parsed = parse_update(update)
    if not parsed:
        return False

    update_id = parsed["update_id"]
    dedup = dedup_repo or get_dedup_repo()
    dedup_key = f"tg_{update_id}"

    if dedup.is_duplicate(dedup_key):
        log.debug("Skipping duplicate Telegram update_id=%s", update_id)
        return False

    tg_client = client or TelegramChannelClient(settings=settings)
    await handle_incoming_message(parsed, settings=settings, client=tg_client)
    return True


async def run_polling(
    settings: Settings | None = None,
    client: TelegramChannelClient | None = None,
    poll_timeout: int = 30,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Long-polling loop for Telegram Bot updates (getUpdates)."""
    cfg = settings or get_settings()
    tg_client = client or TelegramChannelClient(settings=cfg)
    token = tg_client._get_bot_token()
    base_url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset: int | None = None
    http_c = get_http_client()

    log.info("Starting Telegram long-polling loop (timeout=%ds)...", poll_timeout)

    while True:
        if stop_event and stop_event.is_set():
            log.info("Telegram polling stop event received, exiting loop.")
            break

        params: dict[str, Any] = {"timeout": poll_timeout}
        if offset is not None:
            params["offset"] = offset

        try:
            r = await http_c.get(base_url, params=params, timeout=poll_timeout + 10.0)
            if r.status_code != 200:
                log.warning("Telegram getUpdates returned status %d: %s", r.status_code, r.text[:200])
                await asyncio.sleep(2.0)
                continue

            data = r.json()
            if not data.get("ok"):
                log.error("Telegram getUpdates error: %s", data.get("description"))
                await asyncio.sleep(3.0)
                continue

            updates = data.get("result", [])
            for u in updates:
                u_id = u.get("update_id")
                if u_id is not None:
                    offset = u_id + 1
                try:
                    await process_update(u, settings=cfg, client=tg_client)
                except Exception as ex:
                    log.exception("Error processing update %s: %s", u_id, ex)

        except asyncio.CancelledError:
            log.info("Telegram polling loop cancelled.")
            break
        except httpx.TransportError as te:
            log.warning("Network transport error during getUpdates: %s", te)
            await asyncio.sleep(2.0)
        except Exception as e:
            log.exception("Unexpected error in Telegram polling loop: %s", e)
            await asyncio.sleep(2.0)
