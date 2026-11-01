"""Live integration smoke tests for Gnani Prisma STT and Timbre TTS.

LABEL: LIVE (SKIPPED WITHOUT KEYS).
These tests make real network calls to api.vachana.ai and consume API credits.
They are automatically skipped if GNANI_API_KEY is not set in backend/.env.
"""

import pytest

from backend.app.core.config import get_settings
from backend.app.integrations.gnani.tts import synthesize

settings = get_settings()
HAS_GNANI_KEY = bool(settings.GNANI_API_KEY.strip())


@pytest.mark.skipif(not HAS_GNANI_KEY, reason="GNANI_API_KEY not configured (MOCKED ONLY - LIVE CALL SKIPPED)")
@pytest.mark.asyncio
async def test_live_timbre_tts_telugu():
    """LIVE: Tests synthesis of short Telugu text on Timbre TTS endpoint."""
    text = "నమస్కారం రైతు సోదరులారా"
    wav_bytes = await synthesize(text, language="te-IN", settings=settings)
    assert len(wav_bytes) > 1000
    # Check WAV RIFF header magic bytes
    assert wav_bytes[:4] == b"RIFF"


@pytest.mark.skipif(not HAS_GNANI_KEY, reason="GNANI_API_KEY not configured (MOCKED ONLY - LIVE CALL SKIPPED)")
@pytest.mark.asyncio
async def test_live_timbre_tts_hindi():
    """LIVE: Tests synthesis of short Hindi text on Timbre TTS endpoint."""
    text = "नमस्ते किसान भाइयों"
    wav_bytes = await synthesize(text, language="hi-IN", settings=settings)
    assert len(wav_bytes) > 1000
    assert wav_bytes[:4] == b"RIFF"
