"""Gnani Prisma Speech-to-Text (STT) REST adapter.

Verified against docs/gnani-api-notes.md.
Prisma REST endpoint: POST https://api.vachana.ai/stt/v3
Header: X-API-Key-ID
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from ...core.config import MAX_STT_SECONDS, STT_URL, Settings, get_settings
from ...core.http_client import get_http_client
from .errors import GnaniRateLimitError, STTError

log = logging.getLogger("gnani.stt")

# Language code alias mappings for Prisma STT output normalisation.
# UNVERIFIED FORMAT: Prisma v3.0's exact casing and structure for detected_language_code
# is not yet verified live. This layer normalizes known representations into standard BCP-47.
_LANG_ALIASES: dict[str, str] = {
    "te": "te-IN",
    "tel": "te-IN",
    "telugu": "te-IN",
    "te-in": "te-IN",
    "te-IN": "te-IN",
    "hi": "hi-IN",
    "hin": "hi-IN",
    "hindi": "hi-IN",
    "hi-in": "hi-IN",
    "hi-IN": "hi-IN",
    "en": "en-IN",
    "eng": "en-IN",
    "english": "en-IN",
    "en-in": "en-IN",
    "en-IN": "en-IN",
    "hi-en": "hi-en",
    "hinglish": "hi-en",
    "hi_en": "hi-en",
}


def normalize_language_code(raw_code: str | None) -> str | None:
    """Normalizes raw language code from STT into the canonical voice format.

    NOTE: FORMAT UNVERIFIED. Marked as unverified until live tests confirm
    Prisma v3.0 detected_language_code outputs.
    """
    if not raw_code:
        return None
    cleaned = raw_code.strip()
    return _LANG_ALIASES.get(cleaned.lower(), _LANG_ALIASES.get(cleaned, cleaned))


def _get_headers(settings: Settings) -> dict[str, str]:
    if not settings.GNANI_API_KEY:
        raise STTError("GNANI_API_KEY is not set in environment or config.")
    return {"X-API-Key-ID": settings.GNANI_API_KEY}


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    max_retries: int = 3,
    timeout: float = 60.0,
    **kwargs: Any,
) -> httpx.Response:
    """Performs HTTP POST with bounded exponential backoff for 429 and 5xx."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            r = await client.post(url, headers=headers, timeout=timeout, **kwargs)
            if r.status_code == 429:
                log.warning("Gnani STT 429 rate limit encountered (attempt %d/%d)", attempt + 1, max_retries)
                last_err = GnaniRateLimitError("Rate limit exceeded on Gnani STT endpoint.")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code in (500, 502, 503, 504):
                log.warning("Gnani STT server error %d (attempt %d/%d)", r.status_code, attempt + 1, max_retries)
                last_err = STTError(f"Gnani server error {r.status_code}: {r.text[:200]}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            return r
        except httpx.TransportError as e:
            log.warning("Gnani STT transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            last_err = STTError(f"Transport error connecting to Gnani STT: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))

    raise last_err or STTError("Gnani STT failed after maximum retries.")


async def transcribe_short(
    wav_path: str,
    language_code: str | None = None,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Transcribes an audio clip (<= 30 s) using a single Gnani Prisma REST call."""
    cfg = settings or get_settings()
    lang = language_code or cfg.STT_LANGUAGE

    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"Audio file not found at {wav_path}")

    with open(wav_path, "rb") as f:
        audio_bytes = f.read()

    form_data: dict[str, str] = {"language_code": lang}
    # Prisma v2.5 is the API default; send model only for v3.0 per gnani-api-notes.md
    if cfg.STT_MODEL == "prisma-v3.0":
        form_data["model"] = "prisma-v3.0"

    headers = _get_headers(cfg)
    files = {"audio_file": (os.path.basename(wav_path), audio_bytes, "audio/wav")}

    c = client or get_http_client()
    r = await _post_with_retry(c, STT_URL, headers=headers, data=form_data, files=files, timeout=60.0)
    try:
        body = r.json()
    except ValueError:
        raise STTError(f"Gnani STT returned non-JSON response ({r.status_code}): {r.text[:200]}")

    if r.status_code != 200 or not body.get("success", False):
        raise STTError(f"Gnani STT request failed ({r.status_code}): {body}")

    return body


async def transcribe(
    wav_path: str,
    language_code: str | None = None,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Transcribes audio, chunking if necessary (using audio_service).

    Returns a dict with:
    - transcript: full concatenated transcript
    - detected_language_code: normalized language code
    - raw_language_code: unnormalized code from Prisma
    - chunks: number of chunks processed
    """
    from ...services import audio_service

    cfg = settings or get_settings()
    duration = await asyncio.to_thread(audio_service.get_duration, wav_path)
    c = client or get_http_client()

    if duration <= MAX_STT_SECONDS:
        res = await transcribe_short(wav_path, language_code, settings=cfg, client=c)
        raw_lang = res.get("detected_language_code")
        return {
            "transcript": res.get("transcript", "").strip(),
            "detected_language_code": normalize_language_code(raw_lang),
            "raw_language_code": raw_lang,
            "chunks": 1,
        }

    # Chunk audio if longer than cutoff
    chunks = await asyncio.to_thread(audio_service.split_wav, wav_path, MAX_STT_SECONDS)
    parts: list[str] = []
    raw_lang = None
    for chunk in chunks:
        try:
            res = await transcribe_short(chunk, language_code, settings=cfg, client=c)
            text = res.get("transcript", "").strip()
            if text:
                parts.append(text)
            if not raw_lang:
                raw_lang = res.get("detected_language_code")
        finally:
            if os.path.exists(chunk) and chunk != wav_path:
                try:
                    os.remove(chunk)
                except OSError:
                    pass

    return {
            "transcript": " ".join(parts).strip(),
            "detected_language_code": normalize_language_code(raw_lang),
            "raw_language_code": raw_lang,
            "chunks": len(chunks),
        }
