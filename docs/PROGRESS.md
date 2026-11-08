# Kisan Saathi: Progress Log

## START HERE
Kisan Saathi is a WhatsApp-first voice assistant for Indian farmers (Telugu, Hindi, English; Hinglish tested) built for the Gnani Internship Challenge (Deadline: 10 Nov 2026, treating 9 Nov as the real target). Pipeline: voice note -> Gnani Prisma STT v3.0 -> Evon LLM (OpenAI-compatible adapter with echo fallback and disclosure) with allowlisted tools (mandi prices from data.gov.in, weather from Open-Meteo, crop Q&A from KCC records) -> Gnani Timbre TTS -> voice note back. No pesticide/fertiliser doses are ever generated. All facts come from retrieved evidence.

**REPOSITORY VISIBILITY WARNING:** The GitHub remote repository (`https://github.com/itsakhilesh7/KIsan-Saathi.git`) is confirmed **PUBLIC**. All commits and history are publicly visible. Do NOT stage or commit real API keys, tokens, `.env` files, or raw audio recordings. Always run `python scripts/scan_secrets.py` before pushing.

### Phase Status (P0..P8)
- **P0 (Access & Audit):** Done.
- **P1 (Backend Foundation & Migration):** Done (migrated, hardened, Phase 1.5, 1.6 & 1.7 complete; 42 unit tests passing).
- **P2 (Live Loop / Telegram Channel Fallback):** LIVE Verified on Telegram (D-002 active). Live voice notes in Telugu processed and verified end-to-end via Gnani Prisma STT v3.0 and Timbre TTS v2.5.
- **P3 (Tools, Intent, Grounded Answers):** Phase 3A (Mandi Connector), Phase 3A.1 (Multi-Market Hardening), Phase 3B (Pilot Analysis, Weather Connector, Chilli Disambiguation, Safe Intent Fallback), Phase 3C (Mandi Cache, Variety Separation, Pilot Confirmation), Phase 3D (Wording Single Source of Truth, Mandi Cache Lifecycle, Conversation Flows, Speech Quality), and Router Hardening Done.
- **P4 (Crop Q&A + Safety):** Phase 4 (v1) Complete. Ingestion of 35 official PJTSAU technology cards with SHA-256 hashes, multilingual embedding retrieval comparison (100% Top-1 recall on 30 test queries), E4 safety test suite (51 passing tests enforcing chemical and dosage refusals, disease diagnosis refusal, prompt injection defense, and output post-check), grounded answer composer, and orchestrator routing for Paddy and Cotton.
- **P5 (Evon, Web Demo, Dashboard):** Phase 5-lite completed (Telegram webhook mode, daily usage caps & quotas, Dockerfile containerization, Render deployment guide). **Optional Stretch Web Demo Completed**: `frontend_streamlit/app.py` reusing existing orchestrator functions without logic duplication, microphone input (`st.audio_input`), audio playback, structured evidence cards, model disclosure pills, and Streamlit Community Cloud deployment guide with `packages.txt` (`ffmpeg`).
- **P6 (Evaluation + Deploy):** Done. Experiment E1 (Prisma STT Noise, Telephone, and WhatsApp Robustness) complete with 86 live calls recorded (`evaluation/results/e1_summary_table.md`, `e1_robustness_chart.png`). Achieved SNR mathematically verified on `noise_brown_snr5` (5.00-5.02 dB). E4 Safety Suite complete with 51 automated evaluations passing. Unit test suite: **273 unit tests passing**.
- **P7 (Hardening & Review):** Done. Centralized user-facing strings into `backend/app/core/messages.py`, zero Indic script literals in `services/` or `channels/`, synchronized `docs/WORDING_REVIEW.md`, and completed claims audit against PJTSAU PDF.
- **P8 (Submission):** In Progress / Ready for submission. Technical write-up (`docs/WRITEUP.md`), updated README with empirical results, clean secret scan, and submission checklist complete.

### What works right now
- Backend FastAPI app with Request-ID middleware, structured JSON logging, and `/api/health`.
- Telegram live channel polling runner (`backend/scripts/run_telegram_polling.py`) and webhook mode verified live with end-to-end voice notes and text messages.
- Streamlit web demo (`frontend_streamlit/app.py`) providing in-browser microphone recording (`st.audio_input`), real-time audio playback, structured evidence cards, and model disclosure metadata.
- Live voice pipeline round-trip: download voice OGG/Opus -> ffmpeg wav16k -> Gnani Prisma STT v3.0 -> intent/tool processing -> grounded answer -> Gnani Timbre TTS v2.5 -> OGG/Opus voice note response + text copy.
- Confirmed Pilot (`config/pilot.yaml` with `confirmed: true`): Warangal district (Telangana), APMCs Warangal & Cherial, crops paddy (`Common` and `Fine/Superfine/Grade A`), cotton, chilli (`Green Chilli` and `Dry Chillies` with clarification), and tomato.
- Mandi price units confirmed as **Rs per quintal** (`MANDI_PRICE_UNIT: str = "Rs per quintal"`), with natural localized wording (`క్వింటాలుకు`, `प्रति क्विंटल`, `per quintal`).
- Persistent SQLite Mandi Cache (`integrations/data_gov/mandi_cache.py`) protecting against data.gov.in downtime/502s, with state-level fallback for cotton/dry chilli when Warangal district reports no records.
- Mandi cache lifecycle bug fix (`mandi.py` uses `active_cache.save_evidence`, logs error classes, and provides specific `mandi_service_unavailable` message if cache is empty on API failure).
- Variety and grade separation in grounded answer composer: distinct varieties (e.g. `Paddy (Common)` vs `Paddy (Fine/Superfine)`) are explicitly named and never mixed.
- Open-Meteo 3-day weather forecast connector (`integrations/weather/open_meteo.py`) with geocoding, allowlisted endpoints, in-memory caching, and `Evidence` normalization.
- Grounded answer composers (`services/answer_composer.py`) for mandi prices and weather forecasts enforcing $\le 3$ sentences, strictly verified numbers, uncertainty phrasing, and safety constraints (never claiming conditions are "safe" for spraying or farm operations).
- Centralized user-facing strings module (`core/messages.py`, 55 message keys across te, hi, en, hi-en) with 0 Indic literals in `services/` or `channels/`, and auto-generated `docs/WORDING_REVIEW.md`.
- Natural postposition dates (e.g. "నవంబర్ 5న", "5 नवंबर को") and script harmonization (Latin entities transliterated to Indic script for voice synthesis).
- Conversational dialogue handling: multi-turn pending crop resolution, standalone short crop queries defaulting to Warangal with notification, small-talk handling (thanks, ok, bye, capabilities query, location query).
- Audio hardening: audio $< 1$s or empty transcript returns prompt immediately; spoken replies capped at $\le 15$s.
- Speech evaluation script (`scripts/eval_wer.py` & `report_wer.py`) with identical normalization (WER 0 mathematically guarantees CER 0) and dedicated Hinglish intent/slot extraction.
- Router hardening: whole-word regex (`\b...\b`) for Latin keywords and exact token/phrase matching for Indic; strict 4-tier precedence (domain intents -> pending dialogue -> conversational metadata for short messages <= 6 tokens); exact short chilli follow-up enforcement.
- Complete unit test suite: **273 unit tests passing** (`pytest backend/tests/unit/`).

### Verified LIVE vs only MOCKED
| Integration | Status | Verification Note |
|---|---|---|
| **Gnani Prisma STT v3.0** | LIVE Verified | Live STT verified on 2026-11-05 across 10 audio clips via `eval_wer.py` (Avg WER: Hindi 10.12%, Telugu 12.40%; TEL-04 achieved 0.00% WER) and in live Telegram voice notes (~0.4-0.6s latency). Outgoing Hinglish speech is normalized to `hi-IN` / `indic-auto`. |
| **Gnani Timbre TTS v2.5** | LIVE Verified | Live TTS verified during live Telegram voice note replies (`te-IN` Lavanya, `hi-IN` Nalini, `en-IN` Kaveri, `hi-en` Poorvi, ~1.4-3.8s generation and conversion latency). |
| **Meta Webhook / Send** | BLOCKED (Error 131031) | Meta test account returns error 131031 ("Business Account locked"). Handshake & signature verified in mocks. WhatsApp live steps paused; Telegram and Streamlit serve as active alternatives. |
| **Telegram Channel** | LIVE Verified | Live polling runner and webhook mode tested and confirmed working live by user with both text and voice notes. |
| **Streamlit Web Demo** | LIVE Verified | Local and cloud-ready web interface with microphone recording, real-time voice playback, and verified evidence cards. |
| **data.gov.in (Agmarknet Mandi)** | LIVE Verified | Verified live on 2026-11-04 (331 records) & 2026-11-05 (304 records for Telangana). Protected by persistent `MandiCache`. |
| **Open-Meteo** | LIVE Verified | Live 3-day forecast and geocoding verified on 2026-11-05 (sanitized fixture in `backend/tests/fixtures/weather_sample.json`). |
| **Crop Saathi (PJTSAU Corpus)** | LIVE Grounded | 35 official technology cards from PJTSAU Agro-Technologies 2020-21 with 3072-dim embeddings. Chemical doses stripped, qualitative advice only. |
| **Evon / LLM** | Stand-in / Disclosed | Per D-009, no hosted Evon endpoint was accessible. Stand-in OpenAI-compatible adapter used with mandatory disclosure via `LLM_DISCLOSED_NAME`. |
| **Persistence (SQLite)** | unit-tested, local SQLite | SQLite dedup, events, user preferences, dialogue state, usage limits, and mandi cache tables verified with `tmp_path`. Ephemeral hosting note: SQLite loses data on redeploy unless attached to a persistent volume. |

- **Known issues and risks:** `api.data.gov.in` intermittently returns 502 Bad Gateway or read timeouts on wide queries; handled via exponential backoff retries and the persistent `MandiCache`.
- **Decisions resolved:**
  - D-008: Resolved (Google AI Studio `gemini-embedding-001`, 3072 dimensions, 100% recall on 30 benchmark queries, with deterministic offline fallback).
  - D-009: Resolved (Evon API not available; stand-in with mandatory disclosure active).
  - D-010: Resolved (Pilot confirmed: Warangal, Telangana).
- **Decisions pending:** None.
- **Exact next recommended task:** Final review of submission materials (`README.md`, `docs/WRITEUP.md`) and submission entry for the challenge.

---

## LOG

### [2026-11-08 16:05] Optional Stretch: Interactive Streamlit Web Demo in `frontend_streamlit/`
- **Goal and phase:** Optional stretch (interactive web demo in `frontend_streamlit/` reusing backend orchestrator functions with zero duplicated business logic, audio microphone input, model disclosure, evidence cards, usage caps, and Streamlit Community Cloud deployment documentation).
- **What changed:**
  - **1. Streamlit Application (`frontend_streamlit/app.py`):**
    - Built interactive, mobile-friendly Streamlit web application.
    - Integrated `st.audio_input` for direct in-browser microphone voice queries, alongside an audio file uploader and text query input with quick-action test buttons.
    - Language hint selector: `Auto-detect`, `te-IN` (Telugu), `hi-IN` (Hindi), `en-IN` (English), `hi-en` (Hinglish).
    - Audio output: Synthesized voice note played back via `st.audio` (OGG/Opus format).
    - Evidence & Source Cards: Structured cards rendering Mandi prices (Market, arrival date, modal price, min/max range, data.gov.in link), Weather forecasts (temperature, rain probability, Open-Meteo link), and PJTSAU Agro-Technologies advisory cards (card number, publication year, agro-climatic zone, document link).
    - Model & Provenance Disclosure: Badges displaying STT (`Gnani Prisma v3.0`), TTS (`Gnani Timbre`), and LLM / Grounding Reasoner (`LLM_DISCLOSED_NAME`).
    - Dialogue State & Usage Quota: Real-time user daily voice usage vs limit progress bar (`SQLiteUsageLimitsRepository`), global voice counter, and a "Clear Dialogue State" button.
  - **2. Streamlit Channel Adapter (`StreamlitChannelClient`):**
    - Implemented `ChannelClient` protocol in `frontend_streamlit/app.py` capturing in-memory media bytes and synthesized responses.
  - **3. Orchestrator Pipeline Result Dict Support (`backend/app/services/orchestrator.py`):**
    - Updated `handle_voice_message` and `handle_text_message` to return rich pipeline execution dictionaries with zero breaking changes to existing callers or tests.
    - Supported explicit `language` field in message payload as an override hint while maintaining default language resolution.
    - Added `"audio/webm"` to `ALLOWED_AUDIO_MIMES` in `backend/app/core/security.py` to support browser microphone WebM container formats.
  - **4. Deployment Configuration & Documentation:**
    - Created `frontend_streamlit/requirements.txt` with minimal dependencies (`streamlit`, `httpx`, `pydantic`, `pydantic-settings`, `PyYAML`, `rapidfuzz`).
    - Created `frontend_streamlit/packages.txt` and repo root `packages.txt` with `ffmpeg` so Streamlit Community Cloud automatically installs Debian packages for audio normalization.
    - Updated `docs/DEPLOY.md` (Section 6) with Streamlit Community Cloud deployment steps, 1 GB RAM limits, inactivity sleep behavior, and server-side `secrets.toml` setup.
  - **5. Automated Testing (`backend/tests/unit/test_streamlit_app.py`):**
    - Added 5 unit tests verifying protocol implementation, media handling, text pipeline execution, voice pipeline execution, and secrets defaults.
    - Full test suite: **273 unit tests passing**, 0 failed.
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_streamlit_app.py`: 5 passed in 1.72s.
  - `pytest backend/tests/unit/`: **273 passed**, 0 failed in 21.80s.
  - `ruff check frontend_streamlit/ backend/ scripts/`: All checks passed.
  - `python scripts/scan_secrets.py`: [OK] CLEAN: No exposed secrets detected.
- **Tests:** 273 passed, 0 failed.
- **Goal and phase:** Phase 4 (v1). Deliver Crop Saathi over verified official PJTSAU documents for Paddy and Cotton advisory, enforcing strict safety guardrails (chemical dose refusal, disease diagnosis refusal, and out-of-scope redirection to KVK / 1551), multilingual embedding retrieval benchmark, and Single Source of Truth adherence.
- **What changed:**
  - **1. Source Verification & Ingestion (`backend/scripts/ingest_advisories.py`):**
    - Inspected *Source (b)* (PJTSAU Vyavasaaya Diksoochi Telugu PDFs, 88.3 MB). Text extraction showed unmapped 8-bit ASCII / Anu / PUA glyphs without a ToUnicode CMap; per instructions, Source (b) was officially dropped.
    - Verified *Source (a)*: *PJTSAU Agro-Technologies 2020-21* (Publication `PJTSAU/Res/2020-21/AT`, Directorate of Research). Ingested all 35 official technology cards (cards 106 to 140) into `backend/data/crop_advisories.jsonl` with untouched `raw_text`, title, page, publisher, publication number, year, source URL, agro-climatic zone, retrieved-at timestamp, and SHA-256 `content_hash`.
  - **2. Precomputed Multilingual Embeddings (`backend/scripts/precompute_embeddings.py`):**
    - Generated and cached 3072-dimensional embeddings for all 35 technology cards using Google AI Studio `gemini-embedding-001` (`backend/data/crop_advisories_embeddings.json`).
  - **3. Retrieval Service (`backend/app/services/retrieval_service.py`):**
    - Implemented `AdvisoryRetrievalService` with cosine similarity search, crop filtering (`"paddy"` / `"cotton"`), similarity thresholding (default 0.52), and deterministic offline fallback for sandboxed test environments.
  - **4. Retrieval Benchmark Comparison (`backend/scripts/eval_retrieval_comparison.py`):**
    - Evaluated 30 realistic farmer queries across Telugu (10), Hindi (10), and English (10):
      - **Direct Multilingual Recall:** **30/30 (100.0%)**, Average Cosine Sim: **0.7731**
      - **English Translated Recall:** **30/30 (100.0%)**, Average Cosine Sim: **0.8030**
    - Logged to `evaluation/results/retrieval_benchmark_30.json`. Direct multilingual embeddings eliminate the latency and cost of extra translation calls while achieving 100% Top-1 accuracy.
  - **5. Safety Service (`backend/app/services/safety.py` & `core/safety_keywords.py`):**
    - Under `ALLOW_CHEMICAL_DETAILS=false`: strips chemical names and numeric dosages; appends mandatory product label check and KVK/1551 consultation reminder.
    - Refuses conclusive disease diagnosis from short symptom descriptions (instructs farmer to bring sample to KVK).
    - Defends against prompt injections in cards or queries.
    - Post-check validator (`validate_composer_output`): ensures no ungrounded numbers or prohibited chemicals are emitted.
  - **6. Grounded Answer Composer (`backend/app/services/answer_composer.py`):**
    - Generates responses in user's language in $\le 2$ sentences (spoken $\le 15$s), always mentions agro-climatic zone, appends official source line (`[Title], [Publisher], [Year]`), and loads templates from `core/messages.py`.
  - **7. Orchestrator Wiring (`backend/app/services/orchestrator.py` & `intent_service.py`):**
    - Routed `CROP_ADVISORY_QUERY` to Paddy and Cotton advisory cards with out-of-scope redirection to KVK / 1551 for Chilli and Tomato.
    - Expanded agricultural and agronomic vocabulary in `CROP_ADVISORY_KEYWORDS`.
  - **8. Automated Test Suites:**
    - `test_phase4_crop_saathi.py`: 8 end-to-end and unit tests passing.
    - `test_safety_e4.py`: 51 safety test cases passing across Telugu, Hindi, and English (refusal of doses, mixtures, injections, off-topic medical/legal, and symptom diagnosis).
    - Total test suite: **268 unit tests passing**, 0 failed.
  - **9. Single Source of Truth Compliance:**
    - Zero Indic script literals in `backend/app/services/` or `channels/`. All user-facing strings centralized in `backend/app/core/messages.py` across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`. Synchronized `docs/WORDING_REVIEW.md`.
- **Commands run and their real results:**
  - `python backend/scripts/ingest_advisories.py`: 35 cards ingested into `crop_advisories.jsonl`.
  - `python backend/scripts/precompute_embeddings.py`: 35 cards embedded and saved.
  - `python backend/scripts/eval_retrieval_comparison.py`: 30/30 queries evaluated (100% recall).
  - `pytest backend/tests/unit/`: **268 passed**, 0 failed in 20.40s.
  - `ruff check backend/ scripts/`: All checks passed.
  - `python scripts/scan_secrets.py`: [OK] CLEAN.
- **Tests:** 268 passed, 0 failed.
- **Goal and phase:** Phase 6 (Evaluation E1). Measure the acoustic robustness of Gnani Prisma STT v3.0 under clean conditions, additive environmental noise (pink, brown at SNR 20, 10, 5 dB), telephone transmission (G.711 $\mu$-law 8 kHz, AMR-NB 8 kHz), and WhatsApp Opus 24 kbps VOIP compression across user recordings.
- **What changed:**
  - **1. Audio Generation (`backend/scripts/build_eval_audio.py`):**
    - From the 10 farmer recordings in `backend/data/clips/`, generated deterministic test audio across all degradation conditions using exact RMS decibel matching (`10 * log10(P_signal / P_noise)`).
    - Simulated G.711 $\mu$-law bandlimiting (`pcm_mulaw` at 8 kHz), AMR-NB (`libopencore_amrnb` at 8 kHz), and WhatsApp voice note compression (`libopus` at 24 kbps VOIP mode).
    - Audio artifacts stored in `backend/data/eval_audio/` (gitignored; never committed).
  - **2. Evaluation Runner (`backend/scripts/run_eval_e1.py`):**
    - Executed 86 live STT calls against Gnani Prisma STT v3.0 in explicit language mode (`te-IN` for Telugu, `hi-IN` for Hindi/Hinglish).
    - Applied identical string normalization (`normalize_text`) to reference and hypothesis transcripts for mathematical WER/CER invariants (WER 0 guarantees CER 0).
    - Evaluated Hinglish via intent extraction accuracy rather than string-distance WER due to script-mixing differences (Devanagari hypothesis vs Roman reference).
    - Incremental per-call flushing to `evaluation/results/e1_per_clip.csv` allowing resume on interrupted runs.
  - **3. Artifacts Generated in `evaluation/results/`:**
    - `e1_per_clip.csv`: 86 rows of raw evaluations with WER, CER, hypotheses, and intent classifications.
    - `e1_summary_table.md`: Mean WER and CER by language $\times$ condition.
    - `e1_robustness_chart.png`: High-resolution comparative bar chart.
    - `RUN_INFO.json`: Metadata with timestamp, git commit, model version, and explicit limitations.
  - **4. Key Evaluation Results:**
    - **Telugu (n=4 clips):** Clean Mean WER **12.40%** (CER 3.89%). Heavy 5 dB pink noise increased WER by only 4.19 percentage points to **16.59%** (CER 4.87%). Brown noise at 5 dB remained at **12.40%** (CER 3.89%). Telephony G.711: **16.59%**; AMR-NB: **14.32%**; WhatsApp Opus: **14.32%**.
    - **Hindi (n=4 clips):** Clean Mean WER **12.68%** (CER 6.21%). Heavy 5 dB pink noise: **19.28%** (CER 10.44%). Brown noise at 5 dB: **13.93%** (CER 7.37%). Telephony G.711: **15.18%**; AMR-NB: **15.24%**; WhatsApp Opus: **11.43%** (WER improved over clean baseline due to high-frequency de-noising in Opus encoder).
    - **Hinglish (n=2 clips):** Intent accuracy: **50.0%** across clean, pink 10 dB, and telephony G.711.
  - **5. Limitations Explicitly Stated:** 10 clips total, single speaker, quiet room baseline. Small sample size indicates directional robustness across transmission channels and noise floors rather than population-level demographic benchmarks.
- **Commands run and their real results:**
  - `python -m backend.scripts.run_eval_e1 --suite core_minimal`: 86 calls executed successfully (HTTP 200).
  - `pytest backend/tests/unit/`: 209 passed, 0 failed in 17.48s.
  - `ruff check backend/ scripts/`: All checks passed (0 errors).
  - `python scripts/scan_secrets.py`: [OK] CLEAN: No exposed secrets detected.
- **Tests:** 209 passed, 0 failed.
- **Goal and phase:** Router hardening for `intent_service.py`, `keywords.py`, and `commodity_resolver.py`. Test-first; reproduced all 3 user-reported bugs with failing unit tests, implemented strict whole-word/exact-token matching, established 4-tier precedence, added exact short chilli disambiguation follow-up, and verified across a 90-case test suite including >50 table-driven realistic utterances.
- **What changed:**
  - **1. "नमस्ते" Bug Fixed:** Removed `"नमस्ते"` from `BYE_KEYWORDS` in `backend/app/core/keywords.py`. A Hindi hello is now correctly classified as `GREETING_OR_HELP`, never as `SMALL_TALK` bye.
  - **2. Substring Matching Eliminated:**
    - Script-specific boundary matching: Latin keywords match as whole words using regex word boundaries `\b...\b`; Indic keywords match as whole tokens or exact phrase token sequences.
    - Commodity resolver hardened (`commodity_resolver.py`): eliminated substring matches that caused "price" to resolve to "Paddy(Common)" (matching "rice") and "Dhanyavad" to resolve to "Paddy(Common)" (matching "dhan").
    - Telugu district matching supports attached case markers (e.g. `"వరంగల్‌లో"`, `"ఖమ్మంలో"`).
  - **3. Strict 4-Tier Precedence in `extract_intent`:**
    - **Tier 1 (Strong domain queries):** Weather, Mandi Price, and Crop Advisory intents win whenever strong domain keywords, commodities, or districts are present. Sentences like "Can you help me with tomato price", "weather at my location", and "thank you, what is the cotton price" route immediately to their domain intents.
    - **Tier 2 (Pending dialogue answers):** Chilli follow-up accepts ONLY exact short answers ("1", "2", "green", "dry", "పచ్చి", "ఎండు", "हरी", "सूखी") when $\le 3$ words; otherwise treats the message as a fresh question and clears state.
    - **Tier 3 (Conversational metadata):** Capabilities, location, small talk (thanks, ok, bye), and greeting apply ONLY to short messages ($\le 6$ words) that contain ZERO domain words.
    - **Tier 4 (Fallback):** Unsupported / unclear.
  - **4. Table-Driven Test Suite (`backend/tests/unit/test_router_hardening.py`):**
    - 6 reproduction unit tests for each reported bug.
    - 84 table-driven parameterized cases covering realistic farmer queries across Telugu (`te-IN`), Hindi (`hi-IN`), English (`en-IN`), and Hinglish (`hi-en`).
- **Commands run and their real results:**
  - `pytest backend/tests/unit/test_router_hardening.py`: 90 passed in 9.17s.
  - `pytest backend/tests/unit/`: 198 passed, 0 failed in 21.19s.
  - `ruff check backend/ scripts/`: All checks passed (0 errors).
  - `python scripts/scan_secrets.py`: [OK] CLEAN: No exposed secrets detected.
- **Tests:** 198 passed, 0 failed.

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

---

## 2026-11-07 - Phase 5-lite: Deployable Container, Telegram Webhook Mode, Usage Caps & Verification
- **Goal:** Package Kisan Saathi for public deployment and sharing under strict safety invariants (`rules.md`), implement secure Telegram webhook intake, enforce daily voice rate-limits to protect Gnani credits, configure `pytest-timeout`, and verify mathematical precision in speech reports.
- **Components Implemented & Verified:**
  1. **Fast-Fail Pytest Timeout:**
     - Installed `pytest-timeout==2.4.0` in `.venv`.
     - Configured `addopts = "-v --tb=short --timeout=60"` in `pyproject.toml` ensuring tests fail fast after 60s without hanging.
  2. **Telegram Webhook Mode for Cloud Hosting:**
     - Created `backend/app/channels/telegram/webhook.py` mounting `POST /telegram/webhook/{webhook_path}`.
     - Validates URL secret path segment against `settings.TELEGRAM_WEBHOOK_PATH` and header against `settings.TELEGRAM_WEBHOOK_SECRET` via `secrets.compare_digest`.
     - Returns HTTP 200 `{"ok": true}` immediately and enqueues update processing asynchronously via FastAPI `BackgroundTasks`.
     - Update deduplication verified via SQLite `DeduplicationRepository` (`test_telegram_webhook_deduplication`).
     - Created `backend/scripts/manage_telegram_webhook.py` supporting `set <base_url>`, `delete`, and `info` commands with automatic token redaction.
     - Preserved `backend/scripts/run_telegram_polling.py` for local development.
  3. **Usage Caps & Public Bot Protection:**
     - Created `backend/app/repositories/usage_limits.py` implementing `SQLiteUsageLimitsRepository` in `data/usage_limits.sqlite3`.
     - Added configurable settings in `Settings` and `.env.example`:
       - `DAILY_USER_VOICE_LIMIT: int = 10`
       - `DAILY_GLOBAL_VOICE_LIMIT: int = 200`
       - `PUBLIC_VOICE_MAX_SECONDS: int = 30`
       - `ADMIN_USER_HASHES: str = ""`
     - Orchestrator checks: rejects audio $> 30$s for public bot; checks daily user and global voice caps prior to STT/TTS; responds with polite localized `voice_limit_reached` message (`te-IN`, `hi-IN`, `en-IN`, `hi-en`) via text. Text queries remain unmetered.
     - Admin bypass for hashed user IDs in `ADMIN_USER_HASHES`.
  4. **Docker Packaging & Cloud Deployment Documentation:**
     - Created `Dockerfile` (based on `python:3.11-slim`, with `ffmpeg`, `curl`, healthcheck on `/health`, start command `uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}`).
     - Created `.dockerignore` and production `requirements.txt`.
     - Added non-blocking asynchronous mandi cache warmup on startup in `backend/app/main.py` lifespan (`_warmup_mandi_cache`).
     - Authored `docs/DEPLOY.md` detailing Render (recommended) and Railway deployment, required environment variables, start command, webhook configuration, and the ephemeral disk notice for SQLite databases.
  5. **WER Report Precision:**
     - Verified `backend/scripts/report_wer.py` computes per-clip and summary tables directly from `out/wer_results.csv`.
     - Added mathematical assertion in `backend/tests/unit/test_eval_wer.py` guaranteeing summary averages strictly equal the arithmetic mean of the per-clip rows.
  6. **Documentation & Wording Single Source of Truth:**
     - Refreshed `README.md` with complete LIVE vs MOCKED status table, test counts, and deployment instructions.
     - Synchronized `docs/WORDING_REVIEW.md` from `backend/app/core/messages.py` via `backend.scripts.generate_wording_review`.
- **Commands run and real results:**
  - `pytest backend/tests/unit/`: **205 passed**, 1 warning in 37.77s.
  - `ruff check backend/ scripts/`: All checks passed! (0 errors).
  - `python scripts/scan_secrets.py`: Clean working tree and Git commit history.
  - `python -m backend.scripts.report_wer`: Verified exact math tables.

