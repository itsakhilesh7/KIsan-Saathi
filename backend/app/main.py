"""Kisan Saathi FastAPI application entrypoint.

Layers:
- Request-ID tracing middleware
- Structured JSON logging
- Webhook routes (WhatsApp)
- REST API routes (/api/health, /api/voice)
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routes.health import router as health_router
from .api.routes.voice import router as voice_router
from .channels.telegram.webhook import router as telegram_router
from .channels.whatsapp.webhook import router as whatsapp_router
from .core.config import Settings, get_settings
from .core.http_client import close_http_client, get_http_client
from .core.logging import set_request_id, setup_logging

log = logging.getLogger("main")


def validate_production_settings(settings: Settings) -> None:
    """Fails fast if critical production secrets are missing or use default values."""
    if not settings.is_production:
        return

    if not settings.META_APP_SECRET.strip():
        raise RuntimeError("Production startup failed: META_APP_SECRET is required.")

    if settings.PHONE_HASH_SALT.strip() in ("", "change_me"):
        raise RuntimeError("Production startup failed: PHONE_HASH_SALT must be changed from default.")

    if settings.WHATSAPP_VERIFY_TOKEN.strip() in ("", "change_me_random_string"):
        raise RuntimeError("Production startup failed: WHATSAPP_VERIFY_TOKEN must be changed from default.")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID for every inbound HTTP request."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


async def _warmup_mandi_cache(settings: Settings) -> None:
    """Warms the mandi cache asynchronously in the background at startup without blocking."""
    if not settings.DATA_GOV_API_KEY.strip():
        return
    try:
        from .integrations.data_gov.mandi import fetch_mandi_prices

        pilot_data = settings.load_pilot_config()
        district = pilot_data.get("primary", {}).get("district", "Warangal")
        state = pilot_data.get("primary", {}).get("state", "Telangana")
        await fetch_mandi_prices(state=state, district=district, settings=settings)
        log.info("Background mandi cache warmup completed.")
    except Exception as e:
        log.warning("Background mandi cache warmup failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup checks and teardown."""
    setup_logging()
    settings = get_settings()
    validate_production_settings(settings)

    # Initialize shared outbound HTTP client pool
    get_http_client()

    log.info(
        "Kisan Saathi service starting up",
        extra={
            "app_env": settings.APP_ENV,
            "llm_mode": settings.llm_mode,
            "stt_model": settings.STT_MODEL,
            "tts_model": settings.TTS_MODEL,
        },
    )

    # Warm mandi cache asynchronously without blocking startup
    asyncio.create_task(_warmup_mandi_cache(settings))

    yield
    await close_http_client()
    log.info("Kisan Saathi service shutting down")


app = FastAPI(
    title="Kisan Saathi",
    description="WhatsApp-first voice assistant for Indian farmers",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

# Request-ID tracking middleware
app.add_middleware(RequestIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(health_router)
app.include_router(whatsapp_router)
app.include_router(telegram_router)
app.include_router(voice_router)
