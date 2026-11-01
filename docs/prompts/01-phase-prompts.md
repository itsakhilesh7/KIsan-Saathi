# Phase prompts

Paste one at a time, only after the previous phase report is reviewed. Each begins with: "Read `AGENTS.md`, `rules.md`, and the active phase in `phases.md`. Write a short plan and wait for approval before coding." Recommended models: **Sonnet** for implementation; **Opus** for P4 (retrieval/safety design) and any hard debugging; **Gemini Flash** for boilerplate tests, docs and data-cleaning scripts.

## P1: Backend foundation and migration
Migrate `existing-code/` into `backend/app/` following `architecture.md` section 5, keeping all behaviour and tests. Add: typed `Settings` (one place for env reads), `/api/health` (config presence flags, no values), request-ID middleware, structured logging, explicit provider errors with timeouts and bounded retries, upload validation, Pydantic schemas for intent/evidence/response. Add `backend/tests/live/` with skipped-without-keys smoke tests for Prisma and Timbre. Port `eval_wer.py` and make it report by language and mode. Report tests run, and say which results are mocked.

## P2: WhatsApp live loop
Make the webhook production-minded: refuse to start in production without `META_APP_SECRET`; dedupe that survives restarts (database or TTL store); media size/duration limits; graceful fallback messages in the user's language; read-receipt optional. Add a Telegram adapter only if I say Meta is blocked. Provide a manual test script and a checklist from `docs/whatsapp-integration.md`. Do not claim success until I confirm a real phone worked.

## P3: Tools, intent and grounded answers
Implement mandi and weather connectors from the **live-verified** schema (I will paste a real sample response; do not guess fields), the Evidence model and validator, intent/slot extraction with strict JSON and one retry, the dialogue state with TTL, the answer composer, and a post-check that every number appears in the evidence. Tests: fixtures for parsing, empty results, stale dates, missing fields, prompt-injection strings inside tool data.

## P4: KCC retrieval and safety
Ingest KCC records for the pilot state using the live-verified fields; cleaning and dedupe scripts that keep `raw_text`; build the index offline (embedding provider via `docs/decisions.md` D-008); retrieval with metadata filters, threshold and fallback to 1551; `safety.py` that strips chemical names/doses when `ALLOW_CHEMICAL_DETAILS=false`; refusal suite (E4) as automated tests; a data-quality report (language mix, empties, duplicates). Show me 10 retrieved examples before wiring into answers.

## P5: Evon, web demo, dashboard
Add the OpenAI-compatible Evon configuration and a connectivity check that records the exact model name served. Build the minimal Next.js demo per `design.md` (record/upload/text, transcript, answer, audio, source cards, model names used). Add `/api/dashboard/summary` and a simple page. No new features beyond `prd.md`.

## P6: Evaluation and deploy
Implement scripts E1 to E6 from `docs/evaluation-plan.md`, a report generator that writes tables/charts and `RUN_INFO.json`, deployment configs for API (Render/Railway/Fly) and web (Vercel), keep-alive guidance, and a secrets audit of the repository and git history. I will run the evaluations that need my recordings and GPU.

## P7: Hardening
Fix the top failures from evaluation. Add rate limiting and CORS settings, error pages, a README with exact setup and evaluation commands, an architecture diagram, and a "limitations" section. Prepare screenshots/evidence list for the submission.

## P8: Submission support
Do not add features. Help finalise README, the written explanation using `docs/submission-and-awards.md`, and a final checklist run. Flag any claim in the write-up that is not backed by a committed result.
