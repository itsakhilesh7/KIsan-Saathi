"""CLI smoke test for live Gnani Prisma STT and Timbre TTS verification.

Usage:
  python -m backend.scripts.test_gnani --audio path/to/sample.wav --lang te-IN
  python -m backend.scripts.test_gnani --tts "నమస్కారం రైతు సోదరులారా" --lang te-IN
"""

import argparse
import asyncio
import os
import sys

from ..app.core.config import get_settings
from ..app.integrations.gnani.stt import transcribe
from ..app.integrations.gnani.tts import synthesize


async def main() -> None:
    parser = argparse.ArgumentParser(description="Gnani API Smoke Test")
    parser.add_argument("--audio", help="Path to WAV audio file to transcribe with Prisma STT")
    parser.add_argument("--tts", help="Text to synthesize with Timbre TTS")
    parser.add_argument("--lang", default="te-IN", help="Language code (te-IN, hi-IN, en-IN, indic-auto)")
    parser.add_argument("--out", default="out/test_output.wav", help="Output WAV path for TTS")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.GNANI_API_KEY:
        print("ERROR: GNANI_API_KEY is not set in environment or .env file.")
        sys.exit(1)

    print(f"Using Gnani STT Model: {settings.STT_MODEL}")
    print(f"Using Gnani TTS Model: {settings.TTS_MODEL}")

    if args.audio:
        if not os.path.exists(args.audio):
            print(f"ERROR: Audio file not found: {args.audio}")
            sys.exit(1)
        print(f"Transcribing {args.audio} with language={args.lang}...")
        res = await transcribe(args.audio, language_code=args.lang, settings=settings)
        print("\n--- Transcription Result ---")
        print(f"Transcript: {res.get('transcript')}")
        print(f"Detected Language: {res.get('detected_language_code')} (raw: {res.get('raw_language_code')})")
        print(f"Chunks: {res.get('chunks')}")

    if args.tts:
        print(f"Synthesizing '{args.tts}' in {args.lang}...")
        wav_bytes = await synthesize(args.tts, language=args.lang, settings=settings)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "wb") as f:
            f.write(wav_bytes)
        print(f"Saved synthesized audio ({len(wav_bytes)} bytes) to {args.out}")


if __name__ == "__main__":
    asyncio.run(main())

