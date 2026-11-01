"""Unit tests for /api/health endpoint (MOCKED)."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns status, config booleans, and no secret values."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()

    assert data["status"] == "healthy"
    assert "llm_mode" in data
    assert "pilot_confirmed" in data
    assert "config_present" in data

    config_presence = data["config_present"]
    # All values must be booleans
    for key, val in config_presence.items():
        assert isinstance(val, bool), f"Key {key} must be boolean, got {type(val)}"

    # Confirm legacy /health path works
    r_legacy = client.get("/health")
    assert r_legacy.status_code == 200
    assert r_legacy.json() == data
