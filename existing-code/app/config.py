import os
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# Gnani
GNANI_API_KEY = _get("GNANI_API_KEY")
STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
STT_MODEL = _get("STT_MODEL", "prisma-v3.0")
STT_LANGUAGE = _get("STT_LANGUAGE", "indic-auto")
TTS_MODEL = _get("TTS_MODEL", "timbre-v2.5")
TTS_V3_VOICE = _get("TTS_V3_VOICE", "Shivani")

# Timbre v2.5: each voice has ONE preferred language (see docs "Available Voices").
TTS_V25_VOICES = {
    "te-IN": "Lavanya",
    "hi-IN": "Nalini",
    "en-IN": "Kaveri",
    "hi-en": "Poorvi",
}
TTS_DEFAULT_LANG = "hi-IN"

# LLM (OpenAI-compatible). Empty base URL => echo mode.
LLM_BASE_URL = _get("LLM_BASE_URL").rstrip("/")
LLM_API_KEY = _get("LLM_API_KEY")
LLM_MODEL = _get("LLM_MODEL", "gnani/gnani-evon-v3.3-30B-A3B")

# WhatsApp
WA_PHONE_NUMBER_ID = _get("WHATSAPP_PHONE_NUMBER_ID")
WA_ACCESS_TOKEN = _get("WHATSAPP_ACCESS_TOKEN")
WA_VERIFY_TOKEN = _get("WHATSAPP_VERIFY_TOKEN")
META_APP_SECRET = _get("META_APP_SECRET")
WA_API_VERSION = _get("WA_API_VERSION", "v23.0")
WA_GRAPH = f"https://graph.facebook.com/{WA_API_VERSION}"

SEND_TEXT_COPY = _get("SEND_TEXT_COPY", "true").lower() == "true"

# Prisma REST limit is 30 s; we cut at 25 s to stay safely under it.
MAX_STT_SECONDS = 25
