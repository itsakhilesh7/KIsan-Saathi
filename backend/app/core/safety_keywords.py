"""Indic and English keyword lists, regexes, and lexicons for agricultural safety checks.

Centralized in core/ to preserve single-source-of-truth and ensure zero Indic
literals drift into backend/app/services/ or channels/.
"""

from __future__ import annotations

import re

# Indic chemical brand & active ingredient names for regex detection
PROHIBITED_CHEMICALS_TELUGU: list[str] = [
    "క్లోర్‌పైరిఫాస్", "మోనోక్రోటోఫాస్", "ఎసిఫేట్", "ఇమిడాక్లోప్రిడ్", "కార్బండజిమ్",
    "మాంకోజెబ్", "గ్లైఫోసేట్", "పెండిమిథాలిన్", "లాంబ్డా", "సైపర్‌మెత్రిన్",
    "డైమిథోయేట్", "క్లోరాంట్రానిలిప్రోల్", "ఫిప్రోనిల్", "థయామెథాక్సమ్", "యూరియా",
    "డిఎపి", "పొటాష్", "జింక్", "బోరాన్", "జిబ్బరెల్లిక్", "2,4-డి", "అట్రాజిన్",
]

PROHIBITED_CHEMICALS_HINDI: list[str] = [
    "क्लोरपायरीफॉस", "मोनोक्रोटोफॉस", "इमिडाक्लोप्रिड", "कार्बेंडाजिम", "मैंकोजेब",
    "ग्लाइफोसेट", "पेंडिमिथालिन", "साइपरमेथ्रिन", "एसीफेट", "डायमेथोएट",
    "क्लोरांट्रानिलिप्रोल", "फिप्रोनिल", "थियामेथॉक्सम", "यूरिया", "डीएपी",
    "पोटाश", "जिंक", "बोरोन",
]

# Known agricultural chemicals (insecticides, fungicides, herbicides, acaricides) in English
PROHIBITED_CHEMICALS_ENGLISH: list[str] = [
    # Organophosphates & Carbamates
    "chlorpyrifos", "monocrotophos", "acephate", "profenofos", "quinalphos",
    "dimethoate", "malathion", "carbofuran", "cartap", "cartap hydrochloride",
    "methomyl", "thiodicarb", "triazophos", "phorate",
    # Neonicotinoids & Modern Insecticides
    "imidacloprid", "thiamethoxam", "acetamiprid", "clothianidin", "dinotefuran",
    "fipronil", "spinosad", "emamectin", "emamectin benzoate", "chlorantraniliprole",
    "flubendiamide", "cyantraniliprole", "indoxacarb", "diafenthiuron",
    # Pyrethroids
    "cypermethrin", "deltamethrin", "lambda-cyhalothrin", "bifenthrin", "permethrin",
    # Fungicides
    "carbendazim", "mancozeb", "copper oxychloride", "hexaconazole", "propiconazole",
    "tebuconazole", "azoxystrobin", "difenoconazole", "metalaxyl", "tricyclazole",
    "validamycin", "kasugamycin", "streptocycline", "captan", "thiram",
    # Herbicides
    "glyphosate", "paraquat", "pendimethalin", "atrazine", "bispyribac",
    "bispyribac sodium", "pretilachlor", "butachlor", "2,4-d", "quizalofop",
    "imazethapyr", "metsulfuron", "glufosinate",
]

ALL_PROHIBITED_CHEMICAL_TOKENS: tuple[str, ...] = tuple(
    PROHIBITED_CHEMICALS_ENGLISH + PROHIBITED_CHEMICALS_TELUGU + PROHIBITED_CHEMICALS_HINDI
)

# Dosage measurement units in Telugu and Devanagari
INDIC_DOSAGE_UNITS: list[str] = [
    "మి\\.లీ", "గ్రాములు", "కిలోలు", "మిలీ", "లీటరుకు", "ఎకరాకు",
    "लीटर", "मिली", "ग्राम", "किलो", "प्रति एकड़",
]

# Regex patterns matching dosage specifications: e.g. "2 ml/l", "500 ml", "500 g/ha", "1.5 kg/acre", "100 ppm"
DOSAGE_PATTERN: re.Pattern = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ml\/l(?:itre)?|g\/l(?:itre)?|kg\/(?:ha|acre)|"
    r"ml\s+per\s+(?:litre|liter|acre)|grams?\s+per\s+(?:litre|liter|acre)|"
    r"kg\s+per\s+(?:hectare|acre)|bags?\s+of\s+(?:urea|dap|potash)|"
    r"ml|g|kg|grams?|litres?|liters?|"
    + "|".join(INDIC_DOSAGE_UNITS) +
    r"|ppm)\b",
    re.IGNORECASE,
)

# Explicit chemical dose indicators across English
DOSE_INDICATORS_EN: tuple[str, ...] = (
    "dose", "dosage", "how much chemical", "how much to spray", "tank mix",
    "cocktail", "mixture", "how many ml", "how many grams", "how much pesticide",
    "how much fertilizer", "spray rate", "mixing ratio",
)

# Indic keywords signaling a request for chemical dose or chemical tank-mix
INDIC_CHEMICAL_DOSE_KEYWORDS: tuple[str, ...] = (
    # Telugu
    "మోతాదు", "ఎంత కొట్టాలి", "ఎంత కలపాలి", "ఎన్ని మిలీ", "ఎంత మందు",
    "రసాయన మోతాదు", "ఎన్ని గ్రాములు", "ట్యాంక్ మిక్స్", "కలిపి కొట్టవచ్చా",
    "కలిపి స్ప్రే", "పురుగుల మందు", "తెగుళ్ల మందు", "కీటకనాశిని",
    # Hindi
    "खुराक", "कितनी मात्रा", "कितना छिड़काव", "कितना मिलाना", "कितना स्प्रे",
    "टैंक मिक्स", "कॉकटेल", "कीटनाशक", "दवा की मात्रा", "दवाई कितनी",
    "कितने मिली", "कितना मिली", "प्रति लीटर",
)

# Diagnosis keywords in English
DIAGNOSIS_KEYWORDS_EN: tuple[str, ...] = (
    "which disease", "what disease", "diagnose", "identify the disease",
    "what sickness", "is it blight", "is it wilt", "is it blast", "what infection",
)

# Indic keywords asking for disease diagnosis from short symptom descriptions
INDIC_DIAGNOSTIC_KEYWORDS: tuple[str, ...] = (
    # Telugu
    "ఏ తెగులు", "ఏ తెగులో", "ఏ రోగం", "ఏ రోగమో", "తెగులు ఏమిటి",
    "రోగం ఏమిటి", "గుర్తించండి", "ఏ వ్యాధి", "వ్యాధి ఏమిటి",
    # Hindi
    "कौन सा रोग", "कौन सी बीमारी", "क्या बीमारी है", "पहचान करें",
    "रोग का नाम", "बीमारी क्या है", "रोग लगा है", "बीमारी लगी है",
)

# Prompt injection markers
PROMPT_INJECTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior|safety)\s+(?:instructions|rules|constraints)?", re.IGNORECASE),
    re.compile(r"system\s+(?:prompt|instruction|directive)", re.IGNORECASE),
    re.compile(r"safety\s+disabled", re.IGNORECASE),
    re.compile(r"reveal\s+(?:your\s+)?(?:secret|instructions|prompt|api\s*key)", re.IGNORECASE),
    re.compile(r"drop\s+table", re.IGNORECASE),
    re.compile(r"print\s+env", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+all\s+safety", re.IGNORECASE),
    # Telugu injection attempts
    re.compile(r"(?:సూచనల.*విస్మరించండి|సిస్టమ్\s*ప్రాంప్ట్|డెవలపర్\s*మోడ్|రద్దు\s*చేసి)", re.IGNORECASE),
    # Hindi injection attempts
    re.compile(r"(?:नियम.*भूल\s*जाओ|सिस्टम\s*प्रॉम्प्ट|डेवलपर\s*मोड|बायपास)", re.IGNORECASE),
)

# Off-topic categories (medical, legal)
OFF_TOPIC_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:doctor|hospital|chest\s*pain|headache|paracetamol|aspirin|ibuprofen|cancer|stomach\s*pain)\b", re.IGNORECASE),
    re.compile(r"\b(?:lawsuit|lawyer|sue\s+my|court\s*case|fir\s+against|bail|police\s*complaint)\b", re.IGNORECASE),
    # Indic matches without \b
    re.compile(r"(?:గుండె\s*నొప్పి|ఛాతీలో\s*మంట|తల\s*నొప్పి|ఆసుపత్రి|మందుల\s*బిళ్ళ|పారాసిటమాల్|కోర్టు\s*కేసు|కోర్టులో\s*కేసు|లాయర్|భూ\s*వివాదం|పోలీస్)", re.IGNORECASE),
    re.compile(r"(?:सिरदर्द|सीने\s*में\s*दर्द|अस्पताल|बुखार|गोली|मुकदमा|वकील|पुलिस|एफआईआर|कोर्ट\s*केस)", re.IGNORECASE),
)

# Crop synonyms for offline test similarity matching
INDIC_CROP_SYNONYMS: dict[str, str] = {
    "వరి": "paddy rice",
    "నేరుగా": "direct",
    "విత్తే": "seeded sowing",
    "సాగు": "cultivation",
    "పత్తి": "cotton",
    "యంత్ర": "mechanisation machinery",
    "కలుపు": "weed",
    "తెగులు": "disease protection",
    "వరిచేను": "paddy rice field",
    "ధాన్": "paddy rice",
    "चावल": "paddy rice",
    "कपास": "cotton",
    "बुवाई": "sowing seeded",
    "रोपाई": "transplanting",
}
