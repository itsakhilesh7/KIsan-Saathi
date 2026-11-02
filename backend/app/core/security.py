"""Security, signature verification, and payload validation helpers."""

import hashlib
import hmac
import logging

log = logging.getLogger("security")

ALLOWED_AUDIO_MIMES = {
    "audio/ogg",
    "audio/ogg; codecs=opus",
    "audio/opus",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/aac",
    "audio/amr",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
}


def constant_time_compare(val1: str, val2: str) -> bool:
    """Timing-attack safe string comparison."""
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str,
    is_production: bool = False,
) -> bool:
    """Verifies the X-Hub-Signature-256 header sent by Meta WhatsApp webhook.

    Rules enforced:
    - In production (APP_ENV=production): Must refuse operation if app_secret is unset.
    - In development: Logs a warning if app_secret is unset and allows request.
    - Constant-time HMAC-SHA256 comparison when secret is provided.
    """
    if not app_secret:
        if is_production:
            log.critical("SECURITY VIOLATION: Webhook received in production without META_APP_SECRET!")
            raise RuntimeError("Cannot verify webhook in production: META_APP_SECRET is required.")
        log.warning("META_APP_SECRET not set: skipping signature check (DEVELOPMENT ONLY!)")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    received_signature = signature_header.removeprefix("sha256=")
    return constant_time_compare(expected_signature, received_signature)


def validate_media_type(mime_type: str | None) -> bool:
    """Checks if incoming media MIME type is in allowlisted audio formats."""
    if not mime_type:
        return False
    clean_mime = mime_type.lower().split(";")[0].strip()
    return clean_mime in {m.split(";")[0].strip() for m in ALLOWED_AUDIO_MIMES}

