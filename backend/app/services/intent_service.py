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
    "kitna", "kitni", "crop", "fasal", "mein", "se", "aur", "ye", "yeh", "kahan"
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


def _match_district(text: str) -> str | None:
    """Matches text against known Telangana districts."""
    cleaned = text.lower()
    for word, canonical in KNOWN_DISTRICTS.items():
        if word in cleaned:
            return canonical
    return None


def extract_intent(
    text: str,
    language: str = "te-IN",
    user_hash: str | None = None,
    dialogue_repo: DialogueStateRepository | None = None,
    enable_crop_advisory: bool = False,
) -> ParsedIntent:
    """Extracts user intent and slots, resolving against dialogue state if clarification pending."""
    clean_text = text.strip()
    words = [w for w in re.split(r"[\s,?!.]+", clean_text) if w]
    lower_text = clean_text.lower()

    # Check active dialogue state for this user (10-minute TTL)
    previous_state: dict[str, Any] | None = None
    if user_hash and dialogue_repo:
        previous_state = dialogue_repo.get_state(user_hash, ttl_seconds=600)

    # 1. Small talk: Thanks, OK, Bye
    if any(k in lower_text for k in THANKS_KEYWORDS):
        if user_hash and dialogue_repo:
            dialogue_repo.clear_state(user_hash)
        return ParsedIntent(
            intent=IntentType.SMALL_TALK,
            language=language,
            small_talk_type="thanks",
        )

    if any(k == lower_text or k in words for k in OK_KEYWORDS) and len(words) <= 3:
        if user_hash and dialogue_repo:
            dialogue_repo.clear_state(user_hash)
        return ParsedIntent(
            intent=IntentType.SMALL_TALK,
            language=language,
            small_talk_type="ok",
        )

    if any(k == lower_text or k in words for k in BYE_KEYWORDS) and len(words) <= 3:
        if user_hash and dialogue_repo:
            dialogue_repo.clear_state(user_hash)
        return ParsedIntent(
            intent=IntentType.SMALL_TALK,
            language=language,
            small_talk_type="bye",
        )

    # 2. Capabilities query ("what can you do")
    if any(k in lower_text for k in CAPABILITIES_KEYWORDS):
        return ParsedIntent(
            intent=IntentType.CAPABILITIES_QUERY,
            language=language,
        )

    # 3. Location query ("what's my location?")
    if any(k in lower_text for k in LOCATION_KEYWORDS):
        return ParsedIntent(
            intent=IntentType.LOCATION_QUERY,
            language=language,
        )

    # 4. Greeting: ONLY when message is short (<= 4 words) and has no other query/content
    has_greeting_kw = any(k in lower_text for k in GREETING_KEYWORDS)
    has_price_kw = any(p in clean_text for p in PRICE_KEYWORDS)

    if has_greeting_kw and len(words) <= 4 and not has_price_kw:
        # Check if there is a commodity or district mention
        has_commodity = any(resolve_commodity(w) is not None for w in words)
        has_district = _match_district(clean_text) is not None
        if not has_commodity and not has_district:
            return ParsedIntent(
                intent=IntentType.GREETING_OR_HELP,
                language=language,
                slots=IntentSlots(),
                clarification_needed=False,
            )

    # 5. Check for ambiguous chilli query or chilli disambiguation follow-up from previous state
    clarification_type: str | None = None
    matched_commodity: str | None = None

    if previous_state and previous_state.get("clarification_type") == "chilli_type":
        if any(g in lower_text for g in CHILLI_GREEN_TOKENS):
            matched_commodity = "Green Chilli"
        elif any(d in lower_text for d in CHILLI_DRY_TOKENS):
            matched_commodity = "Dry Chillies"
        else:
            clarification_type = "chilli_type"
    elif is_ambiguous_chilli(clean_text):
        if any(g in lower_text for g in CHILLI_GREEN_TOKENS):
            matched_commodity = "Green Chilli"
        elif any(d in lower_text for d in CHILLI_DRY_TOKENS):
            matched_commodity = "Dry Chillies"
        else:
            clarification_type = "chilli_type"

    # 6. Check for weather query if not in an active chilli or mandi follow-up
    is_weather = False
    if not (previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY and previous_state.get("clarification_type") == "chilli_type"):
        for kw in WEATHER_KEYWORDS:
            if kw in words or (len(kw) > 4 and kw in lower_text):
                is_weather = True
                break

    if is_weather:
        matched_dist = _match_district(clean_text)
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

    # 7. Standard commodity resolution if not already resolved as chilli
    if not matched_commodity and not clarification_type:
        for token in re.split(r"[\s,?!.]+", clean_text):
            if token:
                res = resolve_commodity(token)
                if res:
                    matched_commodity = res
                    break

        if not matched_commodity:
            matched_commodity = resolve_commodity(clean_text)

    # 8. District extraction
    matched_district = _match_district(clean_text)

    # 9. Multi-turn dialogue slot merging
    if previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY:
        prev_slots = previous_state.get("slots", {})
        if not matched_commodity and prev_slots.get("commodity"):
            matched_commodity = prev_slots["commodity"]
        if not matched_district and prev_slots.get("district"):
            matched_district = prev_slots["district"]

    # Check for crop advisory keywords
    has_crop_kw = any(ck in lower_text for ck in CROP_ADVISORY_KEYWORDS)

    # 10. Standalone short commodity query (Item C.2):
    # If message is short (<= 3 words) and is ONLY a known commodity name (not crop problem/advisory),
    # it is a mandi price query for pilot district Warangal
    is_standalone_commodity = False
    if matched_commodity and len(words) <= 3 and not has_price_kw and not clarification_type and not has_crop_kw:
        is_standalone_commodity = True

    # 11. Determine if this is a mandi query
    is_mandi = (
        has_price_kw
        or is_ambiguous_chilli(clean_text)
        or is_standalone_commodity
        or (previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY)
    )

    if not is_mandi:
        # Check for crop advisory query
        if has_crop_kw and enable_crop_advisory:

            resolved_crop = matched_commodity
            if not resolved_crop:
                for token in re.split(r"[\s,?!.]+", clean_text):
                    if token:
                        c = resolve_commodity(token)
                        if c:
                            resolved_crop = c
                            break
            missing_crop = ["crop"] if not resolved_crop else []
            return ParsedIntent(
                intent=IntentType.CROP_ADVISORY_QUERY,
                language=language,
                slots=IntentSlots(
                    crop=resolved_crop,
                    commodity=resolved_crop,
                    district=matched_district,
                    state="Telangana",
                ),
                missing_required_slots=missing_crop,
                clarification_needed=len(missing_crop) > 0,
            )

        return ParsedIntent(
            intent=IntentType.UNSUPPORTED_OR_UNCLEAR,
            language=language,
            slots=IntentSlots(),
            clarification_needed=False,
        )

    # When district is not explicitly stated in a standalone query or query without district,
    # assume pilot district Warangal (Item C.2)
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

    # Save state if clarification is needed
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
        # Clarification complete, clear state
        dialogue_repo.clear_state(user_hash)

    return ParsedIntent(
        intent=IntentType.MANDI_PRICE_QUERY,
        language=language,
        slots=slots,
        missing_required_slots=missing,
        clarification_needed=clarification_needed,
        clarification_type=clarification_type,
        is_assumed_district=is_assumed_district,
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

    if not cfg.LLM_BASE_URL.strip():
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

