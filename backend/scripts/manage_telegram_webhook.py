"""CLI utility to manage Telegram Bot Webhook registration for hosting.

Usage:
    python -m backend.scripts.manage_telegram_webhook set https://your-domain.com
    python -m backend.scripts.manage_telegram_webhook delete
    python -m backend.scripts.manage_telegram_webhook info
"""

import argparse
import sys
from typing import Any

import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.app.core.config import get_settings


def redact_token(token: str) -> str:
    """Safely redacts a Telegram bot token for display."""
    if not token:
        return "<not set>"
    if ":" in token:
        prefix, secret = token.split(":", 1)
        return f"{prefix}:{'*' * (len(secret) - 4)}{secret[-4:]}" if len(secret) > 4 else f"{prefix}:****"
    return f"{'*' * (len(token) - 4)}{token[-4:]}" if len(token) > 4 else "****"


def get_telegram_client_info() -> tuple[str, str, str]:
    """Retrieves token, path, and secret from settings with validation."""
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN.strip().strip("<>").strip()
    if not token:
        print("[!] ERROR: TELEGRAM_BOT_TOKEN is not configured in environment or .env.")
        sys.exit(1)

    webhook_path = settings.TELEGRAM_WEBHOOK_PATH.strip()
    secret = settings.TELEGRAM_WEBHOOK_SECRET.strip()
    return token, webhook_path, secret


def call_telegram_api(token: str, method: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Executes a request against the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    with httpx.Client(timeout=15.0) as client:
        if json_body is not None:
            resp = client.post(url, json=json_body)
        else:
            resp = client.get(url)

    try:
        data = resp.json()
    except Exception:
        print(f"[!] HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

    return data


def set_webhook(base_url: str) -> None:
    """Registers the webhook URL with Telegram Bot API."""
    token, webhook_path, secret = get_telegram_client_info()
    if not webhook_path:
        print("[!] ERROR: TELEGRAM_WEBHOOK_PATH must be configured before setting a webhook.")
        print("    Example: set TELEGRAM_WEBHOOK_PATH=secr3t_path in .env")
        sys.exit(1)

    clean_base = base_url.rstrip("/")
    webhook_url = f"{clean_base}/telegram/webhook/{webhook_path}"

    payload: dict[str, Any] = {
        "url": webhook_url,
        "allowed_updates": ["message", "edited_message"],
    }
    if secret:
        payload["secret_token"] = secret

    print(f"[*] Setting webhook for Bot ({redact_token(token)})...")
    print(f"[*] Target URL: {clean_base}/telegram/webhook/{webhook_path[:3]}...{webhook_path[-3:] if len(webhook_path) > 6 else ''}")
    if secret:
        print("[*] Secret token header configured.")

    res = call_telegram_api(token, "setWebhook", payload)
    if res.get("ok"):
        print("[+] SUCCESS: Webhook registered successfully!")
        print(f"    Description: {res.get('description', 'OK')}")
    else:
        print(f"[-] FAILED to set webhook: {res.get('description')}")
        sys.exit(1)


def delete_webhook() -> None:
    """Deletes existing webhook registration, reverting bot to polling mode."""
    token, _, _ = get_telegram_client_info()
    print(f"[*] Deleting webhook for Bot ({redact_token(token)})...")

    payload = {"drop_pending_updates": False}
    res = call_telegram_api(token, "deleteWebhook", payload)
    if res.get("ok"):
        print("[+] SUCCESS: Webhook deleted successfully! Bot can now use long polling.")
    else:
        print(f"[-] FAILED to delete webhook: {res.get('description')}")
        sys.exit(1)


def get_webhook_info() -> None:
    """Retrieves and prints current webhook status from Telegram."""
    token, _, _ = get_telegram_client_info()
    print(f"[*] Checking webhook info for Bot ({redact_token(token)})...")

    res = call_telegram_api(token, "getWebhookInfo")
    if not res.get("ok"):
        print(f"[-] FAILED to get webhook info: {res.get('description')}")
        sys.exit(1)

    info = res.get("result", {})
    url = info.get("url", "")
    print("=" * 60)
    print(f"Webhook URL:            {url if url else '(None - Polling Mode Active)'}")
    print(f"Has Custom Certificate: {info.get('has_custom_certificate', False)}")
    print(f"Pending Update Count:   {info.get('pending_update_count', 0)}")
    print(f"Max Connections:        {info.get('max_connections', 40)}")
    if info.get("last_error_date"):
        print(f"Last Error Date:        {info.get('last_error_date')}")
        print(f"Last Error Message:     {info.get('last_error_message')}")
    if info.get("last_synchronization_error_date"):
        print(f"Sync Error Date:        {info.get('last_synchronization_error_date')}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Telegram Bot Webhook")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Set Telegram webhook URL")
    set_parser.add_argument("base_url", help="Base public URL of deployed service (e.g. https://my-bot.onrender.com)")

    subparsers.add_parser("delete", help="Delete Telegram webhook")
    subparsers.add_parser("info", help="Get current Telegram webhook status")

    args = parser.parse_args()

    if args.command == "set":
        set_webhook(args.base_url)
    elif args.command == "delete":
        delete_webhook()
    elif args.command == "info":
        get_webhook_info()


if __name__ == "__main__":
    main()
