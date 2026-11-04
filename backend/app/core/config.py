"""Central typed configuration for Kisan Saathi using pydantic-settings.

Every environment variable from .env.example is read here.
No direct os.getenv() calls are permitted elsewhere in application code.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("config")

# Fixed constants per specs in docs/gnani-api-notes.md and architecture.md
STT_URL: str = "https://api.vachana.ai/stt/v3"
TTS_URL: str = "https://api.vachana.ai/api/v1/tts/inference"
MAX_STT_SECONDS: int = 25  # Conservative chunk cutoff under Prisma's 30s limit

# Timbre v2.5 voices are language-specific. A mismatch returns HTTP 400.
TTS_V25_VOICES: dict[str, str] = {
    "te-IN": "Lavanya",
    "hi-IN": "Nalini",
    "en-IN": "Kaveri",
    "hi-en": "Poorvi",
}
TTS_DEFAULT_LANG: str = "hi-IN"


class Settings(BaseSettings):
    """Application settings typed and validated via Pydantic."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- App ----
    APP_ENV: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    PHONE_HASH_SALT: str = "change_me"
    ALLOW_CHEMICAL_DETAILS: bool = False
    RATE_LIMIT_PER_MIN: int = 20
    SEND_TEXT_COPY: bool = True
    # By default False per privacy rules (rules.md). Only set to True for offline consented eval debugging.
    STORE_RAW_TRANSCRIPTS: bool = False

    # ---- Pilot ----
    PILOT_CONFIG_PATH: str = "config/pilot.yaml"

    # ---- Gnani ----
    GNANI_API_KEY: str = ""
    STT_MODEL: str = "prisma-v3.0"
    STT_LANGUAGE: str = "indic-auto"
    TTS_MODEL: str = "timbre-v2.5"
    TTS_V3_VOICE: str = "Shivani"
    TTS_DEFAULT_LANG: str = TTS_DEFAULT_LANG

    # ---- LLM (OpenAI-compatible) ----
    LLM_PROVIDER: str = "openai_compatible"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gnani/gnani-evon-v3.3-30B-A3B"
    LLM_DISCLOSED_NAME: str = ""

    # ---- WhatsApp Cloud API ----
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "change_me_random_string"
    META_APP_SECRET: str = ""
    WA_API_VERSION: str = "v23.0"

    # ---- Telegram (fallback channel per D-002) ----
    TELEGRAM_BOT_TOKEN: str = ""

    # ---- data.gov.in ----
    DATA_GOV_API_KEY: str = ""
    DATA_GOV_BASE_URL: str = "https://api.data.gov.in/resource"
    MANDI_RESOURCE_ID: str = "9ef84268-d588-465a-a308-a864a43d0070"
    KCC_RESOURCE_IDS: str = ""

    # ---- Open-Meteo ----
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

    # ---- Storage / retrieval ----
    DATABASE_URL: str = ""
    VECTOR_BACKEND: str = "pgvector"
    EMBEDDING_PROVIDER: str = ""
    EMBEDDING_MODEL: str = ""
    EMBEDDING_API_KEY: str = ""

    # ---- Audio ----
    AUDIO_MAX_SECONDS: int = 60
    AUDIO_MAX_MB: int = 15
    AUDIO_RETENTION_HOURS: int = 24

    @property
    def pilot_primary_language(self) -> str:
        """Returns the primary pilot language from pilot.yaml (defaults to 'te-IN')."""
        pilot = self.load_pilot_config()
        return pilot.get("primary", {}).get("language", "te-IN")

    @property
    def is_production(self) -> bool:
        """True if running in production environment."""
        return self.APP_ENV.lower() == "production"

    @property
    def llm_mode(self) -> str:
        """Returns 'echo' if LLM_BASE_URL is empty, else 'configured'."""
        return "configured" if self.LLM_BASE_URL.strip() else "echo"

    @property
    def wa_graph(self) -> str:
        """Meta Graph API base URL with version."""
        return f"https://graph.facebook.com/{self.WA_API_VERSION}"

    def load_pilot_config(self) -> dict[str, Any]:
        """Loads and parses the pilot configuration YAML.

        Logs a prominent startup warning if `confirmed` is False.
        """
        path = Path(self.PILOT_CONFIG_PATH)
        if not path.is_absolute():
            # Search in workspace root if relative
            potential_paths = [
                path,
                Path(__file__).resolve().parent.parent.parent.parent / path,
                Path(__file__).resolve().parent.parent.parent / path,
            ]
            for p in potential_paths:
                if p.exists():
                    path = p
                    break

        if not path.exists():
            log.warning("Pilot configuration file not found at %s", self.PILOT_CONFIG_PATH)
            return {"confirmed": False}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            confirmed = data.get("confirmed", False)
            if not confirmed:
                log.warning(
                    "⚠️  STARTUP WARNING: Pilot config at '%s' has confirmed: false! "
                    "Pilot region and commodities are unverified proposed defaults. "
                    "Do NOT treat these values as confirmed production facts.",
                    path,
                )
            return data
        except Exception as e:
            log.error("Failed to parse pilot configuration at %s: %s", path, e)
            return {"confirmed": False}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton cached instance of application settings."""
    settings = Settings()
    # Trigger pilot config check on initial load
    settings.load_pilot_config()
    return settings
