"""Unit tests for Item 2: Per-request timeouts.

Per-request timeouts required:
- STT: 60 s
- TTS: 90 s
- LLM: 120 s
- WhatsApp media: 60 s
"""

import httpx
import pytest

from backend.app.channels.whatsapp.client import download_media, upload_audio
from backend.app.core.config import Settings
from backend.app.integrations.gnani.stt import transcribe_short
from backend.app.integrations.gnani.tts import synthesize
from backend.app.integrations.llm.openai_compatible import OpenAICompatibleLLM


class TimeoutTrackingClient:
    """Mock httpx.AsyncClient that captures the timeout passed to post/get/stream/request."""

    def __init__(self, response: httpx.Response):
        self.response = response
        self.last_timeout = None
        self.last_method = None
        self.last_url = None

    async def post(self, url, *args, **kwargs):
        self.last_method = "POST"
        self.last_url = str(url)
        self.last_timeout = kwargs.get("timeout")
        return self.response

    async def get(self, url, *args, **kwargs):
        self.last_method = "GET"
        self.last_url = str(url)
        self.last_timeout = kwargs.get("timeout")
        return self.response

    async def request(self, method, url, *args, **kwargs):
        self.last_method = method
        self.last_url = str(url)
        self.last_timeout = kwargs.get("timeout")
        return self.response

    def stream(self, method, url, *args, **kwargs):
        self.last_method = method
        self.last_url = str(url)
        self.last_timeout = kwargs.get("timeout")

        class MockStreamContext:
            def __init__(self, resp):
                self.resp = resp
            async def __aenter__(self):
                return self.resp
            async def __aexit__(self, exc_type, exc, tb):
                pass

        class MockStreamResp:
            status_code = 200
            def raise_for_status(self):
                pass
            async def aiter_bytes(self, chunk_size=16384):
                yield b"RIFF"

        return MockStreamContext(MockStreamResp())


@pytest.mark.asyncio
async def test_stt_request_timeout_is_60s(tmp_path):
    """Prisma STT requests must pass a 60s timeout."""
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 100)

    mock_resp = httpx.Response(
        200,
        json={"success": True, "transcript": "test", "detected_language_code": "te-IN"},
        request=httpx.Request("POST", "https://api.vachana.ai/stt/v3"),
    )
    client = TimeoutTrackingClient(mock_resp)
    settings = Settings(GNANI_API_KEY="test_key")

    await transcribe_short(str(wav_file), settings=settings, client=client)
    assert client.last_timeout == 60.0


@pytest.mark.asyncio
async def test_tts_request_timeout_is_90s():
    """Timbre TTS requests must pass a 90s timeout."""
    mock_resp = httpx.Response(
        200,
        content=b"RIFF" + b"\x00" * 50,
        headers={"Content-Type": "audio/wav"},
        request=httpx.Request("POST", "https://api.vachana.ai/api/v1/tts/inference"),
    )
    client = TimeoutTrackingClient(mock_resp)
    settings = Settings(GNANI_API_KEY="test_key")

    await synthesize("Namaskaram", language="te-IN", settings=settings, client=client)
    assert client.last_timeout == 90.0


@pytest.mark.asyncio
async def test_llm_request_timeout_is_120s(monkeypatch):
    """LLM completions must pass a 120s timeout."""
    mock_resp = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Answer"}}]},
        request=httpx.Request("POST", "https://example.com/chat/completions"),
    )
    client = TimeoutTrackingClient(mock_resp)
    monkeypatch.setattr("backend.app.integrations.llm.openai_compatible.get_http_client", lambda: client)

    settings = Settings(
        LLM_BASE_URL="https://example.com",
        LLM_API_KEY="secret",
        LLM_MODEL="model",
    )
    llm = OpenAICompatibleLLM(settings=settings)
    await llm.answer("test query")
    assert client.last_timeout == 120.0


@pytest.mark.asyncio
async def test_whatsapp_media_download_and_upload_timeout_is_60s():
    """WhatsApp media download and upload must pass a 60s timeout."""
    settings = Settings(
        WHATSAPP_ACCESS_TOKEN="mock_token",
        WHATSAPP_PHONE_NUMBER_ID="12345",
    )

    # 1. Download media metadata & streaming
    meta_resp = httpx.Response(
        200,
        json={"url": "https://lookaside.fbsbx.com/sample.ogg"},
        request=httpx.Request("GET", "https://graph.facebook.com/v23.0/media_1"),
    )
    client = TimeoutTrackingClient(meta_resp)
    await download_media("media_1", settings=settings, client=client)
    assert client.last_timeout == 60.0

    # 2. Upload audio
    upload_resp = httpx.Response(
        200,
        json={"id": "media_out_999"},
        request=httpx.Request("POST", "https://graph.facebook.com/v23.0/12345/media"),
    )
    client_up = TimeoutTrackingClient(upload_resp)
    await upload_audio(b"OGG_BYTES", settings=settings, client=client_up)
    assert client_up.last_timeout == 60.0
