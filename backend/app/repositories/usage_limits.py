"""Persistent usage limits repository (SQLite-backed) for rate-limiting voice requests."""

import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("usage_limits")


def get_today_str() -> str:
    """Returns today's date in YYYY-MM-DD format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class SQLiteUsageLimitsRepository:
    """Stores and checks daily voice request counts per user and globally."""

    def __init__(self, db_path: str = "data/usage_limits.sqlite3") -> None:
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
                CREATE TABLE IF NOT EXISTS daily_voice_usage (
                    usage_date TEXT NOT NULL,
                    user_hash TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (usage_date, user_hash)
                );
                """
            )
            conn.commit()

    def get_user_count(self, user_hash: str, date_str: str | None = None) -> int:
        """Returns the number of voice requests made by user on date_str."""
        if not user_hash:
            return 0
        ds = date_str or get_today_str()
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM daily_voice_usage WHERE usage_date = ? AND user_hash = ?",
                (ds, user_hash),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_global_count(self, date_str: str | None = None) -> int:
        """Returns total voice requests across all users on date_str."""
        ds = date_str or get_today_str()
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(count) FROM daily_voice_usage WHERE usage_date = ?",
                (ds,),
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0

    def increment(self, user_hash: str, date_str: str | None = None) -> int:
        """Increments and returns new usage count for user on date_str."""
        if not user_hash:
            return 0
        ds = date_str or get_today_str()
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO daily_voice_usage (usage_date, user_hash, count)
                VALUES (?, ?, 1)
                ON CONFLICT(usage_date, user_hash) DO UPDATE SET
                    count = count + 1;
                """,
                (ds, user_hash),
            )
            conn.commit()
            cursor.execute(
                "SELECT count FROM daily_voice_usage WHERE usage_date = ? AND user_hash = ?",
                (ds, user_hash),
            )
            row = cursor.fetchone()
            return row[0] if row else 1

    def check_and_increment(
        self,
        user_hash: str,
        max_user: int,
        max_global: int,
        admin_hashes: set[str] | list[str] | None = None,
        date_str: str | None = None,
    ) -> tuple[bool, str | None]:
        """Checks limits and increments count atomically if allowed.

        Returns:
            (True, None) if request is allowed.
            (False, reason) if user or global limit reached.
        """
        if not user_hash:
            return True, None

        admin_set = set(admin_hashes) if admin_hashes else set()
        if user_hash in admin_set:
            # Admin bypass: allowed without incrementing against standard limits
            return True, None

        ds = date_str or get_today_str()
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check user count
            if max_user > 0:
                cursor.execute(
                    "SELECT count FROM daily_voice_usage WHERE usage_date = ? AND user_hash = ?",
                    (ds, user_hash),
                )
                row = cursor.fetchone()
                user_cnt = row[0] if row else 0
                if user_cnt >= max_user:
                    return False, "user_limit_exceeded"

            # Check global count
            if max_global > 0:
                cursor.execute(
                    "SELECT SUM(count) FROM daily_voice_usage WHERE usage_date = ?",
                    (ds,),
                )
                row = cursor.fetchone()
                global_cnt = row[0] if row and row[0] is not None else 0
                if global_cnt >= max_global:
                    return False, "global_limit_exceeded"

            # Increment count
            cursor.execute(
                """
                INSERT INTO daily_voice_usage (usage_date, user_hash, count)
                VALUES (?, ?, 1)
                ON CONFLICT(usage_date, user_hash) DO UPDATE SET
                    count = count + 1;
                """,
                (ds, user_hash),
            )
            conn.commit()
            return True, None
