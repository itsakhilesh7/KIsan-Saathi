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
- Production startup fail-fast checks (rejects empty `META_APP_SECRET` and default `PHONE_HASH_SALT` / `WHATSAPP_VERIFY_TOKEN`).
- Outbound HTTP connection pooling via shared `httpx.AsyncClient` (`core/http_client.py`) across WhatsApp, Gnani, and LLM adapters.
- Audio limits: streaming download size guard (`AUDIO_MAX_MB`), duration limit check (`AUDIO_MAX_SECONDS`), and MIME type allowlist.
- Persistent non-blocking audit events (`repositories/events.py` in SQLite + JSONL); transcripts omitted by default (`STORE_RAW_TRANSCRIPTS=false`).
- Fully language-aware prompts (empty transcript, audio too long, fallbacks) across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
- Typed `Settings` reading all `.env.example` keys; startup warning on unconfirmed pilot.
- Gnani Prisma STT & Timbre TTS adapters with explicit timeouts, 429/5xx retries, and language normalization.
- OpenAI-compatible LLM adapter with zero-dependency echo mode and mandatory model name disclosure.
- Audio transcoding & chunking service (`to_wav16k`, `wav_to_ogg_opus`, `split_wav`).
- To run: `pytest backend/tests/` (unit tests passing, live smoke tests skipped without keys).

### Verified LIVE vs only MOCKED
| Integration | Status | Verification Note |
|---|---|---|
| Gnani Prisma STT | MOCKED | Endpoint & headers coded per docs; live call requires `GNANI_API_KEY`. |
| Gnani Timbre TTS | MOCKED | Endpoint & voice mapping coded per docs; live call requires `GNANI_API_KEY`. |
| Meta Webhook | MOCKED | Handshake & signature verified with fixtures; live loop requires Meta setup. |
| data.gov.in | MOCKED | Schema placeholder ready; requires `DATA_GOV_API_KEY` live check. |
| Open-Meteo | MOCKED | Schema placeholder ready; implementation in Phase 3. |
| Evon / LLM | MOCKED | Tested locally in echo mode; live completions require `LLM_BASE_URL`. |
| Persistence (SQLite) | unit-tested, local SQLite | SQLite dedup and events tables verified across unit tests with `tmp_path`. |

- **Known issues and risks:** Windows loopback sockets in sandbox mode block synchronous `TestClient` unless running with sandbox bypass or live network. Prisma STT live language code format is unverified (`format unverified` normalization layer in place).
- **Needs from developer:** Fill `GNANI_API_KEY`, `WHATSAPP_*` credentials in `backend/.env` per `docs/MANUAL_TASKS.md`.
- **Decisions pending:** D-008 (Hosted embedding API choice), D-009 (Evon hosting on Discord), D-010 (Pilot confirmation).
- **Exact next recommended task:** Phase 2 (WhatsApp live loop) once developer supplies Meta credentials.

---

## LOG

### [2026-11-02 00:08] Phase 1.5 Hardening Pass Complete
- **Goal and phase:** Phase 1.5 short hardening pass before Phase 2.
- **What changed:**
  - Resolved `TTS_DEFAULT_LANG` bug: added field to `Settings` making it single source of truth; fixed `AttributeError` when STT returns `None`.
  - Added unit test for `SQLiteDeduplicationRepository` using `tmp_path` verifying initial call `False`, repeat call `True`, and persistence across new instances.
  - Added production fail-fast check in `lifespan`: raises `RuntimeError` at startup if `META_APP_SECRET` is empty, or if `PHONE_HASH_SALT` / `WHATSAPP_VERIFY_TOKEN` use default placeholder values. Added 4 unit tests.
  - Implemented shared outbound `httpx.AsyncClient` connection pool in `backend/app/core/http_client.py` initialized during lifespan and reused by WhatsApp client, Gnani STT/TTS, and LLM adapters.
  - Enforced audio limits: streaming download size guard (`AUDIO_MAX_MB`), audio duration check (`AUDIO_MAX_SECONDS`) before STT, and MIME validation (`validate_media_type`). Added unit tests.
  - Implemented persistent event logging in `backend/app/repositories/events.py` (SQLite + JSONL) with non-blocking async execution. Added `STORE_RAW_TRANSCRIPTS: bool = False` setting (transcripts stored only if explicitly enabled).
  - Language-aware prompts: added `EMPTY_TRANSCRIPT_MESSAGES`, `FALLBACK_MESSAGES` (with 1551 advice), `AUDIO_TOO_LONG_MESSAGES`, and `UNSUPPORTED_MEDIA_MESSAGES` covering `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
  - Removed local absolute path from `README.md`. Confirmed GitHub repository is public via unauthenticated curl check.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_tts_default_lang.py`: reproduced failure, then passed after fix.
  - `pytest backend/tests/unit/test_deduplication.py`: passed (1 passed in 0.30s).
  - `pytest backend/tests/unit/test_lifespan_production.py`: passed (4 passed in 1.02s).
  - `pytest backend/tests/unit/test_audio_limits.py`: passed (2 passed in 1.00s).
  - `pytest backend/tests/unit/test_orchestrator_hardening.py`: passed (3 passed in 1.22s).
  - `pytest backend/tests/unit/test_events_repository.py`: passed (1 passed in 0.21s).
- **Tests:** 28 unit tests passed, 2 live skipped.
- **Git commit hash and message:** pending commit for Phase 1.5.

### [2026-11-01 23:50] Remote Repository Linked and Pushed to GitHub
- **Goal and phase:** Remote repository setup (Phase 0/1 milestone completion).
- **What changed:** Added remote `origin` (`https://github.com/itsakhilesh7/KIsan-Saathi.git`), renamed local branch to `main`, and pushed initial commit history.
- **Commands run and their real results:**
  - `git branch -M main`: successfully switched to `main`.
  - `git remote add origin https://github.com/itsakhilesh7/KIsan-Saathi.git`: added origin remote.
  - `git push -u origin main`: successfully pushed `main -> main`. Tracking set up.
- **Tests:** 16 unit tests passing, 2 live skipped.
- **Git commit hash and message:** `b0412f8` ("chore: normalize line endings across repo").

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
  - Current commit: `555f377` ("feat: complete Phase 0 audit and Phase 1 backend foundation").
