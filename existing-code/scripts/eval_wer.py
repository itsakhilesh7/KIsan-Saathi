"""Measure Prisma word/character error rate on your own recordings.

data/transcripts.csv columns:  file,language,reference
  file      = name inside data/clips/  (e.g. te_01.m4a)
  language  = te-IN | hi-IN | en-IN | hi-en
  reference = what was ACTUALLY said, typed by you

  python -m scripts.eval_wer                      # compares indic-auto vs the labelled language
"""
import argparse
import asyncio
import csv
import os
import re
import tempfile

import jiwer

from app import audio, gnani

CLIPS = "data/clips"


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[।॥.,!?;:\"'()\-–—]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


async def run(csv_path: str, modes: list[str]) -> None:
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    results = []
    for row in rows:
        path = os.path.join(CLIPS, row["file"])
        if not os.path.exists(path):
            print("missing:", path)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            wav = audio.to_wav16k(path, os.path.join(tmp, "x.wav"))
            for mode in modes:
                code = "indic-auto" if mode == "auto" else row["language"]
                try:
                    res = await gnani.transcribe(wav, code)
                except gnani.GnaniError as e:
                    print(f"{row['file']} [{mode}] ERROR {e}")
                    continue
                ref, hyp = normalize(row["reference"]), normalize(res["transcript"])
                results.append({
                    "file": row["file"], "language": row["language"], "mode": mode,
                    "wer": round(jiwer.wer(ref, hyp), 3), "cer": round(jiwer.cer(ref, hyp), 3),
                    "detected": res.get("detected_language_code"), "hyp": res["transcript"],
                })
                print(f"{row['file']:<14} {mode:<5} WER={results[-1]['wer']:<6} CER={results[-1]['cer']:<6} {res['transcript']}")
    if results:
        os.makedirs("out", exist_ok=True)
        with open("out/wer_results.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
        print("\nsaved out/wer_results.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/transcripts.csv")
    ap.add_argument("--modes", nargs="+", default=["auto", "lang"], choices=["auto", "lang"])
    a = ap.parse_args()
    asyncio.run(run(a.csv, a.modes))
