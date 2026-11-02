"""CLI smoke test for live Gnani Prisma STT and Timbre TTS verification.

Usage:
  python -m backend.scripts.test_gnani --audio path/to/sample.m4a --lang te-IN
  python -m backend.scripts.test_gnani --tts "నమస్కారం రైతు సోదరులారా" --lang te-IN
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from ..app.core.config import get_settings
from ..app.integrations.gnani.stt import transcribe_short
from ..app.integrations.gnani.tts import synthesize
from ..app.services import audio_service


async def main() -> None:
    parser = argparse.ArgumentParser(description="Gnani API Smoke Test")
    parser.add_argument("--audio", help="Path to input audio file (m4a, ogg, mp3, wav) to transcribe")
    parser.add_argument("--tts", help="Text to synthesize with Timbre TTS")
    parser.add_argument("--lang", default="te-IN", help="Language code (te-IN, hi-IN, en-IN, indic-auto)")
    parser.add_argument("--out-dir", default="out", help="Output directory to save generated files")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.GNANI_API_KEY:
        print("ERROR: GNANI_API_KEY is not set in environment or .env file.")
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Using Gnani STT Model: {settings.STT_MODEL}")
    print(f"Using Gnani TTS Model: {settings.TTS_MODEL}")

    if args.audio:
        if not os.path.exists(args.audio):
            print(f"ERROR: Audio file not found: {args.audio}")
            sys.exit(1)

        conv_wav = str(out_dir / "converted_16k.wav")
        print(f"Converting {args.audio} to 16 kHz mono WAV: {conv_wav}...")
        audio_service.to_wav16k(args.audio, conv_wav)

        print(f"Transcribing {conv_wav} with language={args.lang}...")
        raw_res = await transcribe_short(conv_wav, language_code=args.lang, settings=settings)

        print("\n--- Raw Prisma STT Response (no secrets) ---")
        print(json.dumps(raw_res, indent=2, ensure_ascii=False))

        print("\n--- Parsed Fields ---")
        print(f"Transcript: {raw_res.get('transcript')}")
        print(f"Raw detected_language_code: {repr(raw_res.get('detected_language_code'))}")
        print(f"Saved 16kHz WAV to: {conv_wav}")

    if args.tts:
        print(f"Synthesizing '{args.tts}' in {args.lang}...")
        wav_bytes = await synthesize(args.tts, language=args.lang, settings=settings)

        wav_out = str(out_dir / "tts_output.wav")
        with open(wav_out, "wb") as f:
            f.write(wav_bytes)

        ogg_out = str(out_dir / "tts_output.ogg")
        print(f"Encoding WAV to WhatsApp-compatible OGG/Opus: {ogg_out}...")
        audio_service.wav_to_ogg_opus(wav_out, ogg_out)

        size_kb = os.path.getsize(ogg_out) / 1024.0
        status_limit = "OK" if size_kb <= 512 else "EXCEEDS LIMIT"

        print("\n--- Timbre TTS Synthesis & Encoding ---")
        print(f"Saved WAV ({len(wav_bytes)} bytes) to: {wav_out}")
        print(f"Saved OGG/Opus ({size_kb:.2f} KB) to: {ogg_out}")
        print(f"WhatsApp 512 KB voice note inline limit: {status_limit} ({size_kb:.2f} KB / 512 KB)")


if __name__ == "__main__":
    asyncio.run(main())
