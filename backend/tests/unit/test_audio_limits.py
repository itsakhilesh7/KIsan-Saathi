"""Unit tests for audio limits (MIME validation, size limit, duration limit)."""

import pytest

from backend.app.channels.whatsapp.client import WhatsAppAPIError
from backend.app.core.config import Settings
from backend.app.core.security import validate_media_type


def test_validate_media_type_allowlist():
    """Verify validate_media_type rejects unsupported formats and accepts allowlisted audio.

    Note: m4a audio files sent from WhatsApp mobile clients report as audio/mp4,
    so audio/mp4 must be accepted while video/mp4 remains rejected.
    """
    assert validate_media_type("audio/ogg") is True
    assert validate_media_type("audio/ogg; codecs=opus") is True
    assert validate_media_type("audio/wav") is True
    assert validate_media_type("audio/mpeg") is True
    assert validate_media_type("audio/aac") is True
    assert validate_media_type("audio/amr") is True
    assert validate_media_type("audio/mp4") is True  # m4a voice notes use audio/mp4 container
    assert validate_media_type("video/mp4") is False
    assert validate_media_type("image/jpeg") is False
    assert validate_media_type(None) is False
    assert validate_media_type("") is False


@pytest.mark.asyncio
async def test_download_media_enforces_streaming_size_limit(monkeypatch):
    """Verify download_media raises WhatsAppAPIError if streaming media exceeds AUDIO_MAX_MB."""

    from backend.app.channels.whatsapp.client import download_media

    settings = Settings(AUDIO_MAX_MB=1, WHATSAPP_ACCESS_TOKEN="mock_token_123")  # 1 MB limit

    class MockStreamResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        async def aiter_bytes(self, chunk_size=8192):
            # Emit two chunks of 600 KB each -> exceeds 1 MB limit on 2nd chunk
            yield b"x" * (600 * 1024)
            yield b"y" * (600 * 1024)

    class MockAsyncClient:
        async def request(self, method, url, **kwargs):
            class MetaResp:
                status_code = 200
                def raise_for_status(self):
                    pass
                def json(self):
                    return {"url": "https://example.com/audio.ogg"}
            return MetaResp()

        def stream(self, method, url, **kwargs):
            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def _stream():
                yield MockStreamResponse()

            return _stream()

    with pytest.raises(WhatsAppAPIError, match="exceeds maximum allowed limit"):
        await download_media("media_large", settings=settings, client=MockAsyncClient())

