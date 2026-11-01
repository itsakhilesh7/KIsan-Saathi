# Kisan Saathi: UX and Visual Design (v1.0)

## 1. Direction
Calm, trustworthy, practical. Not an enterprise dashboard. The most important things on screen: what the user asked, the answer, how fresh the data is, where it came from. Mobile-first, large touch targets, short sentences. Keep decoration minimal.

## 2. Two surfaces
1. **WhatsApp conversation** (primary): there is no UI to design; the *content* is the design. See section 6.
2. **Web demo** (what judges open): same pipeline, with visible evidence.

## 3. Tokens (CSS variables)
| Token | Value | Use |
|---|---|---|
| `--color-primary` | `#245C3A` | actions, headings |
| `--color-primary-soft` | `#E8F2EA` | selected/success background |
| `--color-accent` | `#D9A441` | highlights |
| `--color-bg` | `#F7F8F3` | page |
| `--color-surface` | `#FFFFFF` | cards |
| `--color-text` | `#1F2A22` | text |
| `--color-muted` | `#657268` | metadata |
| `--color-border` | `#DCE4DD` | dividers |
| `--color-danger` | `#B42318` | errors |
| `--color-warning` | `#8A5A00` | stale data, uncertainty |
Check contrast. Never rely on colour alone.

Typography: `Noto Sans Telugu` (Telugu), `Noto Sans Devanagari` (Hindi), `Inter` (Latin), system fallbacks. 8 px spacing scale; cards 16 to 20 px radius; primary buttons >= 48 px high.

## 4. Web demo layout (single page)
- Header: wordmark, language selector (తెలుగు / हिन्दी / English), pilot region label.
- Hero: one sentence of explanation; **large mic button**; secondary: upload audio and a text box (voice is never the only input).
- Example prompts grouped: Mandi, Weather, Crop.
- After a request: transcript panel (with detected language), clarification panel if needed, answer card, **source cards**, freshness label, audio player (no autoplay).
- "How it works" strip showing Prisma -> Evon -> tools -> Timbre, plus the model names actually used for this answer.
- Footer: the safety note and link to the evaluation page.

Voice states: Idle ("Tap to ask"), Recording (real elapsed time, stop), Uploading, Processing ("Understanding your question..."), Clarification, Success, Error (retry + text path). No fake waveforms or fake progress percentages.

## 5. Result cards
**Mandi:** commodity and variety; market and district; modal price large, min/max secondary; unit only if the source gives it; record date; source link; retrieved-at; the caveat "reported wholesale price from a daily record, not a live quote or buyer offer". Multi-market: table on desktop, stacked cards on mobile; highlight the highest only if units/variety/dates are comparable.
**Weather:** location, period, forecast vs current label, temperature/rain with units, source, retrieved-at, uncertainty line.
**Crop:** issue as understood; "what the record says" summary; practical checks; source (KCC record: state, district, date; or document title/publisher/date); escalation block "Ask the Kisan Call Centre on 1551 or your local KVK" when uncertain. No doses, no definitive diagnosis.
**Trust labels (text, not just colour):** "Live data retrieved", "Cached (time)", "No recent record found", "Source found", "Needs clarification", "No suitable source found", "Historical call-centre advice", "Forecast".
Never show an LLM "confidence %".

## 6. WhatsApp content rules
- Voice reply <= about 3 short sentences; text copy may carry a source line ("Source: Agmarknet, 31 Oct 2026").
- Numbers spoken carefully: test TTS on prices, units and place names; spell units out in speech text ("rupees per quintal").
- One clarification question at a time, answerable in a word ("Which market: Warangal or Khammam?").
- Greeting/help message lists three things the bot can do, in the user's language.
- Refusals are warm and specific: say what cannot be answered and who to ask (1551).
- Never reply outside the 24-hour window.

## 7. Dashboard
Cards: queries by intent, language, district/crop; STT-error flags; refusal rate; latency p50/p95. Charts with labels and units; no vanity metrics. Evaluation page: WER table by language x condition, retrieval-vs-no-retrieval comparison, refusal-suite pass rate, with run date and model names.

## 8. Accessibility and responsiveness
Keyboard operable, visible focus, screen-reader labels (mic, play, upload, language), text for every audio answer, no autoplay, readable metadata, mobile single column with the mic reachable one-handed, desktop centred column with an optional evidence side panel.

## 9. Demo script (60 seconds)
0 to 10 s: a farmer in a noisy field sends a Telugu voice note. 10 to 30 s: the reply arrives as voice plus text with the source and date. 30 to 45 s: a risky dose question gets a polite refusal pointing to 1551. 45 to 60 s: the evaluation chart (WER clean vs noisy vs phone-quality) and the three Gnani models named on screen. Use synthetic or consented data only.
