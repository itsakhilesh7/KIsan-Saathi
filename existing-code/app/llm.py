"""LLM layer. Talks to any OpenAI-compatible /chat/completions endpoint (vLLM/SGLang serving Evon).
If LLM_BASE_URL is empty we run in ECHO MODE so the rest of the pipeline can be built first."""
import httpx

from . import config

SYSTEM_PROMPT = """You are Kisan Saathi, a helpful assistant for Indian farmers on WhatsApp.
Rules:
- Reply in the SAME language and script the farmer used (Telugu in Telugu script, Hindi in Devanagari, English in English).
- Keep answers short and simple: at most 3 sentences, because they will be spoken aloud.
- Use ONLY the reference information provided below when it is given. If it does not contain the answer, say you are not sure and suggest calling the Kisan Call Centre on 1551.
- NEVER invent pesticide, fertiliser or medicine doses. If asked for a dose you cannot ground in the reference, refuse politely and refer to 1551 or the local agriculture officer.
- Do not use markdown, bullet points or emojis."""


class LLMError(Exception):
    pass


async def answer(user_text: str, lang: str | None = None, context: str | None = None) -> str:
    if not config.LLM_BASE_URL:
        return user_text  # echo mode: tests STT -> TTS without any LLM

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\nReference information:\n{context}"
    headers = {"Content-Type": "application/json"}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"
    body = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{config.LLM_BASE_URL}/chat/completions", headers=headers, json=body)
    if r.status_code != 200:
        raise LLMError(f"LLM error {r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]["content"].strip()
