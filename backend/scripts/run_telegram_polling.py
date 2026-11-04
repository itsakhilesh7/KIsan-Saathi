"""CLI runner for Telegram long-polling mode in local development.

Allows running the full Kisan Saathi voice/text pipeline locally
without needing a public tunnel (ngrok / cloudflared).

Usage:
    python -m backend.scripts.run_telegram_polling
"""

import asyncio
import logging
import signal
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.app.channels.telegram.poller import run_polling
from backend.app.core.config import get_settings
from backend.app.core.logging import setup_logging

log = logging.getLogger("telegram.runner")


async def main() -> None:
    setup_logging(level=logging.INFO)
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN.strip().strip("<>").strip()

    if not token:
        print("\n[!] ERROR: TELEGRAM_BOT_TOKEN is not configured in backend/.env or environment.")
        print("To create a Telegram bot for local testing:")
        print("  1. Open Telegram and message @BotFather.")
        print("  2. Send '/newbot' and follow the prompts to name your bot.")
        print("  3. Copy the HTTP API token into backend/.env: TELEGRAM_BOT_TOKEN=<your_token>")
        print("  4. Re-run this script.\n")
        sys.exit(1)

    print("=" * 60)
    print("[*] Kisan Saathi - Telegram Polling Mode (D-002 Active)")
    print(f"[*] Pilot Primary Language: {settings.pilot_primary_language}")
    print(f"[*] LLM Mode: {settings.llm_mode} ({settings.LLM_MODEL})")
    print(f"[*] STT Model: {settings.STT_MODEL} ({settings.STT_LANGUAGE})")
    print(f"[*] TTS Model: {settings.TTS_MODEL}")
    print(f"[*] Audio Max Seconds: {settings.AUDIO_MAX_SECONDS}s")
    print("=" * 60)
    print("[*] Bot is polling for voice notes and text messages...")
    print("[*] Press Ctrl+C to stop.\n")

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            # Windows does not support loop.add_signal_handler for SIGINT
            pass

    try:
        await run_polling(settings=settings, stop_event=stop_event)
    except KeyboardInterrupt:
        print("\n[*] Stopping Telegram polling...")
    finally:
        print("[*] Poller stopped safely.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

