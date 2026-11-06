# Kisan Saathi: Progress Log

## START HERE
Kisan Saathi is a WhatsApp-first voice assistant for Indian farmers (Telugu, Hindi, English; Hinglish tested) built for the Gnani Internship Challenge (Deadline: 10 Nov 2026, treating 9 Nov as the real target). Pipeline: voice note -> Gnani Prisma STT v3.0 -> Evon LLM (OpenAI-compatible adapter with echo fallback and disclosure) with allowlisted tools (mandi prices from data.gov.in, weather from Open-Meteo, crop Q&A from KCC records) -> Gnani Timbre TTS -> voice note back. No pesticide/fertiliser doses are ever generated. All facts come from retrieved evidence.

**REPOSITORY VISIBILITY WARNING:** The GitHub remote repository (`https://github.com/itsakhilesh7/KIsan-Saathi.git`) is confirmed **PUBLIC**. All commits and history are publicly visible. Do NOT stage or commit real API keys, tokens, `.env` files, or raw audio recordings. Always run `python scripts/scan_secrets.py` before pushing.

### Phase Status (P0..P8)
- **P0 (Access & Audit):** Done.
- **P1 (Backend Foundation & Migration):** Done (migrated, hardened, Phase 1.5, 1.6 & 1.7 complete; 42 unit tests passing).
- **P2 (Live Loop / Telegram Channel Fallback):** LIVE Verified on Telegram (D-002 active). Live voice notes in Telugu processed and verified end-to-end via Gnani Prisma STT v3.0 and Timbre TTS v2.5.
- **P3 (Tools, Intent, Grounded Answers):** Phase 3A (Mandi Connector), Phase 3A.1 (Multi-Market Hardening), Phase 3B (Pilot Analysis, Weather Connector, Chilli Disambiguation, Safe Intent Fallback), Phase 3C (Mandi Cache, Variety Separation, Pilot Confirmation), and Phase 3D (Wording Single Source of Truth, Mandi Cache Lifecycle, Conversation Flows, Speech Quality) Done (108 unit tests passing).
- **P4 (Crop Q&A + Safety):** Step 3.1 completed (curated advisory document list proposed; awaiting approval).
- **P5 (Evon, Web Demo, Dashboard):** Not started.
- **P6 (Evaluation + Deploy):** In Progress. Speech evaluation (`backend/scripts/eval_wer.py` & `backend/scripts/report_wer.py`) verified (Hindi WER 10.12%, Telugu WER 12.40%, Hinglish intent pass).
- **P7 (Hardening & Review):** Done. Centralized user-facing strings into `backend/app/core/messages.py`, zero Indic script literals in `services/` or `channels/`, and generated `docs/WORDING_REVIEW.md`.
- **P8 (Submission):** Not started.

### What works right now
- Backend FastAPI app with Request-ID middleware, structured JSON logging, and `/api/health`.
- Telegram live channel polling runner (`backend/scripts/run_telegram_polling.py`) verified live with end-to-end voice notes and text messages.
- Live voice pipeline round-trip: download voice OGG/Opus -> ffmpeg wav16k -> Gnani Prisma STT v3.0 -> intent/tool processing -> grounded answer -> Gnani Timbre TTS v2.5 -> OGG/Opus voice note response + text copy.
- Confirmed Pilot (`config/pilot.yaml` with `confirmed: true`): Warangal district (Telangana), APMCs Warangal & Cherial, crops paddy (`Common` and `Fine/Superfine/Grade A`), cotton, chilli (`Green Chilli` and `Dry Chillies` with clarification), and tomato.
- Mandi price units confirmed as **Rs per quintal** (`MANDI_PRICE_UNIT: str = "Rs per quintal"`), with natural localized wording (`క్వింటాలుకు`, `प्रति क्विंटल`, `per quintal`).
- Persistent SQLite Mandi Cache (`integrations/data_gov/mandi_cache.py`) protecting against data.gov.in downtime/502s, with state-level fallback for cotton/dry chilli when Warangal district reports no records.
- Mandi cache lifecycle bug fix (`mandi.py` uses `active_cache.save_evidence`, logs error classes, and provides specific `mandi_service_unavailable` message if cache is empty on API failure).
- Variety and grade separation in grounded answer composer: distinct varieties (e.g. `Paddy (Common)` vs `Paddy (Fine/Superfine)`) are explicitly named and never mixed.
- Open-Meteo 3-day weather forecast connector (`integrations/weather/open_meteo.py`) with geocoding, allowlisted endpoints, in-memory caching, and `Evidence` normalization.
- Grounded answer composers (`services/answer_composer.py`) for mandi prices and weather forecasts enforcing $\le 3$ sentences, strictly verified numbers, uncertainty phrasing, and safety constraints (never claiming conditions are "safe" for spraying or farm operations).
- Centralized user-facing strings module (`core/messages.py`, 41 message keys in te, hi, en, hi-en) with 0 Indic literals in `services/` or `channels/`, and auto-generated `docs/WORDING_REVIEW.md`.
- Natural postposition dates (e.g. "నవంబర్ 5న", "5 नवंबर को") and script harmonization (Latin entities transliterated to Indic script for voice synthesis).
- Conversational dialogue handling: multi-turn pending crop resolution, standalone short crop queries defaulting to Warangal with notification, small-talk handling (thanks, ok, bye, capabilities query, location query).
- Audio hardening: audio $< 1$s or empty transcript returns prompt immediately; spoken replies capped at $\le 15$s.
- Speech evaluation script (`scripts/eval_wer.py` & `report_wer.py`) with identical normalization (WER 0 mathematically guarantees CER 0) and dedicated Hinglish intent/slot extraction.
- Complete unit test suite: **108 unit tests passing** (`pytest backend/tests/unit/`).

### Verified LIVE vs only MOCKED
| Integration | Status | Verification Note |
|---|---|---|
| Gnani Prisma STT | LIVE Verified | Live STT verified on 2026-11-05 across 10 audio clips via `eval_wer.py` (Avg WER: Hindi 10.12%, Telugu 12.40%; TEL-04 achieved 0.00% WER) and in live Telegram voice notes (~0.4-0.6s latency). Note: `hi-en` routes as `hi-IN`. |
| Gnani Timbre TTS | LIVE Verified | Live TTS verified on 2026-11-05 during live Telegram voice note replies (`te-IN` Lavanya, ~1.4-3.8s generation and conversion latency). |
| Meta Webhook / Send | BLOCKED (Error 131031) | Meta test account returns error 131031 ("Business Account locked"). Handshake & signature verified in mocks. WhatsApp live steps paused. |
| Telegram Channel | LIVE Verified | Live polling runner tested and confirmed working live by user with both text and voice notes. |
| data.gov.in (Agmarknet Mandi) | LIVE Verified | Verified live on 2026-11-04 (331 records) & 2026-11-05 (304 records for Telangana). Protected by `MandiCache`. |
| Open-Meteo | LIVE Verified | Live 3-day forecast and geocoding verified on 2026-11-05 (sanitized fixture in `backend/tests/fixtures/weather_sample.json`). |
| Evon / LLM | Stand-in / Echo | Stand-in model active with mandatory disclosure per D-009. Evon on rented GPU planned ~7 Nov if weights provided. |
| Persistence (SQLite) | unit-tested, local SQLite | SQLite dedup, events, user preferences, dialogue state, and mandi cache tables verified with `tmp_path`. Ephemeral hosting note: SQLite loses data on redeploy; will move events to Supabase/PostgreSQL in Phase 6. |

- **Known issues and risks:** `api.data.gov.in` intermittently returns 502 Bad Gateway or read timeouts on wide queries; handled via exponential backoff retries and the persistent `MandiCache`.
- **Decisions resolved:** D-009 (Evon on Discord confirmed non-existent; stand-in with disclosure active), D-010 (Pilot confirmed: Warangal, Telangana).
- **Decisions pending:** D-008 (Hosted embedding API choice for Crop Saathi).
- **Exact next recommended task:** User approves curated advisory document list (Step 3.1) so extraction and offline indexing (Step 3.2 & 3.3) can proceed.

---

## LOG

### [2026-11-06 21:00] Phase 3D: Wording Single Source of Truth, Mandi Cache Lifecycle, Conversation Flows, and Speech Quality
- **Goal and phase:** Phase 3D (Fix pass from live Telegram tests and open items from previous review). Centralized all user strings into `messages.py`, eliminated all Indic script literals outside `messages.py`, fixed the Mandi cache persistence bug without explicit cache, handled live conversation screenshot edge-cases (small talk, pending crop state, standalone crop query), harmonized speech quality/dates, rejected sub-second audio, and prefetched live pilot mandi records.
- **What changed:**
  - **A. Wording Single Source of Truth:**
    - Centralized all 41 message templates into `backend/app/core/messages.py` across `te`, `hi`, `en`, and `hi-en`.
    - Created `backend/app/core/keywords.py` holding language lexicons (districts, greetings, small talk, safety keywords).
    - Removed all hardcoded string dictionaries and Indic literals (`\u0c00-\u0c7f` and `\u0900-\u097f`) from `orchestrator.py`, `answer_composer.py`, and `intent_service.py`.
    - Added unit test `backend/tests/unit/test_wording_single_source.py` enforcing zero Indic script literals in `services/` or `channels/`.
    - Auto-generated `docs/WORDING_REVIEW.md` via `backend/scripts/generate_wording_review.py` to prevent drift.
  - **B. Mandi Cache Lifecycle & Graceful Failure:**
    - Fixed line 256 of `backend/app/integrations/data_gov/mandi.py`: replaced `cache.save_evidence` with `active_cache.save_evidence` so normal calls without an explicit cache persist correctly into the SQLite cache.
    - Removed duplicate return statement and added structured logging of exception class names on cache failure.
    - Added `MandiServiceUnavailableError` raising `mandi_service_unavailable` message in the user's language when both live API and cache are unavailable, replacing the generic 1551 fallback.
    - Added unit test `backend/tests/unit/test_mandi_cache_lifecycle_bug.py`.
  - **C. Conversation Handling (Screenshot Test Cases):**
    - Multi-turn pending crop resolution: stored dialogue state when asking "which crop?" so answers like "Tomato", "Potato", "Cotton", or "టమాటా" resolve directly.
    - Standalone short crop queries ($\le 3$ words) assume pilot district Warangal with an explicit notification message ("Showing Warangal; tell me another district if you want").
    - Small-talk handling: "thanks" / "ok" / "bye" return brief polite acknowledgments without the full menu; "what all can u help me with" explains capabilities (mandi + weather, crop advisory coming); "what's my location?" explains no GPS access and asks for district.
    - Added unit test `backend/tests/unit/test_conversation_flows.py` reproducing the exact user screenshot sequences.
  - **D. Speech Quality & Script Harmonization:**
    - Natural dates with embedded postpositions ("నవంబర్ 5న", "5 नवंबर को", "5 November", "5 November ko") without duplicate suffixes.
    - Script harmonization: transliterated Latin entities and units in Indic speech text before TTS (`Warangal` -> `వరంగల్`/`वारंगल`, `°C` -> `డిగ్రీల సెల్సియస్`, `%` -> `శాతం`, `Rs` -> `రూపాయలు`).
    - Spoken responses strictly capped at $\le 15$s with audio duration logged.
  - **E. Short/Empty Audio & Event Logging:**
    - Audio $< 1$s or empty transcript immediately returns `empty_transcript` prompt without raw transcripts.
    - Log events record `error_type` (exception class name only), `intent`, `tool`, and `audio_duration_seconds`.
    - Added unit test `backend/tests/unit/test_speech_quality_and_short_audio.py`.
  - **F. Live Mandi Prefetch & Speech Metrics:**
    - Executed `backend/scripts/prefetch_mandi.py` against live data.gov.in: cached 22 records for Warangal & Telangana (Paddy Rs 2800 at Cherial APMC, Cotton Rs 8800 at Nekkonda APMC, Dry Chilli Rs 11000 at Mahboob Mansion APMC).
    - Verified all arrival dates returned today are `2026-11-06` (fresh).
    - Generated normalized WER/CER reporting via `backend/scripts/report_wer.py` (Hindi WER 10.12% / CER 4.19%, Telugu WER 12.40% / CER 3.89%, Hinglish intent pass).
- **Commands run and their real results:**
  - `pytest backend/tests/unit/`: 108 passed, 0 failed in 12.54s.
  - `ruff check backend/ scripts/`: All checks passed (0 errors).
  - `python scripts/scan_secrets.py`: [OK] CLEAN: No exposed secrets detected.
- **Tests:** 108 passed, 0 failed.

### [2026-11-05 17:00] Phase 3C (Part 1 & 2): Pilot Confirmation, Mandi Cache, Variety Separation, Wording Centralization & WER Polish
- **Goal and phase:** Phase 3C (Parts 1 & 2). Applied user confirmations, hardened mandi against data.gov.in 502/timeouts via SQLite cache, added state fallback, separated crop varieties/grades, centralized user strings into `messages.py`, generated `docs/WORDING_REVIEW.md`, and polished speech evaluation logic.
- **What changed:**
  - **Pilot & Settings Confirmation:** Set `confirmed: true` in `config/pilot.yaml` with Warangal, Telangana, and confirmed crops (Paddy Common & Fine, Cotton, Green & Dry Chilli, Tomato). Set `MANDI_PRICE_UNIT: str = "Rs per quintal"` with natural language localization across te, hi, en, hi-en. Updated `test_config.py` and `.env.example`.
  - **Decisions & Specs Consistency:** Updated `docs/decisions.md` (D-009 Evon, D-010 Pilot, D-005 Curated Advisories), `docs/data-sources.md`, `prd.md` (sections 4 & 5.6), and `architecture.md` (section 7).
  - **Live Telegram Voice Logging:** Extracted real timings from live Telegram voice session (`data/events.sqlite3`): 3 Telugu voice notes processed with Prisma STT v3.0 and Timbre TTS v2.5 (`te-IN` Lavanya), exhibiting 4.2s, 7.28s, and 9.17s total round-trips (STT ~0.4–0.6s, TTS ~1.4–3.8s).
  - **Speech Evaluation Polish (`backend/scripts/eval_wer.py`):**
    - Mathematically guaranteed WER 0 gives CER 0 by calculating both metrics on the exact same normalized strings; added unit test `test_hin02_identical_normalization_gives_zero_wer_and_cer`.
    - Separated Hinglish from string-distance WER due to script mismatch (Roman reference vs Devanagari STT output); evaluated Hinglish by intent/slot extraction (`weather_query` PASS, `crop_advisory_query` PASS).
    - Documented HTTP 400 `INVALID_LANGUAGE_CODE` on `hi-en` and routing in `docs/gnani-api-notes.md`.
  - **Mandi Freshness, Caching & Variety Separation:**
    - Discovered `api.data.gov.in` returns HTTP 502 / read timeouts on unindexed queries.
    - Implemented `MandiCache` in `backend/app/integrations/data_gov/mandi_cache.py` (thread-safe SQLite cache).
    - Added state-level fallback for Cotton and Dry Chillies when Warangal district reports zero records, marking evidence with `is_state_fallback=True`.
    - Updated `compose_mandi_answer` to group by `(market, variety)` and explicitly state variety names (e.g. `Paddy (Common)` vs `Paddy (Fine/Superfine/Grade A)`) so varieties are never merged or mixed.
  - **Wording Consolidation & Telugu Fix:**
    - Created `backend/app/core/messages.py` holding all user-facing strings across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
    - Replaced non-standard `"హవామాన"` with standard Telugu `"వాతావరణం / వాతావరణ అంచనాలు"`.
    - Generated `docs/WORDING_REVIEW.md` cataloging every message with reviewer notes and flagged terms.
  - **Curated Extension Document List Prepared (Step 3.1):** Compiled list of 10 official publications from PJTSAU, ICAR-IIRR, ICAR-CICR, ICAR-IIHR, and SKLTSHU covering cotton, paddy, chilli, and tomato for user approval gate.
- **Commands run and their real results:**
  - `python -m backend.scripts.eval_wer`: Re-run on 10 clips; verified Hindi (WER 10.12%, CER 4.19%), Telugu (WER 12.40%, CER 3.89%), and Hinglish intent pass.
  - `pytest backend/tests/unit/`: 96 passed, 0 failed in 28.64s.
  - `ruff check backend/ scripts/`: All checks passed.
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 96 passed (2 live fixtures verified + 94 mocked), 0 failed.

### [2026-11-05 16:15] Phase 3B: Speech Evaluation, Live Telangana Pilot Analysis, Weather Connector & Safe Intent Fallback
- **Goal and phase:** Phase 3B. Evaluated real user speech recordings against Gnani Prisma STT, performed live mandi data analysis across Telangana and Warangal for pilot selection, built Open-Meteo weather integration, implemented multi-turn chilli disambiguation, and added safe LLM-assisted intent fallback with strict schema validation.
- **What changed:**
  - **Speech Evaluation (`backend/scripts/eval_wer.py`):**
    - Updated script with UTF-8 BOM tolerance and flexible clip-id to file resolution.
    - Evaluated 10 user audio recordings against Gnani Prisma STT v3.0 in both `indic-auto` and `explicit` modes.
    - **Real Results:**
      - Hindi (4 clips): Avg WER 10.12%, Avg CER 4.19% under `indic-auto` (HIN-01 WER 5.0%, HIN-04 WER 5.88%).
      - Telugu (4 clips): Avg WER 12.40%, Avg CER 3.89% under `explicit` (TEL-04 achieved 0.00% WER, 0.00% CER).
      - Hinglish (2 clips): Transcribed phonetically into Devanagari (e.g. "कल मेरे village में rain होने के chances क्या है?"). Discovered Gnani STT rejects `hi-en` language code with HTTP 400 (`Unsupported languages: hi-en`); normalized outgoing STT requests for Hinglish to `hi-IN` / `indic-auto`.
      - Full metrics recorded in `out/wer_results.csv`.
  - **Live Agmarknet Telangana & Warangal Analysis (`backend/scripts/summarise_telangana.py`):**
    - Executed live against Agmarknet endpoint (`DATA_GOV_API_KEY` from `.env`).
    - Verified 304 live records across 22 Telangana districts today.
    - Key findings: Dataset has both `Green Chilli` and `Dry Chillies`. Warangal has 22 active commodity records across Warangal APMC and Cherial APMC (including Green Chilli, Paddy, Tomato). Cotton reported in nearby Adilabad.
    - Recommendation prepared for user confirmation: Pilot District Warangal, pilot crops Cotton, Paddy, Chilli (Green & Dry), Maize. `confirmed: false` retained in `config/pilot.yaml` pending user confirmation.
  - **Commodity Aliases & Disambiguation (`config/commodity_aliases.yaml`, `commodity_resolver.py`):**
    - Added `Dry Chillies` alongside `Green Chilli`.
    - Added `is_ambiguous_chilli()` detection: generic "మిర్చి" / "mirchi" triggers a single clarification question ("పచ్చి మిర్చా లేదా ఎండు మిర్చా?" / "हरी मिर्च या सूखी लाल मिर्च?") instead of assuming Green Chilli.
    - Handled Telugu word boundary subtleties (dry "ఎండు" vs heat/sun "ఎండ") to prevent dry chilli clarification replies from triggering weather intent.
  - **Weather Connector (`backend/app/integrations/weather/open_meteo.py`):**
    - Fetches 3-day forecast (`temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `precipitation_probability_max`) from Open-Meteo.
    - Resolves district coordinates using Open-Meteo Geocoding API (India-only, state-checked, cached, host allowlisted, with fallback to `pilot.yaml` coordinates).
    - Normalizes forecast into strict `Evidence` schema (`SourceType.WEATHER_FORECAST`, citation, confidence, limitations, retrieved_at).
    - Saved live fixture: `backend/tests/fixtures/weather_sample.json` and `geocoding_warangal_sample.json`.
  - **Grounded Weather Composer (`backend/app/services/answer_composer.py`):**
    - Composes natural language response $\le 3$ sentences copying exact temperatures and rain probabilities from `Evidence`.
    - Includes uncertainty caveats ("forecast shows...", "వాతావరణ అంచనాల ప్రకారం...").
    - **Safety Constraint (Rule 1.1):** Enforces assertion ensuring word "safe" is never used regarding spraying, irrigation, or harvesting. Strips prompt injection tokens from district slots.
  - **LLM-Assisted Intent Fallback (`backend/app/services/intent_service.py`):**
    - When rule-based classification returns `UNSUPPORTED_OR_UNCLEAR` and `LLM_BASE_URL` is configured, calls LLM with strict JSON schema and Pydantic validation.
    - Implemented 1 automatic retry on JSON parse failure; falls back safely to `UNSUPPORTED_OR_UNCLEAR` on failure.
    - LLM never chooses external tools or writes free-form answers.
  - **Orchestrator Integration (`backend/app/services/orchestrator.py`):**
    - Routed `weather_query` to Open-Meteo connector and weather composer.
    - Integrated multi-turn dialogue state for chilli disambiguation.
  - **Unit Test Suite (`backend/tests/unit/test_phase3b_weather_and_intent.py`):**
    - Added 11 new tests covering Open-Meteo parsing, geocoding cache, host allowlist, retries, weather composer numbers & uncertainty, prompt injection safety, chilli multi-turn disambiguation, and LLM JSON fallback.
- **Commands run and their real results:**
  - `python -m backend.scripts.eval_wer`: Evaluated 10 audio clips; output written to `out/wer_results.csv`.
  - `python -m backend.scripts.summarise_telangana`: Queried live Agmarknet; 304 records returned and summarised.
  - `pytest backend/tests/unit/`: 90 passed, 0 failed in 14.88s.
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
  - `ruff check backend/ scripts/`: All checks passed.
- **Tests:** 90 passed (2 live fixtures verified + 88 mocked), 0 failed.

### [2026-11-05 10:00] Phase 3A.1: Fix Pass, Multi-Market Grounding & Guardrail Hardening
- **Goal and phase:** Phase 3A.1. Resolved issues surfaced in live testing: greeting length/content guard, unsupported intent protection, script-based language detection, first-turn disclaimer tracking, multi-market answer grouping, natural date formatting, and price unit configuration.
- **What changed:**
  - **Greeting Guard (`backend/app/services/intent_service.py`):** Messages are classified as greeting ONLY when $\le 4$ words and free of query content (no commodity mentions, no district mentions). Advice queries starting with a greeting (e.g. `"నమస్కారం, నేను ఇక్కడ పత్తి పండిస్తున్నాను, మీరు నాకు ఏమైనా సలహా ఇవ్వగలరా?"`) are properly routed to `unsupported_or_unclear`.
  - **Unsupported Intent Blocking (`backend/app/services/orchestrator.py` & `answer_composer.py`):** Unsupported intents never echo user text and never invoke free-form LLM unless dev flag `ECHO_UNSUPPORTED=true` is set. Added `ECHO_UNSUPPORTED: bool = False` to `Settings`, `.env.example`, and verified via parity test. Fixed guidance messages returned across `te-IN`, `hi-IN`, `en-IN`, and `hi-en` indicating mandi prices are supported and weather/crop advice are coming.
  - **Script-Based Language Detection (`backend/app/services/intent_service.py`):** Script analyzer `detect_text_language(text)` inspects Unicode ranges (`\u0c00-\u0c7f` for Telugu, `\u0900-\u097f` for Hindi Devanagari, Latin script with Hindi vocabulary tokens like `kya`, `bhav`, `hai`, `mein` for `hi-en`, and `en-IN` for English). Persists user's language preference on Turn 1.
  - **First Turn Flag Persistence (`backend/app/services/orchestrator.py`):** User is marked seen on ANY message (text or voice) in `SQLiteUserPreferencesRepository`. AI assistant identity disclaimer (`"కిసాన్ సాథీ AI సహాయకుడిని"`) renders strictly on the very first turn. Subsequent greetings are concise without repeating the intro.
  - **Multi-Market Grounded Answering (`backend/app/services/answer_composer.py`):** `compose_mandi_answer()` groups records by market, citing up to 2 distinct markets sorted by most recent arrival date with verified modal prices. When a requested district has zero records, acknowledges the missing district and offers state-level alternatives.
  - **Natural Dates & Configurable Units (`backend/app/services/answer_composer.py`):** Formats arrival dates naturally per language (`4 నవంబర్`, `4 नवंबर`, `4 November`), retaining ISO strings in `Evidence`. Added `MANDI_PRICE_UNIT: str = ""` to `Settings` and `.env.example` (omitted if empty, localized as `క్వింటాలుకు`, `प्रति क्विंटल`, `per quintal` when set).
  - **Raw Language Code Logging (`backend/app/repositories/events.py`):** Added `raw_detected_language` column to SQLite `events` table (with automatic migration) and JSONL event log to capture raw Prisma STT language tags.
  - **Unit Test Suite (`backend/tests/unit/test_phase3a1_hardening.py`):** Added comprehensive test coverage for all Phase 3A.1 changes.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/`: 79 passed, 0 failed in 13.62s.
  - `ruff check backend/ scripts/`: All checks passed.
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 79 passed (1 live fixture verified + 78 mocked), 0 failed.

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
- **Git commit hash and message:** Commit `9fae561` ("feat(mandi): connect data.gov.in Agmarknet mandi dataset with grounded answering and multi-turn clarification").

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

### [2026-11-06 16:30] Phase 3D Fix Pass and Review Items Complete
- **Goal and phase:** Phase 3D: fix pass from live Telegram tests, plus review open items (wording single source of truth, mandi cache bug, conversation handling, speech quality, short audio handling, prefetch script, wer mathematical consistency).
- **What changed:**
  - **Section A (Wording Single Source of Truth):**
    - Consolidated ALL user-facing strings, prompts, and templates into `backend/app/core/messages.py` across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
    - Removed duplicate dictionary tables from `answer_composer.py` (`AI_DISCLAIMERS`, `CAVEATS`, `STALENESS_WARNINGS`, `NO_RECORDS_MESSAGES`, `UNSUPPORTED_INTENT_MESSAGES`, `CLARIFICATION_MESSAGES`, `CHILLI_CLARIFICATION_MESSAGES`) and `orchestrator.py` (`EMPTY_TRANSCRIPT_MESSAGES`, `FALLBACK_MESSAGES`, `AUDIO_TOO_LONG_MESSAGES`, `UNSUPPORTED_MEDIA_MESSAGES`).
    - Created `backend/app/core/keywords.py` moving all keyword recognition lexicons out of `services/` and `channels/`.
    - Added unit test `backend/tests/unit/test_wording_single_source.py` asserting ZERO Telugu (`\u0c00-\u0c7f`) or Devanagari (`\u0900-\u097f`) literals exist in `services/` or `channels/`.
    - Created `backend/scripts/generate_wording_review.py` auto-generating `docs/WORDING_REVIEW.md` directly from `messages.py`.
  - **Section B (Mandi Cache Bug & Graceful API Failure):**
    - Fixed line 256 bug in `backend/app/integrations/data_gov/mandi.py` where `cache.save_evidence(...)` raised AttributeError because `cache` was `None`. Now saves using `active_cache.save_evidence(evidence_list)` and logs `type(ce).__name__`.
    - Removed duplicate `return evidence_list`.
    - Added `MandiServiceUnavailableError`: when API fails and cache is empty, replies with language-aware specific message (`"the price service is not responding right now, please try again in a few minutes"` / `"ధరల సేవ ప్రస్తుతం స్పందించడం లేదు..."`), never generic 1551 fallback.
    - Added reproduction unit test in `backend/tests/unit/test_mandi_cache_lifecycle_bug.py` verifying cache save with `cache=None`, cached fallback on 502 with date caveat, and specific service-down message.
  - **Section C (Conversation Handling from Screenshots):**
    - Multi-turn state: when bot asks a question (greeting/help or clarification), stores pending dialogue state (`pending_slot="commodity"`). Resolves single-word crop replies like "Tomato", "Potato", "Cotton", "టమాటా", "ఆలూ".
    - Standalone crop query: short message (<= 3 words) that is only a known commodity name is treated as mandi query for pilot district Warangal, with assumed district notice prepended ("Showing Warangal; tell me another district if you want").
    - Small talk: added handlers for "thanks", "ok", "bye" (short friendly replies without long menu), "what can you do" (capabilities: mandi prices + weather, crop advice coming soon), and "what's my location?" (states bot does not have GPS and offers to take district name).
    - Added unit test `backend/tests/unit/test_conversation_flows.py` reproducing exact screenshot sequences:
      1. `Hi` -> `What all can u help me` -> `Tomato` -> `Tell me the price of cotton` -> `Thank you`.
      2. Telugu chilli flow answered with voice note `'ఎండు మిర్చి'`.
  - **Section D & E (Speech Quality & Short Audio):**
    - Natural dates: formatted with language postpositions ("నవంబర్ 5న", "5 नवंबर को", "5 November", "5 November ko") without glued duplicate suffixes.
    - Speech script harmonization: added `to_speech_text` in `messages.py` translating Latin pilot district/market names and units to native script forms ("Warangal" -> "వరంగల్" / "वारंगल", "°C" -> "డిగ్రీల సెల్సియస్", "%" -> "శాతం", "Rs" -> "రూపాయలు").
    - Audio < 1s rejected immediately with language-aware `empty_transcript` message and logged as `status="audio_too_short"`.
    - Event logging: captures `error_type` (exception class name only, no message text), `intent`, and `tool`. No raw transcripts. Logs synthesized audio duration (`audio_duration_seconds`).
    - Added unit test `backend/tests/unit/test_speech_quality_and_short_audio.py`.
  - **Section F (Open Review Items & Prefetch):**
    - Created `backend/scripts/report_wer.py` mathematically recomputing WER/CER per-clip and summary tables directly from `out/wer_results.csv`. Added test in `test_eval_wer.py`.
    - Created `backend/scripts/prefetch_mandi.py` prefetching Warangal pilot crops (Paddy, Cotton, Green & Dry Chilli, Tomato) and state fallbacks.
    - Verified live prefetch against data.gov.in: cached 22 records into `data/mandi_cache.sqlite3`. Confirmed all live arrival dates returned today are `2026-11-06` (no older dates returned today).
- **Commands run and real results:**
  - `python -m pytest backend/tests/unit/`: 108 passed, 1 warning in 12.54s.
  - `ruff check backend/ scripts/`: All checks passed! (0 errors).
  - `python scripts/scan_secrets.py`: Clean working tree and Git history.
  - `python -m backend.scripts.prefetch_mandi`: 22 records cached into `data/mandi_cache.sqlite3`.
  - `python -m backend.scripts.report_wer`: Verified exact math tables.

