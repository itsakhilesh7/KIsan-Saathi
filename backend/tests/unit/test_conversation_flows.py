"""Unit tests for Section C: Conversation Handling from User Screenshots.

Exact sequences tested:
1. Hi -> What all can u help me -> Tomato -> Tell me the price of cotton -> Thank you
2. Telugu chilli flow answered with 'ఎండు మిర్చి' by voice (mocked STT)
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.config import Settings
from backend.app.repositories.dialogue_state import DialogueStateRepository
from backend.app.repositories.events import EventRepository
from backend.app.repositories.user_preferences import SQLiteUserPreferencesRepository
from backend.app.schemas.evidence import Evidence, SourceType
from backend.app.services.orchestrator import (
    handle_text_message,
    handle_voice_message,
    set_dialogue_repo,
    set_event_repo,
    set_user_pref_repo,
)


@pytest.fixture
def test_repos(tmp_path):
    dialogue_db = str(tmp_path / "dialogue.sqlite3")
    user_pref_db = str(tmp_path / "user_pref.sqlite3")
    event_db = str(tmp_path / "events.sqlite3")

    d_repo = DialogueStateRepository(db_path=dialogue_db)
    u_repo = SQLiteUserPreferencesRepository(db_path=user_pref_db)
    e_repo = EventRepository(db_path=event_db)

    set_dialogue_repo(d_repo)
    set_user_pref_repo(u_repo)
    set_event_repo(e_repo)

    yield d_repo, u_repo, e_repo

    set_dialogue_repo(None)
    set_user_pref_repo(None)
    set_event_repo(None)


@pytest.mark.asyncio
async def test_screenshot_sequence_one_english(test_repos):
    """Sequence: Hi -> What all can u help me -> Tomato -> Tell me the price of cotton -> Thank you."""
    d_repo, u_repo, e_repo = test_repos

    settings = Settings(
        PHONE_HASH_SALT="salt_conv",
        PILOT_PRIMARY_LANGUAGE="en-IN",
        MANDI_PRICE_UNIT="per quintal",
    )

    mock_channel = AsyncMock()
    mock_channel.channel_name = "test_whatsapp"
    mock_channel.send_text = AsyncMock()

    phone = "919988776655"

    def make_ev(comm: str, mkt: str, modal: float, fallback: bool = False) -> list[Evidence]:
        return [
            Evidence(
                evidence_id=f"mandi_{comm.lower()}_{mkt.lower()}",
                source_type=SourceType.MANDI_RECORD,
                source_name="Agmarknet",
                source_url="https://api.data.gov.in/test",
                publisher="DMI",
                observation_or_publication_date="2026-11-05",
                location=f"{mkt}, Warangal, Telangana",
                data={
                    "state": "Telangana",
                    "district": "Warangal" if not fallback else "Khammam",
                    "market": mkt,
                    "commodity": comm,
                    "variety": "Common",
                    "grade": "FAQ",
                    "arrival_date": "2026-11-05",
                    "modal_price": modal,
                    "min_price": modal - 200,
                    "max_price": modal + 200,
                    "is_state_fallback": fallback,
                },
                limitations=[],
            )
        ]

    # --- Turn 1: Hi ---
    await handle_text_message({"from": phone, "text": "Hi"}, settings, client=mock_channel)
    assert mock_channel.send_text.called
    turn1_reply = mock_channel.send_text.call_args[0][1]
    assert "Kisan Saathi" in turn1_reply
    assert "Which crop" in turn1_reply or "mandi" in turn1_reply

    # Verify pending dialogue state is set
    state1 = d_repo.get_state(u_repo.get_language(phone) or "salt_conv")
    # State key is hashed phone:
    from backend.app.core.logging import hash_phone
    p_hash = hash_phone(phone, settings.PHONE_HASH_SALT)
    state1 = d_repo.get_state(p_hash)
    assert state1 is not None
    assert state1.get("pending_slot") == "commodity"

    # --- Turn 2: What all can u help me ---
    mock_channel.send_text.reset_mock()
    await handle_text_message({"from": phone, "text": "What all can u help me"}, settings, client=mock_channel)
    assert mock_channel.send_text.called
    turn2_reply = mock_channel.send_text.call_args[0][1]
    # Must list mandi prices AND weather, state crop advice coming soon
    assert "mandi" in turn2_reply.lower()
    assert "weather" in turn2_reply.lower()
    assert "crop advisory" in turn2_reply.lower() or "coming soon" in turn2_reply.lower()

    # --- Turn 3: Tomato ---
    mock_channel.send_text.reset_mock()
    with patch("backend.app.services.orchestrator.fetch_mandi_prices", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = make_ev("Tomato", "Warangal", 2500.0)
        await handle_text_message({"from": phone, "text": "Tomato"}, settings, client=mock_channel)

        assert mock_channel.send_text.called
        turn3_reply = mock_channel.send_text.call_args[0][1]
        # Must resolve to Warangal Tomato and include the assumed district notice
        assert "Warangal" in turn3_reply
        assert "Showing Warangal" in turn3_reply or "tell me another district" in turn3_reply
        assert "2500" in turn3_reply
        assert "per quintal" in turn3_reply

    # --- Turn 4: Tell me the price of cotton ---
    mock_channel.send_text.reset_mock()
    with patch("backend.app.services.orchestrator.fetch_mandi_prices", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = make_ev("Cotton", "Warangal", 7200.0, fallback=True)
        await handle_text_message({"from": phone, "text": "Tell me the price of cotton"}, settings, client=mock_channel)

        assert mock_channel.send_text.called
        turn4_reply = mock_channel.send_text.call_args[0][1]
        assert "7200" in turn4_reply
        assert "Cotton" in turn4_reply or "cotton" in turn4_reply.lower()

    # --- Turn 5: Thank you ---
    mock_channel.send_text.reset_mock()
    await handle_text_message({"from": phone, "text": "Thank you"}, settings, client=mock_channel)
    assert mock_channel.send_text.called
    turn5_reply = mock_channel.send_text.call_args[0][1]
    # Short friendly reply, NOT the full menu!
    assert "welcome" in turn5_reply.lower()
    assert len(turn5_reply.split(".")) <= 3

    # Verify dialogue state is cleared
    state5 = d_repo.get_state(p_hash)
    assert state5 is None


@pytest.mark.asyncio
async def test_screenshot_sequence_two_telugu_voice_chilli_disambiguation(test_repos):
    """Telugu chilli flow: 'మిర్చి ధర ఎంత?' -> clarification -> answered with 'ఎండు మిర్చి' by voice."""
    d_repo, u_repo, e_repo = test_repos

    settings = Settings(
        PHONE_HASH_SALT="salt_tel",
        PILOT_PRIMARY_LANGUAGE="te-IN",
        MANDI_PRICE_UNIT="per quintal",
    )

    mock_channel = AsyncMock()
    mock_channel.channel_name = "test_whatsapp"
    mock_channel.send_text = AsyncMock()
    mock_channel.send_audio_bytes = AsyncMock()
    mock_channel.download_media = AsyncMock(return_value=b"DUMMY_OGG_AUDIO")

    phone = "919123456789"
    from backend.app.core.logging import hash_phone
    p_hash = hash_phone(phone, settings.PHONE_HASH_SALT)

    # --- Turn 1: Text message 'మిర్చి ధర ఎంత?' (Ambiguous chilli) ---
    await handle_text_message({"from": phone, "text": "మిర్చి ధర ఎంత?"}, settings, client=mock_channel)
    assert mock_channel.send_text.called
    turn1_reply = mock_channel.send_text.call_args[0][1]
    # Disambiguation question asking Green vs Dry chilli
    assert "పచ్చి మిర్చి" in turn1_reply
    assert "ఎండు మిర్చి" in turn1_reply

    state1 = d_repo.get_state(p_hash)
    assert state1 is not None
    assert state1.get("clarification_type") == "chilli_type"

    # --- Turn 2: Voice note answering 'ఎండు మిర్చి' ---
    mock_channel.send_text.reset_mock()

    voice_msg = {
        "from": phone,
        "type": "audio",
        "media_id": "media_voice_endu_mirchi",
        "mime_type": "audio/ogg",
    }

    stt_mock_result = {
        "transcript": "ఎండు మిర్చి",
        "detected_language_code": "te-IN",
    }

    def make_dry_chilli_ev():
        return [
            Evidence(
                evidence_id="mandi_dry_chilli_1",
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
                    "commodity": "Dry Chillies",
                    "variety": "Other",
                    "grade": "FAQ",
                    "arrival_date": "2026-11-05",
                    "modal_price": 18500.0,
                    "min_price": 17000.0,
                    "max_price": 20000.0,
                    "is_state_fallback": True,
                },
                limitations=[],
            )
        ]

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=3.5), \
         patch("backend.app.services.audio_service.wav_to_ogg_opus", side_effect=lambda src, dst: open(dst, "wb").write(b"MOCK_OGG")), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock, return_value=stt_mock_result), \
         patch("backend.app.integrations.gnani.tts.synthesize", new_callable=AsyncMock, return_value=b"RIFF_WAV_BYTES"), \
         patch("backend.app.services.orchestrator.fetch_mandi_prices", new_callable=AsyncMock, return_value=make_dry_chilli_ev()):


        await handle_voice_message(voice_msg, settings, client=mock_channel)

        assert mock_channel.send_audio_bytes.called
        assert mock_channel.send_text.called
        text_copy = mock_channel.send_text.call_args[0][1]

        # Must cite 18500, mention Dry Chillies/ఎండు మిర్చి, and state fallback info
        assert "18500" in text_copy
        assert "ఎండు మిర్చి" in text_copy or "Dry Chillies" in text_copy

        # Dialogue state must be cleared after resolution
        state2 = d_repo.get_state(p_hash)
        assert state2 is None
