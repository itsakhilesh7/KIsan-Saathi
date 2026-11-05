"""Centralized, language-aware user-facing messages across Telugu, Hindi, English, and Hinglish.

All user-visible bot prompts and templates are maintained in this single module for native-speaker
linguistic review, auditability, and safety validation.
"""

from typing import Any

# Supported application languages
SUPPORTED_LANGUAGES = ("te-IN", "hi-IN", "en-IN", "hi-en")

MESSAGES: dict[str, dict[str, str]] = {
    # Mandi price units
    "mandi_unit": {
        "te-IN": "క్వింటాలుకు",
        "hi-IN": "प्रति क्विंटल",
        "en-IN": "per quintal",
        "hi-en": "per quintal",
    },
    # AI assistant self-identification on first turn
    "ai_intro": {
        "te-IN": "నేను కిసాన్ సాథీ AI సహాయకుడిని. ",
        "hi-IN": "मैं किसान साथी AI सहायक हूँ। ",
        "en-IN": "I am Kisan Saathi AI assistant. ",
        "hi-en": "Main Kisan Saathi AI assistant hoon. ",
    },
    # Ambiguous chilli clarification question
    "chilli_clarification": {
        "te-IN": "మీరు పచ్చి మిర్చి ధర తెలుసుకోవాలనుకుంటున్నారా లేదా ఎండు మిర్చి ధరా?",
        "hi-IN": "क्या आप हरी मिर्च का भाव जानना चाहते हैं या सूखी लाल मिर्च का?",
        "en-IN": "Would you like to know the price for Green Chilli or Dry Chillies?",
        "hi-en": "Aap green chilli ka bhav janna chahte hain ya dry red chilli ka?",
    },
    # Missing commodity prompt
    "mandi_missing_commodity": {
        "te-IN": "మీరు ఏ పంట లేదా కూరగాయ ధర తెలుసుకోవాలనుకుంటున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.",
        "hi-IN": "आप किस फसल या सब्जी का भाव जानना चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।",
        "en-IN": "Which crop or commodity price would you like to know? For example cotton, paddy, chilli, or tomato.",
        "hi-en": "Aap kis crop ya sabzi ka bhav janna chahte hain? Jaise cotton, paddy, chilli ya tomato.",
    },
    # No mandi records found
    "mandi_no_records": {
        "te-IN": "{district}లో {commodity}కి సంబంధించి తాజా మండి రికార్డులు అందుబాటులో లేవు. మరొక జిల్లా లేదా పంటను అడగండి.",
        "hi-IN": "{district} में {commodity} के लिए कोई ताजा मंडी रिकॉर्ड उपलब्ध नहीं है। कृपया किसी अन्य जिले या फसल का नाम बताएं।",
        "en-IN": "No recent mandi price records found for {commodity} in {district}. Please try another district or crop.",
        "hi-en": "{district} mein {commodity} ke liye koi recent mandi record nahi mila. Kripya doosra district ya crop batayein.",
    },
    # Mandi stale warning
    "mandi_stale_warning": {
        "te-IN": " (గమనిక: ఈ ధరలు మునుపటి రికార్డు ఆధారంగా ఉన్నాయి)",
        "hi-IN": " (ध्यान दें: यह भाव पिछले रिकॉर्ड पर आधारित है)",
        "en-IN": " (Note: This price is based on an earlier reported record)",
        "hi-en": " (Note: Yeh bhav pehle ke record par based hai)",
    },
    # Mandi cached record disclaimer
    "mandi_cached_note": {
        "te-IN": " (గమనిక: తాజా సమాచారం అందుబాటులో లేనందున, {date} నాటి మునుపటి రికార్డు ప్రకారం)",
        "hi-IN": " (ध्यान दें: ताजा रिकॉर्ड उपलब्ध न होने से, {date} के पिछले रिकॉर्ड अनुसार)",
        "en-IN": " (Note: Live record unavailable; showing record from {date})",
        "hi-en": " (Note: Live record unavailable hone ke karan, {date} ke record ke mutabiq)",
    },
    # Mandi state-level fallback disclaimer
    "mandi_state_fallback": {
        "te-IN": "{district} జిల్లాలో రికార్డు లేదు. తెలంగాణ రాష్ట్ర స్థాయి సమాచారం ప్రకారం: ",
        "hi-IN": "{district} जिले में रिकॉर्ड नहीं है। तेलंगाना राज्य स्तर की जानकारी के अनुसार: ",
        "en-IN": "No record found in {district} district. Showing Telangana state-level reported prices: ",
        "hi-en": "{district} district mein record nahi hai. Telangana state-level ke mutabiq: ",
    },
    # Weather answer template (using standard Telugu 'వాతావరణం' instead of non-standard 'హవామాన')
    "weather_forecast": {
        "te-IN": "వాతావరణ అంచనాల ప్రకారం, {district}లో {dates_phrase} ఉష్ణోగ్రత దాదాపు {temp_min}°C నుండి {temp_max}°C వరకు నమోదయ్యే అవకాశం ఉంది. వర్షం పడే అవకాశం గరిష్టంగా {rain_max}%.{rain_note}",
        "hi-IN": "मौसम पूर्वानुमान के अनुसार, {district} में {dates_phrase} तापमान लगभग {temp_min}°C से {temp_max}°C तक रहने की संभावना है। बारिश की संभावना अधिकतम {rain_max}% है।{rain_note}",
        "en-IN": "According to weather forecasts, temperature in {district} over {dates_phrase} is expected between {temp_min}°C and {temp_max}°C. Maximum rain probability is {rain_max}%.{rain_note}",
        "hi-en": "Weather forecast ke mutabiq, {district} mein {dates_phrase} temperature lagbhag {temp_min}°C se {temp_max}°C ke beech rahega. Maximum rain probability {rain_max}% hai.{rain_note}",
    },
    # Weather rain note
    "weather_rain_likely": {
        "te-IN": " వర్షం పడే సూచనలు ఉన్నాయి.",
        "hi-IN": " बारिश होने की संभावना है।",
        "en-IN": " Rain is likely.",
        "hi-en": " Rain hone ke chances hain.",
    },
    "weather_rain_unlikely": {
        "te-IN": " వర్షం పడే అవకాశం తక్కువ.",
        "hi-IN": " बारिश की संभावना कम है।",
        "en-IN": " Rain is unlikely.",
        "hi-en": " Rain ke chances kam hain.",
    },
    # Weather unavailable
    "weather_unavailable": {
        "te-IN": "క్షమించండి, {district} కోసం వాతావరణ సమాచారం ప్రస్తుతం అందుబాటులో లేదు.",
        "hi-IN": "क्षमा करें, {district} के लिए मौसम की जानकारी वर्तमान में उपलब्ध नहीं है।",
        "en-IN": "Sorry, weather forecast for {district} is currently unavailable.",
        "hi-en": "Sorry, {district} ke liye weather forecast abhi available nahi hai.",
    },
    # Unsupported or unclear intent
    "unsupported_intent": {
        "te-IN": "నేను ప్రస్తుతం తాజా మండి ధరలు మరియు వాతావరణ సమాచారాన్ని మాత్రమే అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.",
        "hi-IN": "मैं वर्तमान में केवल ताजा मंडी भाव और मौसम की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।",
        "en-IN": "I can currently help with live mandi prices and weather forecasts. Crop advisory features are coming soon.",
        "hi-en": "Main abhi live mandi bhav aur mausam forecast provide kar sakta hoon. Crop advisory jald hi aayegi.",
    },
    # Empty voice transcript
    "empty_transcript": {
        "te-IN": "మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి కొంచెం బిగ్గరగా మళ్లీ మాట్లాడండి.",
        "hi-IN": "आपकी आवाज़ साफ़ सुनाई नहीं दी। कृपया थोड़ा जोर से दोबारा बोलें।",
        "en-IN": "I couldn't hear your voice clearly. Please speak a little louder and try again.",
        "hi-en": "Aapki awaaz saaf sunai nahi di. Kripya thoda loud hokar dobara bolein.",
    },
    # Audio exceeding maximum duration limit
    "audio_too_long": {
        "te-IN": "వాయిస్ నోట్ చాలా పొడవుగా ఉంది. దయచేసి 60 సెకన్ల లోపు మాట్లాడి పంపండి.",
        "hi-IN": "वॉइस नोट बहुत लंबा है। कृपया 60 सेकंड से कम समय में बोलकर भेजें।",
        "en-IN": "The voice note is too long. Please send a message under 60 seconds.",
        "hi-en": "Voice note bahut lamba hai. Kripya 60 seconds se kam mein bolkar bhejein.",
    },
    # General fallback to Kisan Call Centre (1551)
    "fallback_1551": {
        "te-IN": "క్షమించండి, మీ ప్రశ్నకు సమాచారం పొందలేకపోయాను. దయచేసి కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి సహాయం పొందండి.",
        "hi-IN": "क्षमा करें, मुझे इस प्रश्न की सटीक जानकारी नहीं मिली। कृपया किसान कॉल सेंटर 1551 पर कॉल करें।",
        "en-IN": "I'm sorry, I couldn't find information for your query. Please call Kisan Call Centre at 1551 for assistance.",
        "hi-en": "Sorry, mujhe is sawal ki jaankari nahi mili. Kripya Kisan Call Centre 1551 par call karein.",
    },
    # Crop advisory missing crop clarification
    "crop_advisory_clarification": {
        "te-IN": "మీరు ఏ పంట గురించి సలహా అడుగుతున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.",
        "hi-IN": "आप किस फसल के बारे में सलाह चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।",
        "en-IN": "Which crop are you asking about? For example cotton, paddy, chilli, or tomato.",
        "hi-en": "Aap kis crop ke baare mein advisory chahte hain? Jaise cotton, paddy, chilli ya tomato.",
    },
    # Chemical dosage refusal notice (Rule 1.1 / Rule 3)
    "chemical_safety_refusal": {
        "te-IN": "రసాయన మందుల పరిమాణం లేదా మోతాదులను నేను నేరుగా సూచించలేను. దయచేసి మందుల లేబుల్‌ను పరిశీలించండి లేదా కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి వ్యవసాయ నిపుణులను సంప్రదించండి.",
        "hi-IN": "मैं रसायनों या कीटनाशकों की मात्रा और खुराक की सीधे सिफारिश नहीं कर सकता। कृपया उत्पाद के लेबल को पढ़ें या किसान कॉल सेंटर 1551 पर कृषि विशेषज्ञों से संपर्क करें।",
        "en-IN": "I cannot provide specific chemical dosages or mixtures. Please check the product label or call Kisan Call Centre at 1551 to consult an agricultural specialist.",
        "hi-en": "Main chemical dosage ya mixture recommend nahi kar sakta. Kripya product label check karein ya Kisan Call Centre 1551 par call karein.",
    },
}


def get_message(key: str, language: str = "te-IN", **kwargs: Any) -> str:
    """Retrieves localized message formatted with keyword arguments.

    Falls back to 'te-IN' if language is unknown, and returns empty string if key is invalid.
    """
    lang_dict = MESSAGES.get(key)
    if not lang_dict:
        return ""

    template = lang_dict.get(language) or lang_dict.get("te-IN") or ""
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
