"""WhatsApp Cloud API helpers: signature check, payload parsing, media in/out, sending."""
import hashlib
import hmac
import logging

import httpx

from . import config

log = logging.getLogger("whatsapp")


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    """Meta signs each webhook POST with HMAC-SHA256 using the app secret."""
    if not config.META_APP_SECRET:
        log.warning("META_APP_SECRET not set: skipping signature check (dev only!)")
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(config.META_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def extract_messages(payload: dict) -> list[dict]:
    """Flatten a webhook payload into simple message dicts. Ignores delivery statuses."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in (change.get("value", {}).get("messages") or []):
                item = {"id": m.get("id"), "from": m.get("from"), "type": m.get("type")}
                if item["type"] == "text":
                    item["text"] = m.get("text", {}).get("body", "")
                elif item["type"] == "audio":
                    item["media_id"] = m.get("audio", {}).get("id")
                out.append(item)
    return out


def _auth() -> dict:
    return {"Authorization": f"Bearer {config.WA_ACCESS_TOKEN}"}


async def download_media(media_id: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        meta = await client.get(f"{config.WA_GRAPH}/{media_id}", headers=_auth())
        meta.raise_for_status()
        url = meta.json()["url"]
        f = await client.get(url, headers=_auth())
        f.raise_for_status()
        return f.content


async def upload_audio(ogg_bytes: bytes) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{config.WA_GRAPH}/{config.WA_PHONE_NUMBER_ID}/media",
            headers=_auth(),
            data={"messaging_product": "whatsapp", "type": "audio/ogg"},
            files={"file": ("reply.ogg", ogg_bytes, "audio/ogg")},
        )
        r.raise_for_status()
        return r.json()["id"]


async def _send(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{config.WA_GRAPH}/{config.WA_PHONE_NUMBER_ID}/messages",
            headers={**_auth(), "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "recipient_type": "individual", **payload},
        )
        if r.status_code >= 400:
            log.error("WhatsApp send failed %s: %s", r.status_code, r.text[:300])
        r.raise_for_status()
        return r.json()


async def send_text(to: str, body: str) -> dict:
    return await _send({"to": to, "type": "text", "text": {"body": body[:4000]}})


async def send_audio(to: str, media_id: str) -> dict:
    return await _send({"to": to, "type": "audio", "audio": {"id": media_id}})
