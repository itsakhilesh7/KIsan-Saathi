"""Internal evidence schema contract (architecture.md §6.1).

Every factual claim in Kisan Saathi must pass through this evidence contract.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Allowlisted evidence source types."""

    MANDI_RECORD = "mandi_record"
    WEATHER_FORECAST = "weather_forecast"
    KCC_RECORD = "kcc_record"
    ADVISORY_DOCUMENT = "advisory_document"


class Evidence(BaseModel):
    """Grounded evidence record representing a retrieved factual datum."""

    evidence_id: str
    source_type: SourceType
    source_name: str
    source_url: str
    publisher: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    observation_or_publication_date: str | None = None  # YYYY-MM-DD or null
    location: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
