"""Persistent SQLite dialogue state repository with configurable TTL (default 10 minutes).

Supports multi-turn clarification questions (e.g. asking for market/district).
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("repositories.dialogue_state")

_DEFAULT_DB_PATH = "data/dialogue_state.sqlite3"


class DialogueStateRepository:
    """Manages short-term dialogue context per hashed user."""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dialogue_state (
                    user_hash TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at_ts REAL NOT NULL
                )
                """
            )
            conn.commit()

    def get_state(self, user_hash: str, ttl_seconds: int = 600) -> dict[str, Any] | None:
        """Retrieves active dialogue state if within TTL, else purges and returns None."""
        now = datetime.now(timezone.utc).timestamp()
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT state_json, updated_at_ts FROM dialogue_state WHERE user_hash = ?",
                    (user_hash,),
                ).fetchone()

                if not row:
                    return None

                state_json, updated_at = row
                if (now - updated_at) > ttl_seconds:
                    conn.execute("DELETE FROM dialogue_state WHERE user_hash = ?", (user_hash,))
                    conn.commit()
                    return None

                return json.loads(state_json)
        except Exception as e:
            log.warning("Failed to retrieve dialogue state for user_hash=%s: %s", user_hash, e)
            return None

    def set_state(self, user_hash: str, state_data: dict[str, Any]) -> None:
        """Stores dialogue state for the user with current timestamp."""
        now = datetime.now(timezone.utc).timestamp()
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO dialogue_state (user_hash, state_json, updated_at_ts)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_hash) DO UPDATE SET
                        state_json = excluded.state_json,
                        updated_at_ts = excluded.updated_at_ts
                    """,
                    (user_hash, json.dumps(state_data, ensure_ascii=False), now),
                )
                conn.commit()
        except Exception as e:
            log.warning("Failed to save dialogue state for user_hash=%s: %s", user_hash, e)

    def clear_state(self, user_hash: str) -> None:
        """Clears any dialogue state for user."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM dialogue_state WHERE user_hash = ?", (user_hash,))
                conn.commit()
        except Exception as e:
            log.warning("Failed to clear dialogue state for user_hash=%s: %s", user_hash, e)
