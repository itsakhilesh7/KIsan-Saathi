"""Unit tests for Section D (Speech Quality) and Section E (Short/Empty Audio)."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.config import Settings
from backend.app.core.messages import format_natural_date, get_message, to_speech_text
from backend.app.repositories.events import EventRepository
from backend.app.schemas.evidence import Evidence, SourceType
from backend.app.services.answer_composer import compose_mandi_answer
from backend.app.services.orchestrator import handle_voice_message, set_event_repo


def test_natural_dates_per_language_without_glued_suffixes():
    """Verify natural date formatting embeds language postpositions cleanly."""
    d_te = format_natural_date("2026-11-05", "te-IN")
    d_hi = format_natural_date("2026-11-05", "hi-IN")
    d_en = format_natural_date("2026-11-05", "en-IN")
    d_hien = format_natural_date("2026-11-05", "hi-en")

    assert d_te == "నవంబర్ 5న"
    assert d_hi == "5 नवंबर को"
    assert d_en == "5 November"
    assert d_hien == "5 November ko"

    # Verify that in composed text, no duplicate suffix like 'నన' or 'కో కో' appears
    ev = Evidence(
        evidence_id="mandi_ev1",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-05",
        location="Warangal, Warangal, Telangana",
        data={
            "state": "Telangana",
            "district": "Warangal",
            "market": "Warangal",
            "commodity": "Cotton",
            "arrival_date": "2026-11-05",
            "modal_price": 7200.0,
        },
        limitations=[],
    )

    ans_te = compose_mandi_answer([ev], language="te-IN")
    assert "నవంబర్ 5న" in ans_te
    assert "నన" not in ans_te

    ans_hi = compose_mandi_answer([ev], language="hi-IN")
    assert "5 नवंबर को" in ans_hi
    assert "को को" not in ans_hi


def test_speech_script_harmonization():
    """Verify to_speech_text translates Latin pilot entities and technical symbols to native script."""
    raw_te = "Warangal మార్కెట్లో 5 Novemberన టమాటా modal price Rs 2500, ఉష్ణోగ్రత 32°C, వర్షం 20%."
    speech_te = to_speech_text(raw_te, "te-IN")

    assert "వరంగల్" in speech_te
    assert "డిగ్రీల సెల్సియస్" in speech_te
    assert "శాతం" in speech_te
    assert "రూపాయలు" in speech_te
    assert "Warangal" not in speech_te
    assert "°C" not in speech_te
    assert "%" not in speech_te

    raw_hi = "Warangal Cherial mandi me tamatar 30°C and 40%."
    speech_hi = to_speech_text(raw_hi, "hi-IN")
    assert "वारंगल" in speech_hi
    assert "चेरियाल" in speech_hi
    assert "डिग्री सेल्सियस" in speech_hi
    assert "प्रतिशत" in speech_hi


@pytest.mark.asyncio
async def test_audio_under_one_second_rejected_without_stt(tmp_path):
    """Audio < 1.0s must trigger language-aware empty_transcript message without calling STT."""
    event_db = str(tmp_path / "events.sqlite3")
    e_repo = EventRepository(db_path=event_db)
    set_event_repo(e_repo)

    settings = Settings(PHONE_HASH_SALT="salt_audio", PILOT_PRIMARY_LANGUAGE="te-IN")
    mock_channel = AsyncMock()
    mock_channel.channel_name = "test_whatsapp"
    mock_channel.download_media = AsyncMock(return_value=b"SHORT_0.2S_OGG")
    mock_channel.send_text = AsyncMock()

    msg = {
        "from": "919988112233",
        "type": "audio",
        "media_id": "media_short_02s",
        "mime_type": "audio/ogg",
    }

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=0.2), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt:

        await handle_voice_message(msg, settings, client=mock_channel)

        # STT must NOT be called
        assert not mock_stt.called
        assert mock_channel.send_text.called

        sent_text = mock_channel.send_text.call_args[0][1]
        expected_te = get_message("empty_transcript", "te-IN")
        assert sent_text == expected_te

        # Verify event logged with status audio_too_short
        events = e_repo.get_recent_events(limit=5)
        assert len(events) >= 1
        assert events[0]["status"] == "audio_too_short"
        assert events[0]["audio_duration_seconds"] == 0.2


    set_event_repo(None)


@pytest.mark.asyncio
async def test_error_event_logging_stores_exception_class_name_only_and_no_raw_transcript(tmp_path):
    """On failure, log_event must capture error_type (class name only), intent/tool, and NO raw transcript."""
    event_db = str(tmp_path / "events_err.sqlite3")
    e_repo = EventRepository(db_path=event_db)
    set_event_repo(e_repo)

    settings = Settings(
        PHONE_HASH_SALT="salt_err",
        STORE_RAW_TRANSCRIPTS=False,
    )
    mock_channel = AsyncMock()
    mock_channel.channel_name = "test_whatsapp"
    mock_channel.send_text = AsyncMock()

    msg = {
        "from": "919988112244",
        "text": "What is the price of cotton in Warangal?",
    }

    class CustomSimulatedAPIError(Exception):
        pass

    with patch("backend.app.services.orchestrator.fetch_mandi_prices", side_effect=CustomSimulatedAPIError("Sensitive internal DB error detail")):
        await handle_voice_message if False else None
        from backend.app.services.orchestrator import handle_text_message
        await handle_text_message(msg, settings, client=mock_channel)

        events = e_repo.get_recent_events(limit=5)

        assert len(events) >= 1
        err_event = events[0]
        assert err_event["status"] == "error"
        # Only class name, never the message detail
        assert err_event["error_type"] == "CustomSimulatedAPIError"
        assert "Sensitive internal DB error detail" not in str(err_event)
        # No raw transcripts
        assert err_event.get("transcript") is None

    set_event_repo(None)
