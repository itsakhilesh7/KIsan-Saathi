"""Persistent SQLite cache for Agmarknet mandi daily price evidence."""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from ...schemas.evidence import Evidence

log = logging.getLogger("integrations.data_gov.mandi_cache")


class MandiCache:
    """Thread-safe SQLite cache for storing and retrieving mandi price evidence."""

    def __init__(self, db_path: str = "data/mandi_cache.sqlite3") -> None:
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
                CREATE TABLE IF NOT EXISTS mandi_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT NOT NULL,
                    district TEXT NOT NULL,
                    market TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    variety TEXT,
                    grade TEXT,
                    arrival_date TEXT,
                    modal_price REAL,
                    min_price REAL,
                    max_price REAL,
                    retrieved_at TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    UNIQUE(state, district, market, commodity, variety, grade, arrival_date)
                    ON CONFLICT REPLACE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mandi_cache_query ON mandi_cache (state, district, commodity)"
            )

    def save_evidence(self, evidence_list: list[Evidence]) -> None:
        """Saves a batch of mandi Evidence objects to the cache."""
        if not evidence_list:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        records_to_insert = []

        for ev in evidence_list:
            data = ev.data or {}
            state = data.get("state") or "Unknown"
            district = data.get("district") or "Unknown"
            market = data.get("market") or "Unknown"
            commodity = data.get("commodity") or "Unknown"
            variety = data.get("variety")
            grade = data.get("grade")
            arrival_date = data.get("arrival_date")
            modal_price = data.get("modal_price")
            min_price = data.get("min_price")
            max_price = data.get("max_price")
            ev_json = ev.model_dump_json()

            records_to_insert.append(
                (
                    state,
                    district,
                    market,
                    commodity,
                    variety,
                    grade,
                    arrival_date,
                    modal_price,
                    min_price,
                    max_price,
                    now_iso,
                    ev_json,
                )
            )

        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO mandi_cache (
                    state, district, market, commodity, variety, grade,
                    arrival_date, modal_price, min_price, max_price,
                    retrieved_at, evidence_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records_to_insert,
            )
        log.debug("Cached %d mandi evidence records", len(records_to_insert))

    def query_cached(
        self,
        state: str | None = None,
        district: str | None = None,
        commodity: str | None = None,
        market: str | None = None,
    ) -> list[Evidence]:
        """Queries cached evidence matching state, district, commodity, or market."""
        clauses = []
        params = []

        if state:
            clauses.append("LOWER(state) = LOWER(?)")
            params.append(state)
        if district:
            clauses.append("LOWER(district) = LOWER(?)")
            params.append(district)
        if commodity:
            clauses.append("LOWER(commodity) = LOWER(?)")
            params.append(commodity)
        if market:
            clauses.append("LOWER(market) = LOWER(?)")
            params.append(market)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query_sql = f"""
            SELECT evidence_json, retrieved_at FROM mandi_cache
            {where_sql}
            ORDER BY arrival_date DESC, id DESC
            LIMIT 20
        """

        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(query_sql, params)
            rows = cur.fetchall()

        results: list[Evidence] = []
        for ev_json, ret_at in rows:
            try:
                ev_data = json.loads(ev_json)
                ev = Evidence.model_validate(ev_data)
                # Annotate as cached
                ev.data["cached"] = True
                ev.data["cached_retrieved_at"] = ret_at
                results.append(ev)
            except Exception as e:
                log.warning("Failed to deserialize cached evidence: %s", e)

        return results


# Module-level singleton
_default_cache: MandiCache | None = None


def get_mandi_cache(db_path: str = "data/mandi_cache.sqlite3") -> MandiCache:
    """Gets or initializes the default MandiCache singleton."""
    global _default_cache
    if _default_cache is None:
        _default_cache = MandiCache(db_path=db_path)
    return _default_cache
