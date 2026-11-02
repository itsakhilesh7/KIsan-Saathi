# Code Audit: existing-code/ (Kisan Saathi Starter Codebase)

Date: 2026-11-01  
Auditor: Lead Engineer  
Baseline Test Run: 5 passed in 1.86s (Python 3.13.3, pytest 9.2.0)

---

## 1. File-by-File Summary Mapped to Target Architecture

Target layout defined in `architecture.md` Section 5:

| Existing File (`existing-code/`) | Target Location (`backend/app/...`) | Status / Role in Target Architecture |
|---|---|---|
| `app/__init__.py` | `backend/app/__init__.py` | Package marker |
| `app/config.py` | `backend/app/core/config.py` | Migrate to typed `pydantic-settings` `Settings` object; load `config/pilot.yaml` with `confirmed: false` warning; eliminate all direct `os.getenv` calls. |
| `app/audio.py` | `backend/app/services/audio_service.py` | Audio format conversion, validation (size/duration/mime), and chunking (<= 25s for Prisma). |
| `app/gnani.py` | `backend/app/integrations/gnani/{stt.py, tts.py, errors.py}` | Split into modular typed adapters; add language-code normalization between Prisma output and Timbre input; explicit retries and timeouts. |
| `app/lang.py` | `backend/app/services/dialogue_state.py` & `backend/app/integrations/gnani/stt.py` | Script-based heuristic detection and string shortening. Note: `guess_language` was never actually called in starter pipeline. |
| `app/llm.py` | `backend/app/integrations/llm/{base.py, openai_compatible.py}` | OpenAI-compatible adapter with echo mode fallback; must log and disclose `LLM_DISCLOSED_NAME`. Wire `lang` and `context` into system prompt. |
| `app/main.py` | `backend/app/main.py` & `backend/app/api/routes/health.py` | FastAPI application initialization, lifespan, middleware (Request-ID, structured logging), and `/api/health` route. |
| `app/pipeline.py` | `backend/app/services/{orchestrator.py, answer_service.py}` | Voice-note orchestration: download -> convert -> STT -> intent/LLM -> TTS -> convert -> upload -> send. Replace blocking JSONL writes with non-blocking structured logging. |
| `app/whatsapp.py` | `backend/app/channels/whatsapp/{client.py, parser.py, signature.py, webhook.py}` | WhatsApp Cloud API integration: signature verification (strict in prod), payload extraction, media upload/download, and message dispatch. |
| `tests/test_webhook.py` | `backend/tests/unit/test_webhook.py` | 5 unit tests for webhook signature, verification handshake, deduplication, and payload parsing. |
| `scripts/test_gnani.py` | `backend/scripts/test_gnani.py` | CLI smoke test for live Gnani Prisma STT and Timbre TTS verification. |
| `scripts/eval_wer.py` | `backend/scripts/eval_wer.py` | Speech evaluation reporting WER and CER by language and mode (`indic-auto` vs explicit language code). |
| `data/transcripts.csv` | `backend/data/transcripts.csv` & `evaluation/audio_samples/` | Evaluation dataset manifest (file, language, reference). |

---

## 2. Line-by-Line Gnani Request/Response Comparison

Comparing `existing-code/app/gnani.py` against `docs/gnani-api-notes.md`:

### 2.1 Speech-to-Text (Prisma v3.0 / v2.5)
- **Endpoint:**
  - *Spec:* `POST https://api.vachana.ai/stt/v3` (multipart/form-data)
  - *Code:* `config.STT_URL = "https://api.vachana.ai/stt/v3"` -> **MATCH**.
- **Auth Header:**
  - *Spec:* `X-API-Key-ID: <GNANI_API_KEY>`
  - *Code:* `{"X-API-Key-ID": config.GNANI_API_KEY}` -> **MATCH**.
- **Multipart Form Fields:**
  - *Spec:* `audio_file` (binary), `model` (`prisma-v3.0` for v3, omit for v2.5), `language_code` (`hi-IN`, `te-IN`, `en-IN`, or `indic-auto` for v3.0), optional `format=transcribe`.
  - *Code:*
    - `audio_file`: sent as `(filename, bytes, "audio/wav")` -> **MATCH**.
    - `model`: sent as form data `model="prisma-v3.0"` only when configured -> **MATCH**.
    - `language_code`: sent as form data string -> **MATCH**.
    - `format`: omitted in starter code -> **ACCEPTABLE** (optional in spec).
- **Chunking / Audio Constraints:**
  - *Spec:* Max 30 seconds per call. Supported formats: WAV, MP3, OGG, FLAC, AAC, M4A.
  - *Code:* Chunks at `MAX_STT_SECONDS = 25` using `ffmpeg` segment -> **MATCH** (stays conservatively under 30s limit).
- **Response Handling:**
  - *Spec:* v3.0 returns `{success, request_id, transcript, model, detected_language_code, processing_time, end_to_end_latency}`.
  - *Code:* Checks `res.get("success", False)`, extracts `res["transcript"]` and `res.get("detected_language_code")`.
  - *Gap / Unverifiable:* The exact casing and format of `detected_language_code` returned by Prisma v3.0 is unverified live (e.g., `"te"` vs `"te-IN"` vs `"telugu"` vs `null`). The starter code directly passes this string to Timbre voice selection, risking HTTP 400.

### 2.2 Text-to-Speech (Timbre v2.5 / v3.0)
- **Endpoint:**
  - *Spec:* `POST https://api.vachana.ai/api/v1/tts/inference` (application/json)
  - *Code:* `config.TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"` -> **MATCH**.
- **Auth Header:**
  - *Spec:* `X-API-Key-ID: <GNANI_API_KEY>`, `Content-Type: application/json`
  - *Code:* `{**_headers(), "Content-Type": "application/json"}` -> **MATCH**.
- **JSON Request Body:**
  - *Spec:*
    ```json
    {
      "text": "...",
      "voice": "Nalini",
      "model": "timbre-v2.5",
      "language": "hi-IN",
      "speed": 1.0,
      "audio_config": {
        "sample_rate": 48000,
        "num_channels": 1,
        "sample_width": 2,
        "encoding": "linear_pcm",
        "container": "wav"
      }
    }
    ```
  - *Code (`gnani.py:86-96`):* Exact match on all JSON fields -> **MATCH**.
- **Voice Mapping & Models:**
  - *Spec:*
    - `timbre-v2.5`: Voices are strictly language-specific. Telugu `te-IN`: Suhana, Lehara, Lavanya, Yukti, Varuni. Hindi `hi-IN`: Nalini, Bhavna, Yashvi, etc. English `en-IN`: Kaveri, Trupti, etc. Hinglish `hi-en`: Poorvi. Mismatch returns `400 Bad Request`.
    - `timbre-v3.0`: 13 multilingual voices (e.g., Shivani) speaking all 10 languages.
  - *Code (`config.py:21-26`):*
    - Maps `te-IN` -> `Lavanya`, `hi-IN` -> `Nalini`, `en-IN` -> `Kaveri`, `hi-en` -> `Poorvi`.
    - If `TTS_MODEL == "timbre-v3.0"`, returns `(TTS_V3_VOICE, language)`.
  - *Gap / Bug:* In `.env.example`, `TTS_MODEL=timbre-v2.5` but `TTS_V3_VOICE=Shivani`. If a developer switches `TTS_MODEL` to v3.0, `Shivani` works, but if `TTS_V3_VOICE` is passed to v2.5, it fails with 400. Furthermore, if `detected_language_code` is normalized as `"te"`, v2.5 lookup fails and falls back to Hindi (`Nalini`).

---

## 3. Bugs, Security, and Reliability Issues

### 3.1 Signature Verification Bypass in Production (`app/whatsapp.py:15-17`)
- **Finding:**
  ```python
  if not config.META_APP_SECRET:
      log.warning("META_APP_SECRET not set: skipping signature check (dev only!)")
      return True
  ```
- **Severity:** High / Security Vulnerability.
- **Rule Violation:** `rules.md` explicitly mandates: *"Verify Meta webhook signature when META_APP_SECRET set; refuse production without it."*
- **Remediation:** In `backend/app/channels/whatsapp/signature.py`, if `settings.is_production` and `META_APP_SECRET` is missing/empty, the application must refuse to start or immediately raise a fatal configuration exception. In non-production, log a prominent warning. Constant-time comparison `hmac.compare_digest` must be maintained.

### 3.2 In-Memory Only Deduplication (`app/main.py:16-28`)
- **Finding:** Deduplication uses `_SEEN: OrderedDict[str, None]` with a 2000-item FIFO cap.
- **Severity:** Medium / Reliability.
- **Risk:**
  1. Restarting the server wipes the deduplication cache, leading to duplicate processing of Meta's webhook retries.
  2. Running multi-worker Uvicorn (`--workers > 1`) fragments the cache across workers; duplicate webhooks delivered to different worker processes will bypass deduplication.
- **Remediation:** Place deduplication behind a repository interface (`DeduplicationRepository`) with a lightweight SQLite backend (`data/dedup.sqlite3`) for local/single-node persistence, surviving process restarts.

### 3.3 Language Code Disconnect (Prisma STT -> Timbre TTS)
- **Finding:** `pipeline.py:52` takes `stt.get("detected_language_code")` and passes it directly to `gnani.synthesize(reply, lang)` which calls `pick_voice(language)`.
- **Severity:** Medium / Compatibility.
- **Risk:** Prisma v3.0's exact format for `detected_language_code` under `indic-auto` is unverified. If Prisma outputs `"te"` instead of `"te-IN"`, or `"hi"` instead of `"hi-IN"`, `pick_voice` does not find the key in `TTS_V25_VOICES` and defaults to `"hi-IN"` (`Nalini`), producing Hindi speech for a Telugu farmer.
- **Remediation:** Add a dedicated language normalization layer (`normalize_language_code`) with unit tests covering aliases (`te`, `tel`, `te-in`, `te-IN`, `hi`, `hin`, `en`, `hinglish`). Clearly document it as "Format Unverified" until verified live against Gnani Prisma.

### 3.4 Timbre v2.5 Language-Voice Invariant & HTTP 400
- **Finding:** For `timbre-v2.5`, voices are strictly single-language.
- **Severity:** Medium.
- **Remediation:** Strict validation in `pick_voice`: verify that `(voice, language)` pair is allowed for `timbre-v2.5`. Fall back gracefully to the designated voice for the normalized language.

### 3.5 Temp-File Lifecycle and Media Validation
- **Finding:**
  - `pipeline.py` uses `tempfile.TemporaryDirectory()` context manager, which correctly cleans up files on block exit.
  - However, `whatsapp.py:download_media` loads entire audio payloads directly into memory without checking `Content-Length` or media duration prior to processing.
- **Severity:** Medium / Denial of Service.
- **Remediation:** Enforce `AUDIO_MAX_MB` (e.g. 15 MB) during streaming download and validate audio duration (<= `AUDIO_MAX_SECONDS`) via `ffprobe` before sending to STT.

### 3.6 PII and Blocking I/O in `events.jsonl` Logging (`app/pipeline.py:23-26`)
- **Finding:**
  1. `_anon(phone)` hashes the phone number with SHA-256 (`[:12]`), but does NOT use a secret salt (`PHONE_HASH_SALT`), making it susceptible to rainbow table attacks on 10-digit Indian mobile numbers.
  2. Full user transcript and system reply are written to `events.jsonl` in clear text. Spoken voice notes often contain farmer names, villages, and land survey numbers.
  3. `_log_event` executes synchronous `open(..., "a")` inside an `async` function, blocking the event loop on every incoming request.
- **Severity:** High / Privacy & Performance.
- **Remediation:**
  - Use `PHONE_HASH_SALT` for salted hashing.
  - Structured logging middleware using async/thread executor or Python standard logging with JSON formatting.
  - Do not log sensitive PII; redact or hash where appropriate.

### 3.7 Error Paths and Fallback Messages in Background Tasks
- **Finding:**
  - In `handle_voice`, exceptions trigger `whatsapp.send_text(msg["from"], FALLBACK.get(lang or "", FALLBACK["en-IN"]))`.
  - In `handle_text`, if sending the fallback itself raises an exception, it is unhandled.
  - If `msg["from"]` is missing or invalid, sending fallback will crash.
- **Severity:** Low-Medium.
- **Remediation:** Standardize fallback dispatch wrapped in robust exception handling so background tasks never crash silently.

### 3.8 Timeouts, Retries, and HTTP 429/5xx Behavior
- **Finding:**
  - `gnani.py` implements 3 retries with backoff `1.5 * (attempt + 1)` on status codes `429, 500, 502, 503, 504`.
  - `whatsapp.py` has **zero** retries on download, upload, or send.
  - `llm.py` has **zero** retries on completions.
- **Severity:** Medium / Reliability.
- **Remediation:** Centralize retry logic with `tenacity` or a standard async retry helper across all outbound integrations (`gnani`, `whatsapp`, `llm`).

---

## 4. Test Coverage Gaps

Existing tests: 5 tests in `existing-code/tests/test_webhook.py`:
- `test_verify_ok` (MOCKED via params)
- `test_verify_bad_token` (MOCKED via params)
- `test_post_dispatches_once_and_dedupes` (MOCKED `pipeline.handle_message`)
- `test_signature_enforced` (MOCKED `pipeline.handle_message`)
- `test_extract_ignores_statuses` (Unit test on dict)

**Coverage Gaps:**
1. Zero tests for `gnani.py` (Prisma STT and Timbre TTS request formatting, multipart payload, response parsing, retry handling).
2. Zero tests for `llm.py` (echo mode vs remote completions, system prompt, temperature).
3. Zero tests for `audio.py` (WAV conversion, Opus encoding, chunking logic).
4. Zero tests for `lang.py` (language heuristics, text shortening).
5. Zero tests for `pipeline.py` (end-to-end voice processing flow, error fallbacks, latency logging).
6. Zero tests for config loading, `pilot.yaml` validation, or production secret enforcement.

---

## 5. Migration Plan & Remediations Applied (Phase 1.5)

1. **Step 1: Scaffold Target Directory Hierarchy:**
   Created full directory structure from `architecture.md` Section 5 with README/gitkeep files for future phases.
2. **Step 2: Core Configuration & Lifespan Validation:**
   Implemented `backend/app/core/config.py` with typed Pydantic `Settings`, reading all `.env.example` keys, loading `pilot.yaml`, and raising warnings if unconfirmed. Added `validate_production_settings` in `main.py` lifespan to fail fast if `META_APP_SECRET` is missing, or if `PHONE_HASH_SALT` / `WHATSAPP_VERIFY_TOKEN` use default values.
3. **Step 3: Outbound HTTP Client Pooling:**
   Created `backend/app/core/http_client.py` providing a shared `httpx.AsyncClient` instance with connection pooling (max 20 keepalive, 50 connections) managed during application lifespan and reused across WhatsApp, Gnani, and LLM adapters.
4. **Step 4: Data Schemas:**
   Implemented Pydantic schemas in `backend/app/schemas/` (`intent.py`, `evidence.py`, `conversation.py`, `common.py`).
5. **Step 5: Integrations Layer:**
   Ported and hardened Gnani STT/TTS in `backend/app/integrations/gnani/`, language normalization layer, OpenAI-compatible LLM in `backend/app/integrations/llm/` with echo fallback and model disclosure.
6. **Step 6: WhatsApp Channel & Persistence:**
   Ported WhatsApp webhook and client into `backend/app/channels/whatsapp/`. Added persistent SQLite deduplication (`SQLiteDeduplicationRepository`) surviving restarts, and streaming media size guard (`AUDIO_MAX_MB`).
7. **Step 7: Audio Service & Limits:**
   Ported audio conversion and chunking to `backend/app/services/audio_service.py`. Enforced `validate_media_type` on incoming MIME types and `AUDIO_MAX_SECONDS` before STT.
8. **Step 8: Persistent Non-Blocking Audit Events:**
   Implemented `backend/app/repositories/events.py` logging to SQLite and JSONL non-blockingly. Added `STORE_RAW_TRANSCRIPTS: bool = False` (transcripts omitted by default per privacy rules).
9. **Step 9: Language-Aware Prompts:**
   Standardized `EMPTY_TRANSCRIPT_MESSAGES`, `FALLBACK_MESSAGES` (referencing 1551 helpline), `AUDIO_TOO_LONG_MESSAGES`, and `UNSUPPORTED_MEDIA_MESSAGES` across `te-IN`, `hi-IN`, `en-IN`, and `hi-en`.
10. **Step 10: Phase 1.6 Hardening & Per-Request Timeouts:**
   Configured sensible client pool defaults and enforced per-request timeouts: STT 60s, TTS 90s, LLM 120s, WhatsApp media 60s. Implemented `SQLiteUserPreferencesRepository` remembering user language, and routed unknown-language fallbacks strictly to pilot primary language (`te-IN` Lavanya). Increased `AUDIO_MAX_SECONDS` to 60s with 25-60s chunking and >60s rejection. Allowed `audio/mp4` (m4a voice notes) and `audio/amr`. Added secret scanner (`scripts/scan_secrets.py`) and simulated webhook script (`backend/scripts/simulate_webhook.py`).
11. **Step 11: Unit & Live Test Verification:**
   Expanded test suite to 37 unit tests (100% passing), 5 skipped (2 live smoke tests without keys, 3 ffmpeg fixtures if ffmpeg is missing on PATH), and 0 failures. `existing-code/` remains untouched as an immutable reference snapshot.

