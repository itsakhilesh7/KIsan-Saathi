"""Test reproduction for TTS_DEFAULT_LANG on Settings."""

from backend.app.core.config import Settings
from backend.app.integrations.gnani.tts import pick_voice


def test_pick_voice_with_none_uses_settings_tts_default_lang():
    """Prisma STT returning detected_language_code=None triggers pick_voice with None.

    Should fall back to Settings.TTS_DEFAULT_LANG without raising AttributeError.
    """
    settings = Settings()
    # If TTS_DEFAULT_LANG is missing on Settings, this will raise AttributeError
    voice, lang = pick_voice(None, settings=settings)
    assert lang == "hi-IN"
    assert voice == "Nalini"
