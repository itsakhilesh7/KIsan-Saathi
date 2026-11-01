# Kisan Saathi

WhatsApp voice assistant for farmers: voice note in -> Gnani Prisma (STT) -> Evon (LLM) -> Gnani Timbre (TTS) -> voice note out.

## Setup (Windows PowerShell)
```
winget install Gyan.FFmpeg          # then open a NEW terminal; check: ffmpeg -version
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env              # fill in GNANI_API_KEY first
```
macOS/Linux: `source .venv/bin/activate` and `cp .env.example .env`.

## Step 1 - model smoke tests (no WhatsApp needed)
```
python -m scripts.test_gnani --audio data/clips/te_01.m4a
python -m scripts.test_gnani --tts "నమస్కారం, మీకు ఎలా సహాయం చేయాలి?" --lang te-IN
```
Play `out/reply.ogg` to confirm it sounds right.

## Step 2 - baseline accuracy
Put your clips in `data/clips/`, fill `data/transcripts.csv`, then:
```
python -m scripts.eval_wer
```

## Step 3 - run the server
```
uvicorn app.main:app --reload --port 8000
cloudflared tunnel --url http://localhost:8000     # or: ngrok http 8000
```
In Meta dashboard -> WhatsApp -> Configuration: Callback URL = `<tunnel-url>/webhook`,
Verify token = your `WHATSAPP_VERIFY_TOKEN`, subscribe to the `messages` field.

LLM_BASE_URL empty = echo mode (bot repeats what it heard, in the same language), so you can test the whole voice loop before Evon is hosted.

## Tests
```
pytest -q
```
