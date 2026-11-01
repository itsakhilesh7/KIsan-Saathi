# Kisan Saathi: Progress Log

## START HERE
Kisan Saathi is a WhatsApp-first voice assistant for Indian farmers (Telugu, Hindi, English; Hinglish tested) built for the Gnani Internship Challenge (Deadline: 10 Nov 2026). Pipeline: voice note -> Gnani Prisma STT v3.0 -> Evon LLM (OpenAI-compatible adapter with echo fallback and disclosure) with allowlisted tools (mandi prices from data.gov.in, weather from Open-Meteo, crop Q&A from KCC records) -> Gnani Timbre TTS -> voice note back. No pesticide/fertiliser doses are ever generated. All facts come from retrieved evidence.

### Phase Status (P0..P8)
- **P0 (Access & Audit):** Done (offline parts complete; live API keys pending from developer).
- **P1 (Backend Foundation & Migration):** Done (migrated, hardened, 16 unit tests passing).
- **P2 (WhatsApp Live Loop):** Not started (starts upon developer confirmation of Meta credentials).
- **P3 (Tools, Intent, Grounded Answers):** Not started.
- **P4 (Crop Q&A + Safety):** Not started.
- **P5 (Evon, Web Demo, Dashboard):** Not started.
- **P6 (Evaluation + Deploy):** Not started.
- **P7 (Hardening & Review):** Not started.
- **P8 (Submission):** Not started.

### What works right now
- Backend FastAPI app with Request-ID middleware, structured JSON logging, and `/api/health`.
- Hardened WhatsApp webhook with constant-time HMAC-SHA256 signature checking and SQLite deduplication.
- Typed `Settings` reading all `.env.example` keys; startup warning on unconfirmed pilot.
- Gnani Prisma STT & Timbre TTS adapters with explicit timeouts, 429/5xx retries, and language normalization.
- OpenAI-compatible LLM adapter with zero-dependency echo mode and mandatory model name disclosure.
- Audio transcoding & chunking service (`to_wav16k`, `wav_to_ogg_opus`, `split_wav`).
- To run: `pytest backend/tests/` (16 unit tests passing, 2 live smoke tests skipped without keys).

### Verified LIVE vs only MOCKED
| Integration | Status | Verification Note |
|---|---|---|
| Gnani Prisma STT | MOCKED | Endpoint & headers coded per docs; live call requires `GNANI_API_KEY`. |
| Gnani Timbre TTS | MOCKED | Endpoint & voice mapping coded per docs; live call requires `GNANI_API_KEY`. |
| Meta Webhook | MOCKED | Handshake & signature verified with fixtures; live loop requires Meta setup. |
| data.gov.in | MOCKED | Schema placeholder ready; requires `DATA_GOV_API_KEY` live check. |
| Open-Meteo | MOCKED | Schema placeholder ready; implementation in Phase 3. |
| Evon / LLM | MOCKED | Tested locally in echo mode; live completions require `LLM_BASE_URL`. |
| Persistence (SQLite) | VERIFIED LIVE | `data/dedup.sqlite3` initialized and verified across tests. |

- **Known issues and risks:** Windows loopback sockets in sandbox mode block synchronous `TestClient` unless running with sandbox bypass or live network. Prisma STT live language code format is unverified (`format unverified` normalization layer in place).
- **Needs from developer:** Fill `GNANI_API_KEY`, `WHATSAPP_*` credentials in `backend/.env` per `docs/MANUAL_TASKS.md`.
- **Decisions pending:** D-008 (Hosted embedding API choice), D-009 (Evon hosting on Discord), D-010 (Pilot confirmation).
- **Exact next recommended task:** Phase 2 (WhatsApp live loop) once developer supplies Meta credentials.

---

## LOG

### [2026-11-01 23:40] Phase 0 & Phase 1 Backend Foundation & Migration Complete
- **Goal and phase:** Phase 0 (access, decisions, audit) and Phase 1 (backend foundation & starter code migration).
- **What changed:**
  - Workspace scaffolding: unpacked agent pack to root and starter code to `existing-code/` (preserved as reference snapshot). Added `*.zip` to `.gitignore`. Copied `config/pilot.example.yaml` to `config/pilot.yaml` with `confirmed: false`.
  - Created `docs/code-audit.md`: detailed file-by-file analysis, line-by-line Gnani spec comparison, audit of 8 suspect vulnerability areas, test coverage gaps, and migration plan.
  - Created `docs/MANUAL_TASKS.md`: prioritized human checklist for Gnani key, Meta developer setup, FFmpeg installation, data.gov.in key, and Evon access clarification.
  - Scaffolded full target hierarchy from `architecture.md` Section 5 with README placeholders for later phases.
  - Implemented `backend/app/core/config.py`: typed Pydantic `Settings` reading all 34 `.env.example` keys, `pilot.yaml` parsing with `confirmed: false` startup warning, and properties (`llm_mode`, `is_production`, `wa_graph`).
  - Implemented `backend/app/core/logging.py`: Request-ID context tracing, structured JSON logging, and salted phone number hashing (`hash_phone`).
  - Implemented `backend/app/core/security.py`: constant-time signature comparison, production `META_APP_SECRET` enforcement, and audio MIME validation.
  - Implemented `backend/app/schemas/`: strict contracts for `evidence.py`, `intent.py`, `conversation.py`, and `common.py`.
  - Implemented `backend/app/integrations/gnani/`: `stt.py`, `tts.py`, `errors.py` with explicit timeouts, 429/5xx bounded retries, and language normalization layer.
  - Implemented `backend/app/integrations/llm/`: `base.py`, `openai_compatible.py` with echo mode and mandatory model disclosure.
  - Implemented `backend/app/repositories/deduplication.py`: SQLite-backed persistent deduplication (`data/dedup.sqlite3`) and in-memory test implementation.
  - Implemented `backend/app/channels/whatsapp/`: `signature.py`, `parser.py`, `client.py`, and `webhook.py`.
  - Implemented `backend/app/services/audio_service.py` and `orchestrator.py`: transcoding, chunking (<= 25s), and async pipeline.
  - Implemented `backend/app/api/routes/health.py`: `/api/health` returning status and credential presence booleans (never secret values).
  - Implemented `backend/app/main.py`: FastAPI app with Request-ID middleware and lifespan.
  - Ported and enhanced `backend/scripts/test_gnani.py` and `backend/scripts/eval_wer.py` (supporting WER/CER by language and mode).
  - Built comprehensive test suite in `backend/tests/`: 16 unit tests (all passing) and 2 live smoke tests (skipped without keys).
  - Wrote root `README.md` with complete architecture diagram, setup instructions, and quickstart commands.
- **Commands run and their real results:**
  - `git init`: initialized repository.
  - `pip install -r existing-code/requirements.txt`: installed initial dependencies.
  - `pytest existing-code/tests/`: baseline 5 passed in 1.86s.
  - `ruff check backend/`: 45 formatting/import issues detected, all auto-fixed (`ruff check --fix`), 0 remaining.
  - `pytest backend/tests/ -v`: 16 passed, 2 skipped (LIVE without keys) in 2.64s.
- **Tests:** 16 passed (MOCKED), 2 skipped (LIVE: `test_live_timbre_tts_telugu`, `test_live_timbre_tts_hindi`), 0 failed.
- **Decisions made and assumptions:**
  - Standardized on 25s audio chunking threshold per `architecture.md` precedence.
  - Implemented persistent SQLite deduplication to replace volatile in-memory cache.
  - Created language normalization layer between Prisma and Timbre to prevent HTTP 400 errors.
- **Problems encountered and how they were resolved:**
  - Standard sandbox mode network isolation blocked loopback sockets used by Python asyncio `_fallback_socketpair` in `TestClient`. Resolved by verifying with sandbox bypass for local socket operations.
- **Open issues and what the developer must do next:**
  - Developer must obtain Gnani API key and Meta WhatsApp credentials per `docs/MANUAL_TASKS.md` Priority 1.
- **Git commit hash and message:**
  - Prior commit: `165b8be` ("chore: scaffold repository from agent pack and starter code").
  - New commit: pending final Part 6 commit.
