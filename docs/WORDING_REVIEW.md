# Kisan Saathi Wording Review (User-Facing Messages)

All user-visible responses and prompts in Kisan Saathi are centralized in [`backend/app/core/messages.py`](file:///C:/Users/akhil/.gemini/antigravity/scratch/kisan-saathi/backend/app/core/messages.py).
This document presents the complete catalog of strings across **Telugu (`te-IN`)**, **Hindi (`hi-IN`)**, **English (`en-IN`)**, and **Hinglish (`hi-en`)** for native-speaker linguistic review, natural phrasing, and tone calibration.

> [!NOTE]
> **Single Source of Truth Enforced:** This document is auto-generated directly from `backend/app/core/messages.py` via `backend/scripts/generate_wording_review.py`.
> All changes must be made directly in `messages.py`.

---

## 1. Catalog of User-Facing Messages

| Key | Language | Text | Context / Purpose |
|---|---|---|---|
| `ai_intro` | `te-IN` | `నమస్కారం, నేను కిసాన్ సాథీ AI సహాయకుడిని.` | Centralized template `ai_intro` |
| `ai_intro` | `hi-IN` | `नमस्ते, मैं किसान साथी AI सहायक हूँ।` | Centralized template `ai_intro` |
| `ai_intro` | `en-IN` | `Hello, I am Kisan Saathi, your AI farming assistant.` | Centralized template `ai_intro` |
| `ai_intro` | `hi-en` | `Namaste, main Kisan Saathi AI assistant hoon.` | Centralized template `ai_intro` |
| `audio_too_long` | `te-IN` | `వాయిస్ నోట్ చాలా పెద్దదిగా ఉంది (పరిమితి దాటింది). దయచేసి చిన్న సందేశాన్ని పంపండి.` | Centralized template `audio_too_long` |
| `audio_too_long` | `hi-IN` | `वॉयस नोट बहुत लंबा है (अधिकतम सीमा पार)। कृपया छोटा संदेश भेजें।` | Centralized template `audio_too_long` |
| `audio_too_long` | `en-IN` | `Voice note is too long (limit exceeded). Please send a shorter audio message.` | Centralized template `audio_too_long` |
| `audio_too_long` | `hi-en` | `Voice note zyada lamba hai (limit exceeded). Please chhota audio message bhejein.` | Centralized template `audio_too_long` |
| `capabilities_query` | `te-IN` | `నేను పంటల తాజా మండి ధరలు మరియు 3 రోజుల వాతావరణ సమాచారాన్ని అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.` | Centralized template `capabilities_query` |
| `capabilities_query` | `hi-IN` | `मैं फसलों के ताजा मंडी भाव और 3 दिनों के मौसम पूर्वानुमान की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।` | Centralized template `capabilities_query` |
| `capabilities_query` | `en-IN` | `I can help with live mandi crop prices and 3-day weather forecasts. Crop advisory features are coming soon.` | Centralized template `capabilities_query` |
| `capabilities_query` | `hi-en` | `Main live mandi bhav aur 3 dino ke weather forecast me help kar sakta hoon. Crop advisory jald hi aayegi.` | Centralized template `capabilities_query` |
| `chemical_safety_refusal` | `te-IN` | `రసాయన మందుల పరిమాణం లేదా మోతాదులను నేను నేరుగా సూచించలేను. దయచేసి మందుల లేబుల్‌ను పరిశీలించండి లేదా కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి వ్యవసాయ నిపుణులను సంప్రదించండి.` | Centralized template `chemical_safety_refusal` |
| `chemical_safety_refusal` | `hi-IN` | `मैं रसायनों या कीटनाशकों की मात्रा और खुराक की सीधे सिफारिश नहीं कर सकता। कृपया उत्पाद के लेबल को पढ़ें या किसान कॉल सेंटर 1551 पर कृषि विशेषज्ञों से संपर्क करें।` | Centralized template `chemical_safety_refusal` |
| `chemical_safety_refusal` | `en-IN` | `I cannot provide specific chemical dosages or mixtures. Please check the product label or call Kisan Call Centre at 1551 to consult an agricultural specialist.` | Centralized template `chemical_safety_refusal` |
| `chemical_safety_refusal` | `hi-en` | `Main chemical dosage ya mixture recommend nahi kar sakta. Kripya product label check karein ya Kisan Call Centre 1551 par call karein.` | Centralized template `chemical_safety_refusal` |
| `chilli_clarification` | `te-IN` | `మీరు పచ్చి మిర్చి ధర తెలుసుకోవాలనుకుంటున్నారా లేదా ఎండు మిర్చి ధరా?` | Centralized template `chilli_clarification` |
| `chilli_clarification` | `hi-IN` | `क्या आप हरी मिर्च का भाव जानना चाहते हैं या सूखी लाल मिर्च का?` | Centralized template `chilli_clarification` |
| `chilli_clarification` | `en-IN` | `Would you like to know the price for Green Chilli or Dry Chillies?` | Centralized template `chilli_clarification` |
| `chilli_clarification` | `hi-en` | `Aap green chilli ka bhav janna chahte hain ya dry red chilli ka?` | Centralized template `chilli_clarification` |
| `crop_advisory_clarification` | `te-IN` | `మీరు ఏ పంట గురించి సలహా అడుగుతున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.` | Centralized template `crop_advisory_clarification` |
| `crop_advisory_clarification` | `hi-IN` | `आप किस फसल के बारे में सलाह चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।` | Centralized template `crop_advisory_clarification` |
| `crop_advisory_clarification` | `en-IN` | `Which crop are you asking about? For example cotton, paddy, chilli, or tomato.` | Centralized template `crop_advisory_clarification` |
| `crop_advisory_clarification` | `hi-en` | `Aap kis crop ke baare mein advisory chahte hain? Jaise cotton, paddy, chilli ya tomato.` | Centralized template `crop_advisory_clarification` |
| `default_crop` | `te-IN` | `ఈ పంట` | Centralized template `default_crop` |
| `default_crop` | `hi-IN` | `इस फसल` | Centralized template `default_crop` |
| `default_crop` | `en-IN` | `this crop` | Centralized template `default_crop` |
| `default_crop` | `hi-en` | `is crop` | Centralized template `default_crop` |
| `default_market` | `te-IN` | `మార్కెట్` | Centralized template `default_market` |
| `default_market` | `hi-IN` | `मंडी` | Centralized template `default_market` |
| `default_market` | `en-IN` | `market` | Centralized template `default_market` |
| `default_market` | `hi-en` | `mandi` | Centralized template `default_market` |
| `default_state` | `te-IN` | `తెలంగాణ` | Centralized template `default_state` |
| `default_state` | `hi-IN` | `तेलंगाना` | Centralized template `default_state` |
| `default_state` | `en-IN` | `Telangana` | Centralized template `default_state` |
| `default_state` | `hi-en` | `Telangana` | Centralized template `default_state` |
| `empty_transcript` | `te-IN` | `మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి కొంచెం బిగ్గరగా మళ్లీ మాట్లాడండి.` | Centralized template `empty_transcript` |
| `empty_transcript` | `hi-IN` | `आपकी आवाज़ साफ़ सुनाई नहीं दी। कृपया थोड़ा जोर से दोबारा बोलें।` | Centralized template `empty_transcript` |
| `empty_transcript` | `en-IN` | `I couldn't hear your voice clearly. Please speak a little louder and try again.` | Centralized template `empty_transcript` |
| `empty_transcript` | `hi-en` | `Aapki aawaz saaf sunai nahi di. Kripya thoda loud hokar dobara bolein.` | Centralized template `empty_transcript` |
| `fallback_1551` | `te-IN` | `క్షమించండి, మీ ప్రశ్నకు సమాచారం పొందలేకపోయాను. దయచేసి కిసాన్ కాల్ సెంటర్ 1551 కి కాల్ చేసి సహాయం పొందండి.` | Centralized template `fallback_1551` |
| `fallback_1551` | `hi-IN` | `क्षमा करें, मुझे इस प्रश्न की सटीक जानकारी नहीं मिली। कृपया किसान कॉल सेंटर 1551 पर कॉल करें।` | Centralized template `fallback_1551` |
| `fallback_1551` | `en-IN` | `I'm sorry, I couldn't find information for your query. Please call Kisan Call Centre at 1551 for assistance.` | Centralized template `fallback_1551` |
| `fallback_1551` | `hi-en` | `Sorry, mujhe is sawal ki jaankari nahi mili. Kripya Kisan Call Centre 1551 par call karein.` | Centralized template `fallback_1551` |
| `greeting_first_turn` | `te-IN` | `నమస్కారం! నేను కిసాన్ సాథీ AI సహాయకుడిని. మీరు నన్ను పంటల మండి ధరల సమాచారం గురించి అడగవచ్చు. మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?` | Centralized template `greeting_first_turn` |
| `greeting_first_turn` | `hi-IN` | `नमस्ते! मैं किसान साथी AI सहायक हूँ। आप मुझसे फसलों के मंडी भाव की जानकारी पूछ सकते हैं। आप किस फसल का मंडी भाव जानना चाहते हैं?` | Centralized template `greeting_first_turn` |
| `greeting_first_turn` | `en-IN` | `Hello! I am Kisan Saathi, your AI farming assistant. You can ask me about mandi crop prices. Which crop's mandi price would you like to know?` | Centralized template `greeting_first_turn` |
| `greeting_first_turn` | `hi-en` | `Namaste! Main Kisan Saathi AI assistant hoon. Aap mujhse mandi crop prices pooch sakte hain. Aap kis crop ka mandi price jaanna chahte hain?` | Centralized template `greeting_first_turn` |
| `greeting_repeat` | `te-IN` | `నమస్కారం! మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?` | Centralized template `greeting_repeat` |
| `greeting_repeat` | `hi-IN` | `नमस्ते! आप किस फसल का मंडी भाव जानना चाहते हैं?` | Centralized template `greeting_repeat` |
| `greeting_repeat` | `en-IN` | `Hello! Which crop's mandi price would you like to know?` | Centralized template `greeting_repeat` |
| `greeting_repeat` | `hi-en` | `Namaste! Aap kis crop ka mandi price jaanna chahte hain?` | Centralized template `greeting_repeat` |
| `location_query` | `te-IN` | `నాకు మీ లొకేషన్ సమాచారం అందుబాటులో ఉండదు. మీ జిల్లా పేరు చెబితే స్థానిక మండి ధరలు మరియు వాతావరణ సమాచారం తెలుసుకోవచ్చు.` | Centralized template `location_query` |
| `location_query` | `hi-IN` | `मेरे पास आपकी लोकेशन की जानकारी नहीं है। कृपया अपने जिले का नाम बताएं ताकि मैं स्थानीय मंडी भाव और मौसम बता सकूं।` | Centralized template `location_query` |
| `location_query` | `en-IN` | `I do not have access to your GPS location. Please tell me your district name to get local mandi prices and weather forecasts.` | Centralized template `location_query` |
| `location_query` | `hi-en` | `Mere paas aapki location ki jaankari nahi hai. Kripya apna district batayein taaki local mandi bhav aur weather bata sakun.` | Centralized template `location_query` |
| `mandi_assumed_district` | `te-IN` | `వరంగల్ మార్కెట్ ధరలు చూపిస్తున్నాను; మరొక జిల్లా కావాలంటే చెప్పండి:` | Centralized template `mandi_assumed_district` |
| `mandi_assumed_district` | `hi-IN` | `वारंगल मंडी का भाव दिखा रहा हूँ; दूसरा जिला चाहिए तो बताएं:` | Centralized template `mandi_assumed_district` |
| `mandi_assumed_district` | `en-IN` | `Showing Warangal; tell me another district if you want:` | Centralized template `mandi_assumed_district` |
| `mandi_assumed_district` | `hi-en` | `Warangal mandi ka bhav dikha raha hoon; doosra district chahiye toh batayein:` | Centralized template `mandi_assumed_district` |
| `mandi_cached_note` | `te-IN` | `(గమనిక: తాజా లైవ్ రికార్డు లభించనందున, {date} నాటి మునుపటి రికార్డు ప్రకారం)` | Centralized template `mandi_cached_note` |
| `mandi_cached_note` | `hi-IN` | `(ध्यान दें: ताजा रिकॉर्ड न मिलने से, {date} के पिछले रिकॉर्ड अनुसार)` | Centralized template `mandi_cached_note` |
| `mandi_cached_note` | `en-IN` | `(Note: Latest live record unavailable; showing record from {date})` | Centralized template `mandi_cached_note` |
| `mandi_cached_note` | `hi-en` | `(Note: Live record unavailable hone se, {date} ke record ke mutabiq)` | Centralized template `mandi_cached_note` |
| `mandi_caveat` | `te-IN` | `ఇది మార్కెట్ కమిటీ నివేదించిన రోజువారీ ధర, లైవ్ ట్రేడింగ్ కోట్ కాదు.` | Centralized template `mandi_caveat` |
| `mandi_caveat` | `hi-IN` | `यह मंडी समिति द्वारा दर्ज किया गया दैनिक मूल्य है, लाइव ट्रेडिंग कोट नहीं है।` | Centralized template `mandi_caveat` |
| `mandi_caveat` | `en-IN` | `This is the daily price reported by the market committee, not a live trading quote.` | Centralized template `mandi_caveat` |
| `mandi_caveat` | `hi-en` | `Yeh mandi committee ka reported daily price hai, live trading quote nahi hai.` | Centralized template `mandi_caveat` |
| `mandi_district_label` | `te-IN` | `{district} జిల్లా` | Centralized template `mandi_district_label` |
| `mandi_district_label` | `hi-IN` | `{district} ज़िले` | Centralized template `mandi_district_label` |
| `mandi_district_label` | `en-IN` | `{district} district` | Centralized template `mandi_district_label` |
| `mandi_district_label` | `hi-en` | `{district} district` | Centralized template `mandi_district_label` |
| `mandi_markets_joiner` | `te-IN` | `{mkt1} మరియు {mkt2}` | Centralized template `mandi_markets_joiner` |
| `mandi_markets_joiner` | `hi-IN` | `{mkt1} और {mkt2}` | Centralized template `mandi_markets_joiner` |
| `mandi_markets_joiner` | `en-IN` | `{mkt1} and {mkt2}` | Centralized template `mandi_markets_joiner` |
| `mandi_markets_joiner` | `hi-en` | `{mkt1} and {mkt2}` | Centralized template `mandi_markets_joiner` |
| `mandi_missing_commodity` | `te-IN` | `మీరు ఏ పంట లేదా కూరగాయ ధర తెలుసుకోవాలనుకుంటున్నారు? ఉదాహరణకు పత్తి, వరి, మిర్చి లేదా టమాటా.` | Centralized template `mandi_missing_commodity` |
| `mandi_missing_commodity` | `hi-IN` | `आप किस फसल या सब्जी का भाव जानना चाहते हैं? जैसे कपास, धान, मिर्च या टमाटर।` | Centralized template `mandi_missing_commodity` |
| `mandi_missing_commodity` | `en-IN` | `Which crop or commodity price would you like to know? For example cotton, paddy, chilli, or tomato.` | Centralized template `mandi_missing_commodity` |
| `mandi_missing_commodity` | `hi-en` | `Aap kis crop ya sabzi ka bhav janna chahte hain? Jaise cotton, paddy, chilli ya tomato.` | Centralized template `mandi_missing_commodity` |
| `mandi_no_records` | `te-IN` | `క్షమించండి, మీ ప్రాంతంలో ఈ పంటకు సంబంధించి ప్రస్తుత మండి ధరల రికార్డులు ఏవీ లభించలేదు. దయచేసి సమీప మార్కెట్ లేదా మరొక పంట పేరుతో ప్రయత్నించండి.` | Centralized template `mandi_no_records` |
| `mandi_no_records` | `hi-IN` | `माफ़ कीजिए, आपके क्षेत्र में इस फसल के लिए कोई हालिया मंडी मूल्य रिकॉर्ड नहीं मिला। कृपया नज़दीकी मंडी या दूसरी फसल का नाम बताएं।` | Centralized template `mandi_no_records` |
| `mandi_no_records` | `en-IN` | `Sorry, no recent mandi price records were found for this commodity in your area. Please try asking about a nearby market or a different crop.` | Centralized template `mandi_no_records` |
| `mandi_no_records` | `hi-en` | `Sorry, aapke area me is crop ke liye koi recent mandi price record nahi mila. Please paas ki mandi ya doosri crop try karein.` | Centralized template `mandi_no_records` |
| `mandi_no_records_district` | `te-IN` | `క్షమించండి, {district} జిల్లాలో {commodity}కు సంబంధించి ప్రస్తుత మండి రికార్డులు ఏవీ లభించలేదు. మీరు {state} రాష్ట్రంలోని ఇతర మార్కెట్ల ధరలు తెలుసుకోవాలనుకుంటున్నారా?` | Centralized template `mandi_no_records_district` |
| `mandi_no_records_district` | `hi-IN` | `माफ़ कीजिए, {district} ज़िले में {commodity} का कोई हालिया मंडी रिकॉर्ड नहीं मिला। क्या आप {state} राज्य की अन्य मंडियों के भाव जानना चाहते हैं?` | Centralized template `mandi_no_records_district` |
| `mandi_no_records_district` | `en-IN` | `Sorry, no recent mandi records were found for {commodity} in {district} district. Would you like prices from across {state} state?` | Centralized template `mandi_no_records_district` |
| `mandi_no_records_district` | `hi-en` | `Sorry, {district} district me {commodity} ka koi recent mandi record nahi mila. Kya aap {state} state ki doosri mandiyon ke prices jaanna chahte hain?` | Centralized template `mandi_no_records_district` |
| `mandi_service_unavailable` | `te-IN` | `ధరల సేవ ప్రస్తుతం స్పందించడం లేదు, దయచేసి కొన్ని నిమిషాల తర్వాత మళ్లీ ప్రయత్నించండి.` | Centralized template `mandi_service_unavailable` |
| `mandi_service_unavailable` | `hi-IN` | `मंडी भाव सेवा अभी प्रतिक्रिया नहीं दे रही है, कृपया कुछ मिनटों बाद पुनः प्रयास करें।` | Centralized template `mandi_service_unavailable` |
| `mandi_service_unavailable` | `en-IN` | `The price service is not responding right now, please try again in a few minutes.` | Centralized template `mandi_service_unavailable` |
| `mandi_service_unavailable` | `hi-en` | `Price service abhi respond nahi kar rahi hai, kripya kuch minute baad dobara try karein.` | Centralized template `mandi_service_unavailable` |
| `mandi_single_market` | `te-IN` | `{state_prefix}{mkt1} మార్కెట్లో {date1} {comm} నివేదించిన మోడల్ ధర {price1}{unit}{stale_note}{cached_note}.` | Centralized template `mandi_single_market` |
| `mandi_single_market` | `hi-IN` | `{state_prefix}{mkt1} मंडी में {date1} {comm} का दर्ज मॉडल मूल्य {price1}{unit}{stale_note}{cached_note} है।` | Centralized template `mandi_single_market` |
| `mandi_single_market` | `en-IN` | `{state_prefix}In {mkt1} market on {date1}, the reported modal price for {comm} was {price1}{unit}{stale_note}{cached_note}.` | Centralized template `mandi_single_market` |
| `mandi_single_market` | `hi-en` | `{state_prefix}{mkt1} mandi me {date1} {comm} ka reported modal price {price1}{unit}{stale_note}{cached_note} hai.` | Centralized template `mandi_single_market` |
| `mandi_stale_warning` | `te-IN` | `(గమనిక: ఈ రికార్డు 3 రోజుల కంటే పాతది)` | Centralized template `mandi_stale_warning` |
| `mandi_stale_warning` | `hi-IN` | `(ध्यान दें: यह रिकॉर्ड 3 दिन से अधिक पुराना है)` | Centralized template `mandi_stale_warning` |
| `mandi_stale_warning` | `en-IN` | `(Note: this record is older than 3 days)` | Centralized template `mandi_stale_warning` |
| `mandi_stale_warning` | `hi-en` | `(Note: yeh record 3 din se purana hai)` | Centralized template `mandi_stale_warning` |
| `mandi_state_fallback` | `te-IN` | `{district} జిల్లాలో రికార్డు లేదు. తెలంగాణ రాష్ట్ర స్థాయి సమాచారం ప్రకారం:` | Centralized template `mandi_state_fallback` |
| `mandi_state_fallback` | `hi-IN` | `{district} जिले में रिकॉर्ड नहीं है। तेलंगाना राज्य स्तर की जानकारी के अनुसार:` | Centralized template `mandi_state_fallback` |
| `mandi_state_fallback` | `en-IN` | `No record found in {district} district. Showing Telangana state-level prices:` | Centralized template `mandi_state_fallback` |
| `mandi_state_fallback` | `hi-en` | `{district} district me record nahi mila. Telangana state-level info ke mutabiq:` | Centralized template `mandi_state_fallback` |
| `mandi_two_markets` | `te-IN` | `{state_prefix}{dist_label}లో {mkt1} మార్కెట్లో {date1} {comm1} మోడల్ ధర {price1}{unit}, మరియు {mkt2} మార్కెట్లో {date2} {comm2} {price2}{unit}గా నమోదైంది{stale_note}{cached_note}.` | Centralized template `mandi_two_markets` |
| `mandi_two_markets` | `hi-IN` | `{state_prefix}{dist_label} में {mkt1} मंडी में {date1} {comm1} का मॉडल भाव {price1}{unit}, और {mkt2} मंडी में {date2} {comm2} का भाव {price2}{unit} दर्ज हुआ{stale_note}{cached_note}।` | Centralized template `mandi_two_markets` |
| `mandi_two_markets` | `en-IN` | `{state_prefix}In {dist_label}, reported modal price for {comm1} in {mkt1} on {date1} was {price1}{unit}, and for {comm2} in {mkt2} on {date2} was {price2}{unit}{stale_note}{cached_note}.` | Centralized template `mandi_two_markets` |
| `mandi_two_markets` | `hi-en` | `{state_prefix}In {dist_label}, {comm1} modal price was {price1}{unit} in {mkt1} on {date1}, and {comm2} was {price2}{unit} in {mkt2} on {date2}{stale_note}{cached_note}.` | Centralized template `mandi_two_markets` |
| `mandi_unit` | `te-IN` | `క్వింటాలుకు` | Centralized template `mandi_unit` |
| `mandi_unit` | `hi-IN` | `प्रति क्विंटल` | Centralized template `mandi_unit` |
| `mandi_unit` | `en-IN` | `per quintal` | Centralized template `mandi_unit` |
| `mandi_unit` | `hi-en` | `per quintal` | Centralized template `mandi_unit` |
| `market_1` | `te-IN` | `మార్కెట్ 1` | Centralized template `market_1` |
| `market_1` | `hi-IN` | `मंडी 1` | Centralized template `market_1` |
| `market_1` | `en-IN` | `market 1` | Centralized template `market_1` |
| `market_1` | `hi-en` | `mandi 1` | Centralized template `market_1` |
| `market_2` | `te-IN` | `మార్కెట్ 2` | Centralized template `market_2` |
| `market_2` | `hi-IN` | `मंडी 2` | Centralized template `market_2` |
| `market_2` | `en-IN` | `market 2` | Centralized template `market_2` |
| `market_2` | `hi-en` | `mandi 2` | Centralized template `market_2` |
| `price_not_available` | `te-IN` | `లభ్యం కాలేదు` | Centralized template `price_not_available` |
| `price_not_available` | `hi-IN` | `उपलब्ध नहीं` | Centralized template `price_not_available` |
| `price_not_available` | `en-IN` | `not available` | Centralized template `price_not_available` |
| `price_not_available` | `hi-en` | `available nahi` | Centralized template `price_not_available` |
| `price_range` | `te-IN` | `రూపాయలు {min} నుండి {max}` | Centralized template `price_range` |
| `price_range` | `hi-IN` | `रुपये {min} से {max}` | Centralized template `price_range` |
| `price_range` | `en-IN` | `Rs {min} to {max}` | Centralized template `price_range` |
| `price_range` | `hi-en` | `Rs {min} to {max}` | Centralized template `price_range` |
| `price_single` | `te-IN` | `రూపాయలు {val}` | Centralized template `price_single` |
| `price_single` | `hi-IN` | `रुपये {val}` | Centralized template `price_single` |
| `price_single` | `en-IN` | `Rs {val}` | Centralized template `price_single` |
| `price_single` | `hi-en` | `Rs {val}` | Centralized template `price_single` |
| `small_talk_bye` | `te-IN` | `వీడ్కోలు! మీ రోజు శుభప్రదం కావాలి.` | Centralized template `small_talk_bye` |
| `small_talk_bye` | `hi-IN` | `अलविदा! आपका दिन शुभ हो।` | Centralized template `small_talk_bye` |
| `small_talk_bye` | `en-IN` | `Goodbye! Have a good day.` | Centralized template `small_talk_bye` |
| `small_talk_bye` | `hi-en` | `Alvida! Aapka din accha rahe.` | Centralized template `small_talk_bye` |
| `small_talk_ok` | `te-IN` | `సరే! ఇంకేదైనా సహాయం కావాలంటే చెప్పండి.` | Centralized template `small_talk_ok` |
| `small_talk_ok` | `hi-IN` | `ठीक है! कोई और सहायता चाहिए तो बताएं।` | Centralized template `small_talk_ok` |
| `small_talk_ok` | `en-IN` | `Okay! Let me know if you need any other help.` | Centralized template `small_talk_ok` |
| `small_talk_ok` | `hi-en` | `Theek hai! Koi aur help chahiye toh batayein.` | Centralized template `small_talk_ok` |
| `small_talk_thanks` | `te-IN` | `ధన్యవాదాలు! ఇంకేదైనా సహాయం కావాలంటే అడగండి.` | Centralized template `small_talk_thanks` |
| `small_talk_thanks` | `hi-IN` | `आपका स्वागत है! अगर कोई और सहायता चाहिए तो बताएं।` | Centralized template `small_talk_thanks` |
| `small_talk_thanks` | `en-IN` | `You're welcome! Let me know if you need any other help.` | Centralized template `small_talk_thanks` |
| `small_talk_thanks` | `hi-en` | `Aapka swagat hai! Koi aur help chahiye toh batayein.` | Centralized template `small_talk_thanks` |
| `unsupported_intent` | `te-IN` | `నేను ప్రస్తుతానికి తాజా మండి ధరల సమాచారాన్ని మరియు వాతావరణ సమాచారాన్ని మాత్రమే అందించగలను. పంట సలహాలు త్వరలో రానున్నాయి.` | Centralized template `unsupported_intent` |
| `unsupported_intent` | `hi-IN` | `मैं वर्तमान में केवल ताजा मंडी भाव और मौसम की जानकारी दे सकता हूँ। फसल सलाह जल्द आ रही है।` | Centralized template `unsupported_intent` |
| `unsupported_intent` | `en-IN` | `I can currently help with live mandi prices and weather forecasts. Crop advisory features are coming soon.` | Centralized template `unsupported_intent` |
| `unsupported_intent` | `hi-en` | `Main abhi live mandi bhav aur mausam forecast provide kar sakta hoon. Crop advisory jald hi aayegi.` | Centralized template `unsupported_intent` |
| `unsupported_media` | `te-IN` | `సహాయం కోసం దయచేసి వాయిస్ సందేశం లేదా టెక్స్ట్ మెసేజ్ పంపండి.` | Centralized template `unsupported_media` |
| `unsupported_media` | `hi-IN` | `सहायता के लिए कृपया वॉयस संदेश या टेक्स्ट मैसेज भेजें।` | Centralized template `unsupported_media` |
| `unsupported_media` | `en-IN` | `Please send a voice note or a text message for assistance.` | Centralized template `unsupported_media` |
| `unsupported_media` | `hi-en` | `Help ke liye please audio voice note ya text message bhejein.` | Centralized template `unsupported_media` |
| `voice_limit_reached` | `te-IN` | `ఈ రోజుకు వాయిస్ డెమో పరిమితి ముగిసింది. దయచేసి రేపు మళ్లీ ప్రయత్నించండి లేదా టెక్స్ట్ మెసేజ్ ద్వారా అడగండి.` | Centralized template `voice_limit_reached` |
| `voice_limit_reached` | `hi-IN` | `आज के लिए वॉयस डेमो सीमा समाप्त हो गई है। कृपया कल पुनः प्रयास करें या टेक्स्ट संदेश भेजें।` | Centralized template `voice_limit_reached` |
| `voice_limit_reached` | `en-IN` | `Voice demo limit reached for today. Please try again tomorrow or send a text message.` | Centralized template `voice_limit_reached` |
| `voice_limit_reached` | `hi-en` | `Aaj ke liye voice demo limit khatam ho gayi hai. Please kal try karein ya text message bhejein.` | Centralized template `voice_limit_reached` |
| `weather_forecast` | `te-IN` | `వాతావరణ సూచన ప్రకారం, {district}లో {date0} గరిష్ట ఉష్ణోగ్రత {max0}°C, కనిష్ట ఉష్ణోగ్రత {min0}°C గా నమోదయ్యే అవకాశం ఉంది మరియు వర్షం పడే అవకాశం {rain0}% గా ఉంది. రాబోయే రెండు రోజుల్లో వర్షం పడే అవకాశం దాదాపు {rain_next}% వరకు ఉండవచ్చు. వాతావరణ పరిస్థితులను బట్టి మీ వ్యవసాయ పనులను తగిన జాగ్రత్తలతో ప్లాన్ చేసుకోండి.` | Centralized template `weather_forecast` |
| `weather_forecast` | `hi-IN` | `मौसम पूर्वानुमान के अनुसार, {district} में {date0} अधिकतम तापमान {max0}°C और न्यूनतम तापमान {min0}°C रहने का अनुमान है, तथा वर्षा की संभावना {rain0}% है। अगले दो दिनों में बारिश की संभावना लगभग {rain_next}% तक रह सकती है। मौसम की स्थिति को देखते हुए अपने कृषि कार्यों की उचित योजना बनाएं।` | Centralized template `weather_forecast` |
| `weather_forecast` | `en-IN` | `According to the weather forecast, {district} on {date0} is expected to have a maximum temperature of {max0}°C, a minimum of {min0}°C, and a {rain0}% chance of rain. Over the next two days, the chance of rain may reach approximately {rain_next}%. Please plan your field operations carefully based on local weather conditions.` | Centralized template `weather_forecast` |
| `weather_forecast` | `hi-en` | `Weather forecast ke mutabiq, {district} me {date0} maximum temperature {max0}°C aur minimum {min0}°C rehne ka anuman hai, aur rain ke {rain0}% chances hain. Agle do dino me rain ke chances lagbhag {rain_next}% tak ho sakte hain. Mausam ki sthiti ke hisaab se apne kheti ke kamo ko plan karein.` | Centralized template `weather_forecast` |
| `weather_unavailable` | `te-IN` | `క్షమించండి, ప్రస్తుతం వాతావరణ సమాచారం అందుబాటులో లేదు. దయచేసి కాసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.` | Centralized template `weather_unavailable` |
| `weather_unavailable` | `hi-IN` | `माफ़ कीजिए, फ़िलहाल मौसम की जानकारी उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें।` | Centralized template `weather_unavailable` |
| `weather_unavailable` | `en-IN` | `Sorry, weather information is currently unavailable. Please try again later.` | Centralized template `weather_unavailable` |
| `weather_unavailable` | `hi-en` | `Sorry, abhi weather information available nahi hai. Please thodi der baad try karein.` | Centralized template `weather_unavailable` |
| `your_area` | `te-IN` | `మీ ప్రాంతం` | Centralized template `your_area` |
| `your_area` | `hi-IN` | `आपका क्षेत्र` | Centralized template `your_area` |
| `your_area` | `en-IN` | `your area` | Centralized template `your_area` |
| `your_area` | `hi-en` | `aapka area` | Centralized template `your_area` |
