"""Conversation and voice request/response schemas (architecture.md §6.3)."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from .evidence import Evidence
from .intent import ParsedIntent


class AnswerPayload(BaseModel):
    """Spoken and textual response payload."""

    text: str
    language: str
    audio_available: bool = False
    audio_url: str | None = None


class VoiceRequest(BaseModel):
    """Incoming query from WhatsApp or Web Demo."""

    text: str | None = None
    language: str | None = None
    region_id: str | None = None
    channel: Literal["whatsapp", "web"] = "web"
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class VoiceResponse(BaseModel):
    """End-to-end response for web and API consumers."""

    request_id: str
    transcript: str | None = None
    language: str | None = None
    intent: ParsedIntent | None = None
    answer: AnswerPayload | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    timings: dict[str, float] = Field(default_factory=dict)
    llm_disclosed_name: str | None = None
