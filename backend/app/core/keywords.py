"""Keyword definitions and district mappings for intent and slot extraction.

Centralized in core to keep services/ free of script literals and maintain a single
source of truth for recognition lexicons.
"""

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

GREETING_KEYWORDS: set[str] = {
    "hello", "hi", "hey", "namaste", "namaskaram",
    "నమస్కారం", "నమస్తే", "బాగున్నారా", "హలో",
    "नमस्ते", "प्रणाम", "राम राम",
}

PRICE_KEYWORDS: set[str] = {
    "ధర", "రేటు", "ధరలు", "రేట్లు", "మండి", "మార్కెట్",
    "भाव", "दाम", "कीमत", "मंडी", "रेट",
    "price", "rate", "mandi", "cost", "market", "bhav", "dam", "kimat",
}

WEATHER_KEYWORDS: set[str] = {
    # Telugu
    "వర్షం", "వాన", "వాతావరణం", "ఎండ", "చలి", "ఉష్ణోగ్రత", "తుఫాను", "గాలివాన", "వర్షాలు", "నీళ్లు పెట్టాలా",
    # Hindi
    "बारिश", "मौसम", "तापमान", "बरसात", "धूप", "सर्दी", "हवा", "तूफान", "वर्षा", "सिंचाई", "रेन", "इरीगेशन",
    # English / Hinglish
    "weather", "rain", "rainfall", "forecast", "temperature", "mausam", "barish", "barsat", "irrigation",
}

CROP_ADVISORY_KEYWORDS: set[str] = {
    # Telugu
    "పంట", "ఆకులు", "తెగులు", "పురుగు", "మచ్చలు", "సలహా", "పసుపు", "ముడత", "ఎండిపోవడం", "సస్యరక్షణ",
    # Hindi / Hinglish Devanagari
    "फसल", "पत्ते", "रोग", "कीड़ा", "कीड़े", "धब्बे", "बीमारी", "सलाह", "कर्ल", "प्लांट", "पीले", "सूख",
    # English / Hinglish Latin
    "crop", "disease", "pest", "symptom", "leaves", "leaf", "curl", "spots", "yellowing", "advisory", "plant",
}

# Chilli disambiguation tokens
CHILLI_GREEN_TOKENS: set[str] = {
    "పచ్చి", "green", "hari", "1", "పచ్చి మిర్చి", "పచ్చిమిర్చి", "हरी मिर्च", "हरी",
}

CHILLI_DRY_TOKENS: set[str] = {
    "ఎండు", "ఎర్ర", "dry", "red", "sukhi", "lal", "2", "ఎండు మిర్చి", "ఎండుమిర్చి", "सूखी लाल मिर्च", "लाल मिर्च", "सूखी",
}

# Small talk keywords
THANKS_KEYWORDS: set[str] = {
    "thanks", "thank you", "thank", "thx", "dhanyavad", "dhanyavadamulu",
    "ధన్యవాదాలు", "కృతజ్ఞతలు", "థాంక్స్", "థాంక్యూ",
    "धन्यवाद", "शुक्रिया", "थैंक्स", "थैंक यू",
}

OK_KEYWORDS: set[str] = {
    "ok", "okay", "k", "theek", "theek hai", "accha", "acha",
    "సరే", "ఓకే", "బాగుంది",
    "ठीक", "ठीक है", "अच्छा", "ओके",
}

BYE_KEYWORDS: set[str] = {
    "bye", "goodbye", "bye bye", "tata", "alvida",
    "వీడ్కోలు", "టాటా", "వెళ్లొస్తా", "బై",
    "अलविदा", "बाय", "टाटा",
}

CAPABILITIES_KEYWORDS: set[str] = {
    "what can you do", "what all can u help me", "what can u do", "what can you help with",
    "help", "menu", "features", "options", "capabilities",
    "మీరు ఏమి చేయగలరు", "మీరు ఏం సహాయం చేస్తారు", "సహాయం", "మెనూ",
    "आप क्या कर सकते हैं", "आप क्या मदद कर सकते हैं", "मदद", "मेनू", "सुविधाएं",
}

LOCATION_KEYWORDS: set[str] = {
    "what's my location", "what is my location", "where am i", "my location", "location",
    "నా లొకేషన్ ఏమిటి", "నా ప్రాంతం ఏది", "నా జిల్లా ఏది", "లొకేషన్",
    "मेरी लोकेशन क्या है", "मेरा स्थान क्या है", "मेरा जिला कौन सा है", "लोकेशन",
}

# Strict safety rule keywords: weather answers must never claim farm operations are unconditionally 'safe'
FORBIDDEN_SAFETY_WORDS: set[str] = {
    "సురక్షితమైన",
    "सुरक्षित",
}

