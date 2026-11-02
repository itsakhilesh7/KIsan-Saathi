"""Unit tests for Item 1: Default reply language and user preferences repository.

Unknown-language fallbacks (unsupported media, too long, empty transcript,
generic errors, TTS fallback voice) must use the PRIMARY language from
config/pilot.yaml (te-IN currently), not TTS_DEFAULT_LANG (hi-IN).
Also verifies that the user preference repository remembers last seen language.
"""

from backend.app.core.config import Settings
from backend.app.integrations.gnani.tts import pick_voice
from backend.app.repositories.user_preferences import SQLiteUserPreferencesRepository
from backend.app.services.orchestrator import (
    AUDIO_TOO_LONG_MESSAGES,
    EMPTY_TRANSCRIPT_MESSAGES,
    FALLBACK_MESSAGES,
    UNSUPPORTED_MEDIA_MESSAGES,
)


def test_pick_voice_uses_pilot_primary_language_when_none(tmp_path):
    """When language is None or unmapped, pick_voice must fall back to pilot primary language (te-IN)."""
    settings = Settings()
    assert settings.pilot_primary_language == "te-IN"

    voice, lang = pick_voice(None, settings=settings)
    assert lang == "te-IN"
    assert voice == "Lavanya"

    # Also for an unmapped language
    voice_unmapped, lang_unmapped = pick_voice("klingon", settings=settings)
    assert lang_unmapped == "te-IN"
    assert voice_unmapped == "Lavanya"


def test_user_preferences_repository_lifecycle(tmp_path):
    """User preferences repo remembers last seen language across instances."""
    db_file = tmp_path / "user_pref.sqlite3"
    repo1 = SQLiteUserPreferencesRepository(db_path=str(db_file))

    assert repo1.get_language("user_hash_123") is None
    repo1.set_language("user_hash_123", "hi-IN")
    assert repo1.get_language("user_hash_123") == "hi-IN"

    # Test persistence on second instance
    repo2 = SQLiteUserPreferencesRepository(db_path=str(db_file))
    assert repo2.get_language("user_hash_123") == "hi-IN"

    # Update language
    repo2.set_language("user_hash_123", "te-IN")
    assert repo2.get_language("user_hash_123") == "te-IN"


def test_message_dictionaries_have_primary_pilot_language():
    """All fallback dictionaries must define te-IN."""
    for d in (EMPTY_TRANSCRIPT_MESSAGES, FALLBACK_MESSAGES, AUDIO_TOO_LONG_MESSAGES, UNSUPPORTED_MEDIA_MESSAGES):
        assert "te-IN" in d
        assert len(d["te-IN"]) > 0
