"""Unit tests for Telegram channel client and poller (MOCKED).

Tests parsing, media download with size limits, voice/text sending,
deduplication by update_id, and end-to-end voice pipeline routing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.channels.telegram.client import TelegramChannelClient
from backend.app.channels.telegram.poller import parse_update, process_update
from backend.app.core.config import Settings
from backend.app.repositories.deduplication import InMemoryDeduplicationRepository
from backend.app.repositories.usage_limits import SQLiteUsageLimitsRepository
from backend.app.services.orchestrator import handle_voice_message, set_usage_limits_repo

# Sample Telegram Update Fixtures (MOCKED)
SAMPLE_TEXT_UPDATE = {
    "update_id": 10001,
    "message": {
        "message_id": 42,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Ramesh"},
        "chat": {"id": 987654321, "type": "private"},
        "date": 1700000000,
        "text": "వరి పంటలో తెగులు నివారణ ఎలా?",
    },
}

SAMPLE_VOICE_UPDATE = {
    "update_id": 10002,
    "message": {
        "message_id": 43,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Ramesh"},
        "chat": {"id": 987654321, "type": "private"},
        "date": 1700000005,
        "voice": {
            "file_id": "tg_voice_file_abc123",
            "file_unique_id": "uniq_voice_123",
            "duration": 8,
            "mime_type": "audio/ogg",
            "file_size": 24500,
        },
    },
}

SAMPLE_PHOTO_UPDATE = {
    "update_id": 10003,
    "message": {
        "message_id": 44,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Ramesh"},
        "chat": {"id": 987654321, "type": "private"},
        "date": 1700000010,
        "photo": [{"file_id": "photo_123"}],
    },
}


def test_telegram_parse_text_update():
    """Verify parsing a Telegram text message into internal normalized message format."""
    parsed = parse_update(SAMPLE_TEXT_UPDATE)
    assert parsed is not None
    assert parsed["update_id"] == 10001
    assert parsed["type"] == "text"
    assert parsed["from"] == "987654321"
    assert parsed["text"] == "వరి పంటలో తెగులు నివారణ ఎలా?"


def test_telegram_parse_voice_update():
    """Verify parsing a Telegram voice message into internal normalized message format."""
    parsed = parse_update(SAMPLE_VOICE_UPDATE)
    assert parsed is not None
    assert parsed["update_id"] == 10002
    assert parsed["type"] == "audio"
    assert parsed["from"] == "987654321"
    assert parsed["media_id"] == "tg_voice_file_abc123"
    assert parsed["mime_type"] == "audio/ogg"


def test_telegram_parse_unsupported_update():
    """Verify parsing a non-voice/text update marks it as unsupported."""
    parsed = parse_update(SAMPLE_PHOTO_UPDATE)
    assert parsed is not None
    assert parsed["update_id"] == 10003
    assert parsed["type"] == "unsupported"
    assert parsed["from"] == "987654321"


@pytest.mark.asyncio
async def test_telegram_client_send_text_calls_send_message():
    """MOCKED: TelegramChannelClient.send_text calls sendMessage endpoint."""
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_bot_token_12345")
    mock_http = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 99}}
    mock_http.request.return_value = mock_resp

    client = TelegramChannelClient(settings=settings, http_client=mock_http)
    res = await client.send_text("987654321", "నమస్కారం రైతు సోదరులారా")

    assert res["ok"] is True
    assert mock_http.request.called
    method, url = mock_http.request.call_args[0][:2]
    kwargs = mock_http.request.call_args[1]
    assert method == "POST"
    assert "mock_bot_token_12345/sendMessage" in url
    assert kwargs["json"]["chat_id"] == "987654321"
    assert kwargs["json"]["text"] == "నమస్కారం రైతు సోదరులారా"


@pytest.mark.asyncio
async def test_telegram_client_send_audio_bytes_calls_send_voice():
    """MOCKED: TelegramChannelClient.send_audio_bytes calls sendVoice endpoint with OGG file."""
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_bot_token_12345")
    mock_http = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 100}}
    mock_http.request.return_value = mock_resp

    client = TelegramChannelClient(settings=settings, http_client=mock_http)
    ogg_dummy = b"OggS_MOCK_OPUS_AUDIO"
    res = await client.send_audio_bytes("987654321", ogg_dummy)

    assert res["ok"] is True
    assert mock_http.request.called
    method, url = mock_http.request.call_args[0][:2]
    kwargs = mock_http.request.call_args[1]
    assert method == "POST"
    assert "mock_bot_token_12345/sendVoice" in url
    assert kwargs["data"]["chat_id"] == "987654321"
    assert "voice" in kwargs["files"]
    filename, file_data, mime = kwargs["files"]["voice"]
    assert filename == "voice.ogg"
    assert file_data == ogg_dummy
    assert mime == "audio/ogg"


@pytest.mark.asyncio
async def test_telegram_client_download_media_streams_file():
    """MOCKED: TelegramChannelClient.download_media calls getFile and downloads file stream."""
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_bot_token_12345", AUDIO_MAX_MB=15)
    mock_http = AsyncMock()

    # Step 1 response (getFile)
    get_file_resp = MagicMock()
    get_file_resp.status_code = 200
    get_file_resp.json.return_value = {
        "ok": True,
        "result": {
            "file_id": "file_123",
            "file_size": 1024,
            "file_path": "voice/file_0.oga",
        },
    }
    mock_http.request.return_value = get_file_resp

    # Step 2 streaming response
    stream_cm = MagicMock()
    stream_resp = MagicMock()
    stream_resp.raise_for_status = MagicMock()

    async def aiter_bytes_gen(chunk_size=16384):
        yield b"CHUNK_1_"
        yield b"CHUNK_2"

    stream_resp.aiter_bytes = aiter_bytes_gen
    stream_cm.__aenter__ = AsyncMock(return_value=stream_resp)
    stream_cm.__aexit__ = AsyncMock(return_value=None)
    mock_http.stream = MagicMock(return_value=stream_cm)

    client = TelegramChannelClient(settings=settings, http_client=mock_http)
    media_bytes = await client.download_media("file_123")

    assert media_bytes == b"CHUNK_1_CHUNK_2"
    assert mock_http.request.called
    assert mock_http.stream.called
    download_url = mock_http.stream.call_args[0][1]
    assert "file/botmock_bot_token_12345/voice/file_0.oga" in download_url


@pytest.mark.asyncio
async def test_telegram_poller_dedupes_updates():
    """MOCKED: Duplicate update_id is processed once and subsequent triggers are ignored."""
    dedup = InMemoryDeduplicationRepository()
    settings = Settings(TELEGRAM_BOT_TOKEN="mock_bot_token_12345")
    mock_client = AsyncMock(spec=TelegramChannelClient)
    mock_client.channel_name = "telegram"

    with patch("backend.app.channels.telegram.poller.handle_incoming_message", new_callable=AsyncMock) as mock_handle:
        # First encounter -> True (processed)
        res1 = await process_update(SAMPLE_TEXT_UPDATE, settings=settings, client=mock_client, dedup_repo=dedup)
        assert res1 is True
        assert mock_handle.call_count == 1

        # Second encounter with same update_id -> False (skipped as duplicate)
        res2 = await process_update(SAMPLE_TEXT_UPDATE, settings=settings, client=mock_client, dedup_repo=dedup)
        assert res2 is False
        assert mock_handle.call_count == 1


@pytest.mark.asyncio
async def test_telegram_voice_flow_end_to_end_mocked(tmp_path):
    """MOCKED: Full pipeline using TelegramChannelClient end to end."""
    settings = Settings(
        TELEGRAM_BOT_TOKEN="mock_bot_token_12345",
        AUDIO_MAX_SECONDS=60,
        PHONE_HASH_SALT="salt_tele_123",
        SEND_TEXT_COPY=True,
        ECHO_UNSUPPORTED=True,
    )

    mock_client = AsyncMock()
    mock_client.channel_name = "telegram"
    mock_client.download_media.return_value = b"DUMMY_OGG_BYTES"
    mock_client.send_audio_bytes.return_value = {"ok": True}
    mock_client.send_text.return_value = {"ok": True}

    msg = {
        "from": "987654321",
        "media_id": "tg_voice_file_abc123",
        "mime_type": "audio/ogg",
    }

    def _mock_wav_to_ogg(src, dst):
        with open(dst, "wb") as f:
            f.write(b"MOCK_OGG_CONTENT")

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=12.0), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt, \
         patch("backend.app.integrations.llm.openai_compatible.OpenAICompatibleLLM.answer", new_callable=AsyncMock) as mock_llm, \
         patch("backend.app.integrations.gnani.tts.synthesize", new_callable=AsyncMock) as mock_tts, \
         patch("backend.app.services.audio_service.wav_to_ogg_opus", side_effect=_mock_wav_to_ogg):

        mock_stt.return_value = {
            "transcript": "బ్యాంక్ లోన్ సబ్సిడీ",
            "detected_language_code": "te-IN",
            "raw_language_code": "te-IN",
            "chunks": 1,
        }
        mock_llm.return_value = ("పంటను గమనించి వేపనూనె పిచికారీ చేయండి.", "echo-model")
        mock_tts.return_value = b"DUMMY_TTS_WAV"

        test_limits = SQLiteUsageLimitsRepository(str(tmp_path / "tele_limits_1.sqlite3"))
        set_usage_limits_repo(test_limits)
        try:
            await handle_voice_message(msg, settings, client=mock_client)
        finally:
            set_usage_limits_repo(None)

        # Confirm Telegram client methods called
        assert mock_client.download_media.called
        assert mock_client.download_media.call_args[0][0] == "tg_voice_file_abc123"
        assert mock_client.send_audio_bytes.called
        assert mock_client.send_audio_bytes.call_args[0][0] == "987654321"
        assert mock_client.send_text.called
        assert mock_client.send_text.call_args[0][0] == "987654321"
        assert "వేపనూనె" in mock_client.send_text.call_args[0][1]


@pytest.mark.asyncio
async def test_telegram_voice_flow_unsupported_intent_blocked_default(tmp_path):
    """MOCKED: Unsupported intent returns fixed guidance without LLM when ECHO_UNSUPPORTED=False."""
    settings = Settings(
        TELEGRAM_BOT_TOKEN="mock_bot_token_12345",
        AUDIO_MAX_SECONDS=60,
        PHONE_HASH_SALT="salt_tele_123",
        SEND_TEXT_COPY=True,
        ECHO_UNSUPPORTED=False,
    )

    mock_client = AsyncMock()
    mock_client.channel_name = "telegram"
    mock_client.download_media.return_value = b"DUMMY_OGG_BYTES"
    mock_client.send_audio_bytes.return_value = {"ok": True}
    mock_client.send_text.return_value = {"ok": True}

    msg = {
        "from": "987654321",
        "media_id": "tg_voice_file_abc123",
        "mime_type": "audio/ogg",
    }

    def _mock_wav_to_ogg(src, dst):
        with open(dst, "wb") as f:
            f.write(b"MOCK_OGG_CONTENT")

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=12.0), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt, \
         patch("backend.app.integrations.llm.openai_compatible.OpenAICompatibleLLM.answer", new_callable=AsyncMock) as mock_llm, \
         patch("backend.app.integrations.gnani.tts.synthesize", new_callable=AsyncMock) as mock_tts, \
         patch("backend.app.services.audio_service.wav_to_ogg_opus", side_effect=_mock_wav_to_ogg):

        mock_stt.return_value = {
            "transcript": "బ్యాంక్ లోన్ సబ్సిడీ",
            "detected_language_code": "te-IN",
            "raw_language_code": "te-IN",
            "chunks": 1,
        }
        mock_tts.return_value = b"DUMMY_TTS_WAV"

        test_limits = SQLiteUsageLimitsRepository(str(tmp_path / "tele_limits_1.sqlite3"))
        set_usage_limits_repo(test_limits)
        try:
            await handle_voice_message(msg, settings, client=mock_client)
        finally:
            set_usage_limits_repo(None)

        assert not mock_llm.called
        assert mock_client.send_text.called
        # Contains the fixed Telugu guidance phrase
        assert "మండి ధరల" in mock_client.send_text.call_args[0][1]

