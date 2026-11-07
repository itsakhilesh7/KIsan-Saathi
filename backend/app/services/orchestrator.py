"""Voice-note and text message orchestration pipeline.

Coordinates: WhatsApp media in -> Audio normalize -> Gnani Prisma STT
-> LLM reasoning -> Gnani Timbre TTS -> WhatsApp voice out.
Logs per-stage latency and events without blocking async event loops.
All user-visible prompts are strictly resolved from core.messages.
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
from ..core.messages import get_message, to_speech_text
from ..core.security import validate_media_type
from ..integrations.data_gov.mandi import MandiServiceUnavailableError, fetch_mandi_prices
from ..integrations.gnani import stt as gnani_stt
from ..integrations.gnani import tts as gnani_tts
from ..integrations.llm.openai_compatible import OpenAICompatibleLLM
from ..integrations.weather.open_meteo import fetch_weather_forecast
from ..repositories.dialogue_state import DialogueStateRepository
from ..repositories.events import EventRepository
from ..repositories.usage_limits import SQLiteUsageLimitsRepository
from ..repositories.user_preferences import SQLiteUserPreferencesRepository
from ..schemas.intent import IntentType
from . import audio_service
from .answer_composer import (
    compose_clarification_reply,
    compose_mandi_answer,
    compose_weather_answer,
)
from .intent_service import classify_intent_with_llm_fallback, detect_text_language

log = logging.getLogger("orchestrator")

_event_repo: EventRepository | None = None
_user_pref_repo: SQLiteUserPreferencesRepository | None = None
_dialogue_repo: DialogueStateRepository | None = None
_usage_limits_repo: SQLiteUsageLimitsRepository | None = None


def get_usage_limits_repo() -> SQLiteUsageLimitsRepository:
    """Returns the usage limits repository instance, lazily initializing if needed."""
    global _usage_limits_repo
    if _usage_limits_repo is None:
        _usage_limits_repo = SQLiteUsageLimitsRepository()
    return _usage_limits_repo


def set_usage_limits_repo(repo: SQLiteUsageLimitsRepository | None) -> None:
    """Allows tests to inject a temporary usage limits repository."""
    global _usage_limits_repo
    _usage_limits_repo = repo


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
    return getattr(settings, "PILOT_PRIMARY_LANGUAGE", None) or getattr(settings, "STT_LANGUAGE", "te-IN")



async def handle_voice_message(
    msg: dict[str, Any],
    settings: Settings,
    client: ChannelClient | None = None,
) -> None:
    """Pipeline: WhatsApp media in -> 16kHz WAV -> Prisma STT -> compose grounded answer -> Timbre TTS -> voice out."""
    channel = client or WhatsAppChannelClient(settings=settings)
    media_id = msg.get("media_id", "")
    mime_type = msg.get("mime_type", "")
    sender_phone = msg.get("from", "")
    phone_hash = hash_phone(sender_phone, settings.PHONE_HASH_SALT)
    req_id = get_request_id()

    # Pre-validation check 1: Media MIME type
    if not validate_media_type(mime_type):
        log.warning("Rejected unsupported media MIME type '%s' for user=%s", mime_type, phone_hash)
        fallback_lang = _resolve_user_language(phone_hash, None, settings)
        await channel.send_text(sender_phone, get_message("unsupported_media", fallback_lang))
        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "status": "rejected_mime",
        })
        return

    timings: dict[str, float] = {}
    start_total = time.perf_counter()
    parsed = None
    disclosed_model = None

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_ogg = os.path.join(tmp_dir, "in.ogg")
            in_wav = os.path.join(tmp_dir, "in.wav")
            out_wav = os.path.join(tmp_dir, "out.wav")
            out_ogg = os.path.join(tmp_dir, "out.ogg")

            # Stage 1: Download & convert incoming audio
            s = time.perf_counter()
            audio_bytes = await channel.download_media(media_id)
            with open(in_ogg, "wb") as f:
                f.write(audio_bytes)

            await asyncio.to_thread(audio_service.to_wav16k, in_ogg, in_wav)
            timings["download_convert"] = round(time.perf_counter() - s, 2)

            # Audio limit check 2: Validate duration before calling STT
            duration = await asyncio.to_thread(audio_service.get_duration, in_wav)
            fallback_lang = _resolve_user_language(phone_hash, None, settings)

            effective_max_voice = (
                settings.PUBLIC_VOICE_MAX_SECONDS
                if settings.PUBLIC_VOICE_MAX_SECONDS > 0
                else settings.AUDIO_MAX_SECONDS
            )
            if duration > effective_max_voice:
                log.warning("Voice note duration (%.1fs) exceeds limit (%ds) for user=%s", duration, effective_max_voice, phone_hash)
                too_long_msg = get_message("audio_too_long", fallback_lang)
                await channel.send_text(sender_phone, too_long_msg)
                await get_event_repo().log_event({
                    "request_id": req_id,
                    "user_hash": phone_hash,
                    "channel": channel.channel_name,
                    "status": "rejected_duration",
                    "duration": duration,
                    "timings": timings,
                })
                return

            if duration < 1.0:
                log.info("Voice note duration (%.2fs) < 1.0s, returning empty_transcript message", duration)
                too_short_msg = get_message("empty_transcript", fallback_lang)
                await channel.send_text(sender_phone, too_short_msg)
                await get_event_repo().log_event({
                    "request_id": req_id,
                    "user_hash": phone_hash,
                    "channel": channel.channel_name,
                    "status": "audio_too_short",
                    "duration": duration,
                    "timings": timings,
                })
                return

            # Check daily voice usage limits to protect Gnani credits
            admin_set = {h.strip() for h in settings.ADMIN_USER_HASHES.split(",") if h.strip()}
            allowed, limit_reason = get_usage_limits_repo().check_and_increment(
                phone_hash,
                max_user=settings.DAILY_USER_VOICE_LIMIT,
                max_global=settings.DAILY_GLOBAL_VOICE_LIMIT,
                admin_hashes=admin_set,
            )
            if not allowed:
                log.warning("Voice rate limit reached (%s) for user=%s", limit_reason, phone_hash)
                limit_msg = get_message("voice_limit_reached", fallback_lang)
                await channel.send_text(sender_phone, limit_msg)
                await get_event_repo().log_event({
                    "request_id": req_id,
                    "user_hash": phone_hash,
                    "channel": channel.channel_name,
                    "status": "rejected_rate_limit",
                    "reason": limit_reason,
                    "duration": duration,
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
                clarification = get_message("empty_transcript", detected_lang)
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
            parsed, llm_disclosed = await classify_intent_with_llm_fallback(
                transcript,
                language=detected_lang,
                settings=settings,
                user_hash=phone_hash,
                dialogue_repo=get_dialogue_repo(),
            )

            if parsed.intent == IntentType.MANDI_PRICE_QUERY:
                if parsed.clarification_needed:
                    reply_text = compose_clarification_reply(
                        language=detected_lang,
                        is_first_turn=is_first_turn,
                        clarification_type=parsed.clarification_type,
                    )
                    disclosed_model = "grounded/dialogue_clarification"
                else:
                    try:
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
                            is_assumed_district=parsed.is_assumed_district,
                        )
                        disclosed_model = "grounded/agmarknet_mandi"
                    except MandiServiceUnavailableError:
                        reply_text = get_message("mandi_service_unavailable", detected_lang)
                        disclosed_model = "system/mandi_service_unavailable"
            elif parsed.intent == IntentType.WEATHER_QUERY:
                target_dist = parsed.slots.district or "Warangal"
                weather_ev = await fetch_weather_forecast(
                    district=target_dist,
                    state=parsed.slots.state or "Telangana",
                    settings=settings,
                )
                reply_text = compose_weather_answer(
                    weather_ev,
                    language=detected_lang,
                    is_first_turn=is_first_turn,
                    requested_district=target_dist,
                )
                disclosed_model = "grounded/open_meteo_weather"
            elif parsed.intent == IntentType.GREETING_OR_HELP:
                greeting_key = "greeting_first_turn" if is_first_turn else "greeting_repeat"
                reply_text = get_message(greeting_key, detected_lang)
                disclosed_model = "rule_based/greeting"
                get_dialogue_repo().set_state(
                    phone_hash,
                    {
                        "intent": IntentType.MANDI_PRICE_QUERY,
                        "pending_slot": "commodity",
                        "clarification_type": "missing_commodity",
                    },
                )
            elif parsed.intent == IntentType.SMALL_TALK:
                st_key = f"small_talk_{parsed.small_talk_type or 'ok'}"
                reply_text = get_message(st_key, detected_lang)
                disclosed_model = f"rule_based/{st_key}"
            elif parsed.intent == IntentType.CAPABILITIES_QUERY:
                reply_text = get_message("capabilities_query", detected_lang)
                disclosed_model = "rule_based/capabilities"
                get_dialogue_repo().set_state(
                    phone_hash,
                    {
                        "intent": IntentType.MANDI_PRICE_QUERY,
                        "pending_slot": "commodity",
                        "clarification_type": "missing_commodity",
                    },
                )
            elif parsed.intent == IntentType.LOCATION_QUERY:
                reply_text = get_message("location_query", detected_lang)
                disclosed_model = "rule_based/location"
            else:
                if settings.ECHO_UNSUPPORTED:
                    llm_adapter = OpenAICompatibleLLM(settings=settings)
                    reply_text, disclosed_model = await llm_adapter.answer(transcript, lang=detected_lang)
                else:
                    reply_text = get_message("unsupported_intent", detected_lang)
                    disclosed_model = llm_disclosed or "rule_based/unsupported_intent"

            timings["llm"] = round(time.perf_counter() - s, 2)

            # Stage 4: Timbre Text-to-Speech (translates technical tokens & latin locations to native script)
            s = time.perf_counter()
            speech_text = to_speech_text(reply_text, language=detected_lang)
            wav_bytes = await gnani_tts.synthesize(speech_text, language=detected_lang, settings=settings)
            with open(out_wav, "wb") as f:
                f.write(wav_bytes)

            out_audio_duration = await asyncio.to_thread(audio_service.get_duration, out_wav)
            timings["tts_duration_seconds"] = round(out_audio_duration, 2)
            log.info("Synthesized reply audio duration: %.2fs", out_audio_duration)

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
            "intent": parsed.intent.value if parsed else None,
            "tool": disclosed_model,
            "audio_duration_seconds": round(out_audio_duration, 2) if "out_audio_duration" in locals() else None,
            "timings": timings,
            "status": "ok",
            "transcript": transcript if settings.STORE_RAW_TRANSCRIPTS else None,
            "reply": reply_text if settings.STORE_RAW_TRANSCRIPTS else None,
        })
    except Exception as e:
        log.exception("Voice pipeline processing failed: %s", e)
        err_lang = _resolve_user_language(phone_hash, None, settings)
        if isinstance(e, MandiServiceUnavailableError):
            fallback_msg = get_message("mandi_service_unavailable", err_lang)
        else:
            fallback_msg = get_message("fallback_1551", err_lang)

        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "status": "error",
            "error_type": type(e).__name__,
            "intent": parsed.intent.value if parsed else None,
            "tool": disclosed_model if disclosed_model else None,
            "timings": timings,
        })
        try:
            await channel.send_text(sender_phone, fallback_msg)
        except Exception:
            log.exception("Failed to deliver fallback notification")


async def handle_text_message(
    msg: dict[str, Any],
    settings: Settings,
    client: ChannelClient | None = None,
) -> None:
    """Processes incoming text messages using strict intent extraction and grounded answering."""
    channel = client or WhatsAppChannelClient(settings=settings)
    sender_phone = msg.get("from", "")
    text = msg.get("text", "").strip()
    phone_hash = hash_phone(sender_phone, settings.PHONE_HASH_SALT)
    req_id = get_request_id()
    parsed = None
    disclosed_model = None

    try:
        is_first_turn = get_user_pref_repo().get_language(phone_hash) is None
        detected_script_lang = detect_text_language(text)
        user_lang = detected_script_lang or _resolve_user_language(phone_hash, None, settings)
        get_user_pref_repo().set_language(phone_hash, user_lang)

        parsed, llm_disclosed = await classify_intent_with_llm_fallback(
            text,
            language=user_lang,
            settings=settings,
            user_hash=phone_hash,
            dialogue_repo=get_dialogue_repo(),
        )

        if parsed.intent == IntentType.MANDI_PRICE_QUERY:
            if parsed.clarification_needed:
                reply = compose_clarification_reply(
                    language=user_lang,
                    is_first_turn=is_first_turn,
                    clarification_type=parsed.clarification_type,
                )
                disclosed_model = "grounded/dialogue_clarification"
            else:
                try:
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
                        is_assumed_district=parsed.is_assumed_district,
                    )
                    disclosed_model = "grounded/agmarknet_mandi"
                except MandiServiceUnavailableError:
                    reply = get_message("mandi_service_unavailable", user_lang)
                    disclosed_model = "system/mandi_service_unavailable"
        elif parsed.intent == IntentType.WEATHER_QUERY:
            target_dist = parsed.slots.district or "Warangal"
            weather_ev = await fetch_weather_forecast(
                district=target_dist,
                state=parsed.slots.state or "Telangana",
                settings=settings,
            )
            reply = compose_weather_answer(
                weather_ev,
                language=user_lang,
                is_first_turn=is_first_turn,
                requested_district=target_dist,
            )
            disclosed_model = "grounded/open_meteo_weather"
        elif parsed.intent == IntentType.GREETING_OR_HELP:
            greeting_key = "greeting_first_turn" if is_first_turn else "greeting_repeat"
            reply = get_message(greeting_key, user_lang)
            disclosed_model = "rule_based/greeting"
            get_dialogue_repo().set_state(
                phone_hash,
                {
                    "intent": IntentType.MANDI_PRICE_QUERY,
                    "pending_slot": "commodity",
                    "clarification_type": "missing_commodity",
                },
            )
        elif parsed.intent == IntentType.SMALL_TALK:
            st_key = f"small_talk_{parsed.small_talk_type or 'ok'}"
            reply = get_message(st_key, user_lang)
            disclosed_model = f"rule_based/{st_key}"
        elif parsed.intent == IntentType.CAPABILITIES_QUERY:
            reply = get_message("capabilities_query", user_lang)
            disclosed_model = "rule_based/capabilities"
            get_dialogue_repo().set_state(
                phone_hash,
                {
                    "intent": IntentType.MANDI_PRICE_QUERY,
                    "pending_slot": "commodity",
                    "clarification_type": "missing_commodity",
                },
            )
        elif parsed.intent == IntentType.LOCATION_QUERY:
            reply = get_message("location_query", user_lang)
            disclosed_model = "rule_based/location"
        else:
            if settings.ECHO_UNSUPPORTED:
                llm_adapter = OpenAICompatibleLLM(settings=settings)
                reply, disclosed_model = await llm_adapter.answer(text, lang=user_lang)
            else:
                reply = get_message("unsupported_intent", user_lang)
                disclosed_model = llm_disclosed or "rule_based/unsupported_intent"

        await channel.send_text(sender_phone, reply)
        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "model_name": disclosed_model,
            "intent": parsed.intent.value if parsed else None,
            "tool": disclosed_model,
            "status": "ok",
            "transcript": text if settings.STORE_RAW_TRANSCRIPTS else None,
            "reply": reply if settings.STORE_RAW_TRANSCRIPTS else None,
        })
    except Exception as e:
        log.exception("Text message answering failed: %s", e)
        err_lang = _resolve_user_language(phone_hash, None, settings)
        if isinstance(e, MandiServiceUnavailableError):
            fallback_msg = get_message("mandi_service_unavailable", err_lang)
        else:
            fallback_msg = get_message("fallback_1551", err_lang)

        await get_event_repo().log_event({
            "request_id": req_id,
            "user_hash": phone_hash,
            "channel": channel.channel_name,
            "status": "error",
            "error_type": type(e).__name__,
            "intent": parsed.intent.value if parsed else None,
            "tool": disclosed_model if disclosed_model else None,
        })
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
                unsupported_msg = get_message("unsupported_media", user_lang)
                await channel.send_text(sender_phone, unsupported_msg)
            except Exception:
                log.exception("Failed to send unsupported message notification")
