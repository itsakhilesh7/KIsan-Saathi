"""Smoke test for Prisma + Timbre.

  python -m scripts.test_gnani --audio data/clips/te_01.m4a
  python -m scripts.test_gnani --audio data/clips/hi_01.ogg --lang hi-IN
  python -m scripts.test_gnani --tts "నమస్కారం, మీకు ఎలా సహాయం చేయాలి?" --lang te-IN
"""
import argparse
import asyncio
import os
import tempfile

from app import audio, gnani

OUT = "out"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", help="path to a voice clip (any format ffmpeg reads)")
    ap.add_argument("--lang", default=None, help="te-IN / hi-IN / en-IN / indic-auto (default from .env)")
    ap.add_argument("--tts", help="text to synthesize")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    text, lang = args.tts, args.lang

    if args.audio:
        with tempfile.TemporaryDirectory() as tmp:
            wav = audio.to_wav16k(args.audio, os.path.join(tmp, "in.wav"))
            print(f"duration: {audio.duration_seconds(wav):.1f}s")
            res = await gnani.transcribe(wav, args.lang)
        print("detected:", res["detected_language_code"], "| chunks:", res["chunks"])
        print("transcript:", res["transcript"])
        text = text or res["transcript"]
        lang = res["detected_language_code"] or args.lang

    if text:
        lang = lang if lang and lang != "indic-auto" else "hi-IN"
        wav_bytes = await gnani.synthesize(text, lang)
        wav_path, ogg_path = os.path.join(OUT, "reply.wav"), os.path.join(OUT, "reply.ogg")
        with open(wav_path, "wb") as f:
            f.write(wav_bytes)
        audio.wav_to_ogg_opus(wav_path, ogg_path)
        kb = os.path.getsize(ogg_path) / 1024
        print(f"saved {wav_path} and {ogg_path} ({kb:.0f} KB; keep <512 KB for the WhatsApp play icon)")


if __name__ == "__main__":
    asyncio.run(main())
