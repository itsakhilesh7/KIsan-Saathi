"""WhatsApp webhook endpoints (verification handshake and inbound event intake)."""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from ...core.config import Settings, get_settings
from ...repositories.deduplication import DeduplicationRepository, SQLiteDeduplicationRepository
from . import parser, signature

log = logging.getLogger("whatsapp.webhook")

router = APIRouter()

# Default repository for deduplication
_dedup_repo: DeduplicationRepository = SQLiteDeduplicationRepository()


def get_dedup_repo() -> DeduplicationRepository:
    """Dependency provider for deduplication repository."""
    return _dedup_repo


def set_dedup_repo(repo: DeduplicationRepository) -> None:
    """Allows test fixtures to inject an in-memory repository."""
    global _dedup_repo
    _dedup_repo = repo


@router.get("/webhook")
async def verify_webhook(
    mode: str | None = Query(None, alias="hub.mode"),
    token: str | None = Query(None, alias="hub.verify_token"),
    challenge: str | None = Query(None, alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
) -> PlainTextResponse:
    """Meta webhook verification handshake."""
    if mode == "subscribe" and token and token == settings.WHATSAPP_VERIFY_TOKEN:
        log.info("Webhook verification handshake successful.")
        return PlainTextResponse(challenge or "")
    log.warning("Webhook verification handshake failed: invalid token or mode.")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    dedup: DeduplicationRepository = Depends(get_dedup_repo),
) -> dict[str, str]:
    """Inbound webhook event intake. Validates signature, dedupes, and queues background processing."""
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")

    try:
        valid_sig = signature.verify_signature(raw_body, sig_header, settings)
    except RuntimeError as e:
        log.critical("Webhook rejected due to production security check: %s", e)
        raise HTTPException(status_code=500, detail="Server misconfiguration: security key required.")

    if not valid_sig:
        log.warning("Webhook rejected: Invalid signature.")
        raise HTTPException(status_code=403, detail="Bad signature")

    try:
        payload = json.loads(raw_body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    from ...services.orchestrator import handle_incoming_message

    messages = parser.extract_messages(payload)
    for msg in messages:
        msg_id = msg.get("id")
        if dedup.is_duplicate(msg_id):
            log.info("Skipping duplicate WhatsApp message id=%s", msg_id)
            continue

        background.add_task(handle_incoming_message, msg, settings)

    return {"status": "ok"}
