"""Telegram Bot API channel client for text and voice message handling.

Implements ChannelClient interface:
- download_media: getFile metadata + streaming file download with size guard
- send_text: sendMessage (up to 4096 chars)
- send_audio_bytes: sendVoice with OGG/Opus mono bytes
"""

import asyncio
import logging
from typing import Any

import httpx

from ...core.config import Settings, get_settings
from ...core.http_client import get_http_client

log = logging.getLogger("telegram.client")

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramAPIError(Exception):
    """Raised when an operation on the Telegram Bot API fails."""


class TelegramChannelClient:
    """Telegram Bot API implementation conforming to ChannelClient protocol."""

    channel_name: str = "telegram"

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.settings = settings or get_settings()
        self._http_client = http_client

    def _get_client(self) -> httpx.AsyncClient:
        return self._http_client or get_http_client()

    def _get_bot_token(self) -> str:
        token = self.settings.TELEGRAM_BOT_TOKEN.strip()
        if not token:
            raise TelegramAPIError("TELEGRAM_BOT_TOKEN is not configured in Settings or backend/.env.")
        return token

    def _base_url(self) -> str:
        token = self._get_bot_token()
        return f"{TELEGRAM_API_BASE}/bot{token}"

    def _file_url(self, file_path: str) -> str:
        token = self._get_bot_token()
        return f"{TELEGRAM_API_BASE}/file/bot{token}/{file_path}"

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> httpx.Response:
        """Executes an HTTP request with exponential backoff on 429/5xx, redacting token from logs."""
        client = self._get_client()
        last_err: Exception | None = None

        for attempt in range(max_retries):
            try:
                r = await client.request(method, url, **kwargs)
                if r.status_code in (429, 500, 502, 503, 504):
                    log.warning(
                        "Telegram API request failed with %d (attempt %d/%d)",
                        r.status_code,
                        attempt + 1,
                        max_retries,
                    )
                    last_err = TelegramAPIError(f"Telegram API HTTP {r.status_code}")
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r
            except httpx.TransportError as e:
                log.warning("Telegram API transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
                last_err = TelegramAPIError(f"Transport error: {e}")
                await asyncio.sleep(1.5 * (attempt + 1))
            except httpx.HTTPStatusError as e:
                log.error("Telegram API HTTP status error: %d", e.response.status_code)
                raise TelegramAPIError(f"Telegram API error {e.response.status_code}") from e

        raise last_err or TelegramAPIError("Telegram API request failed after max retries.")

    async def download_media(self, media_id: str) -> bytes:
        """Downloads voice audio file via getFile and streaming HTTP download with AUDIO_MAX_MB limit."""
        client = self._get_client()
        cfg = self.settings
        max_bytes = cfg.AUDIO_MAX_MB * 1024 * 1024

        # Step 1: Query getFile to retrieve file_path
        get_file_url = f"{self._base_url()}/getFile"
        r = await self._request_with_retry("GET", get_file_url, params={"file_id": media_id}, timeout=30.0)
        body = r.json()
        if not body.get("ok", False):
            raise TelegramAPIError(f"Telegram getFile returned error: {body.get('description', 'Unknown error')}")

        result = body.get("result", {})
        file_path = result.get("file_path")
        if not file_path:
            raise TelegramAPIError(f"No file_path returned in Telegram getFile response for {media_id}")

        file_size = result.get("file_size", 0)
        if file_size and file_size > max_bytes:
            raise TelegramAPIError(f"Telegram audio file size ({file_size} B) exceeds maximum {cfg.AUDIO_MAX_MB} MB")

        # Step 2: Download raw audio file in streaming chunks
        download_url = self._file_url(file_path)
        chunks: list[bytes] = []
        downloaded = 0

        async with client.stream("GET", download_url, timeout=60.0) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes(chunk_size=16384):
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    raise TelegramAPIError(
                        f"Telegram audio download exceeded maximum limit of {cfg.AUDIO_MAX_MB} MB."
                    )
                chunks.append(chunk)

        return b"".join(chunks)

    async def send_text(self, to: str, text: str) -> dict[str, Any]:
        """Sends a text message using sendMessage (truncated safely to 4000 characters)."""
        url = f"{self._base_url()}/sendMessage"
        payload = {
            "chat_id": str(to),
            "text": text[:4000],
        }
        res = await self._request_with_retry("POST", url, json=payload, timeout=30.0)
        return res.json()

    async def send_audio_bytes(self, to: str, audio_bytes: bytes) -> dict[str, Any]:
        """Sends a voice note using sendVoice (renders as native waveform voice bubble on Telegram)."""
        url = f"{self._base_url()}/sendVoice"
        data = {"chat_id": str(to)}
        files = {"voice": ("voice.ogg", audio_bytes, "audio/ogg")}
        res = await self._request_with_retry("POST", url, data=data, files=files, timeout=60.0)
        return res.json()
