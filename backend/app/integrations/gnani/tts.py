"""Gnani Timbre Text-to-Speech (TTS) REST adapter.

Verified against docs/gnani-api-notes.md.
Timbre REST endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Header: X-API-Key-ID, Content-Type: application/json
"""

import asyncio
import logging
from typing import Any

import httpx

from ...core.config import TTS_URL, TTS_V25_VOICES, Settings, get_settings
from ...core.http_client import get_http_client
from .errors import GnaniRateLimitError, TTSError
from .stt import normalize_language_code

log = logging.getLogger("gnani.tts")


def pick_voice(language: str | None, settings: Settings | None = None) -> tuple[str, str]:
    """Selects a valid (voice, language) tuple for the configured TTS model.

    Rules from docs/gnani-api-notes.md:
    - timbre-v2.5 voices are single-language. A mismatch returns HTTP 400.
    - timbre-v3.0 voices speak all 10 supported Indian languages.
    - Fallback default uses the pilot primary language (pilot.yaml, e.g. te-IN).
    """
    cfg = settings or get_settings()
    primary_lang = cfg.pilot_primary_language
    norm_lang = normalize_language_code(language) or primary_lang

    if cfg.TTS_MODEL == "timbre-v3.0":
        # In v3.0, every voice speaks all languages
        return cfg.TTS_V3_VOICE, norm_lang

    # timbre-v2.5: verify language has a designated voice
    if norm_lang in TTS_V25_VOICES:
        return TTS_V25_VOICES[norm_lang], norm_lang

    fallback_lang = primary_lang if primary_lang in TTS_V25_VOICES else cfg.TTS_DEFAULT_LANG
    log.warning(
        "Language '%s' (normalized: '%s') not mapped in Timbre v2.5 voices; falling back to primary/default '%s'",
        language,
        norm_lang,
        fallback_lang,
    )
    return TTS_V25_VOICES[fallback_lang], fallback_lang


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    json_data: dict[str, Any],
    max_retries: int = 3,
    timeout: float = 90.0,
) -> httpx.Response:
    """Performs HTTP POST with retry for 429 and 5xx errors."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            r = await client.post(url, headers=headers, json=json_data, timeout=timeout)
            if r.status_code == 429:
                log.warning("Gnani TTS 429 rate limit (attempt %d/%d)", attempt + 1, max_retries)
                last_err = GnaniRateLimitError("Rate limit exceeded on Gnani TTS endpoint.")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code in (500, 502, 503, 504):
                log.warning("Gnani TTS server error %d (attempt %d/%d)", r.status_code, attempt + 1, max_retries)
                last_err = TTSError(f"Gnani TTS server error {r.status_code}: {r.text[:200]}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            return r
        except httpx.TransportError as e:
            log.warning("Gnani TTS transport error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            last_err = TTSError(f"Transport error connecting to Gnani TTS: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))

    raise last_err or TTSError("Gnani TTS failed after maximum retries.")


async def synthesize(
    text: str,
    language: str,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> bytes:
    """Synthesizes text to speech using Gnani Timbre. Returns binary WAV bytes."""
    cfg = settings or get_settings()
    if not cfg.GNANI_API_KEY:
        raise TTSError("GNANI_API_KEY is not set in environment or config.")

    voice, target_lang = pick_voice(language, cfg)

    payload = {
        "text": text,
        "voice": voice,
        "model": cfg.TTS_MODEL,
        "language": target_lang,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 48000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }

    headers = {
        "X-API-Key-ID": cfg.GNANI_API_KEY,
        "Content-Type": "application/json",
    }

    c = client or get_http_client()
    r = await _post_with_retry(c, TTS_URL, headers=headers, json_data=payload, timeout=90.0)
    content_type = r.headers.get("content-type", "")
    if r.status_code != 200 or ("audio" not in content_type and "octet-stream" not in content_type):
        raise TTSError(f"Gnani TTS failed ({r.status_code}, content-type: {content_type}): {r.text[:300]}")
    return r.content
