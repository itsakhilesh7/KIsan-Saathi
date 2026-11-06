"""Generates consistent WER/CER evaluation tables from out/wer_results.csv."""

import csv
from collections import defaultdict
from pathlib import Path


def generate_wer_tables(csv_path: str = "out/wer_results.csv") -> dict[str, str]:
    """Parses wer_results.csv and produces exact per-clip and aggregated markdown tables."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"WER results file not found at {csv_path}")

    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # Group by language and mode
    per_clip_rows = []
    group_stats = defaultdict(list)
    hinglish_rows = []

    for r in reader:
        lang = r["target_language"]
        mode = r["mode"]
        filename = r["file"]
        wer_val = float(r["wer"]) if r.get("wer") and r["wer"].strip() else None
        cer_val = float(r["cer"]) if r.get("cer") and r["cer"].strip() else None

        if lang.lower() in ("hinglish", "hi-en"):
            hinglish_rows.append(r)
            continue

        per_clip_rows.append({
            "file": filename,
            "language": lang,
            "mode": mode,
            "wer": wer_val,
            "cer": cer_val,
            "detected": r.get("detected_language", ""),
        })

        if wer_val is not None and cer_val is not None:
            group_stats[(lang, mode)].append((wer_val, cer_val))

    # Build per-clip Markdown table
    per_clip_md = [
        "| File / Clip | Language | Mode | STT Detected | WER | CER |",
        "|---|---|---|---|---|---|",
    ]
    for row in per_clip_rows:
        wer_str = f"{row['wer']:6.2%}" if row['wer'] is not None else "N/A"
        cer_str = f"{row['cer']:6.2%}" if row['cer'] is not None else "N/A"
        per_clip_md.append(
            f"| `{row['file']}` | {row['language']} | `{row['mode']}` | `{row['detected']}` | {wer_str} | {cer_str} |"
        )

    # Build summary Markdown table
    summary_md = [
        "| Language | Mode | Clip Count | Mean WER | Mean CER |",
        "|---|---|---|---|---|",
    ]
    summary_data = {}
    for (lang, mode), values in sorted(group_stats.items()):
        count = len(values)
        mean_wer = sum(v[0] for v in values) / count if count else 0.0
        mean_cer = sum(v[1] for v in values) / count if count else 0.0
        summary_data[(lang, mode)] = (count, mean_wer, mean_cer)
        summary_md.append(
            f"| **{lang}** | `{mode}` | {count} | **{mean_wer:6.2%}** | **{mean_cer:6.2%}** |"
        )

    return {
        "per_clip_table": "\n".join(per_clip_md),
        "summary_table": "\n".join(summary_md),
        "summary_data": summary_data,
        "per_clip_data": per_clip_rows,
        "hinglish_count": len(hinglish_rows),
    }


if __name__ == "__main__":
    res = generate_wer_tables()
    print("### Per-Clip Evaluation Results")
    print(res["per_clip_table"])
    print("\n### Summary by Language and Mode")
    print(res["summary_table"])
    print(f"\nHinglish clips evaluated by intent/slot extraction: {res['hinglish_count']}")

