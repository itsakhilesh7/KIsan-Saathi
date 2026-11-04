"""Health check endpoint exposing system status and config presence flags.

CRITICAL: Config keys are exposed as BOOLEANS ONLY (True/False whether set).
Values and secrets are NEVER returned under any circumstances.
"""

from typing import Any

from fastapi import APIRouter, Depends

from ...core.config import Settings, get_settings

router = APIRouter()


@router.get("/api/health")
@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    """Returns application status, LLM mode, pilot status, and config presence booleans."""
    pilot_data = settings.load_pilot_config()
    pilot_confirmed = pilot_data.get("confirmed", False)

    # Boolean flags indicating presence of configured credentials (NEVER actual values)
    config_presence = {
        "gnani_api_key": bool(settings.GNANI_API_KEY.strip()),
        "meta_app_secret": bool(settings.META_APP_SECRET.strip()),
        "whatsapp_token": bool(settings.WHATSAPP_ACCESS_TOKEN.strip()),
        "whatsapp_phone_number_id": bool(settings.WHATSAPP_PHONE_NUMBER_ID.strip()),
        "telegram_bot_token": bool(settings.TELEGRAM_BOT_TOKEN.strip()),
        "data_gov_api_key": bool(settings.DATA_GOV_API_KEY.strip()),
        "database_url": bool(settings.DATABASE_URL.strip()),
        "llm_api_key": bool(settings.LLM_API_KEY.strip()),
        "llm_base_url": bool(settings.LLM_BASE_URL.strip()),
    }

    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "llm_mode": settings.llm_mode,
        "stt_model": settings.STT_MODEL,
        "tts_model": settings.TTS_MODEL,
        "pilot_confirmed": pilot_confirmed,
        "config_present": config_presence,
    }
