"""Evaluation runner for Experiment E1: Robustness of Prisma STT.

Evaluates Prisma STT v3.0 under clean, additive noise (pink, brown, ESC-50 engine at 20/10/5 dB),
telephone simulation (G.711 mu-law, AMR-NB), and WhatsApp Opus compression.
Uses explicit language mode only.

Generates:
- evaluation/results/e1_per_clip.csv
- evaluation/results/e1_summary_table.md
- evaluation/results/e1_robustness_chart.png
- evaluation/results/RUN_INFO.json
"""

import argparse
import asyncio
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jiwer

from ..app.core.config import get_settings
from ..app.integrations.gnani.stt import transcribe
from ..app.services.intent_service import extract_intent
from .eval_wer import normalize_text

CORE_CONDITIONS_INDIC = [
    "clean",
    "noise_pink_snr20",
    "noise_pink_snr10",
    "noise_pink_snr5",
    "noise_brown_snr20",
    "noise_brown_snr10",
    "noise_brown_snr5",
    "tel_g711",
    "tel_amrnb",
    "whatsapp_opus",
]

CORE_CONDITIONS_HINGLISH = [
    "clean",
    "noise_pink_snr10",
    "tel_g711",
]

ENGINE_CONDITIONS = [
    "noise_engine_snr20",
    "noise_engine_snr10",
    "noise_engine_snr5",
]


def get_git_commit_hash() -> str:
    """Returns the current git HEAD commit hash."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def generate_e1_chart(summary_data: dict[str, dict[str, Any]], out_path: Path) -> None:
    """Generates a clear bar chart of WER by condition for Telugu and Hindi."""
    os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / "out" / ".matplotlib"))
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)

    telugu_conds = summary_data.get("Telugu", {})
    hindi_conds = summary_data.get("Hindi", {})

    all_conds = [c for c in CORE_CONDITIONS_INDIC if c in telugu_conds or c in hindi_conds]
    # Add any extra conditions evaluated (e.g. engine)
    for c in telugu_conds.keys():
        if c not in all_conds:
            all_conds.append(c)

    if not all_conds:
        return

    label_map = {
        "clean": "Clean",
        "noise_pink_snr20": "Pink 20dB",
        "noise_pink_snr10": "Pink 10dB",
        "noise_pink_snr5": "Pink 5dB",
        "noise_brown_snr20": "Brown 20dB",
        "noise_brown_snr10": "Brown 10dB",
        "noise_brown_snr5": "Brown 5dB",
        "noise_engine_snr20": "Engine 20dB",
        "noise_engine_snr10": "Engine 10dB",
        "noise_engine_snr5": "Engine 5dB",
        "tel_g711": "Tel G.711",
        "tel_amrnb": "Tel AMR-NB",
        "whatsapp_opus": "WhatsApp Opus",
    }

    display_labels = [label_map.get(c, c) for c in all_conds]
    te_wers = [telugu_conds.get(c, {}).get("mean_wer", 0.0) * 100 for c in all_conds]
    hi_wers = [hindi_conds.get(c, {}).get("mean_wer", 0.0) * 100 for c in all_conds]

    x = range(len(all_conds))
    width = 0.38

    fig, ax = plt.subplots(figsize=(15, 6))
    bars1 = ax.bar([i - width / 2 for i in x], te_wers, width, label="Telugu (te-IN)", color="#2b5c8f")
    bars2 = ax.bar([i + width / 2 for i in x], hi_wers, width, label="Hindi (hi-IN)", color="#d95f02")

    ax.set_ylabel("Word Error Rate (WER %)", fontsize=12)
    ax.set_title("Experiment E1: Prisma STT v3.0 Robustness Across Conditions", fontsize=14, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(display_labels, rotation=45, ha="right", fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[+] Saved robustness chart to {out_path}")


def filter_planned_rows(
    all_rows: list[dict[str, Any]],
    suite: str = "core_minimal",
    conditions: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filters audio manifest rows according to requested evaluation suite."""
    filtered = []
    for r in all_rows:
        lang = r["language"].lower()
        cond = r["condition"]

        if conditions:
            if cond in conditions:
                filtered.append(r)
            continue

        if suite == "core_minimal":
            if lang in ("hinglish", "hi-en"):
                if cond in CORE_CONDITIONS_HINGLISH:
                    filtered.append(r)
            else:
                if cond in CORE_CONDITIONS_INDIC:
                    filtered.append(r)
        elif suite == "with_engine":
            if lang in ("hinglish", "hi-en"):
                if cond in CORE_CONDITIONS_HINGLISH:
                    filtered.append(r)
            else:
                if cond in (CORE_CONDITIONS_INDIC + ENGINE_CONDITIONS):
                    filtered.append(r)
        else:  # full
            filtered.append(r)

    return filtered


async def run_evaluation(
    manifest_path: str = "out/eval_audio_manifest.csv",
    results_dir: str = "evaluation/results",
    suite: str = "core_minimal",
    conditions: list[str] | None = None,
    batch_limit: int | None = None,
    dry_run: bool = False,
) -> None:
    settings = get_settings()
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        print(f"ERROR: Audio manifest not found at {manifest_path}.")
        print("Please run `python -m backend.scripts.build_eval_audio` first.")
        sys.exit(1)

    with open(manifest_file, "r", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    rows = filter_planned_rows(all_rows, suite=suite, conditions=conditions)

    total_planned = len(rows)
    clips_count = len({r["clip_id"] for r in rows})
    conds_count = len({r["condition"] for r in rows})
    langs = sorted({r["language"] for r in rows})

    # Load existing results to support seamless resuming
    per_clip_csv = out_dir / "e1_per_clip.csv"
    existing_results: list[dict[str, Any]] = []
    completed_keys: set[tuple[str, str]] = set()

    if per_clip_csv.exists():
        with open(per_clip_csv, "r", encoding="utf-8") as f:
            existing_results = list(csv.DictReader(f))
            for er in existing_results:
                # Convert wer/cer strings back to float/None
                er["wer"] = float(er["wer"]) if er.get("wer") and er["wer"].strip() else None
                er["cer"] = float(er["cer"]) if er.get("cer") and er["cer"].strip() else None
                er["intent_correct"] = (er.get("intent_correct") == "True") if er.get("intent_correct") in ("True", "False") else None
                completed_keys.add((er["clip_id"], er["condition"]))

    remaining_rows = [r for r in rows if (r["clip_id"], r["condition"]) not in completed_keys]

    print("=" * 65)
    print("EXPERIMENT E1: PRISMA STT ROBUSTNESS EVALUATION AUDIT")
    print("=" * 65)
    print(f"Selected Suite:         {suite}")
    print(f"Total Unique Clips:     {clips_count} ({', '.join(langs)})")
    print(f"Conditions in Suite:    {conds_count}")
    print(f"Total Planned Calls:    {total_planned}")
    print(f"Already Completed:      {len(completed_keys)}")
    print(f"Remaining Calls:        {len(remaining_rows)}")
    if batch_limit:
        print(f"Batch Limit for Run:    {batch_limit}")
    print(f"STT Model:              {settings.STT_MODEL}")
    print("Mode:                   explicit (te-IN for Telugu, hi-IN for Hindi/Hinglish)")
    print("=" * 65)

    if dry_run:
        print("\n[!] DRY RUN ONLY: No Prisma API calls executed.")
        return

    if not remaining_rows:
        print("\n[+] All planned calls for this suite have already been executed.")
    else:
        if not settings.GNANI_API_KEY:
            print("[!] ERROR: GNANI_API_KEY is missing from environment. Cannot run live STT.")
            sys.exit(1)

        calls_in_batch = 0
        fieldnames = [
            "clip_id", "language", "language_code", "condition", "condition_type",
            "noise_source", "snr_db", "reference", "hypothesis", "wer", "cer", "intent_correct",
        ]

        # Open file in append or write mode
        file_mode = "a" if per_clip_csv.exists() else "w"
        csv_file = open(per_clip_csv, file_mode, encoding="utf-8", newline="")
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if file_mode == "w":
            writer.writeheader()

        try:
            for r in remaining_rows:
                if batch_limit and calls_in_batch >= batch_limit:
                    print(f"\n[!] Pausing: Reached batch limit of {batch_limit} calls.")
                    print(f"[!] Total calls completed so far: {len(existing_results)}")
                    print("[!] Please check your Gnani credit balance, then resume.")
                    break

                cid = r["clip_id"]
                lang = r["language"]
                lang_code = r["language_code"]
                cond = r["condition"]
                audio_path = r["audio_path"]
                ref = r["reference_transcript"]
                expected_intent = r["expected_intent"]
                is_hinglish = lang.lower() in ("hinglish", "hi-en")

                overall_idx = len(existing_results) + 1
                print(f"[{overall_idx}/{total_planned}] (Batch {calls_in_batch+1}) {cid} ({lang}) | Condition: {cond}...")

                stt_res = await transcribe(audio_path, language_code=lang_code, settings=settings)
                hyp = stt_res.get("transcript", "").strip()

                ref_norm = normalize_text(ref)
                hyp_norm = normalize_text(hyp)

                if is_hinglish:
                    wer_val = None
                    cer_val = None
                    parsed = extract_intent(hyp)
                    intent_pass = (parsed.intent == expected_intent) if expected_intent else True
                    detail_str = f"Intent: {parsed.intent} ({'PASS' if intent_pass else 'FAIL'})"
                else:
                    if ref_norm == hyp_norm:
                        wer_val = 0.0
                        cer_val = 0.0
                    else:
                        wer_val = round(jiwer.wer(ref_norm, hyp_norm) if ref_norm else 0.0, 4)
                        cer_val = round(jiwer.cer(ref_norm, hyp_norm) if ref_norm else 0.0, 4)
                    intent_pass = None
                    detail_str = f"WER: {wer_val:6.2%} | CER: {cer_val:6.2%}"

                print(f"    -> {detail_str} | Hyp: {hyp[:60]}...")

                record = {
                    "clip_id": cid,
                    "language": lang,
                    "language_code": lang_code,
                    "condition": cond,
                    "condition_type": r.get("condition_type", ""),
                    "noise_source": r.get("noise_source", ""),
                    "snr_db": r.get("snr_db", ""),
                    "reference": ref,
                    "hypothesis": hyp,
                    "wer": wer_val,
                    "cer": cer_val,
                    "intent_correct": intent_pass,
                }
                writer.writerow(record)
                csv_file.flush()
                existing_results.append(record)
                calls_in_batch += 1
        finally:
            csv_file.close()

    # If all planned calls are completed, produce final reports
    all_completed = len(existing_results) >= total_planned
    if all_completed:
        print("\n" + "=" * 65)
        print("ALL PLANNED EVALUATION CALLS COMPLETE - GENERATING REPORTS")
        print("=" * 65)

        grouped = defaultdict(lambda: defaultdict(list))
        for r in existing_results:
            grouped[r["language"]][r["condition"]].append(r)

        summary_stats: dict[str, dict[str, Any]] = defaultdict(dict)
        summary_md_lines = [
            "# Experiment E1: Robustness of Prisma STT v3.0",
            "",
            "**Evaluation Conditions & Ground Truth Invariants:**",
            "- Mode: `explicit` language code (`te-IN` for Telugu, `hi-IN` for Hindi/Hinglish).",
            "- Identical string normalizer applied to references and hypotheses (`normalize_text`).",
            "- Hinglish Roman reference strings evaluated via intent extraction (`extract_intent`), not WER.",
            "",
            "| Language | Condition | n | Mean WER | Mean CER | Intent Acc |",
            "|---|---|---|---|---|---|",
        ]

        for lang in sorted(grouped.keys()):
            for cond in grouped[lang].keys():
                items = grouped[lang][cond]
                n = len(items)
                is_h = lang.lower() in ("hinglish", "hi-en")
                if is_h:
                    acc = sum(1 for it in items if it["intent_correct"]) / n if n else 0.0
                    summary_stats[lang][cond] = {"n": n, "intent_acc": acc}
                    summary_md_lines.append(f"| **{lang}** | `{cond}` | {n} | N/A | N/A | **{acc:6.1%}** |")
                else:
                    w_list = [it["wer"] for it in items if it["wer"] is not None]
                    c_list = [it["cer"] for it in items if it["cer"] is not None]
                    m_wer = sum(w_list) / len(w_list) if w_list else 0.0
                    m_cer = sum(c_list) / len(c_list) if c_list else 0.0
                    summary_stats[lang][cond] = {"n": n, "mean_wer": m_wer, "mean_cer": m_cer}
                    summary_md_lines.append(f"| **{lang}** | `{cond}` | {n} | **{m_wer:6.2%}** | **{m_cer:6.2%}** | - |")

        summary_md_path = out_dir / "e1_summary_table.md"
        summary_md_path.write_text("\n".join(summary_md_lines), encoding="utf-8")
        print(f"[+] Saved summary markdown table to {summary_md_path}")

        chart_png_path = out_dir / "e1_robustness_chart.png"
        generate_e1_chart(summary_stats, chart_png_path)

        run_info = {
            "experiment": "E1: Prisma STT Noise, Telephone, and WhatsApp Robustness",
            "date": datetime.now(timezone.utc).isoformat(),
            "git_commit": get_git_commit_hash(),
            "model_stt": settings.STT_MODEL,
            "mode": "explicit",
            "suite": suite,
            "total_calls": len(existing_results),
            "clip_count": clips_count,
            "conditions_count": conds_count,
            "conditions": sorted(list({r['condition'] for r in existing_results})),
            "limits": [
                "10 clips total (4 Telugu, 4 Hindi, 2 Hinglish).",
                "Single speaker recording baseline in quiet room.",
                "Small sample size; results indicate directional robustness across conditions, not population-level benchmark.",
            ],
        }
        run_info_path = out_dir / "RUN_INFO.json"
        with open(run_info_path, "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2)
        print(f"[+] Saved execution metadata to {run_info_path}")

        print("\n" + "\n".join(summary_md_lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Experiment E1 STT evaluation.")
    parser.add_argument("--manifest", default="out/eval_audio_manifest.csv", help="Audio manifest CSV")
    parser.add_argument("--results-dir", default="evaluation/results", help="Directory to save evaluation results")
    parser.add_argument("--suite", default="core_minimal", choices=["core_minimal", "with_engine", "full"], help="Evaluation suite")
    parser.add_argument("--conditions", nargs="*", default=None, help="Optional subset of conditions to run")
    parser.add_argument("--batch-limit", type=int, default=None, help="Stop after executing this many new calls")
    parser.add_argument("--count-only", action="store_true", help="Count total calls and print summary without making API calls")
    args = parser.parse_args()

    asyncio.run(run_evaluation(
        manifest_path=args.manifest,
        results_dir=args.results_dir,
        suite=args.suite,
        conditions=args.conditions,
        batch_limit=args.batch_limit,
        dry_run=args.count_only,
    ))
