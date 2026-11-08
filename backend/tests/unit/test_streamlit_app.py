"""Unit tests for frontend_streamlit integration and StreamlitChannelClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.channels.base import ChannelClient
from backend.app.core.config import Settings
from backend.app.repositories.usage_limits import SQLiteUsageLimitsRepository
from backend.app.services.orchestrator import (
    handle_text_message,
    handle_voice_message,
    set_usage_limits_repo,
)
from frontend_streamlit.app import StreamlitChannelClient, get_streamlit_settings


def test_streamlit_channel_client_implements_protocol():
    """Verifies that StreamlitChannelClient implements ChannelClient protocol."""
    client = StreamlitChannelClient(raw_audio_bytes=b"OGG_RAW_BYTES")
    assert isinstance(client, ChannelClient)
    assert client.channel_name == "streamlit"


@pytest.mark.asyncio
async def test_streamlit_channel_client_media_handling():
    """Verifies audio media download and reply capture."""
    raw_bytes = b"TEST_AUDIO_PAYLOAD"
    client = StreamlitChannelClient(raw_audio_bytes=raw_bytes)

    # 1. Download media returns original bytes
    downloaded = await client.download_media("streamlit_mic_123")
    assert downloaded == raw_bytes

    # 2. Text message capture
    await client.send_text("9876543210", "హలో కిసాన్ సాథీ")
    assert len(client.sent_texts) == 1
    assert client.sent_texts[0] == "హలో కిసాన్ సాథీ"

    # 3. Audio bytes capture
    await client.send_audio_bytes("9876543210", b"SYNTHESIZED_VOICE")
    assert client.sent_audio_bytes == b"SYNTHESIZED_VOICE"


@pytest.mark.asyncio
async def test_streamlit_text_pipeline_execution():
    """Tests end-to-end text message orchestration with StreamlitChannelClient."""
    settings = Settings(
        PHONE_HASH_SALT="test_salt_streamlit",
        ALLOW_CHEMICAL_DETAILS=False,
    )
    client = StreamlitChannelClient()
    msg = {
        "from": "9876543210",
        "text": "నమస్కారం",
        "language": "te-IN",
    }

    result = await handle_text_message(msg, settings=settings, client=client)

    assert result["status"] == "ok"
    assert result["transcript"] == "నమస్కారం"
    assert result["detected_language"] == "te-IN"
    assert "reply_text" in result
    assert result["reply_text"] != ""
    assert client.sent_texts[0] == result["reply_text"]


@pytest.mark.asyncio
async def test_streamlit_voice_pipeline_execution(tmp_path):
    """Tests end-to-end voice message orchestration with StreamlitChannelClient."""
    settings = Settings(
        AUDIO_MAX_SECONDS=60,
        PHONE_HASH_SALT="test_salt_streamlit",
        SEND_TEXT_COPY=True,
        ECHO_UNSUPPORTED=True,
    )
    test_limits = SQLiteUsageLimitsRepository(str(tmp_path / "st_limits.sqlite3"))
    set_usage_limits_repo(test_limits)

    client = StreamlitChannelClient(raw_audio_bytes=b"RAW_OGG_BYTES")
    msg = {
        "from": "9876543210",
        "media_id": "streamlit_mic_test",
        "mime_type": "audio/ogg",
        "language": "te-IN",
    }

    def _mock_wav_to_ogg(src, dst):
        with open(dst, "wb") as f:
            f.write(b"MOCK_STREAMLIT_OGG")

    with patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=5.0), \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt, \
         patch("backend.app.integrations.gnani.tts.synthesize", new_callable=AsyncMock) as mock_tts, \
         patch("backend.app.services.audio_service.wav_to_ogg_opus", side_effect=_mock_wav_to_ogg):

        mock_stt.return_value = {
            "transcript": "టమాట ధర ఎంత",
            "detected_language_code": "te-IN",
            "raw_language_code": "te-IN",
            "chunks": 1,
        }
        mock_tts.return_value = b"DUMMY_TTS_WAV"

        try:
            result = await handle_voice_message(msg, settings=settings, client=client)
        finally:
            set_usage_limits_repo(None)

        assert result["status"] == "ok"
        assert result["transcript"] == "టమాట ధర ఎంత"
        assert result["detected_language"] == "te-IN"
        assert result["audio_bytes"] == b"MOCK_STREAMLIT_OGG"
        assert client.sent_audio_bytes == b"MOCK_STREAMLIT_OGG"


def test_get_streamlit_settings_defaults():
    """Verifies that get_streamlit_settings returns valid Settings instance."""
    settings = get_streamlit_settings()
    assert isinstance(settings, Settings)
    assert hasattr(settings, "PILOT_CONFIG_PATH")
    assert "primary" in settings.load_pilot_config()
