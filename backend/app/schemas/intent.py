"""Strict intent classification and slot schemas (architecture.md §6.2)."""

from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Allowed intent types. Server strictly controls tools; LLM never chooses URLs or SQL."""

    MANDI_PRICE_QUERY = "mandi_price_query"
    WEATHER_QUERY = "weather_query"
    CROP_ADVISORY_QUERY = "crop_advisory_query"
    GREETING_OR_HELP = "greeting_or_help"
    SMALL_TALK = "small_talk"
    CAPABILITIES_QUERY = "capabilities_query"
    LOCATION_QUERY = "location_query"
    UNSUPPORTED_OR_UNCLEAR = "unsupported_or_unclear"



class IntentSlots(BaseModel):
    """Structured entity slots extracted from user utterance."""

    commodity: str | None = None
    state: str | None = None
    district: str | None = None
    market: str | None = None
    date: str = "latest_available"
    crop: str | None = None
    crop_stage: str | None = None
    symptom: str | None = None
    plant_part: str | None = None
    duration: str | None = None


class ParsedIntent(BaseModel):
    """Strict parsed intent contract."""

    intent: IntentType
    language: str  # te-IN | hi-IN | en-IN | hi-en
    slots: IntentSlots = Field(default_factory=IntentSlots)
    missing_required_slots: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_type: str | None = None
    small_talk_type: str | None = None
    is_assumed_district: bool = False

