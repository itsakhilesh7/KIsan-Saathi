"""Unit tests for EventRepository (SQLite + JSONL)."""

import json

import pytest

from backend.app.repositories.events import EventRepository


@pytest.mark.asyncio
async def test_event_repository_records_event_safely(tmp_path):
    """Verify events are logged to SQLite and JSONL without raw PII."""
    db_file = tmp_path / "test_events.sqlite3"
    jsonl_file = tmp_path / "test_events.jsonl"

    repo = EventRepository(db_path=str(db_file), jsonl_path=str(jsonl_file))

    event_payload = {
        "request_id": "req-999",
        "user_hash": "a1b2c3d4e5f60718",
        "channel": "whatsapp",
        "detected_language": "te-IN",
        "model_name": "echo",
        "status": "ok",
        "timings": {"stt": 0.5, "total": 1.2},
        "transcript": None,  # Transcripts omitted when STORE_RAW_TRANSCRIPTS is False
        "reply": None,
    }

    await repo.log_event(event_payload)

    # 1. Verify JSONL
    assert jsonl_file.exists()
    with open(jsonl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["request_id"] == "req-999"
        assert record["user_hash"] == "a1b2c3d4e5f60718"
        assert record["transcript"] is None

    # 2. Verify SQLite table
    import sqlite3
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT request_id, user_hash, detected_language, status FROM events")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "req-999"
        assert row[1] == "a1b2c3d4e5f60718"
        assert row[2] == "te-IN"
        assert row[3] == "ok"
