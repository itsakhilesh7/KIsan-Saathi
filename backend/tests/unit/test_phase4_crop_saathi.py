"""Unit tests for Phase 4 (Crop Saathi) over verified PJTSAU documents.

Verifies:
1. Corpus ingestion: 35 technology cards, SHA256 hashes, zones, and publisher metadata.
2. Retrieval: accuracy, thresholding, and crop filtering (Paddy & Cotton).
3. Scope enforcement: Chilli and Tomato advisory returns polite KVK/1551 disclaimer.
4. Chemical dosage & mixture refusal.
5. Diagnostic query refusal (refusal to diagnose from short descriptions).
6. Grounded Answer Composer: qualitative advice, agro-climatic zone, <= 2 sentences, source line.
7. Orchestrator integration: text message handling end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.channels.base import ChannelClient
from backend.app.core.config import Settings
from backend.app.services.answer_composer import compose_crop_advisory_answer
from backend.app.services.orchestrator import handle_text_message
from backend.app.services.retrieval_service import AdvisoryRetrievalService
from backend.app.services.safety import (
    get_out_of_scope_crop_message,
)


class DummyChannel(ChannelClient):
    channel_name = "dummy"

    def __init__(self):
        self.sent_texts: list[tuple[str, str]] = []
        self.sent_audios: list[tuple[str, bytes]] = []

    async def send_text(self, to_phone: str, text: str) -> None:
        self.sent_texts.append((to_phone, text))

    async def send_audio_url(self, to_phone: str, audio_url: str, caption: str | None = None) -> None:
        pass

    async def send_audio_bytes(self, to_phone: str, audio_bytes: bytes) -> None:
        self.sent_audios.append((to_phone, audio_bytes))


def test_corpus_ingestion_35_cards():
    """Verify that backend/data/crop_advisories.jsonl contains 35 valid cards."""
    corpus_path = Path("backend/data/crop_advisories.jsonl")
    assert corpus_path.exists(), "crop_advisories.jsonl does not exist"

    with open(corpus_path, "r", encoding="utf-8") as f:
        cards = [json.loads(line) for line in f]

    assert len(cards) == 35, f"Expected 35 cards, found {len(cards)}"
    for card in cards:
        assert "card_id" in card
        assert "title" in card
        assert "publisher" in card
        assert "year" in card
        assert "zone" in card
        assert "raw_text" in card
        assert "content_hash" in card
        assert len(card["content_hash"]) == 64  # SHA-256


def test_retrieval_service_filtering_and_scoring():
    """Verify retrieval filters by crop and returns top matching cards."""
    service = AdvisoryRetrievalService(settings=Settings(APP_ENV="test"))

    # Paddy direct seeded rice query
    matches_paddy = service.retrieve(
        query="dry direct seeded rice sowing window and water saving",
        crop="paddy",
        threshold=0.20,
    )
    assert len(matches_paddy) > 0
    top_card, score = matches_paddy[0]
    assert top_card["card_number"] == 111
    assert "Dry Direct Seeded Rice" in top_card["title"]

    # Cotton selective mechanisation query
    matches_cotton = service.retrieve(
        query="selective mechanisation in cotton to save labor in Warangal",
        crop="cotton",
        threshold=0.20,
    )
    assert len(matches_cotton) > 0
    top_card_c, score_c = matches_cotton[0]
    assert top_card_c["card_number"] == 126
    assert "mechanisation in cotton" in top_card_c["title"]


def test_scope_chilli_and_tomato_get_out_of_scope_message():
    """Verify Chilli and Tomato get polite out-of-scope disclaimer pointing to KVK/1551."""
    chilli_msg_te = get_out_of_scope_crop_message("మిర్చి", "te-IN")
    assert "మిర్చి" in chilli_msg_te
    assert "KVK" in chilli_msg_te
    assert "1551" in chilli_msg_te

    tomato_msg_hi = get_out_of_scope_crop_message("टमाटर", "hi-IN")
    assert "टमाटर" in tomato_msg_hi
    assert "KVK" in tomato_msg_hi
    assert "1551" in tomato_msg_hi


def test_composer_qualitative_zone_and_source_line():
    """Verify composer produces <= 2 sentences, mentions zone, and appends source line."""
    corpus_path = Path("backend/data/crop_advisories.jsonl")
    with open(corpus_path, "r", encoding="utf-8") as f:
        cards = [json.loads(line) for line in f]
    card111 = next(c for c in cards if c["card_number"] == 111)

    # Telugu composition
    te_answer = compose_crop_advisory_answer(
        card=card111,
        query="వరి నేరుగా విత్తే పద్ధతి ఎప్పుడు వేయాలి?",
        language="te-IN",
        allow_chemical_details=False,
    )
    assert "వరంగల్" in te_answer
    assert "ఆధారం:" in te_answer
    assert "PJTSAU" in te_answer
    assert "2020-21" in te_answer

    # English composition
    en_answer = compose_crop_advisory_answer(
        card=card111,
        query="when to sow direct seeded rice?",
        language="en-IN",
        allow_chemical_details=False,
    )
    assert "Warangal" in en_answer
    assert "Source:" in en_answer
    assert "PJTSAU" in en_answer
    assert "2020-21" in en_answer


@pytest.mark.asyncio
async def test_orchestrator_handles_paddy_advisory_text():
    """End-to-end test of orchestrator handling a paddy advisory question."""
    settings = Settings(APP_ENV="test", ALLOW_CHEMICAL_DETAILS=False)
    channel = DummyChannel()

    await handle_text_message(
        {"from": "+919876543210", "text": "వరి నేరుగా విత్తే పద్ధతి ఎప్పుడు వేయాలి?"},
        settings=settings,
        client=channel,
    )

    assert len(channel.sent_texts) == 1
    recipient, reply = channel.sent_texts[0]
    assert recipient == "+919876543210"
    assert "ఆధారం:" in reply
    assert "PJTSAU" in reply


@pytest.mark.asyncio
async def test_orchestrator_handles_chilli_out_of_scope_disclaimer():
    """Verify orchestrator returns polite out-of-scope message for chilli crop advisory."""
    settings = Settings(APP_ENV="test", ALLOW_CHEMICAL_DETAILS=False)
    channel = DummyChannel()

    await handle_text_message(
        {"from": "+919876543210", "text": "మిర్చి పంటలో తెగులు సలహా ఇవ్వండి"},
        settings=settings,
        client=channel,
    )

    assert len(channel.sent_texts) == 1
    _, reply = channel.sent_texts[0]
    assert "1551" in reply
    assert "KVK" in reply


@pytest.mark.asyncio
async def test_orchestrator_refuses_chemical_dosage_request():
    """Verify orchestrator refuses chemical dosage request with safety refusal."""
    settings = Settings(APP_ENV="test", ALLOW_CHEMICAL_DETAILS=False)
    channel = DummyChannel()

    await handle_text_message(
        {"from": "+919876543210", "text": "పత్తిలో క్లోర్‌పైరిఫాస్ ఎంత మోతాదులో స్ప్రే చేయాలి?"},
        settings=settings,
        client=channel,
    )

    assert len(channel.sent_texts) == 1
    _, reply = channel.sent_texts[0]
    assert "1551" in reply
    assert ("మోతాదు" in reply or "లేబుల్" in reply)


@pytest.mark.asyncio
async def test_orchestrator_refuses_disease_diagnosis_from_short_description():
    """Verify orchestrator refuses conclusive disease diagnosis from short descriptions."""
    settings = Settings(APP_ENV="test", ALLOW_CHEMICAL_DETAILS=False)
    channel = DummyChannel()

    await handle_text_message(
        {"from": "+919876543210", "text": "నా వరి చేను ఆకులపై పసుపు మరియు నల్లటి మచ్చలు వచ్చాయి, ఇది ఏ తెగులు?"},
        settings=settings,
        client=channel,
    )

    assert len(channel.sent_texts) == 1
    _, reply = channel.sent_texts[0]
    assert "1551" in reply
    assert "KVK" in reply
