"""Simulate inbound WhatsApp webhook (text or audio) with HMAC-SHA256 signature.

Allows end-to-end testing of FastAPI /webhook route, signature verification,
deduplication, and background task dispatch locally without Meta Developer Portal.
DOES NOT call Meta APIs to send inbound webhooks.

NOTE ON AUDIO MODE:
When sending an audio webhook with a fake/mock media_id, the local webhook endpoint
will accept the request (HTTP 200), but the background worker will fail at Stage 1
(download_media) because downloading audio requires a real Meta media ID registered
on WhatsApp Graph API servers. Use `--text` mode for complete offline background task
orchestration testing.

Usage:
    # Text message simulation (fully works end-to-end in echo mode):
    python -m backend.scripts.simulate_webhook --text "వరంగల్ లో పత్తి ధర ఎంత?"

    # Audio message simulation (tests webhook intake, signature & deduplication):
    python -m backend.scripts.simulate_webhook --media-id mock_audio_123
"""

import argparse
import hashlib
import hmac
import json
import sys
import time

import httpx

from backend.app.core.config import get_settings


def generate_fake_text_webhook(
    phone: str = "919876543210",
    text: str = "Namaskaram",
) -> dict:
    """Creates a realistic WhatsApp Cloud API text message webhook payload."""
    msg_id = f"wamid.SIMULATED_TEXT_{int(time.time() * 1000)}"
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
                                    "type": "text",
                                    "text": {
                                        "body": text,
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


def generate_fake_audio_webhook(
    phone: str = "919876543210",
    media_id: str = "mock_audio_media_12345",
    mime_type: str = "audio/ogg; codecs=opus",
) -> dict:
    """Creates a realistic WhatsApp Cloud API audio webhook payload."""
    msg_id = f"wamid.SIMULATED_AUDIO_{int(time.time() * 1000)}"
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
    parser = argparse.ArgumentParser(description="Simulate WhatsApp webhook locally")
    parser.add_argument("--url", default="http://localhost:8000/webhook", help="Webhook URL to target")
    parser.add_argument("--phone", default="919876543210", help="Sender phone number")
    parser.add_argument("--text", default=None, help="Text message content (runs text mode)")
    parser.add_argument("--media-id", default="mock_audio_media_12345", help="Audio media ID (runs audio mode)")
    parser.add_argument("--secret", default=None, help="Meta App Secret (defaults to META_APP_SECRET in .env)")
    args = parser.parse_args()

    settings = get_settings()
    app_secret = args.secret or settings.META_APP_SECRET

    if args.text is not None:
        print(f"[*] Generating simulated WhatsApp TEXT message: '{args.text}'")
        payload = generate_fake_text_webhook(phone=args.phone, text=args.text)
    else:
        print(f"[*] Generating simulated WhatsApp AUDIO message (media_id: {args.media_id})")
        print("    [NOTE] Background processing will fail at media download without a real Meta media ID.")
        payload = generate_fake_audio_webhook(phone=args.phone, media_id=args.media_id)

    raw_body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if app_secret:
        signature = compute_signature(raw_body, app_secret)
        headers["X-Hub-Signature-256"] = signature
        print(f"[*] Signed payload with META_APP_SECRET (sig: {signature[:15]}...)")
    else:
        print("[!] Warning: META_APP_SECRET is empty. Sending without X-Hub-Signature-256 header (allowed in dev).")

    print(f"[*] Posting simulated WhatsApp webhook to {args.url}...")
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
