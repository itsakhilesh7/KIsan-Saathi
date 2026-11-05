"""Voice-note and text message orchestration pipeline.

Coordinates: WhatsApp media in -> Audio normalize -> Gnani Prisma STT
-> LLM reasoning -> Gnani Timbre TTS -> WhatsApp voice out.
Logs per-stage latency and events without blocking async event loops.
"""

import asyncio
import logging
import os
import tempfile
import time
from typing import Any

from ..channels.base import ChannelClient, WhatsAppChannelClient
from ..core.config import Settings, get_settings
from ..core.logging import get_request_id, hash_phone
from ..core.security import validate_media_type
from ..integrations.data_gov.mandi import fetch_mandi_prices
from ..integrations.gnani import stt as gnani_stt
from ..integrations.gnani import tts as gnani_tts
from ..integrations.llm.openai_compatible import OpenAICompatibleLLM
from ..repositories.dialogue_state import DialogueStateRepository
from ..repositories.events import EventRepository
from ..repositories.user_preferences import SQLiteUserPreferencesRepository
from ..schemas.intent import IntentType
from . import audio_service
from .answer_composer import UNSUPPORTED_INTENT_MESSAGES, compose_clarification_reply, compose_mandi_answer
from .intent_service import detect_text_language, extract_intent

log = logging.getLogger("orchestrator")

# Language-aware messages across all 4 supported/tested languages
EMPTY_TRANSCRIPT_MESSAGES: dict[str, str] = {
    "te-IN": "క్షమించండి, మీ వాయిస్ స్పష్టంగా వినబడలేదు. దయచేసి మళ్లీ చెప్పండి.",
    "hi-IN": "माफ़ कीजिए, आवाज़ साफ़ नहीं आई। कृपया दोबारा बोलिए।",
    "en-IN": "Sorry, I could not hear that clearly. Please try speaking again.",
    "hi-en": "Sorry, aapki aawaz clear nahi aayi. Please dobara boliye.",
}

FALLBACK_MESSAGES: dict[str, str] = {
    "te-IN": "క్షమించండి, ఇప్పుడు సమాధానం ఇవ్వడంలో సమస్య ఉంది. దయచేసి కొంత సమయం తర్వాత మళ్లీ ప్రయత్నించండి లేదా 1551 కి కాల్ చేయండి.",
    "hi-IN": "माफ़ कीजिए, अभी जवाब देने में दिक्कत हो रही है। कृपया थोड़ी देर बाद फिर कोशिश करें या 1551 पर कॉल करें।",
    "en-IN": "Sorry, I am having trouble answering right now. Please try again in a little while or call 1551.",
    "hi-en": "Sorry, abhi answer dene me issue ho raha hai. Please thodi der baad dobara try karein ya 1551 par call karein.",
}

AUDIO_TOO_LONG_MESSAGES: dict[str, str] = {
    "te-IN": "వాయిస్ నోట్ చాలా పెద్దదిగా ఉంది (పరిమితి 60 సెకన్లు). దయచేసి చిన్న సందేశాన్ని పంపండి.",
    "hi-IN": "वॉयस नोट बहुत लंबा है (अधिकतम 60 सेकंड)। कृपया छोटा संदेश भेजें।",
    "en-IN": "Voice note is too long (maximum 60 seconds). Please send a shorter audio message.",
    "hi-en": "Voice note zyada lamba hai (limit 60 seconds). Please chhota audio message bhejein.",
}

UNSUPPORTED_MEDIA_MESSAGES: dict[str, str] = {
    "te-IN": "సహాయం కోసం దయచేసి వాయిస్ సందేశం లేదా టెక్స్ట్ మెసేజ్ పంపండి.",
    "hi-IN": "सहायता के लिए कृपया वॉयस संदेश या टेक्स्ट मैसेज भेजें।",
    "en-IN": "Please send a voice note or a text message for assistance.",
    "hi-en": "Help ke liye please audio voice note ya text message bhejein.",
}

_event_repo: EventRepository | None = None
_user_pref_repo: SQLiteUserPreferencesRepository | None = None
_dialogue_repo: DialogueStateRepository | None = None


def get_event_repo() -> EventRepository:
    """Returns the event repository instance, lazily initializing if needed."""
    global _event_repo
    if _event_repo is None:
        _event_repo = EventRepository()
    return _event_repo


def set_event_repo(repo: EventRepository | None) -> None:
    """Allows tests to inject a temporary event repository."""
    global _event_repo
    _event_repo = repo


def get_user_pref_repo() -> SQLiteUserPreferencesRepository:
    """Returns the user preferences repository instance, lazily initializing if needed."""
    global _user_pref_repo
    if _user_pref_repo is None:
        _user_pref_repo = SQLiteUserPreferencesRepository()
    return _user_pref_repo


def set_user_pref_repo(repo: SQLiteUserPreferencesRepository | None) -> None:
    """Allows tests to inject a temporary user preferences repository."""
    global _user_pref_repo
    _user_pref_repo = repo


def get_dialogue_repo() -> DialogueStateRepository:
    """Returns the dialogue state repository instance, lazily initializing if needed."""
    global _dialogue_repo
    if _dialogue_repo is None:
        _dialogue_repo = DialogueStateRepository()
    return _dialogue_repo


def set_dialogue_repo(repo: DialogueStateRepository | None) -> None:
    """Allows tests to inject a temporary dialogue state repository."""
    global _dialogue_repo
    _dialogue_repo = repo


def _resolve_user_language(user_hash: str, explicit_lang: str | None, settings: Settings) -> str:
    """Resolves language: explicit if given, else last seen for user, else pilot primary language."""
    if explicit_lang:
        return explicit_lang
    stored = get_user_pref_repo().get_language(user_hash)
    if stored:
        return stored
    return settings.pilot_primary_language


async def handle_voice_message(
    msg: dict[str, Any],
    settings: Settings,
    client: ChannelClient | None = None,
) -> None:
    """Orchestrates end-to-end voice note pipeline with per-stage timing."""
    channel = client or WhatsAppChannelClient(settings=settings)
    timings: dict[str, float] = {}
    start_total = time.perf_counter()
    detected_lang: str | None = None
    sender_phone = msg.get("from") or ""
    phone_hash = hash_phone(sender_phone, settings.PHONE_HASH_SALT)
    media_id = msg.get("media_id")
    mime_type = msg.get("mime_type")
    req_id = get_request_id()

    if not media_id or not sender_phone:
        log.warning("Voice message missing media_id or sender phone")
        return

    # Audio limit check 1: Validate media type if provided in webhook metadata
    if mime_type and not validate_media_type(mime_type):
        log.warning("Rejected unsupported media MIME type '%s' from user=%s", mime_type, phone_hash)
        fallback_lang = _resolve_user_language(phone_hash, None, settings)
        unsupported_msg = UNSUPPORTED_MEDIA_MESSAGES.get(fallback_lang, UNSUPPORTED_MEDIA_MESSAGES["te-IN"])
        await channel.send_text(sender_phone, unsupported_msg)
        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "status": "rejected_mime",
        })
        return

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_ogg = os.path.join(tmp_dir, "in.ogg")
            in_wav = os.path.join(tmp_dir, "in.wav")
            out_wav = os.path.join(tmp_dir, "out.wav")
            out_ogg = os.path.join(tmp_dir, "out.ogg")

            # Stage 1: Download & convert incoming audio (enforces AUDIO_MAX_MB)
            s = time.perf_counter()
            audio_bytes = await channel.download_media(media_id)
            with open(in_ogg, "wb") as f:
                f.write(audio_bytes)

            await asyncio.to_thread(audio_service.to_wav16k, in_ogg, in_wav)
            timings["download_convert"] = round(time.perf_counter() - s, 2)

            # Audio limit check 2: Validate duration before calling STT (enforces AUDIO_MAX_SECONDS)
            duration = await asyncio.to_thread(audio_service.get_duration, in_wav)
            if duration > settings.AUDIO_MAX_SECONDS:
                log.warning("Voice note duration (%.1fs) exceeds limit (%ds) for user=%s", duration, settings.AUDIO_MAX_SECONDS, phone_hash)
                fallback_lang = _resolve_user_language(phone_hash, None, settings)
                too_long_msg = AUDIO_TOO_LONG_MESSAGES.get(fallback_lang, AUDIO_TOO_LONG_MESSAGES["te-IN"])
                await channel.send_text(sender_phone, too_long_msg)
                await get_event_repo().log_event({
                    "request_id": req_id,
                    "user_hash": phone_hash,
                    "channel": channel.channel_name,
                    "status": "rejected_duration",
                    "timings": timings,
                })
                return

            # Stage 2: Prisma Speech-to-Text
            s = time.perf_counter()
            stt_res = await gnani_stt.transcribe(in_wav, settings=settings)
            timings["stt"] = round(time.perf_counter() - s, 2)

            transcript = stt_res.get("transcript", "").strip()
            raw_detected_lang = stt_res.get("detected_language_code")
            is_first_turn = get_user_pref_repo().get_language(phone_hash) is None
            if raw_detected_lang:
                detected_lang = raw_detected_lang
                get_user_pref_repo().set_language(phone_hash, detected_lang)
            else:
                detected_lang = _resolve_user_language(phone_hash, None, settings)

            if not transcript:
                log.info("Empty transcript returned for user=%s", phone_hash)
                clarification = EMPTY_TRANSCRIPT_MESSAGES.get(detected_lang, EMPTY_TRANSCRIPT_MESSAGES["te-IN"])
                await channel.send_text(sender_phone, clarification)
                await get_event_repo().log_event({
                    "request_id": req_id,
                    "user_hash": phone_hash,
                    "channel": channel.channel_name,
                    "detected_language": detected_lang,
                    "status": "empty_transcript",
                    "timings": timings,
                })
                return

            # Stage 3: Intent extraction & Grounded Answering / LLM reasoning
            s = time.perf_counter()
            parsed = extract_intent(
                transcript,
                language=detected_lang,
                user_hash=phone_hash,
                dialogue_repo=get_dialogue_repo(),
            )

            if parsed.intent == IntentType.MANDI_PRICE_QUERY:
                if parsed.clarification_needed:
                    reply_text = compose_clarification_reply(language=detected_lang, is_first_turn=is_first_turn)
                    disclosed_model = "grounded/dialogue_clarification"
                else:
                    evidence = await fetch_mandi_prices(
                        commodity=parsed.slots.commodity,
                        district=parsed.slots.district,
                        state=parsed.slots.state or "Telangana",
                        settings=settings,
                    )
                    reply_text = compose_mandi_answer(
                        evidence,
                        language=detected_lang,
                        is_first_turn=is_first_turn,
                        requested_district=parsed.slots.district,
                        requested_commodity=parsed.slots.commodity,
                        requested_state=parsed.slots.state or "Telangana",
                        unit=settings.MANDI_PRICE_UNIT,
                    )
                    disclosed_model = "grounded/agmarknet_mandi"
            elif parsed.intent == IntentType.GREETING_OR_HELP:
                if is_first_turn:
                    greetings = {
                        "te-IN": "నమస్కారం! నేను కిసాన్ సాథీ AI సహాయకుడిని. మీరు నన్ను పంటల మండి ధరల సమాచారం గురించి అడగవచ్చు.",
                        "hi-IN": "नमस्ते! मैं किसान साथी AI सहायक हूँ। आप मुझसे फसलों के मंडी भाव की जानकारी पूछ सकते हैं।",
                        "en-IN": "Hello! I am Kisan Saathi, your AI farming assistant. You can ask me about mandi crop prices.",
                        "hi-en": "Namaste! Main Kisan Saathi AI assistant hoon. Aap mujhse mandi crop prices pooch sakte hain.",
                    }
                else:
                    greetings = {
                        "te-IN": "నమస్కారం! మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?",
                        "hi-IN": "नमस्ते! आप किस फसल का मंडी भाव जानना चाहते हैं?",
                        "en-IN": "Hello! Which crop's mandi price would you like to know?",
                        "hi-en": "Namaste! Aap kis crop ka mandi price jaanna chahte hain?",
                    }
                reply_text = greetings.get(detected_lang, greetings["te-IN"])
                disclosed_model = "rule_based/greeting"
            else:
                if settings.ECHO_UNSUPPORTED:
                    llm_adapter = OpenAICompatibleLLM(settings=settings)
                    reply_text, disclosed_model = await llm_adapter.answer(transcript, lang=detected_lang)
                else:
                    reply_text = UNSUPPORTED_INTENT_MESSAGES.get(detected_lang, UNSUPPORTED_INTENT_MESSAGES["te-IN"])
                    disclosed_model = "rule_based/unsupported_intent"

            timings["llm"] = round(time.perf_counter() - s, 2)

            # Stage 4: Timbre Text-to-Speech
            s = time.perf_counter()
            wav_bytes = await gnani_tts.synthesize(reply_text, language=detected_lang, settings=settings)
            with open(out_wav, "wb") as f:
                f.write(wav_bytes)

            await asyncio.to_thread(audio_service.wav_to_ogg_opus, out_wav, out_ogg)
            timings["tts_convert"] = round(time.perf_counter() - s, 2)

            # Stage 5: Upload & reply
            s = time.perf_counter()
            with open(out_ogg, "rb") as f:
                ogg_reply_bytes = f.read()

            await channel.send_audio_bytes(sender_phone, ogg_reply_bytes)

            if settings.SEND_TEXT_COPY:
                await channel.send_text(sender_phone, reply_text)

            timings["upload_send"] = round(time.perf_counter() - s, 2)

        timings["total"] = round(time.perf_counter() - start_total, 2)

        # Store persistent audit event (transcripts stored ONLY if STORE_RAW_TRANSCRIPTS is True)
        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "detected_language": detected_lang,
            "raw_detected_language": raw_detected_lang,
            "model_name": disclosed_model,
            "timings": timings,
            "status": "ok",
            "transcript": transcript if settings.STORE_RAW_TRANSCRIPTS else None,
            "reply": reply_text if settings.STORE_RAW_TRANSCRIPTS else None,
        })

    except Exception as e:
        log.exception(
            "Voice message processing failed: %s",
            e,
            extra={"request_id": req_id, "user_hash": phone_hash},
        )
        err_lang = _resolve_user_language(phone_hash, detected_lang, settings)
        fallback_msg = FALLBACK_MESSAGES.get(err_lang, FALLBACK_MESSAGES["te-IN"])
        try:
            await channel.send_text(sender_phone, fallback_msg)
        except Exception:
            log.exception("Failed to deliver fallback error message to user")

        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "detected_language": detected_lang,
            "status": "error",
            "timings": timings,
        })


async def handle_text_message(
    msg: dict[str, Any],
    settings: Settings,
    client: ChannelClient | None = None,
) -> None:
    """Processes inbound text message query."""
    channel = client or WhatsAppChannelClient(settings=settings)
    sender_phone = msg.get("from") or ""
    phone_hash = hash_phone(sender_phone, settings.PHONE_HASH_SALT)
    text = msg.get("text", "")
    req_id = get_request_id()

    if not text or not sender_phone:
        return

    try:
        is_first_turn = get_user_pref_repo().get_language(phone_hash) is None
        detected_script_lang = detect_text_language(text)
        user_lang = detected_script_lang or _resolve_user_language(phone_hash, None, settings)
        get_user_pref_repo().set_language(phone_hash, user_lang)

        parsed = extract_intent(
            text,
            language=user_lang,
            user_hash=phone_hash,
            dialogue_repo=get_dialogue_repo(),
        )

        if parsed.intent == IntentType.MANDI_PRICE_QUERY:
            if parsed.clarification_needed:
                reply = compose_clarification_reply(language=user_lang, is_first_turn=is_first_turn)
                disclosed_model = "grounded/dialogue_clarification"
            else:
                evidence = await fetch_mandi_prices(
                    commodity=parsed.slots.commodity,
                    district=parsed.slots.district,
                    state=parsed.slots.state or "Telangana",
                    settings=settings,
                )
                reply = compose_mandi_answer(
                    evidence,
                    language=user_lang,
                    is_first_turn=is_first_turn,
                    requested_district=parsed.slots.district,
                    requested_commodity=parsed.slots.commodity,
                    requested_state=parsed.slots.state or "Telangana",
                    unit=settings.MANDI_PRICE_UNIT,
                )
                disclosed_model = "grounded/agmarknet_mandi"
        elif parsed.intent == IntentType.GREETING_OR_HELP:
            if is_first_turn:
                greetings = {
                    "te-IN": "నమస్కారం! నేను కిసాన్ సాథీ AI సహాయకుడిని. మీరు నన్ను పంటల మండి ధరల సమాచారం గురించి అడగవచ్చు.",
                    "hi-IN": "नमस्ते! मैं किसान साथी AI सहायक हूँ। आप मुझसे फसलों के मंडी भाव की जानकारी पूछ सकते हैं।",
                    "en-IN": "Hello! I am Kisan Saathi, your AI farming assistant. You can ask me about mandi crop prices.",
                    "hi-en": "Namaste! Main Kisan Saathi AI assistant hoon. Aap mujhse mandi crop prices pooch sakte hain.",
                }
            else:
                greetings = {
                    "te-IN": "నమస్కారం! మీరు ఏ పంట మండి ధర తెలుసుకోవాలనుకుంటున్నారు?",
                    "hi-IN": "नमस्ते! आप किस फसल का मंडी भाव जानना चाहते हैं?",
                    "en-IN": "Hello! Which crop's mandi price would you like to know?",
                    "hi-en": "Namaste! Aap kis crop ka mandi price jaanna chahte hain?",
                }
            reply = greetings.get(user_lang, greetings["te-IN"])
            disclosed_model = "rule_based/greeting"
        else:
            if settings.ECHO_UNSUPPORTED:
                llm_adapter = OpenAICompatibleLLM(settings=settings)
                reply, disclosed_model = await llm_adapter.answer(text, lang=user_lang)
            else:
                reply = UNSUPPORTED_INTENT_MESSAGES.get(user_lang, UNSUPPORTED_INTENT_MESSAGES["te-IN"])
                disclosed_model = "rule_based/unsupported_intent"

        await channel.send_text(sender_phone, reply)
        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "model_name": disclosed_model,
            "status": "ok",
            "transcript": text if settings.STORE_RAW_TRANSCRIPTS else None,
            "reply": reply if settings.STORE_RAW_TRANSCRIPTS else None,
        })
    except Exception as e:
        log.exception("Text message answering failed: %s", e)
        err_lang = _resolve_user_language(phone_hash, None, settings)
        fallback_msg = FALLBACK_MESSAGES.get(err_lang, FALLBACK_MESSAGES["te-IN"])
        try:
            await channel.send_text(sender_phone, fallback_msg)
        except Exception:
            log.exception("Failed to deliver fallback text")


async def handle_incoming_message(
    msg: dict[str, Any],
    settings: Settings | None = None,
    client: ChannelClient | None = None,
) -> None:
    """Entry point router for background message processing."""
    cfg = settings or get_settings()
    channel = client or WhatsAppChannelClient(settings=cfg)
    msg_type = msg.get("type")

    if msg_type == "audio" and msg.get("media_id"):
        await handle_voice_message(msg, cfg, client=channel)
    elif msg_type == "text":
        await handle_text_message(msg, cfg, client=channel)
    else:
        sender_phone = msg.get("from")
        if sender_phone:
            try:
                phone_hash = hash_phone(sender_phone, cfg.PHONE_HASH_SALT)
                user_lang = _resolve_user_language(phone_hash, None, cfg)
                unsupported_msg = UNSUPPORTED_MEDIA_MESSAGES.get(user_lang, UNSUPPORTED_MEDIA_MESSAGES["te-IN"])
                await channel.send_text(sender_phone, unsupported_msg)
            except Exception:
                log.exception("Failed to send unsupported message notification")
