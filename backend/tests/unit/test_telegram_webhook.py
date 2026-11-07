"""Unit tests for Telegram Webhook route verification, secret token checks, and deduplication."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings, get_settings
from backend.app.main import app
from backend.app.repositories.deduplication import SQLiteDeduplicationRepository


@pytest.fixture
def client():
    return TestClient(app)


def test_telegram_webhook_route_rejects_wrong_path(client):
    """Webhook rejects request when path does not match configured TELEGRAM_WEBHOOK_PATH."""
    settings = Settings(
        TELEGRAM_WEBHOOK_PATH="correct_secret_path",
        TELEGRAM_WEBHOOK_SECRET="mock_token_123",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        response = client.post(
            "/telegram/webhook/wrong_path",
            json={"update_id": 12345},
            headers={"X-Telegram-Bot-Api-Secret-Token": "mock_token_123"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_telegram_webhook_route_rejects_invalid_secret(client):
    """Webhook rejects request when X-Telegram-Bot-Api-Secret-Token header is invalid or missing."""
    settings = Settings(
        TELEGRAM_WEBHOOK_PATH="my_random_path_123",
        TELEGRAM_WEBHOOK_SECRET="mock_token_123",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        # Missing header
        res1 = client.post(
            "/telegram/webhook/my_random_path_123",
            json={"update_id": 12345},
        )
        assert res1.status_code == 403

        # Invalid header
        res2 = client.post(
            "/telegram/webhook/my_random_path_123",
            json={"update_id": 12345},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
        )
        assert res2.status_code == 403
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_telegram_webhook_route_success(client):
    """Webhook returns 200 OK immediately and enqueues background processing."""
    settings = Settings(
        TELEGRAM_WEBHOOK_PATH="my_random_path_123",
        TELEGRAM_WEBHOOK_SECRET="mock_token_123",
    )
    payload = {
        "update_id": 999001,
        "message": {
            "message_id": 10,
            "from": {"id": 12345678, "first_name": "Ramesh"},
            "chat": {"id": 12345678, "type": "private"},
            "text": "Hello bot",
        },
    }

    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch("backend.app.channels.telegram.webhook.process_update", new_callable=AsyncMock) as mock_process:
            response = client.post(
                "/telegram/webhook/my_random_path_123",
                json=payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_token_123"},
            )
            assert response.status_code == 200
            assert response.json() == {"ok": True}
            assert mock_process.called
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_telegram_webhook_deduplication(tmp_path):
    """process_update skips duplicate updates based on update_id."""
    from backend.app.channels.telegram.poller import process_update

    db_file = tmp_path / "dedup.sqlite3"
    dedup = SQLiteDeduplicationRepository(db_path=str(db_file))
    settings = Settings()

    update = {
        "update_id": 888123,
        "message": {
            "message_id": 1,
            "from": {"id": 9999, "first_name": "Farmer"},
            "chat": {"id": 9999},
            "text": "వడ్ల ధర ఎంత?",
        },
    }

    with patch("backend.app.channels.telegram.poller.handle_incoming_message", new_callable=AsyncMock) as mock_handle:
        # First execution -> processed
        res1 = await process_update(update, settings=settings, dedup_repo=dedup)
        assert res1 is True
        assert mock_handle.call_count == 1

        # Second execution -> deduplicated
        res2 = await process_update(update, settings=settings, dedup_repo=dedup)
        assert res2 is False
        assert mock_handle.call_count == 1  # Not called again
