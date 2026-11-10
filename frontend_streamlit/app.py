"""Streamlit web interface for Kisan Saathi (AI Agricultural Assistant).

Directly reuses orchestrator pipeline functions (handle_voice_message, handle_text_message)
without duplicating any business logic. Provides microphone recording (st.audio_input)
or text queries, language hint selection, audio playback, structured evidence cards,
and model disclosure metadata.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for backend module imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from backend.app.channels.base import ChannelClient
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import hash_phone
from backend.app.repositories.dialogue_state import DialogueStateRepository
from backend.app.repositories.usage_limits import SQLiteUsageLimitsRepository
from backend.app.services.orchestrator import (
    get_dialogue_repo,
    get_usage_limits_repo,
    handle_text_message,
    handle_voice_message,
)

log = logging.getLogger("streamlit_app")


# Configuration & Streamlit Secrets Integration
def get_streamlit_settings() -> Settings:
    """Loads application settings, overlaying Streamlit secrets server-side."""
    overrides: dict[str, Any] = {}
    try:
        if hasattr(st, "secrets"):
            secret_keys = [
                "GNANI_API_KEY",
                "GNANI_TOKEN",
                "DATA_GOV_API_KEY",
                "LLM_API_KEY",
                "LLM_BASE_URL",
                "LLM_MODEL",
                "LLM_DISCLOSED_NAME",
                "PHONE_HASH_SALT",
                "DAILY_USER_VOICE_LIMIT",
                "DAILY_GLOBAL_VOICE_LIMIT",
                "PUBLIC_VOICE_MAX_SECONDS",
                "ADMIN_USER_HASHES",
                "ALLOW_CHEMICAL_DETAILS",
                "PILOT_DISTRICT",
                "PILOT_STATE",
                "PILOT_PRIMARY_LANGUAGE",
                "APP_ENV",
                "LOG_LEVEL",
            ]
            for key in secret_keys:
                try:
                    if key in st.secrets:
                        val = st.secrets[key]
                        if isinstance(val, str) and val.lower() in ("true", "false"):
                            overrides[key] = val.lower() == "true"
                        else:
                            overrides[key] = val
                except Exception:
                    continue
    except Exception:
        pass
    return get_settings(**overrides)


# Streamlit Channel Adapter (implements ChannelClient protocol)
class StreamlitChannelClient(ChannelClient):
    """In-memory channel adapter for Streamlit that captures media and audio output."""

    channel_name: str = "streamlit"

    def __init__(self, raw_audio_bytes: bytes | None = None) -> None:
        self.raw_audio_bytes = raw_audio_bytes
        self.sent_texts: list[str] = []
        self.sent_audio_bytes: bytes | None = None

    async def download_media(self, media_id: str) -> bytes:
        """Returns the in-memory recorded or uploaded audio bytes."""
        if self.raw_audio_bytes:
            return self.raw_audio_bytes
        raise ValueError(f"No audio bytes available for media_id: {media_id}")

    async def send_text(self, to: str, text: str) -> dict[str, str]:
        """Captures text message sent by orchestrator."""
        self.sent_texts.append(text)
        return {"status": "ok", "to": to, "text": text}

    async def send_audio_bytes(self, to: str, audio_bytes: bytes) -> dict[str, str]:
        """Captures synthesized voice note sent by orchestrator."""
        self.sent_audio_bytes = audio_bytes
        return {"status": "ok", "to": to}


# Async Execution Helper
def run_sync(coro: Any) -> Any:
    """Executes an async coroutine synchronously inside Streamlit event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already inside an active loop, run in a separate thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# Streamlit UI
def main() -> None:
    st.set_page_config(
        page_title="Kisan Saathi (కిసాన్ సాథీ) - AI Assistant for Farmers",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    settings = get_streamlit_settings()
    limits_repo: SQLiteUsageLimitsRepository = get_usage_limits_repo()
    dialogue_repo: DialogueStateRepository = get_dialogue_repo()

    # Custom styling
    st.markdown(
        """
        <style>
        .metric-card {
            background-color: #f7fafc;
            border-radius: 8px;
            padding: 12px 16px;
            border-left: 4px solid #2e7d32;
            margin-bottom: 12px;
        }
        .evidence-card {
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 14px 18px;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        .model-pill {
            display: inline-block;
            background-color: #e0f2fe;
            color: #0369a1;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-right: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar: Farmer Profile, Controls, and Quota
    st.sidebar.title("🌱 Kisan Saathi")
    st.sidebar.caption("AI Voice Assistant for Smallholder Farmers")

    pilot_cfg = settings.load_pilot_config()
    pilot_dist = pilot_cfg.get("primary", {}).get("district", "Warangal")
    pilot_st = pilot_cfg.get("primary", {}).get("state", "Telangana")
    st.sidebar.subheader("📍 Pilot Region")
    st.sidebar.info(
        f"**District:** {pilot_dist}, {pilot_st}\n\n"
        f"**Primary Crops:** Paddy (వరి), Cotton (పత్తి)\n\n"
        f"**Market Commodities:** Chilli (మిర్చి), Tomato (టమాట), Cotton, Paddy"
    )

    st.sidebar.subheader("👤 Farmer Profile")
    farmer_phone = st.sidebar.text_input(
        "Farmer Identifier / Phone",
        value=st.session_state.get("farmer_phone", "9876543210"),
        help="Used to isolate dialogue state and enforce daily usage caps.",
    )
    st.session_state["farmer_phone"] = farmer_phone
    farmer_hash = hash_phone(farmer_phone, settings.PHONE_HASH_SALT)

    st.sidebar.subheader("🌐 Language Hint")
    language_options = {
        "Auto-detect (ఆటో-డిటెక్ట్)": "auto",
        "Telugu (తెలుగు) - te-IN": "te-IN",
        "Hindi (हिन्दी) - hi-IN": "hi-IN",
        "English - en-IN": "en-IN",
        "Hinglish - hi-en": "hi-en",
    }
    selected_lang_label = st.sidebar.selectbox(
        "Preferred Language",
        options=list(language_options.keys()),
        index=0,
        help="Hints preferred response language. Auto-detect uses spoken dialect.",
    )
    lang_hint = language_options[selected_lang_label]

    # Usage Limits display
    st.sidebar.subheader("📊 Voice Quota Today")
    daily_user_limit = settings.DAILY_USER_VOICE_LIMIT
    user_voice_count = limits_repo.get_user_count(farmer_hash)
    global_voice_count = limits_repo.get_global_count()
    remaining_quota = max(0, daily_user_limit - user_voice_count)

    st.sidebar.progress(
        min(1.0, user_voice_count / daily_user_limit) if daily_user_limit > 0 else 0.0
    )
    st.sidebar.write(
        f"**User Voice Calls:** `{user_voice_count} / {daily_user_limit}` ({remaining_quota} remaining)"
    )
    st.sidebar.caption(f"Global Voice Calls Today: {global_voice_count}")

    # Dialogue State Reset
    st.sidebar.subheader("🔄 Conversation State")
    current_state = dialogue_repo.get_state(farmer_hash)
    if current_state:
        st.sidebar.warning(f"Pending Slot: `{current_state.get('pending_slot')}`")
    else:
        st.sidebar.write("State: *Idle (no pending clarifications)*")

    if st.sidebar.button("🧹 Clear Dialogue State"):
        dialogue_repo.clear_state(farmer_hash)
        st.sidebar.success("Dialogue state reset!")
        st.rerun()

    # Main Content Area
    st.title("🌾 Kisan Saathi (కిసాన్ సాథీ)")
    st.markdown(
        "Ask questions about **Mandi prices** (Agmarknet), **Weather forecasts** (Open-Meteo), "
        "or **Crop management** (PJTSAU Agro-Technologies). Speak in Telugu, Hindi, or English!"
    )

    # Quick example buttons
    st.write("##### Quick Test Queries")
    col1, col2, col3, col4 = st.columns(4)
    quick_query: str | None = None
    if col1.button("🍅 టమాట ధర ఎంత?", use_container_width=True):
        quick_query = "టమాట ధర ఎంత?"
    if col2.button("🌧️ వరంగల్‌లో రేపు వర్షం పడుతుందా?", use_container_width=True):
        quick_query = "వరంగల్‌లో రేపు వర్షం పడుతుందా?"
    if col3.button("🌾 వరిలో నీటి యాజమాన్యం ఎలా?", use_container_width=True):
        quick_query = "వరిలో నీటి యాజమాన్యం ఎలా?"
    if col4.button("🌿 పత్తిలో గులాబీ రంగు పురుగు నివారణ", use_container_width=True):
        quick_query = "పత్తిలో గులాబీ రంగు పురుగు నివారణ"

    tab_voice, tab_text = st.tabs(["🎙️ Voice Query (Microphone)", "⌨️ Text Query"])

    # -------------------------------------------------------------------------
    # Tab 1: Voice Input
    # -------------------------------------------------------------------------
    audio_data_to_process: bytes | None = None
    audio_mime: str = "audio/wav"

    with tab_voice:
        st.markdown("Record your query using your microphone or upload an audio file:")
        mic_audio = st.audio_input("Record Voice Query (Microphone)")

        uploaded_audio = st.file_uploader(
            "Or upload an audio note (.ogg, .wav, .webm, .m4a, .mp3)",
            type=["ogg", "wav", "webm", "m4a", "mp3"],
        )

        if mic_audio is not None:
            audio_data_to_process = mic_audio.read()
            audio_mime = getattr(mic_audio, "type", "audio/wav") or "audio/wav"
        elif uploaded_audio is not None:
            audio_data_to_process = uploaded_audio.read()
            audio_mime = getattr(uploaded_audio, "type", "audio/ogg") or "audio/ogg"

        process_voice = st.button("🚀 Process Voice Query", disabled=(audio_data_to_process is None))

    # Tab 2: Text Input
    with tab_text:
        typed_text = st.text_input(
            "Enter your agricultural query in Telugu, Hindi, or English:",
            value=quick_query or "",
            placeholder="ఉదాహరణ: వరంగల్‌లో పత్తి ధర ఎంత ఉంది?",
        )
        process_text = st.button("🚀 Send Text Query", disabled=(not typed_text.strip()))

    # Determine what to execute
    should_process_voice = process_voice and audio_data_to_process is not None
    should_process_text = (process_text and typed_text.strip()) or (quick_query is not None)

    # Execution & Pipeline Processing
    if should_process_voice:
        client = StreamlitChannelClient(raw_audio_bytes=audio_data_to_process)
        msg = {
            "from": farmer_phone,
            "media_id": f"streamlit_mic_{int(time.time())}",
            "mime_type": audio_mime,
            "language": lang_hint if lang_hint != "auto" else None,
        }

        with st.spinner("Processing voice through Gnani Prisma STT and Grounded Pipeline..."):
            result = run_sync(handle_voice_message(msg, settings=settings, client=client))
            st.session_state["last_result"] = result
            st.session_state["result_type"] = "voice"

    elif should_process_text:
        query_text = quick_query if quick_query else typed_text
        client = StreamlitChannelClient()
        msg = {
            "from": farmer_phone,
            "text": query_text,
            "language": lang_hint if lang_hint != "auto" else None,
        }

        with st.spinner("Analyzing intent and retrieving grounded evidence..."):
            result = run_sync(handle_text_message(msg, settings=settings, client=client))
            st.session_state["last_result"] = result
            st.session_state["result_type"] = "text"

    # -------------------------------------------------------------------------
    # Output Display
    # -------------------------------------------------------------------------
    if "last_result" in st.session_state and st.session_state["last_result"]:
        res = st.session_state["last_result"]
        res_type = st.session_state.get("result_type", "text")

        st.divider()
        st.subheader("📋 Response & Grounded Evidence")

        # Two-column layout: Answer + Audio on Left, Model Disclosure + Timings on Right
        left_col, right_col = st.columns([3, 2])

        with left_col:
            # 1. User Transcript / Query
            transcript = res.get("transcript")
            if transcript:
                st.markdown("**🗣️ Farmer Query (Transcript):**")
                st.info(transcript)

            # 2. Bot Answer Text
            reply_text = res.get("reply_text")
            if reply_text:
                st.markdown("**🤖 Kisan Saathi Answer:**")
                st.success(reply_text)

            # 3. Audio Player (when voice output generated)
            audio_bytes = res.get("audio_bytes")
            if audio_bytes:
                st.markdown("**🔊 Voice Answer (Synthesized Timbre Voice Note):**")
                st.audio(audio_bytes, format="audio/ogg")
            elif res_type == "voice" and res.get("status") != "ok":
                st.warning(f"Voice pipeline status: `{res.get('status')}`")

        with right_col:
            st.markdown("##### 🔬 Models & Provenance")
            # STT Model
            st.markdown(
                '<span class="model-pill">STT: Gnani Prisma v3.0</span>'
                f'<span class="model-pill">Lang: {res.get("detected_language") or "auto"}</span>',
                unsafe_allow_html=True,
            )

            # TTS Model
            if audio_bytes:
                st.markdown(
                    f'<span class="model-pill">TTS: Gnani Timbre ({settings.TTS_MODEL})</span>',
                    unsafe_allow_html=True,
                )

            # LLM / Grounding Model
            llm_disclosed = (
                settings.LLM_DISCLOSED_NAME.strip()
                or settings.LLM_MODEL
                or "Grounded Advisory Engine"
            )
            pipeline_tool = res.get("disclosed_model") or "rule_based/grounded"
            st.markdown(
                f'<span class="model-pill">LLM / Reasoner: {llm_disclosed}</span>'
                f'<span class="model-pill">Tool: {pipeline_tool}</span>',
                unsafe_allow_html=True,
            )

            # Timings & Latency
            timings = res.get("timings") or {}
            if timings:
                with st.expander("⏱️ Latency Breakdown", expanded=False):
                    for stage, duration in timings.items():
                        st.write(f"- **{stage}:** `{duration}s`")

            # Intent & Slots
            intent_val = res.get("intent")
            slots = res.get("slots")
            if intent_val:
                st.write(f"**Intent:** `{intent_val}`")
            if slots:
                st.write(f"**Slots:** `{slots}`")

        # Grounded Evidence Cards
        evidence = res.get("evidence")
        if evidence:
            st.markdown("#### 📑 Grounded Evidence & Verification Sources")

            # Case A: Mandi Prices (list of Evidence items)
            if isinstance(evidence, list):
                st.markdown(
                    f"Found **{len(evidence)} market price record(s)** from official Agmarknet feed:"
                )
                for _i, ev in enumerate(evidence):
                    data = ev.data if hasattr(ev, "data") else (ev.get("data") if isinstance(ev, dict) else {})
                    market = data.get("market") or getattr(ev, "location", "N/A")
                    commodity = data.get("commodity", "")
                    arrival_date = (
                        data.get("arrival_date")
                        or data.get("raw_arrival_date")
                        or getattr(ev, "observation_or_publication_date", "N/A")
                    )
                    modal_price = data.get("modal_price", "N/A")
                    min_price = data.get("min_price", "N/A")
                    max_price = data.get("max_price", "N/A")
                    variety = data.get("variety", "")
                    src_url = getattr(ev, "source_url", "https://data.gov.in")
                    src_name = getattr(ev, "source_name", "Agmarknet via data.gov.in")

                    with st.container():
                        st.markdown(
                            f"""
                            <div class="evidence-card">
                                <h4>🛒 {market} — {commodity} ({variety or 'Standard'})</h4>
                                <p><strong>Modal Price:</strong> ₹{modal_price} / quintal &nbsp;|&nbsp;
                                   <strong>Range:</strong> ₹{min_price} – ₹{max_price}</p>
                                <p><strong>Arrival Date:</strong> {arrival_date} &nbsp;|&nbsp;
                                   <strong>Source:</strong> <a href="{src_url}" target="_blank">{src_name}</a></p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Case B: Weather Forecast (single Evidence item)
            elif (
                (hasattr(evidence, "source_type") and "weather" in str(getattr(evidence, "source_type", "")).lower())
                or (isinstance(evidence, dict) and "weather" in str(evidence.get("source_type", "")).lower())
            ):
                data = evidence.data if hasattr(evidence, "data") else (evidence.get("data") if isinstance(evidence, dict) else {})
                location = getattr(evidence, "location", "Warangal, Telangana")
                date_str = getattr(evidence, "observation_or_publication_date", "Today/Tomorrow")
                src_url = getattr(evidence, "source_url", "https://open-meteo.com")
                temp_max = data.get("temp_max", ["N/A"])[0] if isinstance(data.get("temp_max"), list) else data.get("temp_max", "N/A")
                temp_min = data.get("temp_min", ["N/A"])[0] if isinstance(data.get("temp_min"), list) else data.get("temp_min", "N/A")
                precip = data.get("precipitation_sum", ["0.0"])[0] if isinstance(data.get("precipitation_sum"), list) else data.get("precipitation_sum", "0.0")
                prob = data.get("precipitation_probability", ["0"])[0] if isinstance(data.get("precipitation_probability"), list) else data.get("precipitation_probability", "0")

                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <h4>🌤️ Forecast for {location} ({date_str})</h4>
                        <p><strong>Temperature:</strong> {temp_min}°C to {temp_max}°C &nbsp;|&nbsp;
                           <strong>Rain Expected:</strong> {precip} mm ({prob}% chance)</p>
                        <p><strong>Source:</strong> <a href="{src_url}" target="_blank">Open-Meteo Weather API</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Case C: PJTSAU Crop Advisory Document Card
            else:
                data = evidence.data if hasattr(evidence, "data") else (evidence.get("data") if isinstance(evidence, dict) else {})
                title = getattr(evidence, "source_name", "PJTSAU Agro-Technologies Card")
                zone = getattr(evidence, "location", "Telangana")
                publisher = getattr(evidence, "publisher", "PJTSAU")
                year = getattr(evidence, "observation_or_publication_date", "2020-21")
                card_no = data.get("card_number", "N/A")
                page = data.get("page", "N/A")
                score = data.get("similarity_score", "N/A")
                raw_text = data.get("raw_text", "")
                src_url = getattr(evidence, "source_url", "https://pjtsau.edu.in")

                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <h4>📖 PJTSAU Advisory: {title} (Card #{card_no})</h4>
                        <p><strong>Zone:</strong> {zone} &nbsp;|&nbsp;
                           <strong>Year:</strong> {year} &nbsp;|&nbsp;
                           <strong>Page:</strong> {page} &nbsp;|&nbsp;
                           <strong>Match Score:</strong> {score}</p>
                        <p><strong>Publisher:</strong> {publisher} &nbsp;|&nbsp;
                           <strong>Document URL:</strong> <a href="{src_url}" target="_blank">Download PDF</a></p>
                        <details>
                            <summary>View Verified Guidance Text</summary>
                            <blockquote style="margin-top: 8px;">{raw_text}</blockquote>
                        </details>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
