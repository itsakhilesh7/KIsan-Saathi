"""Unit tests for Pydantic contracts (MOCKED)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.schemas.conversation import AnswerPayload, VoiceResponse
from backend.app.schemas.evidence import Evidence, SourceType
from backend.app.schemas.intent import IntentSlots, IntentType, ParsedIntent


def test_evidence_contract():
    """Verify evidence schema validates all required fields."""
    ev = Evidence(
        evidence_id="mandi-warangal-cotton-20261101",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet data.gov.in",
        source_url="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
        publisher="Ministry of Agriculture",
        retrieved_at=datetime.now(timezone.utc),
        observation_or_publication_date="2026-11-01",
        location="Warangal, Telangana",
        data={"modal_price": 7250, "commodity": "Cotton", "unit": "Rs/Quintal"},
        limitations=["Wholesale daily price; retail and transport costs may vary."],
    )
    assert ev.evidence_id.startswith("mandi-")
    assert ev.source_type == SourceType.MANDI_RECORD
    assert ev.data["modal_price"] == 7250


def test_intent_strict_contract():
    """Verify intent schema adheres to strict enum and slots structure."""
    intent = ParsedIntent(
        intent=IntentType.MANDI_PRICE_QUERY,
        language="te-IN",
        slots=IntentSlots(commodity="cotton", district="Warangal", state="Telangana"),
        missing_required_slots=[],
        clarification_needed=False,
    )
    assert intent.intent == "mandi_price_query"
    assert intent.slots.commodity == "cotton"
    assert intent.slots.market is None

    # Invalid intent must raise ValidationError
    with pytest.raises(ValidationError):
        ParsedIntent(intent="arbitrary_unallowlisted_tool", language="te-IN")


def test_voice_response_contract():
    """Verify voice response payload structure."""
    vr = VoiceResponse(
        request_id="req-12345",
        transcript="పత్తి ధర ఎంత?",
        language="te-IN",
        answer=AnswerPayload(
            text="ఈ రోజు వరంగల్ మార్కెట్‌లో పత్తి సగటు ధర క్వింటాలుకు 7,250 రూపాయలు.",
            language="te-IN",
            audio_available=True,
            audio_url="https://example.com/audio/reply.ogg",
        ),
        llm_disclosed_name="echo",
        timings={"stt": 0.85, "llm": 0.0, "tts_convert": 1.2, "total": 2.1},
    )
    assert vr.request_id == "req-12345"
    assert vr.answer is not None
    assert vr.answer.audio_available is True
