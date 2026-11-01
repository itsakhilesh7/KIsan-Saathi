"""Kisan Saathi FastAPI application entrypoint.

Layers:
- Request-ID tracing middleware
- Structured JSON logging
- Webhook routes (WhatsApp)
- REST API routes (/api/health, /api/voice)
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routes.health import router as health_router
from .api.routes.voice import router as voice_router
from .channels.whatsapp.webhook import router as whatsapp_router
from .core.config import get_settings
from .core.logging import set_request_id, setup_logging

log = logging.getLogger("main")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID for every inbound HTTP request."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup checks and teardown."""
    setup_logging()
    settings = get_settings()
    log.info(
        "Kisan Saathi service starting up",
        extra={
            "app_env": settings.APP_ENV,
            "llm_mode": settings.llm_mode,
            "stt_model": settings.STT_MODEL,
            "tts_model": settings.TTS_MODEL,
        },
    )
    yield
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
app.include_router(voice_router)
