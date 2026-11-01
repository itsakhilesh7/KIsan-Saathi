"""Thin async client for Gnani Prisma (STT) and Timbre (TTS)."""
import asyncio
import os
import tempfile

import httpx

from . import audio, config


class GnaniError(Exception):
    pass


def _headers() -> dict:
    if not config.GNANI_API_KEY:
        raise GnaniError("GNANI_API_KEY is not set in .env")
    return {"X-API-Key-ID": config.GNANI_API_KEY}


async def _post(client: httpx.AsyncClient, url: str, **kw) -> httpx.Response:
    last = None
    for attempt in range(3):
        try:
            r = await client.post(url, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                last = GnaniError(f"{r.status_code}: {r.text[:200]}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            return r
        except httpx.TransportError as e:
            last = e
            await asyncio.sleep(1.5 * (attempt + 1))
    raise GnaniError(f"Request failed after retries: {last}")


async def transcribe_short(wav_path: str, language_code: str | None = None) -> dict:
    """One REST call. Audio must be <= 30 s."""
    lang = language_code or config.STT_LANGUAGE
    with open(wav_path, "rb") as f:
        data_bytes = f.read()
    form = {"language_code": lang}
    # Prisma v2.5 is the API default; the model field is only needed for v3.0.
    if config.STT_MODEL == "prisma-v3.0":
        form["model"] = "prisma-v3.0"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await _post(
            client, config.STT_URL, headers=_headers(),
            files={"audio_file": (os.path.basename(wav_path), data_bytes, "audio/wav")},
            data=form,
        )
    try:
        body = r.json()
    except ValueError:
        raise GnaniError(f"STT non-JSON response ({r.status_code}): {r.text[:200]}")
    if r.status_code != 200 or not body.get("success", False):
        raise GnaniError(f"STT error {r.status_code}: {body}")
    return body


async def transcribe(wav_path: str, language_code: str | None = None) -> dict:
    """Handles clips longer than 30 s by chunking. Returns transcript + detected language."""
    with tempfile.TemporaryDirectory() as tmp:
        chunks = await asyncio.to_thread(audio.split_wav, wav_path, tmp, config.MAX_STT_SECONDS)
        parts, detected = [], None
        for c in chunks:
            res = await transcribe_short(c, language_code)
            if res.get("transcript"):
                parts.append(res["transcript"].strip())
            detected = detected or res.get("detected_language_code")
        return {"transcript": " ".join(parts).strip(), "detected_language_code": detected,
                "chunks": len(chunks)}


def pick_voice(language: str) -> tuple[str, str]:
    """Returns (voice, language) valid for the configured TTS model."""
    if config.TTS_MODEL == "timbre-v3.0":
        return config.TTS_V3_VOICE, language
    lang = language if language in config.TTS_V25_VOICES else config.TTS_DEFAULT_LANG
    return config.TTS_V25_VOICES[lang], lang


async def synthesize(text: str, language: str) -> bytes:
    """Returns WAV bytes."""
    voice, lang = pick_voice(language)
    payload = {
        "text": text,
        "voice": voice,
        "model": config.TTS_MODEL,
        "language": lang,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 48000, "num_channels": 1, "sample_width": 2,
            "encoding": "linear_pcm", "container": "wav",
        },
    }
    async with httpx.AsyncClient(timeout=90) as client:
        r = await _post(client, config.TTS_URL,
                        headers={**_headers(), "Content-Type": "application/json"}, json=payload)
    if r.status_code != 200 or "audio" not in r.headers.get("content-type", ""):
        raise GnaniError(f"TTS error {r.status_code}: {r.text[:300]}")
    return r.content
