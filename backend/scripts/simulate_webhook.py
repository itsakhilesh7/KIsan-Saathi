"""Simulate inbound WhatsApp audio webhook with HMAC-SHA256 signature.

Allows end-to-end testing of FastAPI /webhook route, signature verification,
deduplication, and background task dispatch locally without Meta Developer Portal.
DOES NOT call Meta APIs.

Usage:
    python -m backend.scripts.simulate_webhook
    python -m backend.scripts.simulate_webhook --url http://localhost:8000/webhook
"""

import argparse
import hashlib
import hmac
import json
import sys
import time

import httpx

from backend.app.core.config import get_settings


def generate_fake_audio_webhook(
    phone: str = "919876543210",
    media_id: str = "mock_audio_media_12345",
    mime_type: str = "audio/ogg; codecs=opus",
) -> dict:
    """Creates a realistic WhatsApp Cloud API audio webhook payload."""
    msg_id = f"wamid.SIMULATED_{int(time.time() * 1000)}"
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "100200300400",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919876543210",
                                "phone_number_id": "100200300400",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test Farmer"},
                                    "wa_id": phone,
                                }
                            ],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": msg_id,
                                    "timestamp": str(int(time.time())),
                                    "type": "audio",
                                    "audio": {
                                        "mime_type": mime_type,
                                        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                                        "id": media_id,
                                        "voice": True,
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def compute_signature(payload_bytes: bytes, secret: str) -> str:
    """Computes X-Hub-Signature-256 HMAC for the payload."""
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate WhatsApp audio webhook locally")
    parser.add_argument("--url", default="http://localhost:8000/webhook", help="Webhook URL to target")
    parser.add_argument("--phone", default="919876543210", help="Sender phone number")
    parser.add_argument("--media-id", default="mock_audio_media_12345", help="Audio media ID")
    parser.add_argument("--secret", default=None, help="Meta App Secret (defaults to META_APP_SECRET in .env)")
    args = parser.parse_args()

    settings = get_settings()
    app_secret = args.secret or settings.META_APP_SECRET

    payload = generate_fake_audio_webhook(phone=args.phone, media_id=args.media_id)
    raw_body = json.dumps(payload).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if app_secret:
        signature = compute_signature(raw_body, app_secret)
        headers["X-Hub-Signature-256"] = signature
        print(f"[*] Signed payload with META_APP_SECRET (sig: {signature[:15]}...)")
    else:
        print("[!] Warning: META_APP_SECRET is empty. Sending without X-Hub-Signature-256 header (allowed in dev).")

    print(f"[*] Posting simulated WhatsApp audio webhook to {args.url}...")
    try:
        r = httpx.post(args.url, content=raw_body, headers=headers, timeout=10.0)
        print(f"[+] Response status: {r.status_code}")
        print(f"[+] Response body:   {r.text}")
        if r.status_code == 200:
            print("[OK] Webhook successfully received and accepted by server.")
            return 0
        else:
            print(f"[!] Server returned non-200 code: {r.status_code}")
            return 1
    except httpx.ConnectError:
        print(f"[!] Could not connect to {args.url}. Is the FastAPI server running?")
        print("    Start server with: uvicorn backend.app.main:app --port 8000")
        return 2


if __name__ == "__main__":
    sys.exit(main())
