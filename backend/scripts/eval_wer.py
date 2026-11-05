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
from ..app.services.intent_service import extract_intent

# Indic + English punctuation normalization pattern (including Devanagari danda)
PUNCT_REGEX = re.compile(r"[\.,\?!;:\"'—\-_।॥\(\)\[\]\{\}]")

LANG_MAP = {
    "telugu": "te-IN",
    "te-in": "te-IN",
    "te": "te-IN",
    "hindi": "hi-IN",
    "hi-in": "hi-IN",
    "hi": "hi-IN",
    "hinglish": "hi-IN",
    "hi-en": "hi-IN",
    "english": "en-IN",
    "en-in": "en-IN",
    "en": "en-IN",
}


def normalize_text(text: str) -> str:
    """Normalizes speech text: lowercase, remove punctuation & dandas, collapse whitespace."""
    if not text:
        return ""
    t = text.lower()
    t = PUNCT_REGEX.sub(" ", t)
    return " ".join(t.split())


def _find_clip_file(clips_path: Path, raw_file: str, clip_id: str) -> Path | None:
    """Finds audio clip file by filename, clip_id, or known ID mapping conventions."""
    all_files = list(clips_path.iterdir()) if clips_path.exists() else []

    # 1. Direct raw_file lookup
    if raw_file:
        for f in all_files:
            if f.name.lower() == raw_file.lower() or f.stem.lower() == raw_file.lower():
                return f

    # 2. Direct clip_id lookup
    if clip_id:
        for f in all_files:
            if f.name.lower() == clip_id.lower() or f.stem.lower() == clip_id.lower():
                return f

        # 3. Known ID patterns: TEL-01 -> Telugu_1, HIN-02 -> Hindi_2, HING-01 -> Hinglish_1
        m = re.match(r"(?i)^(TEL|HIN|HING)-0?(\d+)$", clip_id)
        if m:
            prefix_map = {"tel": "telugu", "hin": "hindi", "hing": "hinglish"}
            lang_prefix = prefix_map.get(m.group(1).lower(), m.group(1).lower())
            num = m.group(2)
            target_pattern = f"{lang_prefix}_{num}".lower()
            for f in all_files:
                if f.name.lower().startswith(target_pattern):
                    return f

    return None


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

    with open(csv_file, "r", encoding="utf-8-sig") as f:
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
        clip_id = row.get("clip_id", "").strip()
        target_file = _find_clip_file(clips_path, raw_file, clip_id)

        if target_file:
            found_audio_count += 1
            valid_rows.append((row, target_file))
        else:
            identifier = raw_file or clip_id
            print(f"Warning: Audio file not found for row '{identifier}' (checked in '{clips_dir}')")

    if found_audio_count == 0:
        print(f"ERROR: Zero audio files found in clips directory '{clips_dir}' for manifest '{csv_path}'.")
        print("Please ensure audio clips are placed in the clips directory before running evaluation.")
        sys.exit(1)

    print(f"Found {found_audio_count} audio files matching manifest entries. Beginning evaluation...")

    for row, audio_file in valid_rows:
        ref_lang_raw = row.get("language", "").strip()
        ref_lang_code = LANG_MAP.get(ref_lang_raw.lower(), ref_lang_raw)
        reference = row.get("reference", "").strip() or row.get("reference_transcript", "").strip()
        ref_norm = normalize_text(reference)
        cid = row.get("clip_id") or audio_file.name

        print(f"[*] Processing {cid} ({audio_file.name}, {ref_lang_raw})...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_16k = os.path.join(tmp_dir, "eval.wav")
            await asyncio.to_thread(audio_service.to_wav16k, str(audio_file), wav_16k)

            is_hinglish = ref_lang_raw.lower() in ("hinglish", "hi-en")
            expected_intent = row.get("expected_intent", "").strip()

            for mode in eval_modes:
                lang_arg = "indic-auto" if mode == "indic-auto" else ref_lang_code
                stt_res = await transcribe(wav_16k, language_code=lang_arg, settings=settings)
                hyp = stt_res.get("transcript", "")
                hyp_norm = normalize_text(hyp)

                if is_hinglish:
                    # Hinglish Roman references cannot be scored via string-distance WER against Devanagari output.
                    wer_score = None
                    cer_score = None
                    parsed = extract_intent(hyp)
                    intent_correct = (parsed.intent == expected_intent) if expected_intent else True
                    intent_res_str = f"Intent: {parsed.intent} ({'PASS' if intent_correct else 'FAIL'})"
                else:
                    if ref_norm == hyp_norm:
                        wer_score = 0.0
                        cer_score = 0.0
                    else:
                        wer_score = round(jiwer.wer(ref_norm, hyp_norm) if ref_norm else 0.0, 4)
                        cer_score = round(jiwer.cer(ref_norm, hyp_norm) if ref_norm else 0.0, 4)
                    intent_res_str = ""

                record = {
                    "file": audio_file.name,
                    "target_language": ref_lang_raw,
                    "mode": mode,
                    "detected_language": stt_res.get("detected_language_code"),
                    "reference": reference,
                    "hypothesis": hyp,
                    "wer": wer_score,
                    "cer": cer_score,
                }
                results.append(record)
                if is_hinglish:
                    print(f"    Mode: {mode:<10} | {intent_res_str} | Detected: {stt_res.get('detected_language_code')}")
                else:
                    print(f"    Mode: {mode:<10} | WER: {wer_score:6.2%} | CER: {cer_score:6.2%} | Detected: {stt_res.get('detected_language_code')}")

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
    hinglish_records = []
    for r in results:
        if r["target_language"].lower() in ("hinglish", "hi-en"):
            hinglish_records.append(r)
        else:
            grouped[(r["target_language"], r["mode"])].append(r)

    for (lang, mode), group in sorted(grouped.items()):
        wer_vals = [g["wer"] for g in group if g["wer"] is not None]
        cer_vals = [g["cer"] for g in group if g["cer"] is not None]
        avg_wer = sum(wer_vals) / len(wer_vals) if wer_vals else 0.0
        avg_cer = sum(cer_vals) / len(cer_vals) if cer_vals else 0.0
        print(f"{lang:<12} | {mode:<12} | {len(group):<6} | {avg_wer:<10.2%} | {avg_cer:<10.2%}")

    if hinglish_records:
        print("\n--- Hinglish Evaluation (Intent & Slot Extraction) ---")
        print("Note: Hinglish audio is transcribed into Devanagari script by Prisma STT v3.0.")
        print("String-distance WER is not applicable against Roman script references.")
        print(f"Hinglish evaluated utterances: {len(hinglish_records)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate WER/CER against reference transcripts.")
    parser.add_argument("--csv", default="backend/data/transcripts.csv", help="Path to transcripts.csv")
    parser.add_argument("--clips-dir", default="backend/data/clips", help="Directory containing audio clips")
    parser.add_argument("--out", default="out/wer_results.csv", help="Path to write results CSV")
    args = parser.parse_args()
    asyncio.run(evaluate_manifest(args.csv, clips_dir=args.clips_dir, output_csv=args.out))
