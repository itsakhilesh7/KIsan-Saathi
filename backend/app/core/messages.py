"""Centralized, language-aware user-facing messages across Telugu, Hindi, English, and Hinglish.

All user-visible bot prompts, templates, and speech conversion lexicons are maintained
in this single module as the absolute Single Source of Truth for native-speaker
linguistic review, auditability, and safety validation.
"""

import re
from datetime import datetime
from typing import Any

# Supported application languages
SUPPORTED_LANGUAGES = ("te-IN", "hi-IN", "en-IN", "hi-en")

MONTH_NAMES: dict[str, dict[int, str]] = {
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

MESSAGES: dict[str, dict[str, str]] = {
    # Mandi price units
    "mandi_unit": {
        "te-IN": " క్వింటాలుకు",
        "hi-IN": " प्रति क्विंटल",
        "en-IN": " per quintal",
        "hi-en": " per quintal",
    },
    # AI assistant self-identification on first turn
    "ai_intro": {
        "te-IN": "నమస్కారం, నేను కిసాన్ సాథీ AI సహాయకుడిని. ",
        "hi-IN": "नमस्ते, मैं किसान साथी AI सहायक हूँ। ",
        "en-IN": "Hello, I am Kisan Saathi, your AI farming assistant. ",
        "hi-en": "Namaste, main Kisan Saathi AI assistant hoon. ",
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
    # Assumed pilot district notice (when user supplies only commodity name)
    "mandi_assumed_district": {
        "te-IN": "వరంగల్ మార్కెట్ ధరలు చూపిస్తున్నాను; మరొక జిల్లా కావాలంటే చెప్పండి: ",
        "hi-IN": "वारंगल मंडी का भाव दिखा रहा हूँ; दूसरा जिला चाहिए तो बताएं: ",
        "en-IN": "Showing Warangal; tell me another district if you want: ",
        "hi-en": "Warangal mandi ka bhav dikha raha hoon; doosra district chahiye toh batayein: ",
    },
    # Mandi district label
    "mandi_district_label": {
        "te-IN": "{district} జిల్లా",
        "hi-IN": "{district} ज़िले",
        "en-IN": "{district} district",
        "hi-en": "{district} district",
    },
    # Mandi markets joiner
    "mandi_markets_joiner": {
        "te-IN": "{mkt1} మరియు {mkt2}",
        "hi-IN": "{mkt1} और {mkt2}",
        "en-IN": "{mkt1} and {mkt2}",
        "hi-en": "{mkt1} and {mkt2}",
    },
    # Mandi single market sentence
    "mandi_single_market": {
        "te-IN": "{state_prefix}{mkt1} మార్కెట్లో {date1} {comm} నివేదించిన మోడల్ ధర {price1}{unit}{stale_note}{cached_note}.",
        "hi-IN": "{state_prefix}{mkt1} मंडी में {date1} {comm} का दर्ज मॉडल मूल्य {price1}{unit}{stale_note}{cached_note} है।",
        "en-IN": "{state_prefix}In {mkt1} market on {date1}, the reported modal price for {comm} was {price1}{unit}{stale_note}{cached_note}.",
        "hi-en": "{state_prefix}{mkt1} mandi me {date1} {comm} ka reported modal price {price1}{unit}{stale_note}{cached_note} hai.",
    },
    # Mandi two markets sentence
    "mandi_two_markets": {
        "te-IN": "{state_prefix}{dist_label}లో {mkt1} మార్కెట్లో {date1} {comm1} మోడల్ ధర {price1}{unit}, మరియు {mkt2} మార్కెట్లో {date2} {comm2} {price2}{unit}గా నమోదైంది{stale_note}{cached_note}.",
        "hi-IN": "{state_prefix}{dist_label} में {mkt1} मंडी में {date1} {comm1} का मॉडल भाव {price1}{unit}, और {mkt2} मंडी में {date2} {comm2} का भाव {price2}{unit} दर्ज हुआ{stale_note}{cached_note}।",
        "en-IN": "{state_prefix}In {dist_label}, reported modal price for {comm1} in {mkt1} on {date1} was {price1}{unit}, and for {comm2} in {mkt2} on {date2} was {price2}{unit}{stale_note}{cached_note}.",
        "hi-en": "{state_prefix}In {dist_label}, {comm1} modal price was {price1}{unit} in {mkt1} on {date1}, and {comm2} was {price2}{unit} in {mkt2} on {date2}{stale_note}{cached_note}.",
    },
    # Mandi caveat sentence indicating reported daily price vs live continuous quote
    "mandi_caveat": {
        "te-IN": "ఇది మార్కెట్ కమిటీ నివేదించిన రోజువారీ ధర, లైవ్ ట్రేడింగ్ కోట్ కాదు.",
        "hi-IN": "यह मंडी समिति द्वारा दर्ज किया गया दैनिक मूल्य है, लाइव ट्रेडिंग कोट नहीं है।",
        "en-IN": "This is the daily price reported by the market committee, not a live trading quote.",
        "hi-en": "Yeh mandi committee ka reported daily price hai, live trading quote nahi hai.",
    },
    # No mandi records found for specific district
    "mandi_no_records_district": {
        "te-IN": "క్షమించండి, {district} జిల్లాలో {commodity}కు సంబంధించి ప్రస్తుత మండి రికార్డులు ఏవీ లభించలేదు. మీరు {state} రాష్ట్రంలోని ఇతర మార్కెట్ల ధరలు తెలుసుకోవాలనుకుంటున్నారా?",
        "hi-IN": "माफ़ कीजिए, {district} ज़िले में {commodity} का कोई हालिया मंडी रिकॉर्ड नहीं मिला। क्या आप {state} राज्य की अन्य मंडियों के भाव जानना चाहते हैं?",
        "en-IN": "Sorry, no recent mandi records were found for {commodity} in {district} district. Would you like prices from across {state} state?",
        "hi-en": "Sorry, {district} district me {commodity} ka koi recent mandi record nahi mila. Kya aap {state} state ki doosri mandiyon ke prices jaanna chahte hain?",
    },
    # No mandi records found general
    "mandi_no_records": {
        "te-IN": "క్షమించండి, మీ ప్రాంతంలో ఈ పంటకు సంబంధించి ప్రస్తుత మండి ధరల రికార్డులు ఏవీ లభించలేదు. దయచేసి సమీప మార్కెట్ లేదా మరొక పంట పేరుతో ప్రయత్నించండి.",
        "hi-IN": "माफ़ कीजिए, आपके क्षेत्र में इस फसल के लिए कोई हालिया मंडी मूल्य रिकॉर्ड नहीं मिला। कृपया नज़दीकी मंडी या दूसरी फसल का नाम बताएं।",
        "en-IN": "Sorry, no recent mandi price records were found for this commodity in your area. Please try asking about a nearby market or a different crop.",
        "hi-en": "Sorry, aapke area me is crop ke liye koi recent mandi price record nahi mila. Please paas ki mandi ya doosri crop try karein.",
    },
    # Mandi staleness warning if > 3 days old
    "mandi_stale_warning": {
        "te-IN": " (గమనిక: ఈ రికార్డు 3 రోజుల కంటే పాతది)",
        "hi-IN": " (ध्यान दें: यह रिकॉर्ड 3 दिन से अधिक पुराना है)",
        "en-IN": " (Note: this record is older than 3 days)",
        "hi-en": " (Note: yeh record 3 din se purana hai)",
    },
    # Mandi cached record disclaimer
    "mandi_cached_note": {
        "te-IN": " (గమనిక: తాజా లైవ్ రికార్డు లభించనందున, {date} నాటి మునుపటి రికార్డు ప్రకారం)",
        "hi-IN": " (ध्यान दें: ताजा रिकॉर्ड न मिलने से, {date} के पिछले रिकॉर्ड अनुसार)",
        "en-IN": " (Note: Latest live record unavailable; showing record from {date})",
        "hi-en": " (Note: Live record unavailable hone se, {date} ke record ke mutabiq)",
    },
    # Mandi state-level fallback disclaimer
    "mandi_state_fallback": {
        "te-IN": "{district} జిల్లాలో రికార్డు లేదు. తెలంగాణ రాష్ట్ర స్థాయి సమాచారం ప్రకారం: ",
        "hi-IN": "{district} जिले में रिकॉर्ड नहीं है। तेलंगाना राज्य स्तर की जानकारी के अनुसार: ",
        "en-IN": "No record found in {district} district. Showing Telangana state-level prices: ",
        "hi-en": "{district} district me record nahi mila. Telangana state-level info ke mutabiq: ",
    },
    # Specific mandi API failure message when service down and cache empty
    "mandi_service_unavailable": {
        "te-IN": "ధరల సేవ ప్రస్తుతం స్పందించడం లేదు, దయచేసి కొన్ని నిమిషాల తర్వాత మళ్లీ ప్రయత్నించండి.",
        "hi-IN": "मंडी भाव सेवा अभी प्रतिक्रिया नहीं दे रही है, कृपया कुछ मिनटों बाद पुनः प्रयास करें।",
        "en-IN": "The price service is not responding right now, please try again in a few minutes.",
        "hi-en": "Price service abhi respond nahi kar rahi hai, kripya kuch minute baad dobara try karein.",
    },
    # Price formatting
    "price_single": {
        "te-IN": "రూపాయలు {val}",
        "hi-IN": "रुपये {val}",
        "en-IN": "Rs {val}",
        "hi-en": "Rs {val}",
    },
    "price_range": {
        "te-IN": "రూపాయలు {min} నుండి {max}",
        "hi-IN": "रुपये {min} से {max}",
        "en-IN": "Rs {min} to {max}",
        "hi-en": "Rs {min} to {max}",
    },
    "price_not_available": {
        "te-IN": "లభ్యం కాలేదు",
        "hi-IN": "उपलब्ध नहीं",
        "en-IN": "not available",
        "hi-en": "available nahi",
    },
    # Generic labels
    "your_area": {
        "te-IN": "మీ ప్రాంతం",
        "hi-IN": "आपका क्षेत्र",
        "en-IN": "your area",
        "hi-en": "aapka area",
    },
    "default_crop": {
        "te-IN": "ఈ పంట",
        "hi-IN": "इस फसल",
        "en-IN": "this crop",
        "hi-en": "is crop",
    },
    "default_state": {
        "te-IN": "తెలంగాణ",
        "hi-IN": "तेलंगाना",
        "en-IN": "Telangana",
        "hi-en": "Telangana",
    },
    "default_market": {
        "te-IN": "మార్కెట్",
        "hi-IN": "मंडी",
        "en-IN": "market",
        "hi-en": "mandi",
    },
    "market_1": {
        "te-IN": "మార్కెట్ 1",
        "hi-IN": "मंडी 1",
        "en-IN": "market 1",
        "hi-en": "mandi 1",
    },
    "market_2": {
        "te-IN": "మార్కెట్ 2",
        "hi-IN": "मंडी 2",
        "en-IN": "market 2",
        "hi-en": "mandi 2",
    },

    # Weather answer template
    "weather_forecast": {
        "te-IN": "వాతావరణ సూచన ప్రకారం, {district}లో {date0} గరిష్ట ఉష్ణోగ్రత {max0}°C, కనిష్ట ఉష్ణోగ్రత {min0}°C గా నమోదయ్యే అవకాశం ఉంది మరియు వర్షం పడే అవకాశం {rain0}% గా ఉంది. రాబోయే రెండు రోజుల్లో వర్షం పడే అవకాశం దాదాపు {rain_next}% వరకు ఉండవచ్చు. వాతావరణ పరిస్థితులను బట్టి మీ వ్యవసాయ పనులను తగిన జాగ్రత్తలతో ప్లాన్ చేసుకోండి.",
        "hi-IN": "मौसम पूर्वानुमान के अनुसार, {district} में {date0} अधिकतम तापमान {max0}°C और न्यूनतम तापमान {min0}°C रहने का अनुमान है, तथा वर्षा की संभावना {rain0}% है। अगले दो दिनों में बारिश की संभावना लगभग {rain_next}% तक रह सकती है। मौसम की स्थिति को देखते हुए अपने कृषि कार्यों की उचित योजना बनाएं।",
        "en-IN": "According to the weather forecast, {district} on {date0} is expected to have a maximum temperature of {max0}°C, a minimum of {min0}°C, and a {rain0}% chance of rain. Over the next two days, the chance of rain may reach approximately {rain_next}%. Please plan your field operations carefully based on local weather conditions.",
        "hi-en": "Weather forecast ke mutabiq, {district} me {date0} maximum temperature {max0}°C aur minimum {min0}°C rehne ka anuman hai, aur rain ke {rain0}% chances hain. Agle do dino me rain ke chances lagbhag {rain_next}% tak ho sakte hain. Mausam ki sthiti ke hisaab se apne kheti ke kamo ko plan karein.",
    },
    # Weather unavailable
    "weather_unavailable": {
        "te-IN": "క్షమించండి, ప్రస్తుతం వాతావరణ సమాచారం అందుబాటులో లేదు. దయచేసి కాసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.",
        "hi-IN": "माफ़ कीजिए, फ़िलहाल मौसम की जानकारी उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें।",
        "en-IN": "Sorry, weather information is currently unavailable. Please try again later.",
        "hi-en": "Sorry, abhi weather information available nahi hai. Please thodi der baad try karein.",
    },
    # Greetings - First turn
    "greeting_first_turn": {
        "te-IN": "నమస్కారం! నేను కిసాన్ సాథీ AI సహాయకుడిని. మీరు నన్ను పంటల మండి ధరల సమాచారం గురించి అడగవచ్చు. మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?",
        "hi-IN": "नमस्ते! मैं किसान साथी AI सहायक हूँ। आप मुझसे फसलों के मंडी भाव की जानकारी पूछ सकते हैं। आप किस फसल का मंडी भाव जानना चाहते हैं?",
        "en-IN": "Hello! I am Kisan Saathi, your AI farming assistant. You can ask me about mandi crop prices. Which crop's mandi price would you like to know?",
        "hi-en": "Namaste! Main Kisan Saathi AI assistant hoon. Aap mujhse mandi crop prices pooch sakte hain. Aap kis crop ka mandi price jaanna chahte hain?",
    },
    # Greetings - Subsequent turn
    "greeting_repeat": {
        "te-IN": "నమస్కారం! మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?",
        "hi-IN": "नमस्ते! आप किस फसल का मंडी भाव जानना चाहते हैं?",
        "en-IN": "Hello! Which crop's mandi price would you like to know?",
        "hi-en": "Namaste! Aap kis crop ka mandi price jaanna chahte hain?",
    },
    # Capabilities list ("what can you do")
    "capabilities_query": {
        "te-IN": "నేను పంటల తాజా మండి ధరలు మరియు 3 రోజుల వాతావరణ సమాచారాన్ని అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.",
        "hi-IN": "मैं फसलों के ताजा मंडी भाव और 3 दिनों के मौसम पूर्वानुमान की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।",
        "en-IN": "I can help with live mandi crop prices and 3-day weather forecasts. Crop advisory features are coming soon.",
        "hi-en": "Main live mandi bhav aur 3 dino ke weather forecast me help kar sakta hoon. Crop advisory jald hi aayegi.",
    },
    # Location query ("what's my location?")
    "location_query": {
        "te-IN": "నాకు మీ లొకేషన్ సమాచారం అందుబాటులో ఉండదు. మీ జిల్లా పేరు చెబితే స్థానిక మండి ధరలు మరియు వాతావరణ సమాచారం తెలుసుకోవచ్చు.",
        "hi-IN": "मेरे पास आपकी लोकेशन की जानकारी नहीं है। कृपया अपने जिले का नाम बताएं ताकि मैं स्थानीय मंडी भाव और मौसम बता सकूं।",
        "en-IN": "I do not have access to your GPS location. Please tell me your district name to get local mandi prices and weather forecasts.",
        "hi-en": "Mere paas aapki location ki jaankari nahi hai. Kripya apna district batayein taaki local mandi bhav aur weather bata sakun.",
    },
    # Small talk: Thanks
    "small_talk_thanks": {
        "te-IN": "ధన్యవాదాలు! ఇంకేదైనా సహాయం కావాలంటే అడగండి.",
        "hi-IN": "आपका स्वागत है! अगर कोई और सहायता चाहिए तो बताएं।",
        "en-IN": "You're welcome! Let me know if you need any other help.",
        "hi-en": "Aapka swagat hai! Koi aur help chahiye toh batayein.",
    },
    # Small talk: OK
    "small_talk_ok": {
        "te-IN": "సరే! ఇంకేదైనా సహాయం కావాలంటే చెప్పండి.",
        "hi-IN": "ठीक है! कोई और सहायता चाहिए तो बताएं।",
        "en-IN": "Okay! Let me know if you need any other help.",
        "hi-en": "Theek hai! Koi aur help chahiye toh batayein.",
    },
    # Small talk: Bye
    "small_talk_bye": {
        "te-IN": "వీడ్కోలు! మీ రోజు శుభప్రదం కావాలి.",
        "hi-IN": "अलविदा! आपका दिन शुभ हो।",
        "en-IN": "Goodbye! Have a good day.",
        "hi-en": "Alvida! Aapka din accha rahe.",
    },
    # Unsupported or unclear intent
    "unsupported_intent": {
        "te-IN": "నేను ప్రస్తుతానికి తాజా మండి ధరల సమాచారాన్ని మరియు వాతావరణ సమాచారాన్ని మాత్రమే అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.",
        "hi-IN": "मैं वर्तमान में केवल ताजा मंडी भाव और मौसम की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।",
        "en-IN": "I can currently help with live mandi prices and weather forecasts. Crop advisory features are coming soon.",
        "hi-en": "Main abhi live mandi bhav aur mausam forecast provide kar sakta hoon. Crop advisory jald hi aayegi.",
    },

    # Empty voice transcript / Audio < 1s
    "empty_transcript": {
        "te-IN": "మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి కొంచెం బిగ్గరగా మళ్లీ మాట్లాడండి.",
        "hi-IN": "आपकी आवाज़ साफ़ सुनाई नहीं दी। कृपया थोड़ा जोर से दोबारा बोलें।",
        "en-IN": "I couldn't hear your voice clearly. Please speak a little louder and try again.",
        "hi-en": "Aapki aawaz saaf sunai nahi di. Kripya thoda loud hokar dobara bolein.",
    },

    # Audio exceeding maximum duration limit
    "audio_too_long": {
        "te-IN": "వాయిస్ నోట్ చాలా పెద్దదిగా ఉంది (పరిమితి దాటింది). దయచేసి చిన్న సందేశాన్ని పంపండి.",
        "hi-IN": "वॉयस नोट बहुत लंबा है (अधिकतम सीमा पार)। कृपया छोटा संदेश भेजें।",
        "en-IN": "Voice note is too long (limit exceeded). Please send a shorter audio message.",
        "hi-en": "Voice note zyada lamba hai (limit exceeded). Please chhota audio message bhejein.",
    },
    # Voice rate limit exceeded (daily per-user or global)
    "voice_limit_reached": {
        "te-IN": "ఈ రోజుకు వాయిస్ డెమో పరిమితి ముగిసింది. దయచేసి రేపు మళ్లీ ప్రయత్నించండి లేదా టెక్స్ట్ మెసేజ్ ద్వారా అడగండి.",
        "hi-IN": "आज के लिए वॉयस डेमो सीमा समाप्त हो गई है। कृपया कल पुनः प्रयास करें या टेक्स्ट संदेश भेजें।",
        "en-IN": "Voice demo limit reached for today. Please try again tomorrow or send a text message.",
        "hi-en": "Aaj ke liye voice demo limit khatam ho gayi hai. Please kal try karein ya text message bhejein.",
    },
    # Unsupported media type
    "unsupported_media": {
        "te-IN": "సహాయం కోసం దయచేసి వాయిస్ సందేశం లేదా టెక్స్ట్ మెసేజ్ పంపండి.",
        "hi-IN": "सहायता के लिए कृपया वॉयस संदेश या टेक्स्ट मैसेज भेजें।",
        "en-IN": "Please send a voice note or a text message for assistance.",
        "hi-en": "Help ke liye please audio voice note ya text message bhejein.",
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

# Speech text replacement maps per language to prevent script mixing in TTS
_SPEECH_MAP_TE: list[tuple[str, str]] = [
    # Districts & pilot markets
    ("Warangal (Grain Market)", "వరంగల్ గింజల మార్కెట్"),
    ("Warangal", "వరంగల్"),
    ("Cherial", "చేర్యాల"),
    ("Khammam", "ఖమ్మం"),
    ("Hyderabad", "హైదరాబాద్"),
    ("Adilabad", "ఆదిలాబాద్"),
    ("Karimnagar", "కరీంనగర్"),
    ("Nalgonda", "నల్గొండ"),
    ("Siddipet", "సిద్దిపేట"),
    ("Mahbubnagar", "మహబూబ్‌నగర్"),
    ("Nirmal", "నిర్మల్"),
    # Commodities
    ("Cotton", "పత్తి"),
    ("Paddy(Dhan)(Common)", "వరి"),
    ("Paddy", "వరి"),
    ("Dry Chillies", "ఎండు మిర్చి"),
    ("Green Chilli", "పచ్చి మిర్చి"),
    ("Chilli", "మిర్చి"),
    ("Tomato", "టమాటా"),
    # Units & symbols
    ("°C", " డిగ్రీల సెల్సియస్"),
    ("%", " శాతం"),
    ("Rs.", "రూపాయలు "),
    ("Rs ", "రూపాయలు "),
    ("Rs", "రూపాయలు "),
]

_SPEECH_MAP_HI: list[tuple[str, str]] = [
    # Districts & pilot markets
    ("Warangal (Grain Market)", "वारंगल अनाज मंडी"),
    ("Warangal", "वारंगल"),
    ("Cherial", "चेरियाल"),
    ("Khammam", "खम्मम"),
    ("Hyderabad", "हैदराबाद"),
    ("Adilabad", "आदिलाबाद"),
    ("Karimnagar", "करीमनगर"),
    ("Nalgonda", "नलगोंडा"),
    ("Siddipet", "सिद्धिपेट"),
    ("Mahbubnagar", "महबूबनगर"),
    ("Nirmal", "निर्मल"),
    # Commodities
    ("Cotton", "कपास"),
    ("Paddy(Dhan)(Common)", "धान"),
    ("Paddy", "धान"),
    ("Dry Chillies", "सूखी लाल मिर्च"),
    ("Green Chilli", "हरी मिर्च"),
    ("Chilli", "मिर्च"),
    ("Tomato", "टमाटर"),
    # Units & symbols
    ("°C", " डिग्री सेल्सियस"),
    ("%", " प्रतिशत"),
    ("Rs.", "रुपये "),
    ("Rs ", "रुपये "),
    ("Rs", "रुपये "),
]

_SPEECH_MAP_EN: list[tuple[str, str]] = [
    ("°C", " degrees Celsius"),
    ("%", " per cent"),
    ("Rs.", "rupees "),
    ("Rs ", "rupees "),
    ("Rs", "rupees "),
]

_SPEECH_MAP_HI_EN: list[tuple[str, str]] = [
    ("°C", " degrees Celsius"),
    ("%", " per cent"),
    ("Rs.", "rupaye "),
    ("Rs ", "rupaye "),
    ("Rs", "rupaye "),
]


def format_natural_date(arrival_iso: str | None, language: str = "te-IN") -> str:
    """Converts ISO arrival date (YYYY-MM-DD) into natural localized date string with embedded postposition.

    - te-IN: 'నవంబర్ 5న'
    - hi-IN: '5 नवंबर को'
    - en-IN: '5 November'
    - hi-en: '5 November ko'
    Never glues a duplicate suffix onto a pre-formatted string.
    """
    if not arrival_iso:
        return ""
    try:
        dt = datetime.strptime(str(arrival_iso).strip()[:10], "%Y-%m-%d")
        month_dict = MONTH_NAMES.get(language, MONTH_NAMES["te-IN"])
        month_name = month_dict.get(dt.month, str(dt.month))
        day = dt.day

        if language == "te-IN":
            return f"{month_name} {day}న"
        elif language == "hi-IN":
            return f"{day} {month_name} को"
        elif language == "hi-en":
            return f"{day} {month_name} ko"
        else:
            return f"{day} {month_name}"
    except (ValueError, TypeError):
        return str(arrival_iso)


def to_speech_text(text: str, language: str = "te-IN") -> str:
    """Translates Latin pilot locations and technical symbols into native-script spoken form for TTS."""
    if not text:
        return ""

    if language == "te-IN":
        res = text
        for pat, repl in _SPEECH_MAP_TE:
            res = re.sub(re.escape(pat), repl, res, flags=re.IGNORECASE)
        # Collapse multiple spaces
        return re.sub(r"\s+", " ", res).strip()

    elif language == "hi-IN":
        res = text
        for pat, repl in _SPEECH_MAP_HI:
            res = re.sub(re.escape(pat), repl, res, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", res).strip()

    elif language == "hi-en":
        res = text
        for pat, repl in _SPEECH_MAP_HI_EN:
            res = re.sub(re.escape(pat), repl, res, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", res).strip()

    else:
        res = text
        for pat, repl in _SPEECH_MAP_EN:
            res = re.sub(re.escape(pat), repl, res, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", res).strip()


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
