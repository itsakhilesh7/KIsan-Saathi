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

# Unsupported intent messages (Item 2)
UNSUPPORTED_INTENT_MESSAGES = {
    "te-IN": "నేను ప్రస్తుతానికి పంటల మండి ధరల సమాచారం మాత్రమే అందించగలను (వాతావరణం మరియు పంట సలహాలు త్వరలో రానున్నాయి). మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?",
    "hi-IN": "मैं फ़िलहाल केवल मंडी भाव की जानकारी दे सकता हूँ (मौसम और फसल सलाह जल्द उपलब्ध होगी)। आप किस फसल का मंडी भाव जानना चाहते हैं?",
    "en-IN": "I can currently help with mandi crop prices (weather and crop advice coming soon). Which crop's mandi price would you like to know?",
    "hi-en": "Main abhi sirf mandi crop prices me help kar sakta hoon (weather aur crop advice jald aane wali hai). Aap kis crop ka mandi price jaanna chahte hain?",
}

MONTH_NAMES = {
    "te-IN": {
        1: "జనవరి", 2: "ఫిబ్రవరి", 3: "మార్చి", 4: "ఏప్రిల్", 5: "మే", 6: "జూన్",
        7: "జూలై", 8: "ఆగస్టు", 9: "సెప్టెంబర్", 10: "అక్టోబర్", 11: "నవంబర్", 12: "డిసెంబర్",
    },
    "hi-IN": {
        1: "जनवरी", 2: "फ़रवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
        7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर",
    },
    "en-IN": {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
    },
    "hi-en": {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
    },
}


def format_natural_date(arrival_iso: str | None, language: str = "te-IN") -> str:
    """Converts ISO arrival date (YYYY-MM-DD) into natural localized date string (e.g. '4 November')."""
    if not arrival_iso:
        return ""
    try:
        dt = datetime.strptime(str(arrival_iso).strip()[:10], "%Y-%m-%d")
        month_dict = MONTH_NAMES.get(language, MONTH_NAMES["te-IN"])
        month_name = month_dict.get(dt.month, str(dt.month))
        return f"{dt.day} {month_name}"
    except (ValueError, TypeError):
        return str(arrival_iso)


def _format_unit_phrase(unit: str, language: str) -> str:
    """Formats optional unit phrase (Item 7). If unit is empty, returns empty string."""
    cleaned = (unit or "").strip().lower()
    if not cleaned:
        return ""
    if "quintal" in cleaned:
        if language == "te-IN":
            return " క్వింటాలుకు"
        elif language == "hi-IN":
            return " प्रति क्विंटल"
        else:
            return " per quintal"
    return f" ({unit})"

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


def _format_price_val(
    modal_price: float | None,
    min_price: float | None,
    max_price: float | None,
    language: str,
) -> str:
    """Formats price number cleanly per language without abbreviation periods."""
    if modal_price is not None:
        val = int(modal_price) if modal_price == int(modal_price) else modal_price
        if language == "te-IN":
            return f"రూపాయలు {val}"
        elif language == "hi-IN":
            return f"रुपये {val}"
        else:
            return f"Rs {val}"
    elif min_price is not None and max_price is not None:
        p_min = int(min_price) if min_price == int(min_price) else min_price
        p_max = int(max_price) if max_price == int(max_price) else max_price
        if language == "te-IN":
            return f"రూపాయలు {p_min} నుండి {p_max}"
        elif language == "hi-IN":
            return f"रुपये {p_min} से {p_max}"
        else:
            return f"Rs {p_min} to {p_max}"
    return "లభ్యం కాలేదు" if language == "te-IN" else ("उपलब्ध नहीं" if language == "hi-IN" else "not available")


def compose_mandi_answer(
    evidence_list: list[Evidence],
    language: str = "te-IN",
    is_first_turn: bool = False,
    requested_district: str | None = None,
    requested_commodity: str | None = None,
    requested_state: str | None = "Telangana",
    unit: str = "",
) -> str:
    """Composes a grounded, verified mandi price response of at most 3 sentences.

    Groups records by market for requested commodity & district, mentions up to 2 markets
    (latest date first), and handles empty district records by offering state-level alternatives.
    """
    intro = AI_DISCLAIMERS.get(language, AI_DISCLAIMERS["te-IN"]) if is_first_turn else ""

    if not evidence_list:
        if requested_district:
            crop_name = requested_commodity or ("ఈ పంట" if language == "te-IN" else ("इस फसल" if language == "hi-IN" else "this crop"))
            state_name = requested_state or ("తెలంగాణ" if language == "te-IN" else ("तेलंगाना" if language == "hi-IN" else "Telangana"))
            if language == "te-IN":
                no_dist = f"క్షమించండి, {requested_district} జిల్లాలో {crop_name}కు సంబంధించి ప్రస్తుత మండి రికార్డులు ఏవీ లభించలేదు. మీరు {state_name} రాష్ట్రంలోని ఇతర మార్కెట్ల ధరలు తెలుసుకోవాలనుకుంటున్నారా?"
            elif language == "hi-IN":
                no_dist = f"माफ़ कीजिए, {requested_district} ज़िले में {crop_name} का कोई हालिया मंडी रिकॉर्ड नहीं मिला। क्या आप {state_name} राज्य की अन्य मंडियों के भाव जानना चाहते हैं?"
            elif language == "hi-en":
                no_dist = f"Sorry, {requested_district} district me {crop_name} ka koi recent mandi record nahi mila. Kya aap {state_name} state ki doosri mandiyon ke prices jaanna chahte hain?"
            else:
                no_dist = f"Sorry, no recent mandi records were found for {crop_name} in {requested_district} district. Would you like prices from across {state_name} state?"
            return f"{intro}{no_dist}".strip()

        no_rec = NO_RECORDS_MESSAGES.get(language, NO_RECORDS_MESSAGES["te-IN"])
        return f"{intro}{no_rec}".strip()

    # Group evidence records by market, keeping the record with the latest arrival date for each market
    market_groups: dict[str, Evidence] = {}
    for ev in evidence_list:
        mkt = ev.data.get("market") or "Unknown Market"
        if mkt not in market_groups:
            market_groups[mkt] = ev
        else:
            # Pick latest by arrival_date
            curr_date = ev.data.get("arrival_date") or ""
            prev_date = market_groups[mkt].data.get("arrival_date") or ""
            if curr_date > prev_date:
                market_groups[mkt] = ev

    # Sort markets by arrival date descending
    sorted_markets = sorted(
        market_groups.values(),
        key=lambda x: x.data.get("arrival_date") or "",
        reverse=True,
    )

    selected = sorted_markets[:2]
    u_str = _format_unit_phrase(unit, language)
    caveat = CAVEATS.get(language, CAVEATS["te-IN"])

    if len(selected) == 1:
        d1 = selected[0].data
        comm = d1.get("commodity", requested_commodity or "పంట")
        mkt1 = d1.get("market", "మార్కెట్")
        date1 = format_natural_date(d1.get("arrival_date"), language=language)
        p1_str = _format_price_val(d1.get("modal_price"), d1.get("min_price"), d1.get("max_price"), language)
        stale_note = STALENESS_WARNINGS.get(language, "") if _is_stale(d1.get("arrival_date")) else ""

        if language == "te-IN":
            s1 = f"{mkt1} మార్కెట్లో {date1}న {comm} నివేదించిన మోడల్ ధర {p1_str}{u_str}{stale_note}."
        elif language == "hi-IN":
            s1 = f"{mkt1} मंडी में {date1} को {comm} का दर्ज मॉडल मूल्य {p1_str}{u_str}{stale_note} है।"
        elif language == "hi-en":
            s1 = f"{mkt1} mandi me {date1} ko {comm} ka reported modal price {p1_str}{u_str}{stale_note} hai."
        else:
            s1 = f"In {mkt1} market on {date1}, the reported modal price for {comm} was {p1_str}{u_str}{stale_note}."

    else:
        d1 = selected[0].data
        d2 = selected[1].data
        comm = d1.get("commodity", requested_commodity or "పంట")
        mkt1 = d1.get("market", "మార్కెట్ 1")
        mkt2 = d2.get("market", "మార్కెట్ 2")
        date1 = format_natural_date(d1.get("arrival_date"), language=language)
        date2 = format_natural_date(d2.get("arrival_date"), language=language)
        p1_str = _format_price_val(d1.get("modal_price"), d1.get("min_price"), d1.get("max_price"), language)
        p2_str = _format_price_val(d2.get("modal_price"), d2.get("min_price"), d2.get("max_price"), language)
        any_stale = _is_stale(d1.get("arrival_date")) or _is_stale(d2.get("arrival_date"))
        stale_note = STALENESS_WARNINGS.get(language, "") if any_stale else ""

        dist = requested_district or d1.get("district") or ""
        if dist:
            dist_label_te = f"{dist} జిల్లా"
            dist_label_hi = f"{dist} ज़िले"
            dist_label_en = f"{dist} district"
        else:
            dist_label_te = f"{mkt1} మరియు {mkt2}"
            dist_label_hi = f"{mkt1} और {mkt2}"
            dist_label_en = f"{mkt1} and {mkt2}"

        if language == "te-IN":
            s1 = f"{dist_label_te}లో {mkt1} మార్కెట్లో {date1}న {comm} మోడల్ ధర {p1_str}{u_str}, మరియు {mkt2} మార్కెట్లో {date2}న {p2_str}{u_str}గా నమోదైంది{stale_note}."
        elif language == "hi-IN":
            s1 = f"{dist_label_hi} में {mkt1} मंडी में {date1} को {comm} का मॉडल भाव {p1_str}{u_str}, और {mkt2} मंडी में {date2} को {p2_str}{u_str} दर्ज हुआ{stale_note}।"
        elif language == "hi-en":
            s1 = f"In {dist_label_en}, {comm} modal price was {p1_str}{u_str} in {mkt1} on {date1}, and {p2_str}{u_str} in {mkt2} on {date2}{stale_note}."
        else:
            s1 = f"In {dist_label_en}, the modal price for {comm} was {p1_str}{u_str} in {mkt1} market on {date1}, and {p2_str}{u_str} in {mkt2} market on {date2}{stale_note}."

    reply = f"{intro}{s1} {caveat}".strip()

    # Strictly verify that every cited modal price appears in the reply
    for s_item in selected:
        mp = s_item.data.get("modal_price")
        if mp is not None:
            mp_val = int(mp) if mp == int(mp) else mp
            assert str(mp_val) in reply, f"Verification failed: modal price {mp_val} missing from composed reply"

    return reply
