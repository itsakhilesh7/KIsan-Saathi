"""Unit tests for orchestrator hardening (language-aware fallbacks, audio limits, event logging)."""

import pytest

from backend.app.core.messages import MESSAGES

EMPTY_TRANSCRIPT_MESSAGES = MESSAGES["empty_transcript"]
FALLBACK_MESSAGES = MESSAGES["fallback_1551"]
AUDIO_TOO_LONG_MESSAGES = MESSAGES["audio_too_long"]
UNSUPPORTED_MEDIA_MESSAGES = MESSAGES["unsupported_media"]



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


@pytest.mark.asyncio
async def test_unsupported_message_type_uses_remembered_or_pilot_language():
    """Unsupported message types (e.g. image/sticker) must reply in remembered language or pilot primary."""
    from unittest.mock import AsyncMock, patch

    from backend.app.core.config import Settings
    from backend.app.services.orchestrator import _user_pref_repo, handle_incoming_message

    settings = Settings(PHONE_HASH_SALT="salt_abc")
    phone = "919876543210"

    # 1. No prior history -> pilot primary language (te-IN)
    with patch("backend.app.channels.whatsapp.client.send_text", new_callable=AsyncMock) as mock_send:
        await handle_incoming_message({"type": "image", "from": phone}, settings=settings)
        assert mock_send.called
        sent_text = mock_send.call_args[0][1]
        assert "సహాయం కోసం" in sent_text

    # 2. User has remembered language hi-IN -> replies in Hindi
    from backend.app.core.logging import hash_phone
    phone_hash = hash_phone(phone, settings.PHONE_HASH_SALT)
    _user_pref_repo.set_language(phone_hash, "hi-IN")

    with patch("backend.app.channels.whatsapp.client.send_text", new_callable=AsyncMock) as mock_send:
        await handle_incoming_message({"type": "image", "from": phone}, settings=settings)
        assert mock_send.called
        sent_text = mock_send.call_args[0][1]
        assert "सहायता के लिए" in sent_text
