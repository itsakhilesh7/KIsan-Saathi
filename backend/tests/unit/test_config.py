"""Unit tests for typed configuration, pilot loading, and production safeguards (MOCKED)."""

import pytest

from backend.app.core.config import Settings, get_settings
from backend.app.core.security import verify_webhook_signature


def test_settings_defaults():
    """Verify settings defaults match architecture specifications."""
    s = Settings()
    assert s.STT_MODEL == "prisma-v3.0"
    assert s.TTS_MODEL == "timbre-v2.5"
    assert s.ALLOW_CHEMICAL_DETAILS is False
    assert s.RATE_LIMIT_PER_MIN == 20
    assert s.llm_mode in ("echo", "configured")


def test_production_refuses_empty_meta_secret():
    """Verify system strictly refuses to accept webhooks in production without META_APP_SECRET."""
    with pytest.raises(RuntimeError, match="META_APP_SECRET is required"):
        verify_webhook_signature(
            raw_body=b"{}",
            signature_header="sha256=abc",
            app_secret="",
            is_production=True,
        )


def test_development_allows_empty_meta_secret():
    """Verify system allows development requests with a warning when secret is omitted."""
    res = verify_webhook_signature(
        raw_body=b"{}",
        signature_header=None,
        app_secret="",
        is_production=False,
    )
    assert res is True


def test_pilot_config_confirmed_flag():
    """Verify pilot.yaml loading and confirmed: false detection."""
    s = get_settings()
    data = s.load_pilot_config()
    assert isinstance(data, dict)
    assert "confirmed" in data
    # In initial scaffolding, confirmed is false
    assert data["confirmed"] is False
