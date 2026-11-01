# Kisan Saathi: Agent Instructions

Read by Codex, Antigravity (v1.20.3+) and other coding agents. This file is the single source of truth for working rules.

## What we are building
A WhatsApp-first voice assistant for farmers (Telugu, Hindi, English; Hinglish tested) for the **Gnani "Great Indian AI Internship" challenge**. **Hard deadline: 10 Nov 2026** (treat 9 Nov as the real deadline). A solo developer is building it, so scope discipline matters more than features.

Pipeline: voice note -> Gnani **Prisma** (STT) -> **Evon** (LLM, via an OpenAI-compatible adapter) with tools (mandi prices, weather, crop Q&A grounded in Kisan Call Centre data) -> Gnani **Timbre** (TTS) -> voice note back.

## Read first (in this order)
1. `prd.md` (scope, acceptance criteria)
2. `architecture.md` (boundaries, contracts)
3. `rules.md` (safety, evidence, security, code rules: these are invariants)
4. `phases.md` (the ACTIVE phase and its exit criteria)
5. `docs/decisions.md` (what is decided; do not re-decide)
6. `docs/gnani-api-notes.md`, `docs/whatsapp-integration.md`, `docs/data-sources.md` (verified integration facts)
7. `design.md` only when touching the frontend; `docs/evaluation-plan.md` only when touching evaluation.

## Working method
1. Inspect the repository (including `existing-code/` if present) before editing anything.
2. For any task longer than a few files: **write a short plan first and wait for approval**.
3. Implement only the active phase/task. No scaffolding of future phases.
4. Small, reviewable commits. Do not rewrite large working files without reason.
5. Backend: Python 3.11 + FastAPI + Pydantic v2. Frontend: Next.js + TypeScript (minimal, web demo only). Do not add frameworks without justification.
6. All provider calls (Gnani, LLM, data.gov.in, Open-Meteo, Meta) happen server-side behind adapters in `backend/app/integrations/` or `backend/app/channels/`.
7. **Never invent API parameters.** Gnani endpoints are recorded in `docs/gnani-api-notes.md` (verified from docs.gnani.ai). If something is not there, check the live docs or ask.
8. Never produce a factual agricultural claim without retrieved evidence (see `rules.md`).
9. Unit tests use fixtures; live calls are separate, clearly labelled smoke tests under `backend/tests/live/` and are skipped without keys.
10. Never commit secrets, private audio, or personal data. Phone numbers are stored only as salted hashes.

## Completion report (every task)
- Files changed; exact commands run; test results.
- **Verified live** vs **mocked** integrations, stated separately.
- Assumptions, open issues, next suggested task.
- Update docs when contracts or behaviour change.

## Product boundary (MVP)
In: WhatsApp voice/text channel, web voice demo, mandi + weather tools, KCC-grounded crop Q&A with refusals, evaluation scripts, small dashboard.
Out until all MVP exit criteria pass: PSTN calling, native apps, image diagnosis, pesticide/fertiliser dosage generation, accounts/payments, model fine-tuning.
