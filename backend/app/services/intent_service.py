"""Intent and slot extraction service for Kisan Saathi.

Strictly controls tool selection:
- Extracts IntentType and IntentSlots via rule-based matching + Pydantic validation
- Merges multi-turn clarification slots from DialogueStateRepository (10-minute TTL)
- Ensures LLM never selects tools or generates raw URLs
- Script-free: all lexicon keywords and district maps imported from core.keywords
"""

import json
import logging
import re
from typing import Any

from ..core.config import Settings, get_settings
from ..core.http_client import get_http_client
from ..core.keywords import (
    BYE_KEYWORDS,
    CAPABILITIES_KEYWORDS,
    CHILLI_DRY_TOKENS,
    CHILLI_GREEN_TOKENS,
    CROP_ADVISORY_KEYWORDS,
    GREETING_KEYWORDS,
    KNOWN_DISTRICTS,
    LOCATION_KEYWORDS,
    OK_KEYWORDS,
    PRICE_KEYWORDS,
    THANKS_KEYWORDS,
    WEATHER_KEYWORDS,
)
from ..integrations.data_gov.commodity_resolver import is_ambiguous_chilli, resolve_commodity
from ..repositories.dialogue_state import DialogueStateRepository
from ..schemas.intent import IntentSlots, IntentType, ParsedIntent

log = logging.getLogger("services.intent")

# Unicode regex patterns for script detection
TELUGU_RANGE_REGEX = re.compile(r"[\u0c00-\u0c7f]")
DEVANAGARI_RANGE_REGEX = re.compile(r"[\u0900-\u097f]")
LATIN_RANGE_REGEX = re.compile(r"[a-zA-Z]")

HINGLISH_WORDS = {
    "kya", "hai", "ka", "ki", "ke", "ko", "bhav", "dam", "mandi", "namaste",
    "aap", "mujhe", "batao", "batayein", "kripya", "nahi", "kaise", "chahiye",
    "kitna", "kitni", "crop", "fasal", "mein", "se", "aur", "ye", "yeh", "kahan",
    "ji", "kal", "barish", "theek", "dhanyavad", "alvida", "mera", "meri", "kaisa"
}


def detect_text_language(text: str) -> str:
    """Detects text language based on Unicode script blocks and Hinglish vocabulary markers.

    Returns:
        'te-IN' for Telugu script,
        'hi-IN' for Devanagari script,
        'hi-en' for Latin text containing Hindi markers,
        'en-IN' for standard English Latin text.
    """
    if not text:
        return "te-IN"

    if TELUGU_RANGE_REGEX.search(text):
        return "te-IN"
    if DEVANAGARI_RANGE_REGEX.search(text):
        return "hi-IN"
    if LATIN_RANGE_REGEX.search(text):
        tokens = set(re.split(r"[\s,?!.]+", text.lower()))
        if tokens & HINGLISH_WORDS:
            return "hi-en"
        return "en-IN"
    return "te-IN"


def _matches_kw(kw: str, text: str, tokens_list: list[str]) -> bool:
    """Matches a keyword against text adhering to script-specific boundary rules:
    - Latin keywords match as whole words using regex word boundaries (\\b...\\b).
    - Indic keywords match as whole tokens (single-word) or exact phrase token sequences (multi-word).
    """
    clean_kw = kw.strip()
    if not clean_kw:
        return False
    is_latin = bool(LATIN_RANGE_REGEX.search(clean_kw)) or clean_kw.isdigit()
    if is_latin:
        kw_parts = clean_kw.split()
        pattern = r"\b" + r"\s+".join(re.escape(w) for w in kw_parts) + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))
    else:
        kw_tokens = clean_kw.split()
        if len(kw_tokens) == 1:
            return kw_tokens[0] in tokens_list
        else:
            n = len(kw_tokens)
            return any(tokens_list[i : i + n] == kw_tokens for i in range(len(tokens_list) - n + 1))


def _has_any(keywords: set[str] | list[str], text: str, tokens_list: list[str]) -> bool:
    """Checks whether any keyword in the set matches text using script-safe boundaries."""
    return any(_matches_kw(k, text, tokens_list) for k in keywords)


def _match_district(text: str, tokens_list: list[str] | None = None) -> str | None:
    """Matches text against known Telangana districts using boundary-safe matching."""
    if not text:
        return None
    if tokens_list is None:
        tokens_list = [w.strip(".,?!;:'\"()[]{}") for w in text.split() if w.strip(".,?!;:'\"()[]{}")]
    for word, canonical in KNOWN_DISTRICTS.items():
        if re.search(r"[a-zA-Z]", word):
            if bool(re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE)):
                return canonical
        else:
            if any(t == word or (len(word) >= 3 and t.startswith(word)) for t in tokens_list):
                return canonical
    return None


def extract_intent(
    text: str,
    language: str = "te-IN",
    user_hash: str | None = None,
    dialogue_repo: DialogueStateRepository | None = None,
    enable_crop_advisory: bool = True,
) -> ParsedIntent:
    """Extracts user intent and slots, resolving against dialogue state if clarification pending.

    Precedence order:
    1. Strong domain intents (Weather, Mandi Price, Crop Advisory).
    2. Pending dialogue answers (short chilli answer, pending slot).
    3. Metadata / conversational intents (Small talk, Capabilities, Location, Greeting),
       which apply ONLY to short messages (<= 6 tokens) that contain no domain words.
    4. Fallback to unsupported.
    """
    clean_text = text.strip()
    raw_words = clean_text.split()
    tokens = [w.strip(".,?!;:'\"()[]{}") for w in raw_words if w.strip(".,?!;:'\"()[]{}")]

    # Check active dialogue state for this user (10-minute TTL)
    previous_state: dict[str, Any] | None = None
    if user_hash and dialogue_repo:
        previous_state = dialogue_repo.get_state(user_hash, ttl_seconds=600)

    # 1. Domain keyword extraction
    has_weather_kw = _has_any(WEATHER_KEYWORDS, clean_text, tokens)
    has_price_kw = _has_any(PRICE_KEYWORDS, clean_text, tokens)
    has_crop_kw = _has_any(CROP_ADVISORY_KEYWORDS, clean_text, tokens)
    matched_district = _match_district(clean_text, tokens)

    # Commodity resolution
    matched_commodity: str | None = None
    clarification_type: str | None = None
    is_chilli = is_ambiguous_chilli(clean_text)

    if is_chilli:
        if has_crop_kw and not has_price_kw:
            matched_commodity = "Chilli"
        elif _has_any(CHILLI_GREEN_TOKENS, clean_text, tokens):
            matched_commodity = "Green Chilli"
        elif _has_any(CHILLI_DRY_TOKENS, clean_text, tokens):
            matched_commodity = "Dry Chillies"
        else:
            clarification_type = "chilli_type"

    if not matched_commodity and not clarification_type:
        for tok in tokens:
            res = resolve_commodity(tok)
            if res:
                matched_commodity = res
                break
        if not matched_commodity:
            matched_commodity = resolve_commodity(clean_text)

    has_commodity = (matched_commodity is not None) or is_chilli

    # =========================================================================
    # PRECEDENCE 1: Strong domain queries (Weather, Mandi Price, Crop Advisory)
    # =========================================================================

    # 1A. Weather Intent (e.g. "weather at my location", "rain in Warangal")
    if has_weather_kw:
        matched_dist = matched_district
        if not matched_dist and previous_state and previous_state.get("slots", {}).get("district"):
            matched_dist = previous_state["slots"]["district"]
        if user_hash and dialogue_repo:
            dialogue_repo.clear_state(user_hash)
        return ParsedIntent(
            intent=IntentType.WEATHER_QUERY,
            language=language,
            slots=IntentSlots(district=matched_dist, state="Telangana"),
            clarification_needed=False,
        )

    # 1B. Mandi Price Intent
    is_standalone_commodity = bool(
        matched_commodity
        and len(tokens) <= 3
        and not has_price_kw
        and not has_crop_kw
        and not clarification_type
    )

    is_mandi_domain = not (has_crop_kw and not has_price_kw) and (
        (has_commodity and has_price_kw)
        or (is_chilli and not has_crop_kw)
        or has_price_kw
        or is_standalone_commodity
    )

    if is_mandi_domain:
        is_assumed_district = False
        if not matched_district and matched_commodity and not clarification_type:
            matched_district = "Warangal"
            is_assumed_district = True

        slots = IntentSlots(
            commodity=matched_commodity,
            district=matched_district,
            state="Telangana",
        )
        missing = []
        if not matched_commodity:
            missing.append("commodity")

        clarification_needed = len(missing) > 0 or (clarification_type is not None)

        if clarification_needed and user_hash and dialogue_repo:
            dialogue_repo.set_state(
                user_hash,
                {
                    "intent": IntentType.MANDI_PRICE_QUERY,
                    "slots": slots.model_dump(),
                    "missing": missing,
                    "clarification_type": clarification_type or "missing_commodity",
                    "pending_slot": "commodity",
                },
            )
        elif not clarification_needed and user_hash and dialogue_repo:
            dialogue_repo.clear_state(user_hash)

        return ParsedIntent(
            intent=IntentType.MANDI_PRICE_QUERY,
            language=language,
            slots=slots,
            missing_required_slots=missing,
            clarification_needed=clarification_needed,
            clarification_type=clarification_type or ("missing_commodity" if missing else None),
            is_assumed_district=is_assumed_district,
        )

    # 1C. Crop Advisory Intent
    if has_crop_kw and not has_price_kw:
        if enable_crop_advisory:
            missing_crop = ["crop"] if not matched_commodity else []
            return ParsedIntent(
                intent=IntentType.CROP_ADVISORY_QUERY,
                language=language,
                slots=IntentSlots(
                    crop=matched_commodity,
                    commodity=matched_commodity,
                    district=matched_district,
                    state="Telangana",
                ),
                missing_required_slots=missing_crop,
                clarification_needed=len(missing_crop) > 0,
            )
        else:
            return ParsedIntent(
                intent=IntentType.UNSUPPORTED_OR_UNCLEAR,
                language=language,
                slots=IntentSlots(),
                clarification_needed=False,
            )

    # =========================================================================
    # PRECEDENCE 2: Pending dialogue answers
    # =========================================================================
    if previous_state:
        # 2A. Chilli Disambiguation Follow-up
        if previous_state.get("clarification_type") == "chilli_type":
            # Exact answer only when message is short (<= 3 tokens)
            if len(tokens) <= 3:
                if _has_any(CHILLI_GREEN_TOKENS, clean_text, tokens):
                    prev_dist = previous_state.get("slots", {}).get("district", "Warangal")
                    if user_hash and dialogue_repo:
                        dialogue_repo.clear_state(user_hash)
                    return ParsedIntent(
                        intent=IntentType.MANDI_PRICE_QUERY,
                        language=language,
                        slots=IntentSlots(commodity="Green Chilli", district=prev_dist, state="Telangana"),
                        clarification_needed=False,
                    )
                elif _has_any(CHILLI_DRY_TOKENS, clean_text, tokens):
                    prev_dist = previous_state.get("slots", {}).get("district", "Warangal")
                    if user_hash and dialogue_repo:
                        dialogue_repo.clear_state(user_hash)
                    return ParsedIntent(
                        intent=IntentType.MANDI_PRICE_QUERY,
                        language=language,
                        slots=IntentSlots(commodity="Dry Chillies", district=prev_dist, state="Telangana"),
                        clarification_needed=False,
                    )
            # If not a short exact chilli answer, treat as new query and clear old chilli state
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)

        # 2B. Pending slot resolution (e.g. "which crop?" follow-up)
        elif previous_state.get("pending_slot") == "commodity" and matched_commodity:
            prev_dist = previous_state.get("slots", {}).get("district", "Warangal")
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.MANDI_PRICE_QUERY,
                language=language,
                slots=IntentSlots(commodity=matched_commodity, district=prev_dist, state="Telangana"),
                clarification_needed=False,
                is_assumed_district=True,
            )

        # 2C. Pending district resolution
        elif previous_state.get("pending_slot") == "district" and matched_district:
            prev_comm = previous_state.get("slots", {}).get("commodity")
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.MANDI_PRICE_QUERY,
                language=language,
                slots=IntentSlots(commodity=prev_comm, district=matched_district, state="Telangana"),
                clarification_needed=False,
            )

        # 2D. Pending crop resolution for crop advisory
        elif previous_state.get("pending_slot") == "crop" and matched_commodity:
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.CROP_ADVISORY_QUERY,
                language=language,
                slots=IntentSlots(crop=matched_commodity, commodity=matched_commodity, district="Warangal", state="Telangana"),
                clarification_needed=False,
            )

    # =========================================================================
    # PRECEDENCE 3: Capabilities, Location, Small Talk, Greeting
    # Apply ONLY to short messages (<= 6 tokens) that contain no domain words.
    # =========================================================================
    is_short = len(tokens) <= 6
    no_domain_words = (not has_commodity) and (not has_price_kw) and (not has_weather_kw) and (not has_crop_kw)

    if is_short and no_domain_words:
        # 3A. Small Talk (Thanks, OK, Bye)
        if _has_any(THANKS_KEYWORDS, clean_text, tokens):
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.SMALL_TALK,
                language=language,
                small_talk_type="thanks",
            )

        if _has_any(OK_KEYWORDS, clean_text, tokens):
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.SMALL_TALK,
                language=language,
                small_talk_type="ok",
            )

        if _has_any(BYE_KEYWORDS, clean_text, tokens):
            if user_hash and dialogue_repo:
                dialogue_repo.clear_state(user_hash)
            return ParsedIntent(
                intent=IntentType.SMALL_TALK,
                language=language,
                small_talk_type="bye",
            )

        # 3B. Capabilities Query
        if _has_any(CAPABILITIES_KEYWORDS, clean_text, tokens):
            return ParsedIntent(
                intent=IntentType.CAPABILITIES_QUERY,
                language=language,
            )

        # 3C. Location Query
        if _has_any(LOCATION_KEYWORDS, clean_text, tokens):
            return ParsedIntent(
                intent=IntentType.LOCATION_QUERY,
                language=language,
            )

        # 3D. Greeting (strictly <= 4 words)
        if len(tokens) <= 4 and _has_any(GREETING_KEYWORDS, clean_text, tokens):
            return ParsedIntent(
                intent=IntentType.GREETING_OR_HELP,
                language=language,
                slots=IntentSlots(),
                clarification_needed=False,
            )

    # =========================================================================
    # PRECEDENCE 4: Fallback
    # =========================================================================
    return ParsedIntent(
        intent=IntentType.UNSUPPORTED_OR_UNCLEAR,
        language=language,
        slots=IntentSlots(),
        clarification_needed=False,
    )


LLM_INTENT_SYSTEM_PROMPT = """You are a strict intent classifier for Kisan Saathi, a farmer voice assistant.
Classify the user message into exactly ONE of the allowed intents:
- mandi_price_query (queries about market prices, rates, bhav of crops)
- weather_query (queries about rain, forecast, temperature, weather)
- crop_advisory_query (queries about crop disease, pests, symptoms, cultivation practices)
- greeting_or_help (greetings or queries about what the bot does)
- unsupported_or_unclear (anything else or unclear queries)

You must respond ONLY with a single JSON object conforming to this schema, with no preamble, no markdown, and no extra text:
{"intent": "<one of the 5 allowed intents>", "slots": {"commodity": null, "district": null, "state": "Telangana"}}"""


async def classify_intent_with_llm_fallback(
    text: str,
    language: str = "te-IN",
    settings: Settings | None = None,
    dialogue_repo: DialogueStateRepository | None = None,
    user_hash: str | None = None,
) -> tuple[ParsedIntent, str | None]:
    """Extracts intent rule-based first; if unclear and LLM_BASE_URL is configured, invokes LLM fallback."""
    cfg = settings or get_settings()
    rule_parsed = extract_intent(text, language=language, user_hash=user_hash, dialogue_repo=dialogue_repo)

    if rule_parsed.intent != IntentType.UNSUPPORTED_OR_UNCLEAR:
        return rule_parsed, None

    if not cfg.LLM_BASE_URL.strip() or cfg.APP_ENV == "test":
        return rule_parsed, None

    # LLM-assisted intent classification fallback (Requirement 5)
    disclosed_name = (
        cfg.LLM_DISCLOSED_NAME.strip()
        or cfg.LLM_MODEL.strip()
        or "openai-compatible-model"
    )

    client = get_http_client()
    url = f"{cfg.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg.LLM_API_KEY.strip():
        headers["Authorization"] = f"Bearer {cfg.LLM_API_KEY.strip()}"

    async def _call_llm_for_json(prompt_text: str) -> dict[str, Any] | None:
        payload = {
            "model": cfg.LLM_MODEL,
            "messages": [
                {"role": "system", "content": LLM_INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": 0.0,
            "max_tokens": 150,
        }
        for _ in range(2):
            try:
                resp = await client.post(url, json=payload, headers=headers, timeout=20.0)
                if resp.status_code == 200:
                    raw_json = resp.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(raw_json)
                    if "intent" in parsed:
                        return parsed
            except Exception as e:
                log.warning("LLM intent classification attempt failed: %s", e)
        return None

    parsed_json = await _call_llm_for_json(text)
    if not parsed_json or "intent" not in parsed_json:
        return rule_parsed, None

    raw_intent = str(parsed_json.get("intent", "")).lower()
    intent_map = {
        "mandi_price_query": IntentType.MANDI_PRICE_QUERY,
        "weather_query": IntentType.WEATHER_QUERY,
        "crop_advisory_query": IntentType.CROP_ADVISORY_QUERY,
        "greeting_or_help": IntentType.GREETING_OR_HELP,
    }
    resolved_intent = intent_map.get(raw_intent, IntentType.UNSUPPORTED_OR_UNCLEAR)

    slots_dict = parsed_json.get("slots", {}) or {}
    matched_crop = resolve_commodity(slots_dict.get("commodity") or "")
    matched_district = _match_district(slots_dict.get("district") or "")

    slots = IntentSlots(
        commodity=matched_crop,
        crop=matched_crop,
        district=matched_district,
        state=slots_dict.get("state") or "Telangana",
    )

    return (
        ParsedIntent(
            intent=resolved_intent,
            language=language,
            slots=slots,
            clarification_needed=False,
        ),
        disclosed_name,
    )

