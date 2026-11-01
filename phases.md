# Kisan Saathi: Phases (1 Nov to 10 Nov 2026)

**Day 1 = Sun 1 Nov.** Hard deadline Tue 10 Nov. **Internal submission target: end of Mon 9 Nov.** 10 Nov is buffer only: no new features.

Engagement on public posts counts toward shortlisting, so post early (see `docs/submission-and-awards.md`).

## Priority order if time slips (cut from the bottom)
1. WhatsApp voice loop with Prisma + Timbre (echo mode)
2. Mandi + weather tools with grounded answers
3. Web demo (judges' link)
4. Evaluation: WER by noise condition (the strongest evidence)
5. KCC crop Q&A with safe fallback
6. Evon on a rented GPU (disclose if not achieved)
7. Dashboard
8. Hindi pilot B, click-to-call, extras

## Phase 0: Access, decisions, repo audit (Sun 1 Nov)
- Gnani key works: one Prisma and one Timbre call (te-IN, hi-IN, en-IN).
- Record 10 reference clips + transcripts.
- Verify data.gov.in mandi schema and that pilot markets/crops return rows; locate KCC resource IDs.
- Meta: test number active, `hello_world` received, recipient verified.
- Agent audits `existing-code/`, writes `docs/code-audit.md`, proposes migration plan.
- Confirm `config/pilot.yaml`.
**Exit:** live STT+TTS proof or a documented blocker; one live mandi response; audit report approved.

## Phase 1: Backend foundation and migration (Mon 2 Nov)
- Migrate existing code into the layered structure without losing tests; typed Settings; `/api/health`; request IDs; structured logs; provider errors.
- Audio service with validation; adapters for Prisma/Timbre; baseline WER script on the 10 clips.
**Exit:** local API returns a transcript for a test file; tests green; baseline WER table produced.

## Phase 2: WhatsApp live loop (Tue 3 Nov)
- Webhook (verify, signature, dedupe, background), media download/upload, voice reply, fallback messages. Tunnel for local testing.
- **Teaser post this evening** (30 s clip: voice note in, voice note out).
**Exit:** a real phone sends a voice note and receives a voice reply, recorded on video. Echo mode is acceptable.

## Phase 3: Tools, intent, grounded answers (Wed 4 Nov)
- Mandi and weather connectors with Evidence normalisation; intent/slot extraction with a stand-in LLM; clarification loop; answer composer + number/citation validator.
**Exit:** Telugu/Hindi/English test queries route correctly; empty results handled honestly; no uncited numbers.

## Phase 4: Crop Q&A over KCC + safety (Thu 5 Nov)
- KCC ingestion/cleaning/index; retrieval with thresholds; `safety.py` chemical stripping; refusal suite; fallback to 1551.
**Exit:** supported-crop questions cite KCC records; refusal suite passes; weak retrieval falls back.

## Phase 5: Evon, web demo, dashboard (Fri 6 Nov)
- Rent a GPU, serve Evon (vLLM/SGLang), switch the adapter, rerun the tests; record `LLM_DISCLOSED_NAME`.
- Minimal Next.js demo; small dashboard.
**Exit:** web demo works locally end to end; Evon verified or the exact blocker documented.

## Phase 6: Evaluation and deploy (Sat 7 Nov)
- Run the full evaluation (noise/telephony WER, retrieval comparison, slot F1, refusal, latency); commit results and charts.
- Deploy API + web + DB; set the Meta webhook to the deployed URL; system-user token.
- **Main demo video + post goes up today** to maximise engagement time.
**Exit:** public web URL; reproducible results; webhook live on the deployed host.

## Phase 7: Hardening and review (Sun 8 Nov)
- Native-speaker review of Telugu/Hindi wording and TTS pronunciation (family/friends).
- Fix top failures; load/latency check; secrets audit; README; written explanation draft.
- Record the 60-second demo.
**Exit:** no known critical bugs; docs accurate; demo recorded.

## Phase 8: Submission (Mon 9 Nov)
- Final write-up, video upload, post links, checklist from `docs/submission-and-awards.md`; submit. Verify the submission page for the exact format.
**Exit:** submitted with screenshots of confirmation.

## Tue 10 Nov
Buffer. Fixes to submission problems only.

## Per-phase report template
Status | Implemented | Tests run | Live integrations verified | Mocked | Open issues | Decision needed | Evidence (video/screenshot/result file)
