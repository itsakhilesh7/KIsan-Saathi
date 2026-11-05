"""Persistent, non-blocking event repository for request audit and observability."""

import asyncio
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

log = logging.getLogger("repositories.events")


class EventRepository:
    """Non-blocking append-only event log backed by SQLite and JSONL."""

    def __init__(self, db_path: str = "data/events.sqlite3", jsonl_path: str = "logs/events.jsonl") -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path

        self.jsonl_path = Path(jsonl_path)
        if not self.jsonl_path.is_absolute():
            self.jsonl_path = Path.cwd() / self.jsonl_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    user_hash TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    detected_language TEXT,
                    raw_detected_language TEXT,
                    timings_json TEXT,
                    model_name TEXT,
                    status TEXT NOT NULL,
                    transcript TEXT,
                    reply TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            try:
                conn.execute("ALTER TABLE events ADD COLUMN raw_detected_language TEXT")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Returns the most recent events from SQLite for inspection and testing."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def _sync_log_event(self, event_data: dict[str, Any]) -> None:
        """Appends record to SQLite and events.jsonl synchronously."""
        req_id = event_data.get("request_id", "")
        user_hash = event_data.get("user_hash", "")
        channel = event_data.get("channel", "whatsapp")
        lang = event_data.get("detected_language")
        raw_lang = event_data.get("raw_detected_language")
        timings = json.dumps(event_data.get("timings", {}))
        model = event_data.get("model_name")
        status = event_data.get("status", "ok")
        transcript = event_data.get("transcript")
        reply = event_data.get("reply")

        with self._lock:
            # 1. SQLite insert
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT INTO events (
                            request_id, user_hash, channel, detected_language,
                            raw_detected_language, timings_json, model_name, status, transcript, reply
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (req_id, user_hash, channel, lang, raw_lang, timings, model, status, transcript, reply),
                    )
                    conn.commit()
            except Exception as e:
                log.error("Failed to append event to SQLite: %s", e)

            # 2. JSONL append
            try:
                json_line = json.dumps(event_data, ensure_ascii=False)
                with open(self.jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json_line + "\n")
            except Exception as e:
                log.error("Failed to append event to JSONL: %s", e)

    async def log_event(self, event_data: dict[str, Any]) -> None:
        """Asynchronously dispatches event logging to a worker thread."""
        await asyncio.to_thread(self._sync_log_event, event_data)
