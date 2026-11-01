"""OpenAI-compatible LLM adapter for Evon or development stand-in models.

If LLM_BASE_URL is empty, runs in ECHO MODE (returns user text as-is).
The model name used is ALWAYS disclosed per rules.md.
"""

import asyncio
import logging

import httpx

from ...core.config import Settings, get_settings
from .base import LLMAdapter

log = logging.getLogger("llm.openai_compatible")

SYSTEM_PROMPT = """You are Kisan Saathi, a helpful assistant for Indian farmers on WhatsApp.
Rules:
- Reply in the SAME language and script the farmer used (Telugu in Telugu script, Hindi in Devanagari, English in English).
- Keep answers short and simple: at most 3 sentences, because they will be spoken aloud.
- Use ONLY the reference information provided below when it is given. If it does not contain the answer, say you are not sure and suggest calling the Kisan Call Centre on 1551.
- NEVER invent pesticide, fertiliser or medicine doses. If asked for a dose you cannot ground in the reference, refuse politely and refer to 1551 or the local agriculture officer.
- Do not use markdown, bullet points or emojis."""


class LLMError(Exception):
    """Raised when an LLM completion request fails."""


class OpenAICompatibleLLM(LLMAdapter):
    """Adapter for any OpenAI-compatible completions API (vLLM, SGLang, Ollama, etc.)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def answer(
        self,
        user_text: str,
        lang: str | None = None,
        context: str | None = None,
    ) -> tuple[str, str]:
        """Generates an answer using the configured model, or echoes if unconfigured."""
        if not self.settings.LLM_BASE_URL.strip():
            # Echo mode: STT -> TTS without LLM call during offline/early dev
            return user_text, "echo"

        disclosed_name = (
            self.settings.LLM_DISCLOSED_NAME.strip()
            or self.settings.LLM_MODEL.strip()
            or "openai-compatible-model"
        )

        system = SYSTEM_PROMPT
        if lang:
            system += f"\nTarget language: {lang}"
        if context:
            system += f"\n\nReference information:\n{context}"

        headers = {"Content-Type": "application/json"}
        if self.settings.LLM_API_KEY.strip():
            headers["Authorization"] = f"Bearer {self.settings.LLM_API_KEY.strip()}"

        body = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }

        endpoint = f"{self.settings.LLM_BASE_URL.rstrip('/')}/chat/completions"

        # Bounded retry on 429 and 5xx
        last_err: Exception | None = None
        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(3):
                try:
                    r = await client.post(endpoint, headers=headers, json=body)
                    if r.status_code in (429, 500, 502, 503, 504):
                        log.warning("LLM request failed with %d (attempt %d/3)", r.status_code, attempt + 1)
                        last_err = LLMError(f"LLM API error {r.status_code}: {r.text[:200]}")
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    if r.status_code != 200:
                        raise LLMError(f"LLM error {r.status_code}: {r.text[:300]}")

                    data = r.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return content, disclosed_name
                except httpx.TransportError as e:
                    log.warning("LLM transport error (attempt %d/3): %s", attempt + 1, e)
                    last_err = LLMError(f"Transport error connecting to LLM: {e}")
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise last_err or LLMError("LLM failed after 3 retries.")
