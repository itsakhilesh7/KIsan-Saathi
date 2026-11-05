# Kisan Saathi Wording Review (User-Facing Messages)

All user-visible responses and prompts in Kisan Saathi are centralized in [`backend/app/core/messages.py`](file:///C:/Users/akhil/.gemini/antigravity/scratch/kisan-saathi/backend/app/core/messages.py).
This document presents the complete catalog of strings across **Telugu (`te-IN`)**, **Hindi (`hi-IN`)**, **English (`en-IN`)**, and **Hinglish (`hi-en`)** for native-speaker linguistic review, natural phrasing, and tone calibration.

> [!NOTE]
> **Telugu Language Update:** Replaced non-standard `"హవామాన"` with standard Telugu `"వాతావరణ..."` throughout.
> Any phrases where colloquial farmer terminology might differ from standard Telugu have been flagged with `[FLAGGED FOR REVIEW]` below.

---

## 1. Catalog of User-Facing Messages

| Key | Language | Text | Where Used | Reviewer Notes / Flag |
|---|---|---|---|---|
| `mandi_unit` | `te-IN` | `క్వింటాలుకు` | Mandi composer | Standard Telugu for "per quintal". |
| `mandi_unit` | `hi-IN` | `प्रति क्विंटल` | Mandi composer | Standard Hindi for "per quintal". |
| `mandi_unit` | `en-IN` | `per quintal` | Mandi composer | Standard English. |
| `mandi_unit` | `hi-en` | `per quintal` | Mandi composer | Standard Hinglish. |
| `ai_intro` | `te-IN` | `నేను కిసాన్ సాథీ AI సహాయకుడిని. ` | Turn 1 response intro | Stating AI identity upfront. |
| `ai_intro` | `hi-IN` | `मैं किसान साथी AI सहायक हूँ। ` | Turn 1 response intro | Stating AI identity upfront. |
| `ai_intro` | `en-IN` | `I am Kisan Saathi AI assistant. ` | Turn 1 response intro | Stating AI identity upfront. |
| `ai_intro` | `hi-en` | `Main Kisan Saathi AI assistant hoon. ` | Turn 1 response intro | Stating AI identity upfront. |
| `chilli_clarification` | `te-IN` | `మీరు పచ్చి మిర్చి ధర తెలుసుకోవాలనుకుంటున్నారా లేదా ఎండు మిర్చి ధరా?` | Dialogue clarification for ambiguous "మిర్చి" | Disambiguates Green vs Dry Chilli. |
| `chilli_clarification` | `hi-IN` | `क्या आप हरी मिर्च का भाव जानना चाहते हैं या सूखी लाल मिर्च का?` | Dialogue clarification for ambiguous "मिर्च" | Disambiguates Green vs Dry Chilli. |
| `chilli_clarification` | `en-IN` | `Would you like to know the price for Green Chilli or Dry Chillies?` | Dialogue clarification | English clarification. |
| `chilli_clarification` | `hi-en` | `Aap green chilli ka bhav janna chahte hain ya dry red chilli ka?` | Dialogue clarification | Conversational Hinglish. |
| `mandi_missing_commodity` | `te-IN` | `మీరు ఏ పంట లేదా కూరగాయ ధర తెలుసుకోవాలనుకుంటున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.` | Mandi query missing crop | Asks user for specific commodity. |
| `mandi_missing_commodity` | `hi-IN` | `आप किस फसल या सब्जी का भाव जानना चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।` | Mandi query missing crop | Asks user for specific commodity. |
| `mandi_missing_commodity` | `en-IN` | `Which crop or commodity price would you like to know? For example cotton, paddy, chilli, or tomato.` | Mandi query missing crop | English prompt. |
| `mandi_missing_commodity` | `hi-en` | `Aap kis crop ya sabzi ka bhav janna chahte hain? Jaise cotton, paddy, chilli ya tomato.` | Mandi query missing crop | Hinglish prompt. |
| `mandi_no_records` | `te-IN` | `{district}లో {commodity}కి సంబంధించి తాజా మండి రికార్డులు అందుబాటులో లేవు. మరొక జిల్లా లేదా పంటను అడగండి.` | Empty mandi result | Informs user no reported records found. |
| `mandi_no_records` | `hi-IN` | `{district} में {commodity} के लिए कोई ताजा मंडी रिकॉर्ड उपलब्ध नहीं है। कृपया किसी अन्य जिले या फसल का नाम बताएं।` | Empty mandi result | Informs user no reported records found. |
| `mandi_no_records` | `en-IN` | `No recent mandi price records found for {commodity} in {district}. Please try another district or crop.` | Empty mandi result | English message. |
| `mandi_no_records` | `hi-en` | `{district} mein {commodity} ke liye koi recent mandi record nahi mila. Kripya doosra district ya crop batayein.` | Empty mandi result | Hinglish message. |
| `mandi_stale_warning` | `te-IN` | ` (గమనిక: ఈ ధరలు మునుపటి రికార్డు ఆధారంగా ఉన్నాయి)` | Mandi composer | Added when arrival date is older than 3 days. |
| `mandi_stale_warning` | `hi-IN` | ` (ध्यान दें: यह भाव पिछले रिकॉर्ड पर आधारित है)` | Mandi composer | Added when arrival date is older than 3 days. |
| `mandi_stale_warning` | `en-IN` | ` (Note: This price is based on an earlier reported record)` | Mandi composer | Added when arrival date is older than 3 days. |
| `mandi_stale_warning` | `hi-en` | ` (Note: Yeh bhav pehle ke record par based hai)` | Mandi composer | Added when arrival date is older than 3 days. |
| `mandi_cached_note` | `te-IN` | ` (గమనిక: తాజా సమాచారం అందుబాటులో లేనందున, {date} నాటి మునుపటి రికార్డు ప్రకారం)` | Mandi cached fallback | Informs farmer cached date when live API is down. |
| `mandi_cached_note` | `hi-IN` | ` (ध्यान दें: ताजा रिकॉर्ड उपलब्ध न होने से, {date} के पिछले रिकॉर्ड अनुसार)` | Mandi cached fallback | Informs farmer cached date when live API is down. |
| `mandi_cached_note` | `en-IN` | ` (Note: Live record unavailable; showing record from {date})` | Mandi cached fallback | Informs farmer cached date when live API is down. |
| `mandi_cached_note` | `hi-en` | ` (Note: Live record unavailable hone ke karan, {date} ke record ke mutabiq)` | Mandi cached fallback | Informs farmer cached date when live API is down. |
| `mandi_state_fallback` | `te-IN` | `{district} జిల్లాలో రికార్డు లేదు. తెలంగాణ రాష్ట్ర స్థాయి సమాచారం ప్రకారం: ` | Mandi state-level fallback | Explains fallback from district to state level. |
| `mandi_state_fallback` | `hi-IN` | `{district} जिले में रिकॉर्ड नहीं है। तेलंगाना राज्य स्तर की जानकारी के अनुसार: ` | Mandi state-level fallback | Explains fallback from district to state level. |
| `mandi_state_fallback` | `en-IN` | `No record found in {district} district. Showing Telangana state-level reported prices: ` | Mandi state-level fallback | Explains fallback from district to state level. |
| `mandi_state_fallback` | `hi-en` | `{district} district mein record nahi hai. Telangana state-level ke mutabiq: ` | Mandi state-level fallback | Explains fallback from district to state level. |
| `weather_forecast` | `te-IN` | `వాతావరణ అంచనాల ప్రకారం, {district}లో {dates_phrase} ఉష్ణోగ్రత దాదాపు {temp_min}°C నుండి {temp_max}°C వరకు నమోదయ్యే అవకాశం ఉంది. వర్షం పడే అవకాశం గరిష్టంగా {rain_max}%.{rain_note}` | Weather composer | Fixed `"హవామాన"` -> `"వాతావరణ"`. Grounded numbers only. |
| `weather_forecast` | `hi-IN` | `मौसम पूर्वानुमान के अनुसार, {district} में {dates_phrase} तापमान लगभग {temp_min}°C से {temp_max}°C तक रहने की संभावना है। बारिश की संभावना अधिकतम {rain_max}% है।{rain_note}` | Weather composer | Standard Hindi weather statement. |
| `weather_forecast` | `en-IN` | `According to weather forecasts, temperature in {district} over {dates_phrase} is expected between {temp_min}°C and {temp_max}°C. Maximum rain probability is {rain_max}%.{rain_note}` | Weather composer | Standard English forecast. |
| `weather_forecast` | `hi-en` | `Weather forecast ke mutabiq, {district} mein {dates_phrase} temperature lagbhag {temp_min}°C se {temp_max}°C ke beech rahega. Maximum rain probability {rain_max}% hai.{rain_note}` | Weather composer | Conversational Hinglish. |
| `weather_rain_likely` | `te-IN` | ` వర్షం పడే సూచనలు ఉన్నాయి.` | Weather composer | Appended when rain probability $\ge 40\%$. |
| `weather_rain_likely` | `hi-IN` | ` बारिश होने की संभावना है।` | Weather composer | Appended when rain probability $\ge 40\%$. |
| `weather_rain_likely` | `en-IN` | ` Rain is likely.` | Weather composer | Appended when rain probability $\ge 40\%$. |
| `weather_rain_likely` | `hi-en` | ` Rain hone ke chances hain.` | Weather composer | Appended when rain probability $\ge 40\%$. |
| `weather_rain_unlikely` | `te-IN` | ` వర్షం పడే అవకాశం తక్కువ.` | Weather composer | Appended when rain probability $< 40\%$. |
| `weather_rain_unlikely` | `hi-IN` | ` बारिश की संभावना कम है।` | Weather composer | Appended when rain probability $< 40\%$. |
| `weather_rain_unlikely` | `en-IN` | ` Rain is unlikely.` | Weather composer | Appended when rain probability $< 40\%$. |
| `weather_rain_unlikely` | `hi-en` | ` Rain ke chances kam hain.` | Weather composer | Appended when rain probability $< 40\%$. |
| `weather_unavailable` | `te-IN` | `క్షమించండి, {district} కోసం వాతావరణ సమాచారం ప్రస్తుతం అందుబాటులో లేదు.` | Weather connector error | Open-Meteo failure/fallback. |
| `weather_unavailable` | `hi-IN` | `क्षमा करें, {district} के लिए मौसम की जानकारी वर्तमान में उपलब्ध नहीं है।` | Weather connector error | Open-Meteo failure/fallback. |
| `weather_unavailable` | `en-IN` | `Sorry, weather forecast for {district} is currently unavailable.` | Weather connector error | Open-Meteo failure/fallback. |
| `weather_unavailable` | `hi-en` | `Sorry, {district} ke liye weather forecast abhi available nahi hai.` | Weather connector error | Open-Meteo failure/fallback. |
| `unsupported_intent` | `te-IN` | `నేను ప్రస్తుతం తాజా మండి ధరలు మరియు వాతావరణ సమాచారాన్ని మాత్రమే అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.` | Intent classifier fallback | Informs user what features are currently active. |
| `unsupported_intent` | `hi-IN` | `मैं वर्तमान में केवल ताजा मंडी भाव और मौसम की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।` | Intent classifier fallback | Informs user what features are currently active. |
| `unsupported_intent` | `en-IN` | `I can currently help with live mandi prices and weather forecasts. Crop advisory features are coming soon.` | Intent classifier fallback | English fallback. |
| `unsupported_intent` | `hi-en` | `Main abhi live mandi bhav aur mausam forecast provide kar sakta hoon. Crop advisory jald hi aayegi.` | Intent classifier fallback | Hinglish fallback. |
| `empty_transcript` | `te-IN` | `మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి కొంచెం బిగ్గరగా మళ్లీ మాట్లాడండి.` | STT empty transcript | Prompts user to speak louder. |
| `empty_transcript` | `hi-IN` | `आपकी आवाज़ साफ़ सुनाई नहीं दी। कृपया थोड़ा जोर से दोबारा बोलें।` | STT empty transcript | Prompts user to speak louder. |
| `empty_transcript` | `en-IN` | `I couldn't hear your voice clearly. Please speak a little louder and try again.` | STT empty transcript | English prompt. |
| `empty_transcript` | `hi-en` | `Aapki awaaz saaf sunai nahi di. Kripya thoda loud hokar dobara bolein.` | STT empty transcript | Hinglish prompt. |
| `audio_too_long` | `te-IN` | `వాయిస్ నోట్ చాలా పొడవుగా ఉంది. దయచేసి 60 సెకన్ల లోపు మాట్లాడి పంపండి.` | Audio length limit check | Triggered if audio $> 60$s. |
| `audio_too_long` | `hi-IN` | `वॉइस नोट बहुत लंबा है। कृपया 60 सेकंड से कम समय में बोलकर भेजें।` | Audio length limit check | Triggered if audio $> 60$s. |
| `audio_too_long` | `en-IN` | `The voice note is too long. Please send a message under 60 seconds.` | Audio length limit check | English prompt. |
| `audio_too_long` | `hi-en` | `Voice note bahut lamba hai. Kripya 60 seconds se kam mein bolkar bhejein.` | Audio length limit check | Hinglish prompt. |
| `fallback_1551` | `te-IN` | `క్షమించండి, మీ ప్రశ్నకు సమాచారం పొందలేకపోయాను. దయచేసి కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి సహాయం పొందండి.` | Orchestrator/Advisory fallback | Refers user to Kisan Call Centre 1551. |
| `fallback_1551` | `hi-IN` | `क्षमा करें, मुझे इस प्रश्न की सटीक जानकारी नहीं मिली। कृपया किसान कॉल सेंटर 1551 पर कॉल करें।` | Orchestrator/Advisory fallback | Refers user to Kisan Call Centre 1551. |
| `fallback_1551` | `en-IN` | `I'm sorry, I couldn't find information for your query. Please call Kisan Call Centre at 1551 for assistance.` | Orchestrator/Advisory fallback | Refers user to Kisan Call Centre 1551. |
| `fallback_1551` | `hi-en` | `Sorry, mujhe is sawal ki jaankari nahi mili. Kripya Kisan Call Centre 1551 par call karein.` | Orchestrator/Advisory fallback | Refers user to Kisan Call Centre 1551. |
| `crop_advisory_clarification` | `te-IN` | `మీరు ఏ పంట గురించి సలహా అడుగుతున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.` | Advisory clarification | Prompts user when crop is unspecified. |
| `crop_advisory_clarification` | `hi-IN` | `आप किस फसल के बारे में सलाह चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।` | Advisory clarification | Prompts user when crop is unspecified. |
| `crop_advisory_clarification` | `en-IN` | `Which crop are you asking about? For example cotton, paddy, chilli, or tomato.` | Advisory clarification | English prompt. |
| `crop_advisory_clarification` | `hi-en` | `Aap kis crop ke baare mein advisory chahte hain? Jaise cotton, paddy, chilli ya tomato.` | Advisory clarification | Hinglish prompt. |
| `chemical_safety_refusal` | `te-IN` | `రసాయన మందుల పరిమాణం లేదా మోతాదులను నేను నేరుగా సూచించలేను. దయచేసి మందుల లేబుల్‌ను పరిశీలించండి లేదా కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి వ్యవసాయ నిపుణులను సంప్రదించండి.` | Safety dose suppression | `[FLAGGED FOR REVIEW]` Please check if `రసాయన మందుల పరిమాణం లేదా మోతాదులను` is natural for Telangana farmers. |
| `chemical_safety_refusal` | `hi-IN` | `मैं रसायनों या कीटनाशकों की मात्रा और खुराक की सीधे सिफारिश नहीं कर सकता। कृपया उत्पाद के लेबल को पढ़ें या किसान कॉल सेंटर 1551 पर कृषि विशेषज्ञों से संपर्क करें।` | Safety dose suppression | Standard Hindi chemical safety refusal. |
| `chemical_safety_refusal` | `en-IN` | `I cannot provide specific chemical dosages or mixtures. Please check the product label or call Kisan Call Centre at 1551 to consult an agricultural specialist.` | Safety dose suppression | Strict safety rule enforcement. |
| `chemical_safety_refusal` | `hi-en` | `Main chemical dosage ya mixture recommend nahi kar sakta. Kripya product label check karein ya Kisan Call Centre 1551 par call karein.` | Safety dose suppression | Hinglish chemical safety refusal. |
