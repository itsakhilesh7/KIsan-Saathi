"""Parses and normalizes WhatsApp Cloud API webhook payloads."""

from typing import Any


def extract_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flattens a WhatsApp webhook payload into normalized message dicts.

    Ignores delivery statuses, receipts, and system events.
    """
    out: list[dict[str, Any]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for m in value.get("messages", []) or []:
                msg_type = m.get("type")
                item: dict[str, Any] = {
                    "id": m.get("id"),
                    "from": m.get("from"),
                    "type": msg_type,
                    "timestamp": m.get("timestamp"),
                }
                if msg_type == "text":
                    item["text"] = m.get("text", {}).get("body", "")
                elif msg_type == "audio":
                    audio_info = m.get("audio", {})
                    item["media_id"] = audio_info.get("id")
                    item["mime_type"] = audio_info.get("mime_type")
                out.append(item)
    return out

