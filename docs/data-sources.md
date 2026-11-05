# Data Source Register

Allowlist for factual data. Status values: `discovered`, `schema_verified`, `live_tested`, `reviewed`, `approved_for_mvp`, `deprecated`. Update the status as you go; the agent must not use a source below `live_tested` in user-facing answers.

## 1. Mandi prices
- **Source:** data.gov.in "Current Daily Price of Various Commodities from Various Markets (Mandi)" (Agmarknet). Resource ID in `.env.example` (`9ef84268-d588-465a-a308-a864a43d0070`) is **verified live on 2026-11-04**.
- **API:** `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=<key>&format=json&offset=0&limit=N` plus `filters[...]` (e.g. `filters[state]=Telangana`, `filters[district]=Warangal`, `filters[commodity]=Cotton`).
- **Verified Facts (2026-11-04 live call):**
  - Record fields returned: `state`, `district`, `market`, `commodity`, `variety`, `grade`, `arrival_date` (format `"DD/MM/YYYY"`), `min_price`, `max_price`, `modal_price` (integers/floats).
  - There is NO unit field in the JSON response. Do not default or assume the unit. Coded as "price as reported".
  - State name for Telangana is spelled `"Telangana"`.
  - Pagination works via `offset` and `limit`.
- **Rules:** Not every market reports daily; records represent reported wholesale prices, not guaranteed continuous live quotes. Answers must display commodity, market, district, arrival date, price type, and caveats. Stale warning added if record is older than 3 days.
- **Status:** `live_tested` (Verified live with active key on 2026-11-04; sanitized fixture in `backend/tests/fixtures/mandi_telangana_sample.json`).

## 2. Weather
- **Source:** Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`) and Open-Meteo Geocoding API (`https://geocoding-api.open-meteo.com/v1/search`). Host allowlisted; free non-commercial/demo use without API keys.
- **API Details & Verified Facts (2026-11-05 live call):**
  - **Geocoding:** `https://geocoding-api.open-meteo.com/v1/search?name=<district>&count=5&language=en&country_code=IN`. Verified live for Warangal (`18.0, 79.5833`, admin1=`Telangana`). Caches results in memory; falls back to `pilot.yaml` coordinates if geocoding fails.
  - **Forecast:** `https://api.open-meteo.com/v1/forecast?latitude=<lat>&longitude=<lon>&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Asia/Kolkata&forecast_days=3`.
  - **Daily Fields:** `time` (ISO dates), `temperature_2m_max` (°C), `temperature_2m_min` (°C), `precipitation_sum` (mm), `precipitation_probability_max` (%).
  - Sanitized fixture saved in `backend/tests/fixtures/weather_sample.json`.
- **Rules & Guardrails:** At most 3 sentences in user's language. Uncertainty wording required ("forecast indicates", "chance of rain"). Safety guard: **NEVER assert that spraying, irrigation, or harvesting is "safe"** (Rule 1.1).
- **Status:** `live_tested` (Verified live on 2026-11-05; 11 unit tests passing in `backend/tests/unit/test_phase3b_weather_and_intent.py`).

## 3. Crop Q&A: Kisan Call Centre (KCC)
- **Source:** KCC query/answer records published on data.gov.in (also listed on AIKosh). It is a very large real dataset (tens of millions of calls since 2006) of farmers' queries and expert answers, served by API and split by state/period. Language coverage varies by state.
- **Verify on Day 2:** resource IDs for the pilot state; fields (typically state, district, season, crop, query type, query text, answer, created date: **verify exact names**); share of Telugu vs English/transliterated text; empty/duplicate rate; the dataset licence (cite it in the README); API pagination limits.
- **Use:** retrieval corpus for Crop Saathi. Keep `raw_text` untouched. Label answers "historical call-centre advice (state, district, date)". Strip chemical doses by default (see `rules.md` 3).
- **Eval:** hold out about 200 pilot-crop Q&A pairs. KCC answers are expert-written but are not ground truth.
- Status: `discovered`.

## 4. Curated advisories (optional, 5 to 10 documents)
Publishers: ICAR (icar.gov.in), KVK portal (kvk.icar.gov.in), the state agricultural university, IMD agromet advisories. Store title, publisher, URL, date (or `unknown`), retrieved-at, region, crop, language, hash, reviewer status. No crawling; manual list only.

## 5. Speech evaluation data (accuracy testing, not training)
| Dataset | Use | Notes |
|---|---|---|
| **Own recordings** | Primary test set: 20+ utterances each in Telugu, Hindi, English/Hinglish, with exact transcripts | Consented/synthetic only; you can verify transcripts |
| **Kathbath** (AI4Bharat) | Small read-speech test slices (Telugu, Hindi) | Use test splits only |
| **IndicVoices** (AI4Bharat) | Spontaneous and conversational speech, many languages | Gated on Hugging Face and large: stream or fetch a small test slice, never the full download |
| **Vistaar** (AI4Bharat benchmark) | Benchmark collection that includes telephony-style GramVaani audio | Check each licence before showing audio publicly |
| **FLEURS / Common Voice** | Extra Hindi/Telugu/English checks | Check licence |
| **MUSAN, DEMAND, ESC-50, UrbanSound8K** | Background noise for augmentation | Mix at fixed SNRs |
| **MASSIVE** (Amazon) | Intent/slot sanity check; has several Indian-language subsets | Confirm Hindi/Telugu availability |
No large public Hinglish call-style speech corpus was verified, so Hinglish results rest on your own recordings.

## 6. Provenance every answer must support
Which source; the record/document date; when we retrieved it; which location/crop it applies to; any limitation.
