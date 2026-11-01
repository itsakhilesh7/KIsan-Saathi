# Data Source Register

Allowlist for factual data. Status values: `discovered`, `schema_verified`, `live_tested`, `reviewed`, `approved_for_mvp`, `deprecated`. Update the status as you go; the agent must not use a source below `live_tested` in user-facing answers.

## 1. Mandi prices
- **Source:** data.gov.in "Current Daily Price of Various Commodities from Various Markets (Mandi)" (Agmarknet). Resource ID in `.env.example` (`9ef84268-d588-465a-a308-a864a43d0070`) is **commonly cited but must be verified** against the live resource metadata.
- **API:** `https://api.data.gov.in/resource/<id>?api-key=<key>&format=json&offset=0&limit=N` plus `filters[...]` where supported. Needs a free key from the data.gov.in account page.
- **Verify before coding:** field names, filter names, pagination, date format, whether prices are per quintal, which price fields exist (min/max/modal), whether pilot markets and crops appear, and how often.
- **Rules:** not every market reports daily; a record is a reported wholesale price, not a guaranteed offer; display commodity, variety, market, district, date, price type, unit, source URL, retrieved-at. Status: `discovered`.

## 2. Weather
- **Source:** Open-Meteo Forecast API, `https://api.open-meteo.com/v1/forecast` (free, no key; check terms for the demo). Request only needed variables; set coordinates and timezone (Asia/Kolkata) from `config/pilot.yaml`. Store retrieved-at and horizon. Forecast is not observation. Status: `discovered`.
- Optional supplement: IMD advisories if a stable published endpoint/bulletin exists. No scraping as a hidden dependency.

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
