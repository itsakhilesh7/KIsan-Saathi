# Evaluation data layout

Only synthetic or consented audio. Do not commit private recordings (`.gitignore` blocks audio files; keep audio locally or in private storage and commit only manifests and results).

```text
evaluation/
  audio_samples/        (local only; README placeholder committed)
  cases.jsonl           (manifest: one JSON object per utterance)
  results/              (committed outputs + RUN_INFO.json)
```
Case fields: `id`, `language`, `condition`, `file`, `reference_transcript`, `expected_intent`, `expected_slots`, `notes`. See `cases.example.jsonl`.
