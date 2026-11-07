"""Unit tests for SQLite usage limits repository and voice cap enforcement."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.config import Settings
from backend.app.core.messages import MESSAGES
from backend.app.repositories.usage_limits import SQLiteUsageLimitsRepository
from backend.app.services.orchestrator import handle_incoming_message, set_usage_limits_repo


def test_usage_limits_repository_lifecycle(tmp_path):
    """Test user count, global count, limits and admin bypass in SQLiteUsageLimitsRepository."""
    db_file = tmp_path / "usage_limits.sqlite3"
    repo = SQLiteUsageLimitsRepository(db_path=str(db_file))

    date_str = "2026-11-07"
    user_a = "user_hash_aaa"
    user_b = "user_hash_bbb"

    assert repo.get_user_count(user_a, date_str) == 0
    assert repo.get_global_count(date_str) == 0

    # User A 1st call
    ok, reason = repo.check_and_increment(user_a, max_user=2, max_global=3, date_str=date_str)
    assert ok is True
    assert reason is None
    assert repo.get_user_count(user_a, date_str) == 1
    assert repo.get_global_count(date_str) == 1

    # User A 2nd call
    ok, reason = repo.check_and_increment(user_a, max_user=2, max_global=3, date_str=date_str)
    assert ok is True
    assert repo.get_user_count(user_a, date_str) == 2
    assert repo.get_global_count(date_str) == 2

    # User A 3rd call (exceeds user limit of 2)
    ok, reason = repo.check_and_increment(user_a, max_user=2, max_global=3, date_str=date_str)
    assert ok is False
    assert reason == "user_limit_exceeded"
    assert repo.get_user_count(user_a, date_str) == 2  # unchanged

    # User B 1st call (user limit not reached, global limit becomes 3)
    ok, reason = repo.check_and_increment(user_b, max_user=2, max_global=3, date_str=date_str)
    assert ok is True
    assert repo.get_user_count(user_b, date_str) == 1
    assert repo.get_global_count(date_str) == 3

    # User B 2nd call (exceeds global limit of 3)
    ok, reason = repo.check_and_increment(user_b, max_user=2, max_global=3, date_str=date_str)
    assert ok is False
    assert reason == "global_limit_exceeded"

    # Admin bypass for User A
    ok, reason = repo.check_and_increment(
        user_a,
        max_user=2,
        max_global=3,
        admin_hashes={user_a},
        date_str=date_str,
    )
    assert ok is True
    assert reason is None

    # Next day rollover
    next_day = "2026-11-08"
    assert repo.get_user_count(user_a, next_day) == 0
    ok, reason = repo.check_and_increment(user_a, max_user=2, max_global=3, date_str=next_day)
    assert ok is True


@pytest.mark.asyncio
async def test_orchestrator_rejects_voice_when_limit_reached(tmp_path):
    """Orchestrator rejects voice request with localized message when limit reached."""
    db_file = tmp_path / "usage_limits_orch.sqlite3"
    test_repo = SQLiteUsageLimitsRepository(db_path=str(db_file))
    set_usage_limits_repo(test_repo)

    settings = Settings(
        DAILY_USER_VOICE_LIMIT=1,
        DAILY_GLOBAL_VOICE_LIMIT=10,
        PUBLIC_VOICE_MAX_SECONDS=30,
    )

    phone = "919999999999"
    # Seed usage so limit is reached
    from backend.app.core.logging import hash_phone
    phone_hash = hash_phone(phone, settings.PHONE_HASH_SALT)
    test_repo.increment(phone_hash)

    msg = {
        "type": "audio",
        "from": phone,
        "media_id": "med_123",
        "mime_type": "audio/ogg",
    }

    with (
        patch("backend.app.channels.whatsapp.client.download_media", new_callable=AsyncMock, return_value=b"fake_audio"),
        patch("backend.app.services.audio_service.to_wav16k", return_value=None),
        patch("backend.app.services.audio_service.get_duration", return_value=5.0),
        patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt,
        patch("backend.app.channels.whatsapp.client.send_text", new_callable=AsyncMock) as mock_send,
    ):
        await handle_incoming_message(msg, settings=settings)

        # STT must NOT have been called
        assert not mock_stt.called
        # Polite limit message sent
        assert mock_send.called
        sent_reply = mock_send.call_args[0][1]
        assert MESSAGES["voice_limit_reached"]["te-IN"] in sent_reply or "పరిమితి" in sent_reply

    set_usage_limits_repo(None)


@pytest.mark.asyncio
async def test_orchestrator_rejects_voice_longer_than_public_limit(tmp_path):
    """Voice note longer than 30s is rejected by default for public bot."""
    db_file = tmp_path / "usage_limits_dur.sqlite3"
    test_repo = SQLiteUsageLimitsRepository(db_path=str(db_file))
    set_usage_limits_repo(test_repo)

    settings = Settings(
        PUBLIC_VOICE_MAX_SECONDS=30,
        AUDIO_MAX_SECONDS=60,
    )

    phone = "919888888888"
    msg = {
        "type": "audio",
        "from": phone,
        "media_id": "med_35s",
        "mime_type": "audio/ogg",
    }

    with (
        patch("backend.app.channels.whatsapp.client.download_media", new_callable=AsyncMock, return_value=b"fake_audio"),
        patch("backend.app.services.audio_service.to_wav16k", return_value=None),
        patch("backend.app.services.audio_service.get_duration", return_value=35.0),  # > 30s
        patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt,
        patch("backend.app.channels.whatsapp.client.send_text", new_callable=AsyncMock) as mock_send,
    ):
        await handle_incoming_message(msg, settings=settings)

        assert not mock_stt.called
        assert mock_send.called
        sent_reply = mock_send.call_args[0][1]
        assert MESSAGES["audio_too_long"]["te-IN"] in sent_reply or "పెద్దదిగా" in sent_reply

    set_usage_limits_repo(None)
