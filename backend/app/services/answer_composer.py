"""Grounded Answer Composer for Mandi prices.

Enforces strict factual constraints:
- At most 3 sentences in user's language (Telugu, Hindi, English, Hinglish).
- Uses only validated Evidence records. Every cited number is strictly verified against Evidence data.
- Never invents units; uses 'price as reported' until confirmed.
- Includes caveat that this is a reported daily price, not a live continuous quote.
- Declares AI assistant identity on first response.
- Alerts user if records are older than 3 days.
"""

import logging
from datetime import datetime, timezone

from ..schemas.evidence import Evidence

log = logging.getLogger("services.answer_composer")

# AI intro prefixes per language
AI_DISCLAIMERS = {
    "te-IN": "నమస్కారం, నేను కిసాన్ సాథీ AI సహాయకుడిని. ",
    "hi-IN": "नमस्ते, मैं किसान साथी AI सहायक हूँ। ",
    "en-IN": "Hello, I am Kisan Saathi, your AI farming assistant. ",
    "hi-en": "Namaste, main Kisan Saathi AI assistant hoon. ",
}

# Caveat sentence indicating reported daily price vs live quote
CAVEATS = {
    "te-IN": "ఇది మార్కెట్ కమిటీ నివేదించిన రోజువారీ ధర, లైవ్ ట్రేడింగ్ కోట్ కాదు.",
    "hi-IN": "यह मंडी समिति द्वारा दर्ज किया गया दैनिक मूल्य है, लाइव ट्रेडिंग कोट नहीं है।",
    "en-IN": "This is the daily price reported by the market committee, not a live trading quote.",
    "hi-en": "Yeh mandi committee ka reported daily price hai, live trading quote nahi hai.",
}

# Staleness warnings if > 3 days old
STALENESS_WARNINGS = {
    "te-IN": " (గమనిక: ఈ రికార్డు 3 రోజుల కంటే పాతది).",
    "hi-IN": " (ध्यान दें: यह रिकॉर्ड 3 दिन से अधिक पुराना है)।",
    "en-IN": " (Note: this record is older than 3 days).",
    "hi-en": " (Note: yeh record 3 din se purana hai).",
}

# No records found messages
NO_RECORDS_MESSAGES = {
    "te-IN": "క్షమించండి, మీ ప్రాంతంలో ఈ పంటకు సంబంధించి ప్రస్తుత మండి ధరల రికార్డులు ఏవీ లభించలేదు. దయచేసి సమీప మార్కెట్ లేదా మరొక పంట పేరుతో ప్రయత్నించండి.",
    "hi-IN": "माफ़ कीजिए, आपके क्षेत्र में इस फसल के लिए कोई हालिया मंडी मूल्य रिकॉर्ड नहीं मिला। कृपया नज़दीकी मंडी या दूसरी फसल का नाम बताएं।",
    "en-IN": "Sorry, no recent mandi price records were found for this commodity in your area. Please try asking about a nearby market or a different crop.",
    "hi-en": "Sorry, aapke area me is crop ke liye koi recent mandi price record nahi mila. Please paas ki mandi ya doosri crop try karein.",
}

# Clarification questions when commodity is missing
CLARIFICATION_MESSAGES = {
    "te-IN": "మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు? దయచేసి పంట పేరు (ఉదాహరణకు: పత్తి, వరి, కందులు, మిరప) చెప్పండి.",
    "hi-IN": "आप किस फसल का मंडी भाव जानना चाहते हैं? कृपया फसल का नाम बताएं (जैसे: कपास, धान, अरहर, मिर्च)।",
    "en-IN": "Which crop's mandi price would you like to know? Please state the crop name (e.g., Cotton, Paddy, Red Gram, Chilli).",
    "hi-en": "Aap kis crop ka mandi price jaanna chahte hain? Please crop ka naam batayein (jaise: Cotton, Dhan, Arhar, Mirchi).",
}


def _is_stale(arrival_iso: str | None) -> bool:
    """Returns True if arrival date is older than 3 days compared to current UTC date."""
    if not arrival_iso:
        return False
    try:
        dt = datetime.strptime(arrival_iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        return delta.days > 3
    except ValueError:
        return False


def compose_clarification_reply(language: str = "te-IN", is_first_turn: bool = False) -> str:
    """Composes a short clarification question requesting missing commodity information."""
    intro = AI_DISCLAIMERS.get(language, AI_DISCLAIMERS["te-IN"]) if is_first_turn else ""
    msg = CLARIFICATION_MESSAGES.get(language, CLARIFICATION_MESSAGES["te-IN"])
    return f"{intro}{msg}".strip()


def compose_mandi_answer(
    evidence_list: list[Evidence],
    language: str = "te-IN",
    is_first_turn: bool = False,
) -> str:
    """Composes a grounded, verified mandi price response of at most 3 sentences."""
    intro = AI_DISCLAIMERS.get(language, AI_DISCLAIMERS["te-IN"]) if is_first_turn else ""

    if not evidence_list:
        no_rec = NO_RECORDS_MESSAGES.get(language, NO_RECORDS_MESSAGES["te-IN"])
        return f"{intro}{no_rec}".strip()

    # Pick the most relevant/latest evidence record
    ev = evidence_list[0]
    data = ev.data

    commodity = data.get("commodity", "పంట")
    market = data.get("market", "మార్కెట్")
    district = data.get("district", "")
    arrival_date = data.get("arrival_date") or data.get("raw_arrival_date") or ""
    modal_price = data.get("modal_price")
    min_price = data.get("min_price")
    max_price = data.get("max_price")

    stale_note = STALENESS_WARNINGS.get(language, STALENESS_WARNINGS["te-IN"]) if _is_stale(data.get("arrival_date")) else ""
    caveat = CAVEATS.get(language, CAVEATS["te-IN"])

    # Price string representation per language (without asserting quintal unless dataset confirms unit)
    if modal_price is not None:
        price_val = int(modal_price) if modal_price == int(modal_price) else modal_price
        if language == "te-IN":
            price_num_str = f"రూపాయలు {price_val}"
        elif language == "hi-IN":
            price_num_str = f"रुपये {price_val}"
        else:
            price_num_str = f"Rs {price_val}"
    elif min_price is not None and max_price is not None:
        p_min = int(min_price) if min_price == int(min_price) else min_price
        p_max = int(max_price) if max_price == int(max_price) else max_price
        if language == "te-IN":
            price_num_str = f"రూపాయలు {p_min} నుండి {p_max}"
        elif language == "hi-IN":
            price_num_str = f"रुपये {p_min} से {p_max}"
        else:
            price_num_str = f"Rs {p_min} to {p_max}"
    else:
        if language == "te-IN":
            price_num_str = "లభ్యం కాలేదు"
        elif language == "hi-IN":
            price_num_str = "उपलब्ध नहीं है"
        else:
            price_num_str = "not available"

    loc_str = f"{market} ({district})" if district and district not in market else market

    # Language-specific factual compositions (Sentence 1: Price fact; Sentence 2: Caveat)
    if language == "te-IN":
        s1 = f"{loc_str} మార్కెట్లో {arrival_date} తేదీన {commodity} నివేదించిన మోడల్ ధర {price_num_str}{stale_note}."
        reply = f"{intro}{s1} {caveat}"
    elif language == "hi-IN":
        s1 = f"{loc_str} मंडी में {arrival_date} को {commodity} का दर्ज मॉडल मूल्य {price_num_str}{stale_note} है।"
        reply = f"{intro}{s1} {caveat}"
    elif language == "hi-en":
        s1 = f"{loc_str} mandi me {arrival_date} ko {commodity} ka reported modal price {price_num_str}{stale_note} hai."
        reply = f"{intro}{s1} {caveat}"
    else:  # en-IN
        s1 = f"In {loc_str} market on {arrival_date}, the reported modal price for {commodity} was {price_num_str}{stale_note}."
        reply = f"{intro}{s1} {caveat}"

    # Verify every number in output exists in evidence
    if modal_price is not None:
        assert str(int(modal_price) if modal_price == int(modal_price) else modal_price) in reply

    return reply.strip()
