"""Unit tests for Item 4: AUDIO_MAX_SECONDS (60s), chunking (<= 25s), and duration rejection.

- Audio between 25s and 60s is chunked into parts <= 25s per Prisma call.
- Audio > 60s is rejected with the language-aware message.
- Fixtures for 20s, 40s, 70s generated via ffmpeg (skipped if ffmpeg is missing on PATH).
"""

import shutil
import subprocess
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.core.config import Settings
from backend.app.integrations.gnani.stt import transcribe
from backend.app.services import audio_service
from backend.app.services.orchestrator import handle_voice_message


def _create_ffmpeg_fixture(duration: int, dest_path: str) -> None:
    """Generates a synthetic sine tone WAV of exact duration using ffmpeg."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is not installed on system PATH")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=1000:duration={duration}",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        dest_path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        pytest.skip(f"ffmpeg fixture generation failed: {p.stderr}")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed on PATH")
def test_ffmpeg_fixture_20s_not_chunked(tmp_path):
    """20s audio is <= 25s, so split_wav returns single path."""
    wav_20s = str(tmp_path / "fixture_20s.wav")
    _create_ffmpeg_fixture(20, wav_20s)

    duration = audio_service.get_duration(wav_20s)
    assert 19.5 <= duration <= 20.5

    chunks = audio_service.split_wav(wav_20s, seg_seconds=25)
    assert len(chunks) == 1
    assert chunks[0] == wav_20s


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed on PATH")
def test_ffmpeg_fixture_40s_chunked_into_two_parts(tmp_path):
    """40s audio is between 25s and 60s, so split_wav chunks into parts <= 25s."""
    wav_40s = str(tmp_path / "fixture_40s.wav")
    _create_ffmpeg_fixture(40, wav_40s)

    duration = audio_service.get_duration(wav_40s)
    assert 39.5 <= duration <= 40.5

    chunks = audio_service.split_wav(wav_40s, seg_seconds=25, out_dir=str(tmp_path / "chunks_40"))
    assert len(chunks) == 2
    # Verify both chunks exist and are <= 25s
    dur0 = audio_service.get_duration(chunks[0])
    dur1 = audio_service.get_duration(chunks[1])
    assert dur0 <= 25.5
    assert dur1 <= 25.5


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed on PATH")
def test_ffmpeg_fixture_70s_exceeds_max_seconds(tmp_path):
    """70s audio exceeds AUDIO_MAX_SECONDS (60s)."""
    wav_70s = str(tmp_path / "fixture_70s.wav")
    _create_ffmpeg_fixture(70, wav_70s)

    duration = audio_service.get_duration(wav_70s)
    assert 69.5 <= duration <= 70.5
    settings = Settings(AUDIO_MAX_SECONDS=60)
    assert duration > settings.AUDIO_MAX_SECONDS


@pytest.mark.asyncio
async def test_transcribe_chunks_40s_audio_and_combines_parts():
    """Mocked test asserting transcribe splits a 40s file into 2 chunks <= 25s."""
    settings = Settings(GNANI_API_KEY="mock_key")

    with patch("backend.app.services.audio_service.get_duration", return_value=40.0), \
         patch("backend.app.services.audio_service.split_wav", return_value=["chunk_1.wav", "chunk_2.wav"]) as mock_split, \
         patch("os.path.exists", return_value=False), \
         patch("backend.app.integrations.gnani.stt.transcribe_short", new_callable=AsyncMock) as mock_short:

        mock_short.side_effect = [
            {"transcript": "part one", "detected_language_code": "te-IN"},
            {"transcript": "part two", "detected_language_code": "te-IN"},
        ]

        result = await transcribe("dummy_40s.wav", settings=settings)

        assert mock_split.called
        assert mock_short.call_count == 2
        assert result["transcript"] == "part one part two"
        assert result["chunks"] == 2
        assert result["detected_language_code"] == "te-IN"


@pytest.mark.asyncio
async def test_orchestrator_rejects_70s_voice_note_with_language_aware_message():
    """Voice notes > 60s must be rejected before STT using language-aware message."""
    settings = Settings(AUDIO_MAX_SECONDS=60, PHONE_HASH_SALT="salt_123")

    msg = {
        "from": "919876543210",
        "media_id": "media_70s",
        "mime_type": "audio/ogg",
    }

    with patch("backend.app.channels.whatsapp.client.download_media", new_callable=AsyncMock, return_value=b"DUMMY_OGG"), \
         patch("backend.app.services.audio_service.to_wav16k"), \
         patch("backend.app.services.audio_service.get_duration", return_value=70.0), \
         patch("backend.app.channels.whatsapp.client.send_text", new_callable=AsyncMock) as mock_send_text, \
         patch("backend.app.integrations.gnani.stt.transcribe", new_callable=AsyncMock) as mock_stt:

        await handle_voice_message(msg, settings)

        # STT must NOT have been called because duration exceeded 60s
        assert not mock_stt.called
        assert mock_send_text.called
        sent_phone, sent_text = mock_send_text.call_args[0][:2]
        assert sent_phone == "919876543210"
        # Since no language has been detected, it defaults to pilot primary language (te-IN)
        assert "60 సెకన్లు" in sent_text or "పరిమితి" in sent_text
