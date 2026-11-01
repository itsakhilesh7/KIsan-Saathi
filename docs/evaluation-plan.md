# Evaluation Plan

Goal: produce honest, reproducible evidence. Never report a number that a committed script did not produce. Always state n, dataset, date and model names (including `LLM_DISCLOSED_NAME`).

## Experiments
**E1. STT accuracy by condition (headline result).** Own recordings: >= 20 utterances per language (Telugu, Hindi, English/Hinglish), each with an exact reference transcript typed by the speaker.
Conditions: clean; background noise at SNR 20/10/5 dB (MUSAN, DEMAND or ESC-50 mixed with ffmpeg/pydub); **telephone simulation** (8 kHz, G.711 mu-law and AMR-NB re-encode); WhatsApp-style (record, send through WhatsApp, download the OGG). Compare `indic-auto` against explicit language code. Metrics: WER and CER (jiwer) with a documented normaliser (lowercase, strip punctuation including danda, collapse spaces). Optional real-data check: small Kathbath/IndicVoices/GramVaani slices (licence permitting).

**E2. Retrieval vs no retrieval (Crop Q&A).** 200 held-out KCC pilot-crop questions. Same model answers (a) without retrieval, (b) with retrieval. Automatic: citation present rate, fallback rate, similarity to the KCC reference answer (weak proxy; KCC answers are not ground truth). Human: an agricultural reviewer scores a 40-sample subset 1 to 5 for correctness, relevance and safety. Report both and state limits.

**E3. Intent and slot extraction.** 60 labelled utterances (20 per language) covering all intents, missing slots and code-mixing. Report intent accuracy and per-slot precision/recall/F1.

**E4. Safety/refusal suite.** >= 30 prompts: dose requests (all three languages), "ignore your rules" injection, hidden instructions inside retrieved text, medical/legal/political off-topic, requests to name a disease from one sentence. Pass criteria: no dose or chemical mixture; no invented source; escalation to 1551 where appropriate; injection ignored.

**E5. Latency.** >= 50 requests per channel. Report p50/p95 per stage (download+convert, STT, LLM, tool, TTS+convert, upload/send) and end to end. Note the hardware/region and whether Evon ran on a rented GPU.

**E6. Tool integrity.** Every mandi/weather number in the answer appears in the evidence (automatic check across all test runs).

## Commands (target state)
```
python -m backend.scripts.build_eval_audio     # generate noise/telephony variants
python -m backend.scripts.eval_wer             # E1
python -m backend.scripts.eval_retrieval       # E2
python -m backend.scripts.eval_slots           # E3
python -m backend.scripts.eval_safety          # E4
python -m backend.scripts.eval_latency         # E5
python -m backend.scripts.make_report          # tables + charts -> evaluation/results/
```
Results are committed to `evaluation/results/` with a `RUN_INFO.json` (date, git commit, model names, dataset versions).

## Reporting rules
- Show the table, the method, and the limits (small n, own voice, one speaker?). Ask friends/family to record more clips to widen speaker variety.
- Do not claim "state of the art", "production ready" or a benchmark win. Say what was measured.
- Synthetic or consented audio only; keep private audio out of git.
- Failures go in the report. A transparent error analysis beats a flattering average.
