# Kisan Saathi: Progress Log

## START HERE
Kisan Saathi is a WhatsApp-first voice assistant for Indian farmers (Telugu, Hindi, English; Hinglish tested) built for the Gnani Internship Challenge (Deadline: 10 Nov 2026, treating 9 Nov as the real target). Pipeline: voice note -> Gnani Prisma STT v3.0 -> Evon LLM (OpenAI-compatible adapter with echo fallback and disclosure) with allowlisted tools (mandi prices from data.gov.in, weather from Open-Meteo, crop Q&A from KCC records) -> Gnani Timbre TTS -> voice note back. No pesticide/fertiliser doses are ever generated. All facts come from retrieved evidence.

**REPOSITORY VISIBILITY WARNING:** The GitHub remote repository (`https://github.com/itsakhilesh7/KIsan-Saathi.git`) is confirmed **PUBLIC**. All commits and history are publicly visible. Do NOT stage or commit real API keys, tokens, `.env` files, or raw audio recordings. Always run `python scripts/scan_secrets.py` before pushing.

### Phase Status (P0..P8)
- **P0 (Access & Audit):** Done (offline parts complete; live API keys pending from developer).
- **P1 (Backend Foundation & Migration):** Done (migrated, hardened, Phase 1.5, 1.6 & 1.7 complete; 42 unit tests passing).
- **P2 (Live Loop / Telegram Channel Fallback):** In Progress. WhatsApp live steps paused due to Meta test account blocker (error 131031: "Business Account locked" on every send). Activated Telegram fallback channel (D-002) for immediate live pipeline development and testing without tunnel requirement.
- **P3 (Tools, Intent, Grounded Answers):** Phase 3A (Mandi Connector & First Grounded Answer) Done (69 unit tests passing). Weather and KCC pending Phase 3B/3C.
- **P4 (Crop Q&A + Safety):** Not started.
- **P5 (Evon, Web Demo, Dashboard):** Not started.
- **P6 (Evaluation + Deploy):** Not started.
- **P7 (Hardening & Review):** Not started.
- **P8 (Submission):** Not started.

### What works right now
- Backend FastAPI app with Request-ID middleware, structured JSON logging, and `/api/health`.
- Hardened WhatsApp webhook with constant-time HMAC-SHA256 signature checking and SQLite deduplication.
- Production startup fail-fast checks (rejects empty `META_APP_SECRET` and default `PHONE_HASH_SALT` / `WHATSAPP_VERIFY_TOKEN`).
- Outbound HTTP connection pooling via shared `httpx.AsyncClient` (`core/http_client.py`) with sensible defaults and enforced per-request timeouts (STT 60s, TTS 90s, LLM 120s, WhatsApp media 60s).
- Audio limits: streaming download size guard (`AUDIO_MAX_MB`), duration limit check (`AUDIO_MAX_SECONDS=60`), chunking for 25-60s, and MIME type allowlist (`audio/ogg`, `audio/wav`, `audio/mp4` for m4a, `audio/aac`, `audio/amr`, `audio/mpeg`).
- User preference persistence (`repositories/user_preferences.py`): tracks last seen language per salted phone hash; unknown-language fallbacks strictly route to pilot primary language (`te-IN` Lavanya).
- Persistent non-blocking audit events (`repositories/events.py` in SQLite + JSONL); transcripts omitted by default (`STORE_RAW_TRANSCRIPTS=false`).
- Fully language-aware prompts (empty transcript, audio too long, fallbacks referencing 1551) across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
- Telegram fallback channel adapter & poller (`channels/telegram/`) with token log-redaction filter.
- Agmarknet daily mandi price connector (`integrations/data_gov/mandi.py`) with pagination, retries on 429/5xx, sanitized source URLs, and normalization to `Evidence` schema.
- Commodity alias dictionary (`config/commodity_aliases.yaml`) mapping farmer terms in Telugu, Hindi, and English strictly to confirmed dataset strings.
- Rule-based intent and slot extraction (`services/intent_service.py`) and 10-minute TTL dialogue state repository (`repositories/dialogue_state.py`) supporting multi-turn clarification.
- Grounded answer composer (`services/answer_composer.py`) enforcing $\le 3$ sentences, strictly verified numbers against `Evidence`, first-turn AI identity disclosure, and daily reported price caveat.
- LLM adapter supporting `LLM_EXTRA_BODY_JSON` payload merging for Evon inference flags.
- Complete unit test suite: 69 unit tests passing in ~7s (`pytest backend/tests/unit/`).

### Verified LIVE vs only MOCKED
| Integration | Status | Verification Note |
|---|---|---|
| Gnani Prisma STT | MOCKED | Endpoint & headers coded per docs; live call requires `GNANI_API_KEY`. |
| Gnani Timbre TTS | MOCKED | Endpoint & voice mapping coded per docs; live call requires `GNANI_API_KEY`. |
| Meta Webhook / Send | BLOCKED (Error 131031) | Meta test account returns error 131031 ("Business Account locked"). Handshake & signature verified in mocks. WhatsApp live steps paused. |
| Telegram Channel | In Development | Fallback channel per D-002; long-polling via Bot API without tunnel. |
| data.gov.in (Agmarknet Mandi) | LIVE Verified | Verified live on 2026-11-04 (HTTP 200, 331 records returned for Telangana; sanitized fixture in `backend/tests/fixtures/mandi_telangana_sample.json`). |
| Open-Meteo | MOCKED | Schema placeholder ready; implementation in Phase 3. |
| Evon / LLM | MOCKED | Tested locally in echo mode; live completions require `LLM_BASE_URL`. |
| Persistence (SQLite) | unit-tested, local SQLite | SQLite dedup, events, user preferences, and dialogue state tables verified with `tmp_path`. Ephemeral hosting note: SQLite loses data on redeploy; will move events to Supabase/PostgreSQL in Phase 6. |

- **Known issues and risks:** Windows loopback sockets in sandbox mode block synchronous `TestClient` unless running with sandbox bypass or live network. Prisma STT live language code format is unverified (`format unverified` normalization layer in place). **SQLite on Ephemeral Hosting:** Hosting platforms (e.g., Render, Railway without persistent disks) reset local SQLite files on redeployment; audit events and deduplication tables will migrate to managed Supabase/Postgres (`DATABASE_URL`) in Phase 6.
- **Needs from developer:** Fill `GNANI_API_KEY`, `WHATSAPP_*` credentials in `backend/.env` per `docs/MANUAL_TASKS.md`.
- **Decisions pending:** D-008 (Hosted embedding API choice), D-009 (Evon hosting on Discord), D-010 (Pilot confirmation).
- **Exact next recommended task:** Developer provides live Gnani and Meta responses to confirm real formats before Phase 2.

---

## LOG

### [2026-11-04 16:30] Phase 3A: Mandi Connector & First Grounded Answer Complete
- **Goal and phase:** Phase 3A. Connected data.gov.in Agmarknet daily mandi prices dataset, built commodity resolver, intent & slot extraction, multi-turn clarification with 10-minute TTL dialogue state, grounded answer composer, and integrated end-to-end with orchestrator.
- **What changed:**
  - **Live Agmarknet Mandi API Verified:** Verified live against `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070` returning HTTP 200 with 331 records for Telangana on 04/11/2026. Documented real facts: no unit field exists (prices described as "price as reported"), dates in `"DD/MM/YYYY"`. Saved sanitized, zero-secret fixture to `backend/tests/fixtures/mandi_telangana_sample.json`.
  - **Data Gov API Key Redaction:** Updated `TelegramTokenRedactionFilter` and `StructuredJsonFormatter` in `backend/app/core/logging.py` to regex-redact `api-key=[REDACTED]` from all URLs and log records.
  - **Commodity Aliases (`config/commodity_aliases.yaml` + `commodity_resolver.py`):** Mapped Telugu, Hindi, and English crop names strictly to confirmed Agmarknet canonical strings (Cotton, Paddy, Red Gram, Black Gram, Soyabean, Tomato, Green Chilli, Brinjal, etc.). No hallucinated strings.
  - **Mandi Connector (`backend/app/integrations/data_gov/mandi.py`):** Built typed query function `fetch_mandi_prices` with pagination, exponential backoff retries on 429/5xx, sanitized source URLs without API keys, date parsing to ISO, safe float price parsing, and normalization to `Evidence` schema contract.
  - **Dialogue State Repository (`backend/app/repositories/dialogue_state.py`):** Created persistent SQLite repository managing 10-minute TTL context for multi-turn clarification. Isolated via pytest `tmp_path` in `conftest.py`.
  - **Intent & Slot Extraction (`backend/app/services/intent_service.py`):** Rule-based intent classifier supporting `mandi_price_query`, `greeting_or_help`, and `unsupported_or_unclear`. Identifies missing commodity slots and flags clarification requirement.
  - **Grounded Answer Composer (`backend/app/services/answer_composer.py`):** Formats strictly verified responses in user's language ($\le 3$ sentences, verified numbers against `Evidence`, AI identity disclaimer on first turn, daily reported price caveat, and staleness warning if $> 3$ days). Formats currency cleanly (`రూపాయలు`, `रुपये`, `Rs`) to avoid abbreviation dot splitting.
  - **LLM Extra Body Support:** Added `LLM_EXTRA_BODY_JSON` to `Settings`, `.env.example`, and merged into completion payload for Evon generation flags.
  - **Orchestrator Integration (`backend/app/services/orchestrator.py`):** Wired `extract_intent`, `fetch_mandi_prices`, and `compose_mandi_answer` into both `handle_voice_message` and `handle_text_message`.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_mandi_connector.py`: 14 passed in 1.20s.
  - `pytest backend/tests/unit/`: 69 passed, 0 failed in 6.90s.
  - `ruff check backend/ scripts/`: All checks passed!
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 69 passed (1 live fixture verified + 68 mocked), 0 failed.

### [2026-11-04 15:20] Telegram Poller Import Fix & Token Log Redaction
- **Goal and phase:** Phase 2 Telegram pre-live hardening. Fixed runner script logger import and hardened token privacy against HTTP client URL leaks.
- **What changed:**
  - **Runner Import (`backend/scripts/run_telegram_polling.py`):** Fixed import from `configure_logging` to `setup_logging`. Added `configure_logging` alias in `backend/app/core/logging.py`.
  - **HTTP Logger Quieting (`backend/app/core/logging.py`):** Set `httpx` and `httpcore` loggers to `logging.WARNING` in `setup_logging` to prevent httpx from logging outbound request URLs containing bot tokens at INFO.
  - **Token Log Redaction Filter (`TelegramTokenRedactionFilter`):** Implemented regex redaction filter and formatter sanitizer scrubbing `/bot[0-9]+:[A-Za-z0-9_-]+` patterns to `/bot[REDACTED]`, attached to root logger and stream handler.
  - **Unit Tests (`backend/tests/unit/test_telegram_logging_and_runner.py`):** Added 4 test-first unit tests verifying runner module import, logger levels, regex filter behavior, and end-to-end token suppression in emitted log strings.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_telegram_logging_and_runner.py`: 4 passed in 0.36s.
  - `pytest backend/tests/unit/`: 54 passed, 0 failed in 9.62s.
  - `ruff check backend/ scripts/`: All checks passed!
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 54 passed (MOCKED), 0 failed.

### [2026-11-04 10:50] Telegram Channel Implementation (D-002 Fallback Active)
- **Goal and phase:** Phase 2 WhatsApp Live Loop fallback: Meta test account returned error 131031 ("Business Account locked"). Activated D-002 Telegram fallback channel to unblock live voice/text loop without requiring a public webhook tunnel.
- **What changed:**
  - **ChannelClient Protocol (`backend/app/channels/base.py`):** Created minimal abstract channel interface (`download_media`, `send_text`, `send_audio_bytes`) and implemented `WhatsAppChannelClient`.
  - **Orchestrator Refactor (`backend/app/services/orchestrator.py`):** Made `handle_voice_message`, `handle_text_message`, and `handle_incoming_message` channel-agnostic by taking optional `ChannelClient`, defaulting to `WhatsAppChannelClient` to keep 100% backward compatibility with existing tests. Logged audit events record the dynamic `channel` name (`whatsapp` or `telegram`).
  - **Telegram Bot Client (`backend/app/channels/telegram/client.py`):** Implemented `TelegramChannelClient` using `httpx`. Implements streaming voice download via `getFile` with `AUDIO_MAX_MB` guard, `sendMessage` (truncated to 4000 chars), and `sendVoice` (native OGG/Opus voice note with waveform). Redacts bot tokens in logs.
  - **Telegram Poller (`backend/app/channels/telegram/poller.py`):** Parses native voice notes and text messages, hashes user IDs with `PHONE_HASH_SALT`, enforces deduplication by `f"tg_{update_id}"`, and dispatches to orchestrator.
  - **Local Runner (`backend/scripts/run_telegram_polling.py`):** Added long-polling CLI runner (`getUpdates`) for tunnel-free local development with graceful `Ctrl+C` shutdown.
  - **Configuration & Parity:** Added `TELEGRAM_BOT_TOKEN` to `Settings`, `.env.example`, and `health.py` config presence booleans. Updated `test_env_example_matches_settings.py`.
  - **Unit Tests (`backend/tests/unit/test_telegram_channel.py`):** Added 8 unit tests covering parsing (text, voice, unsupported), `send_text`, `send_audio_bytes`, streaming media download, deduplication by update_id, and mocked end-to-end voice pipeline routing.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_telegram_channel.py`: 8 passed in 0.79s.
  - `pytest backend/tests/unit/`: 50 passed in 5.54s (42 original + 8 new).
  - `ruff check backend/ scripts/`: All checks passed!
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 50 passed (MOCKED), 0 failed.
- **Git commit hash and message:** Commit `a572049` ("feat(channels): add Telegram Bot channel adapter and polling runner under D-002").

### [2026-11-02 09:55] Phase 1.7 Fix Pass Complete
- **What changed:**
  - **Item 1 (.env.example & Settings parity):** Set `AUDIO_MAX_SECONDS=60` and synchronized all keys and defaults with `Settings`. Added unit test `test_env_example_matches_settings.py` checking bidirectional key parity and default equality.
  - **Item 2 (Single repo-root virtual environment):** Created root virtual environment `.venv/` and installed all requirements. Updated `docs/PHASE2_CHECKLIST.md`, `scripts/scan_secrets.ps1`, and `README.md`. Removed redundant `existing-code/.venv`.
  - **Item 3 (test_gnani.py live diagnostics):** Pre-converts any input audio (`.m4a`, `.ogg`, `.mp3`, `.wav`) to 16 kHz mono WAV with `audio_service`. Prints full raw Prisma STT JSON response for real `detected_language_code` inspection. Post-TTS encodes OGG/Opus mono, calculates file size in KB, and asserts against the WhatsApp 512 KB inline limit. Saves outputs under `out/`.
  - **Item 4 (eval_wer.py clips discovery):** Defaulted clips directory to `backend/data/clips/`, added `--clips-dir` CLI option, accepts plain filenames from `transcripts.csv`, and exits with a clear error if 0 matching audio clips exist.
  - **Item 5 (PHASE2_CHECKLIST.md real log output):** Replaced placeholder log examples with real single-line JSON structured logs emitted by `StructuredJsonFormatter` and real JSON audit records from `EventRepository` (transcripts omitted).
  - **Item 6 (Remaining TTS_DEFAULT_LANG fallbacks replaced):** Replaced hardcoded default language fallbacks in `handle_text_message` and unsupported message type handling with `_resolve_user_language` (user's remembered language or pilot primary language `te-IN`). Added unit test.
  - **Item 7 (scripts/scan_secrets.py hardened):** Added unquoted `KEY=VALUE` matching for keys containing KEY, SECRET, TOKEN, PASSWORD with 16+ chars. Updated Meta pattern to `EAA[A-Za-z0-9]{20,}`. Removed incorrect `ai.vachana.ai` regex. Added commit history check for added `.env` files via `git log --all --diff-filter=A --name-only`. Restricted allowlist to exact placeholder matches only. Documented `gitleaks` secondary check in `docs/MANUAL_TASKS.md`.
  - **Item 8 (Test database isolation):** Added autouse fixture `isolate_databases_and_logs` in `backend/tests/conftest.py` redirecting `EventRepository`, `SQLiteUserPreferencesRepository`, and deduplication to pytest `tmp_path`, guaranteeing `./data` and `./logs` are never touched during test runs.
  - **Item 9 (simulate_webhook.py text mode):** Added `--text` flag for end-to-end offline testing and documented that audio mode with fake media ID fails at media download without real Meta media ID.
  - **Item 10 (Ephemeral hosting note):** Documented that SQLite on ephemeral hosting loses state on redeploy and will migrate to managed Supabase in Phase 6.
- **Commands run and their real results:**
  - `pytest backend/tests/`: 39 passed, 5 skipped (2 live smoke tests + 3 ffmpeg fixtures), 0 failed in 3.65s.
  - `ruff check backend/ scripts/`: All checks passed! (0 errors).
  - `python scripts/scan_secrets.py`: `[OK] CLEAN: No exposed secrets or committed .env files detected in working tree or git history.`
- **Tests:** 39 unit tests passed, 5 skipped.
- **Git commit hashes:** Pending small atomic commits.

### [2026-11-02 09:30] Phase 1.6 Follow-Up Hardening Pass Complete
- **Goal and phase:** Phase 1.6 short follow-up before Phase 2.
- **What changed:**
  - **Item 1 (Default reply language & user preference memory):** Unknown-language fallbacks (unsupported media, audio too long, empty transcript, error fallback, TTS fallback voice) now strictly route to the pilot primary language (`te-IN`, `Lavanya`) from `config/pilot.yaml`. Built `backend/app/repositories/user_preferences.py` (SQLite-backed) to record and remember the last seen language for each salted user hash.
  - **Item 2 (Timeouts):** Shared `httpx.AsyncClient` configured with sensible defaults (`Timeout(60.0, connect=10.0, read=60.0, write=30.0)`). Per-request timeouts enforced: STT (60s), TTS (90s), LLM (120s), WhatsApp media download & upload (60s). Verified via mock timeout tracking client.
  - **Item 3 (MIME Allowlist):** Added `audio/mp4` and `audio/amr` to `ALLOWED_AUDIO_MIMES` in `core/security.py`. Updated unit test to confirm `audio/mp4` is valid (WhatsApp voice notes from iOS/Android frequently use `.m4a` inside an `audio/mp4` container) while `video/mp4` is rejected.
  - **Item 4 (Audio Duration & Chunking):** Raised `AUDIO_MAX_SECONDS` default to 60s. Enforced chunking (<= 25s per Prisma STT call) for clips between 25s and 60s, and rejection for clips > 60s using language-aware message. Added test fixtures for 20s, 40s, and 70s (skipped when ffmpeg is missing on PATH).
  - **Item 5 (Docs Consistency):** Unified test counts (37 unit tests passed, 5 skipped, 0 failed), statuses, and verified public repository notes across `README.md`, `docs/PROGRESS.md`, and `docs/code-audit.md`.
  - **Item 6 (Secret Scanner):** Created `scripts/scan_secrets.py` and PowerShell wrapper `scripts/scan_secrets.ps1`. Scans working tree and complete Git history (`git log -p --all`) for credentials. Clean run documented in `docs/MANUAL_TASKS.md`.
  - **Item 7 (Simulate Webhook):** Created `backend/scripts/simulate_webhook.py` generating signed WhatsApp audio webhooks to test local `/webhook` route without calling Meta.
  - **Item 8 (Phase 2 Checklist):** Created `docs/PHASE2_CHECKLIST.md` with step-by-step Windows runbook for tunneling, Meta Developer Portal configuration, token generation, text/voice testing, and expected log lines.
- **Commands run and their real results:**
  - `pytest backend/tests/`: 37 passed, 5 skipped, 0 failed in 1.73s.
  - `ruff check backend/`: All checks passed! (0 errors).
  - `python scripts/scan_secrets.py`: `[OK] CLEAN: No exposed secrets detected in working tree or git history.`
- **Tests:** 37 unit tests passed, 5 skipped (2 live without keys, 3 ffmpeg fixtures).
- **Git commit hashes:** `4cb221c`, `26da4ce`, `605ba01`, `535e279`.

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
- **Git commit hash and message:** `ecfcc79` through `dcd2ea7` (pushed to origin main).

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
