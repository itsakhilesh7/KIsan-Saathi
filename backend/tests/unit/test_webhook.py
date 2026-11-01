"""Unit tests for WhatsApp webhook (MOCKED).

Migrated and hardened from existing-code/tests/test_webhook.py.
All tests run with local fixtures and mocked background tasks.
"""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.channels.whatsapp.parser import extract_messages
from backend.app.channels.whatsapp.webhook import set_dedup_repo
from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.repositories.deduplication import InMemoryDeduplicationRepository
from backend.tests.fixtures.sample_payloads import make_whatsapp_payload

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Isolates settings and resets in-memory deduplication for each test."""
    repo = InMemoryDeduplicationRepository()
    set_dedup_repo(repo)
    settings = get_settings()
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "test_verify_token")
    monkeypatch.setattr(settings, "META_APP_SECRET", "")
    yield


def test_verify_ok(monkeypatch):
    """Test webhook verification challenge handshake with valid token (MOCKED)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "secret_token_123")
    r = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "secret_token_123",
            "hub.challenge": "challenge_string_42",
        },
    )
    assert r.status_code == 200
    assert r.text == "challenge_string_42"


def test_verify_bad_token(monkeypatch):
    """Test webhook verification challenge rejected with invalid token (MOCKED)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "secret_token_123")
    r = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_string_42",
        },
    )
    assert r.status_code == 403


def test_post_dispatches_once_and_dedupes(monkeypatch):
    """Test duplicate delivery is caught by deduplication repository (MOCKED)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "META_APP_SECRET", "")  # dev mode allows empty secret

    dispatched = []

    async def fake_handle(msg, cfg):
        dispatched.append(msg)

    # Patch the orchestrator background task
    import backend.app.services.orchestrator as orch
    monkeypatch.setattr(orch, "handle_incoming_message", fake_handle)

    body = json.dumps(make_whatsapp_payload(msg_id="wamid.dup_test_1", mtype="audio"))

    # First call: processes message
    r1 = client.post("/webhook", content=body)
    assert r1.status_code == 200

    # Second call (Meta retry): deduplicated
    r2 = client.post("/webhook", content=body)
    assert r2.status_code == 200

    assert len(dispatched) == 1
    assert dispatched[0]["id"] == "wamid.dup_test_1"
    assert dispatched[0]["type"] == "audio"
    assert dispatched[0]["media_id"] == "MEDIA_ID_123"


def test_signature_enforced(monkeypatch):
    """Test HMAC-SHA256 signature verification and rejection of forged payloads (MOCKED)."""
    settings = get_settings()
    secret = "test_meta_app_secret_abc"
    monkeypatch.setattr(settings, "META_APP_SECRET", secret)

    payload_dict = make_whatsapp_payload(msg_id="wamid.sig_test_1")
    raw_bytes = json.dumps(payload_dict).encode("utf-8")

    # 1. Missing signature header -> 403
    r_no_sig = client.post("/webhook", content=raw_bytes)
    assert r_no_sig.status_code == 403

    # 2. Invalid signature header -> 403
    r_bad_sig = client.post("/webhook", content=raw_bytes, headers={"X-Hub-Signature-256": "sha256=invalid"})
    assert r_bad_sig.status_code == 403

    # 3. Valid signature header -> 200
    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    async def noop_handle(msg, cfg):
        pass

    import backend.app.services.orchestrator as orch
    monkeypatch.setattr(orch, "handle_incoming_message", noop_handle)

    r_ok = client.post("/webhook", content=raw_bytes, headers={"X-Hub-Signature-256": valid_sig})
    assert r_ok.status_code == 200


def test_extract_ignores_statuses():
    """Test that message extractor filters out status updates and delivery receipts (MOCKED)."""
    status_payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.sent_1",
                                    "status": "delivered",
                                    "timestamp": "1730467200",
                                    "recipient_id": "919999999999",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    extracted = extract_messages(status_payload)
    assert extracted == []
