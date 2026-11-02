"""Persistent user preferences repository (SQLite-backed) for language continuity."""

import logging
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger("user_preferences")


class SQLiteUserPreferencesRepository:
    """Stores and retrieves user preferences such as last seen language."""

    def __init__(self, db_path: str = "data/user_preferences.sqlite3") -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_hash TEXT PRIMARY KEY,
                    last_language TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def get_language(self, user_hash: str) -> str | None:
        """Returns the last known language for the given hashed user, or None."""
        if not user_hash:
            return None
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_language FROM user_preferences WHERE user_hash = ?", (user_hash,))
            row = cursor.fetchone()
            return row[0] if row else None

    def set_language(self, user_hash: str, language: str) -> None:
        """Upserts the last known language for the given hashed user."""
        if not user_hash or not language:
            return
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_preferences (user_hash, last_language, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_hash) DO UPDATE SET
                    last_language = excluded.last_language,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_hash, language),
            )
            conn.commit()
