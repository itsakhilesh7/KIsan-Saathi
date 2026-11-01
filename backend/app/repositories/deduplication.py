"""Deduplication repository for idempotent webhook processing."""

import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path

log = logging.getLogger("deduplication")


class DeduplicationRepository(ABC):
    """Abstract interface for webhook message deduplication."""

    @abstractmethod
    def is_duplicate(self, msg_id: str | None) -> bool:
        """Returns True if msg_id has already been processed, else records it and returns False."""


class InMemoryDeduplicationRepository(DeduplicationRepository):
    """In-memory LRU deduplication for unit tests."""

    def __init__(self, max_size: int = 2000) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._max = max_size
        self._lock = threading.Lock()

    def is_duplicate(self, msg_id: str | None) -> bool:
        if not msg_id:
            return False
        with self._lock:
            if msg_id in self._seen:
                return True
            self._seen[msg_id] = None
            if len(self._seen) > self._max:
                self._seen.popitem(last=False)
            return False

    def clear(self) -> None:
        with self._lock:
            self._seen.clear()


class SQLiteDeduplicationRepository(DeduplicationRepository):
    """Persistent SQLite-backed deduplication repository surviving process restarts."""

    def __init__(self, db_path: str = "data/dedup.sqlite3") -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            # Resolve relative to backend or workspace
            self.db_path = Path.cwd() / self.db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_messages (
                    msg_id TEXT PRIMARY KEY,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def is_duplicate(self, msg_id: str | None) -> bool:
        if not msg_id:
            return False

        with self._lock, sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("INSERT INTO seen_messages (msg_id) VALUES (?)", (msg_id,))
                conn.commit()
                return False
            except sqlite3.IntegrityError:
                return True
            except Exception as e:
                log.error("Deduplication database error: %s", e)
                return False

    def clear(self) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM seen_messages")
            conn.commit()
