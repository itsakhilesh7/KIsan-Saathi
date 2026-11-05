"""Intent and slot extraction service for Kisan Saathi.

Strictly controls tool selection:
- Extracts IntentType and IntentSlots via rule-based matching + Pydantic validation
- Merges multi-turn clarification slots from DialogueStateRepository (10-minute TTL)
- Ensures LLM never selects tools or generates raw URLs
"""

import json
import logging
import re
from typing import Any

from ..core.config import Settings, get_settings
from ..core.http_client import get_http_client
from ..integrations.data_gov.commodity_resolver import is_ambiguous_chilli, resolve_commodity
from ..repositories.dialogue_state import DialogueStateRepository
from ..schemas.intent import IntentSlots, IntentType, ParsedIntent

log = logging.getLogger("services.intent")

# Known Telangana districts seen in live data.gov.in Agmarknet data
KNOWN_DISTRICTS: dict[str, str] = {
    "warangal": "Warangal",
    "వరంగల్": "Warangal",
    "वारंगल": "Warangal",
    "khammam": "Khammam",
    "ఖమ్మం": "Khammam",
    "खम्मम": "Khammam",
    "hyderabad": "Hyderabad",
    "హైదరాబాద్": "Hyderabad",
    "हैदराबाद": "Hyderabad",
    "adilabad": "Adilabad",
    "ఆదిలాబాద్": "Adilabad",
    "आदिलाबाद": "Adilabad",
    "karimnagar": "Karimnagar",
    "కరీంనగర్": "Karimnagar",
    "करीमनगर": "Karimnagar",
    "nalgonda": "Nalgonda",
    "నల్గొండ": "Nalgonda",
    "नलगोंडा": "Nalgonda",
    "siddipet": "Siddipet",
    "సిద్దిపేట": "Siddipet",
    "mahbubnagar": "Mahbubnagar",
    "మహబూబ్‌నగర్": "Mahbubnagar",
    "nirmal": "Nirmal",
    "నిర్మల్": "Nirmal",
}

GREETING_KEYWORDS = {
    "hello", "hi", "hey", "namaste", "namaskaram",
    "నమస్కారం", "నమస్తే", "బాగున్నారా", "హలో",
    "नमस्ते", "प्रणाम", "राम राम",
}

PRICE_KEYWORDS = {
    "ధర", "రేటు", "ధరలు", "రేట్లు", "మండి", "మార్కెట్",
    "भाव", "दाम", "कीमत", "मंडी", "रेट",
    "price", "rate", "mandi", "cost", "market",
}

WEATHER_KEYWORDS = {
    # Telugu
    "వర్షం", "వాన", "వాతావరణం", "ఎండ", "చలి", "ఉష్ణోగ్రత", "తుఫాను", "గాలివాన", "వర్షాలు", "నీళ్లు పెట్టాలా",
    # Hindi
    "बारिश", "मौसम", "तापमान", "बरसात", "धूप", "सर्दी", "हवा", "तूफान", "वर्षा", "सिंचाई", "रेन", "इरीगेशन",
    # English / Hinglish
    "weather", "rain", "rainfall", "forecast", "temperature", "mausam", "barish", "barsat", "irrigation",
}

CROP_ADVISORY_KEYWORDS = {
    # Telugu
    "పంట", "ఆకులు", "తెగులు", "పురుగు", "మచ్చలు", "సలహా", "పసుపు", "ముడత", "ఎండిపోవడం", "సస్యరక్షణ",
    # Hindi / Hinglish Devanagari
    "फसल", "पत्ते", "रोग", "कीड़ा", "कीड़े", "धब्बे", "बीमारी", "सलाह", "कर्ल", "प्लांट", "पीले", "सूख",
    # English / Hinglish Latin
    "crop", "disease", "pest", "symptom", "leaves", "leaf", "curl", "spots", "yellowing", "advisory", "plant",
}

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

    # Check for greeting first: ONLY when message is short (<= 4 words) and has no other query/content
    words = [w for w in re.split(r"[\s,?!.]+", clean_text) if w]
    has_greeting_kw = any(k in clean_text.lower() for k in GREETING_KEYWORDS)
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

    # Check active dialogue state for this user (10-minute TTL)
    previous_state: dict[str, Any] | None = None
    if user_hash and dialogue_repo:
        previous_state = dialogue_repo.get_state(user_hash, ttl_seconds=600)

    # Check for ambiguous chilli query or chilli disambiguation follow-up from previous state
    clarification_type: str | None = None
    matched_commodity: str | None = None

    if previous_state and previous_state.get("clarification_type") == "chilli_type":
        lower = clean_text.lower()
        if any(g in lower for g in ["పచ్చి", "green", "hari", "1"]):
            matched_commodity = "Green Chilli"
        elif any(d in lower for d in ["ఎండు", "ఎర్ర", "dry", "red", "sukhi", "lal", "2"]):
            matched_commodity = "Dry Chillies"
        else:
            clarification_type = "chilli_type"
    elif is_ambiguous_chilli(clean_text):
        lower = clean_text.lower()
        if any(g in lower for g in ["పచ్చి", "green", "hari"]):
            matched_commodity = "Green Chilli"
        elif any(d in lower for d in ["ఎండు", "ఎర్ర", "dry", "red", "sukhi", "lal"]):
            matched_commodity = "Dry Chillies"
        else:
            clarification_type = "chilli_type"

    # Check for weather query if not in an active mandi dialogue follow-up
    # Checks token equality or longer phrase inclusion to avoid substring collision (e.g. 'ఎండ' in 'ఎండు')
    is_weather = False
    if not (previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY):
        for kw in WEATHER_KEYWORDS:
            if kw in words or (len(kw) > 4 and kw in clean_text.lower()):
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

    # Attempt standard commodity resolution if not already resolved as chilli
    if not matched_commodity and not clarification_type:
        for token in re.split(r"[\s,?!.]+", clean_text):
            if token:
                res = resolve_commodity(token)
                if res:
                    matched_commodity = res
                    break

        if not matched_commodity:
            matched_commodity = resolve_commodity(clean_text)

    # Attempt district extraction
    matched_district = _match_district(clean_text)

    # If previous clarification was active, merge slots
    if previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY:
        prev_slots = previous_state.get("slots", {})
        if not matched_commodity and prev_slots.get("commodity"):
            matched_commodity = prev_slots["commodity"]
        if not matched_district and prev_slots.get("district"):
            matched_district = prev_slots["district"]

    # Determine if this is a mandi query: requires a price keyword, chilli mention, or active mandi dialogue state
    is_mandi = (
        any(p in clean_text for p in PRICE_KEYWORDS)
        or is_ambiguous_chilli(clean_text)
        or (previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY)
    )

    if not is_mandi:
        # Check for crop advisory query (enabled when crop advisory retrieval corpus is wired)
        has_crop_kw = any(ck in clean_text.lower() for ck in CROP_ADVISORY_KEYWORDS)
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
                "clarification_type": clarification_type,
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
        try:
            resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Strip markdown blocks if returned
                if content.startswith("```"):
                    content = re.sub(r"^```(?:json)?\s*", "", content)
                    content = re.sub(r"\s*```$", "", content)
                return json.loads(content)
        except Exception as e:
            log.warning("LLM intent classification attempt failed: %s", e)
        return None

    # First attempt
    res = await _call_llm_for_json(text)

    # One retry if JSON parsing or request failed
    if res is None:
        log.info("Retrying LLM intent classification once...")
        res = await _call_llm_for_json(f"Return valid JSON only. User query: {text}")

    if not res or not isinstance(res, dict):
        return ParsedIntent(intent=IntentType.UNSUPPORTED_OR_UNCLEAR, language=language), disclosed_name

    try:
        raw_intent_str = res.get("intent", "")
        intent_type = IntentType(raw_intent_str)
        raw_slots = res.get("slots", {}) or {}

        # Canonicalize commodity using commodity_resolver to prevent hallucinated crops
        raw_comm = raw_slots.get("commodity")
        canonical_comm = resolve_commodity(raw_comm) if raw_comm else None

        raw_dist = raw_slots.get("district")
        canonical_dist = _match_district(raw_dist) if raw_dist else _match_district(text)

        slots = IntentSlots(
            commodity=canonical_comm,
            district=canonical_dist,
            state="Telangana",
        )

        missing = []
        if intent_type == IntentType.MANDI_PRICE_QUERY and not canonical_comm:
            missing.append("commodity")

        parsed = ParsedIntent(
            intent=intent_type,
            language=language,
            slots=slots,
            missing_required_slots=missing,
            clarification_needed=len(missing) > 0,
        )
        return parsed, disclosed_name

    except (ValueError, TypeError) as e:
        log.warning("Pydantic validation failed for LLM intent '%s': %s", res, e)
        return ParsedIntent(intent=IntentType.UNSUPPORTED_OR_UNCLEAR, language=language), disclosed_name
