"""Unit tests for orchestrator hardening (language-aware fallbacks, audio limits, event logging)."""

from backend.app.services.orchestrator import (
    AUDIO_TOO_LONG_MESSAGES,
    EMPTY_TRANSCRIPT_MESSAGES,
    FALLBACK_MESSAGES,
    UNSUPPORTED_MEDIA_MESSAGES,
)


def test_language_aware_dictionaries_contain_all_four_languages():
    """Verify Hindi, Telugu, English, and Hinglish keys exist in all message maps."""
    required_langs = {"te-IN", "hi-IN", "en-IN", "hi-en"}
    assert required_langs.issubset(set(EMPTY_TRANSCRIPT_MESSAGES.keys()))
    assert required_langs.issubset(set(FALLBACK_MESSAGES.keys()))
    assert required_langs.issubset(set(AUDIO_TOO_LONG_MESSAGES.keys()))
    assert required_langs.issubset(set(UNSUPPORTED_MEDIA_MESSAGES.keys()))


def test_empty_transcript_messages_content():
    """Verify content of empty transcript prompts for each language."""
    assert "స్పష్టంగా" in EMPTY_TRANSCRIPT_MESSAGES["te-IN"]
    assert "साफ़" in EMPTY_TRANSCRIPT_MESSAGES["hi-IN"]
    assert "hear" in EMPTY_TRANSCRIPT_MESSAGES["en-IN"]
    assert "aawaz" in EMPTY_TRANSCRIPT_MESSAGES["hi-en"]


def test_fallback_messages_reference_1551():
    """Verify all fallback messages advise the 1551 helpline."""
    for lang in ["te-IN", "hi-IN", "en-IN", "hi-en"]:
        assert "1551" in FALLBACK_MESSAGES[lang]
