"""Speech evaluation script reporting WER and CER by language and mode.

Supports comparison between:
- mode="indic-auto": Automatic language detection via Prisma v3.0
- mode="explicit": Explicit language code matching ground truth reference

Manifest format (backend/data/transcripts.csv):
file,language,reference
"""

import argparse
import asyncio
import csv
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import jiwer

from ..app.core.config import get_settings
from ..app.integrations.gnani.stt import transcribe
from ..app.services import audio_service

# Indic + English punctuation normalization pattern (including Devanagari danda)
PUNCT_REGEX = re.compile(r"[\.,\?!;:\"'—\-_।॥\(\)\[\]\{\}]")


def normalize_text(text: str) -> str:
    """Normalizes speech text: lowercase, remove punctuation & dandas, collapse whitespace."""
    if not text:
        return ""
    t = text.lower()
    t = PUNCT_REGEX.sub(" ", t)
    return " ".join(t.split())


async def evaluate_manifest(
    csv_path: str,
    clips_dir: str = "backend/data/clips",
    output_csv: str = "out/wer_results.csv",
    modes: list[str] | None = None,
) -> None:
    settings = get_settings()
    if not settings.GNANI_API_KEY:
        print("ERROR: GNANI_API_KEY is required for live WER evaluation.")
        sys.exit(1)

    eval_modes = modes or ["indic-auto", "explicit"]
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"ERROR: Transcripts manifest not found at {csv_path}")
        sys.exit(1)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        print(f"Manifest at {csv_path} contains no data rows.")
        return

    clips_path = Path(clips_dir)
    results: list[dict[str, Any]] = []
    found_audio_count = 0

    # First pass: verify at least one audio file exists
    valid_rows: list[tuple[dict[str, str], Path]] = []
    for row in reader:
        raw_file = row.get("file", "").strip()
        if not raw_file:
            continue

        # Check candidate locations:
        # 1. clips_dir / raw_file
        # 2. clips_dir / basename(raw_file) (accepts plain filenames)
        # 3. relative to csv_path
        candidates = [
            clips_path / raw_file,
            clips_path / Path(raw_file).name,
            csv_file.parent / raw_file,
        ]
        target_file: Path | None = None
        for c in candidates:
            if c.exists() and c.is_file():
                target_file = c
                break

        if target_file:
            found_audio_count += 1
            valid_rows.append((row, target_file))
        else:
            print(f"Warning: Audio file not found for row file='{raw_file}' (checked in '{clips_dir}')")

    if found_audio_count == 0:
        print(f"ERROR: Zero audio files found in clips directory '{clips_dir}' for manifest '{csv_path}'.")
        print("Please ensure audio clips are placed in the clips directory before running evaluation.")
        sys.exit(1)

    print(f"Found {found_audio_count} audio files matching manifest entries. Beginning evaluation...")

    for row, audio_file in valid_rows:
        ref_lang = row.get("language", "").strip()
        reference = row.get("reference", "").strip()
        ref_norm = normalize_text(reference)

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_16k = os.path.join(tmp_dir, "eval.wav")
            await asyncio.to_thread(audio_service.to_wav16k, str(audio_file), wav_16k)

            for mode in eval_modes:
                lang_arg = "indic-auto" if mode == "indic-auto" else ref_lang
                stt_res = await transcribe(wav_16k, language_code=lang_arg, settings=settings)
                hyp = stt_res.get("transcript", "")
                hyp_norm = normalize_text(hyp)

                wer_score = jiwer.wer(ref_norm, hyp_norm) if ref_norm else 0.0
                cer_score = jiwer.cer(ref_norm, hyp_norm) if ref_norm else 0.0

                record = {
                    "file": audio_file.name,
                    "target_language": ref_lang,
                    "mode": mode,
                    "detected_language": stt_res.get("detected_language_code"),
                    "reference": reference,
                    "hypothesis": hyp,
                    "wer": round(wer_score, 4),
                    "cer": round(cer_score, 4),
                }
                results.append(record)

    # Save detailed CSV
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    fieldnames = ["file", "target_language", "mode", "detected_language", "reference", "hypothesis", "wer", "cer"]
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved detailed evaluation to {output_csv}")

    # Aggregated reporting by language and mode
    print("\n=================== EVALUATION REPORT ===================")
    print(f"{'Language':<12} | {'Mode':<12} | {'Count':<6} | {'Avg WER':<10} | {'Avg CER':<10}")
    print("-" * 60)

    grouped = defaultdict(list)
    for r in results:
        grouped[(r["target_language"], r["mode"])].append(r)

    for (lang, mode), group in sorted(grouped.items()):
        avg_wer = sum(g["wer"] for g in group) / len(group)
        avg_cer = sum(g["cer"] for g in group) / len(group)
        print(f"{lang:<12} | {mode:<12} | {len(group):<6} | {avg_wer:<10.2%} | {avg_cer:<10.2%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate WER/CER against reference transcripts.")
    parser.add_argument("--csv", default="backend/data/transcripts.csv", help="Path to transcripts.csv")
    parser.add_argument("--clips-dir", default="backend/data/clips", help="Directory containing audio clips")
    parser.add_argument("--out", default="out/wer_results.csv", help="Path to write results CSV")
    args = parser.parse_args()
    asyncio.run(evaluate_manifest(args.csv, clips_dir=args.clips_dir, output_csv=args.out))
