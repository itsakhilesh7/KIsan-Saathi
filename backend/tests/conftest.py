"""Pytest global configuration and test environment isolation fixtures."""

import pytest

import backend.app.channels.telegram.poller as tg_poller
import backend.app.channels.whatsapp.webhook as wa_webhook
import backend.app.services.orchestrator as orch
from backend.app.repositories.deduplication import InMemoryDeduplicationRepository
from backend.app.repositories.events import EventRepository
from backend.app.repositories.user_preferences import SQLiteUserPreferencesRepository


@pytest.fixture(autouse=True)
def isolate_databases_and_logs(tmp_path, monkeypatch):
    """Ensures test runs never write to ./data or ./logs by redirecting to tmp_path."""
    tmp_events = EventRepository(
        db_path=str(tmp_path / "test_events.sqlite3"),
        jsonl_path=str(tmp_path / "test_events.jsonl"),
    )
    tmp_user_pref = SQLiteUserPreferencesRepository(
        db_path=str(tmp_path / "test_user_preferences.sqlite3"),
    )
    tmp_dedup = InMemoryDeduplicationRepository()

    monkeypatch.setattr(orch, "_event_repo", tmp_events)
    monkeypatch.setattr(orch, "_user_pref_repo", tmp_user_pref)
    monkeypatch.setattr(wa_webhook, "_dedup_repo", tmp_dedup)
    monkeypatch.setattr(tg_poller, "_dedup_repo", tmp_dedup)

    yield
