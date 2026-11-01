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
    output_csv: str = "out/wer_results.csv",
    modes: list[str] | None = None,
) -> None:
    settings = get_settings()
    if not settings.GNANI_API_KEY:
        print("ERROR: GNANI_API_KEY is required for live WER evaluation.")
        sys.exit(1)

    eval_modes = modes or ["indic-auto", "explicit"]
    if not os.path.exists(csv_path):
        print(f"ERROR: Transcripts manifest not found at {csv_path}")
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        print(f"Manifest at {csv_path} contains no data rows.")
        return

    results: list[dict[str, Any]] = []
    base_dir = os.path.dirname(os.path.abspath(csv_path))

    for row in reader:
        rel_file = row.get("file", "").strip()
        ref_lang = row.get("language", "").strip()
        reference = row.get("reference", "").strip()
        ref_norm = normalize_text(reference)

        audio_file = os.path.join(base_dir, rel_file)
        if not os.path.exists(audio_file):
            print(f"Warning: Audio file not found, skipping: {audio_file}")
            continue

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_16k = os.path.join(tmp_dir, "eval.wav")
            await asyncio.to_thread(audio_service.to_wav16k, audio_file, wav_16k)

            for mode in eval_modes:
                lang_arg = "indic-auto" if mode == "indic-auto" else ref_lang
                stt_res = await transcribe(wav_16k, language_code=lang_arg, settings=settings)
                hyp = stt_res.get("transcript", "")
                hyp_norm = normalize_text(hyp)

                wer_score = jiwer.wer(ref_norm, hyp_norm) if ref_norm else 0.0
                cer_score = jiwer.cer(ref_norm, hyp_norm) if ref_norm else 0.0

                record = {
                    "file": rel_file,
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

    from collections import defaultdict
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
    parser.add_argument("--out", default="out/wer_results.csv", help="Path to write results CSV")
    args = parser.parse_args()
    asyncio.run(evaluate_manifest(args.csv, args.out))
