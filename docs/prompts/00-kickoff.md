# Kickoff prompt (paste into Antigravity or Codex after opening the repo root)

Use **Planning mode** (not Fast). Recommended model: Claude Opus for this first task, then Sonnet for implementation tasks.

---

You are joining a solo developer building **Kisan Saathi** for the Gnani "Great Indian AI Internship" challenge. The hard deadline is **10 Nov 2026**; today is **1 Nov 2026**. Quality of evidence and honesty matter as much as features.

## Step 1: Read
Read completely and in this order: `AGENTS.md`, `prd.md`, `architecture.md`, `rules.md`, `phases.md`, `docs/decisions.md`, `docs/gnani-api-notes.md`, `docs/whatsapp-integration.md`, `docs/data-sources.md`, `docs/evaluation-plan.md`, `design.md`, `config/pilot.example.yaml`.

## Step 2: Audit the existing code (do not modify anything yet)
The folder `existing-code/` contains a working starter that already implements: a FastAPI WhatsApp webhook (verification, signature check, dedupe, background processing), a Gnani Prisma/Timbre REST client, ffmpeg audio helpers (OGG/Opus <-> WAV, chunking to <= 25 s), an OpenAI-compatible LLM adapter with an echo mode, a voice-note pipeline with per-stage latency logging, a WER evaluation script and webhook tests (5 passing). It has **not** been run against the real Gnani or Meta APIs.

Produce `docs/code-audit.md` containing:
1. A file-by-file summary of what exists and how it maps onto the target layout in `architecture.md` section 5.
2. Verified-against-docs check: compare every Gnani request/response detail in the code with `docs/gnani-api-notes.md`; list mismatches and risks.
3. Bugs, race conditions, security issues (for example signature verification when the secret is empty, in-memory dedupe across multiple workers, temp-file handling, error paths, missing timeouts, logging of PII).
4. Test coverage gaps.
5. A migration plan: ordered steps to move it into `backend/app/...` without losing behaviour, keeping tests green.
6. Anything in the pack's documents that conflicts with the code or with itself.

## Step 3: Propose the Phase 0 and Phase 1 plan
Write a short plan (checklist with file names) for **Phase 0 and Phase 1 only** from `phases.md`. Include which tasks need the developer's manual action (API keys, Meta dashboard, recording clips) and which you can do now.

## Step 4: STOP and report
Stop after Steps 2 and 3. Do not implement anything. Report:
- The audit highlights (top 5 risks).
- The plan and your estimate of effort per task.
- Questions or decisions you need (only genuinely blocking ones; use the defaults in `docs/decisions.md` for the rest).

## Constraints
- Follow `rules.md` strictly. Do not invent Gnani parameters. Do not call external APIs without keys; never print or commit secrets.
- Do not choose the pilot region or crops yourself; use `config/pilot.example.yaml` as the proposed default and say so.
- Do not add WhatsApp calling, PSTN, accounts or payments.
- Be explicit about what you verified by running code versus what you read.
