"""voice note in -> Prisma -> LLM -> Timbre -> voice note out. Logs per-stage latency."""
import asyncio
import hashlib
import json
import logging
import os
import tempfile
import time

from . import audio, config, gnani, llm, whatsapp

log = logging.getLogger("pipeline")
EVENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "events.jsonl")

FALLBACK = {
    "hi-IN": "माफ़ कीजिए, अभी जवाब देने में दिक्कत हो रही है। कृपया थोड़ी देर बाद फिर कोशिश करें।",
    "te-IN": "క్షమించండి, ఇప్పుడు సమాధానం ఇవ్వడంలో సమస్య ఉంది. దయచేసి కొంత సమయం తర్వాత మళ్లీ ప్రయత్నించండి.",
    "en-IN": "Sorry, I'm having trouble answering right now. Please try again in a little while.",
}
NOT_SUPPORTED = "Please send a voice note or a text message."


def _log_event(event: dict) -> None:
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _anon(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:12]  # never store raw numbers


async def handle_voice(msg: dict) -> None:
    t = {}
    start = time.perf_counter()
    lang = None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            ogg_in, wav_in = os.path.join(tmp, "in.ogg"), os.path.join(tmp, "in.wav")

            s = time.perf_counter()
            data = await whatsapp.download_media(msg["media_id"])
            with open(ogg_in, "wb") as f:
                f.write(data)
            await asyncio.to_thread(audio.to_wav16k, ogg_in, wav_in)
            t["download_convert"] = round(time.perf_counter() - s, 2)

            s = time.perf_counter()
            stt = await gnani.transcribe(wav_in)
            t["stt"] = round(time.perf_counter() - s, 2)
            transcript = stt["transcript"]
            lang = stt.get("detected_language_code") or config.TTS_DEFAULT_LANG
            if not transcript:
                await whatsapp.send_text(msg["from"], "I couldn't hear that clearly. Please try again.")
                return

            s = time.perf_counter()
            reply = await llm.answer(transcript, lang)
            t["llm"] = round(time.perf_counter() - s, 2)

            s = time.perf_counter()
            wav_bytes = await gnani.synthesize(reply, lang)
            wav_out, ogg_out = os.path.join(tmp, "out.wav"), os.path.join(tmp, "out.ogg")
            with open(wav_out, "wb") as f:
                f.write(wav_bytes)
            await asyncio.to_thread(audio.wav_to_ogg_opus, wav_out, ogg_out)
            t["tts_convert"] = round(time.perf_counter() - s, 2)

            s = time.perf_counter()
            with open(ogg_out, "rb") as f:
                ogg_bytes = f.read()
            media_id = await whatsapp.upload_audio(ogg_bytes)
            await whatsapp.send_audio(msg["from"], media_id)
            if config.SEND_TEXT_COPY:
                await whatsapp.send_text(msg["from"], reply)
            t["upload_send"] = round(time.perf_counter() - s, 2)

        t["total"] = round(time.perf_counter() - start, 2)
        _log_event({"ts": time.time(), "user": _anon(msg["from"]), "kind": "voice", "lang": lang,
                    "transcript": transcript, "reply": reply, "timings": t})
        log.info("voice ok lang=%s timings=%s", lang, t)
    except Exception as e:  # noqa: BLE001 - never crash the background task silently
        log.exception("voice handling failed")
        _log_event({"ts": time.time(), "user": _anon(msg["from"]), "kind": "voice_error",
                    "error": str(e)[:300]})
        try:
            await whatsapp.send_text(msg["from"], FALLBACK.get(lang or "", FALLBACK["en-IN"]))
        except Exception:  # noqa: BLE001
            log.exception("could not send fallback message")


async def handle_text(msg: dict) -> None:
    try:
        reply = await llm.answer(msg.get("text", ""))
        await whatsapp.send_text(msg["from"], reply)
        _log_event({"ts": time.time(), "user": _anon(msg["from"]), "kind": "text",
                    "transcript": msg.get("text"), "reply": reply})
    except Exception:  # noqa: BLE001
        log.exception("text handling failed")
        await whatsapp.send_text(msg["from"], FALLBACK["en-IN"])


async def handle_message(msg: dict) -> None:
    kind = msg.get("type")
    if kind == "audio" and msg.get("media_id"):
        await handle_voice(msg)
    elif kind == "text":
        await handle_text(msg)
    else:
        await whatsapp.send_text(msg["from"], NOT_SUPPORTED)
