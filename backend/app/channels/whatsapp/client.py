"""WhatsApp Cloud API client for media download/upload and messaging."""

import asyncio
import logging
from typing import Any

import httpx

from ...core.config import Settings, get_settings
from ...core.http_client import get_http_client

log = logging.getLogger("whatsapp.client")


class WhatsAppAPIError(Exception):
    """Raised when an operation on WhatsApp Cloud API fails."""


def _auth_headers(settings: Settings) -> dict[str, str]:
    if not settings.WHATSAPP_ACCESS_TOKEN:
        raise WhatsAppAPIError("WHATSAPP_ACCESS_TOKEN is not configured.")
    return {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    max_retries: int = 3,
    **kwargs: Any,
) -> httpx.Response:
    """Performs an HTTP request with exponential backoff on 429/5xx."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            r = await client.request(method, url, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504):
                log.warning("WhatsApp API %s failed with %d (attempt %d/%d)", method, r.status_code, attempt + 1, max_retries)
                last_err = WhatsAppAPIError(f"WhatsApp API HTTP {r.status_code}: {r.text[:200]}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r
        except httpx.TransportError as e:
            log.warning("WhatsApp API transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            last_err = WhatsAppAPIError(f"Transport error: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))
        except httpx.HTTPStatusError as e:
            log.error("WhatsApp API status error: %s - %s", e.response.status_code, e.response.text[:300])
            raise WhatsAppAPIError(f"WhatsApp API error {e.response.status_code}: {e.response.text[:300]}") from e

    raise last_err or WhatsAppAPIError("WhatsApp API request failed after max retries.")


async def download_media(
    media_id: str,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> bytes:
    """Downloads voice note media from WhatsApp Graph API, validating size via streaming."""
    cfg = settings or get_settings()
    c = client or get_http_client()

    # Step 1: Query media metadata to get download URL
    meta_url = f"{cfg.wa_graph}/{media_id}"
    meta_res = await _request_with_retry(c, "GET", meta_url, headers=_auth_headers(cfg), timeout=60.0)
    meta_data = meta_res.json()
    file_url = meta_data.get("url")
    if not file_url:
        raise WhatsAppAPIError(f"No download URL in media metadata: {meta_data}")

    # Check file size if available in metadata
    file_size = meta_data.get("file_size", 0)
    max_bytes = cfg.AUDIO_MAX_MB * 1024 * 1024
    if file_size and file_size > max_bytes:
        raise WhatsAppAPIError(f"Audio media size ({file_size} bytes) exceeds limit ({max_bytes} bytes).")

    # Step 2: Download raw binary media in streaming mode with size guard
    chunks: list[bytes] = []
    downloaded = 0
    async with c.stream("GET", file_url, headers=_auth_headers(cfg), timeout=60.0) as stream_resp:
        stream_resp.raise_for_status()
        async for chunk in stream_resp.aiter_bytes(chunk_size=16384):
            downloaded += len(chunk)
            if downloaded > max_bytes:
                raise WhatsAppAPIError(
                    f"Audio media size exceeds maximum allowed limit of {cfg.AUDIO_MAX_MB} MB."
                )
            chunks.append(chunk)

    return b"".join(chunks)


async def upload_audio(
    ogg_bytes: bytes,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Uploads OGG/Opus audio to WhatsApp Cloud API, returning the media ID."""
    cfg = settings or get_settings()
    c = client or get_http_client()
    url = f"{cfg.wa_graph}/{cfg.WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = _auth_headers(cfg)
    data = {"messaging_product": "whatsapp", "type": "audio/ogg"}
    files = {"file": ("reply.ogg", ogg_bytes, "audio/ogg")}

    res = await _request_with_retry(c, "POST", url, headers=headers, data=data, files=files, timeout=60.0)
    return res.json()["id"]


async def _send(
    payload: dict[str, Any],
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Sends a message payload via WhatsApp Graph API."""
    cfg = settings or get_settings()
    c = client or get_http_client()
    url = f"{cfg.wa_graph}/{cfg.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {**_auth_headers(cfg), "Content-Type": "application/json"}
    full_payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        **payload,
    }
    res = await _request_with_retry(c, "POST", url, headers=headers, json=full_payload)
    return res.json()


async def send_text(
    to: str,
    body: str,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Sends a text message (truncated safely to WhatsApp 4096 limit)."""
    return await _send({"to": to, "type": "text", "text": {"body": body[:4000]}}, settings=settings, client=client)


async def send_audio(
    to: str,
    media_id: str,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Sends a voice message using an uploaded media ID."""
    return await _send({"to": to, "type": "audio", "audio": {"id": media_id}}, settings=settings, client=client)
