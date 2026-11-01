"""WhatsApp webhook signature verification."""

import logging

from ...core.config import Settings, get_settings
from ...core.security import verify_webhook_signature as _verify

log = logging.getLogger("whatsapp.signature")


def verify_signature(
    raw_body: bytes,
    header: str | None,
    settings: Settings | None = None,
) -> bool:
    """Verifies X-Hub-Signature-256 using constant-time comparison.

    Refuses execution in production if META_APP_SECRET is not configured.
    """
    cfg = settings or get_settings()
    return _verify(
        raw_body=raw_body,
        signature_header=header,
        app_secret=cfg.META_APP_SECRET,
        is_production=cfg.is_production,
    )
