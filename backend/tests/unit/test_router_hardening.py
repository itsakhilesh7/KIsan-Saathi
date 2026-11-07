"""Reproduction and hardening unit tests for Intent Router and Keyword matching.

Failing test cases before fixes:
1. 'नमस्ते' is treated as BYE because it's present in BYE_KEYWORDS and small talk runs early.
2. Substring matching causes:
   - 'Can you help me with tomato price' -> treated as CAPABILITIES_QUERY ('help' substring).
   - 'weather at my location' -> treated as LOCATION_QUERY ('location' substring).
   - 'thank you, what is the cotton price' -> treated as SMALL_TALK thanks ('thank you' prefix).
   - 'which crop' and 'this' -> treated as GREETING_OR_HELP ('hi' substring in 'which'/'this').
3. Chilli clarification follow-up matches substrings:
   - 'I want 10 day weather forecast' -> matches '1' in CHILLI_GREEN_TOKENS and becomes Green Chilli.
"""

import pytest

from backend.app.repositories.dialogue_state import DialogueStateRepository
from backend.app.schemas.intent import IntentType
from backend.app.services.intent_service import extract_intent


def test_namaste_is_greeting_not_bye():
    """'नमस्ते' must be recognized as GREETING_OR_HELP, never as BYE."""
    res = extract_intent("नमस्ते", language="hi-IN")
    assert res.intent == IntentType.GREETING_OR_HELP, f"Expected GREETING_OR_HELP, got {res.intent} (small_talk_type={res.small_talk_type})"


def test_can_you_help_me_with_tomato_price_is_mandi():
    """'Can you help me with tomato price' has a commodity and price intent, so it must win over capabilities."""
    res = extract_intent("Can you help me with tomato price", language="en-IN")
    assert res.intent == IntentType.MANDI_PRICE_QUERY
    assert res.slots.commodity == "Tomato"


def test_weather_at_my_location_is_weather():
    """'weather at my location' is a weather query, not a location query."""
    res = extract_intent("weather at my location", language="en-IN")
    assert res.intent == IntentType.WEATHER_QUERY


def test_thank_you_what_is_cotton_price_is_mandi():
    """'thank you, what is the cotton price' must route to cotton mandi price, not small talk thanks."""
    res = extract_intent("thank you, what is the cotton price", language="en-IN")
    assert res.intent == IntentType.MANDI_PRICE_QUERY
    assert res.slots.commodity == "Cotton"


def test_which_crop_and_this_do_not_trigger_greeting_via_hi_substring():
    """'which crop' and 'this' must not trigger greeting due to 'hi' being a substring."""
    res_which = extract_intent("which crop", language="en-IN")
    assert res_which.intent != IntentType.GREETING_OR_HELP

    res_this = extract_intent("this is not working", language="en-IN")
    assert res_this.intent != IntentType.GREETING_OR_HELP


def test_chilli_follow_up_requires_exact_short_answer(tmp_path):
    """During chilli disambiguation, only exact short tokens resolve to green/dry chilli.

    Unrelated queries (e.g. weather forecast containing '1') must be treated as a new query.
    """
    db_path = str(tmp_path / "test_dialogue.sqlite3")
    repo = DialogueStateRepository(db_path=db_path)
    user_hash = "test_user_chilli"
    repo.set_state(
        user_hash,
        {
            "intent": IntentType.MANDI_PRICE_QUERY,
            "clarification_type": "chilli_type",
            "slots": {"district": "Warangal"},
        },
    )

    # 1. Exact answer '1' resolves to Green Chilli
    res_exact = extract_intent("1", language="en-IN", user_hash=user_hash, dialogue_repo=repo)
    assert res_exact.intent == IntentType.MANDI_PRICE_QUERY
    assert res_exact.slots.commodity == "Green Chilli"

    # Reset state for next check
    repo.set_state(
        user_hash,
        {
            "intent": IntentType.MANDI_PRICE_QUERY,
            "clarification_type": "chilli_type",
            "slots": {"district": "Warangal"},
        },
    )

    # 2. Query containing '1' but asking weather must route to weather, NOT green chilli
    res_weather = extract_intent("I want 10 day weather forecast", language="en-IN", user_hash=user_hash, dialogue_repo=repo)
    assert res_weather.intent == IntentType.WEATHER_QUERY
    assert res_weather.slots.commodity != "Green Chilli"


TABLE_DRIVEN_CASES = [
    # ------------------ Telugu (te-IN) ------------------
    # Greetings
    ("నమస్కారం", "te-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("నమస్తే", "te-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("హలో బాగున్నారా", "te-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    # Mandi with commodity & district
    ("వరంగల్‌లో పత్తి ధర ఎంత?", "te-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("ఖమ్మం మార్కెట్లో టమాటా రేటు చెప్పండి", "te-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Khammam", False, None, None),
    ("వరి ధర ఎంత?", "te-IN", IntentType.MANDI_PRICE_QUERY, "Paddy(Common)", "Warangal", False, None, None),
    ("మిర్చి ధర ఎంత", "te-IN", IntentType.MANDI_PRICE_QUERY, None, None, True, "chilli_type", None),
    ("పచ్చి మిర్చి ధర ఎంత", "te-IN", IntentType.MANDI_PRICE_QUERY, "Green Chilli", "Warangal", False, None, None),
    ("ఎండు మిర్చి రేటు ఎంత", "te-IN", IntentType.MANDI_PRICE_QUERY, "Dry Chillies", "Warangal", False, None, None),
    ("టమాటా", "te-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    ("పత్తి", "te-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    # Weather
    ("రేపు వరంగల్‌లో వర్షం పడుతుందా?", "te-IN", IntentType.WEATHER_QUERY, None, "Warangal", False, None, None),
    ("ఖమ్మం వాతావరణం ఎలా ఉంది?", "te-IN", IntentType.WEATHER_QUERY, None, "Khammam", False, None, None),
    ("ఈ రోజు వాతావరణం చెప్పండి", "te-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    ("నా ప్రాంతంలో వర్షం వస్తుందా", "te-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    # Small talk / Capabilities / Location
    ("ధన్యవాదాలు", "te-IN", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("సరే", "te-IN", IntentType.SMALL_TALK, None, None, False, None, "ok"),
    ("వీడ్కోలు", "te-IN", IntentType.SMALL_TALK, None, None, False, None, "bye"),
    ("మీరు ఏమి చేయగలరు", "te-IN", IntentType.CAPABILITIES_QUERY, None, None, False, None, None),
    ("నా లొకేషన్ ఏమిటి", "te-IN", IntentType.LOCATION_QUERY, None, None, False, None, None),

    # ------------------ Hindi (hi-IN) ------------------
    # Greetings
    ("नमस्ते", "hi-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("प्रणाम", "hi-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("राम राम", "hi-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    # Mandi
    ("वारंगल में कपास का भाव क्या है?", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("टमाटर का दाम बताओ", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    ("धान की कीमत कितनी है?", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Paddy(Common)", "Warangal", False, None, None),
    ("मिर्च का भाव", "hi-IN", IntentType.MANDI_PRICE_QUERY, None, None, True, "chilli_type", None),
    ("हरी मिर्च का भाव क्या है?", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Green Chilli", "Warangal", False, None, None),
    ("सूखी लाल मिर्च का भाव बताओ", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Dry Chillies", "Warangal", False, None, None),
    ("कपास", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("टमाटर", "hi-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    # Weather
    ("वारंगल में कल बारिश होगी क्या?", "hi-IN", IntentType.WEATHER_QUERY, None, "Warangal", False, None, None),
    ("आज का मौसम कैसा रहेगा?", "hi-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    ("खम्मम का तापमान क्या है?", "hi-IN", IntentType.WEATHER_QUERY, None, "Khammam", False, None, None),
    ("मेरी लोकेशन का मौसम बताओ", "hi-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    # Small talk / Capabilities / Location
    ("धन्यवाद", "hi-IN", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("शुक्रिया", "hi-IN", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("ठीक है", "hi-IN", IntentType.SMALL_TALK, None, None, False, None, "ok"),
    ("अलविदा", "hi-IN", IntentType.SMALL_TALK, None, None, False, None, "bye"),
    ("आप क्या कर सकते हैं", "hi-IN", IntentType.CAPABILITIES_QUERY, None, None, False, None, None),
    ("मेरी लोकेशन क्या है", "hi-IN", IntentType.LOCATION_QUERY, None, None, False, None, None),

    # ------------------ English (en-IN) ------------------
    # Greetings
    ("Hi", "en-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("Hello", "en-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("Hey", "en-IN", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    # Mandi
    ("What is the price of cotton in Warangal?", "en-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("Tell me the price of cotton", "en-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("Can you help me with tomato price", "en-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    ("thank you, what is the cotton price", "en-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("paddy rate", "en-IN", IntentType.MANDI_PRICE_QUERY, "Paddy(Common)", "Warangal", False, None, None),
    ("chilli price", "en-IN", IntentType.MANDI_PRICE_QUERY, None, None, True, "chilli_type", None),
    ("green chilli price", "en-IN", IntentType.MANDI_PRICE_QUERY, "Green Chilli", "Warangal", False, None, None),
    ("dry chilli rate", "en-IN", IntentType.MANDI_PRICE_QUERY, "Dry Chillies", "Warangal", False, None, None),
    ("Tomato", "en-IN", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    ("Cotton", "en-IN", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    # Weather
    ("What is the weather forecast for Warangal?", "en-IN", IntentType.WEATHER_QUERY, None, "Warangal", False, None, None),
    ("Will it rain tomorrow in Khammam?", "en-IN", IntentType.WEATHER_QUERY, None, "Khammam", False, None, None),
    ("weather at my location", "en-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    ("is it going to rain", "en-IN", IntentType.WEATHER_QUERY, None, None, False, None, None),
    # Small talk / Capabilities / Location
    ("Thank you", "en-IN", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("Thanks a lot", "en-IN", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("Ok", "en-IN", IntentType.SMALL_TALK, None, None, False, None, "ok"),
    ("Okay", "en-IN", IntentType.SMALL_TALK, None, None, False, None, "ok"),
    ("Bye", "en-IN", IntentType.SMALL_TALK, None, None, False, None, "bye"),
    ("What can you do", "en-IN", IntentType.CAPABILITIES_QUERY, None, None, False, None, None),
    ("What all can u help me", "en-IN", IntentType.CAPABILITIES_QUERY, None, None, False, None, None),
    ("What's my location", "en-IN", IntentType.LOCATION_QUERY, None, None, False, None, None),
    # Non-greeting / edge cases
    ("which crop", "en-IN", IntentType.UNSUPPORTED_OR_UNCLEAR, None, None, False, None, None),
    ("this is not working", "en-IN", IntentType.UNSUPPORTED_OR_UNCLEAR, None, None, False, None, None),

    # ------------------ Hinglish (hi-en) ------------------
    ("Namaste", "hi-en", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("Hello ji", "hi-en", IntentType.GREETING_OR_HELP, None, None, False, None, None),
    ("Warangal mein cotton ka rate kya hai", "hi-en", IntentType.MANDI_PRICE_QUERY, "Cotton", "Warangal", False, None, None),
    ("Tomato ka price batao", "hi-en", IntentType.MANDI_PRICE_QUERY, "Tomato", "Warangal", False, None, None),
    ("Khammam mandi mein paddy ka bhav", "hi-en", IntentType.MANDI_PRICE_QUERY, "Paddy(Common)", "Khammam", False, None, None),
    ("Mirchi ka dam kya hai", "hi-en", IntentType.MANDI_PRICE_QUERY, None, None, True, "chilli_type", None),
    ("Green chilli ka rate", "hi-en", IntentType.MANDI_PRICE_QUERY, "Green Chilli", "Warangal", False, None, None),
    ("Sukhi lal mirch ka bhav", "hi-en", IntentType.MANDI_PRICE_QUERY, "Dry Chillies", "Warangal", False, None, None),
    ("Warangal mein kal barish hogi kya", "hi-en", IntentType.WEATHER_QUERY, None, "Warangal", False, None, None),
    ("Aaj ka mausam kaisa hai", "hi-en", IntentType.WEATHER_QUERY, None, None, False, None, None),
    ("Meri location pe rain hogi kya", "hi-en", IntentType.WEATHER_QUERY, None, None, False, None, None),
    ("Dhanyavad", "hi-en", IntentType.SMALL_TALK, None, None, False, None, "thanks"),
    ("Theek hai", "hi-en", IntentType.SMALL_TALK, None, None, False, None, "ok"),
    ("Alvida", "hi-en", IntentType.SMALL_TALK, None, None, False, None, "bye"),
    ("Aap kya help kar sakte ho", "hi-en", IntentType.CAPABILITIES_QUERY, None, None, False, None, None),
    ("Mera location kya hai", "hi-en", IntentType.LOCATION_QUERY, None, None, False, None, None),
]


@pytest.mark.parametrize(
    "utterance,expected_lang,expected_intent,expected_commodity,expected_district,expected_clarification,expected_clarification_type,expected_small_talk",
    TABLE_DRIVEN_CASES,
)
def test_realistic_utterances_table_driven(
    utterance: str,
    expected_lang: str,
    expected_intent: IntentType,
    expected_commodity: str | None,
    expected_district: str | None,
    expected_clarification: bool,
    expected_clarification_type: str | None,
    expected_small_talk: str | None,
):
    """Table-driven test validating > 50 realistic utterances across te, hi, en, and hi-en."""
    res = extract_intent(utterance, language=expected_lang)
    assert res.intent == expected_intent, f"Utterance '{utterance}' ({expected_lang}): expected intent {expected_intent}, got {res.intent}"

    if expected_commodity is not None:
        assert res.slots.commodity == expected_commodity, f"Utterance '{utterance}': expected commodity {expected_commodity}, got {res.slots.commodity}"

    if expected_district is not None:
        assert res.slots.district == expected_district, f"Utterance '{utterance}': expected district {expected_district}, got {res.slots.district}"

    assert res.clarification_needed == expected_clarification, (
        f"Utterance '{utterance}': expected clarification_needed={expected_clarification}, got {res.clarification_needed}"
    )

    if expected_clarification_type is not None:
        assert res.clarification_type == expected_clarification_type, (
            f"Utterance '{utterance}': expected clarification_type={expected_clarification_type}, got {res.clarification_type}"
        )

    if expected_small_talk is not None:
        assert res.small_talk_type == expected_small_talk, (
            f"Utterance '{utterance}': expected small_talk_type={expected_small_talk}, got {res.small_talk_type}"
        )

