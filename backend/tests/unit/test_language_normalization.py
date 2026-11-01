"""Unit tests for language normalization layer and Timbre voice selection (MOCKED)."""

from backend.app.core.config import Settings
from backend.app.integrations.gnani.stt import normalize_language_code
from backend.app.integrations.gnani.tts import pick_voice


def test_language_normalization_aliases():
    """Verify various casing and dialect string mappings."""
    assert normalize_language_code("te") == "te-IN"
    assert normalize_language_code("tel") == "te-IN"
    assert normalize_language_code("telugu") == "te-IN"
    assert normalize_language_code("te-IN") == "te-IN"
    assert normalize_language_code("te-in") == "te-IN"

    assert normalize_language_code("hi") == "hi-IN"
    assert normalize_language_code("hin") == "hi-IN"
    assert normalize_language_code("hindi") == "hi-IN"
    assert normalize_language_code("hi-IN") == "hi-IN"

    assert normalize_language_code("en") == "en-IN"
    assert normalize_language_code("english") == "en-IN"
    assert normalize_language_code("en-IN") == "en-IN"

    assert normalize_language_code("hinglish") == "hi-en"
    assert normalize_language_code("hi-en") == "hi-en"

    assert normalize_language_code(None) is None
    assert normalize_language_code("") is None


def test_pick_voice_timbre_v25():
    """Verify Timbre v2.5 assigns designated voice per language."""
    s = Settings(TTS_MODEL="timbre-v2.5")

    voice, lang = pick_voice("te-IN", s)
    assert voice == "Lavanya"
    assert lang == "te-IN"

    voice, lang = pick_voice("hi-IN", s)
    assert voice == "Nalini"
    assert lang == "hi-IN"

    voice, lang = pick_voice("en-IN", s)
    assert voice == "Kaveri"
    assert lang == "en-IN"

    voice, lang = pick_voice("hi-en", s)
    assert voice == "Poorvi"
    assert lang == "hi-en"

    # Unknown language falls back to default hi-IN Nalini
    voice, lang = pick_voice("unrecognized", s)
    assert voice == "Nalini"
    assert lang == "hi-IN"


def test_pick_voice_timbre_v30():
    """Verify Timbre v3.0 uses multilingual voice across all languages."""
    s = Settings(TTS_MODEL="timbre-v3.0", TTS_V3_VOICE="Shivani")

    voice, lang = pick_voice("te-IN", s)
    assert voice == "Shivani"
    assert lang == "te-IN"

    voice, lang = pick_voice("hi-IN", s)
    assert voice == "Shivani"
    assert lang == "hi-IN"
