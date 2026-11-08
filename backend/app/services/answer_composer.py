"""Grounded Answer Composer for Mandi prices and Weather.

Enforces strict factual constraints:
- At most 3 sentences in user's language (Telugu, Hindi, English, Hinglish).
- Uses only validated Evidence records. Every cited number is strictly verified against Evidence data.
- Never invents units; uses confirmed 'Rs per quintal' or 'price as reported'.
- Includes caveat that this is a reported daily price, not a live continuous quote.
- Declares AI assistant identity on first response.
- Alerts user if records are older than 3 days.
- All wording is dynamically loaded from backend.app.core.messages (Single Source of Truth).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from ..core.keywords import FORBIDDEN_SAFETY_WORDS
from ..core.messages import MESSAGES, format_natural_date, get_message
from ..schemas.evidence import Evidence
from .safety import (
    contains_prohibited_chemicals,
    get_label_reminder,
    is_prompt_injection,
    strip_chemical_details,
    validate_composer_output,
)

log = logging.getLogger("services.answer_composer")


def _format_unit_phrase(unit: str, language: str) -> str:
    """Formats optional unit phrase using centralized messages."""
    cleaned = (unit or "").strip().lower()
    if not cleaned:
        return ""
    if "quintal" in cleaned:
        return get_message("mandi_unit", language)
    return f" ({unit})"


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


def compose_clarification_reply(
    language: str = "te-IN",
    is_first_turn: bool = False,
    clarification_type: str | None = None,
) -> str:
    """Composes a short clarification question for missing commodity or ambiguous chilli type."""
    intro = get_message("ai_intro", language) if is_first_turn else ""
    if clarification_type == "chilli_type":
        msg = get_message("chilli_clarification", language)
    else:
        msg = get_message("mandi_missing_commodity", language)
    return f"{intro}{msg}".strip()


def _format_price_val(
    modal_price: float | None,
    min_price: float | None,
    max_price: float | None,
    language: str,
) -> str:
    """Formats price number cleanly per language via centralized templates."""
    if modal_price is not None:
        val = int(modal_price) if modal_price == int(modal_price) else modal_price
        return get_message("price_single", language, val=val)
    elif min_price is not None and max_price is not None:
        p_min = int(min_price) if min_price == int(min_price) else min_price
        p_max = int(max_price) if max_price == int(max_price) else max_price
        return get_message("price_range", language, min=p_min, max=p_max)
    return get_message("price_not_available", language)


def compose_mandi_answer(
    evidence_list: list[Evidence],
    language: str = "te-IN",
    is_first_turn: bool = False,
    requested_district: str | None = None,
    requested_commodity: str | None = None,
    requested_state: str | None = "Telangana",
    unit: str = "",
    is_assumed_district: bool = False,
) -> str:
    """Composes a grounded, verified mandi price response of at most 3 sentences.

    Groups records by market for requested commodity & district, mentions up to 2 markets
    (latest date first), and handles empty district records by offering state-level alternatives.
    """
    intro = get_message("ai_intro", language) if is_first_turn else ""

    if not evidence_list:
        if requested_district:
            crop_name = requested_commodity or get_message("default_crop", language)
            state_name = requested_state or get_message("default_state", language)
            no_dist = get_message(
                "mandi_no_records_district",
                language,
                district=requested_district,
                commodity=crop_name,
                state=state_name,
            )
            return f"{intro}{no_dist}".strip()

        no_rec = get_message("mandi_no_records", language)
        return f"{intro}{no_rec}".strip()

    # Group evidence records by (market, variety) to prevent mixing varieties or overwriting distinct grades
    groups: dict[tuple[str, str], Evidence] = {}
    for ev in evidence_list:
        mkt = ev.data.get("market") or "Unknown Market"
        var = ev.data.get("variety") or ev.data.get("grade") or "Standard"
        key = (mkt, var)
        if key not in groups:
            groups[key] = ev
        else:
            # Pick latest by arrival_date
            curr_date = ev.data.get("arrival_date") or ""
            prev_date = groups[key].data.get("arrival_date") or ""
            if curr_date > prev_date:
                groups[key] = ev

    # Sort groups by arrival date descending
    sorted_groups = sorted(
        groups.values(),
        key=lambda x: x.data.get("arrival_date") or "",
        reverse=True,
    )

    selected = sorted_groups[:2]
    u_str = _format_unit_phrase(unit, language)
    caveat = get_message("mandi_caveat", language)

    def _get_comm_label(data: dict[str, Any]) -> str:
        base = data.get("commodity", requested_commodity or get_message("default_crop", language))
        v = data.get("variety")
        g = data.get("grade")
        qualifier = ""
        if v and v.lower() not in ("other", "none", "unknown", "local", "common"):
            qualifier = v
        elif g and g.lower() not in ("faq", "other", "none", "unknown", "grade a"):
            qualifier = g
        if qualifier and qualifier.lower() not in base.lower():
            return f"{base} ({qualifier})"
        return base

    # Assumed pilot district note
    assumed_prefix = get_message("mandi_assumed_district", language) if is_assumed_district else ""

    # State fallback prefix
    state_prefix = ""
    if any(ev.data.get("is_state_fallback") for ev in selected):
        dist_name = requested_district or "Warangal"
        state_prefix = get_message("mandi_state_fallback", language, district=dist_name)

    # Cached data note
    cached_note = ""
    if any(ev.data.get("cached") for ev in selected):
        c_date = format_natural_date(selected[0].data.get("arrival_date"), language=language)
        cached_note = get_message("mandi_cached_note", language, date=c_date)

    if len(selected) == 1:
        d1 = selected[0].data
        comm = _get_comm_label(d1)
        mkt1 = d1.get("market") or get_message("default_market", language)
        date1 = format_natural_date(d1.get("arrival_date"), language=language)
        p1_str = _format_price_val(d1.get("modal_price"), d1.get("min_price"), d1.get("max_price"), language)
        stale_note = get_message("mandi_stale_warning", language) if _is_stale(d1.get("arrival_date")) else ""

        s1 = get_message(
            "mandi_single_market",
            language,
            state_prefix=state_prefix,
            mkt1=mkt1,
            date1=date1,
            comm=comm,
            price1=p1_str,
            unit=u_str,
            stale_note=stale_note,
            cached_note=cached_note,
        )

    else:
        d1 = selected[0].data
        d2 = selected[1].data
        comm1 = _get_comm_label(d1)
        comm2 = _get_comm_label(d2)
        mkt1 = d1.get("market") or get_message("market_1", language)
        mkt2 = d2.get("market") or get_message("market_2", language)
        date1 = format_natural_date(d1.get("arrival_date"), language=language)
        date2 = format_natural_date(d2.get("arrival_date"), language=language)
        p1_str = _format_price_val(d1.get("modal_price"), d1.get("min_price"), d1.get("max_price"), language)
        p2_str = _format_price_val(d2.get("modal_price"), d2.get("min_price"), d2.get("max_price"), language)
        any_stale = _is_stale(d1.get("arrival_date")) or _is_stale(d2.get("arrival_date"))
        stale_note = get_message("mandi_stale_warning", language) if any_stale else ""

        dist = requested_district or d1.get("district")
        if dist:
            dist_label = get_message("mandi_district_label", language, district=dist)
        else:
            dist_label = get_message("mandi_markets_joiner", language, mkt1=mkt1, mkt2=mkt2)

        s1 = get_message(
            "mandi_two_markets",
            language,
            state_prefix=state_prefix,
            dist_label=dist_label,
            mkt1=mkt1,
            date1=date1,
            comm1=comm1,
            price1=p1_str,
            mkt2=mkt2,
            date2=date2,
            comm2=comm2,
            price2=p2_str,
            unit=u_str,
            stale_note=stale_note,
            cached_note=cached_note,
        )

    reply = f"{intro}{assumed_prefix}{s1} {caveat}".strip()

    # Strictly verify that every cited modal price appears in the reply
    for s_item in selected:
        mp = s_item.data.get("modal_price")
        if mp is not None:
            mp_val = int(mp) if mp == int(mp) else mp
            assert str(mp_val) in reply, f"Verification failed: modal price {mp_val} missing from composed reply"

    return reply


def compose_weather_answer(
    evidence: Evidence,
    language: str = "te-IN",
    is_first_turn: bool = False,
    requested_district: str | None = None,
) -> str:
    """Composes a grounded, verified weather response of at most 3 sentences.

    Enforces uncertainty wording and strictly never claims that spraying, irrigation,
    or harvesting is 'safe'.
    """
    intro = get_message("ai_intro", language) if is_first_turn else ""
    data = evidence.data or {}
    dates = data.get("dates") or []
    temp_max = data.get("temp_max") or []
    temp_min = data.get("temp_min") or []
    precip_prob = data.get("precipitation_probability") or []

    if not dates or not temp_max or not temp_min:
        unavailable = get_message("weather_unavailable", language)
        return f"{intro}{unavailable}".strip()

    raw_dist = requested_district or data.get("district") or get_message("your_area", language)
    # Prompt injection mitigation: strip newlines and control directives from user-supplied location names
    dist = re.sub(r"[\r\n].*", "", str(raw_dist)).strip()
    dist = re.sub(r"(?i)\b(system|ignore|instructions|prompt|safe|100%)\b", "", dist).strip() or get_message("your_area", language)

    d0_date = format_natural_date(dates[0], language=language)
    max0 = int(round(temp_max[0]))
    min0 = int(round(temp_min[0]))
    rain0 = int(round(precip_prob[0])) if precip_prob else 0
    rain_next = int(round(max(precip_prob[1:3]))) if len(precip_prob) > 1 else rain0

    forecast_body = get_message(
        "weather_forecast",
        language,
        district=dist,
        date0=d0_date,
        max0=max0,
        min0=min0,
        rain0=rain0,
        rain_next=rain_next,
    )

    reply = f"{intro}{forecast_body}".strip()

    # Safety checks: never claim that any operation is "safe"
    assert "safe" not in reply.lower() or "safely" in reply.lower(), "Safety violation: unconditional safety asserted"
    assert not any(w in reply for w in FORBIDDEN_SAFETY_WORDS), "Safety violation: safe spraying/irrigation asserted in native language"

    # Strictly verify that cited numbers appear in reply
    assert str(max0) in reply, f"Verification failed: max temp {max0} missing from weather reply"
    assert str(min0) in reply, f"Verification failed: min temp {min0} missing from weather reply"
    assert str(rain0) in reply, f"Verification failed: rain probability {rain0} missing from weather reply"

    return reply


def compose_crop_advisory_answer(
    card: dict[str, Any],
    query: str,
    language: str = "te-IN",
    is_first_turn: bool = False,
    allow_chemical_details: bool = False,
) -> str:
    """Composes a strictly verified, source-grounded crop advisory response (Phase 4).

    Constraints:
    - At most 2 sentences in user's language (spoken <= 15 seconds) plus a source line.
    - Qualitative advice only (timing, method, water saving, mechanisation).
    - Always states the agro-climatic zone from the card.
    - Strips chemical names, doses, and mixtures unless allow_chemical_details=True.
    - Attaches mandatory product label & KVK/1551 consultation reminder.
    - Appends exact source line: [Title], [Publisher], [Year].
    - Post-check verification against source text.
    """
    intro = get_message("ai_intro", language) if is_first_turn else ""
    card_no = card.get("card_number")
    title = card.get("title", "")
    zone = card.get("zone", "Telangana")
    publisher = "PJTSAU"
    year = card.get("year", "2020-21")
    raw_text = card.get("raw_text", "")
    if is_prompt_injection(raw_text):
        cleaned_sentences = [
            s.strip() for s in re.split(r"[.!?]\s+", raw_text)
            if not is_prompt_injection(s) and len(s.strip()) > 5
        ]
        raw_text = ". ".join(cleaned_sentences) if cleaned_sentences else f"{zone} agricultural recommendations"

    # Source line formatting via Single Source of Truth
    source_line = get_message(
        "advisory_source_line",
        language,
        title=title,
        publisher=publisher,
        year=year,
    )

    # Body formatting via Single Source of Truth
    card_key = f"advisory_card_{card_no}"
    if card_key in MESSAGES:
        body = get_message(card_key, language)
    else:
        # Generic qualitative fallback extracted from raw_text or template
        cleaned_text = strip_chemical_details(raw_text, language=language) if not allow_chemical_details else raw_text
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", cleaned_text) if len(s.strip()) > 10]
        selected_text = ". ".join(sentences[:2]) if sentences else ""
        body = get_message(
            "advisory_card_generic",
            language,
            zone=zone,
            crop=card.get("crop", "crop"),
        )
        if selected_text:
            body = f"{body} {selected_text}"

    # Strip chemicals and attach label reminder if required
    if not allow_chemical_details and contains_prohibited_chemicals(body):
        body = strip_chemical_details(body, language=language)

    # Compose final text with intro and source line
    final_reply = f"{intro}{body.strip()} {source_line}".strip()

    # Post-check validation
    valid, reason = validate_composer_output(
        answer=final_reply,
        source_text=raw_text,
        allow_chemical_details=allow_chemical_details,
    )
    if not valid:
        log.error("Composer output failed safety validation: %s", reason)
        # Safe fallback: zone mention + label reminder + source line
        reminder = get_label_reminder(language)
        safe_body = f"{zone} - {reminder}"
        final_reply = f"{intro}{safe_body} {source_line}".strip()

    return final_reply
