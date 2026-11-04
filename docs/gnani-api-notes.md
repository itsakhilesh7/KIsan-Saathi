# Gnani API Notes (verified from docs.gnani.ai on 1 Nov 2026)

Source: https://docs.gnani.ai/api/introduction/quick-start and https://docs.gnani.ai/api/TTS/available-voices.md. Re-check the live docs if anything fails. Do **not** invent parameters beyond this file.

Auth for all REST calls: header `X-API-Key-ID: <GNANI_API_KEY>`. Keys are generated at https://app.gnani.ai/voice/.

## Speech-to-text: Prisma
**REST** `POST https://api.vachana.ai/stt/v3` (multipart form)
- File field `audio_file`. Formats: WAV, MP3, OGG, FLAC, AAC, M4A. Sample rate 8 to 44.1 kHz. **Max 30 seconds.**
- Form field `model`: add `prisma-v3.0` to use v3.0. **Prisma v2.5 is the default** when `model` is omitted.
- Form field `language_code`: e.g. `hi-IN`, `te-IN`, `en-IN`; **`indic-auto` is Prisma v3.0 only**. Optional `format=transcribe` (e.g. numbers as digits) appears in the v3.0 example.
- v3.0 response: `success`, `request_id`, `transcript`, `model`, `detected_language_code`, `processing_time`, `end_to_end_latency`. v2.5 response: `success`, `request_id`, `transcript`, `model`.
- Our code sends `model` only when it is `prisma-v3.0`.

**Realtime** `wss://api.vachana.ai/stt/v3/stream`: upgrade headers `x-api-key-id`, `model`, `language_code` (a code, `indic-auto`, or a list like `hi-IN,en-IN` for v3.0), `x-sample-rate` (16000 in the example). Send binary PCM frames (16-bit mono, 8 or 16 kHz, 1024 bytes per frame); send `{"type":"commit"}` to finish. Events: `{"type":"transcript","text",...,"segment_id","latency"}` and `{"type":"error","message"}`. Not used for the MVP (REST is enough).

**Batch transcription** exists (https://docs.gnani.ai/api/STTBatch/Introduction.md). Not verified or used yet.

## Text-to-speech: Timbre
**REST** `POST https://api.vachana.ai/api/v1/tts/inference`, JSON body:
```json
{"text": "...", "voice": "Nalini", "model": "timbre-v2.5", "language": "hi-IN", "speed": 1.0,
 "audio_config": {"sample_rate": 48000, "num_channels": 1, "sample_width": 2, "encoding": "linear_pcm", "container": "wav"}}
```
Returns binary audio (`200 OK`, e.g. `audio/wav`). Streaming SSE: `POST /api/v1/tts/sse` (events `start`, `chunk` with base64 audio, `complete`). Realtime WS: `wss://api.vachana.ai/api/v1/tts`.

**Models and voices (they are NOT interchangeable; a mismatch returns `400 Bad Request` listing valid voices):**
- `timbre-v2.5`: 42 voices, each with ONE preferred language; set `language` to match (or `auto` to detect from script). Telugu `te-IN`: Suhana, Lehara, Lavanya, Yukti, Varuni. Hindi `hi-IN`: Nalini, Bhavna, Yashvi, Urmila, Jwala, Chitra, Ambuja, Deepak, Roopesh, Vikrant, Hemraj, Jalaj, Omkar. English `en-IN`: Kaveri, Trupti, Devika, Pranav, Shlok, Girish. Hinglish `hi-en`: Poorvi. Other languages also exist (Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi).
- `timbre-v3.0`: 13 voices; **every voice speaks all 10 languages** (hi, en, ta, te, kn, ml, mr, pa, bn, gu). Female: Shivani, Lakshmi, Kalpana, Chetana, Vasudha, Riyaa, Tarika. Male: Avinash, Shubham, Prakash, Devansh, Yashraj, Harshad. Supports inline audio tags (`<pauses>`, `<laugh>`, ...). With v2.5 the tags are stripped; text consisting only of tags returns 400.
- Preview voices in the Gnani TTS playground before choosing.

**Voice cloning** (not in MVP): `POST /api/v1/tts/voice-clone/embeddings` (field `audio_file`, 5 to 30 s) returns a `speaker_embedding`; synthesise with `model: "vachana-vc-v1"` plus the embedding. Needs explicit consent if ever used.

## LLM: Evon
Model card name: `gnani/gnani-evon-v3.3-30B-A3B` (hybrid Mamba MoE, about 30B total / 3B active, 10 Indian languages + English, 128K context, Apache 2.0). Running it needs roughly 21 GB VRAM even quantised (Q4).
- **Naming note:** Friendli lists the model as `gnani/gnani-evon-v3.3-30B-A3B` (dedicated endpoints only); the Hugging Face model card quick-start uses `gnani/gnani-evon-v3.3`. The setting `LLM_MODEL` must equal the exact served model name expected by the host endpoint.
- **Generation params (Evon specific):** Supports `LLM_EXTRA_BODY_JSON` for extra generation fields: `{"chat_template_kwargs": {"enable_thinking": false}, "repetition_penalty": 1.1, "top_p": 0.95}`.
- Always record `LLM_DISCLOSED_NAME` in every event log and eval output. Plan: OpenAI-compatible endpoint served by vLLM/SGLang on a rented GPU, or a hosted provider that lists it. Always record which model answered.

## Python/SDK
Other documents mention a `gnani-vachana` SDK. It is **unverified**; our adapters use REST directly with `httpx`. If you adopt the SDK, check its installed version and README first.

## Unverified items (check live on Day 1; record results in `docs/decisions.md`)
- Per-request credit cost and rate limits for the 5,000 credits.
- Whether `language: "auto"` works for Timbre v2.5 with Telugu text.
- Whether other `sample_rate` values (e.g. 24000) are accepted by TTS (we use 48000 as in the docs).
- Whether Prisma accepts WhatsApp OGG/Opus directly (it lists OGG). If yes, skip conversion for clips <= 25 s as an optimisation; still convert for chunking.
- Telugu STT/TTS quality on farm vocabulary, place names and numbers.
- Hinglish handling under `indic-auto` vs explicit `hi-IN`.
