import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app import config, main, whatsapp

client = TestClient(main.app)


def _payload(msg_id="wamid.1", mtype="audio"):
    msg = {"id": msg_id, "from": "919999999999", "type": mtype}
    if mtype == "audio":
        msg["audio"] = {"id": "MEDIA123", "mime_type": "audio/ogg; codecs=opus"}
    else:
        msg["text"] = {"body": "namaste"}
    return {"entry": [{"changes": [{"value": {"messages": [msg]}}]}]}


def test_verify_ok(monkeypatch):
    monkeypatch.setattr(config, "WA_VERIFY_TOKEN", "secret")
    r = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "secret", "hub.challenge": "42"})
    assert r.status_code == 200 and r.text == "42"


def test_verify_bad_token(monkeypatch):
    monkeypatch.setattr(config, "WA_VERIFY_TOKEN", "secret")
    r = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "42"})
    assert r.status_code == 403


def test_post_dispatches_once_and_dedupes(monkeypatch):
    monkeypatch.setattr(config, "META_APP_SECRET", "")
    seen = []

    async def fake_handle(msg):
        seen.append(msg)

    monkeypatch.setattr(main.pipeline, "handle_message", fake_handle)
    main._SEEN.clear()
    body = json.dumps(_payload("wamid.dup"))
    for _ in range(2):  # Meta retry
        assert client.post("/webhook", content=body).status_code == 200
    assert len(seen) == 1
    assert seen[0]["type"] == "audio" and seen[0]["media_id"] == "MEDIA123"


def test_signature_enforced(monkeypatch):
    monkeypatch.setattr(config, "META_APP_SECRET", "appsecret")
    body = json.dumps(_payload("wamid.sig")).encode()
    assert client.post("/webhook", content=body).status_code == 403
    sig = "sha256=" + hmac.new(b"appsecret", body, hashlib.sha256).hexdigest()
    monkeypatch.setattr(main.pipeline, "handle_message", _noop_handle)
    assert client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sig}).status_code == 200


async def _noop_handle(msg):
    return None


def test_extract_ignores_statuses():
    p = {"entry": [{"changes": [{"value": {"statuses": [{"id": "x", "status": "delivered"}]}}]}]}
    assert whatsapp.extract_messages(p) == []
