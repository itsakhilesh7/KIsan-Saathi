"""Test reproduction for TTS_DEFAULT_LANG on Settings."""

from backend.app.core.config import Settings
from backend.app.integrations.gnani.tts import pick_voice


def test_pick_voice_with_none_uses_pilot_primary_language():
    """Prisma STT returning detected_language_code=None triggers pick_voice with None.

    Should fall back to Settings.pilot_primary_language (te-IN -> Lavanya) without raising AttributeError.
    """
    settings = Settings()
    assert hasattr(settings, "TTS_DEFAULT_LANG")
    voice, lang = pick_voice(None, settings=settings)
    assert lang == "te-IN"
    assert voice == "Lavanya"
