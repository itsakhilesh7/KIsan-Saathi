"""Intent and slot extraction service for Kisan Saathi.

Strictly controls tool selection:
- Extracts IntentType and IntentSlots via rule-based matching + Pydantic validation
- Merges multi-turn clarification slots from DialogueStateRepository (10-minute TTL)
- Ensures LLM never selects tools or generates raw URLs
"""

import logging
import re
from typing import Any

from ..integrations.data_gov.commodity_resolver import resolve_commodity
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
) -> ParsedIntent:
    """Extracts user intent and slots, resolving against dialogue state if clarification pending."""
    clean_text = text.strip()

    # Check for greeting first
    if any(k in clean_text.lower() for k in GREETING_KEYWORDS) and not any(p in clean_text for p in PRICE_KEYWORDS):
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

    # Attempt commodity resolution
    matched_commodity = None
    for token in re.split(r"[\s,?!.]+", clean_text):
        if token:
            res = resolve_commodity(token)
            if res:
                matched_commodity = res
                break

    # If not found token-by-token, check entire text
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

    # Determine if this is a mandi query: requires a price keyword OR an active mandi dialogue state
    is_mandi = (
        any(p in clean_text for p in PRICE_KEYWORDS)
        or (previous_state and previous_state.get("intent") == IntentType.MANDI_PRICE_QUERY)
    )

    if not is_mandi:
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

    clarification_needed = len(missing) > 0

    # Save state if clarification is needed
    if clarification_needed and user_hash and dialogue_repo:
        dialogue_repo.set_state(
            user_hash,
            {
                "intent": IntentType.MANDI_PRICE_QUERY,
                "slots": slots.model_dump(),
                "missing": missing,
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
    )
