"""Unit tests for production startup safeguards in application lifespan."""

import pytest

from backend.app.core.config import Settings
from backend.app.main import validate_production_settings


def test_production_fails_when_meta_secret_empty():
    """Fail fast on startup in production when META_APP_SECRET is empty."""
    s = Settings(
        APP_ENV="production",
        META_APP_SECRET="",
        PHONE_HASH_SALT="secure_salt_value_123",
        WHATSAPP_VERIFY_TOKEN="secure_token_value_456",
    )
    with pytest.raises(RuntimeError, match="META_APP_SECRET is required"):
        validate_production_settings(s)


def test_production_fails_when_phone_salt_default():
    """Fail fast on startup in production when PHONE_HASH_SALT is the default."""
    s = Settings(
        APP_ENV="production",
        META_APP_SECRET="prod_secret_123",
        PHONE_HASH_SALT="change_me",
        WHATSAPP_VERIFY_TOKEN="secure_token_value_456",
    )
    with pytest.raises(RuntimeError, match="PHONE_HASH_SALT must be changed from default"):
        validate_production_settings(s)


def test_production_fails_when_verify_token_default():
    """Fail fast on startup in production when WHATSAPP_VERIFY_TOKEN is the default."""
    s = Settings(
        APP_ENV="production",
        META_APP_SECRET="prod_secret_123",
        PHONE_HASH_SALT="secure_salt_value_123",
        WHATSAPP_VERIFY_TOKEN="change_me_random_string",
    )
    with pytest.raises(RuntimeError, match="WHATSAPP_VERIFY_TOKEN must be changed from default"):
        validate_production_settings(s)


def test_production_passes_when_all_configured():
    """Startup check passes when all secrets are properly configured in production."""
    s = Settings(
        APP_ENV="production",
        META_APP_SECRET="prod_secret_123",
        PHONE_HASH_SALT="secure_salt_value_123",
        WHATSAPP_VERIFY_TOKEN="secure_token_value_456",
    )
    # Should not raise
    validate_production_settings(s)
