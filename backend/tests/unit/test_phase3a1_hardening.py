"""Unit tests for Phase 3A.1 hardening and fixes.

Covers:
1. Greeting detection length & content threshold (crop advice question is not a greeting).
2. Unsupported intent fixed language-aware reply (no echo unless ECHO_UNSUPPORTED=true).
3. Script-based text language detection (Telugu, Devanagari, Latin/Hinglish, English).
4. First turn flag persistence on all messages (voice and text).
5. Mandi composer grouping by up to 2 markets, natural dates, and empty district handling.
6. MANDI_PRICE_UNIT configuration support.
7. Logging raw Prisma detected_language_code in events.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.config import Settings
from backend.app.schemas.evidence import Evidence, SourceType
from backend.app.schemas.intent import IntentType
from backend.app.services.answer_composer import (
    compose_mandi_answer,
    format_natural_date,
)
from backend.app.services.intent_service import detect_text_language, extract_intent
from backend.app.services.orchestrator import handle_text_message, handle_voice_message


def test_greeting_detection_requires_short_message_and_no_content():
    """Verify greeting is only classified when <= 4 words and has no other query content."""
    # 1. Short pure greetings -> GREETING_OR_HELP
    assert extract_intent("నమస్కారం").intent == IntentType.GREETING_OR_HELP
    assert extract_intent("హలో సర్").intent == IntentType.GREETING_OR_HELP
    assert extract_intent("Namaste").intent == IntentType.GREETING_OR_HELP
    assert extract_intent("Hello").intent == IntentType.GREETING_OR_HELP

    # 2. Advice question starting with greeting must NOT be classified as greeting
    advice_query = "నమస్కారం, నేను ఇక్కడ పత్తి పండిస్తున్నాను, మీరు నాకు ఏమైనా సలహా ఇవ్వగలరా?"
    res = extract_intent(advice_query)
    assert res.intent != IntentType.GREETING_OR_HELP
    assert res.intent == IntentType.UNSUPPORTED_OR_UNCLEAR


def test_detect_text_language_scripts():
    """Verify text language detection via script analysis and Hinglish keywords."""
    # Telugu script
    assert detect_text_language("వరంగల్ లో పత్తి ధర ఎంత?") == "te-IN"
    assert detect_text_language("నమస్కారం") == "te-IN"

    # Devanagari script (Hindi)
    assert detect_text_language("वारंगल में कपास का भाव क्या है?") == "hi-IN"
    assert detect_text_language("नमस्ते") == "hi-IN"

    # Latin script with Hindi/Hinglish vocabulary
    assert detect_text_language("Warangal me kapas ka bhav kya hai?") == "hi-en"
    assert detect_text_language("Namaste, mujhe mandi bhav batao") == "hi-en"

    # Plain English
    assert detect_text_language("What is the cotton price in Warangal?") == "en-IN"
    assert detect_text_language("Hello assistant, can you help me?") == "en-IN"


def test_format_natural_date():
    """Verify ISO dates are formatted naturally per language (Item 6)."""
    assert format_natural_date("2026-11-04", language="te-IN") == "4 నవంబర్"
    assert format_natural_date("2026-11-04", language="hi-IN") == "4 नवंबर"
    assert format_natural_date("2026-11-04", language="en-IN") == "4 November"
    assert format_natural_date("2026-11-04", language="hi-en") == "4 November"


def test_mandi_composer_groups_up_to_two_markets():
    """Verify composer groups by market, mentions up to 2 markets, and verifies numbers (Item 5)."""
    ev1 = Evidence(
        evidence_id="ev_01",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-04",
        location="Warangal APMC, Warangal, Telangana",
        data={
            "commodity": "Cotton",
            "market": "Warangal APMC",
            "district": "Warangal",
            "arrival_date": "2026-11-04",
            "modal_price": 7400.0,
        },
    )
    ev2 = Evidence(
        evidence_id="ev_02",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-04",
        location="Narsampet, Warangal, Telangana",
        data={
            "commodity": "Cotton",
            "market": "Narsampet",
            "district": "Warangal",
            "arrival_date": "2026-11-04",
            "modal_price": 7250.0,
        },
    )

    ans = compose_mandi_answer([ev1, ev2], language="te-IN", is_first_turn=False, requested_district="Warangal")
    # Both market prices must be cited and numbers verified
    assert "7400" in ans
    assert "7250" in ans
    assert "Warangal APMC" in ans
    assert "Narsampet" in ans
    assert "4 నవంబర్" in ans


def test_mandi_composer_unit_setting():
    """Verify MANDI_PRICE_UNIT setting is respected (empty by default, included when set)."""
    ev = Evidence(
        evidence_id="ev_01",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-04",
        location="Warangal APMC, Warangal, Telangana",
        data={
            "commodity": "Cotton",
            "market": "Warangal APMC",
            "district": "Warangal",
            "arrival_date": "2026-11-04",
            "modal_price": 7400.0,
        },
    )

    # 1. Default empty unit: no unit string
    ans_no_unit = compose_mandi_answer([ev], language="te-IN", unit="")
    assert "క్వింటాలుకు" not in ans_no_unit
    assert "7400" in ans_no_unit

    # 2. Configured unit: appends unit phrase
    ans_with_unit = compose_mandi_answer([ev], language="te-IN", unit="quintal")
    assert "క్వింటాలుకు" in ans_with_unit
    assert "7400" in ans_with_unit


def test_mandi_composer_empty_district_offers_state():
    """Verify that when a district has no records, message mentions the district and offers the state."""
    ans = compose_mandi_answer(
        [],
        language="te-IN",
        requested_district="Adilabad",
        requested_commodity="Cotton",
        requested_state="Telangana",
    )
    assert "Adilabad" in ans or "ఆదిలాబాద్" in ans
    assert "తెలంగాణ" in ans or "రాష్ట్ర" in ans


@pytest.mark.asyncio
async def test_unsupported_intent_never_echoes_by_default(tmp_path):
    """Verify unsupported query gets fixed help message and never calls LLM when ECHO_UNSUPPORTED=false."""
    settings = Settings(ECHO_UNSUPPORTED=False, TELEGRAM_BOT_TOKEN="mock_token")
    mock_client = AsyncMock()
    mock_client.channel_name = "telegram"

    msg = {"from": "918888888888", "text": "నమస్కారం, నేను ఇక్కడ పత్తి పండిస్తున్నాను, మీరు నాకు ఏమైనా సలహా ఇవ్వగలరా?"}

    with patch("backend.app.integrations.llm.openai_compatible.OpenAICompatibleLLM.answer", new_callable=AsyncMock) as mock_llm:
        await handle_text_message(msg, settings, client=mock_client)

        assert not mock_llm.called
        assert mock_client.send_text.called
        reply = mock_client.send_text.call_args[0][1]
        assert "మండి ధరల" in reply
        assert "వాతావరణం" in reply or "సలహాలు" in reply


@pytest.mark.asyncio
async def test_first_turn_flag_persists_on_text_and_voice(tmp_path):
    """Verify user is marked as seen on first text message, so AI intro appears only once."""
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_token")
    mock_client = AsyncMock()
    mock_client.channel_name = "telegram"

    msg1 = {"from": "917777777777", "text": "హలో"}
    msg2 = {"from": "917777777777", "text": "హలో"}

    # Turn 1: text message
    await handle_text_message(msg1, settings, client=mock_client)
    reply1 = mock_client.send_text.call_args[0][1]
    assert "కిసాన్ సాథీ AI సహాయకుడిని" in reply1

    # Turn 2: second text message -> AI disclaimer must NOT be repeated
    await handle_text_message(msg2, settings, client=mock_client)
    reply2 = mock_client.send_text.call_args[0][1]
    assert "కిసాన్ సాథీ AI సహాయకుడిని" not in reply2


@pytest.mark.asyncio
async def test_voice_event_records_raw_detected_language(tmp_path):
    """Verify EventRepository records raw_detected_language from Prisma STT."""
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_token")
    mock_client = AsyncMock()
    mock_client.channel_name = "telegram"
    mock_client.download_media.return_value = b"DUMMY_OGG"

    msg = {
        "from": "916666666666",
        "media_id": "test_voice_id",
        "mime_type": "audio/ogg",
    }

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=5.0), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt, \
         patch("backend.app.integrations.gnani.tts.synthesize", new_callable=AsyncMock) as mock_tts, \
         patch("backend.app.services.audio_service.wav_to_ogg_opus", side_effect=lambda src, dst: Path(dst).write_bytes(b"DUMMY_OGG")):

        mock_stt.return_value = {
            "transcript": "హలో",
            "detected_language_code": "te-IN_RAW_PRISMA",
            "raw_language_code": "te-IN_RAW_PRISMA",
            "chunks": 1,
        }
        mock_tts.return_value = b"DUMMY_WAV"

        from backend.app.services.orchestrator import get_event_repo
        await handle_voice_message(msg, settings, client=mock_client)

        events = get_event_repo().get_recent_events(limit=5)
        voice_events = [e for e in events if e.get("channel") == "telegram" and e.get("status") == "ok"]
        assert len(voice_events) > 0
        assert voice_events[0].get("raw_detected_language") == "te-IN_RAW_PRISMA"
