# Kisan Saathi: Product Requirements (v1.0)

**Status:** locked for the hackathon build. **Deadline:** 10 Nov 2026 (internal deadline 9 Nov). **Owner:** solo developer.

## 1. Summary
Kisan Saathi lets a farmer ask a question by **WhatsApp voice note** (or text) in Telugu, Hindi or English and get a short **spoken and written answer grounded in traceable sources**: live mandi prices, a weather forecast, or crop guidance retrieved from real Kisan Call Centre (KCC) records. A web demo offers the same pipeline in a browser.

It is not a general chatbot. It never invents prices, forecasts, doses, diagnoses or sources. Facts come from tools; the LLM only routes, extracts and explains.

## 2. Why this design (strategy)
- The challenge rewards a working app, a demo, written explanation, public posts, and real-world fit for regional-language, noisy-audio and Tier 2/3 use cases. Check `docs/submission-and-awards.md`.
- WhatsApp is where target users already are. Voice notes are compressed and noisy, which is exactly the "noisy telephonic audio" evaluation story.
- Judges cannot message our WhatsApp **test number** (the Meta test number only allows a handful of pre-verified recipients). A public **web demo** is therefore mandatory, not optional.
- All three Gnani models are used: **Prisma** (STT), **Evon** (reasoning), **Timbre** (TTS).

## 3. Users
- Primary: farmers who prefer speaking Telugu, Hindi, English or a mix.
- Secondary: agricultural reviewers (domain validation), judges/evaluators (need a link and visible sources).

## 4. Pilot scope
Configured in `config/pilot.yaml`. Confirmed by developer on 2026-11-05: Telangana/Warangal, crops paddy (`Paddy(Common)`, `Paddy(Fine/Superfine/Grade A)`), cotton, chilli (green AND dry, with clarification question), tomato. Maize removed as live data has no records today. State-level fallback enabled for cotton and dry chilli when the district has no record. `confirmed: true`. Optional second pilot Rajasthan/Jaipur for Hindi deferred after Phase 4.

## 5. Capabilities

### 5.1 Voice channel (WhatsApp)
- Receive voice notes (OGG/Opus) and text via Meta Cloud API webhook; verify signature; dedupe retries; answer the webhook immediately and process in the background.
- Reply with a voice note (OGG/Opus mono) plus a text copy (configurable). Keep replies short enough for the inline play icon (<= 512 KB).
- Respect the 24-hour customer-service window: we only reply to farmer-initiated messages.

### 5.2 Speech
- Prisma v3.0 via REST (<= 30 s per call; longer notes chunked) with `indic-auto` and explicit-language modes. Record detected language, latency and request ID.
- Timbre v2.5 default with per-language voices; Timbre v3.0 evaluated for Telugu quality. Text always accompanies audio.
- Never claim a language or code-mix mode works until it is measured (see evaluation plan).

### 5.3 Understanding
Intents: `mandi_price_query`, `weather_query`, `crop_advisory_query`, `greeting_or_help`, `unsupported_or_unclear`. The LLM returns schema-validated JSON (intent, language, slots, missing slots). The **server** chooses tools; the LLM never picks URLs, SQL or code. Missing required slots trigger a clarification question (one question at a time).

### 5.4 Mandi Saathi
data.gov.in Agmarknet daily prices. Filter by state/district/market/commodity; show modal price with min/max when present, unit, variety, market, **record date**, source URL and retrieval time. State clearly that these are reported wholesale prices from a daily record, not live quotes or buyer offers. If no recent record exists, say so.

### 5.5 Weather Saathi
Open-Meteo forecast for the pilot location (or a user-confirmed district). Show location, period, units, retrieval time; distinguish current from forecast; use uncertain language; never say spraying or irrigating is "safe".

### 5.6 Crop Saathi (grounded Q&A)
- Corpus: **Curated official university & ICAR extension advisories** (PJTSAU, ICAR-CRIDA/CICR/IIRR/IIHR, KVK, Telangana Agriculture Department) for pilot crops (paddy, cotton, chilli, tomato). Finding (2026-11-05): no usable real-time API or downloadable CSV exists for KCC data in the pilot state on data.gov.in; generic retrieval architecture (`documents -> chunks -> metadata`) remains identical.
- Retrieval with metadata filters (state, district, crop, season/date). Every answer cites the source document (title, publisher, date, region).
- Weak, conflicting or out-of-scope retrieval produces a safe fallback: say you are unsure and suggest the Kisan Call Centre (**1551**) or the local agriculture officer / KVK.
- **No pesticide/fertiliser dose or chemical mixture is surfaced** unless `ALLOW_CHEMICAL_DETAILS=true` and the text is quoted verbatim from a reviewed source (default false). See `rules.md`.

### 5.7 Web demo
Next.js page: record/upload/type, transcript, answer, audio player, source cards, freshness labels, language selector. Rate-limited, no login. See `design.md`.

### 5.8 Dashboard (small)
Query counts by intent/language/crop/district, latency, refusal rate, STT error flags. Reads `events` from the database. Phone numbers hashed.

### 5.9 Evaluation (a first-class deliverable)
Reproducible scripts for: WER/CER by language and noise condition; retrieval-vs-no-retrieval comparison; slot extraction F1; refusal/safety suite; latency p50/p95. See `docs/evaluation-plan.md`. Results are committed and shown in the demo.

## 6. Out of scope
PSTN/real phone calls (stretch: browser click-to-call only if all exit criteria pass), native apps, image diagnosis, dose/chemical generation, user accounts, payments, fine-tuning, nationwide claims, scraping arbitrary sites.

## 7. User journeys
**A. Mandi (voice, Telugu):** farmer asks the price of a crop -> transcript -> intent + slots -> missing market? ask -> mandi tool -> validated evidence -> short Telugu answer + source/date -> voice note.
**B. Weather (voice, Hindi):** asks about rain in the coming days -> forecast tool -> answer with period, source, uncertainty note.
**C. Crop (voice, Telugu/Hinglish):** describes a problem -> clarifying question if crop/stage/symptom missing -> retrieval over KCC -> grounded answer with citation, or safe fallback to 1551.
**D. Refusal:** asks for a pesticide dose -> polite refusal + escalation, no number.

## 8. Functional requirements and acceptance
| ID | Requirement | Acceptance |
|---|---|---|
| FR-01 | WhatsApp voice in/out | Real phone sends a voice note and receives a voice reply; verified live, screenshot/video evidence |
| FR-02 | Prisma STT | Transcript + detected language + latency logged; chunking for > 25 s clips |
| FR-03 | Timbre TTS | Voice reply for Telugu, Hindi, English; OGG/Opus <= 512 KB typical |
| FR-04 | Intent/slots | Strict schema; unknown -> `unsupported_or_unclear`; nulls never guessed |
| FR-05 | Mandi tool | Live record shown with date, unit, market, source; empty result handled |
| FR-06 | Weather tool | Forecast with period, units, retrieved_at |
| FR-07 | Crop Q&A | Every substantive answer cites >= 1 stored source; weak retrieval falls back safely |
| FR-08 | Safety | Refusal suite passes (no doses, no diagnoses, prompt-injection resisted) |
| FR-09 | Web demo | Public URL works without login; rate limited |
| FR-10 | Evaluation | One command reproduces the reported tables from committed data |
| FR-11 | Privacy | Keys server-side; phone hashed; audio retention per config |
| FR-12 | Observability | Per-request stage latencies and request ID, no secrets in logs |

## 9. Non-functional
Typed schemas at boundaries; timeouts with bounded retries; structured logs; upload validation; allowlisted external hosts; LLM output never executed; usable if TTS or one tool is down (text fallback); webhook answers in < 3 s (Meta retries slow webhooks); responsive and accessible UI.

## 10. Success metrics (measure, never invent)
STT WER/CER by language x condition; intent accuracy; slot F1; % answers with valid citations; groundedness (with vs without retrieval); refusal-suite pass rate; end-to-end latency p50/p95; TTS completion rate; reviewer ratings for crop answers.

## 11. Risks
| Risk | Mitigation |
|---|---|
| No GPU for Evon | Adapter + stand-in for development; rent a GPU for tests/recording; disclose exactly which model produced each result |
| Meta onboarding slow / token expiry | Start early; Telegram adapter fallback; system-user token |
| KCC data messy / thin in Telugu | Day-2 data audit; supplement with curated ICAR/KVK docs; state limits in the write-up |
| Unsafe agricultural advice | Retrieval-only answers, citations, dose suppression, escalation to 1551 |
| Webhook cold starts on free hosting | Keep-alive, background processing, deploy early (Phase 6) |
| Over-scoping | Priority order and cut-lines in `phases.md` |
| Honesty / authenticity penalties | Label synthetic vs real data; show real latency; no scripted flawless demos |
